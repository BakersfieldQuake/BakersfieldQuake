r"""Builds G:\Quake\Combat\BakersfieldQuake\custom_models_and_animations.html:
A 100% self-contained, single-file offline WebGL2 + Crisp 2D Canvas Showcase of ALL custom
animations & 3D models in BakersfieldQuake — strictly EXCLUDING all cars/vehicles and all guns/weapons —
ready to share directly with friends as a single .html file!

Categories packed:
  1. featured       — 8 Multi-Animation Character Showcases (Bryan 18 anims, Wheelman 9 360° actions,
                      Wheelman 14 spherical/stunt/explosion clips, Paul 7 anims, Dennis 7 anims,
                      QuakeGuy 7 anims, Rob's MR. D.I.Y. 2 anims, Rubber Finger 3 anims)
  2. chars3d        — 16 Custom 3D Characters, Sculpted Heads & Mega-Man Riders
  3. contraptions3d — 38 Custom 3D Flying Creations, 16-Vision Mystery Cube, 8-Channel TV, Bots, Props & FX
  4. sprites        — 20 Multi-Angle Turnaround Sprites & Real-Life Friends Crew
  + 22-Clip Custom Voice & Comedy Soundboard

Usage:
    python3.13 source/mm_tools/build_friends_showcase_html.py
"""
import base64
import glob
import gzip
import io
import json
import math
import os
import re
import struct
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(MOD, ".."))
PROGS = os.path.join(MOD, "progs")
SOUND = os.path.join(MOD, "sound")
BKP_CHARS = os.path.join(ROOT, "_backups", "player_bodies_removed_2026-10-30", "progs")
TEMPLATE = os.path.join(HERE, "friends_showcase.template.html")
OUT_HTML = os.path.join(MOD, "custom_models_and_animations.html")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_all_custom_assets_html as ba


# --------------------------------------------------------------------------- Extended Packer Helper
def add_prebuilt_atlas(packer, key, uri, w, h, cols, rows, tile_w, tile_h, pad=0, count=None, nearest=False):
    """Registers an already-encoded WebGL2-safe (<4096x4096) WebP/PNG data URI without re-encoding."""
    ck = ("prebuilt", key)
    if ck in packer.tex_map:
        return packer.tex_map[ck]
    assert w <= 4096 and h <= 4096, f"Prebuilt atlas {key} ({w}x{h}) exceeds WebGL2 4096 limit!"
    cnt = int(count if count is not None else cols * rows)
    idx = len(packer.tex_list)
    packer.tex_map[ck] = idx
    packer.tex_list.append(dict(
        key=key,
        w=int(w),
        h=int(h),
        uri=uri,
        alpha=True,
        nearest=bool(nearest),
        noMip=True,
        wrap=False,
        cols=int(cols),
        rows=int(rows),
        tileW=int(tile_w),
        tileH=int(tile_h),
        pad=int(pad),
        count=cnt,
    ))
    return idx


def decode_data_uri_pil(uri):
    raw = base64.b64decode(uri.split(",", 1)[1])
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    im.load()
    return im


def slice_grid_tiles(im, dirs, frames, tw, th):
    tiles = []
    for d in range(dirs):
        y0 = d * th
        for f in range(frames):
            x0 = f * tw
            tiles.append(im.crop((x0, y0, x0 + tw, y0 + th)))
    return tiles


def make_sprite_suite_model(packer, model_id, badge, title, file, desc, default_tid, clips,
                            hw=36.0, hh=68.0, cat="featured", fmt="360° SUITE", turn_dirs=8, default_clip=0):
    vq = [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]]
    nq = [[-1.0, 0.0, 0.0]] * 4
    s_enc = ba.make_quad_surface(packer, "char_card", model_id, vq, nq, dict(
        tex=default_tid, unlit=True, alphaTest=True, alphaBlend=True, billboard=1,
    ))
    tot_frames = sum(int(c["sprMode"]["dirs"] * c["sprMode"]["fpd"]) for c in clips if "sprMode" in c)
    return dict(
        id=model_id,
        cat=cat,
        status="active",
        fmt=fmt,
        badge=badge,
        title=title,
        file=file,
        desc=desc,
        nf=max(1, tot_frames),
        nv=4,
        nt=2,
        bbox=[[-hw, -hw, 0.0], [hw, hw, hh]],
        isSprite=True,
        turnDirs=int(turn_dirs),
        turnSign=-1 if turn_dirs > 1 else 1,
        defaultClip=int(default_clip),
        surfaces=[s_enc],
        clips=clips,
    )


# --------------------------------------------------------------------------- 22-Clip Voice & Comedy Soundboard
def pack_friends_soundboard():
    specs = [
        (os.path.join(SOUND, "bryan", "noway.wav"),         '🛸 Bryan: "No Way!"',          "audio/wav"),
        (os.path.join(SOUND, "bryan", "detector.wav"),      '📡 Bryan: EMF Detector',       "audio/wav"),
        (os.path.join(SOUND, "bryan", "sense.wav"),         '🧠 Bryan: Psychic Sense',      "audio/wav"),
        (os.path.join(SOUND, "bryan", "portal_die.wav"),    '🌀 Bryan: Portal Vortex',      "audio/wav"),
        (os.path.join(MOD, "mrdiy_sprite", "mrdiy_laugh.mp3"), '🕺 Rob MR. D.I.Y. Laugh',   "audio/mpeg"),
        (os.path.join(SOUND, "wcannon", "wc_scream.wav"),   '🛞 Wheelman Scream!',          "audio/wav"),
        (os.path.join(SOUND, "john", "jwthrow.wav"),        '🌊 "JOHN WAVE!"',              "audio/wav"),
        (os.path.join(SOUND, "funny", "waveofhair.wav"),    '💇 "Wave of Hair!"',           "audio/wav"),
        (os.path.join(SOUND, "john", "jv00.wav"),           '🎙 John Quip #1',              "audio/wav"),
        (os.path.join(SOUND, "john", "jv01.wav"),           '🎙 John Quip #2',              "audio/wav"),
        (os.path.join(SOUND, "pickle", "surprise.wav"),     '🥒 "Pickle Surprise!"',        "audio/wav"),
        (os.path.join(SOUND, "floathead", "sight1.wav"),    '😱 Rob Head Sight #1',         "audio/wav"),
        (os.path.join(SOUND, "floathead", "sight2.wav"),    '👀 Rob Head Sight #2',         "audio/wav"),
        (os.path.join(SOUND, "hackmon", "hm_imin.wav"),     '💻 Hack: "I\'m In!"',          "audio/wav"),
        (os.path.join(SOUND, "hackmon", "hm_hacking.wav"),  '⌨️ "> HACKING" Alert',         "audio/wav"),
        (os.path.join(SOUND, "netsend", "wheres_disk.wav"), '💾 "Where\'s My Disk?!"',      "audio/wav"),
        (os.path.join(SOUND, "netsend", "ns_beep.wav"),     '📟 NetSend PC Beep',           "audio/wav"),
        (os.path.join(SOUND, "friends", "megamayan.wav"),   '⚙ "Mega-Mayan!"',             "audio/wav"),
        (os.path.join(SOUND, "friends", "johnnnny.wav"),    '📣 "JOHNNNNY!"',               "audio/wav"),
        (os.path.join(SOUND, "friends", "gowewd.wav"),      '😂 Friends: "Gowewd!"',        "audio/wav"),
        (os.path.join(SOUND, "larry", "it_wont_boot.wav"),  '🖥 Larry: "It Won\'t Boot!"',  "audio/wav"),
        (os.path.join(SOUND, "larry", "giggle_hacks.wav"),  '🤭 Larry: Giggle Hacks',       "audio/wav"),
    ]
    out = []
    for p, label, mime in specs:
        if os.path.isfile(p) and os.path.getsize(p) < 350_000:
            b64 = base64.b64encode(open(p, "rb").read()).decode("ascii")
            out.append(dict(label=label, uri=f"data:{mime};base64,{b64}"))
    return out


# --------------------------------------------------------------------------- Category 1: Featured Multi-Animation Suites
def build_bryan_suite(packer):
    adir = os.path.join(MOD, "bryan_sprite", "atlases")
    # (key, label, dirs, fpd, fps)
    bryan_specs = [
        ("whirl",              "🌀 Demon Whirlwind (360° 8×8f)",            8,  8, 12.0),
        ("run",                "🏃 Tinfoil Demon Chase (360° 8×6f)",        8,  6, 11.0),
        ("surge",              "⚡ Psychic Demon Surge (360° 8×8f)",        8,  8, 12.0),
        ("scan",               "📡 EMF Detector Scan (360° 8×6f)",          8,  6, 10.0),
        ("flat_earth",         "🌍 Flat-Earth Frisbee Toss (360° 8×24f)",   8, 24, 15.0),
        ("chemtrails",         "☁️ Chemtrail Vinegar Spray (360° 8×24f)",   8, 24, 15.0),
        ("five_g",             "📶 5G Faraday Shield Block (360° 8×24f)",   8, 24, 15.0),
        ("illuminati",         "👁️ Illuminati Eye Magnifier (360° 8×24f)",  8, 24, 15.0),
        ("corkboard",          "🧶 Red-Yarn Conspiracy Board (360° 8×24f)", 8, 24, 15.0),
        ("ufo_naruto",         "🛸 Area-51 Naruto Run + UFO (360° 8×24f)",  8, 24, 16.0),
        ("katana_anime",       "⚔️ Anime Katana Slash (360° 8×24f)",        8, 24, 16.0),
        ("lightsaber_paladin", "✨ Twin-Blade Lightsaber Spin (360° 8×24f)", 8, 24, 16.0),
        ("nunchuck_god",       "🥋 Flaming Nunchuck Fury (360° 8×24f)",     8, 24, 16.0),
        ("super_saiyan",       "🔥 Super Saiyan Tinfoil Aura (360° 8×24f)", 8, 24, 16.0),
        ("dnd_nat20",          "🎲 D&D Giant Nat-20 Crit (360° 8×24f)",     8, 24, 15.0),
        ("matrix_larp",        "🕶️ Matrix Bullet-Time + Zap (360° 8×24f)",  8, 24, 15.0),
        ("death",              "💀 Vortex Portal Death (32f)",              1, 32, 14.0),
        ("spr32",              "👾 In-Game Quake .SPR32 (360° 8×6f)",       8,  6, 11.0),
    ]
    clips = []
    first_tid = -1
    for key, label, dirs, fpd, fps in bryan_specs:
        wp = os.path.join(adir, f"{key}.webp")
        raw = open(wp, "rb").read()
        im = Image.open(io.BytesIO(raw)).convert("RGBA")
        w, h = im.size
        if w <= 4096 and h <= 4096:
            uri = "data:image/webp;base64," + base64.b64encode(raw).decode("ascii")
            tid = add_prebuilt_atlas(packer, f"bryan_{key}", uri, w, h, cols=fpd, rows=dirs, tile_w=320, tile_h=288, pad=0, count=dirs * fpd)
        else:
            tiles = slice_grid_tiles(im, dirs, fpd, 320, 288)
            max_td = 236 if dirs == 1 else 204
            tid = packer.add_atlas(f"bryan_{key}", tiles, max_tile_dim=max_td, pad=1, quality=80)
        if first_tid < 0:
            first_tid = tid
        clips.append(dict(
            id=key, label=label, start=0, count=fpd, fps=fps,
            sprMode=dict(base=0, dirs=dirs, fpd=fpd, fps=fps, tex=tid),
        ))
    return make_sprite_suite_model(
        packer,
        model_id="bryan_suite",
        badge="18 ANIMATIONS · 2,592 FRAMES",
        title='Bryan — "Tinfoil Hat & Demons" (All 18 360° & Conspiracy Animations)',
        file="bryan_sprite/atlases/*.webp + progs/bryan.spr32",
        desc="Complete 18-animation suite for Tinfoil-Hat Bryan & his orbiting Demons: 4 core combat loops, all 6 Conspiracy Theory attacks, all 6 Nerd/Weapon ultimate moves, Portal Death & SPR32!",
        default_tid=first_tid,
        clips=clips,
        hw=37.0,
        hh=66.5,
    )


def _warp_diva_ribbon_pil(src_rgba: np.ndarray, ph: float, swell: float = 0.0) -> Image.Image:
    """Renders a smooth base-planted S-curve inflatable wave / balloon-swell frame in 512x512 RGBA."""
    import cv2
    H, W = src_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    foot_y = 492.0
    hm = np.clip((foot_y - yg) / 468.0, 0.0, 1.0)  # 0 at base, 1 at crown top
    stretch = (1.0 + 0.068 * math.sin(2.0 * ph)) * (1.0 + 0.12 * swell)
    wave_x = (hm ** 1.38) * (17.5 * np.sin(ph - 1.90 * hm) + 5.5 * np.sin(2.0 * ph - 3.10 * hm)) * (1.0 - 0.45 * swell)
    shudder_x = (hm ** 1.1) * swell * 9.5 * math.sin(ph * 5.0)
    bulge = (1.0 / math.sqrt(1.0 + 0.068 * math.sin(2.0 * ph))) * (
        1.0 + 0.34 * swell * np.sin(np.pi * (hm ** 0.82))
    )
    src_x = 256.0 + (xg - 256.0 - wave_x - shudder_x) / np.maximum(bulge, 0.25)
    src_y = foot_y - (foot_y - yg) / stretch
    pm = src_rgba.astype(np.float32)
    pm[..., :3] *= pm[..., 3:4] / 255.0
    warped = cv2.remap(pm, src_x.astype(np.float32), src_y.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = np.clip(warped[..., 3], 0.0, 255.0)
    rgb = np.clip(warped[..., :3] / np.maximum(a[..., None] / 255.0, 1e-4), 0.0, 255.0)
    a_u8 = np.round(a).astype(np.uint8)
    rgb_u8 = np.round(rgb).astype(np.uint8)
    rgb_u8[a_u8 == 0] = 0
    return Image.fromarray(np.dstack([rgb_u8, a_u8]), "RGBA")


def build_pickle_diva_suite(packer):
    """Builds the 360° 16-angle multi-animation Pickle Surprise Diva showcase suite (`pickle_suite`)."""
    diva_dir = os.path.join(HERE, "out", "pickle_overhaul", "diva_views")
    # pose_sets[s][d] for s in 0..3, d in 0..15
    pose_sets = [
        [np.asarray(Image.open(os.path.join(diva_dir, f"diva_s{s}_v{d:02d}.png")).convert("RGBA")) for d in range(16)]
        for s in range(4)
    ]

    # Clip 1: 16 angles x 8f Wacky-Waving Inflatable Diva Dance
    wave_tiles = []
    expr_wave = [0, 0, 1, 0, 2, 2, 1, 0]
    for d in range(16):
        for f in range(8):
            ph = 2.0 * math.pi * (f / 8.0)
            wave_tiles.append(_warp_diva_ribbon_pil(pose_sets[expr_wave[f]][d], ph, swell=0.0))
    tid_wave = packer.add_atlas("pk_suite_wave16x8", wave_tiles, max_tile_dim=212, pad=1, quality=82)

    # Clip 2: 16 angles x 6f Cheeky Wink & Wild Pink-Tongue Taunt
    taunt_tiles = []
    expr_taunt = [0, 1, 1, 2, 2, 0]
    for d in range(16):
        for f in range(6):
            ph = 2.0 * math.pi * (f / 6.0)
            taunt_tiles.append(_warp_diva_ribbon_pil(pose_sets[expr_taunt[f]][d], ph * 0.5, swell=0.04 if expr_taunt[f] == 2 else 0.0))
    tid_taunt = packer.add_atlas("pk_suite_taunt16x6", taunt_tiles, max_tile_dim=224, pad=1, quality=83)

    # Clip 3: 16 angles x 8f "PICKLE SURPRISE!" Balloon Swell & 360° Giant Scream
    swell_tiles = []
    for d in range(16):
        for f in range(8):
            u = f / 7.0
            swell = math.sin(min(1.0, u * 1.25) * math.pi * 0.5) if u < 0.85 else 0.72
            s_set = 0 if f == 0 else (2 if f == 1 else 3)
            swell_tiles.append(_warp_diva_ribbon_pil(pose_sets[s_set][d], 2.0 * math.pi * u, swell=swell))
    tid_swell = packer.add_atlas("pk_suite_swell16x8", swell_tiles, max_tile_dim=212, pad=1, quality=82)

    # Clip 4: 16 angles x 1f Studio Turnaround (Rim-Decontaminated & Profile-Eye Repaired)
    turn_tiles = [Image.fromarray(pose_sets[0][d], "RGBA") for d in range(16)]
    tid_turn = packer.add_atlas("pk_suite_turn16x1", turn_tiles, max_tile_dim=256, pad=1, quality=86)

    clips = [
        dict(id="wave",  label="🥒 Wacky-Waving Inflatable Dance (360° 16×8f)", start=0, count=8, fps=11.0,
             sprMode=dict(base=0, dirs=16, fpd=8, fps=11.0, tex=tid_wave)),
        dict(id="taunt", label="👅 Cheeky Wink & Pink-Tongue Taunt (360° 16×6f)", start=0, count=6, fps=8.5,
             sprMode=dict(base=0, dirs=16, fpd=6, fps=8.5, tex=tid_taunt)),
        dict(id="swell", label='😱 "Pickle Surprise!" Balloon Swell & Scream (360° 16×8f)', start=0, count=8, fps=10.0,
             sprMode=dict(base=0, dirs=16, fpd=8, fps=10.0, tex=tid_swell)),
        dict(id="turn",  label="🔄 Crisp 16-Angle Studio Turnaround (360° 16×1f)", start=0, count=1, fps=8.0,
             sprMode=dict(base=0, dirs=16, fpd=1, fps=8.0, tex=tid_turn)),
    ]
    return make_sprite_suite_model(
        packer,
        model_id="pickle_suite",
        badge="4 ANIMATIONS · 16 ANGLES · 368f",
        title='Pickle Surprise Diva — 360° Inflatable Dance, Pink-Tongue Taunt & Giant Scream',
        file="progs/pickle.md3 + progs/pkv_s0..3_v00..15.png",
        desc="Overhauled 16-angle (360°) Pickle Surprise Diva suite: rim-decontaminated studio sRGB, repaired profile eyes, base-planted S-curve inflatable dance, cheeky wink, photographed pink-tongue taunt & full 16-angle pre-blast balloon swell!",
        default_tid=tid_wave,
        clips=clips,
        hw=34.0,
        hh=68.0,
        turn_dirs=16,
    )


def build_overhauled_pickle3d_asset(packer):
    """Loads the 61-frame 4-clip animated watertight 3D `pickle3d` hull (`pickle3d_anim.npz` + `pickle3d_srgb.png`)."""
    p_dir = os.path.join(HERE, "out", "pickle_overhaul")
    npz = np.load(os.path.join(p_dir, "pickle3d_anim.npz"), allow_pickle=False)
    all_v = npz["verts"].astype(np.float32)
    all_n = npz["norms"].astype(np.float32)
    uv_arr = npz["uvs"].astype(np.float32)
    tri_arr = npz["tris"].astype(np.int32)
    clips_meta = json.loads(str(npz["clips_json"]))

    tid = packer.add_tex_file(os.path.join(p_dir, "pickle3d_srgb.png"), max_dim=1024, quality=88)
    s_enc = ba.encode_surface(
        packer, "pickle3d_hull", "progs/pickle3d", uv_arr.tolist(), tri_arr.tolist(),
        all_v, all_n, dict(tex=tid, metallic=0.10, roughness=0.46, spec=0.38),
    )
    bmin = all_v[0].min(axis=0).round(2).tolist()
    bmax = all_v[0].max(axis=0).round(2).tolist()
    return dict(
        id="pickle3d",
        cat="chars3d",
        status="active",
        fmt="MD3 · 61f",
        badge="3D TOTEM · 4 CLIPS · 61f",
        title="3D Pickle Surprise Character (Waving Dance, Pogo-Sprint & Balloon Swell)",
        file="source/mm_tools/out/pickle_overhaul/pickle3d_anim.npz",
        desc="Watertight 3D marching-cubes Pickle Surprise character reconstructed from all 16 repaired studio-sRGB views with 4 multi-frame 3D animations (Wacky-Waving Dance, Bouncy Pogo-Sprint, 'Pickle Surprise!' Balloon Swell & Studio Pose)!",
        nf=int(all_v.shape[0]),
        nv=int(s_enc["nv"]),
        nt=int(s_enc["nt"]),
        az=-0.32,
        el=0.16,
        bbox=[bmin, bmax],
        surfaces=[s_enc],
        clips=clips_meta,
    )


def build_wheelman_actions_suite(packer):
    wt = open(os.path.join(MOD, "wheelman_animations.html"), "r", encoding="utf-8").read()
    anims = json.loads(re.search(r"const ANIMS\s*=\s*(\[.*?\]);", wt, re.S).group(1))
    uris = json.loads(re.search(r"const ATLAS_URIS\s*=\s*(\{.*?\});", wt, re.S).group(1))

    emoji_map = {
        "run_stuck":     ("🏃 Sprint w/ Stuck Wheels (360° 8×10f)",      14.0),
        "dance":         ("🕺 Barefoot Disco & Jig Dance (360° 8×12f)",  13.0),
        "turn_robot":    ("🤖 Nanotech Cyber-Robot Morph (360° 8×14f)",  12.0),
        "weightlift":    ("🏋️ Olympic Barbell Clean & Press (360° 8×12f)", 12.0),
        "hands_up_kick": ("🙌 Hands High & Scissor Kicks (360° 8×10f)",  13.0),
        "throw_rig":     ("🤾 Wind-Up & Hurl Wheel-Bar (360° 8×12f)",    13.0),
        "run_overhead":  ("🏃‍♂️ Overhead Barbell Sprint (360° 8×10f)",     14.0),
        "spin_bar":      ("🌪️ 360° Hammer-Throw Cyclone (360° 8×12f)",   14.0),
        "explode":       ("💥 Magma Swell & Gib Blast (360° 8×12f)",     12.0),
    }
    ordered_keys = [
        "run_stuck", "dance", "turn_robot", "weightlift", "hands_up_kick",
        "throw_rig", "run_overhead", "spin_bar", "explode",
    ]
    anim_by_key = {a["key"]: a for a in anims}
    clips = []
    first_tid = -1
    for key in ordered_keys:
        a = anim_by_key[key]
        fpd = int(a["n_frames"])
        im = decode_data_uri_pil(uris[key])
        tiles = slice_grid_tiles(im, 8, fpd, 360, 360)
        tid = packer.add_atlas(f"wm_act_{key}", tiles, max_tile_dim=216, pad=1, quality=81)
        if first_tid < 0:
            first_tid = tid
        lbl, fps = emoji_map[key]
        clips.append(dict(
            id=key, label=lbl, start=0, count=fpd, fps=fps,
            sprMode=dict(base=0, dirs=8, fpd=fpd, fps=fps, tex=tid),
        ))
    return make_sprite_suite_model(
        packer,
        model_id="wheelman_actions",
        badge="9 FULL 360° ACTIONS · 832f",
        title="Wheelman — All 9 Full-360° Action, Dance, Barbell & Cyber-Robot Animations",
        file="wheelman_animations.html + progs/wheelman_actions.spr32",
        desc="All 9 custom 8-direction (360°) Wheelman animations: upright sprint, disco jig, liquid-chrome Mecha-Wheelman transformation, Olympic barbell press, hurling rig, cyclone spin & gib blast!",
        default_tid=first_tid,
        clips=clips,
        hw=35.0,
        hh=70.0,
    )


def build_wheelman_spherical_suite(packer):
    ws = open(os.path.join(MOD, "wheelman_sprite", "index.html"), "r", encoding="utf-8").read()

    def load_ws_json(const_name):
        m = re.search(rf"const\s+{const_name}\s*=\s*(.*?);\s*\n", ws)
        assert m is not None, f"Missing {const_name} in wheelman_sprite/index.html"
        return json.loads(m.group(1))

    idle_b64    = load_ws_json("IDLE_B64")
    roll_b64    = load_ws_json("ROLL_B64")
    scream_b64  = load_ws_json("SCREAM_B64")
    above90_b64 = load_ws_json("ABOVE90_B64")
    above45_b64 = load_ws_json("ABOVE45_B64")
    below45_b64 = load_ws_json("BELOW45_B64")
    below90_b64 = load_ws_json("BELOW90_B64")

    t_roll = packer.add_atlas(
        "wm_sph_roll", [decode_data_uri_pil(u) for row in roll_b64 for u in row],
        max_tile_dim=216, pad=1, quality=82,
    )
    t_scream = packer.add_atlas(
        "wm_sph_scream", [decode_data_uri_pil(u) for row in scream_b64 for u in row],
        max_tile_dim=216, pad=1, quality=82,
    )
    t_idle = packer.add_atlas(
        "wm_sph_idle", [decode_data_uri_pil(u) for u in idle_b64],
        max_tile_dim=240, pad=1, quality=84,
    )
    t_ab90 = packer.add_atlas(
        "wm_sph_above90", [decode_data_uri_pil(u) for u in above90_b64["roll"]],
        max_tile_dim=224, pad=1, quality=83,
    )
    t_ab45 = packer.add_atlas(
        "wm_sph_above45", [decode_data_uri_pil(u) for u in above45_b64["scream"]],
        max_tile_dim=224, pad=1, quality=83,
    )
    t_bl45 = packer.add_atlas(
        "wm_sph_below45", [decode_data_uri_pil(u) for u in below45_b64["scream"]],
        max_tile_dim=224, pad=1, quality=83,
    )
    t_bl90 = packer.add_atlas(
        "wm_sph_below90", [decode_data_uri_pil(u) for u in below90_b64["roll"]],
        max_tile_dim=224, pad=1, quality=83,
    )

    # Un-tone progs/wheelman.spr32 (baked at 0.50 brightness for DarkPlaces HDR) back to 2.0x studio sRGB!
    sp = ba.parse_spr_frames(os.path.join(PROGS, "wheelman.spr32"))

    def untone_range(start_idx, count):
        out_imgs = []
        for idx in range(start_idx, start_idx + count):
            arr = np.asarray(sp["frames"][idx][0], dtype=np.float32).copy()
            arr[:, :, :3] = np.clip(np.rint(arr[:, :, :3] * 2.0), 0.0, 255.0)
            out_imgs.append(Image.fromarray(arr.astype(np.uint8), "RGBA"))
        return out_imgs

    t_stunt_fire = packer.add_atlas("wm_stunt_fire", untone_range(648, 48), max_tile_dim=224, pad=1, quality=82)
    t_stunt_long = packer.add_atlas("wm_stunt_long", untone_range(696, 48), max_tile_dim=240, pad=1, quality=82)
    t_stunt_jet  = packer.add_atlas("wm_stunt_jet",  untone_range(744, 48), max_tile_dim=224, pad=1, quality=82)

    t_exp1 = packer.add_atlas("wm_exp_tier1", untone_range(200, 112), max_tile_dim=212, pad=1, quality=80)
    t_exp2 = packer.add_atlas("wm_exp_tier2", untone_range(312, 112), max_tile_dim=212, pad=1, quality=80)
    t_exp3 = packer.add_atlas("wm_exp_tier3", untone_range(424, 112), max_tile_dim=212, pad=1, quality=80)
    t_exp4 = packer.add_atlas("wm_exp_tier4", untone_range(536, 112), max_tile_dim=212, pad=1, quality=80)

    clips = [
        dict(id="roll",       label="🛞 360° Rolling Loop (8×12f)",                start=0, count=12, fps=16.0, sprMode=dict(base=0, dirs=8, fpd=12, fps=16.0, tex=t_roll)),
        dict(id="scream",     label="😱 360° Screaming Roll (8×12f)",              start=0, count=12, fps=16.0, sprMode=dict(base=0, dirs=8, fpd=12, fps=16.0, tex=t_scream)),
        dict(id="stunt_fire", label="🔥 Stunt: Fire-Wheels Burnout (360° 8×6f)",   start=0, count=6,  fps=14.0, sprMode=dict(base=0, dirs=8, fpd=6,  fps=14.0, tex=t_stunt_fire)),
        dict(id="stunt_long", label="📏 Stunt: Super-Long Steamroller (360° 8×6f)",start=0, count=6,  fps=14.0, sprMode=dict(base=0, dirs=8, fpd=6,  fps=14.0, tex=t_stunt_long)),
        dict(id="stunt_jet",  label="🚀 Stunt: Jetpack Hover + Wheels (360° 8×6f)",start=0, count=6,  fps=14.0, sprMode=dict(base=0, dirs=8, fpd=6,  fps=14.0, tex=t_stunt_jet)),
        dict(id="exp1",       label="💣 Explosion Tier 1: Classic Gibs (8×14f)",   start=0, count=14, fps=14.0, sprMode=dict(base=0, dirs=8, fpd=14, fps=14.0, tex=t_exp1)),
        dict(id="exp2",       label="🔥 Explosion Tier 2: Napalm Fireball (8×14f)",start=0, count=14, fps=14.0, sprMode=dict(base=0, dirs=8, fpd=14, fps=14.0, tex=t_exp2)),
        dict(id="exp3",       label="☢️ Explosion Tier 3: Plasma Shockwave (8×14f)",start=0, count=14, fps=14.0, sprMode=dict(base=0, dirs=8, fpd=14, fps=14.0, tex=t_exp3)),
        dict(id="exp4",       label="🍄 Explosion Tier 4: Thermonuclear (8×14f)",  start=0, count=14, fps=14.0, sprMode=dict(base=0, dirs=8, fpd=14, fps=14.0, tex=t_exp4)),
        dict(id="above90",    label="🦅 Overhead +90° Top-Down View (12f)",        start=0, count=12, fps=15.0, sprMode=dict(base=0, dirs=1, fpd=12, fps=15.0, tex=t_ab90)),
        dict(id="above45",    label="📐 High +45° Screaming View (12f)",           start=0, count=12, fps=15.0, sprMode=dict(base=0, dirs=1, fpd=12, fps=15.0, tex=t_ab45)),
        dict(id="below45",    label="📐 Low -45° Screaming View (12f)",            start=0, count=12, fps=15.0, sprMode=dict(base=0, dirs=1, fpd=12, fps=15.0, tex=t_bl45)),
        dict(id="below90",    label="🕳️ Underfoot -90° Bottom-Up View (12f)",      start=0, count=12, fps=15.0, sprMode=dict(base=0, dirs=1, fpd=12, fps=15.0, tex=t_bl90)),
        dict(id="idle",       label="🧍 360° Idle Turnaround (8 Angles)",          start=0, count=1,  fps=10.0, sprMode=dict(base=0, dirs=8, fpd=1,  fps=10.0, tex=t_idle)),
    ]
    return make_sprite_suite_model(
        packer,
        model_id="wheelman_spherical",
        badge="14 CLIPS · SPHERICAL + 4 BOOMS",
        title="Wheelman — Spherical Angles (+90° to -90°), 3 Stunts & 4 Escalating Explosions",
        file="wheelman_sprite/index.html + progs/wheelman.spr32",
        desc="Complete spherical Wheelman showcase: 360° Rolling & Screaming loops, Fire-Wheels Burnout, Super-Long Bar, Jetpack Hover, 4 escalating 360° Explosion tiers, and Overhead/Underfoot views!",
        default_tid=t_roll,
        clips=clips,
        hw=35.0,
        hh=66.0,
    )


def build_char_inspector_suites(packer):
    cs = open(os.path.join(MOD, "character_sprites_inspector.html"), "r", encoding="utf-8").read()
    chars = json.loads(re.search(r"const CHARS\s*=\s*(\[.*?\]);\s*\n", cs, re.S).group(1))
    by_key = {c["key"]: c for c in chars}

    meta_map = {
        "paul": (
            'Paul — "PAAAAUUUUUL!" (7 High-FPS 360° & Action Animations)',
            "7-animation live-action & 360° suite for Paul: 128-frame 360° Scream-Run, signature 'PAAAAUUUUUL!' sonic scream, 28fps turbo sprint, 144-frame 360° jump, frontflip & 48f gib explosion!",
        ),
        "dennis": (
            'Dennis — "Reading For 30 Years" (7 High-FPS 360° & Action Animations)',
            "7-animation live-action & 360° suite for Dennis: 128-frame 360° suit run, signature 'Reading For 30 Years' lecture, turbo dash, 144-frame 360° jump, frontflip & 48f gib explosion!",
        ),
        "quakeguy": (
            'QuakeGuy — "Quake Shirt Ranger" (7 High-FPS 360° & Action Animations)',
            "7-animation live-action & 360° suite for QuakeGuy in the classic Quake tee: 128-frame 360° run, combat launch action, turbo sprint, 144-frame 360° jump, frontflip & 48f gib explosion!",
        ),
    }

    suites = []
    for key in ("paul", "dennis", "quakeguy"):
        c = by_key[key]
        title, desc = meta_map[key]
        gw, gh = int(c["gridW"]), int(c["gridH"])  # 210, 280
        sw, sh = int(c["seqW"]), int(c["seqH"])    # 270, 360

        t_run    = add_prebuilt_atlas(packer, f"{key}_run",    c["runAtlas"],    gw * 16, gh * 8, 16, 8, gw, gh, pad=0, count=128)
        t_act    = add_prebuilt_atlas(packer, f"{key}_act",    c["actAtlas"],    sw * 8,  sh * 3,  8, 3, sw, sh, pad=0, count=24)
        t_sprint = add_prebuilt_atlas(packer, f"{key}_sprint", c["sprintAtlas"], sw * 8,  sh * 3,  8, 3, sw, sh, pad=0, count=24)
        t_jump   = add_prebuilt_atlas(packer, f"{key}_jump",   c["jumpAtlas"],   gw * 18, gh * 8, 18, 8, gw, gh, pad=0, count=144)
        t_flip   = add_prebuilt_atlas(packer, f"{key}_flip",   c["flipAtlas"],   sw * 8,  sh * 4,  8, 4, sw, sh, pad=0, count=32)
        t_exp    = add_prebuilt_atlas(packer, f"{key}_exp",    c["expAtlas"],    sw * 8,  sh * 6,  8, 6, sw, sh, pad=0, count=48)
        t_idle   = add_prebuilt_atlas(packer, f"{key}_idle",   c["idleAtlas"],   sw * 8,  sh * 1,  8, 1, sw, sh, pad=0, count=8)

        clips = [
            dict(id="run",    label="🏃 360° Run Loop (8×16f @ 24fps)", start=0, count=16, fps=24.0, sprMode=dict(base=0, dirs=8, fpd=16, fps=24.0, tex=t_run)),
            dict(id="act",    label=c["actionLabel"],                   start=0, count=24, fps=20.0, sprMode=dict(base=0, dirs=1, fpd=24, fps=20.0, tex=t_act)),
            dict(id="sprint", label="💨 Turbo Sprint (24f @ 28fps)",    start=0, count=24, fps=28.0, sprMode=dict(base=0, dirs=1, fpd=24, fps=28.0, tex=t_sprint)),
            dict(id="jump",   label="🦘 360° Jump Arc (8×18f)",         start=0, count=18, fps=22.0, sprMode=dict(base=0, dirs=8, fpd=18, fps=22.0, tex=t_jump)),
            dict(id="flip",   label="🤸 Acrobatic Frontflip (32f)",     start=0, count=32, fps=28.0, sprMode=dict(base=0, dirs=1, fpd=32, fps=28.0, tex=t_flip)),
            dict(id="exp",    label="💥 Gib Explosion (48f)",           start=0, count=48, fps=24.0, sprMode=dict(base=0, dirs=1, fpd=48, fps=24.0, tex=t_exp)),
            dict(id="idle",   label="🧍 360° Idle Stand (8 Angles)",    start=0, count=1,  fps=10.0, sprMode=dict(base=0, dirs=8, fpd=1,  fps=10.0, tex=t_idle)),
        ]
        suites.append(make_sprite_suite_model(
            packer,
            model_id=f"{key}_suite",
            badge="7 ANIMATIONS · 408 FRAMES",
            title=title,
            file=f"character_sprites_inspector.html + {c['sprFile']}",
            desc=desc,
            default_tid=t_run,
            clips=clips,
            hw=26.25,
            hh=70.0,
        ))
    return suites


def build_mrdiy_suite(packer):
    mdir = os.path.join(MOD, "mrdiy_sprite")
    hero_imgs = [Image.open(os.path.join(mdir, f"mrdiy_{k:02d}.png")).convert("RGBA") for k in range(16)]
    turn_imgs = [
        Image.open(os.path.join(mdir, f"mrdiy_d{d}_f{f}.png")).convert("RGBA")
        for d in range(8) for f in range(6)
    ]
    t_hero = packer.add_atlas("mrdiy_hero_16", hero_imgs, max_tile_dim=272, pad=2, quality=85)
    t_turn = packer.add_atlas("mrdiy_turn_8x6", turn_imgs, max_tile_dim=224, pad=2, quality=84)
    clips = [
        dict(id="turn", label="🔄 360° Turnaround Boogie (8×6f)", start=0, count=6,  fps=12.0, sprMode=dict(base=0, dirs=8, fpd=6,  fps=12.0, tex=t_turn)),
        dict(id="hero", label="🕺 Full-Body Hero Dance (16f)",    start=0, count=16, fps=14.0, sprMode=dict(base=0, dirs=1, fpd=16, fps=14.0, tex=t_hero)),
    ]
    return make_sprite_suite_model(
        packer,
        model_id="mrdiy_suite",
        badge="MR. D.I.Y. · 360° + DANCE",
        title="Rob's MR. D.I.Y. Mascot (360° Turnaround Boogie & 16f Hero Dance)",
        file="mrdiy_sprite/*.png + progs/fr_mrdiy.spr32",
        desc="Rob's joyful yellow hammer-mascot MR. D.I.Y. character with both the 8-direction × 6-frame 360° boogie turnaround and the 16-frame full-body hero dance!",
        default_tid=t_turn,
        clips=clips,
        hw=32.5,
        hh=70.0,
    )


def build_rubber_finger_suite(packer):
    fdir = os.path.join(MOD, "rubber_finger_sprite")
    run_imgs = [
        Image.open(os.path.join(fdir, f"finger_d{d}_f{f}.png")).convert("RGBA")
        for d in range(8) for f in range(8)
    ]
    bonk_imgs = [Image.open(os.path.join(fdir, f"finger_bonk_{k:02d}.png")).convert("RGBA") for k in range(8)]
    idle_imgs = [Image.open(os.path.join(fdir, f"finger_idle_d{d}.png")).convert("RGBA") for d in range(8)]

    t_run  = packer.add_atlas("finger_run_8x8", run_imgs,  max_tile_dim=224, pad=2, quality=84)
    t_bonk = packer.add_atlas("finger_bonk_8",  bonk_imgs, max_tile_dim=256, pad=2, quality=85)
    t_idle = packer.add_atlas("finger_idle_8",  idle_imgs, max_tile_dim=232, pad=2, quality=85)

    clips = [
        dict(id="run",  label="🪱 360° Wiggling Run (8×8f)",         start=0, count=8, fps=14.0, sprMode=dict(base=0, dirs=8, fpd=8, fps=14.0, tex=t_run)),
        dict(id="bonk", label="🔨 Whipping Rubber Bonk Attack (8f)", start=0, count=8, fps=13.0, sprMode=dict(base=0, dirs=1, fpd=8, fps=13.0, tex=t_bonk)),
        dict(id="idle", label="🧍 360° Idle Turnaround (8 Angles)",  start=0, count=1, fps=10.0, sprMode=dict(base=0, dirs=8, fpd=1, fps=10.0, tex=t_idle)),
    ]
    return make_sprite_suite_model(
        packer,
        model_id="rubber_finger_suite",
        badge="3 ANIMATIONS · 80 FRAMES",
        title="Crazy Floppy Worm / Rubber Finger Maniac (360° Wiggle & Whip Bonk)",
        file="rubber_finger_sprite/*.png + progs/fr_finger.spr32",
        desc="Unhinged giant rubber-finger / floppy-worm character featuring a full 8-direction × 8-frame wiggling chase cycle, giant overhead whipping bonk attack, and 360° turnaround!",
        default_tid=t_run,
        clips=clips,
        hw=31.0,
        hh=70.0,
    )


# --------------------------------------------------------------------------- Special 3D Contraptions: Mystery Box & 8-Channel TV
def build_mystery_box_assets(packer):
    mbox_root = os.path.join(HERE, "out", "mystery_box")
    tex_dir = os.path.join(mbox_root, "textures")
    md3_dir = os.path.join(mbox_root, "md3")

    t_qmark = packer.add_tex_file(os.path.join(tex_dir, "mbox_qmark.png"), max_dim=768, force_png=True)
    t_glass = packer.add_tex_file(os.path.join(tex_dir, "mbox_glass.png"), max_dim=768, quality=88)
    t_gh3d  = packer.add_tex_file(os.path.join(tex_dir, "mbox_ghost_3d.png"), max_dim=512, quality=88)
    t_ghspr = packer.add_tex_file(os.path.join(tex_dir, "mbox_ghost_spr.png"), max_dim=768, quality=88)
    t_fx    = packer.add_tex_file(os.path.join(tex_dir, "mbox_fx.png"), max_dim=512, force_png=True)

    mbox_mats = {
        "crystal_core": dict(tex=t_qmark, unlit=True, alphaBlend=True),
        "ghost_3d":     dict(tex=t_gh3d,  unlit=True, additive=True),
        "ghost_spr":    dict(tex=t_ghspr, unlit=True, additive=True),
        "box_glass":    dict(tex=t_glass, unlit=True, alphaBlend=True),
        "box_qmark":    dict(tex=t_qmark, unlit=True, alphaBlend=True),
        "box_fx":       dict(tex=t_fx,    unlit=True, additive=True),
    }

    def pack_lifted_mbox(md3_name, meta_dict):
        m = ba.read_md3_fast(os.path.join(md3_dir, md3_name))
        glass_s = next(s for s in m["surfaces"] if s["name"] == "box_glass")
        z_shift = -float(glass_s["all_v"][0, :, 2].min()) + 6.0
        for s in m["surfaces"]:
            s["all_v"] = s["all_v"] + np.array([0.0, 0.0, z_shift], dtype=np.float32)

        surfs_out = []
        tot_v, tot_t = 0, 0
        for s in m["surfaces"]:
            sname = s["name"]
            tot_v += len(s["st"])
            tot_t += len(s["tris"])
            surfs_out.append(ba.encode_surface(packer, sname, s["shader"], s["st"], s["tris"], s["all_v"], s["all_n"], mbox_mats[sname]))

        gv0 = glass_s["all_v"][0]
        bmin = gv0.min(axis=0).round(2).tolist()
        bmax = gv0.max(axis=0).round(2).tolist()
        out = dict(
            fmt="MD3",
            status="active",
            nf=int(m["nframes"]),
            nv=int(tot_v),
            nt=int(tot_t),
            names=m["frame_names"],
            bbox=[bmin, bmax],
            surfaces=surfs_out,
        )
        out.update(meta_dict)
        return out

    hero_clips = [
        dict(id="all",      label="🔮 All Floating Visions Jukebox (192f)", start=0,   count=192, fps=11.0),
        dict(id="v_mm",     label="⚙ Vision: Mega-Man Rig (12f)",          start=0,   count=12,  fps=8.5),
        dict(id="v_wm",     label="🛞 Vision: Wheelman (12f)",              start=12,  count=12,  fps=8.5),
        dict(id="v_suit",   label="🕺 Vision: Suit Rider (12f)",            start=24,  count=12,  fps=8.5),
        dict(id="v_scis",   label="✂️ Vision: Giant Scissors (12f)",        start=60,  count=12,  fps=8.5),
        dict(id="v_squat",  label="😁 Vision: Squat Rider (12f)",           start=72,  count=12,  fps=8.5),
        dict(id="v_nspc",   label="💻 Vision: NetSend CRT PC (12f)",        start=96,  count=12,  fps=8.5),
        dict(id="v_pickle", label="🥒 Vision: Pickle Surprise (12f)",       start=108, count=12,  fps=8.5),
        dict(id="v_horse",  label="🐎 Vision: Golden West Horse (12f)",     start=120, count=12,  fps=8.5),
        dict(id="v_ears",   label="👂 Vision: Big-Ears 3D Head (12f)",      start=144, count=12,  fps=8.5),
    ]
    m_closeup = pack_lifted_mbox(
        "mysterybox_closeup.md3",
        dict(
            id="mysterybox_closeup",
            cat="contraptions3d",
            badge="CRYSTAL BALL · 192f",
            title="Mystery Box 3D Prismatic Crystal-Ball Cube (Floating 3D Visions)",
            file="source/mm_tools/out/mystery_box/md3/mysterybox_closeup.md3",
            desc="192-frame levitating iridescent crystal cube with orbiting '?' glyphs and holographic 3D & sprite visions materializing inside its core!",
            az=0.55,
            el=0.20,
            distMul=2.35,
            clips=hero_clips,
        ),
    )
    m_proj = pack_lifted_mbox(
        "proj_mysterybox.md3",
        dict(
            id="proj_mysterybox",
            cat="contraptions3d",
            badge="COMET CUBE · 32f",
            title="Mystery Box Tumbling Comet Cube & Spark Trail",
            file="source/mm_tools/out/mystery_box/md3/proj_mysterybox.md3",
            desc="32-frame tumbling prismatic crystal cube surrounded by swirling plasma comet ribbons!",
            az=0.62,
            el=0.22,
            distMul=2.45,
            clips=[dict(id="spin", label="☄️ Tumbling Comet Loop (32f)", start=0, count=32, fps=14.0)],
        ),
    )
    return [m_closeup, m_proj]


def make_box_mesh(x0, y0, z0, x1, y1, z1):
    faces = [
        ([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], (-1, 0, 0)),
        ([(x1, y1, z0), (x1, y0, z0), (x1, y0, z1), (x1, y1, z1)], (+1, 0, 0)),
        ([(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)], (0, -1, 0)),
        ([(x1, y1, z0), (x1, y1, z1), (x0, y1, z1), (x0, y1, z0)], (0, +1, 0)),
        ([(x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)], (0, 0, +1)),
        ([(x0, y1, z0), (x0, y0, z0), (x1, y0, z0), (x1, y1, z0)], (0, 0, -1)),
    ]
    vs, ns, uvs, tris = [], [], [], []
    for quad, nrm in faces:
        b = len(vs)
        vs.extend(quad)
        ns.extend([nrm] * 4)
        uvs.extend([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
        tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])
    return vs, ns, uvs, tris


def build_bktv_asset(packer):
    m = ba.read_md3_fast(os.path.join(PROGS, "bk_tvscr.md3"))
    s_scr = m["surfaces"][0]
    z_lift = 24.0
    v_scr = s_scr["all_v"] + np.array([0.0, 0.0, z_lift], dtype=np.float32)

    bktv_dir = os.path.join(PROGS, "bktv")
    ch_tids = []
    for ch in range(8):
        all_jpgs = sorted(glob.glob(os.path.join(bktv_dir, f"v{ch}_*.jpg")))
        step = max(1, len(all_jpgs) // 48)
        picked = all_jpgs[::step][:48]
        frames_pil = []
        for jp in picked:
            arr = np.asarray(Image.open(jp).convert("RGB"), dtype=np.float32)
            # Undo BRIGHT=0.55 baked for DarkPlaces x2.5 scene lighting
            arr = np.clip(np.rint(arr * (1.0 / 0.55)), 0.0, 255.0).astype(np.uint8)
            frames_pil.append(Image.fromarray(arr, "RGB").convert("RGBA"))
        tid = packer.add_atlas(f"bktv_ch{ch + 1}", frames_pil, max_tile_dim=160, pad=1, quality=82)
        ch_tids.append(tid)

    s_scr_enc = ba.encode_surface(
        packer, "bk_tvscr", "progs/bktv_ch1", s_scr["st"], s_scr["tris"], v_scr, s_scr["all_n"],
        dict(tex=ch_tids[0], animFps=10.0, unlit=True),
    )

    # Dark 3D TV cabinet & pedestal stand behind the screen so 360° orbiting looks great
    cab_im = Image.new("RGB", (32, 32), (28, 33, 43))
    t_cab = packer.add_tex_pil(("solid", "tv_cabinet"), "tv_cabinet_matte", cab_im, max_dim=32, force_png=True)
    boxes = [
        make_box_mesh(-3.6, -26.0, 4.0, -0.15, +26.0, 44.0),   # main flatscreen housing
        make_box_mesh(-2.8,  -3.2, 0.8, -0.80,  +3.2,  4.2),   # neck post
        make_box_mesh(-6.5, -13.0, 0.0, +3.50, +13.0,  1.1),   # tabletop/floor base
    ]
    bv, bn, buv, btr = [], [], [], []
    for vs, ns, uvs, trs in boxes:
        off = len(bv)
        bv.extend(vs)
        bn.extend(ns)
        buv.extend(uvs)
        btr.extend([(a + off, b + off, c + off) for a, b, c in trs])
    bv_np = np.asarray(bv, dtype=np.float32)
    bn_np = np.asarray(bn, dtype=np.float32)
    s_cab_enc = ba.encode_surface(
        packer, "tv_cabinet_stand", "tv_cabinet", buv, btr, bv_np[None, ...], bn_np[None, ...],
        dict(tex=t_cab, metallic=0.35, roughness=0.42, spec=0.50),
    )

    pts = np.vstack([v_scr[0], bv_np])
    skins = [
        dict(label=f"📺 Ch {ch + 1}", map={"bk_tvscr": dict(tex=ch_tids[ch], animFps=10.0)})
        for ch in range(8)
    ]
    return dict(
        id="bk_tvscr",
        cat="contraptions3d",
        status="active",
        fmt="MD3 + VIDEO",
        badge="8 VIDEO CHANNELS · TV",
        title="LAN-Party 3D Flatscreen TV (All 8 Custom Video Channels!)",
        file="progs/bk_tvscr.md3 + progs/bktv/v0..v7_*.jpg",
        desc="Custom in-world Bakersfield LAN TV screen loaded with all 8 custom video channels — click Ch 1 through Ch 8 in the Skins / Channels bar to surf!",
        nf=1,
        nv=int(s_scr_enc["nv"] + s_cab_enc["nv"]),
        nt=int(s_scr_enc["nt"] + s_cab_enc["nt"]),
        az=0.0,
        el=0.10,
        bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
        skins=skins,
        surfaces=[s_cab_enc, s_scr_enc],
        clips=[dict(id="tv", label="📺 Live 10fps Broadcast Loop", start=0, count=1, fps=10.0, lie=True)],
    )


def main():
    print("1. Packing 22-clip Custom Voice & Comedy Soundboard...", flush=True)
    sounds = pack_friends_soundboard()
    packer = ba.ArenaPacker()
    models_out = []

    # Shared studio sRGB textures
    t_jw_scream = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_scream_srgb.png"), max_dim=1024, quality=88)
    t_jw_calm   = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_calm_srgb.png"), max_dim=768, quality=88)
    t_jw_fed    = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_fedora_srgb.png"), max_dim=512, quality=88)
    t_jw_wave   = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_wave_srgb.png"), max_dim=256, quality=88)
    t_jw_fx     = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_fx_srgb.png"), max_dim=256, force_png=True)

    t_bigears   = packer.add_tex_file(os.path.join(HERE, "out", "skyveh", "bigears_srgb.png"), max_dim=1024, quality=88)
    t_pinklady  = packer.add_tex_file(os.path.join(HERE, "out", "skyveh", "pinklady3d_srgb.png"), max_dim=1024, quality=88)

    t_mm_chr    = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_chrome_axle.png"), max_dim=512, quality=88)
    t_mm_whl    = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_wheel.png"), max_dim=512, quality=88)
    t_mm_scan   = packer.add_tex_file(os.path.join(PROGS, "megaman.png"), max_dim=768, quality=86, lift=1.60)

    # ==================== CATEGORY 1: FEATURED MULTI-ANIMATION CHARACTER SUITES ====================
    print("2. Packing Category 1 (featured): 9 Multi-Animation Character Showcases...", flush=True)
    models_out.append(build_bryan_suite(packer))
    models_out.append(build_pickle_diva_suite(packer))
    models_out.append(build_wheelman_actions_suite(packer))
    models_out.append(build_wheelman_spherical_suite(packer))
    models_out.extend(build_char_inspector_suites(packer))
    models_out.append(build_mrdiy_suite(packer))
    models_out.append(build_rubber_finger_suite(packer))

    # ==================== CATEGORY 2: CUSTOM 3D CHARACTERS, HEADS & RIDERS ====================
    print("3. Packing Category 2 (chars3d): 16 Custom 3D Characters, Sculpted Heads & Riders...", flush=True)
    rider_clips = [
        dict(id="drive",  label="🛞 Drive Roll (16f)",      start=12, count=16, fps=14.0),
        dict(id="idle",   label="🧍 Idle Balance (12f)",    start=0,  count=12, fps=10.0),
        dict(id="boost",  label="🚀 Turbo Boost (12f)",     start=28, count=12, fps=16.0),
        dict(id="charge", label="😤 Monster Charge (12f)",  start=40, count=12, fps=15.0),
        dict(id="slam",   label="💥 Wheelie Slam (8f)",     start=52, count=8,  fps=14.0),
        dict(id="all",    label="🎬 All 60f",               start=0,  count=60, fps=14.0),
    ]
    t_suit_h  = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_suit_human_srgb.png"), max_dim=1024, quality=88)
    t_suit_r  = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_suit_rig_srgb.png"), max_dim=768, quality=88)
    t_squat_h = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_squat_human_srgb.png"), max_dim=1024, quality=88)
    t_squat_g = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_squat_human_grin_srgb.png"), max_dim=1024, quality=88)
    t_squat_r = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_squat_rig_srgb.png"), max_dim=768, quality=88)
    t_rid_fx  = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_rider_fx_srgb.png"), max_dim=256, force_png=True)

    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "mm_suit_rider.md3"),
        dict(
            id="mm_suit_rider", cat="chars3d", badge="MEGA-MAN RIDER · 60f",
            title="Suit Guy Riding Mega-Man Contraption",
            file="progs/mm_suit_rider.md3",
            desc="60-frame articulated 3D Suit Guy balanced atop a twin-wheel Mega-Man rig with drive, turbo boost, monster charge & wheelie-slam animations!",
            clips=rider_clips,
        ),
        surf_mats={
            "progs/mm_suit_human": dict(tex=t_suit_h, metallic=0.06, roughness=0.58, spec=0.28),
            "progs/mm_suit_rig":   dict(tex=t_suit_r, metallic=0.55, roughness=0.28, spec=0.72),
            "progs/mm_rider_fx":   dict(tex=t_rid_fx, unlit=True, additive=True),
        },
        allow_rigid=False,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "mm_squat_rider.md3"),
        dict(
            id="mm_squat_rider", cat="chars3d", badge="MEGA-MAN RIDER · 2 SKINS",
            title="Squat Rider on Mega-Man Rig (Neutral & Grin Skins)",
            file="progs/mm_squat_rider.md3",
            desc="60-frame low-slung 3D Squat Rider gripping the Mega-Man axle with 2 switchable facial skins (Focused Neutral & Manic Grin)!",
            clips=rider_clips,
            skins=[
                dict(label="😐 Neutral Face", map={"rider_human": dict(tex=t_squat_h)}),
                dict(label="😁 Grinning Face", map={"rider_human": dict(tex=t_squat_g)}),
            ],
        ),
        surf_mats={
            "progs/mm_squat_human": dict(tex=t_squat_h, metallic=0.06, roughness=0.58, spec=0.28),
            "progs/mm_squat_rig":   dict(tex=t_squat_r, metallic=0.55, roughness=0.28, spec=0.72),
            "progs/mm_rider_fx":    dict(tex=t_rid_fx,  unlit=True, additive=True),
        },
        allow_rigid=False,
    ))

    m_pl3d = ba.build_pinklady3d_asset(packer, t_pinklady)
    m_pl3d["cat"] = "chars3d"
    models_out.append(m_pl3d)

    models_out.append(ba.pack_mdl_asset(
        packer, os.path.join(PROGS, "floathead.mdl"),
        dict(
            id="floathead", cat="chars3d", badge="MONSTER · 2 SKINS · 20f",
            title="Rob Dob Floating 3D Head Monster (v2 Turnaround)",
            file="progs/floathead.mdl",
            desc="20-frame hovering 3D Rob Dob monster reconstructed from 6 turnaround angles with articulated jaw drop & automatic screaming mouth skin!",
            az=-0.28, el=0.14, frameSkin=8,
        ),
        skin_labels=["🙂 Closed Mouth (Idle)", "😱 Screaming Open Jaw"],
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "johnhead3d.md3"),
        dict(
            id="johnhead3d", cat="chars3d", badge="3D HEAD · SCREAMING JOHN",
            title="John Wave Screaming Flying 3D Head",
            file="progs/johnhead3d.md3",
            desc="4,837-vertex 3D visual-hull head carved from 113 green-screen turntable frames of John screaming!",
            az=-0.28, el=0.14,
        ),
        surf_mats={"progs/johnhead3d": dict(tex=t_jw_scream, metallic=0.05, roughness=0.60, spec=0.28)},
    ))

    m_calm = ba.build_calm_john_asset(packer, t_jw_calm)
    m_calm["cat"] = "chars3d"
    models_out.append(m_calm)

    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "bigears.md3"),
        dict(
            id="bigears", cat="chars3d", badge="3D HEAD · BIG EARS",
            title="Giant-Eared Screaming 3D Floating Head",
            file="progs/bigears.md3",
            desc="Watertight 4,562-vertex / 5,600-triangle 3D head carved from 48 turntable views with sculpted giant cupped ears!",
            az=-0.34, el=0.10,
        ),
        surf_mats={"progs/bigears": dict(tex=t_bigears, metallic=0.05, roughness=0.60, spec=0.26)},
    ))
    models_out.append(ba.pack_mdl_asset(
        packer, os.path.join(PROGS, "grenade.mdl"),
        dict(
            id="john_bouncing_head", cat="chars3d", badge="3D SCULPTED HEAD",
            title="John Wave 3D Bouncing Portrait Head",
            file="progs/grenade.mdl + grenade.mdl_0.tga",
            desc="Custom 32×32 ring-mesh 3D John head wrapped in a high-res front/back TGA portrait skin.",
            az=-0.28, el=0.16,
        ),
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(HERE, "out", "pocket_rocket", "md3", "pocket_rocket_char.md3"),
        dict(
            id="pocket_rocket_char", cat="chars3d", badge="FULL-BODY 3D · 16kf",
            title="Miniature Superhero Full-Body 3D Character",
            file="source/mm_tools/out/pocket_rocket/md3/pocket_rocket_char.md3",
            desc="23,159-vertex full-body 3D character in pink crop-top, jeans & sneakers with animated pose sequence.",
            clips=[dict(id="all", label="🎬 Character Sequence (16kf)", start=0, count=16, fps=6.0)],
        ),
        allow_rigid=False, frame_stride=2,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(HERE, "out", "pocket_rocket", "md3", "pocket_rocket_proj.md3"),
        dict(
            id="pocket_rocket_proj", cat="chars3d", badge="SUPERHERO FLIGHT · 8kf",
            title="Flying 3D Character w/ Anime Speedlines",
            file="source/mm_tools/out/pocket_rocket/md3/pocket_rocket_proj.md3",
            desc="Horizontal supersonic flying 3D character surrounded by additive anime speedlines!",
            clips=[dict(id="fly", label="🚀 Supersonic Flight (8kf)", start=0, count=8, fps=7.0)],
        ),
        allow_rigid=False, frame_stride=2,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(HERE, "out", "removed_guns_src", "girl_assets", "progs", "girl.md3"),
        dict(
            id="girl", cat="chars3d", badge="26K-TRI 3D HULL · 8f",
            title="Full-Body 3D Running Chaser (26,000-Triangle Hull)",
            file="source/mm_tools/out/removed_guns_src/girl_assets/progs/girl.md3",
            desc="Full-body 3D human reconstructed from video across 5 MD3 surfaces with an 8-frame running lean/bob cycle.",
            az=-0.28, el=0.18,
            clips=[dict(id="run", label="🏃 Run Cycle (8f)", start=0, count=8, fps=10.0)],
        ),
        allow_rigid=False,
    ))

    player143_clips = [
        dict(id="stand", label="🧍 Stand (5f)",         start=12,  count=5,   fps=9.0),
        dict(id="run",   label="🏃 Sprint Cycle (6f)",  start=6,   count=6,   fps=11.0),
        dict(id="walk",  label="🚶 Stride Cycle (6f)",  start=0,   count=6,   fps=11.0),
        dict(id="act",   label="⚡ Action Pose (6f)",   start=113, count=6,   fps=11.0),
        dict(id="swing", label="💪 Overhead Swing (6f)", start=119, count=6,   fps=11.0),
        dict(id="pain",  label="💢 Stagger / Pain (6f)",start=29,  count=6,   fps=10.0),
        dict(id="death", label="💀 Dramatic Collapse (11f)", start=50, count=11, fps=10.0),
        dict(id="all",   label="🎬 All 143 Frames",     start=0,   count=143, fps=11.0),
    ]
    for cid, title, fn, desc in [
        ("suitguy", "Suit Guy (143-Frame Custom 3D Character)", "suitguy.mdl",
         "Full 143-frame 3D character model built from front & back studio photos in a dark business suit + high-color TGA skin."),
        ("robeguy", "Robe Guy (143-Frame Custom 3D Character)", "robeguy.mdl",
         "Full 143-frame 3D character model built from front & back studio photos in a white bathrobe + high-color TGA skin."),
        ("wifeguy", "Wife (143-Frame Custom 3D Character)", "wifeguy.mdl",
         "Full 143-frame 3D character model built from front & back studio photos + custom high-color TGA skin."),
    ]:
        models_out.append(ba.pack_mdl_asset(
            packer, os.path.join(BKP_CHARS, fn),
            dict(
                id=cid, cat="chars3d", badge="3D CHARACTER · 143f",
                title=title,
                file=f"_backups/player_bodies_removed_2026-10-30/progs/{fn}",
                desc=desc, az=-0.28, el=0.18, clips=player143_clips,
            ),
        ))

    models_out.append(ba.pack_mdl_asset(
        packer, os.path.join(HERE, "preview", "floathead", "floathead.mdl"),
        dict(
            id="floathead_v1", cat="chars3d", badge="PROTOTYPE v1 · 20f",
            title="Rob Dob Floating 3D Head (v1 Single-Photo Prototype)",
            file="source/mm_tools/preview/floathead/floathead.mdl",
            desc="Original single-photograph 3D Rob Dob head prototype with 20 idle/rush/pain frames and dual mouth skins.",
            az=-0.28, el=0.14, frameSkin=8,
        ),
        skin_labels=["🙂 Closed Mouth", "😱 Screaming Jaw"],
    ))

    models_out.append(build_overhauled_pickle3d_asset(packer))

    # ==================== CATEGORY 3: 3D CONTRAPTIONS, MYSTERY CUBE, TV, PROPS & FX ====================
    print("4. Packing Category 3 (contraptions3d): Mystery Cube, Flying John Craft, 8-Ch TV, Bots & FX...", flush=True)
    models_out.extend(build_mystery_box_assets(packer))

    jw_mats = {
        "progs/jw_air_scream": dict(tex=t_jw_scream, metallic=0.05, roughness=0.62, spec=0.28),
        "progs/jw_air_calm":   dict(tex=t_jw_calm,   metallic=0.05, roughness=0.60, spec=0.28),
        "progs/jw_air_fedora": dict(tex=t_jw_fed,    metallic=0.04, roughness=0.76, spec=0.24),
        "progs/jw_air_chrome": dict(tex=t_mm_chr,    metallic=0.88, roughness=0.17, spec=0.96),
        "progs/jw_air_wheel":  dict(tex=t_mm_whl,    metallic=0.16, roughness=0.52, spec=0.42),
        "progs/jw_air_wave":   dict(tex=t_jw_wave,   unlit=True),
        "progs/jw_air_fx":     dict(tex=t_jw_fx,     unlit=True, additive=True),
    }
    jw_clips = [
        dict(id="cruise", label="✈ Cruise (16f)",           start=0,  count=8,  fps=6.0),
        dict(id="boost",  label="🔥 Scream Boost (16f)",    start=8,  count=8,  fps=9.0),
        dict(id="roll",   label="🌀 360° Barrel Roll (16f)", start=28, count=8,  fps=8.0),
        dict(id="hover",  label="🚁 VTOL Hover (12f)",      start=16, count=6,  fps=5.0),
        dict(id="rest",   label="🛬 Landed / Snoring (12f)",start=22, count=6,  fps=4.0, lie=True),
        dict(id="all",    label="🎬 All 72f (36kf)",        start=0,  count=36, fps=6.5),
    ]
    for vid, badge, title, fn_disp, desc in [
        ("jw_air_v1", "FLYING JOHN V1 · 72f", 'F-69 "The Mouth-Breather" Giant-John Biplane', "progs/jw_air_v1.md3",
         "Crimson-Fedora Giant Bobblehead John biplane with Gold Tire-Monocle, Mega-Man Cigar puffing 3D surf rings, mustache rotors & flapping henchmen wings!"),
        ("jw_air_v2", "FLYING JOHN V2 · 72f", 'SR-99 "In-One-Ear" Giant-John Rocket Jet', "progs/jw_air_v2.md3",
         "Mach-5 Mega-Man Rocket spearing out of Giant John's mouth and skewering him ear-to-ear with tilt-rotor headphone tires & twin ramjets!"),
        ("jw_air_v3", "FLYING JOHN V3 · 72f", 'CH-99 "The Hair-icopter" Twin-John Chinook', "progs/jw_air_v3.md3",
         "Push-Me-Pull-You twin-rotor helicopter sculpted from Deadpan Lush-Hair Johns fore & aft plus a Tire-Shades Biker midship!"),
    ]:
        models_out.append(ba.pack_md3_asset(
            packer, os.path.join(PROGS, f"{vid}.md3"),
            dict(id=vid, cat="contraptions3d", badge=badge, title=title, file=fn_disp, desc=desc, clips=jw_clips),
            surf_mats=jw_mats, allow_rigid=False, frame_stride=2, bbox_frames=(0, 22),
        ))

    models_out.append(build_bktv_asset(packer))

    # NetSend Retro CRT Desktop PC + 8 Skins
    tid_ns_loop, ord_ns_loop = ba.build_anim_atlas_from_files(
        packer, "netsend_scr_loop16", [os.path.join(PROGS, f"netsend_s_l{k:02d}.png") for k in range(16)], max_tile_dim=256)
    tid_ns_off   = packer.add_tex_file(os.path.join(PROGS, "netsend_s_off.png"), max_dim=256)
    tid_ns_noise, ord_ns_noise = ba.build_anim_atlas_from_files(
        packer, "netsend_scr_noise", [os.path.join(PROGS, f"netsend_s_n{k}.png") for k in range(3)], max_tile_dim=256)
    tid_ns_init, ord_ns_init = ba.build_anim_atlas_from_files(
        packer, "netsend_scr_init", [os.path.join(PROGS, f"netsend_s_init{k}.png") for k in range(2)], max_tile_dim=256)
    tid_ns_lol, ord_ns_lol = ba.build_anim_atlas_from_files(
        packer, "netsend_scr_lol", [os.path.join(PROGS, f"netsend_s_lol{k}.png") for k in range(2)], max_tile_dim=256)
    tid_ns_fst, ord_ns_fst = ba.build_anim_atlas_from_files(
        packer, "netsend_scr_fst", [os.path.join(PROGS, f"netsend_s_fst{k}.png") for k in range(2)], max_tile_dim=256)
    tid_ns_dot, ord_ns_dot = ba.build_anim_atlas_from_files(
        packer, "netsend_scr_dot", [os.path.join(PROGS, f"netsend_s_dot{k}.png") for k in range(2)], max_tile_dim=256)

    m_ns_arc = ba.read_md3_fast(os.path.join(PROGS, "netsend_arc.md3"))
    sa_ns = m_ns_arc["surfaces"][0]
    t_ns_arc = packer.add_tex_file(os.path.join(PROGS, "netsend_arc.png"), max_dim=256, force_png=True)
    s_ns_arc_overlay = ba.encode_surface(
        packer, "electric_arc_cage", sa_ns["shader"], sa_ns["st"], sa_ns["tris"], sa_ns["all_v"], sa_ns["all_n"],
        dict(tex=t_ns_arc, unlit=True, additive=True),
    )
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "netsend_pc.md3"),
        dict(
            id="netsend_pc", cat="contraptions3d", badge="RETRO CRT PC · 8 SKINS",
            title="NetSend 90s Beige CRT Desktop PC (All 8 Screen & Overload States)",
            file="progs/netsend_pc.md3 + netsend_arc.md3",
            desc="50-frame retro beige PC tower & CRT monitor spitting floppy disks—switch all 7 CRT boot/noise/LOL.BAT screens plus 3D Overload Electric Arcs!",
            clips=[dict(id="all", label="💾 Floppy Eject Loop (50f)", start=0, count=50, fps=15.0, lie=True)],
            skins=[
                dict(label="0: LOL Loop (16f)",       map={"netsend_screen": dict(tex=tid_ns_loop,  animFps=6.0,  animOrder=ord_ns_loop),  "electric_arc_cage": dict(nodraw=True)}),
                dict(label="1: CRT Off",              map={"netsend_screen": dict(tex=tid_ns_off,   animFps=0.0,  animOrder=None),         "electric_arc_cage": dict(nodraw=True)}),
                dict(label="2: Static Noise",         map={"netsend_screen": dict(tex=tid_ns_noise, animFps=14.0, animOrder=ord_ns_noise), "electric_arc_cage": dict(nodraw=True)}),
                dict(label="3: BIOS Init",            map={"netsend_screen": dict(tex=tid_ns_init,  animFps=4.0,  animOrder=ord_ns_init),  "electric_arc_cage": dict(nodraw=True)}),
                dict(label="4: LOL.BAT Alert",        map={"netsend_screen": dict(tex=tid_ns_lol,   animFps=4.0,  animOrder=ord_ns_lol),   "electric_arc_cage": dict(nodraw=True)}),
                dict(label="5: First Boot",           map={"netsend_screen": dict(tex=tid_ns_fst,   animFps=3.0,  animOrder=ord_ns_fst),   "electric_arc_cage": dict(nodraw=True)}),
                dict(label="6: Cursor Blink",         map={"netsend_screen": dict(tex=tid_ns_dot,   animFps=3.0,  animOrder=ord_ns_dot),   "electric_arc_cage": dict(nodraw=True)}),
                dict(label="7: ⚡ Overload + 3D Arcs", map={"netsend_screen": dict(tex=tid_ns_loop,  animFps=9.0,  animOrder=ord_ns_loop),  "electric_arc_cage": dict(nodraw=False)}),
            ],
        ),
        surf_mats={"netsend_screen": dict(tex=tid_ns_loop, animFps=6.0, animOrder=ord_ns_loop, unlit=True)},
        allow_rigid=False, lift_default=1.40, extra_surfaces=[s_ns_arc_overlay],
    ))

    # Jetpack
    jp_plumes = [os.path.join(PROGS, f"jetpack_plume_{k}.png") for k in range(4)]
    tid_jp_plume, ord_jp_plume = ba.build_anim_atlas_from_files(packer, "jetpack_plume_4f", jp_plumes, max_tile_dim=256)
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "jetpack.md3"),
        dict(
            id="jetpack", cat="contraptions3d", badge="FLIGHT PACK · 16f",
            title="JP-02 Twin-Turbine Rocket Jetpack",
            file="progs/jetpack.md3",
            desc="9-surface wearable rocket pack with brushed titanium tanks, cyan plasma window, PSI gauge & 4-frame shock-diamond exhaust plumes!",
            az=2.55, el=0.16,
            clips=[
                dict(id="thrust", label="🔥 Afterburner Thrust (8f)", start=0, count=8,  fps=15.0),
                dict(id="idle",   label="🕯 Standby Pilot Flame (8f)",start=8, count=8,  fps=10.0, lie=True),
                dict(id="all",    label="🎬 All 16f",                 start=0, count=16, fps=14.0),
            ],
        ),
        surf_mats={
            "progs/jetpack_plume": dict(tex=tid_jp_plume, animFps=18.0, animOrder=ord_jp_plume, unlit=True, additive=True),
            "progs/jetpack_glow":  dict(tex=packer.add_tex_file(os.path.join(PROGS, "jetpack_glow.png"), max_dim=256), unlit=True),
            "progs/jetpack_dial":  dict(tex=packer.add_tex_file(os.path.join(PROGS, "jetpack_dial.png"), max_dim=256), unlit=True),
        },
        allow_rigid=False, bbox_frames=list(range(0, 8)),
    ))

    # Mega-Man Bots, Wheelman Barbell, Bronze Horse, Trashcan, CRT Monitor, Fedora
    mmw_rig_mats = {
        "progs/mmw_chrome_axle": dict(tex=t_mm_chr, metallic=0.88, roughness=0.17, spec=0.95),
        "progs/mmw_wheel":       dict(tex=t_mm_whl, metallic=0.16, roughness=0.52, spec=0.42),
    }
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(HERE, "out", "megaman_weapon", "megaman_clean.md3"),
        dict(
            id="megaman_clean", cat="contraptions3d", badge="HIGH-DETAIL RIG · 16f",
            title="Mega-Man Precision Chrome Bar & Dish-Tires Contraption",
            file="source/mm_tools/out/megaman_weapon/megaman_clean.md3",
            desc="Precision-lathed gleaming chrome bullet shaft, TIG cross-axle, cotter pins & 5-ribbed pneumatic rubber tires on concave white dish rims!",
            clips=[dict(id="spin", label="⚙ Dish-Tire Spin (16f)", start=0, count=16, fps=15.0)],
        ),
        surf_mats=mmw_rig_mats, allow_rigid=False,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "megaman.md3"),
        dict(
            id="megaman", cat="contraptions3d", badge="AUTONOMOUS BOT · 16f",
            title='Wheeled "Mega Man" Autonomous Bot (Scanned MD3)',
            file="progs/megaman.md3",
            desc="16-frame two-wheeled Segway-pipe contraption that steers, honks, hops & leaps around the arena!",
            clips=[dict(id="drive", label="⚙ Wheel Spin (16f)", start=0, count=16, fps=15.0)],
        ),
        surf_mats={"progs/megaman": dict(tex=t_mm_scan, metallic=0.25, roughness=0.48, spec=0.45)},
        allow_rigid=False,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "wc_bar.md3"),
        dict(
            id="wc_bar", cat="contraptions3d", badge="3D BARBELL · MD3",
            title="Wheelman Heavy Olympic Chrome Barbell & Tires",
            file="progs/wc_bar.md3",
            desc="Custom 3D two-wheel steel axle & chrome barbell assembly lifted and hurled by Wheelman.",
        ),
        surf_mats={"progs/wc_bar": dict(tex=packer.add_tex_file(os.path.join(PROGS, "wc_bar.png"), max_dim=512, lift=1.35),
                                        metallic=0.65, roughness=0.28, spec=0.78)},
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "gw_horse.md3"),
        dict(
            id="gw_horse", cat="contraptions3d", badge="MONUMENT · 3,692t",
            title="Golden West Rearing Bronze Horse Statue on Rocky Plinth",
            file="progs/gw_horse.md3",
            desc="3,692-triangle sculpted bronze stallion monument rearing atop a rugged stone plinth.",
        ),
        surf_mats={
            "progs/gw_horse": dict(tex=packer.add_tex_file(os.path.join(PROGS, "gw_horse.png"), max_dim=512, lift=1.40),
                                   metallic=0.72, roughness=0.30, spec=0.80),
            "progs/gw_rock":  dict(tex=packer.add_tex_file(os.path.join(PROGS, "gw_rock.png"), max_dim=512, lift=1.35),
                                   metallic=0.05, roughness=0.82, spec=0.18),
        },
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "hackmon_a.md3"),
        dict(
            id="hackmon_a", cat="contraptions3d", badge='RETRO CRT · "> HACKING"',
            title='"> HACKING" Green-Phosphor Retro CRT Monitor',
            file="progs/hackmon_a.md3",
            desc="19-surface beige 90s CRT monitor with glowing green '> HACKING' terminal screen, swivel base, vents & power LED!",
        ),
        lift_default=1.35,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "fedora.md3"),
        dict(
            id="fedora", cat="contraptions3d", badge="CRIMSON HAT · MD3",
            title='Crimson "Red Hat" Linux Fedora',
            file="progs/fedora.md3",
            desc="Procedural pinched-crown, curled-brim crimson fedora hat.",
        ),
        lift_default=1.30,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "bklan", "trashcan.md3"),
        dict(
            id="trashcan", cat="contraptions3d", badge="CUSTOM PROP · 840t",
            title="Custom Slatted Park Trash Receptacle",
            file="progs/bklan/trashcan.md3",
            desc="Custom-modeled 840-triangle slatted park trash receptacle built for Bakersfield LAN.",
        ),
        surf_mats={"progs/bklan/bk_trash": dict(
            tex=packer.add_tex_file(os.path.join(PROGS, "bklan", "bk_trash.png"), max_dim=512, lift=1.35),
            metallic=0.32, roughness=0.48, spec=0.45,
        )},
    ))

    pk_bomb_paths = [os.path.join(HERE, "out", "pickle_overhaul", "bomb_faces", f"bomb_face_{k:02d}.png") for k in range(8)]
    tid_pk_bomb, ord_pk_bomb = ba.build_anim_atlas_from_files(packer, "pickle_bombskin_8_srgb", pk_bomb_paths, max_tile_dim=256)
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "pickle_bomb.md3"),
        dict(
            id="pickle_bomb", cat="contraptions3d", badge="8 LIVE FACES · 360° MD3",
            title="3D Turquoise Gold-Studded Pickle Surprise (8-Expression Live Face)",
            file="progs/pickle_bomb.md3 + scripts/pickle.shader",
            desc="360-degree cylindrical turquoise gold-studded 3D Pickle Surprise totem cycling through 8 live expressions (Sing, Cheeky Pucker Wink, Bug-Eyes + Pink Tongue Out & Surprised Gasp)!",
            az=1.57, el=0.24,
        ),
        surf_mats={"progs/pickle_bombskin": dict(tex=tid_pk_bomb, animFps=7.0, animOrder=ord_pk_bomb, roughness=0.45, spec=0.35)},
    ))

    m_ltg_head = ba.build_ltg_head_md3(packer)
    m_ltg_head["cat"] = "contraptions3d"
    m_ltg_head["title"] = "24-Angle 3D Ear-Head + Animated Wi-Fi/Cable Aura"
    m_ltg_head["desc"] = "Camera-reactive 24-surface 3D head paired with an 8-frame additive Wi-Fi & Ethernet cable halo (toggle aura via Skins or Surfaces!)."
    models_out.append(m_ltg_head)

    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "mm_explode.md3"),
        dict(
            id="mm_explode", cat="contraptions3d", badge="SHATTER FX · 20f",
            title="Mega-Man 20-Frame Voronoi Shatter & Fireball",
            file="progs/mm_explode.md3",
            desc="20-frame outward-flying Voronoi shell shatter + additive blast flash when a Mega-Man contraption detonates.",
            clips=[dict(id="boom", label="💥 20f Shatter Burst", start=0, count=20, fps=16.0, lie=True)],
        ),
        allow_rigid=False, bbox_frames=[2, 4],
    ))
    models_out.append(ba.build_constellation_md3(
        packer,
        [("mm_cap", os.path.join(PROGS, "mm_cap.md3"), None)]
        + [(f"mm_frag{k}", os.path.join(PROGS, f"mm_frag{k}.md3"), None) for k in range(1, 7)],
        dict(
            id="mm_shrapnel_pack", cat="contraptions3d", badge="7-PIECE CONSTELLATION",
            title="Mega-Man 7-Piece Voronoi Shrapnel Ring",
            file="progs/mm_cap.md3 + progs/mm_frag1..6.md3",
            desc="All 7 custom end-cap & Voronoi casing shrapnel models arranged in an inspection ring—click Solo in 3D Parts to isolate any piece!",
        ),
        radius=16.0,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "mm_wheel.md3"),
        dict(
            id="mm_wheel", cat="contraptions3d", badge="SPINNING TIRE · 16f",
            title="Mega-Man Detached Spinning Rubber Tire",
            file="progs/mm_wheel.md3",
            desc="16-frame spinning detached rubber tire & hubcap mesh.",
            clips=[dict(id="spin", label="🛞 Tire Spin (16f)", start=0, count=16, fps=15.0)],
        ),
        allow_rigid=False,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "mm_bar.md3"),
        dict(
            id="mm_bar", cat="contraptions3d", badge="CHROME PIPE · MD3",
            title="Mega-Man Fractured Chrome Center Pipe",
            file="progs/mm_bar.md3",
            desc="3,655-vertex fractured central chrome bar mesh.",
        ),
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "mm_axle.md3"),
        dict(
            id="mm_axle", cat="contraptions3d", badge="STEEL AXLE · MD3",
            title="Mega-Man Hexagonal Steel Cross-Axle",
            file="progs/mm_axle.md3",
            desc="Procedural hexagonal steel cross-axle rod with flanged end-caps.",
        ),
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "netsend_disk.md3"),
        dict(
            id="netsend_disk", cat="contraptions3d", badge="SPINNING DISK · 8f",
            title='Spinning "LOL.BAT" 3.5" Floppy Diskette',
            file="progs/netsend_disk.md3",
            desc="8-frame frisbee-spinning 3.5-inch 'LOL.BAT' floppy diskette.",
            clips=[dict(id="spin", label="💾 Frisbee Spin (8f)", start=0, count=8, fps=16.0)],
        ),
        allow_rigid=False, lift_default=1.40,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "netsend_arc.md3"),
        dict(
            id="netsend_arc", cat="contraptions3d", badge="ELECTRIC FX · 8f",
            title="NetSend 3D Crackling Electric Arc Cage",
            file="progs/netsend_arc.md3",
            desc="8-frame crackling 3D additive lightning cage enveloping overloaded retro PCs.",
            clips=[dict(id="arc", label="⚡ Electric Crackles (8f)", start=0, count=8, fps=15.0, lie=True)],
        ),
        surf_mats={"progs/netsend_arc": dict(tex=t_ns_arc, unlit=True, additive=True)},
        allow_rigid=False,
    ))

    for hid, title, desc in [
        ("hd_kbd",    "Retro AT/PS2 Mechanical Keyboard",   "Wedge-profile beige mechanical keyboard with drawn keycaps & lock LEDs."),
        ("hd_mouse",  "Retro Beige 2-Button Ball Mouse",    "Classic 90s 2-button serial/PS2 ball mouse."),
        ("hd_floppy", '3.5" Floppy Diskette Prop',          "Procedural 3.5-inch diskette with sliding metal shutter & striped label."),
        ("hd_cd",     "Iridescent Rainbow CD-ROM Disc",     "16-sided annular CD-ROM disc with center hole & HSV rainbow diffraction sheen."),
        ("hd_board",  "Green Motherboard PCB w/ IC Chips",  "Green circuit board populated with DIP IC chips, gold fingers & copper traces."),
    ]:
        models_out.append(ba.pack_md3_asset(
            packer, os.path.join(PROGS, f"{hid}.md3"),
            dict(id=hid, cat="contraptions3d", badge="90s PC HARDWARE", title=title, file=f"progs/{hid}.md3", desc=desc, el=0.52),
            lift_default=1.25,
        ))

    models_out.append(ba.build_constellation_md3(
        packer,
        [(f"zap{k}", os.path.join(PROGS, f"zap{k}.md3"), None) for k in (1, 2, 3)],
        dict(
            id="zap_bolts", cat="contraptions3d", badge="3D LIGHTNING · 3 ARCS",
            title="3D Green Electric Lightning Bolts (zap1–3)",
            file="progs/zap1.md3 + zap2.md3 + zap3.md3",
            desc="All 3 crossed-ribbon 3D green electric lightning arc variants (use Solo in 3D Parts to inspect each bolt).",
        ),
        radius=0.0,
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "goo.md3"),
        dict(
            id="goo", cat="contraptions3d", badge="MORPH BLOB · 6f",
            title="Bio-Foam Morphing Sticky Goo Blob",
            file="progs/goo.md3",
            desc="6-frame polyurethane bio-foam cluster morphing from a compact glob into an expanding sticky splat!",
            clips=[dict(id="splat", label="🧪 Glob -> Expanding Splat (6f)", start=0, count=6, fps=10.0)],
        ),
        allow_rigid=False,
    ))
    t_pk_gib = packer.add_tex_file(os.path.join(HERE, "out", "pickle_overhaul", "pickle_skin_srgb.png"), max_dim=256, quality=88)
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "pickle_gib.md3"),
        dict(
            id="pickle_gib", cat="contraptions3d", badge="TURQUOISE STUDDED · MD3",
            title="3D Turquoise Gold-Studded Pickle Shrapnel",
            file="progs/pickle_gib.md3",
            desc="Bouncing 3D turquoise gold-studded Pickle Surprise shrapnel showered outward when the giant Diva balloon explodes.",
        ),
        surf_mats={"progs/pickle_skin": dict(tex=t_pk_gib, roughness=0.45, spec=0.35)},
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "ccc.md3"),
        dict(
            id="ccc", cat="contraptions3d", badge="3D TYPOGRAPHY · MD3",
            title="Bevelled 3D Extruded Yellow Letter 'C'",
            file="progs/ccc.md3",
            desc="Bevelled 3D extruded yellow letter 'C' mesh.",
        ),
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "fg_pongball.md3"),
        dict(
            id="fg_pongball", cat="contraptions3d", badge="TABLE TENNIS · MD3",
            title="3D Orange Table-Tennis Ping-Pong Ball",
            file="progs/fg_pongball.md3",
            desc="3D orange table-tennis sphere.",
        ),
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(HERE, "out", "removed_guns_src", "banana_assets", "progs", "banana.md3"),
        dict(
            id="banana", cat="contraptions3d", badge="3D FRUIT · MD3",
            title="Curved 3D Yellow Banana",
            file="source/mm_tools/out/removed_guns_src/banana_assets/progs/banana.md3",
            desc="Custom curved 3D yellow banana mesh.",
        ),
    ))
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "jw_wave.md3"),
        dict(
            id="jw_wave", cat="contraptions3d", badge="TIDAL RING · MD3",
            title='Foamy "John Wave" Rippled Ocean Surf Ring',
            file="progs/jw_wave.md3",
            desc="960-triangle curling Pacific tidal-wave ring!",
            el=0.42,
        ),
        surf_mats={"progs/jw_wave": dict(tex=t_jw_wave, unlit=True)},
    ))
    t_aura = packer.add_tex_file(os.path.join(PROGS, "aura.png"), max_dim=256, wrap=True, force_png=True)
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "aura.md3"),
        dict(
            id="aura", cat="contraptions3d", badge="SCROLLING SHIELD",
            title="Scrolling Cyan Energy Shield Bubble",
            file="progs/aura.md3 + scripts/aura.shader",
            desc="672-triangle additive energy bubble with continuous vertical UV scrolling!",
        ),
        surf_mats={"progs/aura": dict(tex=t_aura, scrollV=0.6, unlit=True, additive=True)},
    ))

    ms_mats = {}
    for k in range(6):
        tid_m = packer.add_tex_file(os.path.join(PROGS, f"milksplat_{k}.png"), max_dim=256, force_png=True)
        ms_mats[f"progs/milksplat_v{k}"] = dict(tex=tid_m, unlit=True, alphaBlend=True)
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "milksplat.md3"),
        dict(
            id="milksplat", cat="contraptions3d", badge="6 SPLATTER FRAMES",
            title="Milk Splatter Shapes (6 Animated Variants)",
            file="progs/milksplat.md3 + scripts/milky.shader",
            desc="6-frame milk splatter decal model—play or scrub frames 0–5 to see all 6 splatter shapes!",
            el=0.45,
            clips=[dict(id="all", label="🥛 Cycle All 6 Splatters", start=0, count=6, fps=3.0, lie=True)],
        ),
        surf_mats=ms_mats, allow_rigid=False, bbox_frames=list(range(6)),
    ))

    m_sparks = ba.build_sparks_mdl(packer)
    m_sparks["cat"] = "contraptions3d"
    models_out.append(m_sparks)

    # ==================== CATEGORY 4: TURNAROUND SPRITES & FRIENDS CREW ====================
    print("5. Packing Category 4 (sprites): 20 Turnaround Sprites & Real-Life Friends Crew...", flush=True)
    models_out.append(ba.build_scissor_studio(packer))

    # Standing 36-Frame Base-Planted 3D Deforming Pickle Surprise Ribbon Mesh (`progs/pickle.md3` + 4 Expression Skins)
    diva_out_dir = os.path.join(HERE, "out", "pickle_overhaul", "diva_views")
    t_pk_s0 = packer.add_tex_file(os.path.join(diva_out_dir, "diva_s0_v00.png"), max_dim=384, force_png=True)
    t_pk_s1 = packer.add_tex_file(os.path.join(diva_out_dir, "diva_s1_v00.png"), max_dim=384, force_png=True)
    t_pk_s2 = packer.add_tex_file(os.path.join(diva_out_dir, "diva_s2_v00.png"), max_dim=384, force_png=True)
    t_pk_s3 = packer.add_tex_file(os.path.join(diva_out_dir, "diva_s3_v00.png"), max_dim=384, force_png=True)
    models_out.append(ba.pack_md3_asset(
        packer, os.path.join(PROGS, "pickle.md3"),
        dict(
            id="pickle_turntable", cat="sprites", badge="36f RIBBON · 4 SKINS",
            title="In-Game Deforming Pickle Surprise Balloon (36f Mesh + 4 Expressions)",
            file="progs/pickle.md3 + progs/pickle.md3_0..63.skin",
            desc="Overhauled in-game 36-frame base-planted 3D deforming 9×17 ribbon-grid Pickle Surprise balloon (zero collapsed-card shrinking!) — switch Skins to preview all 4 facial poses!",
            az=0.0, el=0.08,
            skins=[
                dict(label="🎵 Singing Diva",       map={"card": dict(tex=t_pk_s0)}),
                dict(label="😘 Cheeky Pucker Wink", map={"card": dict(tex=t_pk_s1)}),
                dict(label="👅 Bug-Eyes + Tongue",  map={"card": dict(tex=t_pk_s2)}),
                dict(label="😱 Giant Scream",       map={"card": dict(tex=t_pk_s3)}),
            ],
            clips=[
                dict(id="wave",  label="🥒 S-Curve Inflatable Dance (24f)", start=0,  count=24, fps=18.0),
                dict(id="swell", label="😱 Pre-Blast Balloon Swell (12f)",  start=24, count=12, fps=14.0),
                dict(id="all",   label="🎬 Full 36-Frame Mesh Cycle",       start=0,  count=36, fps=18.0),
            ],
        ),
        surf_mats={"progs/pkv_s0_v00": dict(tex=t_pk_s0, unlit=True, alphaTest=True, alphaBlend=True)},
        allow_rigid=False, bbox_frames=[0, 35],
    ))

    models_out.append(ba.build_pinklady_sprite(packer))
    models_out.append(ba.build_earhead_studio(packer))

    models_out.append(ba.pack_spr_asset(
        packer, os.path.join(PROGS, "fr_rob.spr32"),
        dict(
            id="fr_rob", cat="sprites", badge="FRIEND CREW · 56f",
            title="Friend Crew: Rob (8-Dir × 6f Run & Idle .SPR32)",
            file="progs/fr_rob.spr32",
            desc="8-direction photo-cutout sprite of Rob (8 idle angles + 8×6 run loop)—drag horizontally or toggle Crisp 2D Canvas!",
        ),
    ))

    friend_names = [
        ("babydavid", "Baby David"), ("david", "David"), ("jeffery", "Jeffery"),
        ("jessa", "Jessa"), ("john", "John"), ("julian", "Julian"),
        ("larry", "Larry"), ("marc", "Marc"), ("mike", "Mike"), ("reese", "Reese"),
    ]
    for fn_key, nice_nm in friend_names:
        models_out.append(ba.pack_spr_asset(
            packer, os.path.join(HERE, "out", "friends", "progs", f"fr_{fn_key}.spr32"),
            dict(
                id=f"fr_{fn_key}", cat="sprites", badge="FRIEND CREW · 56f",
                title=f"Friend Crew: {nice_nm} (8-Dir × 6f Run & Idle)",
                file=f"source/mm_tools/out/friends/progs/fr_{fn_key}.spr32",
                desc=f"56-frame 8-direction photo sprite for {nice_nm} (8 directional idle angles + 8-way × 6-frame run cycle)!",
            ),
        ))

    models_out.append(ba.pack_spr_asset(
        packer, os.path.join(PROGS, "fr_scissors.spr32"),
        dict(
            id="fr_scissors", cat="sprites", badge="8-DIR SPR32 · 56f",
            title="Giant Running Scissors In-Game (.SPR32)",
            file="progs/fr_scissors.spr32",
            desc="Active 56-frame 8-direction SPR32 sprite for the snipping Giant Scissors hazard (8 idle + 8×6 run).",
        ),
    ))
    models_out.append(ba.pack_spr_asset(
        packer, os.path.join(HERE, "out", "removed_guns_src", "john_assets", "progs", "fr_johnhead.spr32"),
        dict(
            id="fr_johnhead", cat="sprites", badge="16-ANGLE SPR32",
            title="John Flying Head 16-Angle Sprite (.SPR32)",
            file="source/mm_tools/out/removed_guns_src/john_assets/progs/fr_johnhead.spr32",
            desc="16-angle 32-bit RGBA turnaround sprite of John's flying head.",
        ),
        mode="turn16",
    ))
    models_out.append(ba.pack_spr_asset(
        packer, os.path.join(PROGS, "jw_ripple.spr32"),
        dict(
            id="jw_ripple", cat="sprites", badge="FLOOR SPR32 · 10f",
            title="John Wave Expanding Floor Water Ripple (.SPR32)",
            file="progs/jw_ripple.spr32",
            desc="10-frame oriented horizontal water shockwave sprite spawned flat along the floor.",
            el=0.62,
        ),
        mode="floor", scale_u=0.35,
    ))
    models_out.append(ba.pack_spr_asset(
        packer, os.path.join(PROGS, "jw_splash.spr32"),
        dict(
            id="jw_splash", cat="sprites", badge="SPLASH SPR32 · 8f",
            title="John Wave Foaming Water Splash (.SPR32)",
            file="progs/jw_splash.spr32",
            desc="8-frame 32-bit RGBA foaming water burst sprite.",
        ),
        scale_u=0.45,
    ))
    models_out.append(ba.pack_spr_asset(
        packer, os.path.join(PROGS, "netsend_arc.spr"),
        dict(
            id="netsend_arc_spr", cat="sprites", badge="8-BIT SPR · 8f",
            title="Electric Spark Burst (Classic Quake 8-Bit .SPR)",
            file="progs/netsend_arc.spr",
            desc="8-frame classic Quake IDSP v1 8-bit paletted electric spark sprite.",
            additive=True,
        ),
        scale_u=0.65,
    ))

    # ==================== STRICT SCOPE & INTEGRITY VALIDATION ====================
    print(f"6. Validating {len(models_out)} custom models/suites & {len(packer.tex_list)} textures/atlases...", flush=True)

    forbidden_ids = {
        # Cars / Ground vehicles / Kart / Van-fuselage skyveh
        "pink_supercar", "veh_van", "van_walkin", "veh_truck", "veh_sedan", "veh_coupe",
        "veh_blast", "veh_van_wreck", "veh_truck_wreck", "veh_sedan_wreck", "veh_coupe_wreck",
        "veh_blown_parts", "jesskart_studio", "jesskart_spr32",
        "skyveh_v1", "skyveh_v2", "skyveh_v3", "skyveh_v4",
        # Guns / Viewmodels / Weapon Rigs / Weapon Pickups / Sentry Gun
        "v_megaman", "v_megaman_hand", "v_megaman_classic", "v_laptop", "ltg_view", "ltg_p", "ltg_g",
        "v_netsend", "v_googun", "p_googun", "v_hammer", "v_srifle", "g_srifle", "p_srifle",
        "v_robdob", "v_sledge", "sledge", "v_paddle", "paddle", "v_hackmon", "v_span",
        "v_milky", "v_pickle", "fr_johnhand", "v_pocket_rocket", "v_banana_girl", "v_banana",
        "v_robrocket", "v_mysterybox", "sight_spr", "laser_beams", "sentry_turret", "sentry_gibs",
    }

    for ti, t in enumerate(packer.tex_list):
        assert 1 <= t["w"] <= 4096 and 1 <= t["h"] <= 4096, f"Tex #{ti} {t['key']} exceeds 4096: {t['w']}x{t['h']}"
        assert t["uri"].startswith("data:image/"), f"Tex #{ti} {t['key']} is not an inline data URI!"

    seen_ids = set()
    arena_len = len(packer.buf)
    num_tex = len(packer.tex_list)
    cat_counts = {}
    total_clips = 0

    for m in models_out:
        mid = m["id"]
        assert mid not in forbidden_ids, f"FORBIDDEN car/gun asset leaked: {mid}"
        assert not mid.startswith(("v_", "veh_", "skyveh_", "sr_")), f"FORBIDDEN prefix on {mid}"
        assert mid not in seen_ids, f"Duplicate model id: {mid}"
        seen_ids.add(mid)
        assert m["cat"] in ("featured", "chars3d", "contraptions3d", "sprites"), f"Bad cat on {mid}: {m['cat']}"
        cat_counts[m["cat"]] = cat_counts.get(m["cat"], 0) + 1
        assert m["nf"] >= 1 and len(m["surfaces"]) >= 1 and len(m["clips"]) >= 1, f"Empty model {mid}"
        total_clips += len(m["clips"])

        if "rigidMats" in m:
            off, ln = m["rigidMats"]
            assert 0 <= off and off + ln <= arena_len and (off & 7) == 0 and ln == m["nf"] * 48, f"Bad rigidMats on {mid}"

        surf_names = {s["name"] for s in m["surfaces"]}
        for s in m["surfaces"]:
            assert s["nfGeom"] >= 1, f"Missing nfGeom on {mid}:{s['name']}"
            for bk in ("tris", "edges", "uv", "pos", "nrm"):
                off, ln = s[bk]
                assert 0 <= off and off + ln <= arena_len and (off & 7) == 0, f"Bad slice {bk} on {mid}:{s['name']}"
            assert -1 <= s["tex"] < num_tex, f"Bad tex {s['tex']} on {mid}:{s['name']}"
            assert -1 <= s["glowTex"] < num_tex, f"Bad glowTex {s['glowTex']} on {mid}:{s['name']}"

        for sk in m.get("skins", []):
            for sk_surf, ov in sk["map"].items():
                assert sk_surf in surf_names, f"Skin {sk['label']} unknown surf {sk_surf} on {mid}"
                if "tex" in ov:
                    assert -1 <= ov["tex"] < num_tex, f"Bad skin tex on {mid}"
                if "glowTex" in ov:
                    assert -1 <= ov["glowTex"] < num_tex, f"Bad skin glowTex on {mid}"

        for cl in m["clips"]:
            sm = cl.get("sprMode")
            if sm and "tex" in sm:
                assert 0 <= sm["tex"] < num_tex, f"Bad clip sprMode.tex on {mid}:{cl['id']}"

    print(f"   Categories: {cat_counts} -> TOTAL: {len(models_out)} items, {total_clips} animation clips, {len(sounds)} sounds", flush=True)

    raw_bytes = bytes(packer.buf)
    gz_bytes = gzip.compress(raw_bytes, compresslevel=6)
    b64_gz = base64.b64encode(gz_bytes).decode("ascii")
    tex_uri_bytes = sum(len(t["uri"]) for t in packer.tex_list)
    snd_uri_bytes = sum(len(s["uri"]) for s in sounds)
    print(
        f"   Geometry arena: {len(raw_bytes)/1e6:.2f} MB raw -> {len(gz_bytes)/1e6:.2f} MB gzip ({len(b64_gz)/1e6:.2f} MB b64)\n"
        f"   Textures/Atlases: {num_tex} items ({tex_uri_bytes/1e6:.2f} MB data URIs)\n"
        f"   Soundboard: {len(sounds)} clips ({snd_uri_bytes/1e6:.2f} MB data URIs)",
        flush=True,
    )

    meta_obj = dict(
        sounds=sounds,
        textures=packer.tex_list,
        models=models_out,
    )
    meta_json = json.dumps(meta_obj, separators=(",", ":"))

    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    assert "/*__META_JSON__*/" in tpl, "Missing /*__META_JSON__*/ in template!"
    assert "/*__BIN_GZ__*/" in tpl, "Missing /*__BIN_GZ__*/ in template!"
    html = tpl.replace("/*__META_JSON__*/", meta_json, 1).replace("/*__BIN_GZ__*/", b64_gz, 1)
    assert "/*__META_JSON__*/" not in html and "/*__BIN_GZ__*/" not in html

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"7. SUCCESS! Wrote self-contained showcase: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)", flush=True)


if __name__ == "__main__":
    main()
