"""Generate animated 256x192 CRT monitor screen textures and scripts/lan_props.shader for BakersfieldQuake LAN rooms:
  - scr_q3a1 (8 frames): Quake III Arena - q3dm17 (The Longest Yard) rocket & railgun duel + full Q3 HUD
  - scr_q3a2 (8 frames): Quake III Arena - q3dm6 (The Campgrounds) railgun corkscrew + Quad Damage atrium + Q3 HUD
  - scr_cs1  (8 frames): Counter-Strike 1.5 - de_dust2 Long A M4A1 burst, green radar, killfeed, $16000 HUD
  - scr_cs2  (8 frames): Counter-Strike 1.5 - de_dust AK-47 -> AWP sniper scope shot -> Counter-Terrorists Win!
  - scr_win98a (8 frames): Windows 98 Classic Teal Desktop, pixel icons, Explorer, bouncing Winamp spectrum, NET SEND popup
  - scr_win98b (8 frames): Windows 98 GameSpy 3D LAN Server Browser -> flashing classic Windows 98 BSOD
  - scr_dead (1 frame): Shattered / imploded dark CRT phosphor tube

All self-lit rgbGen identity screen textures are scaled by BRIGHT=0.55 to match DarkPlaces ~2.5x HDR scene brightness
(same calibration as build_bklan_tv.py).
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 256, 192
BRIGHT = float(os.environ.get("LAN_SCR_BRIGHT", "0.56"))


def _font(size, bold=False, mono=False):
    if mono:
        names = ("consolab.ttf", "consola.ttf", "courbd.ttf", "cour.ttf", "lucon.ttf")
    elif bold:
        names = ("arialbd.ttf", "tahomabd.ttf", "verdanab.ttf", "impact.ttf", "arial.ttf")
    else:
        names = ("tahoma.ttf", "ms sans serif.fon", "verdana.ttf", "arial.ttf")
    for n in names:
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", n), size)
        except OSError:
            pass
    return ImageFont.load_default()


def _crt_postprocess(im: Image.Image, frame_idx: int = 0, glass_glare: bool = True) -> Image.Image:
    """Apply subtle CRT scanlines, RGB shadow-mask warmth, corner tube vignette, and HDR scene brightness scale."""
    arr = np.asarray(im.convert("RGB"), dtype=np.float32)

    # Subtle horizontal CRT scanlines (every 2nd row slightly darker, faint refresh roll)
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    xx = np.arange(W, dtype=np.float32)[None, :, None]
    scan = np.where((np.arange(H) % 2 == 1)[:, None, None], 0.86, 1.04)
    # Very gentle refresh band drifting down across frames
    band_y = (frame_idx * 24) % H
    dist_b = np.minimum(np.abs(yy[:, 0, 0] - band_y), H - np.abs(yy[:, 0, 0] - band_y))[:, None, None]
    refresh = 1.0 + 0.06 * np.exp(-(dist_b * dist_b) / (2.0 * 14.0 * 14.0))
    arr = arr * scan * refresh

    # Soft phosphor bloom from bright highlights
    hi = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=2.2))
    arr = arr * 0.88 + np.asarray(hi, dtype=np.float32) * 0.20

    # Subtle curved-tube corner vignette + dark bezel mask edge
    nx = (xx[:, :, 0] - (W - 1) * 0.5) / (W * 0.5)
    ny = (yy[:, :, 0] - (H - 1) * 0.5) / (H * 0.5)
    r4 = (nx * nx) ** 2 + (ny * ny) ** 2
    vig = np.clip(1.03 - 0.28 * r4, 0.55, 1.03)[:, :, None]
    arr *= vig

    if glass_glare:
        # Faint curved CRT glass reflection arc in upper-left quadrant
        gx = (nx + 0.42) * 1.1
        gy = (ny + 0.46) * 1.3
        glare = 18.0 * np.exp(-(gx * gx + gy * gy) * 4.5)[:, :, None]
        arr += glare

    arr = np.clip(arr * BRIGHT, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


# ==============================================================================
# 1. QUAKE III ARENA SCREENS (q3dm17 & q3dm6)
# ==============================================================================
def _draw_q3_hud(d: ImageDraw.ImageDraw, hp: int, ammo: int, armor: int, frags: int, frag_msg: str = ""):
    f_big = _font(22, bold=True)
    f_sm = _font(10, bold=True)
    f_tiny = _font(9, bold=True)

    # Top-right timer + frag counter boxes (authentic Q3A translucent blue/red boxes)
    d.rectangle([208, 6, 249, 18], fill=(18, 22, 34))
    d.text((212, 7), "08:%02d" % (49 - (frags % 9)), font=f_tiny, fill=(245, 245, 255))
    d.rectangle([208, 20, 228, 33], fill=(175, 28, 22))
    d.rectangle([229, 20, 249, 33], fill=(28, 65, 165))
    d.text((212, 21), str(frags), font=f_sm, fill=(255, 255, 255))
    d.text((233, 21), "14", font=f_sm, fill=(220, 230, 255))

    # Center white circle + dot Q3 crosshair
    cx, cy = W // 2, H // 2 - 4
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=(220, 245, 255), width=1)
    d.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill=(255, 255, 255))

    if frag_msg:
        tw = len(frag_msg) * 6
        d.rectangle([cx - tw // 2 - 4, 34, cx + tw // 2 + 4, 48], fill=(10, 12, 20))
        d.text((cx - tw // 2, 35), frag_msg, font=f_sm, fill=(255, 235, 90))

    # Bottom Q3A status bar: Sarge head + big yellow/red digits
    by = H - 30
    # Sarge helmet/head icon at x=54..74
    d.ellipse([54, by + 3, 73, by + 23], fill=(165, 112, 82), outline=(40, 22, 14))
    d.pieslice([53, by + 1, 74, by + 16], 180, 360, fill=(85, 95, 72))  # combat helmet / bandana
    d.rectangle([54, by + 8, 73, by + 11], fill=(195, 32, 24))           # red bandana
    d.rectangle([66, by + 18, 75, by + 20], fill=(210, 180, 130))        # cigar!
    d.ellipse([74, by + 17, 77, by + 20], fill=(255, 110, 20))           # glowing cigar tip

    hp_col = (255, 215, 45) if hp >= 50 else (255, 55, 35)
    d.text((9, by + 2), str(hp), font=f_big, fill=(20, 12, 6))
    d.text((8, by + 1), str(hp), font=f_big, fill=hp_col)

    # Center ammo count + rocket/slug icon
    d.text((103, by + 2), str(ammo), font=f_big, fill=(20, 12, 6))
    d.text((102, by + 1), str(ammo), font=f_big, fill=(255, 215, 45))
    d.polygon([(136, by + 19), (147, by + 8), (150, by + 11), (139, by + 22)], fill=(230, 95, 35))
    d.polygon([(146, by + 7), (152, by + 5), (150, by + 11)], fill=(255, 220, 90))

    # Right armor count + yellow Q3 shield icon
    d.text((177, by + 2), str(armor), font=f_big, fill=(20, 12, 6))
    d.text((176, by + 1), str(armor), font=f_big, fill=(255, 215, 45))
    d.polygon([(222, by + 5), (238, by + 5), (236, by + 16), (230, by + 24), (224, by + 16)],
              fill=(235, 190, 30), outline=(90, 60, 10))


def make_q3a1_frames():
    """Quake III Arena q3dm17 (The Longest Yard): space void, floating decks, jump pad, rocket explosion & railgun."""
    rng = random.Random(303)
    stars = [(rng.randint(0, W - 1), rng.randint(0, 128), rng.choice([(255, 255, 255), (180, 205, 255), (255, 195, 165)]))
             for _ in range(95)]
    frames = []
    for f in range(8):
        im = Image.new("RGB", (W, H), (8, 8, 18))
        # Space nebula background
        arr = np.asarray(im, dtype=np.float32)
        yy, xx = np.mgrid[0:H, 0:W]
        neb1 = np.exp(-((xx - 72) ** 2 / 3800.0 + (yy - 46) ** 2 / 1400.0))
        neb2 = np.exp(-((xx - 190) ** 2 / 4200.0 + (yy - 64) ** 2 / 1800.0))
        arr[:, :, 0] += neb1 * 88 + neb2 * 35
        arr[:, :, 1] += neb1 * 22 + neb2 * 26
        arr[:, :, 2] += neb1 * 55 + neb2 * 95
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)

        pan = int(round(math.sin(f * math.pi / 4.0) * 8))
        for sx, sy, scol in stars:
            d.point(((sx + pan) % W, sy), fill=scol)

        # Distant upper railgun platform (q3dm17 iconic suspended gothic steel deck)
        ux0, ux1 = 82 + pan, 178 + pan
        d.polygon([(ux0, 68), (ux1, 68), (ux1 - 12, 79), (ux0 + 12, 79)], fill=(68, 72, 84), outline=(112, 118, 134))
        d.rectangle([ux0 + 20, 79, ux0 + 28, 104], fill=(44, 48, 58))
        d.rectangle([ux1 - 28, 79, ux1 - 20, 104], fill=(44, 48, 58))
        # Red armor / Quad glow on upper platform
        d.ellipse([124 + pan, 56, 136 + pan, 68], fill=(255, 80, 35))

        # Midground main platform + angled jump pad Ramp
        d.polygon([(18 + pan, 112), (238 + pan, 112), (255, 191), (0, 191)], fill=(62, 58, 64))
        # Metal floor grid lines in perspective
        for gx in range(-3, 5):
            x_top = 128 + pan + gx * 26
            x_bot = 128 + pan + gx * 68
            d.line([(x_top, 112), (x_bot, 191)], fill=(38, 36, 42), width=1)
        for gy in (122, 136, 154, 174):
            d.line([(0, gy), (W, gy)], fill=(42, 40, 46), width=1)
        # Platform trim + glowing orange Q3 jump-pad circle
        d.line([(18 + pan, 112), (238 + pan, 112)], fill=(150, 135, 115), width=2)
        jp_x = 68 + pan
        d.ellipse([jp_x - 22, 128, jp_x + 22, 146], fill=(95, 45, 18), outline=(255, 145, 30), width=2)
        pulse = (f % 4) * 3
        d.ellipse([jp_x - 12 - pulse, 133, jp_x + 12 + pulse, 141], outline=(255, 220, 90), width=1)

        # Enemy player (bright green/orange Q3 competitive Visor model) strafing & jumping on upper deck
        ex = 128 + pan + int(math.sin(f * 0.9) * 22)
        ey = 58 - int(abs(math.sin(f * 0.8)) * 14)
        if f != 4:
            # Bright Q3 enemy silhouette
            d.rectangle([ex - 4, ey - 8, ex + 4, ey + 4], fill=(60, 245, 75))
            d.ellipse([ex - 3, ey - 13, ex + 3, ey - 7], fill=(255, 180, 60))
            d.line([(ex - 3, ey + 4), (ex - 5, ey + 11)], fill=(50, 190, 65), width=2)
            d.line([(ex + 3, ey + 4), (ex + 5, ey + 11)], fill=(50, 190, 65), width=2)

        # Weapon action: frames 0..4 Rocket flight + massive Q3 fireball; frames 5..7 Cyan spiral Railgun beam!
        cx, cy = W // 2, H // 2 - 4
        if f in (1, 2, 3):
            t = f / 3.5
            rx = int(172 + (ex - 172) * t)
            ry = int(136 + (ey - 136) * t)
            d.line([(178, 142), (rx, ry)], fill=(210, 195, 175), width=3)  # smoke trail
            d.ellipse([rx - 5, ry - 5, rx + 5, ry + 5], fill=(255, 235, 90), outline=(255, 95, 20))
        elif f == 4:
            # Iconic Q3A fiery rocket explosion on upper platform!
            d.ellipse([ex - 26, ey - 24, ex + 26, ey + 24], fill=(255, 95, 18))
            d.ellipse([ex - 17, ey - 16, ex + 17, ey + 16], fill=(255, 205, 55))
            d.ellipse([ex - 8, ey - 8, ex + 8, ey + 8], fill=(255, 255, 225))
        elif f in (6, 7):
            # Cyan/blue Q3A Railgun beam + spiral rings!
            d.line([(182, 146), (ex, ey)], fill=(70, 220, 255), width=3)
            d.line([(182, 146), (ex, ey)], fill=(230, 255, 255), width=1)
            for s_i in range(8):
                u = (s_i + 0.5) / 8.0
                sx_ = int(182 + (ex - 182) * u)
                sy_ = int(146 + (ey - 146) * u)
                r_ = int(6 * (1.0 - 0.5 * u))
                d.ellipse([sx_ - r_, sy_ - r_, sx_ + r_, sy_ + r_], outline=(35, 145, 255))

        # Q3A Rocket Launcher viewmodel (bottom right, kicking back on fire)
        kick = 7 if f in (1, 6) else (3 if f in (2, 7) else 0)
        vx, vy = 158 + kick, 126 + kick
        if f in (0, 1):
            d.ellipse([vx - 8, vy - 6, vx + 16, vy + 18], fill=(255, 185, 65))
        d.polygon([(vx, vy + 6), (vx + 22, vy - 2), (255, 152), (255, 191), (195, 191)],
                  fill=(118, 42, 34), outline=(45, 18, 16))
        d.polygon([(vx + 4, vy + 2), (vx + 26, vy + 4), (246, 168), (212, 178)],
                  fill=(152, 156, 166))
        d.ellipse([vx - 3, vy, vx + 11, vy + 14], fill=(28, 30, 36), outline=(185, 190, 200))

        frag_str = "You fragged Visor" if f in (4, 5, 7) else ""
        _draw_q3_hud(d, hp=125 - (f // 3) * 5, ammo=15 - (f // 2), armor=85, frags=18 + (1 if f >= 4 else 0), frag_msg=frag_str)
        frames.append(_crt_postprocess(im, f))
    return frames


def make_q3a2_frames():
    """Quake III Arena q3dm6 (The Campgrounds): warm gothic arches, Quad Damage bridge, Railgun duel."""
    frames = []
    for f in range(8):
        im = Image.new("RGB", (W, H), (36, 24, 18))
        d = ImageDraw.Draw(im)
        pan = int(round(math.cos(f * math.pi / 4.0) * 6))

        # Warm gothic stone ceiling, arches, pillars, torchlight
        d.rectangle([0, 0, W, 52], fill=(48, 32, 24))
        d.rectangle([0, 52, W, 118], fill=(78, 54, 38))
        for px in (28 + pan, 92 + pan, 164 + pan, 228 + pan):
            d.rectangle([px - 10, 18, px + 10, 128], fill=(96, 68, 48), outline=(46, 30, 20))
            # Wall flame sconce
            d.ellipse([px - 5, 48, px + 5, 62], fill=(255, 150, 35))
            d.ellipse([px - 2, 51, px + 2, 58], fill=(255, 245, 170))
        # Upper bridge + glowing blue Quad Damage symbol in center!
        d.rectangle([48 + pan, 72, 208 + pan, 82], fill=(112, 82, 58), outline=(52, 36, 26))
        qx = 128 + pan
        qy = 56 + int(math.sin(f * 0.9) * 3)
        d.ellipse([qx - 14, qy - 12, qx + 14, qy + 12], fill=(25, 85, 210))
        d.arc([qx - 8, qy - 8, qx + 8, qy + 6], 200, 340, fill=(160, 235, 255), width=3)
        d.line([(qx, qy - 8), (qx, qy + 9)], fill=(195, 245, 255), width=2)

        # Lower stone arena floor
        d.polygon([(0, 120), (W, 120), (W, 191), (0, 191)], fill=(86, 64, 48))
        for gy in (132, 148, 168):
            d.line([(0, gy), (W, gy)], fill=(58, 42, 32), width=1)

        # Opponent crossing bridge
        ex = 152 + pan - f * 7
        ey = 60
        d.rectangle([ex - 4, ey - 7, ex + 4, ey + 10], fill=(255, 70, 45))
        d.ellipse([ex - 3, ey - 12, ex + 3, ey - 7], fill=(255, 210, 140))

        # Green/cyan Railgun beam on frames 2, 3, 6
        if f in (2, 3, 6):
            d.line([(170, 144), (ex, ey)], fill=(65, 255, 120), width=4)
            d.line([(170, 144), (ex, ey)], fill=(230, 255, 240), width=1)
            d.ellipse([ex - 12, ey - 12, ex + 12, ey + 12], outline=(120, 255, 175), width=2)

        # Q3A Railgun viewmodel with glowing green energy core
        kick = 6 if f in (2, 6) else 0
        vx, vy = 156 + kick, 130 + kick
        d.polygon([(vx, vy + 4), (vx + 22, vy - 2), (255, 154), (255, 191), (190, 191)],
                  fill=(82, 88, 96), outline=(32, 36, 42))
        d.line([(vx + 6, vy + 4), (236, 168)], fill=(80, 255, 120), width=4)  # glowing railgun hum chamber

        msg = "IMPRESSIVE!" if f in (3, 4, 7) else ""
        _draw_q3_hud(d, hp=100, ammo=9 - (f // 3), armor=100, frags=23 + (1 if f >= 3 else 0), frag_msg=msg)
        frames.append(_crt_postprocess(im, f))
    return frames


# ==============================================================================
# 2. COUNTER-STRIKE 1.5 / 1.6 SCREENS (de_dust2 & de_dust AWP)
# ==============================================================================
def _draw_cs_hud(d: ImageDraw.ImageDraw, f: int, hp: int, armor: int, clip: int, money: int, kill_line: str = "", win_msg: str = ""):
    f_hud = _font(12, bold=True, mono=True)
    f_tiny = _font(9, bold=True)

    # Iconic translucent green circular CS Radar at top-left!
    d.ellipse([8, 8, 52, 52], fill=(16, 62, 28), outline=(70, 215, 95), width=1)
    d.line([(30, 8), (30, 52)], fill=(45, 135, 65), width=1)
    d.line([(8, 30), (52, 30)], fill=(45, 135, 65), width=1)
    d.line([(30, 30), (16, 14)], fill=(95, 240, 120), width=1)
    d.line([(30, 30), (44, 14)], fill=(95, 240, 120), width=1)
    # Teammate blips on radar
    d.rectangle([25 + (f % 3), 20, 27 + (f % 3), 22], fill=(130, 255, 150))
    d.rectangle([35, 24 - (f % 2), 37, 26 - (f % 2)], fill=(130, 255, 150))
    d.rectangle([29, 29, 31, 31], fill=(255, 255, 255))

    # Top-right Counter-Strike killfeed!
    if kill_line:
        d.text((126, 9), "Maverick", font=f_tiny, fill=(125, 185, 255))
        d.rectangle([172, 11, 190, 16], fill=(235, 190, 75))  # tiny rifle icon
        d.text((194, 9), "l33t_T", font=f_tiny, fill=(255, 95, 85))

    if win_msg:
        d.rectangle([48, 58, 208, 76], fill=(16, 22, 28))
        d.text((58, 61), win_msg, font=f_tiny, fill=(165, 215, 255))

    # Dynamic green 4-line CS crosshair
    cx, cy = W // 2, H // 2
    gap = 6 if (f % 2 == 1) else 3
    ln = 6
    for dx0, dy0, dx1, dy1 in ((-gap - ln, 0, -gap, 0), (gap, 0, gap + ln, 0),
                                (0, -gap - ln, 0, -gap), (0, gap, 0, gap + ln)):
        d.line([(cx + dx0, cy + dy0), (cx + dx1, cy + dy1)], fill=(65, 255, 75), width=1)

    # Classic amber-yellow CS 1.5 / 1.6 bottom HUD numbers (with subtle dark backing for bright sand contrast)!
    amber = (245, 175, 35)
    shd = (28, 22, 14)
    by = H - 20
    # Cross + HP | Shield + Armor
    d.rectangle([10, by + 4, 18, by + 6], fill=amber)
    d.rectangle([13, by + 1, 15, by + 9], fill=amber)
    d.text((22, by), str(hp), font=f_hud, fill=shd)
    d.text((21, by - 1), str(hp), font=f_hud, fill=amber)
    d.polygon([(54, by + 1), (62, by + 1), (61, by + 8), (58, by + 11), (55, by + 8)], outline=amber)
    d.text((67, by), str(armor), font=f_hud, fill=shd)
    d.text((66, by - 1), str(armor), font=f_hud, fill=amber)

    # Round timer center
    d.text((111, by), "01:%02d" % (48 - f), font=f_hud, fill=shd)
    d.text((110, by - 1), "01:%02d" % (48 - f), font=f_hud, fill=amber)

    # $16000 money + 30 | 90 ammo bottom-right
    d.text((193, by - 14), "$ %d" % money, font=f_hud, fill=shd)
    d.text((192, by - 15), "$ %d" % money, font=f_hud, fill=(85, 235, 95))
    d.text((197, by), "%02d | 90" % clip, font=f_hud, fill=shd)
    d.text((196, by - 1), "%02d | 90" % clip, font=f_hud, fill=amber)


def make_cs1_frames():
    """Counter-Strike 1.5 de_dust2 / de_dust sandstone corridor, crates, M4A1 viewmodel firing bursts."""
    frames = []
    for f in range(8):
        # Bright desert sky at top
        im = Image.new("RGB", (W, H), (165, 212, 238))
        d = ImageDraw.Draw(im)
        pan = int(round(math.sin(f * 0.7) * 5))

        # Left & right sandstone perspective walls (de_dust2 Long A / archway vibe!)
        d.polygon([(0, 0), (88 + pan, 42), (88 + pan, 122), (0, 165)], fill=(208, 182, 136), outline=(145, 120, 82))
        d.polygon([(W, 0), (172 + pan, 38), (172 + pan, 122), (W, 168)], fill=(186, 158, 114), outline=(132, 108, 72))
        # Sandstone block courses
        for sy in range(24, 150, 18):
            d.line([(0, sy), (88 + pan, int(42 + (sy / 165.0) * 80))], fill=(168, 142, 102), width=1)
            d.line([(W, sy), (172 + pan, int(38 + (sy / 168.0) * 84))], fill=(150, 126, 88), width=1)

        # Distant desert arch & tower
        d.rectangle([88 + pan, 56, 172 + pan, 122], fill=(224, 198, 150))
        d.rectangle([114 + pan, 72, 146 + pan, 122], fill=(56, 46, 36))  # dark tunnel arch!
        d.pieslice([114 + pan, 60, 146 + pan, 86], 180, 360, fill=(56, 46, 36))

        # Sandy ground + dust2 wooden bombsite crate with red "A" stencil
        d.polygon([(0, 165), (88 + pan, 122), (172 + pan, 122), (W, 168), (W, 191), (0, 191)], fill=(196, 170, 124))
        cx0 = 146 + pan
        d.rectangle([cx0, 96, cx0 + 28, 126], fill=(164, 126, 74), outline=(92, 68, 36), width=1)
        d.line([(cx0, 96), (cx0 + 28, 126)], fill=(118, 88, 48), width=1)
        d.line([(cx0 + 28, 96), (cx0, 126)], fill=(118, 88, 48), width=1)

        # Terrorist (Arctic / Phoenix / Leet Krew) peeking out of dark archway!
        tx = 128 + pan + (2 if f % 3 == 0 else -1)
        ty = 96
        if f < 6:
            d.rectangle([tx - 4, ty - 6, tx + 4, ty + 8], fill=(62, 74, 52))     # green shirt (Leet Krew!)
            d.rectangle([tx - 4, ty + 8, tx + 4, ty + 18], fill=(52, 68, 102))   # jeans
            d.ellipse([tx - 3, ty - 11, tx + 3, ty - 5], fill=(212, 172, 132))
            if f in (2, 4):
                d.ellipse([tx + 3, ty - 2, tx + 10, ty + 4], fill=(255, 225, 95))
        else:
            # Ragdoll downed by archway + red hit puff!
            d.rectangle([tx - 8, ty + 14, tx + 8, ty + 19], fill=(62, 74, 52))

        # CT Viewmodel: Colt M4A1 Carbine on right with navy sleeve, dark glove, carry handle, muzzle flash!
        firing = f in (1, 3, 5)
        rk = 5 if firing else 0
        mx, my = 148 + rk, 112 + rk
        if firing:
            # Iconic 4-spike CS muzzle flash!
            d.polygon([(mx - 22, my - 4), (mx - 6, my - 6), (mx - 4, my - 22), (mx + 2, my - 6),
                       (mx + 16, my - 4), (mx + 2, my + 2), (mx - 2, my + 16), (mx - 6, my + 2)],
                      fill=(255, 235, 115), outline=(255, 155, 35))
            # Flying brass shell casing
            d.rectangle([196 + f * 3, 108 - f * 2, 201 + f * 3, 110 - f * 2], fill=(245, 205, 75))

        # M4A1 barrel, handguard, receiver + carry handle, CT gloved left hand
        d.line([(mx - 6, my - 4), (mx + 24, my + 12)], fill=(42, 46, 52), width=4)         # barrel
        d.polygon([(mx + 12, my + 4), (mx + 42, my + 18), (mx + 36, my + 30), (mx + 8, my + 14)],
                  fill=(54, 58, 66), outline=(24, 26, 30))                                  # ribbed handguard
        d.polygon([(mx + 38, my + 16), (238, 168), (232, 191), (185, 191), (mx + 32, my + 32)],
                  fill=(44, 48, 56), outline=(20, 22, 26))                                  # receiver & stock
        d.line([(mx + 42, my + 12), (mx + 68, my + 26)], fill=(68, 72, 80), width=3)        # M4 carry handle!
        # CT dark glove + navy blue BDU sleeve
        d.ellipse([mx + 16, my + 14, mx + 34, my + 30], fill=(32, 34, 38))
        d.polygon([(mx + 24, my + 28), (mx + 44, my + 28), (195, 191), (156, 191)], fill=(38, 54, 86))

        _draw_cs_hud(d, f, hp=100 if f < 4 else 84, armor=96, clip=30 - f * 2, money=16000,
                     kill_line=("1" if f >= 6 else ""))
        frames.append(_crt_postprocess(im, f))
    return frames


def make_cs2_frames():
    """Counter-Strike 1.5 de_dust underpass stairs (homage to orcom 00894.jpg!) -> AWP Sniper Scope -> CT Win!"""
    frames = []
    for f in range(8):
        im = Image.new("RGB", (W, H), (145, 198, 220))
        d = ImageDraw.Draw(im)

        if f in (4, 5, 6):
            # ICONIC COUNTER-STRIKE AWP SNIPER DUAL-CROSSHAIR SCOPE VIEW!
            im.paste((12, 14, 16), [0, 0, W, H])
            cx, cy, r = W // 2, H // 2, 78
            # Zoomed sandstone archway inside lens
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(214, 188, 140))
            shk = -8 if f == 6 else 0
            d.rectangle([cx - 32, cy - 42 + shk, cx + 32, cy + 46 + shk], fill=(64, 52, 40))
            d.rectangle([cx - 74, cy + 24 + shk, cx + 74, cy + 78], fill=(182, 154, 108))
            # Zoomed Terrorist target in crosshairs!
            if f < 6:
                d.rectangle([cx - 8, cy - 10, cx + 8, cy + 20], fill=(72, 82, 58))
                d.ellipse([cx - 6, cy - 22, cx + 6, cy - 9], fill=(42, 42, 46))  # balaclava head
            else:
                # Muzzle flash bloom + blood mist on shot!
                d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(255, 230, 140))
            # Re-mask circular black scope border
            mask = Image.new("L", (W, H), 255)
            md = ImageDraw.Draw(mask)
            md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
            blk = Image.new("RGB", (W, H), (8, 8, 10))
            im.paste(blk, mask=mask)
            d = ImageDraw.Draw(im)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(42, 46, 52), width=2)
            # Thick outer + thin inner AWP scope lines + glowing red center dot!
            d.line([(cx - r, cy), (cx + r, cy)], fill=(10, 10, 10), width=1)
            d.line([(cx, cy - r), (cx, cy + r)], fill=(10, 10, 10), width=1)
            d.line([(cx - r, cy), (cx - 28, cy)], fill=(5, 5, 5), width=3)
            d.line([(cx + 28, cy), (cx + r, cy)], fill=(5, 5, 5), width=3)
            d.line([(cx, cy - r), (cx, cy - 28)], fill=(5, 5, 5), width=3)
            d.line([(cx, cy + 28), (cx, cy + r)], fill=(5, 5, 5), width=3)
            d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(255, 35, 35))
        else:
            # de_dust underpass sandstone stairs (direct homage to Orcom 2.mpg 00894.jpg!)
            d.polygon([(0, 0), (68, 36), (68, 134), (0, 178)], fill=(182, 160, 122))
            d.polygon([(W, 0), (188, 32), (188, 134), (W, 178)], fill=(204, 180, 138))
            # Stepped sandstone staircase rising in the middle
            for st in range(6):
                y0 = 138 - st * 11
                x_in = st * 6
                d.rectangle([58 + x_in, y0 - 8, 198 - x_in, y0], fill=(172 - st * 4, 150 - st * 4, 114 - st * 3),
                            outline=(118, 98, 72))
            d.polygon([(0, 178), (58, 138), (198, 138), (W, 178), (W, 191), (0, 191)], fill=(142, 124, 92))
            # Green AWP rifle barrel + wood/olive stock viewmodel on right
            bob = int(math.sin(f * 1.1) * 3)
            d.line([(126, 102 + bob), (178, 136 + bob)], fill=(38, 42, 46), width=4)       # long sniper barrel
            d.line([(146, 108 + bob), (182, 130 + bob)], fill=(28, 30, 34), width=6)       # telescopic scope!
            d.polygon([(168, 132 + bob), (242, 172), (235, 191), (184, 191), (162, 146 + bob)],
                      fill=(64, 92, 54), outline=(30, 44, 26))                             # classic green AWP stock!

        _draw_cs_hud(d, f, hp=100, armor=100, clip=10 if f < 6 else 9, money=16000,
                     kill_line=("1" if f >= 6 else ""),
                     win_msg=("Counter-Terrorists Win!" if f == 7 else ""))
        frames.append(_crt_postprocess(im, f))
    return frames


# ==============================================================================
# 3. WINDOWS 98 SCREENS (Desktop + Winamp + Explorer + NET SEND + BSOD)
# ==============================================================================
def _bevel_box(d: ImageDraw.ImageDraw, x0, y0, x1, y1, fill=(192, 192, 192), sunken=False):
    tl = (110, 110, 110) if sunken else (250, 250, 250)
    br = (250, 250, 250) if sunken else (95, 95, 95)
    d.rectangle([x0, y0, x1, y1], fill=fill)
    d.line([(x0, y0), (x1, y0)], fill=tl, width=1)
    d.line([(x0, y0), (x0, y1)], fill=tl, width=1)
    d.line([(x0, y1), (x1, y1)], fill=br, width=1)
    d.line([(x1, y0), (x1, y1)], fill=br, width=1)


def _draw_win98_shell(d: ImageDraw.ImageDraw, time_str="11:47 PM", active_tab="Games"):
    f_ic = _font(8)
    f_ui = _font(9, bold=True)
    f_reg = _font(9)

    # Classic Windows 98 Desktop Icons on left column
    icons = [
        ("My Computer", (185, 205, 235), "pc"),
        ("Network", (190, 215, 185), "net"),
        ("Recycle Bin", (210, 215, 220), "bin"),
        ("Quake III", (220, 48, 36), "q3"),
        ("Counter-Strike", (235, 185, 42), "cs"),
    ]
    for idx, (lbl, col, kind) in enumerate(icons):
        ix, iy = 14, 8 + idx * 32
        if kind == "pc":
            d.rectangle([ix, iy, ix + 14, iy + 11], fill=col, outline=(30, 40, 60))
            d.rectangle([ix + 2, iy + 2, ix + 12, iy + 8], fill=(60, 140, 210))
            d.rectangle([ix - 1, iy + 11, ix + 15, iy + 14], fill=(210, 205, 190), outline=(70, 70, 70))
        elif kind == "net":
            d.rectangle([ix - 1, iy, ix + 9, iy + 8], fill=(180, 200, 225), outline=(40, 50, 70))
            d.rectangle([ix + 6, iy + 5, ix + 16, iy + 13], fill=(180, 200, 225), outline=(40, 50, 70))
        elif kind == "bin":
            d.polygon([(ix + 1, iy + 2), (ix + 13, iy + 2), (ix + 11, iy + 14), (ix + 3, iy + 14)],
                      fill=col, outline=(70, 75, 80))
        elif kind == "q3":
            d.ellipse([ix, iy, ix + 14, iy + 14], fill=(35, 16, 16), outline=(235, 55, 35))
            d.text((ix + 3, iy + 1), "III", font=f_ic, fill=(255, 80, 45))
        else:
            d.ellipse([ix, iy, ix + 14, iy + 14], fill=(235, 185, 35), outline=(40, 30, 10))
            d.rectangle([ix + 5, iy + 3, ix + 9, iy + 11], fill=(25, 25, 25))
        d.text((4, iy + 16), lbl[:11], font=f_ic, fill=(255, 255, 255))

    # Bottom Windows 98 Taskbar (#C0C0C0)
    ty = H - 18
    _bevel_box(d, 0, ty, W - 1, H - 1, fill=(195, 195, 195))
    # Start button with 4-color Windows flag!
    _bevel_box(d, 2, ty + 2, 42, H - 3, fill=(195, 195, 195))
    d.rectangle([5, ty + 5, 8, ty + 8], fill=(230, 50, 35))
    d.rectangle([9, ty + 5, 12, ty + 8], fill=(55, 185, 65))
    d.rectangle([5, ty + 9, 8, ty + 12], fill=(45, 105, 225))
    d.rectangle([9, ty + 9, 12, ty + 12], fill=(245, 205, 35))
    d.text((15, ty + 4), "Start", font=f_ui, fill=(10, 10, 10))

    # Active taskbar window buttons
    _bevel_box(d, 46, ty + 2, 112, H - 3, fill=(175, 175, 175), sunken=True)
    d.text((50, ty + 4), active_tab, font=f_reg, fill=(10, 10, 10))
    _bevel_box(d, 115, ty + 2, 172, H - 3, fill=(195, 195, 195))
    d.text((119, ty + 4), "Winamp", font=f_reg, fill=(10, 10, 10))

    # System tray + clock
    _bevel_box(d, 202, ty + 2, W - 3, H - 3, fill=(186, 186, 186), sunken=True)
    d.text((207, ty + 4), time_str, font=f_ic, fill=(15, 15, 15))


def _draw_win98_window(d: ImageDraw.ImageDraw, x0, y0, x1, y1, title: str):
    f_ui = _font(9, bold=True)
    _bevel_box(d, x0, y0, x1, y1, fill=(195, 195, 195))
    # Classic Win98 gradient title bar (#000080 -> #1084D0)
    steps = max(1, (x1 - x0 - 6) // 4)
    for s in range(steps):
        u0 = s / steps
        col = (int(0 + 16 * u0), int(0 + 132 * u0), int(128 + 80 * u0))
        sx0 = x0 + 3 + int((x1 - x0 - 6) * u0)
        sx1 = x0 + 3 + int((x1 - x0 - 6) * (s + 1) / steps)
        d.rectangle([sx0, y0 + 3, sx1, y0 + 15], fill=col)
    d.text((x0 + 6, y0 + 4), title, font=f_ui, fill=(255, 255, 255))
    # _ [] X buttons
    for bi, sym in enumerate(("_", "o", "x")):
        bx = x1 - 34 + bi * 10
        _bevel_box(d, bx, y0 + 4, bx + 8, y0 + 13, fill=(195, 195, 195))
        d.text((bx + 2, y0 + 3), sym, font=_font(8, bold=True), fill=(10, 10, 10))


def make_win98a_frames():
    r"""Windows 98 Teal Desktop (#008080) + \\B-LAN\Games Explorer + Bouncing Winamp 2.7 + NET SEND popup!"""
    f_sm = _font(8)
    f_ui = _font(9, bold=True)
    frames = []
    for f in range(8):
        # Classic #008080 Win98 Teal!
        im = Image.new("RGB", (W, H), (0, 132, 132))
        d = ImageDraw.Draw(im)
        _draw_win98_shell(d, "11:47 PM", "\\\\B-LAN\\Games")

        # Open Windows 98 Explorer window (\\B-LAN\Games)
        _draw_win98_window(d, 58, 10, 246, 108, "\\\\B-LAN\\Games")
        d.text((64, 27), "File  Edit  View  Go  Favorites  Help", font=f_sm, fill=(20, 20, 20))
        _bevel_box(d, 62, 38, 242, 103, fill=(255, 255, 255), sunken=True)
        folders = [("Quake3", (235, 205, 95)), ("cstrike_15", (235, 205, 95)),
                   ("Maps_PK3", (235, 205, 95)), ("Patch132.exe", (120, 165, 235)),
                   ("hl1110.exe", (235, 145, 70)), ("Winamp27.exe", (245, 195, 55))]
        for fi, (fnm, fcol) in enumerate(folders):
            fx = 70 + (fi % 3) * 56
            fy = 43 + (fi // 3) * 28
            d.rectangle([fx, fy, fx + 14, fy + 10], fill=fcol, outline=(120, 95, 35))
            if fi == (f // 2) % 6:
                d.rectangle([fx - 2, fy + 12, fx + 44, fy + 21], fill=(0, 0, 128))
                d.text((fx, fy + 12), fnm[:9], font=f_sm, fill=(255, 255, 255))
            else:
                d.text((fx, fy + 12), fnm[:9], font=f_sm, fill=(15, 15, 15))

        # Iconic Winamp 2.7 dark charcoal player bottom-right with live bouncing spectrum bars!
        wx0, wy0, wx1, wy1 = 104, 112, 246, 166
        d.rectangle([wx0, wy0, wx1, wy1], fill=(32, 34, 42), outline=(95, 105, 120))
        d.rectangle([wx0 + 2, wy0 + 2, wx1 - 2, wy0 + 11], fill=(52, 62, 82))
        d.text((wx0 + 6, wy0 + 2), "WINAMP 2.72", font=f_sm, fill=(235, 210, 120))
        # Green digital timer + scrolling track title
        d.rectangle([wx0 + 5, wy0 + 14, wx0 + 62, wy0 + 40], fill=(10, 18, 12), outline=(60, 70, 75))
        d.text((wx0 + 9, wy0 + 15), "02:%02d" % (14 + f), font=f_ui, fill=(75, 255, 95))
        # 12 animated green/yellow/red spectrum analyzer bars!
        for bi in range(12):
            bh = int(4 + 13 * abs(math.sin(f * 1.15 + bi * 0.72)))
            bx = wx0 + 8 + bi * 4
            for by_i in range(0, bh, 2):
                bcol = (255, 55, 40) if by_i > 11 else ((250, 225, 55) if by_i > 6 else (65, 245, 85))
                d.rectangle([bx, wy0 + 38 - by_i, bx + 2, wy0 + 39 - by_i], fill=bcol)
        # Marquee track box + transport buttons
        d.rectangle([wx0 + 66, wy0 + 15, wx1 - 5, wy0 + 26], fill=(12, 20, 14))
        scroll = "1. Nine Inch Nails - Quake Theme (192kbps)   "
        sh = (f * 3) % 18
        d.text((wx0 + 68, wy0 + 16), scroll[sh:sh + 14], font=f_sm, fill=(85, 245, 95))
        for ti in range(5):
            _bevel_box(d, wx0 + 68 + ti * 13, wy0 + 38, wx0 + 78 + ti * 13, wy0 + 48, fill=(155, 162, 172))

        # Frames 5..7: Classic LAN party Windows Messenger Service "NET SEND" popup dialog!
        if f >= 5:
            _draw_win98_window(d, 48, 52, 212, 124, "Messenger Service")
            d.text((56, 70), "Message from ORCOM_HOST:", font=f_sm, fill=(10, 10, 10))
            d.text((56, 82), "Q3DM17 + CS DUST2 TOURNEY", font=f_ui, fill=(0, 0, 128))
            d.text((56, 94), "JOIN 192.168.0.14 NOW!!", font=f_sm, fill=(165, 20, 20))
            _bevel_box(d, 112, 106, 148, 119, fill=(195, 195, 195))
            d.text((123, 108), "OK", font=f_ui, fill=(10, 10, 10))

        # Crisp white Win98 mouse cursor moving across screen
        mx = 96 + f * 9 if f < 5 else 130
        my = 52 + (f % 3) * 14 if f < 5 else 112
        d.polygon([(mx, my), (mx, my + 11), (mx + 3, my + 8), (mx + 6, my + 13),
                   (mx + 8, my + 12), (mx + 5, my + 7), (mx + 9, my + 7)],
                  fill=(255, 255, 255), outline=(0, 0, 0))

        frames.append(_crt_postprocess(im, f))
    return frames


def make_win98b_frames():
    """Windows 98 GameSpy 3D / Half-Life LAN Server Browser (frames 0..5) -> Classic Win98 BSOD (frames 6..7)!"""
    f_sm = _font(8)
    f_mono = _font(9, bold=True, mono=True)
    frames = []
    for f in range(8):
        if f >= 6:
            # ICONIC WINDOWS 98 BLUE SCREEN OF DEATH (#0000AA)!
            im = Image.new("RGB", (W, H), (0, 0, 175))
            d = ImageDraw.Draw(im)
            d.rectangle([96, 26, 160, 38], fill=(185, 185, 185))
            d.text((104, 27), "Windows", font=f_mono, fill=(0, 0, 175))
            lines = [
                "A fatal exception 0E has occurred at",
                "0028:C0011E36 in VXD VMM(01) +",
                "00010E36. The current application",
                "will be terminated.",
                "",
                "* Press any key to terminate app.",
                "* Press CTRL+ALT+DEL to restart PC.",
                "  You will lose unsaved info.",
                "",
                "    Press any key to continue " + ("_" if f == 6 else " "),
            ]
            for li, ln in enumerate(lines):
                d.text((16, 48 + li * 12), ln, font=f_mono, fill=(245, 245, 255))
            frames.append(_crt_postprocess(im, f))
            continue

        im = Image.new("RGB", (W, H), (0, 132, 132))
        d = ImageDraw.Draw(im)
        _draw_win98_shell(d, "12:14 AM", "GameSpy 3D")

        _draw_win98_window(d, 52, 10, 250, 164, "GameSpy 3D - Local LAN Servers")
        _bevel_box(d, 56, 28, 246, 138, fill=(24, 30, 26), sunken=True)
        # Green GameSpy server rows!
        d.rectangle([58, 30, 244, 41], fill=(45, 65, 52))
        d.text((60, 31), "Server Name           Map      Plr Ping", font=f_sm, fill=(175, 255, 185))
        rows = [
            ("B-LAN 130A Q3 FFA", "q3dm17", "11/12", "3ms"),
            ("ORCOM CS 1.5 #1", "de_dust2", "16/16", "2ms"),
            ("ORCOM CS 1.5 #2", "de_aztec", "14/16", "4ms"),
            ("Larry's QuakeBox", "bklan4", " 8/12", "1ms"),
            ("MegaMan Rocketz", "q3dm6", " 6/8 ", "5ms"),
            ("Half-Life Crossfire", "crossfir", "10/16", "3ms"),
        ]
        sel = min(f, 5)
        for ri, (snm, mp, pl, pg) in enumerate(rows):
            ry = 44 + ri * 14
            if ri == sel:
                d.rectangle([58, ry - 1, 244, ry + 11], fill=(28, 115, 52))
            col = (120, 255, 135) if ri != sel else (255, 255, 165)
            d.text((60, ry), "%-18s %-8s %s %s" % (snm[:16], mp[:7], pl, pg), font=f_sm, fill=col)

        # Progress bar + Connect button
        _bevel_box(d, 58, 143, 178, 158, fill=(255, 255, 255), sunken=True)
        for bi in range(min(10, f * 2 + 2)):
            d.rectangle([60 + bi * 11, 145, 69 + bi * 11, 156], fill=(0, 0, 145))
        _bevel_box(d, 184, 143, 244, 158, fill=(195, 195, 195), sunken=(f == 5))
        d.text((196, 146), "Connect!", font=_font(9, bold=True), fill=(10, 10, 10))

        mx = 150 + f * 12
        my = 65 + f * 16
        d.polygon([(mx, my), (mx, my + 11), (mx + 3, my + 8), (mx + 6, my + 13),
                   (mx + 8, my + 12), (mx + 5, my + 7), (mx + 9, my + 7)],
                  fill=(255, 255, 255), outline=(0, 0, 0))
        frames.append(_crt_postprocess(im, f))
    return frames


def make_dead_screen():
    """Shattered / imploded dark CRT phosphor tube face."""
    im = Image.new("RGB", (W, H), (18, 20, 22))
    d = ImageDraw.Draw(im)
    cx, cy = W // 2 - 8, H // 2 + 4
    d.ellipse([cx - 42, cy - 34, cx + 42, cy + 34], fill=(8, 9, 10), outline=(48, 52, 56))
    d.ellipse([cx - 12, cy - 10, cx + 12, cy + 10], fill=(75, 48, 26))  # exposed copper electron gun neck
    rng = random.Random(99)
    for k in range(22):
        ang = 2 * math.pi * k / 22.0 + rng.uniform(-0.1, 0.1)
        r0 = rng.randint(12, 28)
        r1 = rng.randint(85, 145)
        pts = [(cx + int(r0 * math.cos(ang)), cy + int(r0 * math.sin(ang)))]
        for s in (0.4, 0.7, 1.0):
            ja = ang + rng.uniform(-0.08, 0.08)
            pts.append((cx + int((r0 + (r1 - r0) * s) * math.cos(ja)),
                        cy + int((r0 + (r1 - r0) * s) * math.sin(ja))))
        d.line(pts, fill=(135, 145, 152), width=1 if k % 3 else 2)
    return _crt_postprocess(im, 0, glass_glare=False)


def build_all_screens(progs_bklan_dir: str, scripts_dir: str):
    os.makedirs(progs_bklan_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)

    seqs = {
        "scr_q3a1": (7, make_q3a1_frames()),
        "scr_q3a2": (7, make_q3a2_frames()),
        "scr_cs1": (8, make_cs1_frames()),
        "scr_cs2": (6, make_cs2_frames()),
        "scr_win98a": (4, make_win98a_frames()),
        "scr_win98b": (3, make_win98b_frames()),
    }

    shader_blocks = [
        "// Generated by build_lan_props.py: animated CRT monitor screens & modded PC case glow\n"
    ]
    for name, (fps, frames) in seqs.items():
        frame_names = []
        for idx, im in enumerate(frames):
            rel = f"progs/bklan/{name}_{idx}"
            im.save(os.path.join(progs_bklan_dir, f"{name}_{idx}.png"))
            frame_names.append(rel)
            if idx == 0:
                # Base fallback texture matching shader name
                im.save(os.path.join(progs_bklan_dir, f"{name}.png"))
        shader_blocks.append(
            f"progs/bklan/{name}\n{{\n\tcull none\n\t{{\n\t\tanimmap {fps} {' '.join(frame_names)}\n\t\trgbGen identity\n\t}}\n}}\n"
        )

    dead_im = make_dead_screen()
    dead_im.save(os.path.join(progs_bklan_dir, "scr_dead.png"))
    shader_blocks.append(
        "progs/bklan/scr_dead\n{\n\tcull none\n\t{\n\t\tmap progs/bklan/scr_dead\n\t\trgbGen lightingDiffuse\n\t}\n}\n"
    )

    # Self-lit UV cold-cathode interior + red top neon shader for lan_pc2 (Chieftec modded tower)
    shader_blocks.append(
        "progs/bklan/scr_pc2uv\n{\n\tcull none\n\t{\n\t\tmap progs/bklan/scr_pc2uv\n\t\trgbGen identity\n\t}\n}\n"
    )

    shader_path = os.path.join(scripts_dir, "lan_props.shader")
    with open(shader_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(shader_blocks))
    print(f"Wrote {len(seqs)} animated CRT screen sequences + {shader_path}")
