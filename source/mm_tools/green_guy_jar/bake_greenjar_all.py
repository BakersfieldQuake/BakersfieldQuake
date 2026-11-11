"""Master Asset Baker for the 'Jar o' Green Guys' Weapon (`bake_greenjar_all.py`).

Generates in a single pass:
  1. Visual Audit Contact Sheet (`work/audit_greenjar_all.jpg`)
  2. DarkPlaces First-Person 2D Weapon Sprite Viewmodel:
       - `progs/v_greenjar.md3` (4-vertex camera-aligned 2D sprite card)
       - `progs/gjvm_000..111.png` + `progs/v_greenjar.md3_0..111.skin` + `scripts/greenjarvm.shader`
         * Skins 0..59   (60): 4-Antic In-Jar Spaz Idle Loop (Hamster Climb, Face Squish, Pogo Lid-Bonk, Tornado Spaz)
         * Skins 60..75  (16): Cocktail-Shaker Windup Loop (hold Fire to rattle & supercharge mist!)
         * Skins 76..93  (18): Overhand Whip-Throw (76..83 cock-back & whip; 84..93 splayed open-claw follow-through!)
         * Skins 94..111 (18): Belt-Snatch Fresh Jar Reload & Settle!
  3. DarkPlaces World `.spr32` Sprites:
       - `progs/greenjar_proj.spr32`  (16 frames, 96x96, tumbling sealed glass jar)
       - `progs/greenjar_burst.spr32` (16 frames, 160x160, shattering glass shards + igniting neon-green smoke cloud)
       - `progs/greenguy_mini.spr32`  (320 frames, 112x112: 16x6 scurry, 16x6 wall_climb, 16x6 pogo_jump, 16 shot_spin, 16 balloon_pop)
  4. 60 FPS WebP Atlases + Poster (`greenjar_poster.jpg`) + Animated GIF (`greenjar_preview.gif`) in `green_guy_jar_weapon/`!
"""
from __future__ import annotations

import glob
import json
import math
import os
import struct
import sys
import time
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.abspath(os.path.join(HERE, ".."))
GS_DIR = os.path.abspath(os.path.join(MM_TOOLS, "greensuit_monster"))
for p in (HERE, MM_TOOLS, GS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import md3lib
from greensuit_core import ANGLES_DEG, N_DIRS, resize_rgba_premul
from greensuit_turnarounds import build_all_16_turnarounds
import greenjar_sprites as gs

MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
PROGS_DIR = os.path.join(MOD_ROOT, "progs")
SCRIPTS_DIR = os.path.join(MOD_ROOT, "scripts")
PACK_DIR = os.path.join(MOD_ROOT, "green_guy_jar_weapon")
ATLAS_DIR = os.path.join(PACK_DIR, "atlases")


def tone_for_quake_hdr_rgba(srgb_rgba: np.ndarray, dim: float = 0.56, contrast: float = 1.08) -> np.ndarray:
    a = srgb_rgba[..., 3]
    rgb_im = Image.fromarray(srgb_rgba[..., :3], "RGB")
    if abs(contrast - 1.0) > 1e-3:
        rgb_im = ImageEnhance.Contrast(rgb_im).enhance(contrast)
    if abs(dim - 1.0) > 1e-3:
        rgb_im = ImageEnhance.Brightness(rgb_im).enhance(dim)
    rgb_arr = np.asarray(rgb_im, dtype=np.uint8).copy()
    a_clean = np.where(a < 6, 0, a).astype(np.uint8)
    rgb_arr[a_clean == 0] = 0
    return np.dstack([rgb_arr, a_clean])


def tone_for_spr32_bytes(rgba: np.ndarray) -> bytes:
    pil = Image.fromarray(rgba, "RGBA")
    rgb = ImageEnhance.Contrast(pil.convert("RGB")).enhance(1.18)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.52)
    rgb.putalpha(pil.getchannel("A"))
    return rgb.tobytes()


def write_darkplaces_spr32(spr_path: str, raw_frame_bytes: List[bytes], w: int, h: int, ground_y: int) -> float:
    rad = math.hypot(w * 0.5, h)
    ox = -(w // 2)
    oy = ground_y
    buf = bytearray(b"IDSP" + struct.pack("<iifiiifi", 32, 0, rad, w, h, len(raw_frame_bytes), 0.0, 0))
    frame_hdr = struct.pack("<i", 0) + struct.pack("<iiii", ox, oy, w, h)
    for fb in raw_frame_bytes:
        buf += frame_hdr
        buf += fb
    os.makedirs(os.path.dirname(spr_path), exist_ok=True)
    with open(spr_path, "wb") as f:
        f.write(buf)
    return len(buf) / (1024.0 * 1024.0)


def write_card_md3(
    path: str,
    model_name: str,
    surf_name: str,
    default_shader: str,
    dx: float,
    y_left: float,
    y_right: float,
    z_bot: float,
    z_top: float,
) -> None:
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    card = [
        (dx, y_left, z_bot),
        (dx, y_left, z_top),
        (dx, y_right, z_top),
        (dx, y_right, z_bot),
    ]
    surf = dict(
        name=surf_name,
        shader=default_shader,
        tris=tris,
        st=st,
        frames=[(card, [(-1.0, 0.0, 0.0)] * 4)],
    )
    md3lib.write(path, dict(name=model_name, surfaces=[surf], nframes=1))


def pack_webp_grid(frames: List[np.ndarray], cell_w: int, cell_h: int, cols: int, out_path: str, quality: int = 84) -> Tuple[int, int, float]:
    n = len(frames)
    rows = int(math.ceil(n / float(cols)))
    sheet = np.zeros((rows * cell_h, cols * cell_w, 4), dtype=np.uint8)
    for idx, fr in enumerate(frames):
        r = idx // cols
        c = idx % cols
        rs = resize_rgba_premul(fr, cell_w, cell_h)
        sheet[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w] = rs
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(sheet, "RGBA").save(out_path, "WEBP", quality=quality, method=4)
    return cols, rows, os.path.getsize(out_path) / 1024.0


def save_audit_sheet(rig: gs.JarGauntletRig, vm: Dict[str, List[np.ndarray]], proj: List[np.ndarray], burst: List[np.ndarray], mini: Dict[str, object], out_p: str) -> None:
    W, H = 1680, 990
    sheet = Image.new("RGB", (W, H), (22, 26, 30))
    dr = ImageDraw.Draw(sheet)

    def paste_rgba(im_arr: np.ndarray, x: int, y: int, w: int, h: int, label: str = "") -> None:
        pil = Image.fromarray(im_arr, "RGBA").resize((w, h), Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", (w, h), (34, 40, 46, 255))
        comp = Image.alpha_composite(bg, pil).convert("RGB")
        sheet.paste(comp, (x, y))
        dr.rectangle([x, y, x + w - 1, y + h - 1], outline=(70, 95, 75))
        if label:
            dr.text((x + 4, y + 4), label, fill=(180, 255, 160))

    idle_picks = [8, 22, 55, 72, 98, 112, 145, 165]
    labels_i = ["Antic0 ClimbA", "Antic0 LidFlip", "Antic1 GrinSquish", "Antic1 ScreamSquish", "Antic2 Pogo1", "Antic2 LidBonk", "Antic3 TornadoA", "Antic3 TornadoB"]
    for i, (fi, lb) in enumerate(zip(idle_picks, labels_i)):
        paste_rgba(vm["vm_idle"][fi], 12 + i * 206, 12, 198, 212, lb)

    r2 = [
        (vm["vm_shake"][2], "Shake 2"),
        (vm["vm_shake"][6], "Shake 6"),
        (vm["vm_throw"][3], "Throw CockBack"),
        (vm["vm_throw"][7], "Throw Whip"),
        (vm["vm_throw"][9], "Throw OpenClaw!"),
        (vm["vm_throw"][13], "Throw Follow"),
        (vm["vm_reload"][4], "Reload Raise"),
        (vm["vm_reload"][15], "Reload Settle"),
    ]
    for i, (arr, lb) in enumerate(r2):
        paste_rgba(arr, 12 + i * 206, 236, 198, 212, lb)

    r3 = [
        (rig.standalone_jar, "StandaloneJar"),
        (proj[0], "Proj 0"),
        (proj[5], "Proj 5"),
        (proj[11], "Proj 11"),
        (proj[17], "Proj 17"),
        (burst[1], "Burst Flash 1"),
        (burst[6], "Burst Shards 6"),
        (burst[14], "Burst Smoke 14"),
        (burst[22], "Burst Smoke 22"),
        (burst[30], "Burst Fade 30"),
    ]
    for i, (arr, lb) in enumerate(r3):
        paste_rgba(arr, 12 + i * 165, 462, 158, 158, lb)

    r4 = [
        (mini["scurry"][0][2], "Scurry 0deg"),
        (mini["scurry"][3][5], "Scurry 67deg"),
        (mini["scurry"][8][8], "Scurry 180deg"),
        (mini["wall_climb"][2][1], "WallClimb R1"),
        (mini["wall_climb"][4][6], "WallClimb R2"),
        (mini["wall_climb"][12][3], "WallClimb L1"),
        (mini["pogo_jump"][0][1], "Pogo Crouch"),
        (mini["pogo_jump"][0][6], "Pogo Apex!"),
        (mini["pogo_jump"][2][6], "Pogo 45deg!"),
        (mini["pogo_jump"][14][6], "Pogo 315deg!"),
    ]
    for i, (arr, lb) in enumerate(r4):
        paste_rgba(arr, 12 + i * 165, 634, 158, 158, lb)

    r5 = [
        (mini["shot_spin"][1], "ShotSpin 1"),
        (mini["shot_spin"][6], "ShotSpin 6"),
        (mini["shot_spin"][12], "ShotSpin 12"),
        (mini["shot_spin"][18], "ShotSpin 18"),
        (mini["balloon_pop"][1], "Swell 1"),
        (mini["balloon_pop"][5], "Swell 1.46x!"),
        (mini["balloon_pop"][6], "POP Shock 6!"),
        (mini["balloon_pop"][9], "Confetti 9!"),
        (mini["balloon_pop"][14], "Confetti 14!"),
        (mini["balloon_pop"][20], "Confetti 20!"),
    ]
    for i, (arr, lb) in enumerate(r5):
        paste_rgba(arr, 12 + i * 165, 806, 158, 158, lb)

    os.makedirs(os.path.dirname(out_p), exist_ok=True)
    sheet.save(out_p, quality=92)


def save_poster_and_preview_gif(vm: Dict[str, List[np.ndarray]], proj: List[np.ndarray], burst: List[np.ndarray], mini: Dict[str, object]) -> None:
    os.makedirs(PACK_DIR, exist_ok=True)
    # 1. Rich 1720x980 Showcase Poster for Telegram & Web OG
    W, H = 1720, 980
    poster = Image.new("RGB", (W, H), (12, 18, 22))
    dr = ImageDraw.Draw(poster)
    dr.text((26, 16), "JAR O' GREEN GUYS (IMPULSE 62) — 60 FPS LIVE-ACTION DIGITIZED QUAKE SWARM & DISTRACTION WEAPON", fill=(134, 255, 78))
    dr.text((26, 40), "4-Antic Spazzing Specimen Jar · Igniting Neon-Green Smoke Shatter · 12 Wall-Climbing / 5x Face-Orbiting Gremlins · 1-Shot Helium Spin -> Rainbow Confetti Pop!", fill=(176, 198, 212))

    # Left Hero Cards: 4 Held-Jar Antics + Shake + Open-Claw Whip
    hero_cards = [
        (vm["vm_idle"][10],  "1. Hamster-Wheel Climb"),
        (vm["vm_idle"][56],  "2. Grin Glass-Squish + Fog"),
        (vm["vm_idle"][74],  "3. Scream Glass-Squish"),
        (vm["vm_idle"][112], "4. Pogo Lid-Bonk!"),
        (vm["vm_shake"][4],  "5. Cocktail-Shaker Windup"),
        (vm["vm_throw"][9],  "6. Whip-Throw Open Claw!"),
    ]
    for idx, (arr, cap) in enumerate(hero_cards):
        bx = 24 + idx * 280
        by = 72
        tile = Image.new("RGBA", (268, 290), (22, 32, 36, 255))
        rs = resize_rgba_premul(arr, 260, 278)
        tile.alpha_composite(Image.fromarray(rs, "RGBA"), (4, 10))
        poster.paste(tile.convert("RGB"), (bx, by))
        dr.rectangle([bx, by, bx + 267, by + 289], outline=(68, 132, 82), width=2)
        dr.text((bx + 8, by + 6), cap, fill=(250, 214, 65))

    # Middle Strip: Shatter Sequence + 16-Angle Mini-Gremlin Wall-Climb & Pogo Face-Swarm
    dr.text((26, 378), "SHATTERING GLASS & IGNITING GREEN SMOKE  ->  12 UNLEASHED FLOOR-ZOOMING, BUILDING-CLIMBING & EYE-LEVEL FACE-BLOCKING GREMLINS", fill=(72, 226, 255))
    mid_cards = [
        (proj[2], "Tumbling Jar"),
        (proj[9], "Mid-Air Spin"),
        (burst[1], "Ignition Flash!"),
        (burst[7], "Glass Shatter!"),
        (burst[15], "Green Smoke Cloud!"),
        (mini["scurry"][0][2], "Floor Zoom 0°"),
        (mini["scurry"][4][6], "Ankle Orbit 90°"),
        (mini["wall_climb"][2][2], "Wall-Climb Up!"),
        (mini["wall_climb"][13][6], "Building Scale!"),
        (mini["pogo_jump"][0][6], "Eye-Level Block!"),
    ]
    for idx, (arr, cap) in enumerate(mid_cards):
        bx = 24 + idx * 168
        by = 404
        tile = Image.new("RGBA", (158, 168), (20, 28, 34, 255))
        rs = resize_rgba_premul(arr, 152, 152)
        tile.alpha_composite(Image.fromarray(rs, "RGBA"), (3, 14))
        poster.paste(tile.convert("RGB"), (bx, by))
        dr.rectangle([bx, by, bx + 157, by + 167], outline=(54, 98, 112), width=1)
        dr.text((bx + 5, by + 4), cap, fill=(175, 245, 255))

    # Bottom Strip: 1-Hit Punctured-Helium-Balloon Shot-Spin -> Balloon Swell -> Rainbow Party-Confetti POP!
    dr.text((26, 590), "1-HIT LOW-HP COMEDY DEATH: PUNCTURED-HELIUM-BALLOON 360° CARTWHEEL SPIN  ->  1.5x BALLOON SWELL  ->  RAINBOW CONFETTI POP!", fill=(255, 108, 172))
    bot_cards = [
        (mini["shot_spin"][0], "Shot! 1 HP"),
        (mini["shot_spin"][4], "Helium Spin 1"),
        (mini["shot_spin"][9], "Cartwheel Jet!"),
        (mini["shot_spin"][15], "Pinwheel 360°!"),
        (mini["shot_spin"][20], "Ricochet Shriek"),
        (mini["balloon_pop"][1], "Balloon Swell 1"),
        (mini["balloon_pop"][5], "Over-Inflated!"),
        (mini["balloon_pop"][6], "SHOCKWAVE POP!"),
        (mini["balloon_pop"][10], "Rainbow Confetti!"),
        (mini["balloon_pop"][15], "Party Shower!"),
    ]
    for idx, (arr, cap) in enumerate(bot_cards):
        bx = 24 + idx * 168
        by = 616
        tile = Image.new("RGBA", (158, 168), (28, 22, 34, 255))
        rs = resize_rgba_premul(arr, 152, 152)
        tile.alpha_composite(Image.fromarray(rs, "RGBA"), (3, 14))
        poster.paste(tile.convert("RGB"), (bx, by))
        dr.rectangle([bx, by, bx + 157, by + 167], outline=(132, 68, 112), width=1)
        dr.text((bx + 5, by + 4), cap, fill=(255, 196, 228))

    # Footer spec banner
    dr.rectangle([24, 804, W - 24, 956], fill=(18, 27, 31), outline=(72, 148, 86), width=2)
    dr.text((42, 818), "BAKERSFIELD QUAKE LIVE WEAPON SPECS (FUN GUN SLOT 2 — IMPULSE 62):", fill=(134, 255, 78))
    dr.text((42, 846), "• First-Person Sprite (`progs/v_greenjar.md3`): 4 Manic In-Jar Antics + Hold-Fire Cocktail-Shaker + Whip-Throw + Belt Reload + Muffled Jar Giggles!", fill=(226, 238, 244))
    dr.text((42, 872), "• Impact Swarm (`12x greenguy_mini.spr32`): Igniting Green-Smoke Burst -> Fast Floor Zoomers, 90° Vertical Building Climbers & Pogo Face-Jumpers!", fill=(226, 238, 244))
    dr.text((42, 898), "• Pure Annoyance Distraction: Circles Victim 5 Full Orbits Jumping in Their Face (1%-2% Non-Lethal Chip Pokes, NEVER Kills: Clamped >= 1 HP) -> Confetti Pop!", fill=(226, 238, 244))
    dr.text((42, 924), "• 1-Shot Helium Spin & Helium Voice Pack: Shoot Any Gremlin for a Shrieking 360° Cartwheel Spin into Rainbow Confetti + High-Pitched Laughing & Giggling!", fill=(255, 216, 92))

    poster_path = os.path.join(PACK_DIR, "greenjar_poster.jpg")
    poster.save(poster_path, quality=92)

    # 2. Animated Preview GIF (`greenjar_preview.gif`, 64 frames @ 25 FPS showing Left: Held Jar Spaz/Shake/Throw, Right: Smoke -> Wall-Climb -> Spin -> Confetti Pop!)
    gif_frames: List[Image.Image] = []
    GW, GH = 680, 360
    for gf in range(64):
        frame_im = Image.new("RGBA", (GW, GH), (16, 22, 28, 255))
        gdr = ImageDraw.Draw(frame_im)
        gdr.rectangle([8, 8, 332, 352], fill=(22, 32, 36, 255), outline=(74, 152, 86, 255), width=2)
        gdr.rectangle([344, 8, 672, 352], fill=(24, 26, 36, 255), outline=(88, 132, 196, 255), width=2)

        # Left pane: Idle Antics (0..39) -> Cocktail Shake (40..51) -> Whip Throw (52..63)
        if gf < 40:
            v_arr = vm["vm_idle"][(gf * 4) % len(vm["vm_idle"])]
            lbl_l = "HELD JAR: 60 FPS IN-JAR SPAZ & MIST"
        elif gf < 52:
            v_arr = vm["vm_shake"][((gf - 40) * 2) % len(vm["vm_shake"])]
            lbl_l = "HOLD FIRE: COCKTAIL-SHAKER WINDUP!"
        else:
            v_arr = vm["vm_throw"][min(len(vm["vm_throw"]) - 1, int((gf - 52) * 1.5))]
            lbl_l = "THROW: OVERHAND WHIP & OPEN CLAW!"
        v_rs = resize_rgba_premul(v_arr, 296, 318)
        frame_im.alpha_composite(Image.fromarray(v_rs, "RGBA"), (22, 30))
        gdr.text((18, 14), lbl_l, fill=(154, 255, 98, 255))

        # Right pane: Tumbling Jar (0..9) -> Smoke Burst (10..23) -> Wall-Climb & Face-Jump Swarm (24..43) -> Shot-Spin & Confetti Pop (44..63)
        if gf < 10:
            r_arr = proj[(gf * 2) % len(proj)]
            lbl_r = "THROWN TUMBLING SPECIMEN JAR"
        elif gf < 24:
            r_arr = burst[min(len(burst) - 1, int((gf - 10) * 2.4))]
            lbl_r = "SHATTER & GREEN SMOKE IGNITION!"
        elif gf < 44:
            sub_k = gf - 24
            if sub_k < 10:
                r_arr = mini["wall_climb"][(sub_k * 2) % 16][sub_k % 12]
                lbl_r = "12x GREMLINS: WALL-CLIMBING!"
            else:
                r_arr = mini["pogo_jump"][((sub_k - 10) * 2) % 16][(sub_k * 2) % 12]
                lbl_r = "5x FACE-BLOCKING ORBIT JUMP!"
        elif gf < 53:
            r_arr = mini["shot_spin"][min(23, int((gf - 44) * 2.6))]
            lbl_r = "1-SHOT HELIUM CARTWHEEL SPIN!"
        else:
            r_arr = mini["balloon_pop"][min(23, int((gf - 53) * 2.2))]
            lbl_r = "1.5x SWELL -> RAINBOW CONFETTI POP!"
        r_rs = resize_rgba_premul(r_arr, 268, 268)
        frame_im.alpha_composite(Image.fromarray(r_rs, "RGBA"), (374, 56))
        gdr.text((354, 14), lbl_r, fill=(255, 212, 84, 255))

        gif_frames.append(frame_im.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    gif_path = os.path.join(PACK_DIR, "greenjar_preview.gif")
    gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:], duration=42, loop=0, optimize=False)


def main() -> None:
    t0 = time.time()
    os.makedirs(gs.WORK_DIR, exist_ok=True)
    os.makedirs(PROGS_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    os.makedirs(ATLAS_DIR, exist_ok=True)

    print("[1/5] Loading 16-angle live-action Green-Suit turnarounds & building JarGauntletRig...")
    turns = build_all_16_turnarounds()
    rig = gs.JarGauntletRig(turns)

    print("[2/5] Synthesizing 60 FPS Held-Jar Viewmodel, Projectile, Green-Smoke Ignition & 12-Gremlin Sprites...")
    vm = rig.render_viewmodel_sequences_out()
    proj, burst = gs.build_projectile_and_smoke_sprites(rig)
    mini = gs.build_mini_gremlin_sprites(turns)

    audit_p = os.path.join(gs.WORK_DIR, "audit_greenjar_all.jpg")
    save_audit_sheet(rig, vm, proj, burst, mini, audit_p)
    print(f"      Saved visual audit sheet -> {audit_p}")

    print("[3/5] Exporting DarkPlaces `progs/v_greenjar.md3` + 112 skins + `scripts/greenjarvm.shader`...")
    for old in glob.glob(os.path.join(PROGS_DIR, "gjvm_*.png")) + glob.glob(os.path.join(PROGS_DIR, "v_greenjar.md3_*.skin")):
        os.remove(old)

    # Skin table:
    #   0..59   (60): Idle 4-antic loop (every 3rd frame of 180f -> 20 FPS = 3.0s)
    #   60..75  (16): Cocktail-Shaker loop (16 evenly spaced frames of 24f -> 40 FPS = 0.40s)
    #   76..93  (18): Whip-Throw & Splayed Open-Claw Release (all 18f; jar launches at skin 84!)
    #   94..111 (18): Belt-Snatch Reload (all 18f)
    idle_60 = [vm["vm_idle"][i * 3] for i in range(60)]
    shake_16 = [vm["vm_shake"][int(round(i * 23 / 15.0))] for i in range(16)]
    throw_18 = vm["vm_throw"]
    reload_18 = vm["vm_reload"]
    all_112 = idle_60 + shake_16 + throw_18 + reload_18
    assert len(all_112) == 112

    shader_names: List[str] = []
    for idx, fr in enumerate(all_112):
        toned = tone_for_quake_hdr_rgba(fr, dim=0.56, contrast=1.08)
        tex_name = f"gjvm_{idx:03d}"
        Image.fromarray(toned, "RGBA").save(os.path.join(PROGS_DIR, f"{tex_name}.png"), optimize=False)
        sh = f"progs/{tex_name}"
        shader_names.append(sh)
        with open(os.path.join(PROGS_DIR, f"v_greenjar.md3_{idx}.skin"), "wb") as sf:
            sf.write(f"card,{sh}\n".encode("ascii"))

    # Viewport quad placement: jar centered comfortably in right-hand viewmodel zone, forearm sweeping past bottom-right!
    write_card_md3(
        os.path.join(PROGS_DIR, "v_greenjar.md3"),
        "v_greenjar",
        "card",
        shader_names[0],
        dx=14.0,
        y_left=-1.5,
        y_right=-26.5,
        z_bot=-18.6,
        z_top=8.2,
    )

    sh_lines = ["// written by source/mm_tools/green_guy_jar/bake_greenjar_all.py\n"]
    for sh in shader_names:
        sh_lines.append(
            f"{sh}\n{{\n\tcull none\n\t{{\n\t\tmap {sh}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
        )
    with open(os.path.join(SCRIPTS_DIR, "greenjarvm.shader"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(sh_lines))

    print("[4/5] Exporting DarkPlaces `.spr32` world sprites (`greenjar_proj`, `greenjar_burst`, `greenguy_mini`)...")
    proj_16_bytes = [
        tone_for_spr32_bytes(resize_rgba_premul(proj[int(round(i * 23 / 15.0))], 96, 96))
        for i in range(16)
    ]
    mb_proj = write_darkplaces_spr32(os.path.join(PROGS_DIR, "greenjar_proj.spr32"), proj_16_bytes, 96, 96, 48)

    burst_16_bytes = [
        tone_for_spr32_bytes(resize_rgba_premul(burst[int(round(i * 35 / 15.0))], 160, 160))
        for i in range(16)
    ]
    mb_burst = write_darkplaces_spr32(os.path.join(PROGS_DIR, "greenjar_burst.spr32"), burst_16_bytes, 160, 160, 104)

    mini_bytes: List[bytes] = []
    # 0..95: scurry (16 dirs x 6 frames)
    for d in range(N_DIRS):
        for k in range(6):
            mini_bytes.append(tone_for_spr32_bytes(resize_rgba_premul(mini["scurry"][d][k * 2], 112, 112)))
    # 96..191: wall_climb (16 dirs x 6 frames)
    for d in range(N_DIRS):
        for k in range(6):
            mini_bytes.append(tone_for_spr32_bytes(resize_rgba_premul(mini["wall_climb"][d][k * 2], 112, 112)))
    # 192..287: pogo_jump (16 dirs x 6 frames)
    for d in range(N_DIRS):
        for k in range(6):
            mini_bytes.append(tone_for_spr32_bytes(resize_rgba_premul(mini["pogo_jump"][d][k * 2], 112, 112)))
    # 288..303: shot_spin (16 frames)
    for i in range(16):
        mini_bytes.append(tone_for_spr32_bytes(resize_rgba_premul(mini["shot_spin"][int(round(i * 23 / 15.0))], 112, 112)))
    # 304..319: balloon_pop (4 swell frames [0,2,4,5] + 12 confetti pop frames [6..23])
    pop_indices = [0, 2, 4, 5] + [6 + int(round(j * 17 / 11.0)) for j in range(12)]
    for pi in pop_indices:
        mini_bytes.append(tone_for_spr32_bytes(resize_rgba_premul(mini["balloon_pop"][pi], 112, 112)))
    assert len(mini_bytes) == 320
    mb_mini = write_darkplaces_spr32(os.path.join(PROGS_DIR, "greenguy_mini.spr32"), mini_bytes, 112, 112, 98)
    print(f"      .spr32 sizes: proj={mb_proj:.2f}MB, burst={mb_burst:.2f}MB, mini={mb_mini:.2f}MB")

    print("[5/5] Packing 60 FPS WebP Atlases, Showcase Poster & Preview GIF...")
    manifest = {}
    c, r, kb = pack_webp_grid(vm["vm_idle"], 260, 278, 15, os.path.join(ATLAS_DIR, "vm_idle.webp"), quality=82)
    manifest["vm_idle"] = {"w": 260, "h": 278, "cols": c, "rows": r, "count": 180, "kb": round(kb, 1)}

    vm_act = vm["vm_shake"] + vm["vm_throw"] + vm["vm_reload"]  # 24 + 18 + 18 = 60
    c, r, kb = pack_webp_grid(vm_act, 260, 278, 12, os.path.join(ATLAS_DIR, "vm_action.webp"), quality=82)
    manifest["vm_action"] = {"w": 260, "h": 278, "cols": c, "rows": r, "count": 60, "kb": round(kb, 1)}

    c, r, kb = pack_webp_grid(proj, 152, 152, 12, os.path.join(ATLAS_DIR, "proj_jar.webp"), quality=84)
    manifest["proj_jar"] = {"w": 152, "h": 152, "cols": c, "rows": r, "count": 24, "kb": round(kb, 1)}

    c, r, kb = pack_webp_grid(burst, 192, 192, 12, os.path.join(ATLAS_DIR, "smoke_burst.webp"), quality=84)
    manifest["smoke_burst"] = {"w": 192, "h": 192, "cols": c, "rows": r, "count": 36, "kb": round(kb, 1)}

    for key_m, fn_m in [("scurry", "mini_scurry.webp"), ("wall_climb", "mini_wall.webp"), ("pogo_jump", "mini_pogo.webp")]:
        flat_m = [mini[key_m][d][f] for d in range(N_DIRS) for f in range(12)]
        c, r, kb = pack_webp_grid(flat_m, 128, 128, 12, os.path.join(ATLAS_DIR, fn_m), quality=82)
        manifest[key_m] = {"w": 128, "h": 128, "cols": c, "rows": r, "count": 192, "kb": round(kb, 1)}

    fx_flat = mini["shot_spin"] + mini["balloon_pop"]  # 24 + 24 = 48
    c, r, kb = pack_webp_grid(fx_flat, 140, 140, 12, os.path.join(ATLAS_DIR, "mini_fx.webp"), quality=84)
    manifest["mini_fx"] = {"w": 140, "h": 140, "cols": c, "rows": r, "count": 48, "kb": round(kb, 1)}

    with open(os.path.join(PACK_DIR, "manifest.json"), "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)

    save_poster_and_preview_gif(vm, proj, burst, mini)
    tot_kb = sum(v["kb"] for v in manifest.values())
    print(f"DONE in {time.time() - t0:.1f}s! Total WebP atlas payload: {tot_kb / 1024.0:.2f} MB")


if __name__ == "__main__":
    main()
