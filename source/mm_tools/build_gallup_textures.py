"""build_gallup_textures.py — Generates all high-resolution textures for the 1:1 Quake replica
of 7705 Gallup Dr & Laurelglen neighborhood (Bakersfield, CA 93309).

Writes full-res PNGs (`ga_*.png` and `{ga_*.png`) to `BakersfieldQuake/textures/` and quarter-size
Quake-palette miptex lumps to `source/mm_tools/out/maps/gallup.wad`.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402

TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
WAD = os.path.join(HERE, "out", "maps", "gallup.wad")
rnd = random.Random(933097705)


def font(names, px):
    for n in names:
        for prefix in ("", "C:/Windows/Fonts/"):
            try:
                return ImageFont.truetype(prefix + n, px)
            except OSError:
                pass
    return ImageFont.load_default()


BOLD = ["arialbd.ttf", "calibrib.ttf", "DejaVuSans-Bold.ttf"]
BLACK = ["ariblk.ttf", "impact.ttf", "arialbd.ttf"]
SERIF = ["timesbd.ttf", "georgiab.ttf", "arialbd.ttf"]


def add_noise(im, amt=6, seed=None):
    r = random.Random(seed) if seed is not None else rnd
    rgba = im.mode == "RGBA"
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            n = r.randint(-amt, amt)
            p = px[x, y]
            if rgba:
                if p[3] == 0:
                    continue
                px[x, y] = (
                    max(0, min(255, p[0] + n)),
                    max(0, min(255, p[1] + n)),
                    max(0, min(255, p[2] + n)),
                    p[3],
                )
            else:
                px[x, y] = (
                    max(0, min(255, p[0] + n)),
                    max(0, min(255, p[1] + n)),
                    max(0, min(255, p[2] + n)),
                )
    return im


def dim(im, k=0.88):
    if im.mode == "RGBA":
        rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(k)
        rgb.putalpha(im.getchannel("A"))
        return rgb
    return ImageEnhance.Brightness(im.convert("RGB")).enhance(k)


def stucco(col=(224, 218, 208), amt=8, seed=10):
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    for _ in range(180):
        x, y = r.randint(-24, S), r.randint(-24, S)
        rx, ry = r.randint(10, 36), r.randint(10, 36)
        dv = r.randint(-7, 7)
        c = tuple(max(0, min(255, col[i] + dv)) for i in range(3))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + rx, y + dy + ry], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(1.3))
    return dim(add_noise(im, amt, seed + 1), 0.88)


def shingles(base=(122, 110, 98), seed=20):
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    row_h = 32
    for row in range(S // row_h):
        y0 = row * row_h
        off = (row % 2) * 32
        for col in range(-1, S // 64 + 2):
            x0 = col * 64 + off + r.randint(-2, 2)
            dv = r.randint(-14, 14)
            c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
            d.rectangle([x0, y0, x0 + 62, y0 + row_h - 2], fill=c)
        d.line([(0, y0 + row_h - 1), (S, y0 + row_h - 1)], fill=tuple(max(0, v - 32) for v in base), width=2)
    return dim(add_noise(im, 7, seed + 1), 0.88)


def wood_siding(base=(72, 54, 44), boards=8, vert=False, seed=30):
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    step = S // boards
    for k in range(boards):
        dv = r.randint(-8, 8)
        c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
        if vert:
            d.rectangle([k * step, 0, (k + 1) * step - 2, S], fill=c)
            d.line([(k * step, 0), (k * step, S)], fill=tuple(max(0, v - 26) for v in base), width=2)
        else:
            d.rectangle([0, k * step, S, (k + 1) * step - 2], fill=c)
            d.line([(0, (k + 1) * step - 1), (S, (k + 1) * step - 1)], fill=tuple(max(0, v - 28) for v in base), width=2)
    return dim(add_noise(im, 5, seed + 1), 0.90)


def slump_block(base=(214, 198, 174), seed=40):
    """Laurelglen tan/cream slump-stone / cinderblock perimeter wall."""
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    rh = 32
    mortar = tuple(max(0, v - 28) for v in base)
    for row in range(S // rh):
        y0 = row * rh
        off = (row % 2) * 32
        for c_i in range(-1, S // 64 + 2):
            x0 = c_i * 64 + off
            dv = r.randint(-9, 9)
            c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
            d.rectangle([x0 + 1, y0 + 1, x0 + 62, y0 + rh - 2], fill=c)
        d.line([(0, y0), (S, y0)], fill=mortar, width=2)
    return dim(add_noise(im, 6, seed + 1), 0.88)


# ============================================================================== 7705 GALLUP DR HERO TEXTURES
def garage_7705():
    """Double taupe-grey 4-row sectional garage door with 8 small rectangular top windows (img_011.jpg!)."""
    W, H = 512, 256
    base = (182, 172, 166)
    im = Image.new("RGB", (W, H), base)
    d = ImageDraw.Draw(im)
    # 4 horizontal sections, 8 columns across
    for row in range(4):
        y0 = 8 + row * 60
        y1 = y0 + 54
        d.line([(0, y1 + 3), (W, y1 + 3)], fill=(138, 128, 122), width=2)
        for col in range(8):
            x0 = 10 + col * 62
            x1 = x0 + 54
            d.rectangle([x0, y0 + 4, x1, y1 - 2], outline=(148, 138, 132), width=2)
            if row == 0:
                # 8 small dark rectangular windows in top row (img_011.jpg!)
                d.rectangle([x0 + 3, y0 + 6, x1 - 3, y1 - 6], fill=(32, 34, 38), outline=(216, 210, 204), width=2)
                d.line([(x0 + 6, y0 + 9), (x0 + 20, y1 - 9)], fill=(58, 64, 72), width=2)
            else:
                d.rectangle([x0 + 4, y0 + 8, x1 - 4, y1 - 6], outline=(196, 188, 182), width=1)
    return dim(add_noise(im, 4, 77051), 0.90)


def garage_7701():
    """White double garage door of 7701 (east neighbor) with 8 small arched/fanlight windows (img_016.jpg!)."""
    W, H = 512, 256
    base = (232, 234, 236)
    im = Image.new("RGB", (W, H), base)
    d = ImageDraw.Draw(im)
    for row in range(4):
        y0 = 8 + row * 60
        y1 = y0 + 54
        d.line([(0, y1 + 3), (W, y1 + 3)], fill=(190, 194, 198), width=2)
        for col in range(8):
            x0 = 10 + col * 62
            x1 = x0 + 54
            if row == 0:
                # Fanlight half-arch window!
                d.pieslice([x0 + 3, y0 + 8, x1 - 3, y0 + 62], 180, 360, fill=(36, 40, 44), outline=(205, 208, 212), width=2)
                cx = (x0 + x1) // 2
                for ang in (215, 250, 290, 325):
                    rx = cx + int(22 * math.cos(math.radians(ang)))
                    ry = (y0 + 35) + int(22 * math.sin(math.radians(ang)))
                    d.line([(cx, y0 + 35), (rx, ry)], fill=(215, 218, 222), width=1)
            else:
                d.rectangle([x0 + 3, y0 + 6, x1 - 3, y1 - 4], outline=(204, 208, 212), width=2)
    return dim(add_noise(im, 3, 77011), 0.90)


def arch_window_7705():
    """Tall arched clerestory window above 7705's front door + '7705' transom beam below (img_011.jpg!)."""
    W, H = 256, 256
    stuc = (218, 212, 204)
    im = Image.new("RGB", (W, H), stuc)
    d = ImageDraw.Draw(im)
    # Upper arched dark-bronze glass window (y = 18 .. 188)
    d.pieslice([18, 20, W - 18, 240], 180, 360, fill=(38, 44, 42), outline=(64, 50, 42), width=5)
    d.rectangle([18, 130, W - 18, 188], fill=(38, 44, 42), outline=(64, 50, 42), width=4)
    # Subtle tree/sky reflection + center vertical mullion seen in img_011.jpg
    d.pieslice([28, 30, W - 28, 230], 200, 265, fill=(68, 82, 64))
    d.line([(W // 2, 22), (W // 2, 188)], fill=(58, 46, 38), width=4)
    d.line([(18, 188), (W - 18, 188)], fill=(58, 46, 38), width=5)
    # Stucco transom beam below arch (y = 190 .. 255) with centered house number '7705'
    d.rectangle([0, 190, W, H], fill=stuc)
    f = font(BOLD, 34)
    txt = "7705"
    bb = d.textbbox((0, 0), txt, font=f)
    tw = bb[2] - bb[0]
    d.text(((W - tw) // 2, 204), txt, font=f, fill=(44, 34, 28))
    return dim(add_noise(im, 4, 77052), 0.90)


def entry_door_7705():
    """Dark espresso-brown double/wide paneled front entry doors of 7705 Gallup Dr (img_011.jpg!)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (44, 33, 28))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, W - 6, H - 2], outline=(28, 20, 16), width=5)
    d.line([(W // 2, 8), (W // 2, H - 4)], fill=(24, 18, 14), width=4)
    for sx in (18, W // 2 + 12):
        pw = W // 2 - 30
        for py, ph in ((20, 62), (96, 78), (188, 52)):
            d.rectangle([sx, py, sx + pw, py + ph], outline=(62, 48, 40), width=3)
            d.rectangle([sx + 4, py + 4, sx + pw - 4, py + ph - 4], outline=(30, 22, 18), width=2)
    # Brass handle set
    d.rectangle([W // 2 - 14, 128, W // 2 - 6, 156], fill=(178, 152, 88))
    d.rectangle([W // 2 + 6, 128, W // 2 + 14, 156], fill=(178, 152, 88))
    return add_noise(im, 3, 77053)


def awning_bw():
    """Crisp black-and-white vertical-striped window awning over 7705's right front window (img_011.jpg!)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (240, 240, 238))
    d = ImageDraw.Draw(im)
    stripes = 9
    sw = W / stripes
    for i in range(stripes):
        col = (30, 32, 34) if (i % 2 == 0) else (240, 240, 236)
        d.rectangle([int(i * sw), 0, int((i + 1) * sw) + 1, H], fill=col)
    # Bottom valance shadow seam
    d.line([(0, H - 22), (W, H - 22)], fill=(90, 90, 90), width=3)
    return dim(add_noise(im, 4, 77054), 0.92)


def window_3pane(frame_col=(52, 42, 36), blinds=True):
    """Dark-bronze 3-pane horizontal slider window with interior blinds (7705 & neighbors in img_011.jpg!)."""
    W, H = 256, 160
    im = Image.new("RGB", (W, H), (44, 50, 54))
    d = ImageDraw.Draw(im)
    if blinds:
        for y in range(10, H - 10, 8):
            d.line([(10, y), (W - 10, y)], fill=(168, 164, 156), width=3)
            d.line([(10, y + 3), (W - 10, y + 3)], fill=(72, 74, 78), width=2)
    # Subtle glass reflection tint
    for x in range(10, W - 10):
        if (x // 28) % 2 == 0:
            d.line([(x, 8), (x, H - 8)], fill=(58, 66, 72), width=1)
    d.rectangle([0, 0, W - 1, H - 1], outline=frame_col, width=8)
    d.line([(W // 3, 4), (W // 3, H - 4)], fill=frame_col, width=6)
    d.line([(2 * W // 3, 4), (2 * W // 3, H - 4)], fill=frame_col, width=6)
    return dim(add_noise(im, 3, 77055), 0.92)


def curb_7705():
    """Concrete curb stencil '7705' visible on the curb in img_011.jpg!"""
    W, H = 256, 64
    im = Image.new("RGB", (W, H), (188, 184, 176))
    d = ImageDraw.Draw(im)
    d.rectangle([36, 10, W - 36, H - 10], fill=(236, 236, 232), outline=(60, 60, 60), width=2)
    f = font(BLACK, 34)
    txt = "7705"
    bb = d.textbbox((0, 0), txt, font=f)
    d.text(((W - (bb[2] - bb[0])) // 2, 11), txt, font=f, fill=(28, 28, 28))
    return dim(add_noise(im, 5, 77056), 0.88)


def brick_fireplace():
    """Warm red-brown 1983 running-bond brick for 7705's living room fireplace & 7701's chimney."""
    r = random.Random(77057)
    S = 256
    im = Image.new("RGB", (S, S), (168, 158, 148))
    d = ImageDraw.Draw(im)
    bh, bw = 16, 48
    for row in range(S // bh):
        y0 = row * bh
        off = (row % 2) * (bw // 2)
        for col in range(-1, S // bw + 2):
            x0 = col * bw + off
            c = (
                max(60, min(210, 148 + r.randint(-26, 24))),
                max(35, min(140, 72 + r.randint(-16, 16))),
                max(28, min(115, 56 + r.randint(-12, 12))),
            )
            d.rectangle([x0 + 2, y0 + 2, x0 + bw - 2, y0 + bh - 2], fill=c)
    return dim(add_noise(im, 6, 77058), 0.90)


def oak_cabinet():
    """Honest neutral 1983/classic raised-panel kitchen cabinetry for 7705 kitchen."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (176, 136, 92))
    d = ImageDraw.Draw(im)
    for col in range(2):
        x0 = 8 + col * 124
        x1 = x0 + 116
        d.rectangle([x0, 10, x1, H - 10], fill=(168, 128, 84), outline=(112, 80, 48), width=4)
        d.rectangle([x0 + 14, 24, x1 - 14, H - 24], outline=(124, 90, 54), width=3)
    # Wood grain lines
    r = random.Random(77059)
    for y in range(0, H, 3):
        dv = r.randint(-8, 8)
        d.line([(0, y), (W, y)], fill=(170 + dv, 130 + dv, 86 + dv), width=1)
    for col in range(2):
        x0 = 8 + col * 124
        x1 = x0 + 116
        d.rectangle([x0, 10, x1, H - 10], outline=(106, 74, 42), width=4)
        d.rectangle([x0 + 14, 24, x1 - 14, H - 24], outline=(122, 88, 52), width=3)
    return dim(add_noise(im, 4, 77060), 0.90)


def hvac_carrier():
    """Feb 2025 Carrier grey Louvered HVAC condenser unit in 7705's backyard!"""
    S = 256
    im = Image.new("RGB", (S, S), (148, 152, 156))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, S - 5, S - 5], outline=(96, 100, 104), width=6)
    for y in range(28, S - 24, 10):
        d.line([(20, y), (S - 20, y)], fill=(68, 72, 76), width=4)
    # Small blue oval Carrier badge (no invented fine text, clean emblem)
    d.ellipse([S // 2 - 26, 10, S // 2 + 26, 26], fill=(28, 68, 138), outline=(220, 226, 235), width=2)
    return dim(add_noise(im, 4, 77061), 0.90)


# ============================================================================== FOLIAGE & FENCES (ALPHA `{ga_*`)
def foliage_card(cols, seed=80):
    """Lush alpha-masked tree crown card (`{ga_*`)."""
    r = random.Random(seed)
    S = 256
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(380):
        ang = r.uniform(0, math.tau)
        rad = (r.random() ** 0.62) * 108
        cx = int(128 + math.cos(ang) * rad)
        cy = int(132 + math.sin(ang) * rad * 0.88)
        rx, ry = r.randint(8, 22), r.randint(7, 18)
        c = r.choice(cols)
        dv = r.randint(-14, 14)
        rgba = (max(0, min(255, c[0] + dv)), max(0, min(255, c[1] + dv)), max(0, min(255, c[2] + dv)), 255)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=rgba)
    return add_noise(im, 5, seed + 1)


def photinia_hedge():
    """Crossway Baptist Church black wrought-iron fence + red-tipped green hedge (img_118, img_119!)."""
    r = random.Random(881)
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (36, 58, 34))
    d = ImageDraw.Draw(im)
    for _ in range(700):
        x, y = r.randint(0, W - 1), r.randint(0, H - 1)
        rx, ry = r.randint(5, 14), r.randint(4, 12)
        # Red tips concentrated near top and scattered across outer shoots!
        if y < 56 or r.random() < 0.24:
            c = (r.randint(135, 185), r.randint(36, 58), r.randint(34, 52))
        else:
            c = (r.randint(32, 58), r.randint(62, 96), r.randint(30, 52))
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=c)
    # Black vertical wrought-iron fence pickets & horizontal rails in front (img_119.jpg!)
    d.rectangle([0, 14, W, 22], fill=(24, 26, 28))
    d.rectangle([0, H - 24, W, H - 16], fill=(24, 26, 28))
    for px in range(8, W, 16):
        d.rectangle([px, 10, px + 4, H - 4], fill=(22, 24, 26))
    return dim(add_noise(im, 4, 882), 0.90)


def hedge_green():
    """Lush clipped California green boxwood/privet hedge without iron bars (7705 front hedge & shrubs!)."""
    r = random.Random(883)
    S = 256
    im = Image.new("RGB", (S, S), (46, 84, 38))
    d = ImageDraw.Draw(im)
    for _ in range(950):
        x, y = r.randint(-12, S), r.randint(-12, S)
        rx, ry = r.randint(5, 13), r.randint(4, 11)
        c = (
            max(20, min(140, 56 + r.randint(-20, 26))),
            max(45, min(175, 98 + r.randint(-26, 32))),
            max(18, min(110, 44 + r.randint(-16, 20))),
        )
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx - rx, y + dy - ry, x + dx + rx, y + dy + ry], fill=c)
    return dim(add_noise(im, 4, 884), 0.90)


# ============================================================================== ROAD STENCILS & STREET SIGNS
def road_stencil_tex(text, seed=901):
    """Crisp weathered white asphalt stencil ('Gallup Dr', 'Litchfield Dr', 'Deming Ct', 'Olympia Dr')."""
    W, H = 512, 128
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(BOLD, 72)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((W - tw) // 2, (H - th) // 2 - 8), text, font=f, fill=(236, 236, 232, 255))
    # Subtle tire wear speckles so it blends naturally with asphalt
    r = random.Random(seed)
    px = im.load()
    for _ in range(900):
        x, y = r.randint(0, W - 1), r.randint(0, H - 1)
        if r.random() < 0.35:
            px[x, y] = (0, 0, 0, 0)
    return im


def double_yellow_tex():
    """Double yellow center lines for Olympia Dr (img_061, img_087!)."""
    W, H = 128, 256
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([42, 0, 56, H], fill=(228, 184, 42, 255))
    d.rectangle([72, 0, 86, H], fill=(228, 184, 42, 255))
    return add_noise(im, 5, 910)


def green_street_sign(main_txt, sub_txt=""):
    """Bakersfield green reflective street-name blade ('LITCHFIELD DR', 'PRESCOTT WAY', 'DEMING CT <- 3300')."""
    W, H = 256, 64
    im = Image.new("RGB", (W, H), (22, 108, 62))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, W - 4, H - 4], outline=(238, 242, 238), width=3)
    f = font(BOLD, 30 if not sub_txt else 26)
    bb = d.textbbox((0, 0), main_txt, font=f)
    if sub_txt:
        d.text((14, 16), main_txt, font=f, fill=(244, 246, 244))
        fs = font(BOLD, 16)
        d.text((W - 76, 24), sub_txt, font=fs, fill=(244, 246, 244))
    else:
        d.text(((W - (bb[2] - bb[0])) // 2, 15), main_txt, font=f, fill=(244, 246, 244))
    return im


def speed_55_sign():
    """'SPEED LIMIT 55' sign on Gosford Rd in front of Crossway Baptist Church (img_118.jpg!)."""
    W, H = 128, 160
    im = Image.new("RGB", (W, H), (242, 242, 240))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, W - 5, H - 5], outline=(24, 24, 24), width=4)
    f1 = font(BOLD, 22)
    f2 = font(BLACK, 64)
    d.text((26, 14), "SPEED", font=f1, fill=(20, 20, 20))
    d.text((31, 38), "LIMIT", font=f1, fill=(20, 20, 20))
    d.text((22, 66), "55", font=f2, fill=(20, 20, 20))
    return im


# ============================================================================== LANDMARKS: CROSSWAY, LAURELWOOD, ALBERTSONS
def crossway_sign():
    """Blue 'CROSSWAY' monument sign with white cross inside the 'O' (img_118.jpg!)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (36, 74, 128))
    d = ImageDraw.Draw(im)
    # Soft sky/cloud gradient reflection seen on sign face in img_118.jpg
    for y in range(H):
        t = y / H
        r_c = int(34 + 28 * (1.0 - abs(2 * t - 1)))
        g_c = int(72 + 38 * (1.0 - abs(2 * t - 1)))
        b_c = int(126 + 44 * (1.0 - abs(2 * t - 1)))
        d.line([(0, y), (W, y)], fill=(r_c, g_c, b_c))
    d.rectangle([3, 3, W - 4, H - 4], outline=(218, 222, 228), width=5)
    f = font(SERIF, 36)
    # Draw 'CR', custom 'O' with white cross inside, 'SSWAY'!
    d.text((16, 36), "CR", font=f, fill=(245, 248, 252))
    # O circle + cross inside!
    ox, oy, orad = 89, 55, 17
    d.ellipse([ox - orad, oy - orad, ox + orad, oy + orad], outline=(245, 248, 252), width=4)
    d.line([(ox, oy - orad + 3), (ox, oy + orad - 3)], fill=(245, 248, 252), width=3)
    d.line([(ox - orad + 4, oy - 3), (ox + orad - 4, oy - 3)], fill=(245, 248, 252), width=3)
    d.text((110, 36), "SSWAY", font=f, fill=(245, 248, 252))
    return dim(add_noise(im, 3, 920), 0.94)


def base_3200():
    """Concrete base of Crossway sign with '3200' address (img_118.jpg!)."""
    W, H = 256, 64
    im = Image.new("RGB", (W, H), (196, 190, 178))
    d = ImageDraw.Draw(im)
    f = font(BOLD, 30)
    d.text((28, 16), "3200", font=f, fill=(48, 44, 40))
    return dim(add_noise(im, 5, 921), 0.90)


def portico_7900():
    """Tan stucco Albertsons corner portico lintel with recessed square, brown fascia & '7900' (img_127.jpg!)."""
    W, H = 256, 128
    stuc = (218, 202, 174)
    im = Image.new("RGB", (W, H), stuc)
    d = ImageDraw.Draw(im)
    # Subtle stucco panel joint lines + small recessed architectural square (img_127.jpg!)
    d.line([(0, 38), (W, 38)], fill=(168, 152, 126), width=2)
    d.line([(W // 2, 0), (W // 2, H - 24)], fill=(176, 160, 134), width=1)
    d.rectangle([118, 30, 138, 50], fill=(192, 176, 148), outline=(120, 104, 84), width=2)
    # Dark brown lower beam fascia + crisp bronze '7900' address digits above it
    d.rectangle([0, H - 24, W, H], fill=(96, 74, 58))
    d.line([(0, H - 25), (W, H - 25)], fill=(142, 120, 98), width=2)
    f = font(BOLD, 24)
    d.text((99, H - 52), "7900", font=f, fill=(44, 34, 28))
    return dim(add_noise(im, 5, 922), 0.92)


def albertsons_pediment():
    """Tan stucco Albertsons gable wall with blue logo medallion & white 'Albertsons' channel letters (img_125.jpg!)."""
    W, H = 512, 256
    stuc = (218, 204, 178)
    im = Image.new("RGB", (W, H), stuc)
    d = ImageDraw.Draw(im)
    # Subtle drop shadow + blue leaf/A medallion + bold white 'Albertsons' letters
    d.ellipse([42, 92, 98, 164], fill=(22, 88, 168), outline=(245, 248, 252), width=4)
    d.polygon([(70, 104), (54, 150), (86, 150)], fill=(245, 248, 252))
    f = font(SERIF, 74)
    d.text((112, 92), "Albertsons", font=f, fill=(130, 120, 104))
    d.text((108, 88), "Albertsons", font=f, fill=(248, 248, 246))
    # Lower brown architectural band (img_125.jpg!)
    d.rectangle([0, H - 36, W, H], fill=(128, 102, 80))
    d.rectangle([0, H - 22, W, H - 8], fill=(236, 234, 228))
    return dim(add_noise(im, 5, 930), 0.92)


def albertsons_window():
    """Dark storefront windows of Albertsons with blue Oreo display & 'Shop happy' sign (img_125.jpg!)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (44, 42, 38))
    d = ImageDraw.Draw(im)
    # Warm interior ceiling lights reflection
    for row_y in (38, 62):
        for lx in range(24, W - 24, 56):
            d.line([(lx, row_y), (lx + 32, row_y)], fill=(225, 218, 188), width=3)
    # 4 vertical dark bronze mullions
    for mx in (0, 128, 256, 384, W - 6):
        d.rectangle([mx, 0, mx + 8, H], fill=(58, 56, 54))
    d.rectangle([0, 0, W, 10], fill=(58, 56, 54))
    d.rectangle([0, H - 12, W, H], fill=(58, 56, 54))
    # Oreo blue display pyramids in panel 2 (img_125.jpg!)
    for ox in (148, 196):
        d.rectangle([ox, 178, ox + 42, H - 14], fill=(28, 62, 138), outline=(180, 200, 240), width=2)
        d.polygon([(ox + 2, 178), (ox + 21, 150), (ox + 40, 178)], fill=(120, 175, 225))
        d.polygon([(ox + 15, 152), (ox + 21, 124), (ox + 27, 152)], fill=(224, 176, 72))
    # 'Shop happy' sign in panel 4 (img_125.jpg!)
    d.rectangle([404, 166, 492, H - 16], fill=(234, 236, 240), outline=(36, 84, 158), width=3)
    f = font(BOLD, 18)
    d.text((414, 182), "Shop", font=f, fill=(24, 78, 156))
    d.text((412, 204), "happy", font=f, fill=(24, 78, 156))
    return dim(add_noise(im, 3, 931), 0.92)


def red_clay_tile():
    """Spanish red clay barrel-tile roof trim of Albertsons (img_125.jpg!)."""
    r = random.Random(932)
    S = 256
    im = Image.new("RGB", (S, S), (166, 78, 52))
    d = ImageDraw.Draw(im)
    bw = 32
    for col in range(S // bw):
        x0 = col * bw
        for row in range(S // 64):
            y0 = row * 64
            dv = r.randint(-14, 14)
            d.rectangle([x0 + 2, y0 + 2, x0 + bw - 3, y0 + 62], fill=(172 + dv, 82 + dv // 2, 54 + dv // 2))
            d.line([(x0 + 6, y0 + 4), (x0 + 6, y0 + 60)], fill=(202, 110, 78), width=3)
            d.line([(x0 + bw - 3, y0), (x0 + bw - 3, y0 + 64)], fill=(96, 40, 26), width=3)
    return dim(add_noise(im, 5, 933), 0.90)


def laurelwood_sign():
    """Laurelwood Gardens & West Villas white/sage monument board (img_067, img_089: 'RENTAL OFFICE ->')."""
    W, H = 256, 192
    im = Image.new("RGB", (W, H), (238, 240, 238))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 48, W, H], fill=(138, 152, 118))
    d.rectangle([4, 4, W - 5, H - 5], outline=(96, 108, 84), width=4)
    # Green leaf emblem + RENTAL OFFICE + right arrow (visible in img_089/090!)
    d.polygon([(46, 28), (68, 18), (60, 44)], fill=(54, 118, 68))
    f1 = font(SERIF, 20)
    f2 = font(BOLD, 28)
    d.text((76, 22), "Laurelwood", font=f1, fill=(44, 68, 52))
    d.text((54, 58), "RENTAL", font=f2, fill=(32, 42, 48))
    d.text((58, 90), "OFFICE", font=f2, fill=(32, 42, 48))
    # Crisp black arrow below
    d.rectangle([76, 126, 158, 134], fill=(28, 32, 36))
    d.polygon([(156, 118), (182, 130), (156, 142)], fill=(28, 32, 36))
    return dim(add_noise(im, 3, 940), 0.92)


# ============================================================================== HIGH-VISIBILITY FUN JUMP PADS!
def jumppad_tex(sky_mode=False):
    """Vibrant Quake-arena chevron jump pad texture (`ga_jumppad` = warm gold/orange, `ga_jumpsky` = cyan/electric blue)."""
    S = 256
    im = Image.new("RGB", (S, S), (34, 36, 42))
    d = ImageDraw.Draw(im)
    # Brushed steel hazard border
    d.rectangle([6, 6, S - 7, S - 7], outline=(96, 102, 112), width=8)
    acc = (56, 212, 255) if sky_mode else (255, 174, 36)
    glow = (180, 245, 255) if sky_mode else (255, 236, 138)
    dark_in = (18, 38, 54) if sky_mode else (48, 30, 16)
    d.rectangle([22, 22, S - 23, S - 23], fill=dark_in, outline=acc, width=4)
    # Concentric energy ring + 3 bold launch chevrons
    d.ellipse([38, 38, S - 39, S - 39], outline=acc, width=6)
    for cy_off in (168, 122, 76):
        pts = [
            (72, cy_off + 24),
            (128, cy_off - 22),
            (184, cy_off + 24),
            (184, cy_off + 42),
            (128, cy_off - 4),
            (72, cy_off + 42),
        ]
        d.polygon(pts, fill=acc, outline=glow)
    return im


def main():
    os.makedirs(TEX, exist_ok=True)
    os.makedirs(os.path.dirname(WAD), exist_ok=True)

    texs = {
        # 7705 Gallup Dr Hero Exterior & Honest Listing Interior
        "ga_stuc_7705": stucco((226, 220, 212), 7, 101),
        "ga_stuc_crm": stucco((224, 212, 192), 7, 102),
        "ga_stuc_tan": stucco((204, 186, 160), 8, 103),
        "ga_stuc_wht": stucco((238, 238, 236), 6, 104),
        "ga_stuc_sage": stucco((192, 200, 184), 7, 105),
        "ga_stuc_gry": stucco((176, 180, 186), 7, 106),
        "ga_stuc_apt": stucco((216, 198, 156), 7, 107),
        "ga_trim_brn": wood_siding((66, 48, 38), 8, False, 110),
        "ga_siding_wht": wood_siding((236, 238, 240), 10, False, 111),
        "ga_siding_apt": wood_siding((214, 196, 152), 10, False, 112),
        "ga_wood_fnc": wood_siding((112, 92, 74), 10, True, 113),
        "ga_block_tan": slump_block((212, 194, 168), 120),
        "ga_block_wht": slump_block((232, 230, 224), 121),
        "ga_roof_7705": shingles((128, 116, 104), 130),
        "ga_roof_terra": shingles((158, 96, 72), 131),
        "ga_roof_brn": shingles((112, 92, 76), 132),
        "ga_roof_gry": shingles((118, 122, 126), 133),
        "ga_roof_drk": shingles((76, 78, 82), 134),
        "ga_gar_7705": garage_7705(),
        "ga_gar_7701": garage_7701(),
        "ga_arch_7705": arch_window_7705(),
        "ga_door_7705": entry_door_7705(),
        "ga_awning_bw": awning_bw(),
        "ga_win_3p": window_3pane((52, 42, 36), True),
        "ga_win_wht": window_3pane((228, 230, 232), True),
        "ga_curb_7705": curb_7705(),
        "ga_brick_fp": brick_fireplace(),
        "ga_cab_oak": oak_cabinet(),
        "ga_counter": stucco((214, 208, 198), 5, 140),
        "ga_floor_wd": wood_siding((164, 132, 96), 8, False, 141),
        "ga_floor_tl": slump_block((216, 210, 198), 142),
        "ga_wall_int": stucco((234, 230, 222), 4, 143),
        "ga_hvac": hvac_carrier(),
        "ga_pool_wtr": stucco((74, 194, 212), 9, 144),
        "ga_mulch_red": stucco((142, 62, 48), 12, 145),
        "ga_curb_red": stucco((184, 52, 46), 7, 146),
        # Landmarks & Signs
        "ga_photinia": photinia_hedge(),
        "ga_hedge_grn": hedge_green(),
        "ga_cross_sgn": crossway_sign(),
        "ga_base_3200": base_3200(),
        "ga_port_7900": portico_7900(),
        "ga_spd55": speed_55_sign(),
        "ga_alb_logo": albertsons_pediment(),
        "ga_alb_win": albertsons_window(),
        "ga_alb_tile": red_clay_tile(),
        "ga_apt_sign": laurelwood_sign(),
        "ga_sgn_litch": green_street_sign("LITCHFIELD DR"),
        "ga_sgn_presc": green_street_sign("PRESCOTT WAY"),
        "ga_sgn_dem33": green_street_sign("DEMING CT", "<- 3300"),
        "ga_sgn_gal": green_street_sign("GALLUP DR"),
        "ga_sgn_oly": green_street_sign("OLYMPIA DR"),
        # Jump Pads!
        "ga_jumppad": jumppad_tex(False),
        "ga_jumpsky": jumppad_tex(True),
        # Alpha-Masked Foliage & Road Stencils (`{ga_*`)
        "{ga_redleaf": foliage_card([(122, 34, 46), (144, 42, 54), (96, 26, 36)], 201),
        "{ga_jacar": foliage_card([(138, 102, 182), (156, 120, 198), (94, 118, 86)], 202),
        "{ga_blossom": foliage_card([(218, 158, 178), (232, 178, 196), (186, 124, 146)], 203),
        "{ga_olive": foliage_card([(108, 122, 92), (124, 138, 106), (88, 102, 74)], 204),
        "{ga_rd_gal": road_stencil_tex("Gallup Dr", 301),
        "{ga_rd_lit": road_stencil_tex("Litchfield Dr", 302),
        "{ga_rd_dem": road_stencil_tex("Deming Ct", 303),
        "{ga_rd_oly": road_stencil_tex("Olympia Dr", 304),
        "{ga_dbl_yel": double_yellow_tex(),
    }

    wad_imgs = {}
    for name, im in texs.items():
        png_path = os.path.join(TEX, f"{name}.png")
        im.save(png_path)
        qw = max(16, (im.width // 4) // 16 * 16)
        qh = max(16, (im.height // 4) // 16 * 16)
        if name.startswith("{"):
            # Preserve crisp alpha channel for WAD2 index-255 cutout
            rgb = im.convert("RGB").resize((qw, qh), Image.LANCZOS)
            a = im.getchannel("A").resize((qw, qh), Image.NEAREST)
            qim = rgb.convert("RGBA")
            qim.putalpha(a)
        else:
            qim = im.resize((qw, qh), Image.LANCZOS)
        wad_imgs[name] = qim

    write_wad(WAD, wad_imgs)
    print(f"Wrote {len(texs)} PNGs to {TEX} and WAD2 ({len(wad_imgs)} miptex) to {WAD}")


if __name__ == "__main__":
    main()
