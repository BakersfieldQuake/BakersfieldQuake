"""Textures for The Historic Bakersfield Fox Theater (2001 H Street, corner of 20th St & H St):
writes high-res fx_*.png (+ bespoke fx_*_glow.png emissive maps) to BakersfieldQuake/textures/
and quarter-size Quake palette miptex lumps to source/mm_tools/out/maps/fox.wad.

Sources matched:
- Exterior: SoCal Landmarks (John Bare 2022) & bakersfieldlive.com hero photos (Spanish Colonial Revival
  cream stucco, terracotta Churrigueresque reliefs, giant crimson 3D FOX channel letters, navy-blue 4-sided
  clock faces, silver-blue ribbed dome, 1953 wrap-around Fox script marquee with seafoam/coral Art Deco fins
  & 'DANCE NATION / JUNE 10 & 11' readerboard, turquoise bulb soffit, rainbow Skouras terrazzo, Walk of Stars,
  green-striped storefronts, HOPE bronze street clock).
- Interior: 2026 Production Pack PDF + bakersfieldlive.com auditorium/lobby archives (1953 Carl Moeller /
  Charles Skouras gilded Rococo scroll arches over crimson diamond-tufted trellis, champagne-gold & crimson
  proscenium swags, indigo atmospheric starlit sky ceiling, red/gold floral aisle carpet, crimson/blonde-wood
  seats, sloping stenciled lobby raker beams, 1953 concession stand, California tapestry, Green Room guitars).
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402
from fox_neighborhood_textures import build_neighborhood_textures, load_art  # noqa: E402
from padre_hotel_textures import build_padre_textures  # noqa: E402
from fox_extra_textures import build_extra_textures  # noqa: E402

TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
WAD = os.path.join(HERE, "out", "maps", "fox.wad")
rnd = random.Random(19301225)


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
SERIF = ["georgia.ttf", "timesbd.ttf", "pala.ttf", "arialbd.ttf"]
SCRIPT = ["kunstler.ttf", "vladimir.ttf", "brushsci.ttf", "segoesc.ttf", "georgiaz.ttf"]


def add_noise(im, amt=6, seed=None):
    r = random.Random(seed) if seed is not None else rnd
    rgba = im.mode == "RGBA"
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            n = r.randint(-amt, amt)
            p = px[x, y]
            if rgba:
                px[x, y] = (max(0, min(255, p[0] + n)), max(0, min(255, p[1] + n)), max(0, min(255, p[2] + n)), p[3])
            else:
                px[x, y] = (max(0, min(255, p[0] + n)), max(0, min(255, p[1] + n)), max(0, min(255, p[2] + n)))
    return im


def dim(im, k):
    if im.mode == "RGBA":
        rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(k)
        rgb.putalpha(im.getchannel("A"))
        return rgb
    return ImageEnhance.Brightness(im.convert("RGB")).enhance(k)


def wrapped(im, fn):
    w, h = im.size
    d = ImageDraw.Draw(im)
    for dx in (-w, 0, w):
        for dy in (-h, 0, h):
            fn(d, dx, dy)


# ============================================================================== EXTERIOR
def stucco(col=(236, 228, 208), blotch=10):
    S = 256
    im = Image.new("RGB", (S, S), col)
    d = ImageDraw.Draw(im)
    for _ in range(180):
        x, y = rnd.randint(-20, S), rnd.randint(-20, S)
        c = rnd.randint(-blotch, blotch)
        rx, ry = rnd.randint(14, 48), rnd.randint(10, 36)
        fill = tuple(max(0, min(255, col[i] + c)) for i in range(3))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + rx, y + dy + ry], fill=fill)
    im = im.filter(ImageFilter.GaussianBlur(2.2))
    return dim(add_noise(im, 5), 0.90)


def terracotta_trim():
    """Spanish Churrigueresque cast-stone / peach-terracotta molding."""
    S = 256
    im = Image.new("RGB", (S, S), (208, 146, 106))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 64):
        d.rectangle([0, y, S, y + 8], fill=(232, 184, 142))
        d.rectangle([0, y + 52, S, y + 64], fill=(166, 104, 72))
        for x in range(0, S, 32):
            d.ellipse([x + 4, y + 14, x + 28, y + 46], outline=(236, 196, 156), width=3)
            d.ellipse([x + 10, y + 20, x + 22, y + 40], fill=(184, 118, 82))
    return dim(add_noise(im, 6).filter(ImageFilter.GaussianBlur(0.4)), 0.92)


def churrigueresque_crest():
    """Sculpted Spanish Colonial Revival relief cartouche above the marquee & on the 20th St gable."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (228, 218, 196))
    d = ImageDraw.Draw(im)
    # Recessed terracotta shell niche
    d.rounded_rectangle([18, 18, W - 18, H - 18], radius=28, fill=(196, 128, 88), outline=(156, 96, 64), width=5)
    # Radiating scallop ribs
    cx, cy = W // 2, H - 56
    for k in range(-6, 7):
        ang = -math.pi / 2 + k * 0.19
        x2 = cx + math.cos(ang) * 145
        y2 = cy + math.sin(ang) * 145
        d.line([(cx, cy), (x2, y2)], fill=(238, 198, 158), width=6)
        d.line([(cx + 2, cy + 2), (x2 + 2, y2 + 2)], fill=(142, 82, 54), width=2)
    # Central escutcheon shield & scrolls
    d.ellipse([cx - 46, 78, cx + 46, 196], fill=(236, 220, 190), outline=(168, 108, 72), width=5)
    d.ellipse([cx - 30, 96, cx + 30, 178], fill=(208, 140, 96), outline=(244, 232, 206), width=3)
    for sx in (-1, 1):
        d.arc([cx + sx * 56 - 30, 40, cx + sx * 56 + 30, 110], 0, 300, fill=(240, 226, 198), width=7)
        d.arc([cx + sx * 62 - 28, 150, cx + sx * 62 + 28, 224], 40, 340, fill=(240, 226, 198), width=7)
    return dim(add_noise(im, 5), 0.92)


def lancet_window():
    """Tall twin-lancet tower window with dark glass, bronze muntins, and cream center mullion."""
    W, H = 128, 256
    im = Image.new("RGB", (W, H), (34, 38, 46))
    d = ImageDraw.Draw(im)
    # Subtle sky gradient reflection in panes
    for y in range(H):
        t = y / H
        col = (int(44 - 16 * t), int(54 - 20 * t), int(68 - 24 * t))
        d.line([(0, y), (W, y)], fill=col)
    # Outer frame & center vertical mullion
    d.rectangle([0, 0, W - 1, H - 1], outline=(216, 206, 184), width=8)
    d.rectangle([W // 2 - 5, 0, W // 2 + 5, H], fill=(224, 214, 192))
    # Horizontal transoms (upper & lower louver bands as seen in photo)
    for y in (36, 72, 184, 220):
        d.rectangle([6, y - 3, W - 6, y + 3], fill=(168, 152, 124))
    # Louver slats in top & bottom sections
    for y in range(10, 34, 5):
        d.line([(10, y), (W // 2 - 7, y)], fill=(26, 28, 32), width=2)
        d.line([(W // 2 + 7, y), (W - 10, y)], fill=(26, 28, 32), width=2)
    return add_noise(im, 3)


def fox_red_letter():
    """Deep crimson enameled 3D channel letter face with warm neon tube channel."""
    S = 128
    im = Image.new("RGB", (S, S), (186, 28, 30))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, S - 1], outline=(128, 16, 18), width=6)
    d.rectangle([14, 14, S - 15, S - 15], outline=(255, 110, 80), width=5)
    glow = Image.new("RGB", (S, S), (55, 6, 6))
    gd = ImageDraw.Draw(glow)
    gd.rectangle([12, 12, S - 13, S - 13], outline=(220, 52, 30), width=8)
    return add_noise(im, 4), glow.filter(ImageFilter.GaussianBlur(2.0))


def tower_clock():
    """Navy-blue square clock face of the Fox Clock Tower (white Arabic 1-12, minute track, hands, neon rim)."""
    S = 256
    im = Image.new("RGB", (S, S), (226, 214, 190))
    glow = Image.new("RGB", (S, S), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    # Molded frame + navy dial
    d.rectangle([8, 8, S - 9, S - 9], fill=(192, 152, 118), outline=(140, 102, 74), width=4)
    d.rectangle([20, 20, S - 21, S - 21], fill=(24, 46, 86), outline=(238, 236, 228), width=4)
    # Blue neon square tube on rim (seen in clock_tower_header.png!)
    gd.rectangle([22, 22, S - 23, S - 23], outline=(65, 135, 255), width=5)
    cx, cy = S // 2, S // 2
    # Minute ticks
    for m in range(60):
        a = math.radians(m * 6 - 90)
        r0 = 92 if m % 5 == 0 else 96
        r1 = 101
        w = 3 if m % 5 == 0 else 1
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        d.line([p0, p1], fill=(242, 244, 248), width=w)
    # Arabic numerals 1..12
    f = font(BOLD, 24)
    for hr in range(1, 13):
        a = math.radians(hr * 30 - 90)
        tx = cx + math.cos(a) * 74
        ty = cy + math.sin(a) * 74
        d.text((tx, ty), str(hr), font=f, fill=(248, 248, 245), anchor="mm")
        gd.text((tx, ty), str(hr), font=f, fill=(140, 95, 50), anchor="mm")
    # Hands set to ~1:52 (matching user's uploaded photo!)
    for ang_deg, length, wid in ((56, 54, 7), (-48, 80, 5)):
        a = math.radians(ang_deg - 90)
        hx, hy = cx + math.cos(a) * length, cy + math.sin(a) * length
        tx, ty = cx - math.cos(a) * 14, cy - math.sin(a) * 14
        d.line([(tx, ty), (hx, hy)], fill=(248, 248, 244), width=wid)
        gd.line([(tx, ty), (hx, hy)], fill=(120, 110, 90), width=wid)
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(235, 210, 150))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.5))


def dome_metal():
    """Silver-blue ribbed metallic dome surface."""
    S = 256
    im = Image.new("RGB", (S, S), (186, 202, 220))
    d = ImageDraw.Draw(im)
    for y in range(S):
        t = math.sin(y / S * math.pi)
        c = (int(172 + 34 * t), int(190 + 32 * t), int(212 + 28 * t))
        d.line([(0, y), (S, y)], fill=c)
    for x in range(0, S, 32):
        d.line([(x, 0), (x, S)], fill=(142, 158, 178), width=3)
        d.line([(x + 3, 0), (x + 3, S)], fill=(224, 234, 246), width=2)
    return dim(add_noise(im, 4), 0.94)


def spanish_tile():
    """Red-terracotta Mission clay barrel-tile roofing."""
    S = 256
    im = Image.new("RGB", (S, S), (176, 82, 56))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 24):
        for k in range(24):
            s = math.sin(k / 23 * math.pi)
            col = (int(128 + 74 * s), int(54 + 44 * s), int(38 + 30 * s))
            d.line([(x + k, 0), (x + k, S)], fill=col)
    for y in range(0, S, 32):
        d.line([(0, y), (S, y)], fill=(104, 42, 28), width=3)
        d.line([(0, y + 3), (S, y + 3)], fill=(208, 112, 82), width=1)
    return dim(add_noise(im, 6).filter(ImageFilter.GaussianBlur(0.35)), 0.88)


def awning_green():
    """Classic dark seafoam/forest green & cream striped fabric awning (20th St & H St storefronts)."""
    S = 256
    im = Image.new("RGB", (S, S), (42, 102, 78))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):
        d.rectangle([x, 0, x + 19, S], fill=(38, 96, 72))
        d.rectangle([x + 20, 0, x + 29, S], fill=(224, 222, 204))
        d.rectangle([x + 30, 0, x + 31, S], fill=(28, 72, 54))
    return dim(add_noise(im, 5), 0.88)


def hvac_duct():
    """Beige-cream sheet-metal rooftop HVAC duct with standing seams."""
    S = 128
    im = Image.new("RGB", (S, S), (222, 210, 188))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 32):
        d.line([(0, y), (S, y)], fill=(168, 156, 136), width=3)
        d.line([(0, y + 2), (S, y + 2)], fill=(244, 236, 218), width=2)
    return dim(add_noise(im, 4), 0.92)


def wrought_iron():
    """Alpha-cutout ornate Spanish wrought-iron scroll balustrade ({fx_iron)."""
    W, H = 256, 128
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ink = (28, 28, 32, 255)
    hi = (52, 50, 56, 255)
    # Top & bottom rails
    d.rectangle([0, 0, W, 10], fill=hi)
    d.rectangle([0, H - 10, W, H], fill=ink)
    d.rectangle([0, 16, W, 21], fill=ink)
    # Vertical pickets & S-scrolls every 64 px
    for x0 in range(0, W, 64):
        d.rectangle([x0, 0, x0 + 6, H], fill=ink)
        d.rectangle([x0 + 30, 18, x0 + 34, H - 10], fill=ink)
        d.arc([x0 + 8, 24, x0 + 30, 68], 40, 330, fill=ink, width=4)
        d.arc([x0 + 34, 24, x0 + 56, 68], 210, 140, fill=ink, width=4)
        d.arc([x0 + 8, 66, x0 + 30, 112], 30, 320, fill=ink, width=4)
        d.arc([x0 + 34, 66, x0 + 56, 112], 220, 150, fill=ink, width=4)
        d.ellipse([x0 + 25, 60, x0 + 39, 74], outline=hi, width=4)
    return im


def street_clock_dial():
    """Round vintage cream clock face on the bronze 'HOPE' street clock (20th St sidewalk)."""
    S = 256
    im = Image.new("RGB", (S, S), (58, 42, 28))
    glow = Image.new("RGB", (S, S), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.ellipse([10, 10, S - 11, S - 11], fill=(244, 236, 210), outline=(176, 134, 68), width=10)
    gd.ellipse([18, 18, S - 19, S - 19], fill=(120, 105, 72))
    cx, cy = S // 2, S // 2
    romans = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    f = font(SERIF, 20)
    for i, rm in enumerate(romans):
        a = math.radians(i * 30 - 90)
        d.text((cx + math.cos(a) * 82, cy + math.sin(a) * 82), rm, font=f, fill=(32, 26, 20), anchor="mm")
    d.text((cx, cy - 32), "BAKERSFIELD", font=font(SERIF, 13), fill=(60, 44, 28), anchor="mm")
    d.line([(cx, cy), (cx + 42, cy - 28)], fill=(24, 20, 16), width=6)
    d.line([(cx, cy), (cx - 56, cy - 42)], fill=(24, 20, 16), width=4)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(160, 120, 56))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.5))


def hope_pedestal():
    """Bronze & gold-lit 'HOPE' street clock pedestal panel."""
    W, H = 128, 256
    im = Image.new("RGB", (W, H), (64, 44, 30))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([6, 6, W - 7, H - 7], outline=(182, 138, 68), width=5)
    d.rectangle([14, 16, W - 15, 52], fill=(44, 30, 20), outline=(212, 168, 86), width=3)
    d.text((W // 2, 34), "HOPE", font=font(SERIF, 24), fill=(246, 214, 124), anchor="mm")
    gd.text((W // 2, 34), "HOPE", font=font(SERIF, 24), fill=(160, 125, 55), anchor="mm")
    # Warm backlit amber filigree glass panel
    d.rectangle([18, 64, W - 19, H - 24], fill=(232, 178, 88), outline=(182, 138, 68), width=4)
    gd.rectangle([22, 68, W - 23, H - 28], fill=(150, 105, 42))
    for y in range(80, H - 30, 34):
        d.ellipse([30, y, W - 31, y + 28], outline=(72, 48, 28), width=3)
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.5))


# ============================================================================== MARQUEE & VESTIBULE
def marquee_script():
    """Rooftop 'Fox' cursive neon sign over gold-and-olive horizontal ribbed Art Deco backing (gal_020.jpg & gal_023.jpg)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (206, 174, 72))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    # Stepped gold-and-olive horizontal ribs behind 'Fox' matching gal_020.jpg!
    for y in range(0, H, 12):
        d.rectangle([0, y, W, y + 6], fill=(224, 192, 78))
        d.rectangle([0, y + 6, W, y + 11], fill=(92, 118, 62))
    d.rectangle([4, 4, W - 5, H - 5], outline=(188, 52, 48), width=8)
    for y in (20, H - 20):
        d.line([(16, y), (W - 16, y)], fill=(246, 196, 86), width=4)
        gd.line([(16, y), (W - 16, y)], fill=(155, 110, 35), width=5)

    # Custom bold geometric-cursive 'Fox' matching the Bakersfield Fox rooftop sign (crimson channel + cream border)!
    def draw_fox_strokes(drw, col, w):
        drw.line([(72, 62), (176, 48), (242, 54)], fill=col, width=w, joint="curve")
        drw.line([(164, 52), (132, 138), (98, 212), (72, 218)], fill=col, width=w, joint="curve")
        drw.line([(86, 134), (186, 128)], fill=col, width=int(w * 0.85))
        drw.ellipse([198, 96, 308, 206], outline=col, width=w)
        drw.line([(322, 102), (378, 152), (438, 206)], fill=col, width=w, joint="curve")
        drw.line([(444, 96), (376, 154), (314, 208)], fill=col, width=w, joint="curve")

    draw_fox_strokes(d, (64, 34, 32), 48)
    draw_fox_strokes(d, (242, 236, 226), 40)
    draw_fox_strokes(d, (186, 32, 36), 26)
    draw_fox_strokes(d, (255, 138, 128), 6)
    draw_fox_strokes(gd, (235, 45, 50), 20)
    draw_fox_strokes(gd, (255, 145, 135), 7)
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(2.5))


def marquee_reader(lines, w=512, h=192):
    """Backlit white milk-glass changeable-letter marquee board with horizontal tracks & bulb borders."""
    im = Image.new("RGB", (w, h), (238, 240, 236))
    glow = Image.new("RGB", (w, h), (95, 98, 92))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    # Top & bottom coral-green marquee trim with warm chase bulbs
    for y0, y1 in ((0, 22), (h - 22, h)):
        d.rectangle([0, y0, w, y1], fill=(176, 86, 82))
        gd.rectangle([0, y0, w, y1], fill=(20, 10, 10))
        yc = (y0 + y1) // 2
        for x in range(10, w, 18):
            d.ellipse([x - 5, yc - 5, x + 5, yc + 5], fill=(255, 238, 168), outline=(130, 60, 48))
            gd.ellipse([x - 5, yc - 5, x + 5, yc + 5], fill=(220, 185, 85))
    # Horizontal milk-glass letter tracks
    inner_top, inner_bot = 24, h - 24
    nrows = 3
    for r in range(nrows + 1):
        yy = inner_top + int((inner_bot - inner_top) * r / nrows)
        d.line([(0, yy), (w, yy)], fill=(178, 186, 188), width=3)
    # Vertical panel muntins
    for x in range(64, w, 64):
        d.line([(x, inner_top), (x, inner_bot)], fill=(206, 212, 212), width=2)
    # Red-maroon theater letters
    for idx, txt in enumerate(lines):
        if not txt:
            continue
        cy = inner_top + (inner_bot - inner_top) * (idx + 0.5) / len(lines)
        f = font(BLACK, 34 if len(lines) == 2 else 28)
        d.text((w // 2, cy), txt, font=f, fill=(154, 24, 30), anchor="mm")
        gd.text((w // 2, cy), txt, font=f, fill=(25, 5, 5), anchor="mm")
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.2))


def marquee_wing():
    """Seafoam/mint-green corrugated Art Deco marquee upper valence with coral-pink & gold chevron plumes."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (146, 176, 148))
    d = ImageDraw.Draw(im)
    # Horizontal seafoam green corrugated metal bands
    for y in range(0, H, 12):
        d.rectangle([0, y, W, y + 6], fill=(158, 188, 156))
        d.rectangle([0, y + 6, W, y + 11], fill=(116, 146, 118))
    # Top gold/amber trim & bottom coral bead molding
    d.rectangle([0, 0, W, 10], fill=(214, 176, 104))
    d.rectangle([0, H - 12, W, H], fill=(216, 124, 122))
    # Vertical Art Deco coral-pink & gold feathered chevron divider ribs
    for cx in (64, 192):
        d.rectangle([cx - 16, 8, cx + 16, H - 8], fill=(224, 134, 132), outline=(196, 158, 86), width=3)
        for y in range(18, H - 16, 16):
            d.polygon([(cx - 13, y + 10), (cx, y), (cx + 13, y + 10), (cx, y + 5)], fill=(246, 212, 138))
    return dim(add_noise(im, 4), 0.94)


def marquee_soffit():
    """Pale robin's-egg turquoise marquee ceiling soffit studded with warm light bulbs."""
    S = 256
    im = Image.new("RGB", (S, S), (124, 184, 186))
    glow = Image.new("RGB", (S, S), (16, 28, 30))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    for x in range(32, S, 64):
        d.line([(x, 0), (x, S)], fill=(96, 152, 156), width=2)
    for x in range(32, S, 64):
        for y in range(32, S, 64):
            d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(210, 190, 140))
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(255, 246, 205))
            gd.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(210, 190, 130))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.8))


def terrazzo_floor():
    """Polished multi-color Skouras terrazzo ('a rainbow of polished terrazzo' in coral, seafoam, cream & brass)."""
    S = 256
    im = Image.new("RGB", (S, S), (222, 214, 196))
    d = ImageDraw.Draw(im)
    # Geometric Art Deco color fields
    d.polygon([(0, 0), (128, 0), (64, 128), (0, 128)], fill=(208, 134, 118))       # coral rose
    d.polygon([(128, 0), (256, 0), (256, 128), (192, 128)], fill=(138, 178, 164))  # seafoam mint
    d.polygon([(0, 128), (64, 128), (128, 256), (0, 256)], fill=(138, 178, 164))
    d.polygon([(192, 128), (256, 128), (256, 256), (128, 256)], fill=(208, 134, 118))
    d.ellipse([68, 68, 188, 188], fill=(234, 224, 198), outline=(194, 162, 88), width=4)
    d.ellipse([96, 96, 160, 160], fill=(54, 62, 68), outline=(194, 162, 88), width=3)
    # Terrazzo marble aggregate chips
    chips = [(245, 240, 228), (180, 96, 84), (96, 140, 126), (70, 70, 74), (224, 192, 128)]
    for _ in range(900):
        x, y = rnd.randint(0, S - 4), rnd.randint(0, S - 4)
        d.rectangle([x, y, x + rnd.randint(2, 4), y + rnd.randint(2, 4)], fill=rnd.choice(chips))
    # Brass divider strips
    for p0, p1 in [((128, 0), (64, 128)), ((64, 128), (128, 256)), ((128, 0), (192, 128)), ((192, 128), (128, 256)),
                   ((0, 128), (68, 128)), ((188, 128), (256, 128))]:
        d.line([p0, p1], fill=(198, 166, 92), width=3)
    return dim(add_noise(im, 3), 0.92)


def walk_of_stars(label="BUCK OWENS"):
    """Bakersfield Fox Walk of Stars sidewalk plaque (coral terrazzo star with brass rim & star emblem)."""
    S = 256
    im = Image.new("RGB", (S, S), (72, 72, 76))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, S - 7, S - 7], fill=(58, 58, 62), outline=(196, 162, 88), width=5)
    cx, cy = S // 2, S // 2 + 4
    pts = []
    for k in range(10):
        a = math.radians(k * 36 - 90)
        r = 98 if k % 2 == 0 else 42
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    d.polygon(pts, fill=(208, 112, 98), outline=(218, 184, 102), width=4)
    d.text((cx, cy - 8), label, font=font(BOLD, 16), fill=(246, 222, 146), anchor="mm")
    d.text((cx, cy + 16), "FOX THEATER", font=font(BOLD, 12), fill=(240, 212, 134), anchor="mm")
    return dim(add_noise(im, 5), 0.94)


def poster_case(title1, title2, accent):
    """Ornate dark-bronze theater poster display case."""
    W, H = 192, 256
    im = Image.new("RGB", (W, H), (54, 34, 26))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([6, 6, W - 7, H - 7], fill=(82, 48, 34), outline=(188, 148, 78), width=5)
    d.rectangle([18, 18, W - 19, 44], fill=(140, 28, 32), outline=(212, 174, 96), width=2)
    d.text((W // 2, 31), "NOW AT THE FOX", font=font(BOLD, 15), fill=(250, 232, 172), anchor="mm")
    # Illuminated poster interior
    d.rectangle([20, 50, W - 21, H - 22], fill=accent, outline=(212, 174, 96), width=3)
    gd.rectangle([22, 52, W - 23, H - 24], fill=tuple(c // 3 for c in accent))
    d.ellipse([38, 72, W - 39, 176], fill=(244, 218, 152), outline=(186, 48, 42), width=4)
    d.text((W // 2, 114), title1, font=font(BLACK, 20), fill=(36, 24, 28), anchor="mm")
    d.text((W // 2, 140), title2, font=font(BOLD, 15), fill=(156, 30, 34), anchor="mm")
    d.text((W // 2, 206), "BAKERSFIELD LIVE", font=font(BOLD, 14), fill=(248, 238, 212), anchor="mm")
    return add_noise(im, 4), glow.filter(ImageFilter.GaussianBlur(1.5))


def boxoffice_win():
    """Island Ticket Booth etched glass window with brass speaking grille."""
    W, H = 128, 192
    im = Image.new("RGB", (W, H), (224, 214, 192))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, W - 9, H - 9], fill=(42, 58, 68), outline=(196, 158, 84), width=6)
    # Warm interior glow visible inside booth
    d.rectangle([16, 16, W - 17, H - 17], fill=(92, 76, 58))
    d.text((W // 2, 42), "TICKETS", font=font(BOLD, 20), fill=(246, 216, 136), anchor="mm")
    d.ellipse([W // 2 - 22, 74, W // 2 + 22, 118], fill=(198, 162, 86), outline=(120, 92, 42), width=3)
    for y in range(84, 112, 6):
        d.line([(W // 2 - 14, y), (W // 2 + 14, y)], fill=(54, 40, 22), width=2)
    d.rounded_rectangle([W // 2 - 26, 142, W // 2 + 26, 172], radius=8, fill=(32, 26, 22), outline=(198, 162, 86), width=3)
    return add_noise(im, 4)


def entry_door():
    """Aluminum-and-glass theater entrance door with push bar & transom."""
    W, H = 128, 256
    im = Image.new("RGB", (W, H), (220, 222, 220))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, W - 5, 54], fill=(46, 62, 72), outline=(186, 190, 192), width=5)
    d.rectangle([4, 62, W - 5, H - 5], outline=(186, 190, 192), width=6)
    d.rectangle([14, 72, W - 15, H - 42], fill=(42, 56, 66))
    d.line([(22, 160), (100, 82)], fill=(96, 118, 132), width=4)
    # Brass push bar & kickplate
    d.rectangle([10, 146, W - 11, 156], fill=(208, 174, 98))
    d.rectangle([10, H - 38, W - 11, H - 10], fill=(194, 160, 86))
    return add_noise(im, 3)


def shop_window():
    """H Street boutique storefront display window."""
    W, H = 256, 192
    im = Image.new("RGB", (W, H), (48, 44, 42))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(76, 62, 50), width=8)
    d.rectangle([W // 2 - 4, 0, W // 2 + 4, H], fill=(76, 62, 50))
    for x0 in (12, W // 2 + 8):
        d.rectangle([x0, 12, x0 + W // 2 - 20, H - 12], fill=(56, 68, 76))
        d.rectangle([x0 + 18, 56, x0 + 88, H - 18], fill=(128, 98, 76))
        d.line([(x0 + 12, H - 24), (x0 + 92, 34)], fill=(112, 134, 148), width=4)
    return add_noise(im, 4)


def evas_sign():
    """EVA'S East Lobby Lounge sign (from bakersfieldlive.com/rental-information)."""
    W, H = 256, 96
    im = Image.new("RGB", (W, H), (44, 24, 28))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([4, 4, W - 5, H - 5], outline=(214, 174, 96), width=5)
    d.text((W // 2, 38), "EVA'S", font=font(SERIF, 42), fill=(255, 214, 132), anchor="mm")
    d.text((W // 2, 74), "EAST LOBBY LOUNGE & STAGE", font=font(BOLD, 14), fill=(228, 164, 142), anchor="mm")
    gd.text((W // 2, 38), "EVA'S", font=font(SERIF, 42), fill=(195, 140, 65), anchor="mm")
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.6))


# ============================================================================== LOBBY & CONCESSIONS
def skouras_carpet():
    """Lush Skouras floral/acanthus theater carpet (cream, crimson-red, olive-green & gold, matched to site_img_35.png)."""
    S = 256
    im = Image.new("RGB", (S, S), (178, 38, 34))

    def motif(d, dx, dy):
        for cx, cy in ((64, 64), (192, 192), (192, 64), (64, 192)):
            x, y = cx + dx, cy + dy
            # Olive-sage acanthus leaves
            for k in range(6):
                a = k * math.pi / 3 + 0.3
                lx, ly = x + math.cos(a) * 34, y + math.sin(a) * 34
                d.ellipse([lx - 18, ly - 12, lx + 18, ly + 12], fill=(96, 128, 78))
            # Oversized cream & gold Skouras blossom
            for k in range(8):
                a = k * math.pi / 4
                px, py = x + math.cos(a) * 22, y + math.sin(a) * 22
                d.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(238, 224, 184))
            d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(212, 92, 48), outline=(246, 232, 194), width=3)

    wrapped(im, motif)
    return dim(add_noise(im, 6).filter(ImageFilter.GaussianBlur(0.5)), 0.90)


def lobby_plaster():
    """Warm antique parchment/gold Venetian plaster of the Spanish-Deco lobby."""
    return stucco((226, 206, 172), blotch=14)


def raker_stencil():
    """Stenciled geometric Spanish-Deco concrete balcony-support raker beam (site_img_02 & site_img_13)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (176, 152, 118))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=(122, 96, 68))
    d.rectangle([0, H - 14, W, H], fill=(122, 96, 68))
    for x in range(0, W, 64):
        pts = [(x + 32, 20), (x + 56, 64), (x + 32, 108), (x + 8, 64)]
        d.polygon(pts, fill=(144, 72, 54), outline=(228, 204, 158), width=3)
        d.ellipse([x + 22, 54, x + 42, 74], fill=(224, 194, 132))
    return dim(add_noise(im, 5), 0.92)


def california_tapestry():
    """1930 California Mission & Golden Poppies woven tapestry in the West Lobby alcove (gal_117 / site_img_13)."""
    return load_art("fox_california_tapestry.jpg", (512, 384), sat=1.05, contrast=1.05, bright=0.88)


def concession_front():
    """1953 Skouras streamlined glass & chrome candy/popcorn concession counter."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (168, 42, 44))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    # Brushed stainless/chrome bands
    for y in (0, 18, H - 16):
        d.rectangle([0, y, W, y + 10], fill=(214, 218, 224))
    # Illuminated glass candy display case
    d.rectangle([20, 32, W - 21, H - 22], fill=(248, 232, 186), outline=(204, 208, 214), width=4)
    gd.rectangle([24, 36, W - 25, H - 26], fill=(140, 120, 75))
    d.line([(22, 68), (W - 23, 68)], fill=(190, 194, 200), width=3)
    cols = [(210, 52, 52), (236, 178, 44), (62, 132, 196), (148, 86, 52), (224, 96, 142)]
    for row_y in (44, 78):
        for i, x in enumerate(range(32, W - 36, 28)):
            d.rectangle([x, row_y, x + 20, row_y + 18], fill=cols[i % len(cols)], outline=(255, 255, 255))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.2))


def concession_menu():
    """1950s Skouras neon backbar sign: FOX REFRESHMENTS."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (42, 24, 34))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([6, 6, W - 7, H - 7], outline=(124, 214, 204), width=4)
    gd.rectangle([6, 6, W - 7, H - 7], outline=(55, 145, 135), width=4)
    d.text((W // 2, 36), "FOX REFRESHMENTS", font=font(BOLD, 21), fill=(255, 132, 148), anchor="mm")
    gd.text((W // 2, 36), "FOX REFRESHMENTS", font=font(BOLD, 21), fill=(205, 65, 85), anchor="mm")
    d.text((W // 2, 72), "HOT BUTTERED POPCORN", font=font(BOLD, 15), fill=(252, 228, 144), anchor="mm")
    d.text((W // 2, 98), "CANDY  •  FOUNTAIN DRINKS", font=font(BOLD, 14), fill=(176, 236, 228), anchor="mm")
    gd.text((W // 2, 72), "HOT BUTTERED POPCORN", font=font(BOLD, 15), fill=(140, 115, 55), anchor="mm")
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.5))


# ============================================================================== AUDITORIUM & STAGE
def atmospheric_sky_ceiling():
    """Indigo-violet atmospheric night-sky ceiling with twinkling stars (site_img_35.png & Wikipedia)."""
    S = 512
    im = Image.new("RGB", (S, S), (58, 62, 138))
    glow = Image.new("RGB", (S, S), (18, 20, 58))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    for _ in range(120):
        x, y = rnd.randint(-40, S), rnd.randint(-40, S)
        r = rnd.randint(30, 80)
        c = rnd.randint(-10, 14)
        col = (58 + c, 62 + c, min(200, 138 + c * 2))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + r, y + dy + r], fill=col)
    im = im.filter(ImageFilter.GaussianBlur(8.0))
    d = ImageDraw.Draw(im)
    # Twinkling stars across the indigo sky!
    for _ in range(220):
        sx, sy = rnd.randint(4, S - 5), rnd.randint(4, S - 5)
        big = rnd.random() < 0.14
        if big:
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 250, 224))
            gd.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 244, 196))
            gd.line([(sx - 6, sy), (sx + 6, sy)], fill=(180, 195, 255), width=1)
            gd.line([(sx, sy - 6), (sx, sy + 6)], fill=(180, 195, 255), width=1)
        else:
            d.rectangle([sx, sy, sx + 1, sy + 1], fill=(228, 234, 255))
            gd.rectangle([sx - 1, sy - 1, sx + 1, sy + 1], fill=(165, 180, 240))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(0.8))


def skouras_wall_mural():
    """1953 Carl Moeller / Charles Skouras side wall: crimson diamond-tufted trellis with rosettes & gold Rococo scrolls!"""
    S = 512
    im = Image.new("RGB", (S, S), (132, 28, 30))
    d = ImageDraw.Draw(im)
    # Crimson diamond-tufted lattice with cream/gold buttons (exact match to site_img_35.png!)
    step = 48
    for k in range(-S, S * 2, step):
        d.line([(k, 0), (k + S, S)], fill=(78, 14, 16), width=5)
        d.line([(k + 2, 0), (k + S + 2, S)], fill=(214, 178, 128), width=2)
        d.line([(k, S), (k + S, 0)], fill=(78, 14, 16), width=5)
        d.line([(k + 2, S), (k + S + 2, 0)], fill=(214, 178, 128), width=2)
    for y in range(0, S + step, step // 2):
        off = 0 if (y // (step // 2)) % 2 == 0 else step // 2
        for x in range(off, S + step, step):
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(242, 224, 184), outline=(156, 118, 62), width=2)
    # Sweeping gilded Skouras Rococo scroll arch framing the trellis!
    for w, col in ((46, (108, 72, 24)), (36, (188, 142, 54)), (20, (242, 206, 108)), (8, (255, 236, 168))):
        d.arc([-80, 24, S + 80, S * 2], 195, 345, fill=col, width=w)
        d.arc([24, 140, 236, 360], 20, 310, fill=col, width=max(4, w * 2 // 3))
        d.arc([S - 236, 140, S - 24, 360], 230, 160, fill=col, width=max(4, w * 2 // 3))
    return dim(add_noise(im, 4), 0.94)


def gold_leaf():
    """Burnished 24k gold-leaf sculptural ornament (proscenium sunburst crest & Skouras scroll ribs)."""
    S = 256
    im = Image.new("RGB", (S, S), (198, 154, 62))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):
        for k in range(32):
            s = math.sin(k / 31 * math.pi)
            col = (int(138 + 108 * s), int(98 + 104 * s), int(34 + 78 * s))
            d.line([(x + k, 0), (x + k, S)], fill=col)
    return dim(add_noise(im, 5), 0.95)


def drape(base_rgb, fold_px=24):
    """Pleated theatrical velvet/satin stage & wall curtain."""
    S = 256
    im = Image.new("RGB", (S, S), base_rgb)
    d = ImageDraw.Draw(im)
    for x in range(S):
        s = 0.62 + 0.38 * math.sin(2 * math.pi * x / fold_px)
        col = tuple(max(0, min(255, int(c * s))) for c in base_rgb)
        d.line([(x, 0), (x, S)], fill=col)
    return add_noise(im, 4)


def seat_row_backs():
    """Crimson-red upholstered theater seats with curved blonde-wood top rail & dividers (site_img_35.png)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (36, 22, 22))
    d = ImageDraw.Draw(im)
    n_seats = 4
    sw = W // n_seats
    for i in range(n_seats):
        x0, x1 = i * sw, (i + 1) * sw
        # Blonde wood outer standard / armrest cap
        d.rectangle([x0, 28, x0 + 5, H], fill=(214, 166, 92))
        d.rectangle([x1 - 5, 28, x1, H], fill=(186, 138, 70))
        # Curved crimson seat back
        d.rounded_rectangle([x0 + 4, 6, x1 - 4, H - 4], radius=14, fill=(176, 36, 38), outline=(222, 176, 98), width=3)
        d.rounded_rectangle([x0 + 10, 16, x1 - 10, H - 14], radius=8, fill=(194, 46, 48))
    return dim(add_noise(im, 4), 0.94)


def seat_standard():
    """Blonde-wood & gilded cast-iron aisle seat standard."""
    W, H = 128, 128
    im = Image.new("RGB", (W, H), (192, 144, 78))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 6, W - 9, 24], fill=(228, 184, 108), outline=(132, 92, 42), width=2)
    d.rectangle([16, 28, W - 17, H - 8], fill=(154, 42, 40), outline=(218, 176, 98), width=4)
    for y in range(42, H - 18, 18):
        d.line([(26, y), (W - 27, y)], fill=(218, 176, 98), width=3)
    return dim(add_noise(im, 4), 0.92)


def balcony_fascia():
    """Ivory-cream Art Moderne balcony fascia with recessed Leko spotlight port (site_img_25.png)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (234, 226, 208))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([0, 0, W, 14], fill=(212, 178, 114))
    d.rectangle([0, H - 16, W, H], fill=(204, 194, 174))
    d.line([(0, 26), (W, 26)], fill=(212, 202, 182), width=3)
    d.line([(0, H - 26), (W, H - 26)], fill=(212, 202, 182), width=3)
    for cx in (64, 192):
        d.ellipse([cx - 22, 38, cx + 22, 86], fill=(38, 36, 40), outline=(176, 158, 124), width=4)
        d.ellipse([cx - 9, 52, cx + 9, 72], fill=(246, 232, 192))
        gd.ellipse([cx - 8, 53, cx + 8, 71], fill=(160, 145, 105))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.2))


def stage_floor():
    """Dark oiled theatrical hardwood stage boards."""
    S = 256
    im = Image.new("RGB", (S, S), (58, 42, 32))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 16):
        c = rnd.randint(-7, 7)
        d.rectangle([0, y, S, y + 14], fill=(58 + c, 42 + c, 32 + c))
        d.line([(0, y + 15), (S, y + 15)], fill=(34, 24, 18), width=2)
    return add_noise(im, 4)


def silver_screen():
    """21' x 46' perforated cinema screen with warm vintage 'THE HISTORIC BAKERSFIELD FOX' projection."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (218, 220, 226))
    glow = Image.new("RGB", (W, H), (75, 78, 86))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    # Vignette + classic Fox Deco sunbeams
    cx, cy = W // 2, H - 24
    for k in range(-7, 8):
        a = -math.pi / 2 + k * 0.18
        pts = [(cx, cy), (cx + math.cos(a - 0.05) * 420, cy + math.sin(a - 0.05) * 420),
               (cx + math.cos(a + 0.05) * 420, cy + math.sin(a + 0.05) * 420)]
        d.polygon(pts, fill=(236, 230, 208))
    d.rectangle([12, 12, W - 13, H - 13], outline=(156, 134, 88), width=5)
    d.text((W // 2, 74), "THE HISTORIC", font=font(SERIF, 24), fill=(72, 58, 44), anchor="mm")
    d.text((W // 2, 122), "BAKERSFIELD FOX", font=font(SERIF, 42), fill=(138, 34, 36), anchor="mm")
    d.text((W // 2, 168), "CHRISTMAS DAY 1930  •  2001 H STREET", font=font(BOLD, 16), fill=(72, 58, 44), anchor="mm")
    gd.rectangle([16, 16, W - 17, H - 17], fill=(95, 92, 82))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.5))


def exit_sign():
    """Glowing red theatrical EXIT sign."""
    W, H = 128, 64
    im = Image.new("RGB", (W, H), (218, 214, 204))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([8, 8, W - 9, H - 9], fill=(184, 24, 26), outline=(140, 136, 128), width=3)
    d.text((W // 2, H // 2), "EXIT", font=font(BOLD, 32), fill=(255, 244, 236), anchor="mm")
    gd.rectangle([10, 10, W - 11, H - 11], fill=(175, 22, 22))
    gd.text((W // 2, H // 2), "EXIT", font=font(BOLD, 32), fill=(255, 220, 200), anchor="mm")
    return im, glow.filter(ImageFilter.GaussianBlur(1.0))


def foh_console():
    """Midas M32 & Avolites Sapphire Touch FOH mixing desk (Production Pack Pages 13 & 16)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (34, 36, 42))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    # Dual glowing touchscreens
    for x0, col in ((22, (48, 148, 214)), (142, (214, 96, 56))):
        d.rectangle([x0, 14, x0 + 92, 56], fill=col, outline=(88, 92, 100), width=3)
        gd.rectangle([x0 + 2, 16, x0 + 90, 54], fill=tuple(c * 2 // 3 for c in col))
    # Motorized faders & LED scribble strips
    for x in range(18, W - 18, 12):
        d.line([(x, 70), (x, 114)], fill=(18, 18, 22), width=3)
        fy = 78 + (x * 7) % 26
        d.rectangle([x - 3, fy, x + 3, fy + 8], fill=(214, 218, 224))
        led = (64, 224, 112) if x % 24 else (244, 188, 56)
        d.rectangle([x - 4, 62, x + 4, 66], fill=led)
        gd.rectangle([x - 4, 62, x + 4, 66], fill=led)
    return add_noise(im, 2), glow.filter(ImageFilter.GaussianBlur(1.0))


def greenroom_wall():
    """Forest-green Stage Left Green Room wall with hanging guitars & concert frames (Production Pack Page 11)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (36, 78, 56))
    d = ImageDraw.Draw(im)
    # Framed concert posters
    for fx, fy, col in ((22, 134, (214, 188, 132)), (98, 142, (184, 72, 62)), (178, 134, (86, 138, 186))):
        d.rectangle([fx, fy, fx + 54, fy + 74], fill=col, outline=(42, 30, 22), width=5)
        d.rectangle([fx + 8, fy + 10, fx + 46, fy + 52], fill=(38, 34, 38))
    # Hanging acoustic & electric guitars near top (exact match to Page 11 photo!)
    for gx, body_col in ((52, (198, 126, 54)), (132, (214, 52, 46)), (208, (232, 188, 116))):
        d.rectangle([gx - 3, 22, gx + 3, 74], fill=(92, 58, 34))
        d.ellipse([gx - 16, 66, gx + 16, 98], fill=body_col, outline=(48, 30, 18), width=2)
        d.ellipse([gx - 20, 86, gx + 20, 122], fill=body_col, outline=(48, 30, 18), width=2)
        d.ellipse([gx - 6, 84, gx + 6, 96], fill=(32, 22, 16))
    return dim(add_noise(im, 5), 0.92)


def vanity_mirror():
    """Upstairs Dressing Room mirror with warm vertical tube sconces (Production Pack Page 10)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (146, 68, 58))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([12, 12, W - 13, H - 13], fill=(96, 108, 118), outline=(198, 158, 84), width=4)
    d.line([(36, H - 20), (116, 20)], fill=(142, 158, 170), width=6)
    for sx in (28, 128, 228):
        d.rectangle([sx - 4, 20, sx + 4, H - 20], fill=(255, 240, 196), outline=(198, 158, 84), width=1)
        gd.rectangle([sx - 5, 20, sx + 5, H - 20], fill=(225, 190, 120))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.5))


def rollup_door():
    """8' x 13'6" grey steel Stage Alley loading roll-up door (Production Pack Page 4)."""
    S = 128
    im = Image.new("RGB", (S, S), (168, 174, 180))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 8):
        d.line([(0, y), (S, y)], fill=(128, 134, 140), width=2)
        d.line([(0, y + 2), (S, y + 2)], fill=(198, 204, 210), width=1)
    return dim(add_noise(im, 4), 0.90)


def stage_truss():
    """Alpha-cutout 40' aluminum box lighting truss ({fx_truss)."""
    W, H = 256, 64
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    al = (192, 198, 206, 255)
    sh = (132, 138, 146, 255)
    d.rectangle([0, 0, W, 8], fill=al)
    d.rectangle([0, H - 8, W, H], fill=sh)
    for x in range(0, W, 64):
        d.rectangle([x, 0, x + 6, H], fill=al)
        d.line([(x + 3, 6), (x + 35, H - 6)], fill=sh, width=5)
        d.line([(x + 35, H - 6), (x + 64, 6)], fill=al, width=5)
    return im


def build():
    foxred, foxred_g = fox_red_letter()
    clk, clk_g = tower_clock()
    stclk, stclk_g = street_clock_dial()
    hope, hope_g = hope_pedestal()
    mqs, mqs_g = marquee_script()
    mqf, mqf_g = marquee_reader(["DANCE NATION", "JUNE 10 & 11"])
    mqsd, mqsd_g = marquee_reader(["THE HISTORIC", "BAKERSFIELD FOX", "EST. DEC 25 1930"])
    mqsof, mqsof_g = marquee_soffit()
    p1, p1_g = poster_case("JUST IMAGINE", "CHRISTMAS 1930", (42, 68, 118))
    p2, p2_g = poster_case("CULTS &", "CLASSICS", (118, 38, 48))
    p3, p3_g = poster_case("DANCE", "NATION", (44, 96, 84))
    eva, eva_g = evas_sign()
    conc, conc_g = concession_front()
    cmenu, cmenu_g = concession_menu()
    skyc, skyc_g = atmospheric_sky_ceiling()
    bfasc, bfasc_g = balcony_fascia()
    scr, scr_g = silver_screen()
    ex, ex_g = exit_sign()
    foh, foh_g = foh_console()
    van, van_g = vanity_mirror()

    tex = {
        "fx_stucco": stucco((238, 230, 210), 9),
        "fx_stucco_dk": stucco((214, 202, 178), 10),
        "fx_terra": terracotta_trim(),
        "fx_crest": churrigueresque_crest(),
        "fx_lancet": lancet_window(),
        "fx_foxred": foxred,
        "fx_foxside": stucco((136, 22, 24), 4),
        "fx_clock": clk,
        "fx_dome": dome_metal(),
        "fx_bronze": stucco((96, 72, 42), 6),
        "fx_stclock": stclk,
        "fx_hope": hope,
        "fx_tile": spanish_tile(),
        "fx_awngrn": awning_green(),
        "fx_duct": hvac_duct(),
        "{fx_iron": wrought_iron(),
        "fx_mqscript": mqs,
        "fx_mqfront": mqf,
        "fx_mqside": mqsd,
        "fx_mqwing": marquee_wing(),
        "fx_mqsoffit": mqsof,
        "fx_terrazzo": terrazzo_floor(),
        "fx_walkstar": walk_of_stars("BUCK OWENS"),
        "fx_poster1": p1,
        "fx_poster2": p2,
        "fx_poster3": p3,
        "fx_boxwin": boxoffice_win(),
        "fx_entrydr": entry_door(),
        "fx_shopwin": shop_window(),
        "fx_evasign": eva,
        "fx_lobcarp": skouras_carpet(),
        "fx_lobwall": lobby_plaster(),
        "fx_raker": raker_stencil(),
        "fx_tapestry": california_tapestry(),
        "fx_concess": conc,
        "fx_concmenu": cmenu,
        "fx_skyceil": skyc,
        "fx_skscroll": skouras_wall_mural(),
        "fx_goldleaf": gold_leaf(),
        "fx_drapered": drape((168, 28, 32), 20),
        "fx_drapegld": drape((218, 178, 108), 18),
        "fx_drapeblk": drape((36, 38, 44), 16),
        "fx_seatback": seat_row_backs(),
        "fx_seatarm": seat_standard(),
        "fx_balcfasc": bfasc,
        "fx_stageflr": stage_floor(),
        "fx_screen": scr,
        "fx_exit": ex,
        "fx_console": foh,
        "fx_greenrm": greenroom_wall(),
        "fx_vanity": van,
        "fx_rollup": rollup_door(),
        "{fx_truss": stage_truss(),
    }
    glows = {
        "fx_foxred": foxred_g,
        "fx_clock": clk_g,
        "fx_stclock": stclk_g,
        "fx_hope": hope_g,
        "fx_mqscript": mqs_g,
        "fx_mqfront": mqf_g,
        "fx_mqside": mqsd_g,
        "fx_mqsoffit": mqsof_g,
        "fx_poster1": p1_g,
        "fx_poster2": p2_g,
        "fx_poster3": p3_g,
        "fx_evasign": eva_g,
        "fx_concess": conc_g,
        "fx_concmenu": cmenu_g,
        "fx_skyceil": skyc_g,
        "fx_balcfasc": bfasc_g,
        "fx_screen": scr_g,
        "fx_exit": ex_g,
        "fx_console": foh_g,
        "fx_vanity": van_g,
    }
    ntex, nglows = build_neighborhood_textures()
    tex.update(ntex)
    glows.update(nglows)
    ptex, pglows = build_padre_textures()
    tex.update(ptex)
    glows.update(pglows)
    etex, eglows = build_extra_textures()
    tex.update(etex)
    glows.update(eglows)
    return tex, glows


def main():
    os.makedirs(TEX, exist_ok=True)
    os.makedirs(os.path.dirname(WAD), exist_ok=True)
    tex, glows = build()
    small = {}
    for n, im in tex.items():
        assert len(n) <= 15, f"Texture name too long for WAD2: {n}"
        im.save(os.path.join(TEX, n + ".png"))
        if n in glows:
            glows[n].save(os.path.join(TEX, n + "_glow.png"))
        sw = max(16, -(-im.width // 4 // 16) * 16)
        sh = max(16, -(-im.height // 4 // 16) * 16)
        sm = im.resize((sw, sh), Image.LANCZOS)
        if im.mode == "RGBA":
            sm = sm.convert("RGBA")
        small[n] = sm
    write_wad(WAD, small)
    print(f"wrote {WAD}: {len(small)} textures ({len(glows)} glow maps)")


if __name__ == "__main__":
    main()
