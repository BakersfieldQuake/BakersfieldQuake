"""build_spruce_textures.py — Generates all high-resolution textures for the 1:1 Quake replica
of the Spruce St / Westchester neighborhood & Water Tower (Bakersfield, CA 93301).

Writes full-res PNGs (`sp_*.png` and `{sp_*.png`) to `BakersfieldQuake/textures/` and quarter-size
Quake-palette miptex lumps to `source/mm_tools/out/maps/spruce.wad`.
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
WAD = os.path.join(HERE, "out", "maps", "spruce.wad")
rnd = random.Random(933013003)


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
HAND = ["comicbd.ttf", "segoesc.ttf", "arialbd.ttf"]


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


def dim(im, k=0.90):
    if im.mode == "RGBA":
        rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(k)
        rgb.putalpha(im.getchannel("A"))
        return rgb
    return ImageEnhance.Brightness(im.convert("RGB")).enhance(k)


# ============================================================================== 1. ROADS, CURBS, YARDS & GROUNDS
def cracked_asphalt(base=(126, 126, 124), crack_cnt=22, patch_cnt=8, seed=101):
    """Weathered grey Bakersfield residential asphalt with tar-sealed alligator cracks."""
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    for _ in range(140):
        x, y = r.randint(-30, S), r.randint(-30, S)
        rx, ry = r.randint(14, 52), r.randint(14, 52)
        dv = r.randint(-12, 12)
        c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + rx, y + dy + ry], fill=c)
    for _ in range(patch_cnt):
        x, y = r.randint(0, S - 1), r.randint(0, S - 1)
        w, h = r.randint(24, 70), r.randint(18, 54)
        dv = r.randint(-18, -6)
        c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.rectangle([x + dx, y + dy, x + dx + w, y + dy + h], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(1.6))
    d = ImageDraw.Draw(im)
    for _ in range(crack_cnt):
        cx, cy = r.uniform(0, S), r.uniform(0, S)
        ang = r.uniform(0, math.tau)
        pts = [(cx, cy)]
        for _ in range(r.randint(6, 14)):
            ang += r.uniform(-0.65, 0.65)
            step = r.uniform(8, 20)
            cx += math.cos(ang) * step
            cy += math.sin(ang) * step
            pts.append((cx, cy))
        col = (68, 66, 64) if r.random() < 0.65 else (88, 86, 84)
        w = 2 if r.random() < 0.4 else 1
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.line([(px + dx, py + dy) for px, py in pts], fill=col, width=w)
    return dim(add_noise(im, 7, seed + 1), 0.88)


def concrete_walk(base=(194, 190, 180), seed=202):
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    for _ in range(110):
        x, y = r.randint(-20, S), r.randint(-20, S)
        rx, ry = r.randint(12, 42), r.randint(12, 42)
        dv = r.randint(-9, 9)
        c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + rx, y + dy + ry], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(1.4))
    d = ImageDraw.Draw(im)
    for k in (0, 128):
        d.line([(0, k), (S, k)], fill=(150, 146, 138), width=2)
        d.line([(k, 0), (k, S)], fill=(156, 152, 144), width=2)
    return dim(add_noise(im, 5, seed + 1), 0.88)


def lawn_tex(col=(92, 124, 62), dry_mix=0.15, leaves=False, seed=303):
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    for _ in range(260):
        x, y = r.randint(-24, S), r.randint(-24, S)
        rx, ry = r.randint(10, 44), r.randint(10, 44)
        if r.random() < dry_mix:
            c = (r.randint(132, 156), r.randint(124, 142), r.randint(78, 96))
        else:
            dv = r.randint(-16, 16)
            c = (max(0, min(255, col[0] + dv)), max(0, min(255, col[1] + dv)), max(0, min(255, col[2] + dv // 2)))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + rx, y + dy + ry], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(1.6))
    d = ImageDraw.Draw(im)
    # Fine grass blades
    for _ in range(900):
        x, y = r.randint(0, S - 1), r.randint(0, S - 1)
        c = (max(0, col[0] + r.randint(-20, 22)), max(0, col[1] + r.randint(-20, 24)), max(0, col[2] + r.randint(-14, 14)))
        d.line([(x, y), (x + r.randint(-2, 2), y + r.randint(-4, 4))], fill=c, width=1)
    if leaves:
        # Scattered golden-brown autumn leaves (for 3001 Spruce St yard in img_039!)
        for _ in range(650):
            x, y = r.randint(0, S - 1), r.randint(0, S - 1)
            lc = r.choice([(178, 138, 56), (158, 112, 46), (192, 156, 68), (134, 92, 42)])
            for dx in (-S, 0, S):
                for dy in (-S, 0, S):
                    d.ellipse([x + dx, y + dy, x + dx + r.randint(3, 6), y + dy + r.randint(2, 5)], fill=lc)
    return dim(add_noise(im, 6, seed + 5), 0.90)


def gravel_yard(seed=404):
    """Crushed pale grey-tan decomposed granite / gravel for the Water Tower compound."""
    r = random.Random(seed)
    S = 256
    base = (168, 162, 150)
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    for _ in range(220):
        x, y = r.randint(-20, S), r.randint(-20, S)
        rx, ry = r.randint(12, 40), r.randint(12, 40)
        dv = r.randint(-14, 14)
        c = tuple(base[i] + dv for i in range(3))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + rx, y + dy + ry], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(im)
    for _ in range(1400):
        x, y = r.randint(0, S - 1), r.randint(0, S - 1)
        dv = r.randint(-26, 24)
        c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
        d.rectangle([x, y, x + r.randint(1, 3), y + r.randint(1, 3)], fill=c)
    return dim(add_noise(im, 6, seed + 1), 0.87)


def mulch_bed(seed=409):
    r = random.Random(seed)
    S = 128
    base = (98, 78, 60)
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    for _ in range(500):
        x, y = r.randint(0, S - 1), r.randint(0, S - 1)
        dv = r.randint(-22, 22)
        c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
        d.line([(x, y), (x + r.randint(-4, 4), y + r.randint(-3, 3))], fill=c, width=2)
    return dim(add_noise(im, 5, seed + 1), 0.90)


# ============================================================================== 2. STUCCO, BRICK, SIDING & ROOFS
def stucco_tex(col=(224, 218, 200), blotch=9, seed=500):
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    for _ in range(200):
        x, y = r.randint(-24, S), r.randint(-24, S)
        rx, ry = r.randint(12, 44), r.randint(10, 36)
        dv = r.randint(-blotch, blotch)
        c = tuple(max(0, min(255, col[i] + dv)) for i in range(3))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + rx, y + dy + ry], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(1.8))
    return dim(add_noise(im, 5, seed + 1), 0.89)


def lap_siding(col=(156, 160, 150), courses=12, seed=520):
    """Horizontal clapboard/lap siding (3037 Jacaranda sage-grey & Water Tower beige pump shed)."""
    S = 256
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    ch = S / courses
    for k in range(courses):
        y0 = int(round(k * ch))
        y1 = int(round((k + 1) * ch))
        for y in range(y0, y1):
            t = (y - y0) / max(1, y1 - y0)
            dv = int(8 - 16 * t)
            c = tuple(max(0, min(255, col[i] + dv)) for i in range(3))
            d.line([(0, y), (S, y)], fill=c)
        d.line([(0, y1 - 1), (S, y1 - 1)], fill=tuple(max(0, col[i] - 34) for i in range(3)), width=2)
    return dim(add_noise(im, 4, seed), 0.90)


def brick_tex(col=(168, 78, 62), mortar=(204, 198, 186), rows=12, cols=6, seed=540):
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), mortar)
    d = ImageDraw.Draw(im)
    rh = S / rows
    cw = S / cols
    for row in range(rows):
        y0 = int(round(row * rh)) + 2
        y1 = int(round((row + 1) * rh)) - 1
        off = 0.5 * cw if (row % 2) else 0.0
        for col_i in range(-1, cols + 1):
            x0 = int(round(col_i * cw + off)) + 2
            x1 = int(round((col_i + 1) * cw + off)) - 1
            dv = r.randint(-18, 18)
            c = (max(0, min(255, col[0] + dv)), max(0, min(255, col[1] + dv // 2)), max(0, min(255, col[2] + dv // 2)))
            d.rectangle([x0, y0, x1, y1], fill=c)
    return dim(add_noise(im, 5, seed + 1), 0.90)


def stone_veneer(seed=555):
    """Cream/tan/grey flagstone veneer on 3037 Jacaranda Dr porch accent."""
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), (188, 182, 170))
    d = ImageDraw.Draw(im)
    y = 0
    while y < S:
        h = r.randint(22, 38)
        x = 0
        while x < S:
            w = r.randint(32, 68)
            c = r.choice([(212, 202, 184), (196, 178, 152), (174, 168, 158), (222, 214, 198), (184, 164, 138)])
            d.rounded_rectangle([x + 2, y + 2, min(S - 2, x + w - 2), min(S - 2, y + h - 2)], radius=5, fill=c, outline=(146, 140, 130), width=2)
            x += w
        y += h
    return dim(add_noise(im, 6, seed + 1), 0.89)


def shingle_roof(col=(128, 98, 74), seed=600):
    """Architectural asphalt shingle roof."""
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    rows = 16
    rh = S // rows
    for row in range(rows):
        y0 = row * rh
        x = -(row % 3) * 14
        while x < S:
            w = r.randint(24, 38)
            dv = r.randint(-15, 15)
            c = tuple(max(0, min(255, col[i] + dv)) for i in range(3))
            d.rectangle([x, y0, x + w - 1, y0 + rh - 2], fill=c)
            x += w
        d.line([(0, y0 + rh - 1), (S, y0 + rh - 1)], fill=tuple(max(0, col[i] - 28) for i in range(3)), width=2)
    return dim(add_noise(im, 6, seed + 1), 0.90)


def solar_panel():
    """Sleek dark-blue/black residential rooftop PV solar array with silver frame & cell grid."""
    S = 256
    im = Image.new("RGB", (S, S), (28, 34, 46))
    d = ImageDraw.Draw(im)
    # 2x1 module layout inside 256x256
    for px0, px1 in ((4, 124), (132, 252)):
        d.rectangle([px0, 4, px1, S - 4], fill=(24, 30, 44), outline=(168, 174, 182), width=3)
        for gx in range(px0 + 20, px1, 20):
            d.line([(gx, 7), (gx, S - 7)], fill=(46, 56, 76), width=1)
        for gy in range(24, S - 8, 24):
            d.line([(px0 + 3, gy), (px1 - 3, gy)], fill=(46, 56, 76), width=1)
    return add_noise(im, 3, 615)


# ============================================================================== 3. WATER TOWER MATERIALS
def wt_tank_metal():
    """Gleaming silver-white painted steel water tower plate with subtle weld seams & sheen."""
    S = 256
    im = Image.new("RGB", (S, S), (244, 246, 250))
    d = ImageDraw.Draw(im)
    for y in range(S):
        sh = int(5 * math.sin(y / S * math.tau * 2))
        c = (min(255, 243 + sh), min(255, 246 + sh), min(255, 250 + sh))
        d.line([(0, y), (S, y)], fill=c)
    for y in (64, 128, 192):
        d.line([(0, y), (S, y)], fill=(218, 224, 230), width=2)
        d.line([(0, y + 2), (S, y + 2)], fill=(252, 253, 255), width=1)
    for k, x in enumerate((0, 85, 170)):
        y0 = (k % 2) * 64
        d.line([(x, y0), (x, y0 + 128)], fill=(222, 226, 232), width=1)
    return dim(add_noise(im, 2, 701), 0.97)


def wt_top_dome():
    """Water tower crown gleaming silver-white with very light crown weathering."""
    im = wt_tank_metal()
    d = ImageDraw.Draw(im)
    r = random.Random(702)
    for _ in range(28):
        x, y = r.randint(0, 255), r.randint(0, 255)
        rx, ry = r.randint(6, 20), r.randint(6, 20)
        d.ellipse([x, y, x + rx, y + ry], fill=(224, 220, 212))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    return add_noise(im, 2, 703)


def wt_green_steel():
    """Forest-green structural tubular steel for the 8 legs & ring girders (img_169, img_179)."""
    S = 128
    im = Image.new("RGB", (S, S), (58, 98, 66))
    d = ImageDraw.Draw(im)
    for x in range(S):
        sh = int(14 * math.cos((x / S - 0.35) * math.tau))
        c = (max(0, 58 + sh), max(0, 98 + sh), max(0, 66 + sh))
        d.line([(x, 0), (x, S)], fill=c)
    d.line([(0, 64), (S, 64)], fill=(42, 74, 48), width=3)
    return add_noise(im, 4, 705)


def wt_catwalk_rail():
    """{sp_wtrail: Dark green/charcoal steel X-braced catwalk handrail around the tank belly."""
    W, H = 256, 128
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (44, 66, 48, 255)
    # Top rail, mid rail, toe kick
    d.rectangle([0, 4, W, 14], fill=col)
    d.rectangle([0, H // 2 - 3, W, H // 2 + 3], fill=col)
    d.rectangle([0, H - 16, W, H], fill=(52, 78, 56, 255))
    # Posts & X-bracing every 64 px
    for x in range(0, W, 64):
        d.rectangle([x, 4, x + 7, H], fill=col)
        d.line([(x + 3, 12), (x + 61, H - 14)], fill=col, width=4)
        d.line([(x + 61, 12), (x + 3, H - 14)], fill=col, width=4)
    return im


def wt_cross_brace():
    """{sp_wtbrace: Forest-green diagonal tie rods + turnbuckles between water tower legs."""
    W, H = 256, 256
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (52, 92, 60, 255)
    # Horizontal strut at top & bottom + crisp X-rods
    d.rectangle([0, 0, W, 12], fill=col)
    d.rectangle([0, H - 12, W, H], fill=col)
    d.line([(6, 10), (W - 6, H - 10)], fill=col, width=6)
    d.line([(W - 6, 10), (6, H - 10)], fill=col, width=6)
    d.ellipse([W // 2 - 9, H // 2 - 9, W // 2 + 9, H // 2 + 9], fill=(44, 78, 50, 255))
    return im


def shed_south_wall():
    """South wall of the Water Tower pump shed (img_169): beige lap siding + square boarded panel."""
    im = lap_siding((188, 184, 162), courses=14, seed=710)
    d = ImageDraw.Draw(im)
    # Center boarded square hatch seen in img_169
    d.rectangle([88, 76, 168, 172], fill=(176, 172, 150), outline=(136, 132, 114), width=4)
    for y in range(84, 170, 14):
        d.line([(92, y), (164, y)], fill=(148, 144, 126), width=2)
    return im


def shed_gable_vent():
    """Gable louvered vent on the pump shed."""
    W, H = 128, 64
    im = Image.new("RGB", (W, H), (178, 174, 152))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, W - 5, H - 5], outline=(128, 124, 108), width=4)
    for y in range(12, H - 10, 7):
        d.line([(10, y), (W - 10, y)], fill=(86, 84, 74), width=3)
    return dim(add_noise(im, 4, 712), 0.90)


# ============================================================================== 4. DOORS, WINDOWS, SHUTTERS & GARAGES
def panel_door(col=(42, 86, 62), trim=(226, 222, 210), top_panes=0, seed=800):
    W, H = 128, 256
    im = Image.new("RGB", (W, H), trim)
    d = ImageDraw.Draw(im)
    # Outer jamb/trim
    d.rectangle([10, 10, W - 11, H - 1], fill=col, outline=tuple(max(0, col[i] - 22) for i in range(3)), width=3)
    hi = tuple(min(255, col[i] + 18) for i in range(3))
    lo = tuple(max(0, col[i] - 24) for i in range(3))
    if top_panes == 3:
        # 3075 Spruce St door (img_072): 3 small vertical glass lights across upper third + lower panels!
        pw = 20
        for k in range(3):
            x0 = 24 + k * 28
            d.rectangle([x0, 28, x0 + pw, 72], fill=(32, 42, 46), outline=hi, width=2)
        for py0, py1 in ((92, 158), (174, 236)):
            for px0, px1 in ((24, 58), (70, 104)):
                d.rectangle([px0, py0, px1, py1], outline=lo, width=3)
                d.rectangle([px0 + 3, py0 + 3, px1 - 3, py1 - 3], outline=hi, width=2)
    else:
        for py0, py1 in ((28, 86), (104, 168), (184, 238)):
            for px0, px1 in ((24, 58), (70, 104)):
                d.rectangle([px0, py0, px1, py1], outline=lo, width=3)
                d.rectangle([px0 + 3, py0 + 3, px1 - 3, py1 - 3], outline=hi, width=2)
    # Brass doorknob
    d.ellipse([W - 28, 134, W - 18, 144], fill=(204, 176, 98))
    return dim(add_noise(im, 4, seed), 0.92)


def shuttered_window(wall_col=(228, 222, 198), shutter_col=(44, 82, 52), twin=False, seed=820):
    """Multi-pane white-sash window flanked by louvered shutters (green for 3075/3055, dark for 3013/3059)."""
    W, H = (256, 128) if twin else (192, 128)
    im = Image.new("RGB", (W, H), wall_col)
    d = ImageDraw.Draw(im)
    sw = 32
    pad = 8
    # Left & right shutters
    for sx in (pad, W - pad - sw):
        d.rectangle([sx, 8, sx + sw, H - 8], fill=shutter_col, outline=tuple(max(0, shutter_col[i] - 20) for i in range(3)), width=2)
        for ly in range(16, H - 14, 6):
            d.line([(sx + 4, ly), (sx + sw - 4, ly)], fill=tuple(max(0, shutter_col[i] - 18) for i in range(3)), width=2)

    def draw_sash(x0, x1):
        d.rectangle([x0, 8, x1, H - 8], fill=(238, 238, 234), outline=(180, 178, 170), width=2)
        d.rectangle([x0 + 6, 14, x1 - 6, H - 14], fill=(46, 58, 66))
        # Subtle sky reflection in glass
        for y in range(15, H - 14):
            t = (y - 15) / (H - 30)
            gc = (int(62 - 24 * t), int(78 - 30 * t), int(90 - 34 * t))
            d.line([(x0 + 7, y), (x1 - 7, y)], fill=gc)
        # White muntin grid (3x4 panes)
        w_in = x1 - x0 - 12
        for k in (1, 2):
            gx = x0 + 6 + int(round(w_in * k / 3))
            d.line([(gx, 14), (gx, H - 14)], fill=(232, 232, 228), width=2)
        d.rectangle([x0 + 5, H // 2 - 3, x1 - 5, H // 2 + 3], fill=(238, 238, 234))
        for gy in (14 + (H - 28) // 4, 14 + 3 * (H - 28) // 4):
            d.line([(x0 + 6, gy), (x1 - 6, gy)], fill=(232, 232, 228), width=2)

    if twin:
        mid = W // 2
        draw_sash(pad + sw + 4, mid - 3)
        draw_sash(mid + 3, W - pad - sw - 4)
    else:
        draw_sash(pad + sw + 4, W - pad - sw - 4)
    return dim(add_noise(im, 3, seed), 0.91)


def std_window(frame_col=(52, 56, 54), glass_col=(44, 52, 58), wide=False, seed=840):
    """Dark-framed casement or picture window (as on 3003 Spruce St!) or white vinyl slider."""
    W, H = (256, 128) if wide else (128, 128)
    im = Image.new("RGB", (W, H), frame_col)
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, W - 9, H - 9], fill=glass_col)
    for y in range(9, H - 9):
        t = y / H
        c = (int(glass_col[0] + 18 * (1 - t)), int(glass_col[1] + 22 * (1 - t)), int(glass_col[2] + 26 * (1 - t)))
        d.line([(9, y), (W - 10, y)], fill=c)
    if wide:
        for gx in (W // 3, 2 * W // 3):
            d.rectangle([gx - 3, 8, gx + 3, H - 9], fill=frame_col)
    else:
        d.rectangle([8, H // 2 - 3, W - 9, H // 2 + 3], fill=frame_col)
    return add_noise(im, 3, seed)


def garage_door(col=(222, 220, 214), ribbed=False, panels=True, seed=860):
    W, H = 256, 192
    im = Image.new("RGB", (W, H), col)
    d = ImageDraw.Draw(im)
    lo = tuple(max(0, col[i] - 32) for i in range(3))
    hi = tuple(min(255, col[i] + 16) for i in range(3))
    if ribbed:
        # Horizontal corrugated/ribbed steel alley garage door (3035 alley img_113!)
        for y in range(0, H, 10):
            d.rectangle([0, y, W, y + 4], fill=hi)
            d.rectangle([0, y + 5, W, y + 9], fill=lo)
        d.rectangle([0, 0, W - 1, H - 1], outline=(110, 112, 110), width=4)
    else:
        for row in range(4):
            y0, y1 = row * (H // 4), (row + 1) * (H // 4)
            d.line([(0, y1 - 1), (W, y1 - 1)], fill=lo, width=3)
            if panels:
                for k in range(4):
                    x0, x1 = 10 + k * 60, 62 + k * 60
                    d.rectangle([x0, y0 + 8, x1, y1 - 8], outline=lo, width=2)
                    d.rectangle([x0 + 2, y0 + 10, x1 - 2, y1 - 10], outline=hi, width=1)
    return dim(add_noise(im, 4, seed), 0.90)


def commercial_rollup(with_door=False):
    """Black steel roll-up bay door for CITYSERVE (img_145: Bay 1 has inset man-door + blue placard!)."""
    S = 256
    im = Image.new("RGB", (S, S), (42, 44, 48))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 8):
        d.line([(0, y), (S, y)], fill=(56, 58, 64), width=2)
        d.line([(0, y + 4), (S, y + 4)], fill=(28, 30, 34), width=2)
    d.rectangle([0, 0, S - 1, S - 1], outline=(24, 26, 30), width=5)
    if with_door:
        d.rectangle([48, 86, 116, S - 4], fill=(38, 40, 44), outline=(68, 72, 78), width=3)
        d.ellipse([104, 172, 110, 178], fill=(180, 184, 190))
        # Blue placard above/on Bay 1 seen in img_145!
        d.rectangle([96, 98, 136, 120], fill=(42, 76, 152), outline=(220, 226, 236), width=2)
    return add_noise(im, 3, 875)


def brick_steps_white_riser():
    """sp_brkstep_w: Red-brick step tread + crisp white riser face for 3075 Spruce St (img_072)."""
    W, H = 128, 64
    im = Image.new("RGB", (W, H), (232, 230, 224))
    d = ImageDraw.Draw(im)
    # Top 22px terracotta brick bullnose, lower 42px crisp white riser
    d.rectangle([0, 0, W, 22], fill=(172, 82, 64))
    for x in range(0, W, 16):
        d.line([(x, 0), (x, 22)], fill=(208, 198, 186), width=2)
    d.line([(0, 22), (W, 22)], fill=(138, 64, 50), width=2)
    return dim(add_noise(im, 4, 881), 0.91)


# ============================================================================== 5. FENCES, RAILINGS, BINS & PROPS
def wrought_railing(col=(236, 236, 232, 255)):
    """{sp_rail_w / {sp_rail_dk: Sloped/stepped porch wrought-iron railing with vertical balusters."""
    W, H = 192, 128
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Top & bottom angled rails (sloping down left-to-right to match porch steps, or straight)
    # Actually straight rail on a brush or sloped: let's draw crisp vertical balusters + top/bottom rail
    d.rectangle([0, 6, W, 15], fill=col)
    d.rectangle([0, H - 18, W, H - 10], fill=col)
    d.rectangle([0, 4, 9, H], fill=col)
    d.rectangle([W - 9, 4, W, H], fill=col)
    for x in range(18, W - 12, 16):
        d.rectangle([x, 12, x + 5, H - 12], fill=col)
    return im


def chainlink_fence(green_screen=False):
    """{sp_chain / {sp_chain_grn: Galvanized diamond mesh chain-link fence."""
    S = 128
    bg = (68, 88, 72, 232) if green_screen else (0, 0, 0, 0)
    im = Image.new("RGBA", (S, S), bg)
    d = ImageDraw.Draw(im)
    wire = (182, 188, 192, 235) if not green_screen else (164, 172, 168, 255)
    step = 16
    for k in range(-S, S * 2, step):
        d.line([(k, 0), (k + S, S)], fill=wire, width=2)
        d.line([(k + S, 0), (k, S)], fill=wire, width=2)
    # Top rail & post
    d.rectangle([0, 0, S, 6], fill=(192, 198, 202, 255))
    d.rectangle([0, 0, 6, S], fill=(186, 192, 196, 255))
    return im


def white_picket_fence():
    """{sp_picket: White dog-ear wooden fence along 3018/3021 NE arm & alley (img_097)."""
    S = 128
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 26, S, 34], fill=(214, 212, 204, 255))
    d.rectangle([0, S - 28, S, S - 20], fill=(214, 212, 204, 255))
    pw = 16
    for k in range(8):
        x0 = k * pw + 1
        x1 = (k + 1) * pw - 2
        pts = [(x0, 14), (x0 + 4, 6), (x1 - 4, 6), (x1, 14), (x1, S), (x0, S)]
        v = 234 - (k % 3) * 5
        d.polygon(pts, fill=(v, v - 2, v - 6, 255))
    return add_noise(im, 4, 902)


def white_lattice_fence():
    """sp_latfence: White diagonal wood lattice over weathered lower boards in 3035 North Alley (img_113)."""
    S = 256
    im = Image.new("RGB", (S, S), (92, 82, 72))
    d = ImageDraw.Draw(im)
    # Lower 72px weathered peeling white/wood vertical boards
    d.rectangle([0, S - 72, S, S], fill=(216, 210, 198))
    for x in range(0, S, 20):
        d.line([(x, S - 72), (x, S)], fill=(138, 126, 110), width=2)
        if (x // 20) % 2 == 0:
            d.rectangle([x + 3, S - 36, x + 15, S], fill=(166, 152, 132))
    # Upper diagonal white lattice
    lat = (232, 230, 224)
    for k in range(-S, S * 2, 18):
        d.line([(k, 0), (k + S - 72, S - 72)], fill=lat, width=5)
        d.line([(k + S - 72, 0), (k, S - 72)], fill=lat, width=5)
    d.rectangle([0, 0, S, 8], fill=lat)
    d.rectangle([0, S - 76, S, S - 68], fill=lat)
    return dim(add_noise(im, 5, 905), 0.89)


def wood_fence(col=(148, 126, 102), seed=910):
    r = random.Random(seed)
    S = 256
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    bw = 16
    for k in range(S // bw):
        x0 = k * bw
        dv = r.randint(-16, 16)
        c = tuple(max(0, min(255, col[i] + dv)) for i in range(3))
        d.rectangle([x0, 0, x0 + bw - 2, S], fill=c)
        d.line([(x0 + bw - 1, 0), (x0 + bw - 1, S)], fill=tuple(max(0, col[i] - 38) for i in range(3)), width=2)
    return dim(add_noise(im, 6, seed + 1), 0.90)


def bin_3035_lid(col=(72, 114, 188), text="30035"):
    """Spray-painted '3035' / 'CITY OF BAKERSFIELD' trash bin lid/front in North Alley (img_113!)."""
    S = 128
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, S - 7, S - 7], outline=tuple(max(0, col[i] - 24) for i in range(3)), width=4)
    f1 = font(HAND, 30)
    f2 = font(BOLD, 11)
    d.text((16, 28), text, fill=(232, 232, 226), font=f1)
    d.text((18, 76), "CITY OF", fill=(224, 228, 234), font=f2)
    d.text((18, 90), "BAKERSFIELD", fill=(224, 228, 234), font=f2)
    return dim(add_noise(im, 5, 920), 0.90)


def garden_hose_sprite():
    """{sp_hose: Coiled green garden hose mounted on stucco wall of 3075 Spruce St (img_072!)."""
    S = 128
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r, w, c in ((50, 9, (38, 108, 62, 255)), (41, 8, (52, 134, 78, 255)), (32, 8, (34, 96, 56, 255)), (24, 6, (48, 126, 72, 255))):
        d.ellipse([64 - r, 66 - r, 64 + r, 66 + r], outline=c, width=w)
    # Hose hanger bracket at top
    d.rectangle([56, 8, 72, 28], fill=(92, 92, 88, 255))
    return im


def us_flag_sprite():
    """{sp_usflag: Small porch American flag on 3058 Spruce St next door to 3075 (img_078/079)."""
    W, H = 128, 96
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sh = H // 13
    for k in range(13):
        c = (182, 38, 44, 255) if (k % 2 == 0) else (234, 232, 226, 255)
        d.rectangle([0, k * sh, W, (k + 1) * sh], fill=c)
    d.rectangle([0, 0, 54, 7 * sh], fill=(32, 54, 112, 255))
    for sy in range(6, 7 * sh - 4, 10):
        for sx in range(6, 50, 10):
            d.rectangle([sx, sy, sx + 2, sy + 2], fill=(236, 236, 232, 255))
    return im


# ============================================================================== 6. ROAD STENCILS & COMMERCIAL / STREET SIGNS
def road_stencil_tex(label):
    """Weathered painted white asphalt street-name stencil ('Spruce St', 'Hubbard St', 'Jacaranda Dr', 'STOP')."""
    W, H = 256, 96
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(BOLD, 44 if len(label) <= 10 else 36)
    bb = d.textbbox((0, 0), label, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((W - tw) // 2 - bb[0], (H - th) // 2 - bb[1]), label, fill=(224, 222, 214, 225), font=f)
    # Weather/wear speckles so road asphalt peeks through realistically
    r = random.Random(hash(label) & 0xFFFF)
    px = im.load()
    for y in range(H):
        for x in range(W):
            if px[x, y][3] > 0 and r.random() < 0.14:
                px[x, y] = (0, 0, 0, 0)
    return im


def stop_sign_tex():
    S = 128
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(26, 4), (102, 4), (124, 26), (124, 102), (102, 124), (26, 124), (4, 102), (4, 26)]
    d.polygon(pts, fill=(218, 218, 214, 255))
    pts_in = [(29, 9), (99, 9), (119, 29), (119, 99), (99, 119), (29, 119), (9, 99), (9, 29)]
    d.polygon(pts_in, fill=(184, 34, 36, 255))
    f = font(BOLD, 34)
    bb = d.textbbox((0, 0), "STOP", font=f)
    d.text(((S - (bb[2] - bb[0])) // 2 - bb[0], (S - (bb[3] - bb[1])) // 2 - bb[1]), "STOP", fill=(236, 236, 232, 255), font=f)
    return im


def speed25_tex():
    """SPEED LIMIT 25 sign at Spruce St & Beech St (img_035!)."""
    W, H = 96, 128
    im = Image.new("RGB", (W, H), (228, 228, 224))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, W - 5, H - 5], outline=(32, 32, 34), width=3)
    f_sm = font(BOLD, 16)
    f_lg = font(BLACK, 44)
    d.text((18, 12), "SPEED", fill=(28, 28, 30), font=f_sm)
    d.text((23, 30), "LIMIT", fill=(28, 28, 30), font=f_sm)
    d.text((18, 54), "25", fill=(28, 28, 30), font=f_lg)
    return dim(add_noise(im, 3, 940), 0.91)


def yellow_arrow_sign(right=True):
    """Yellow/black directional arrow sign along Pine/30th lane (img_154)."""
    W, H = 128, 64
    im = Image.new("RGB", (W, H), (218, 174, 34))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, W - 4, H - 4], outline=(28, 28, 30), width=3)
    if right:
        d.rectangle([18, 24, 84, 40], fill=(26, 26, 28))
        d.polygon([(78, 10), (112, 32), (78, 54)], fill=(26, 26, 28))
    else:
        d.rectangle([44, 24, 110, 40], fill=(26, 26, 28))
        d.polygon([(50, 10), (16, 32), (50, 54)], fill=(26, 26, 28))
    return dim(add_noise(im, 3, 942), 0.91)


def cityserve_sign():
    """Royal-blue 'CITYSERVE / MAIN HUB' banner above Bays 4-5 on CITYSERVE warehouse (img_145!)."""
    W, H = 256, 96
    im = Image.new("RGB", (W, H), (44, 78, 158))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, W - 4, H - 4], outline=(218, 224, 236), width=2)
    # White city skyline icon on left (matching img_145!)
    for bx, bh in ((22, 18), (32, 30), (42, 42), (54, 26), (64, 16)):
        d.rectangle([bx, 58 - bh, bx + 8, 58], fill=(238, 242, 248))
    d.polygon([(20, 62), (46, 52), (74, 62)], fill=(238, 242, 248))
    f_main = font(BLACK, 26)
    f_sub = font(BOLD, 11)
    d.text((86, 22), "CITYSERVE", fill=(240, 244, 250), font=f_main)
    d.text((126, 62), "M A I N   H U B", fill=(214, 224, 242), font=f_sub)
    return dim(add_noise(im, 3, 950), 0.92)


def smartfinal_sign():
    W, H = 256, 64
    im = Image.new("RGB", (W, H), (192, 36, 38))
    d = ImageDraw.Draw(im)
    f = font(BLACK, 24)
    d.text((12, 16), "Smart & Final extra!", fill=(242, 242, 238), font=f)
    return dim(add_noise(im, 3, 951), 0.90)


def dollartree_sign():
    W, H = 256, 64
    im = Image.new("RGB", (W, H), (36, 134, 62))
    d = ImageDraw.Draw(im)
    f = font(BLACK, 28)
    d.text((22, 14), "DOLLAR TREE", fill=(240, 242, 236), font=f)
    return dim(add_noise(im, 3, 952), 0.90)


def wt_fence_sign():
    """Small blue utility sign on the Water Tower chain-link fence east of gate (img_169)."""
    W, H = 64, 96
    im = Image.new("RGB", (W, H), (34, 98, 196))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, W - 4, H - 4], outline=(232, 236, 242), width=2)
    for y in (16, 28, 44, 56, 68):
        d.rectangle([10, y, W - 10, y + 5], fill=(232, 236, 242))
    return im


# ============================================================================== 7. FOLIAGE & BARK
def bark_tex(eucalyptus=False, seed=960):
    r = random.Random(seed)
    S = 128
    base = (152, 144, 128) if eucalyptus else (96, 82, 68)
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    for _ in range(180):
        x, y = r.randint(0, S - 1), r.randint(0, S - 1)
        h = r.randint(16, 52)
        if eucalyptus:
            c = r.choice([(178, 170, 154), (118, 108, 92), (138, 132, 114), (92, 82, 68)])
            d.ellipse([x - 4, y, x + 5, y + h], fill=c)
        else:
            dv = r.randint(-24, 20)
            c = tuple(max(0, min(255, base[i] + dv)) for i in range(3))
            d.line([(x, y), (x + r.randint(-2, 2), y + h)], fill=c, width=3)
    return dim(add_noise(im, 5, seed + 1), 0.90)


def foliage_block(col=(64, 98, 52), seed=970):
    """Dense opaque/clipped hedge & shrub texture."""
    r = random.Random(seed)
    S = 128
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    for _ in range(420):
        x, y = r.randint(-8, S), r.randint(-8, S)
        rad = r.randint(4, 12)
        dv = r.randint(-22, 24)
        c = (max(0, min(255, col[0] + dv)), max(0, min(255, col[1] + dv)), max(0, min(255, col[2] + dv // 2)))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + rad, y + dy + rad], fill=c)
    return dim(add_noise(im, 6, seed + 1), 0.90)


def canopy_alpha(col=(66, 98, 54), airy=0.30, flowers=None, seed=980):
    """{sp_leaf / {sp_euc / {sp_cedar / {sp_gold / {sp_pinkbush: Alpha-masked organic branch/leaf cluster!"""
    r = random.Random(seed)
    S = 256
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Keep all leaf blobs strictly inside [10..S-11] so GL_REPEAT never wraps border pixels!
    cx, cy = S // 2, S // 2
    max_r = S * 0.35
    n_blobs = 580
    for _ in range(n_blobs):
        ang = r.uniform(0, math.tau)
        dist = (r.random() ** 0.60) * max_r
        bx = cx + math.cos(ang) * dist
        by = cy + math.sin(ang) * dist
        if r.random() < airy * (dist / max_r):
            continue
        rad = r.randint(7, 17)
        dv = r.randint(-22, 26)
        sun_bias = int(16 * (0.5 - by / S))
        c = (
            max(0, min(255, col[0] + dv + sun_bias)),
            max(0, min(255, col[1] + dv + sun_bias)),
            max(0, min(255, col[2] + dv // 2 + sun_bias // 2)),
            255,
        )
        d.ellipse([bx - rad, by - rad, bx + rad, by + rad], fill=c)
        if flowers and r.random() < 0.30:
            fc = (
                max(0, min(255, flowers[0] + r.randint(-16, 16))),
                max(0, min(255, flowers[1] + r.randint(-14, 14))),
                max(0, min(255, flowers[2] + r.randint(-14, 14))),
                255,
            )
            fr = r.randint(4, 9)
            d.ellipse([bx - fr, by - fr, bx + fr, by + fr], fill=fc)
    out = dim(add_noise(im, 5, seed + 1), 0.92)
    # Strictly clear 8px transparent margin on all 4 sides to prevent any texture-wrap edge lines!
    px = out.load()
    pad = 8
    for x in range(S):
        for y in list(range(pad)) + list(range(S - pad, S)):
            px[x, y] = (0, 0, 0, 0)
    for y in range(S):
        for x in list(range(pad)) + list(range(S - pad, S)):
            px[x, y] = (0, 0, 0, 0)
    return out


# ============================================================================== 8. 3003 SPRUCE ST ("DAVID OJEDA" HOUSE) INTERIOR & BACKYARD TEXTURES
def wood_plank_floor(seed=1001):
    """sp_woodflr: Grey-taupe weathered wood-plank laminate floor in 3003 Kitchen & Vestibule (img2_032..036)."""
    r = random.Random(seed)
    S = 256
    base = (158, 146, 134)
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    pw = 32
    for col_i in range(S // pw):
        x0 = col_i * pw
        y_off = (col_i * 73) % S
        for seg in range(-2, 4):
            y0 = y_off + seg * 128 - 128
            y1 = y0 + 128
            yb, yt = max(0, y0), min(S - 1, y1 - 2)
            if yt <= yb:
                continue
            dv = r.randint(-16, 16)
            c = (base[0] + dv, base[1] + dv - 2, base[2] + dv - 4)
            d.rectangle([x0, yb, x0 + pw - 2, yt], fill=c)
            # Subtle wood grain streaks
            for _ in range(14):
                gx = r.randint(x0 + 2, x0 + pw - 4)
                gdv = r.randint(-12, 10)
                gc = (c[0] + gdv, c[1] + gdv, c[2] + gdv)
                d.line([(gx, yb), (gx, yt)], fill=gc, width=1)
            if 0 <= y1 < S:
                d.line([(x0, y1 - 1), (x0 + pw - 1, y1 - 1)], fill=(112, 102, 92), width=1)
        d.line([(x0 + pw - 1, 0), (x0 + pw - 1, S)], fill=(108, 98, 88), width=1)
    return dim(add_noise(im, 4, seed + 1), 0.94)


def plush_carpet(seed=1005):
    """sp_carpet: Warm speckled brown-taupe plush carpet in 3003 Living Room & Bedrooms (img2_037..041)."""
    r = random.Random(seed)
    S = 128
    base = (146, 132, 118)
    im = Image.new("RGB", (S, S), base)
    px = im.load()
    for y in range(S):
        for x in range(S):
            dv = r.randint(-20, 20)
            warm = r.randint(-5, 6)
            px[x, y] = (
                max(0, min(255, base[0] + dv + warm)),
                max(0, min(255, base[1] + dv)),
                max(0, min(255, base[2] + dv - warm // 2)),
            )
    return dim(im, 0.93)


def ceramic_bath_tile(seed=1010):
    """sp_bathtile: Square grey-taupe ceramic floor tile in 3003 Turquoise Bathroom (img2_042)."""
    r = random.Random(seed)
    S = 128
    im = Image.new("RGB", (S, S), (104, 96, 88))
    d = ImageDraw.Draw(im)
    ts = 32
    for ty in range(4):
        for tx in range(4):
            dv = r.randint(-8, 8)
            c = (150 + dv, 140 + dv, 130 + dv)
            d.rectangle([tx * ts + 2, ty * ts + 2, (tx + 1) * ts - 2, (ty + 1) * ts - 2], fill=c)
    return dim(add_noise(im, 5, seed + 1), 0.93)


def cabinet_white_arch():
    """sp_cab_wht: White raised cathedral-arch kitchen cabinet door w/ brushed nickel knob (img2_032..035)."""
    W, H = 128, 192
    im = Image.new("RGB", (W, H), (236, 235, 230))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, W - 4, H - 4], outline=(196, 194, 188), width=3)
    # Recessed arch panel Groove
    d.rectangle([18, 36, W - 19, H - 20], outline=(182, 180, 174), width=3)
    d.arc([18, 16, W - 19, 64], 180, 360, fill=(182, 180, 174), width=3)
    d.line([(21, 38), (21, H - 22)], fill=(248, 248, 244), width=2)
    # Brushed nickel round knob
    d.ellipse([W - 16, H // 2 - 5, W - 6, H // 2 + 5], fill=(154, 156, 160), outline=(96, 98, 102))
    return dim(add_noise(im, 3, 1020), 0.95)


def granite_counter(seed=1025):
    """sp_granite: Speckled grey/white/black salt-and-pepper granite countertop (img2_032..035)."""
    r = random.Random(seed)
    S = 128
    im = Image.new("RGB", (S, S), (186, 188, 186))
    px = im.load()
    palette = [(232, 234, 232), (196, 198, 196), (146, 150, 148), (74, 78, 80), (214, 212, 206)]
    for y in range(S):
        for x in range(S):
            px[x, y] = r.choice(palette)
    return dim(im.filter(ImageFilter.BoxBlur(0.5)), 0.95)


def subway_backsplash(seed=1030):
    """sp_subtile: Glossy warm-grey subway-tile kitchen backsplash w/ white grout (img2_032..035)."""
    r = random.Random(seed)
    S = 128
    im = Image.new("RGB", (S, S), (226, 226, 224))
    d = ImageDraw.Draw(im)
    rh, cw = 16, 42
    for row in range(S // rh):
        y0 = row * rh
        ofs = (row % 2) * (cw // 2)
        for col_i in range(-1, S // cw + 2):
            x0 = col_i * cw + ofs
            dv = r.randint(-7, 7)
            c = (140 + dv, 140 + dv, 136 + dv)
            d.rectangle([x0 + 1, y0 + 1, x0 + cw - 2, y0 + rh - 2], fill=c)
            d.line([(x0 + 2, y0 + 2), (x0 + cw - 3, y0 + 2)], fill=(166, 166, 162), width=1)
    return dim(im, 0.95)


def stove_blue_tile():
    """sp_bluetile: Blue & white decorative tile medallion square behind gas stove (img2_032, 036!)."""
    S = 128
    im = Image.new("RGB", (S, S), (32, 58, 96))
    d = ImageDraw.Draw(im)
    ts = 32
    for ty in range(4):
        for tx in range(4):
            x0, y0 = tx * ts, ty * ts
            d.rectangle([x0, y0, x0 + ts - 1, y0 + ts - 1], outline=(214, 220, 228), width=2)
            cx, cy = x0 + 16, y0 + 16
            d.polygon([(cx, y0 + 4), (x0 + ts - 4, cy), (cx, y0 + ts - 4), (x0 + 4, cy)], fill=(234, 236, 240))
            d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(42, 74, 122))
    return dim(im, 0.94)


def stove_front_tex():
    """sp_stove_fr: Black & stainless gas oven front w/ window & knobs (img2_032, 033, 036)."""
    S = 128
    im = Image.new("RGB", (S, S), (34, 36, 38))
    d = ImageDraw.Draw(im)
    # Top stainless/black control fascia + 5 burner knobs
    d.rectangle([0, 0, S, 24], fill=(54, 56, 60))
    for kx in (14, 38, 64, 90, 114):
        d.ellipse([kx - 5, 7, kx + 5, 17], fill=(22, 22, 24), outline=(148, 152, 156))
    # Stainless oven door trim, handle & dark glass window
    d.rectangle([6, 28, S - 7, S - 18], fill=(164, 168, 172), outline=(42, 44, 46), width=2)
    d.rectangle([14, 33, S - 15, 38], fill=(212, 216, 220))
    d.rectangle([18, 44, S - 19, S - 28], fill=(24, 26, 30), outline=(82, 86, 90), width=2)
    # Bottom storage drawer
    d.rectangle([6, S - 15, S - 7, S - 3], fill=(42, 44, 48))
    return im


def stove_top_tex():
    """sp_stove_tp: 5-burner cast-iron gas stove grates (img2_033!)."""
    S = 128
    im = Image.new("RGB", (S, S), (28, 30, 32))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, S - 5, S - 5], outline=(168, 172, 176), width=3)
    for gx0, gx1 in ((8, 46), (48, 80), (82, 120)):
        d.rectangle([gx0, 10, gx1, S - 11], outline=(68, 70, 74), width=3)
        d.line([(gx0, S // 2), (gx1, S // 2)], fill=(68, 70, 74), width=3)
    for bx, by, br in ((27, 34, 10), (27, 94, 10), (64, 64, 12), (101, 34, 10), (101, 94, 10)):
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=(48, 50, 54), outline=(92, 94, 98), width=2)
    return im


def microwave_tex():
    """sp_micro: Stainless LG over-the-range microwave front (img2_033!)."""
    W, H = 128, 80
    im = Image.new("RGB", (W, H), (182, 186, 190))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, W - 3, H - 3], outline=(96, 100, 104), width=2)
    # Dark microwave window + curved silver handle + black keypad
    d.rectangle([10, 12, 86, H - 13], fill=(32, 36, 40), outline=(64, 68, 72), width=2)
    d.arc([82, 8, 98, H - 9], 270, 90, fill=(224, 228, 232), width=4)
    d.rectangle([100, 12, 120, H - 13], fill=(36, 38, 42))
    for ky in range(20, H - 18, 7):
        for kx in (104, 112):
            d.rectangle([kx, ky, kx + 4, ky + 3], fill=(168, 176, 172))
    return im


def sink_top_tex():
    """sp_sink_top: Brushed stainless double-basin sink inset in granite (img2_032, 034)."""
    S = 128
    im = granite_counter(1027)
    d = ImageDraw.Draw(im)
    d.rectangle([12, 18, S - 13, S - 15], fill=(166, 172, 176), outline=(112, 116, 120), width=3)
    for x0, x1 in ((18, 61), (67, 110)):
        d.rectangle([x0, 26, x1, S - 21], fill=(126, 132, 138), outline=(88, 92, 96), width=2)
        cx, cy = (x0 + x1) // 2, 66
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(58, 60, 64))
    return im


def fluor_light_tex():
    """sp_fluor: Bright white kitchen ceiling fluorescent light fixture (img2_032)."""
    W, H = 64, 128
    im = Image.new("RGB", (W, H), (250, 250, 246))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, W - 3, H - 3], outline=(188, 192, 196), width=3)
    return im


def doormat_tex():
    """sp_doormat: Dark charcoal 'HELLO / GOODBYE' welcome mat inside 3003 front door (img2_037, 038!)."""
    W, H = 128, 80
    im = Image.new("RGB", (W, H), (58, 58, 60))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, W - 5, H - 5], outline=(88, 88, 90), width=2)
    f = font(BOLD, 16)
    d.text((34, 16), "HELLO", fill=(224, 224, 220), font=f)
    d.text((22, 42), "GOODBYE", fill=(214, 214, 210), font=f)
    return add_noise(im, 5, 1045)


def blinds_window_tex(vertical=False, wood=False):
    """sp_vblinds / sp_hblinds / sp_wblinds: Sunlit interior window blinds (img2_034..042)."""
    W, H = (192, 128) if vertical else (128, 128)
    base = (182, 146, 112) if wood else (238, 240, 242)
    im = Image.new("RGB", (W, H), base)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(228, 228, 224), width=6)
    if vertical:
        for x in range(8, W - 8, 9):
            d.line([(x, 8), (x, H - 9)], fill=(198, 202, 206), width=2)
            d.line([(x + 3, 8), (x + 3, H - 9)], fill=(248, 250, 252), width=2)
    else:
        slat_dk = (142, 108, 78) if wood else (204, 208, 212)
        for y in range(8, H - 8, 6):
            d.line([(8, y), (W - 9, y)], fill=slat_dk, width=1)
        d.rectangle([6, H // 2 - 3, W - 7, H // 2 + 2], fill=(224, 224, 220))
    return im


def sheer_curtain_alpha():
    """{sp_sheer: Semi-opaque white geometric sheer curtain on dark grommet rod (img2_034, 037, 040, 041)."""
    W, H = 128, 192
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Curtain rod & grommet rings along top (keep 4px margin on sides)
    d.rectangle([6, 8, W - 7, 13], fill=(68, 64, 60, 255))
    # Drape folds
    for x in range(12, W - 12):
        fold = int(14 * math.sin(x * 0.28))
        c = (232 + fold // 2, 233 + fold // 2, 236 + fold // 2, 255)
        # Dithered sheer weave so sunlit window behind peeks through!
        for y in range(10, H - 6):
            if ((x + y) % 3 != 0) or (y < 22):
                im.putpixel((x, y), c)
    for gx in range(18, W - 16, 18):
        d.ellipse([gx - 4, 5, gx + 4, 15], outline=(58, 54, 50, 255), width=2)
    return im


def shower_curtain_alpha():
    """{sp_shwcurt: Coastal starfish, seashell & coral patterned shower curtain in 3003 Bathroom (img2_042!)."""
    W, H = 128, 192
    im = Image.new("RGBA", (W, H), (238, 240, 236, 255))
    d = ImageDraw.Draw(im)
    r = random.Random(1060)
    # Chrome shower rod at top
    d.rectangle([0, 4, W, 10], fill=(184, 188, 192, 255))
    # Turquoise coral & lime seaweed motifs + brown starfish
    for _ in range(34):
        cx, cy = r.randint(12, W - 12), r.randint(20, H - 14)
        col = r.choice([(58, 158, 168, 255), (168, 198, 92, 255), (128, 182, 184, 255)])
        for a in range(5):
            ang = r.uniform(0, math.tau)
            d.line([(cx, cy), (cx + int(11 * math.cos(ang)), cy + int(14 * math.sin(ang)))], fill=col, width=2)
    for _ in range(14):
        sx, sy = r.randint(16, W - 16), r.randint(24, H - 18)
        for k in range(5):
            ang = k * math.tau / 5.0 - 0.3
            d.line([(sx, sy), (sx + int(9 * math.cos(ang)), sy + int(9 * math.sin(ang)))], fill=(138, 108, 86, 255), width=3)
    # Clear 2px top above rod
    for x in range(W):
        for y in range(4):
            im.putpixel((x, y), (0, 0, 0, 0))
    return im


def vanity_mirror_tex():
    """sp_mirror: Wood-framed bathroom mirror reflecting turquoise wall (img2_042)."""
    W, H = 96, 128
    im = Image.new("RGB", (W, H), (112, 72, 46))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, W - 9, H - 9], fill=(164, 212, 214), outline=(82, 50, 30), width=2)
    d.line([(16, 22), (W - 22, H - 28)], fill=(214, 240, 242), width=4)
    return im


def house_num_3003():
    """sp_num3003: Crisp white '3003' on dark green-brown eave fascia above 3003 front door (img2_043, 044!)."""
    W, H = 128, 48
    im = Image.new("RGB", (W, H), (46, 68, 52))
    d = ImageDraw.Draw(im)
    f = font(BOLD, 30)
    bb = d.textbbox((0, 0), "3003", font=f)
    d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], (H - (bb[3] - bb[1])) // 2 - bb[1]), "3003", fill=(242, 240, 234), font=f)
    return im


def backyard_wood_shed():
    """sp_shed_wd: Rustic weathered brown vertical-board shed w/ double doors & 2 small white windows (img2_045!)."""
    W, H = 256, 128
    im = wood_fence((136, 92, 68), seed=1075).resize((W, H), Image.NEAREST)
    d = ImageDraw.Draw(im)
    # Center double doors
    d.rectangle([96, 22, 160, H - 2], outline=(78, 50, 36), width=3)
    d.line([(128, 22), (128, H - 2)], fill=(68, 42, 30), width=3)
    # Two small white-trimmed windows flanking doors (exact match to img2_045!)
    for wx in (28, 196):
        d.rectangle([wx, 34, wx + 32, 74], fill=(182, 190, 196), outline=(232, 230, 224), width=4)
        d.line([(wx + 16, 34), (wx + 16, 74)], fill=(232, 230, 224), width=2)
    return im


def build():
    return {
        # 1. Roads, Curbs & Grounds
        "sp_asphalt": cracked_asphalt((128, 128, 126), crack_cnt=24, patch_cnt=6, seed=101),
        "sp_alley": cracked_asphalt((138, 136, 130), crack_cnt=30, patch_cnt=10, seed=105),
        "sp_lot": cracked_asphalt((148, 146, 140), crack_cnt=28, patch_cnt=8, seed=109),
        "sp_conc": concrete_walk((196, 192, 182), seed=202),
        "sp_lawn": lawn_tex((88, 120, 58), dry_mix=0.14, seed=303),
        "sp_drylawn": lawn_tex((118, 126, 72), dry_mix=0.52, seed=307),
        "sp_autlawn": lawn_tex((96, 114, 58), dry_mix=0.25, leaves=True, seed=311),
        "sp_gravel": gravel_yard(seed=404),
        "sp_mulch": mulch_bed(seed=409),
        # 2. Walls & Roofs
        "sp_stuc_crm": stucco_tex((226, 220, 204), blotch=8, seed=501),
        "sp_stuc_3075": stucco_tex((228, 222, 196), blotch=7, seed=502),
        "sp_stuc_tan": stucco_tex((206, 188, 158), blotch=9, seed=503),
        "sp_stuc_mint": stucco_tex((198, 216, 198), blotch=7, seed=504),
        "sp_stuc_blu": stucco_tex((152, 166, 178), blotch=8, seed=505),
        "sp_stuc_gry": stucco_tex((186, 188, 186), blotch=8, seed=506),
        "sp_stuc_wht": stucco_tex((236, 234, 228), blotch=6, seed=507),
        "sp_sid_sage": lap_siding((134, 140, 130), courses=12, seed=521),
        "sp_stone": stone_veneer(seed=555),
        "sp_redbrk": brick_tex((168, 78, 62), (206, 198, 186), rows=12, cols=6, seed=540),
        "sp_tanbrk": brick_tex((182, 160, 134), (162, 148, 128), rows=14, cols=6, seed=542),
        "sp_cmu": brick_tex((166, 166, 162), (138, 138, 134), rows=8, cols=4, seed=545),
        "sp_roof_brn": shingle_roof((132, 102, 76), seed=601),
        "sp_roof_grn": shingle_roof((122, 136, 118), seed=602),
        "sp_roof_drk": shingle_roof((76, 78, 82), seed=603),
        "sp_roof_lt": shingle_roof((168, 168, 166), seed=604),
        "sp_roof_tan": shingle_roof((158, 132, 102), seed=605),
        "sp_solar": solar_panel(),
        "sp_trim_grn": stucco_tex((46, 84, 56), blotch=4, seed=610),
        "sp_cooler": lap_siding((164, 158, 146), courses=16, seed=612),
        # 3. Water Tower & Shed
        "sp_wt_tank": wt_tank_metal(),
        "sp_wt_top": wt_top_dome(),
        "sp_wt_green": wt_green_steel(),
        "{sp_wtrail": wt_catwalk_rail(),
        "{sp_wtbrace": wt_cross_brace(),
        "sp_shed_wall": lap_siding((188, 184, 162), courses=14, seed=710),
        "sp_shed_s": shed_south_wall(),
        "sp_shed_vent": shed_gable_vent(),
        "sp_wtsign": wt_fence_sign(),
        # 4. Doors, Windows, Shutters, Garages & Steps
        "sp_door_3003": panel_door((48, 92, 68), (224, 220, 206), top_panes=0, seed=801),
        "sp_door_3075": panel_door((38, 72, 48), (232, 228, 214), top_panes=3, seed=802),
        "sp_door_3013": panel_door((34, 54, 92), (228, 226, 218), top_panes=0, seed=803),
        "sp_door_wht": panel_door((226, 224, 218), (196, 194, 188), top_panes=3, seed=804),
        "sp_win_3075l": shuttered_window((228, 222, 196), (42, 78, 50), twin=True, seed=821),
        "sp_win_grnsh": shuttered_window((226, 222, 198), (42, 78, 50), twin=False, seed=822),
        "sp_win_mint": shuttered_window((198, 216, 198), (46, 92, 68), twin=False, seed=823),
        "sp_win_dksh": shuttered_window((218, 206, 184), (42, 46, 52), twin=False, seed=824),
        "sp_win_whtsh": shuttered_window((206, 188, 158), (228, 226, 220), twin=False, seed=825),
        "sp_win_dark": std_window((48, 52, 50), (38, 46, 50), wide=False, seed=841),
        "sp_win_pic": std_window((46, 72, 54), (42, 48, 50), wide=True, seed=842),
        "sp_win_wht": std_window((232, 232, 228), (48, 58, 66), wide=False, seed=843),
        "sp_win_whtw": std_window((232, 232, 228), (48, 58, 66), wide=True, seed=844),
        "sp_gar_wht": garage_door((226, 224, 218), ribbed=False, panels=True, seed=861),
        "sp_gar_rib": garage_door((168, 168, 164), ribbed=True, panels=False, seed=862),
        "sp_gar_yel": garage_door((196, 196, 94), ribbed=False, panels=True, seed=863),
        "sp_rollup": commercial_rollup(with_door=False),
        "sp_rollup1": commercial_rollup(with_door=True),
        "sp_redstep": stucco_tex((168, 72, 64), blotch=6, seed=880),
        "sp_brkstep_w": brick_steps_white_riser(),
        # 5. Fences, Railings, Bins & Yard Props
        "{sp_rail_w": wrought_railing((238, 238, 234, 255)),
        "{sp_rail_dk": wrought_railing((38, 40, 44, 255)),
        "{sp_chain": chainlink_fence(green_screen=False),
        "{sp_chaingrn": chainlink_fence(green_screen=True),
        "{sp_picket": white_picket_fence(),
        "sp_latfence": white_lattice_fence(),
        "sp_woodfnc": wood_fence((146, 124, 98), seed=910),
        "sp_redfnc": wood_fence((142, 76, 58), seed=912),
        "sp_bin_3035b": bin_3035_lid((68, 108, 184), "30035"),
        "sp_bin_3035g": bin_3035_lid((96, 112, 88), "3035"),
        "sp_bin_blu": stucco_tex((56, 94, 172), blotch=4, seed=921),
        "sp_bin_grn": stucco_tex((68, 98, 66), blotch=4, seed=922),
        "sp_bin_brn": stucco_tex((118, 92, 68), blotch=4, seed=923),
        "{sp_hose": garden_hose_sprite(),
        "{sp_usflag": us_flag_sprite(),
        # 6. Road Stencils & Commercial / Traffic Signs
        "{sp_rd_spruc": road_stencil_tex("Spruce St"),
        "{sp_rd_hubb": road_stencil_tex("Hubbard St"),
        "{sp_rd_jac": road_stencil_tex("Jacaranda Dr"),
        "{sp_rd_stop": road_stencil_tex("STOP"),
        "{sp_stopsign": stop_sign_tex(),
        "sp_spd25": speed25_tex(),
        "sp_arrow_r": yellow_arrow_sign(right=True),
        "sp_arrow_l": yellow_arrow_sign(right=False),
        "sp_cityserve": cityserve_sign(),
        "sp_smartfin": smartfinal_sign(),
        "sp_dollartr": dollartree_sign(),
        # 7. Trees, Bark & Shrubs
        "sp_bark": bark_tex(eucalyptus=False, seed=960),
        "sp_eucbark": bark_tex(eucalyptus=True, seed=962),
        "sp_hedge": foliage_block((64, 98, 50), seed=970),
        "{sp_leaf": canopy_alpha((68, 104, 52), airy=0.28, seed=981),
        "{sp_euc": canopy_alpha((84, 104, 72), airy=0.24, seed=982),
        "{sp_cedar": canopy_alpha((54, 82, 48), airy=0.22, seed=983),
        "{sp_weep": canopy_alpha((102, 134, 62), airy=0.30, seed=984),
        "{sp_gold": canopy_alpha((186, 146, 52), airy=0.28, seed=985),
        "{sp_pinkbush": canopy_alpha((112, 92, 68), airy=0.32, flowers=(196, 84, 92), seed=986),
        "{sp_invis": Image.new("RGBA", (64, 64), (0, 0, 0, 0)),
        # 8. 3003 Spruce St ("David Ojeda" House) Interior & Backyard
        "sp_woodflr": wood_plank_floor(seed=1001),
        "sp_carpet": plush_carpet(seed=1005),
        "sp_bathtile": ceramic_bath_tile(seed=1010),
        "sp_wall_kit": stucco_tex((156, 164, 174), blotch=4, seed=1012),
        "sp_wall_liv": stucco_tex((192, 182, 170), blotch=4, seed=1014),
        "sp_wall_turq": stucco_tex((122, 192, 194), blotch=4, seed=1016),
        "sp_ceil_wht": stucco_tex((238, 238, 234), blotch=3, seed=1018),
        "sp_cab_wht": cabinet_white_arch(),
        "sp_granite": granite_counter(seed=1025),
        "sp_subtile": subway_backsplash(seed=1030),
        "sp_bluetile": stove_blue_tile(),
        "sp_stove_fr": stove_front_tex(),
        "sp_stove_tp": stove_top_tex(),
        "sp_micro": microwave_tex(),
        "sp_sink_top": sink_top_tex(),
        "sp_fluor": fluor_light_tex(),
        "sp_door_tan": panel_door((168, 152, 134), (192, 178, 160), top_panes=0, seed=1040),
        "sp_doormat": doormat_tex(),
        "sp_vblinds": blinds_window_tex(vertical=True, wood=False),
        "sp_hblinds": blinds_window_tex(vertical=False, wood=False),
        "sp_wblinds": blinds_window_tex(vertical=False, wood=True),
        "{sp_sheer": sheer_curtain_alpha(),
        "sp_vanity": wood_fence((118, 76, 48), seed=1052),
        "sp_mirror": vanity_mirror_tex(),
        "{sp_shwcurt": shower_curtain_alpha(),
        "sp_num3003": house_num_3003(),
        "sp_shed_wd": backyard_wood_shed(),
    }


def main():
    os.makedirs(TEX, exist_ok=True)
    os.makedirs(os.path.dirname(WAD), exist_ok=True)
    tex = build()
    small = {}
    for n, im in tex.items():
        assert len(n) <= 15, f"Texture name too long for WAD2: {n} ({len(n)} chars)"
        im.save(os.path.join(TEX, n + ".png"))
        sw = max(16, -(-im.width // 4 // 16) * 16)
        sh = max(16, -(-im.height // 4 // 16) * 16)
        sm = im.resize((sw, sh), Image.LANCZOS)
        if im.mode == "RGBA":
            sm = sm.convert("RGBA")
        small[n] = sm
    write_wad(WAD, small)
    print(f"wrote {WAD}: {len(small)} textures (+ high-res PNGs in {TEX})")


if __name__ == "__main__":
    main()
