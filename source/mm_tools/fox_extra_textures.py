"""Additional Feb 2026 photo-matched Downtown Bakersfield landmark & street textures
for the full G St..K St, 18th St..21st St scope of fox-block-gallery.

All texture names are strictly <= 15 chars for WAD2 compatibility.
"""
from __future__ import annotations
import math
import random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from fox_neighborhood_textures import (
    add_noise, dim, font, load_art, BLACK, BOLD, SERIF, SCRIPT, street_blade, road_name_stencil
)


def nile_marquee_2026():
    """Feb 2026 Nile Theater marquee (1721 19th St): cursive 'Nile', red/blue chevrons,
    left: SPLOONKY RAVE 2.6 / LOS HERMANOS MENDOZA 2.15, right: CUP CAKKE / SOLD OUT 2.21."""
    W, H = 512, 160
    im = Image.new("RGB", (W, H), (238, 232, 218))
    glow = Image.new("RGB", (W, H), (18, 18, 22))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)

    # Upper Art Deco chevron frieze in cobalt blue & crimson red on white
    d.rectangle([0, 0, W, 56], fill=(242, 240, 236))
    for x in range(0, W, 32):
        d.polygon([(x, 42), (x + 16, 18), (x + 32, 42)], outline=(38, 86, 172), width=4)
        d.polygon([(x, 52), (x + 16, 28), (x + 32, 52)], outline=(198, 42, 46), width=4)
    # Cursive 'Nile' neon script on left and right wings + center vertical fin
    d.rectangle([244, 0, 268, 58], fill=(232, 228, 222), outline=(198, 42, 46), width=3)
    for cx in (118, 394):
        for ox, oy in ((-2, 2), (2, 2)):
            d.text((cx + ox, 28 + oy), "Nile", font=font(SCRIPT, 44), fill=(32, 68, 148), anchor="mm")
        d.text((cx, 28), "Nile", font=font(SCRIPT, 44), fill=(228, 56, 62), anchor="mm")
        gd.text((cx, 28), "Nile", font=font(SCRIPT, 44), fill=(235, 75, 75), anchor="mm")

    # Warm gold-trimmed readerboard boxes
    d.rectangle([0, 56, W, H], fill=(208, 152, 82))
    for bx0, bx1, lines in [
        (12, 244, [("SPLOONKY RAVE   2.6", (34, 34, 38)), ("LOS HERMANOS MENDOZA 2.15", (176, 32, 34))]),
        (268, 500, [("CUP CAKKE     2.21", (176, 32, 34)), ("SOLD OUT", (34, 34, 38))]),
    ]:
        d.rectangle([bx0, 66, bx1, H - 14], fill=(238, 236, 228), outline=(176, 44, 42), width=3)
        gd.rectangle([bx0, 66, bx1, H - 14], fill=(155, 148, 128))
        for li, (txt, col) in enumerate(lines):
            cy = 88 + li * 30
            fsz = 16 if len(txt) > 20 else 20
            d.text(((bx0 + bx1) // 2, cy), txt, font=font(BLACK, fsz), fill=col, anchor="mm")
            gd.text(((bx0 + bx1) // 2, cy), txt, font=font(BLACK, fsz), fill=(0, 0, 0), anchor="mm")
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(0.8))


def nile_upper_deco():
    """White fluted vertical Art Deco facade of The Nile Theater above marquee (fblk_133/294)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (234, 232, 226))
    d = ImageDraw.Draw(im)
    for x in range(12, W, 24):
        d.rectangle([x, 16, x + 8, H - 20], fill=(198, 196, 190))
        d.line([(x, 16), (x, H - 20)], fill=(152, 150, 146), width=2)
    d.rectangle([0, 0, W, 14], fill=(184, 180, 172))
    return dim(add_noise(im, 4), 0.96)


def nile_blue_tile():
    """Deep cobalt-blue mosaic tile entrance & ticket booth base of The Nile Theater (fblk_133)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (26, 44, 98))
    d = ImageDraw.Draw(im)
    rng = random.Random(1721)
    for y in range(0, H, 8):
        for x in range(0, W, 8):
            v = rng.randint(-14, 18)
            d.rectangle([x, y, x + 6, y + 6], fill=(max(0, 26 + v), max(0, 44 + v), min(255, 98 + v)))
    # Center white ticket booth window & twin glass doors
    d.rectangle([104, 24, 152, 98], fill=(232, 230, 224), outline=(36, 62, 134), width=3)
    d.rectangle([118, 42, 138, 68], fill=(42, 48, 58))
    for dx in (32, 184):
        d.rectangle([dx, 20, dx + 42, H - 4], fill=(44, 52, 64), outline=(178, 182, 188), width=3)
        d.line([(dx + 21, 20), (dx + 21, H - 4)], fill=(178, 182, 188), width=2)
    return add_noise(im, 3)


def front_porch_music():
    """Light ice-blue storefront of 'FRONT PORCH MUSIC' adjacent east of Nile Theater (fblk_292)."""
    W, H = 256, 160
    im = Image.new("RGB", (W, H), (188, 206, 212))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 42), "FRONT PORCH", font=font(SERIF, 24), fill=(34, 42, 48), anchor="mm")
    d.text((W // 2, 68), "MUSIC", font=font(BLACK, 22), fill=(48, 64, 82), anchor="mm")
    d.rectangle([16, 94, W - 16, H], fill=(42, 46, 52), outline=(228, 228, 224), width=3)
    for x in (82, 174):
        d.line([(x, 94), (x, H)], fill=(228, 228, 224), width=3)
    return dim(add_noise(im, 4), 0.95)


def thirst_trap_billboard():
    """Dramatic rooftop-bar billboard at SW 19th & H reading 'THIRST TRAP / PRAIRIE FIRE • PADRE HOTEL' (fblk_046/047)."""
    W, H = 512, 256
    im = load_art("padre_thirst_billboard.jpg", (W, H), sat=1.05, contrast=1.06, bright=0.90)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(48, 46, 44), width=6)
    d.rectangle([6, 6, W - 7, H - 7], outline=(86, 82, 78), width=2)
    # Subtle evening billboard floodlight glow across the central typography
    glow = ImageEnhance.Brightness(im).enhance(0.24)
    gd = ImageDraw.Draw(glow)
    gd.rectangle([0, 0, W - 1, 14], fill=(0, 0, 0))
    gd.rectangle([0, H - 15, W - 1, H - 1], fill=(0, 0, 0))
    gd.rectangle([0, 0, 14, H - 1], fill=(0, 0, 0))
    gd.rectangle([W - 15, 0, W - 1, H - 1], fill=(0, 0, 0))
    return im, glow.filter(ImageFilter.GaussianBlur(1.5))


def ovation_theatre():
    """The Ovation Theatre (1622 19th St): cream 2-story facade, 5 blue arched awnings & OVATION window sign (fblk_137)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (226, 220, 208))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=(176, 168, 156))
    # 5 arched 2nd-story windows with royal-blue dome awnings
    for i in range(5):
        cx = 56 + i * 100
        d.rectangle([cx - 24, 48, cx + 24, 112], fill=(54, 62, 70), outline=(188, 182, 170), width=3)
        d.pieslice([cx - 28, 26, cx + 28, 82], 180, 360, fill=(36, 74, 138), outline=(24, 52, 98), width=2)
    # Molded cornice band
    d.rectangle([0, 126, W, 142], fill=(198, 190, 176))
    # Ground floor dark storefront windows + door on left + OVATION sign
    d.rectangle([22, 162, 66, H], fill=(78, 62, 48), outline=(176, 170, 158), width=3)
    d.rectangle([92, 162, W - 28, H - 14], fill=(42, 48, 54), outline=(232, 228, 220), width=4)
    for mx in range(172, W - 40, 80):
        d.line([(mx, 162), (mx, H - 14)], fill=(232, 228, 220), width=3)
    d.rectangle([182, 174, 246, 214], fill=(238, 236, 230))
    d.text((214, 202), "OVATION", font=font(BLACK, 13), fill=(32, 36, 44), anchor="mm")
    return dim(add_noise(im, 4), 0.96)


def zama_brick_facade():
    """Red-brick 1-story restaurant row on south side of 19th St (H..Eye) with white stone diamonds & 'ZAMA' (fblk_141)."""
    W, H = 512, 192
    im = Image.new("RGB", (W, H), (146, 72, 62))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 10):
        d.line([(0, y), (W, y)], fill=(118, 56, 48), width=1)
    d.rectangle([0, 0, W, 14], fill=(224, 220, 212))
    # Decorative white diamond inlays
    for dx in (86, 426):
        d.polygon([(dx, 36), (dx + 14, 52), (dx, 68), (dx - 14, 52)], fill=(232, 228, 220))
    # Charcoal ZAMA sign panel & black patio awning
    d.rectangle([166, 32, 346, 86], fill=(58, 56, 54), outline=(196, 188, 174), width=2)
    d.text((256, 66), "Z A M A", font=font(SERIF, 24), fill=(228, 208, 158), anchor="mm")
    d.rectangle([16, 98, W - 16, 120], fill=(32, 32, 36))
    d.rectangle([28, 120, W - 28, H], fill=(38, 34, 32))
    for gx in range(48, W - 48, 72):
        d.rectangle([gx, 128, gx + 52, H - 6], fill=(58, 52, 46), outline=(92, 76, 62), width=2)
    return dim(add_noise(im, 4), 0.95)


def art_center_facade():
    """Bakersfield Art Association 'ART CENTER GALLERY' at SW corner of 19th & Eye (fblk_309)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (228, 224, 218))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 12], fill=(168, 58, 48))
    for wx in (48, 206, 364):
        d.rectangle([wx, 34, wx + 96, 104], fill=(58, 68, 76), outline=(176, 172, 166), width=4)
        d.line([(wx + 48, 34), (wx + 48, 104)], fill=(224, 220, 214), width=3)
    d.rectangle([24, 122, W - 24, 162], fill=(28, 72, 78))
    d.text((W // 2, 138), "ART CENTER", font=font(SERIF, 24), fill=(242, 240, 234), anchor="mm")
    d.text((W // 2, 154), "GALLERY", font=font(BOLD, 12), fill=(212, 218, 216), anchor="mm")
    d.rectangle([24, 162, W - 24, 184], fill=(142, 78, 72))
    d.rectangle([32, 184, W - 32, H], fill=(46, 52, 58))
    return dim(add_noise(im, 4), 0.96)


def buena_vista_museum():
    """Buena Vista Museum of Natural History & Science (2018 Chester Ave): green/yellow upper + blue curved sign + science/fauna murals (fblk_163)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (146, 204, 154))
    d = ImageDraw.Draw(im)
    # Green & yellow upper facade with 3 dark framed windows + trim
    d.rectangle([0, 0, 28, 128], fill=(226, 208, 78))
    d.rectangle([W - 28, 0, W, 128], fill=(226, 208, 78))
    d.rectangle([0, 0, W, 8], fill=(214, 196, 68))
    for wx in (64, 216, 368):
        d.rectangle([wx, 18, wx + 80, 86], fill=(48, 60, 70), outline=(42, 86, 64), width=5)
        d.line([(wx + 40, 18), (wx + 40, 86)], fill=(176, 186, 192), width=2)
    # Projecting royal-blue curved awning sign
    d.rectangle([16, 92, W - 16, 156], fill=(24, 82, 174), outline=(222, 232, 246), width=3)
    d.text((W // 2, 106), "Buena Vista", font=font(SCRIPT, 23), fill=(242, 218, 92), anchor="mm")
    d.text((W // 2, 128), "MUSEUM", font=font(SERIF, 30), fill=(248, 250, 254), anchor="mm")
    d.text((W // 2, 147), "of Natural History & Science", font=font(BOLD, 14), fill=(224, 234, 248), anchor="mm")
    # Blue security-gated entrance below with crisp science/animal silhouettes, vertical 'MUSEUM' & '2018' (fblk_163.jpg!)
    d.rectangle([0, 156, W, H], fill=(28, 36, 50))
    for gx in range(18, W - 18, 16):
        d.line([(gx, 160), (gx, H)], fill=(34, 86, 174), width=2)
    wht = (238, 244, 250)
    # 1) Great white / Miocene shark silhouette on left (x=34..128)
    d.polygon([
        (36, 208), (68, 196), (82, 178), (90, 195), (124, 202),
        (134, 190), (128, 208), (136, 224), (122, 213), (92, 218),
        (80, 230), (76, 217), (52, 214)
    ], fill=wht)
    # 2) Atom Bohr orbital emblem (cx=168, cy=188) + Whale fluke/body below (x=148..216)
    acx, acy = 168, 184
    d.ellipse([acx - 18, acy - 7, acx + 18, acy + 7], outline=wht, width=2)
    d.ellipse([acx - 7, acy - 18, acx + 7, acy + 18], outline=wht, width=2)
    d.ellipse([acx - 4, acy - 4, acx + 4, acy + 4], fill=(244, 218, 76))
    d.polygon([(148, 222), (174, 210), (206, 214), (220, 204), (214, 218), (222, 230), (204, 224), (172, 228)], fill=wht)
    # Center royal-blue pier with vertical gold 'M U S E U M'
    d.rectangle([236, 160, 276, H - 4], fill=(24, 74, 162), outline=(218, 228, 244), width=2)
    for idx, ch in enumerate("MUSEUM"):
        d.text((256, 171 + idx * 14), ch, font=font(BLACK, 13), fill=(246, 216, 68), anchor="mm")
    # 3) DNA double-helix strand (x=296..324)
    for y in range(168, 244, 6):
        dx = int(11 * math.sin((y - 168) * 0.16))
        d.ellipse([310 + dx - 2, y - 2, 310 + dx + 2, y + 2], fill=wht)
        d.ellipse([310 - dx - 2, y - 2, 310 - dx + 2, y + 2], fill=(168, 216, 250))
        d.line([(310 - dx, y), (310 + dx, y)], fill=(128, 176, 226), width=1)
    # 4) Striding lion silhouette (x=340..404)
    d.ellipse([342, 192, 366, 216], fill=wht)  # mane
    d.polygon([(356, 202), (396, 204), (402, 218), (398, 238), (390, 238), (388, 220),
               (366, 220), (362, 238), (354, 238), (354, 216)], fill=wht)
    d.arc([392, 190, 412, 214], 260, 120, fill=wht, width=3)  # tail
    # 5) Bold '2018' address numerals on right
    d.rectangle([420, 186, 488, 220], fill=(22, 68, 148), outline=(238, 216, 86), width=2)
    d.text((454, 203), "2018", font=font(BLACK, 20), fill=(246, 220, 84), anchor="mm")
    return dim(add_noise(im, 3), 0.94)


def aura_facade():
    """Crisp white gabled facade next to Buena Vista Museum with giant black 'AURA' channel letters (fblk_162/420)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (232, 232, 230))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 12], fill=(52, 54, 58))
    d.text((W // 2, 92), "A U R A", font=font(SERIF, 64), fill=(28, 30, 34), anchor="mm")
    d.rectangle([0, 156, W, 174], fill=(24, 26, 30))
    d.rectangle([16, 174, W - 16, H], fill=(42, 46, 52))
    return add_noise(im, 4)


def woolworth_sign():
    """Classic red wrap-around 'F. W. WOOLWORTH CO.' sign band with gold serif letters (1400 19th St, fblk_169)."""
    W, H = 512, 96
    im = Image.new("RGB", (W, H), (192, 44, 42))
    glow = Image.new("RGB", (W, H), (24, 6, 6))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([0, 0, W, 10], fill=(228, 226, 220))
    d.rectangle([0, H - 10, W, H], fill=(228, 226, 220))
    for y in (16, H - 16):
        d.line([(0, y), (W, y)], fill=(238, 204, 112), width=3)
    d.text((W // 2, H // 2), "F. W.  WOOLWORTH  CO.", font=font(SERIF, 34), fill=(246, 216, 124), anchor="mm")
    gd.text((W // 2, H // 2), "F. W.  WOOLWORTH  CO.", font=font(SERIF, 34), fill=(160, 130, 60), anchor="mm")
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(0.8))


def woolworth_upper():
    """White 3-story mid-century ribbon-window upper facade of Woolworth's building (1400 19th St, fblk_328)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (236, 236, 232))
    d = ImageDraw.Draw(im)
    for wy in (36, 142):
        d.rectangle([28, wy, W - 28, wy + 58], fill=(56, 66, 72), outline=(188, 190, 186), width=4)
        for mx in range(76, W - 36, 56):
            d.rectangle([mx, wy, mx + 6, wy + 58], fill=(224, 224, 220))
    return add_noise(im, 3)


def kress_art_deco():
    """Historic 4-story tan brick/terracotta S. H. Kress & Co. Art Deco facade (1401 19th St, fblk_173/326)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (208, 192, 164))
    d = ImageDraw.Draw(im)
    # Tall vertical spandrel bays
    for bx in (20, 96, 172):
        d.rectangle([bx, 18, bx + 60, H - 36], fill=(78, 92, 88), outline=(228, 216, 192), width=4)
        for sy in (86, 154):
            d.rectangle([bx, sy, bx + 60, sy + 18], fill=(156, 142, 118))
        d.line([(bx + 30, 18), (bx + 30, H - 36)], fill=(218, 206, 182), width=2)
    d.rectangle([0, H - 32, W, H], fill=(58, 56, 48))
    d.text((W // 2, H - 16), "K R E S S", font=font(SERIF, 20), fill=(228, 206, 142), anchor="mm")
    return dim(add_noise(im, 4), 0.96)


def kress_blade():
    """Vertical dark-green/bronze 'KRESS' blade sign at 19th & K St (fblk_172)."""
    W, H = 64, 256
    im = Image.new("RGB", (W, H), (38, 46, 42))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, W - 4, H - 4], outline=(212, 192, 136), width=3)
    for i, ch in enumerate("KRESS"):
        d.text((W // 2, 34 + i * 46), ch, font=font(SERIF, 34), fill=(238, 228, 198), anchor="mm")
    return add_noise(im, 3)


def antique_mall():
    """Slate-blue 'ANTIQUE MALL' storefront west of Kress on 19th St (fblk_174)."""
    W, H = 256, 160
    im = Image.new("RGB", (W, H), (96, 118, 146))
    d = ImageDraw.Draw(im)
    d.rectangle([48, 28, W - 48, 76], fill=(236, 232, 222), outline=(44, 56, 74), width=3)
    d.text((W // 2, 52), "ANTIQUE MALL", font=font(SERIF, 20), fill=(36, 48, 68), anchor="mm")
    d.rectangle([16, 92, W - 16, H], fill=(42, 46, 54))
    return dim(add_noise(im, 4), 0.95)


def micasa_furniture():
    """Mi Casa Home Furniture ('LIQUIDATION SALE') curved corner facade at NE 19th & K St (fblk_322)."""
    W, H = 512, 192
    im = Image.new("RGB", (W, H), (222, 220, 216))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 16):
        d.line([(x, 0), (x, 96)], fill=(198, 196, 192), width=1)
    d.ellipse([216, 8, 296, 48], fill=(196, 38, 38))
    d.text((256, 28), "Mi Casa", font=font(SCRIPT, 22), fill=(248, 244, 238), anchor="mm")
    d.text((256, 62), "HOME FURNITURE", font=font(BLACK, 24), fill=(196, 36, 36), anchor="mm")
    d.rectangle([176, 76, 336, 102], fill=(244, 232, 72), outline=(196, 36, 36), width=2)
    d.text((256, 89), "LIQUIDATION SALE", font=font(BLACK, 15), fill=(196, 28, 28), anchor="mm")
    d.rectangle([0, 104, W, 118], fill=(192, 38, 38))
    d.rectangle([16, 118, W - 16, H], fill=(44, 42, 42))
    return add_noise(im, 4)


def mint_bar_facade():
    """The Mint Bar (1207 19th St): tan stucco + red brick piers + vintage 'COCKTAILS / The MINT' green neon sign (fblk_124)."""
    W, H = 512, 192
    im = Image.new("RGB", (W, H), (198, 184, 156))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([42, 28, 224, 92], fill=(224, 220, 208), outline=(58, 96, 68), width=3)
    d.text((133, 44), "COCKTAILS", font=font(BOLD, 14), fill=(178, 52, 44), anchor="mm")
    d.text((133, 70), "The MINT", font=font(SCRIPT, 32), fill=(36, 128, 72), anchor="mm")
    gd.text((133, 70), "The MINT", font=font(SCRIPT, 32), fill=(48, 185, 96), anchor="mm")
    d.rectangle([284, 42, 456, 78], fill=(232, 228, 218), outline=(92, 84, 72), width=2)
    d.text((370, 60), "CashGOLDEN.com", font=font(BOLD, 18), fill=(38, 36, 34), anchor="mm")
    # Brick lower storefront with wrought-iron security grilles
    d.rectangle([0, 104, W, H], fill=(138, 68, 52))
    for wx in (36, 156, 286, 404):
        d.rectangle([wx, 116, wx + 84, H - 6], fill=(38, 40, 44), outline=(188, 182, 172), width=2)
    return add_noise(im, 4), glow.filter(ImageFilter.GaussianBlur(1.0))


def tiki_ko_facade():
    """Tiki-Ko tropical cocktail lounge on K St & Service St (fblk_377/384)."""
    W, H = 256, 192
    im = Image.new("RGB", (W, H), (222, 220, 212))
    d = ImageDraw.Draw(im)
    for wx in (24, 96, 168):
        d.rectangle([wx, 24, wx + 52, 74], fill=(56, 66, 68), outline=(168, 166, 158), width=3)
    d.rectangle([56, 86, 200, 120], fill=(238, 234, 222), outline=(64, 52, 38), width=2)
    d.text((128, 103), "Tiki-Ko", font=font(SCRIPT, 26), fill=(44, 36, 28), anchor="mm")
    d.rectangle([0, 122, W, 136], fill=(82, 118, 92))
    d.rectangle([16, 136, W - 16, H], fill=(64, 52, 42))
    d.rectangle([96, 142, 160, H - 6], fill=(214, 112, 54))
    return add_noise(im, 4)


def bobby_cloud_law():
    """Red-brick corner building on Service St & Chester ('BOBBY CLOUD LAW', fblk_375)."""
    W, H = 256, 160
    im = Image.new("RGB", (W, H), (142, 74, 62))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 12], fill=(198, 192, 182))
    d.rectangle([0, 72, W, 96], fill=(34, 36, 40))
    d.text((W // 2, 84), "BOBBY CLOUD LAW", font=font(SERIF, 16), fill=(232, 214, 156), anchor="mm")
    d.rectangle([18, 96, W - 18, H], fill=(46, 52, 58))
    return dim(add_noise(im, 4), 0.95)


def h1800_chester():
    """The 18hundred (1800 Chester Ave) 2-story concrete-pilaster facade with Brazilian Acai & Habibi's Hookah (fblk_179)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (196, 188, 176))
    d = ImageDraw.Draw(im)
    # 2nd-floor blue reflective windows between concrete pilasters
    for bx in (18, 182, 346):
        d.rectangle([bx, 22, bx + 146, 106], fill=(74, 96, 122), outline=(216, 210, 198), width=4)
        for mx in range(bx + 36, bx + 140, 36):
            d.line([(mx, 22), (mx, 106)], fill=(212, 206, 196), width=2)
    # Ground-floor tenant signs: BRAZILIAN ACAI BOWLS & JUICE BAR | Habibi's Hookah LOUNGE & SMOKE SHOP
    d.rectangle([18, 126, 248, 150], fill=(76, 168, 72))
    d.text((133, 138), "BRAZILIAN ACAI & JUICE BAR", font=font(BLACK, 13), fill=(248, 248, 242), anchor="mm")
    d.rectangle([264, 126, 494, 150], fill=(196, 36, 42))
    d.text((379, 138), "Habibi's Hookah  SMOKE SHOP", font=font(BLACK, 13), fill=(248, 244, 242), anchor="mm")
    d.rectangle([18, 152, 248, H], fill=(52, 56, 62))
    d.rectangle([264, 152, 494, H], fill=(44, 48, 58))
    return add_noise(im, 4)


def chain_cohn_clark():
    """Tan classical stucco building at NW 18th & Chester ('CHAIN | COHN | CLARK', fblk_183)."""
    W, H = 512, 192
    im = Image.new("RGB", (W, H), (198, 188, 162))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 28], fill=(168, 158, 134))
    d.text((W // 2, 14), "CHAIN | COHN | CLARK", font=font(SERIF, 20), fill=(48, 44, 38), anchor="mm")
    for wx in (36, 146, 316, 424):
        d.rectangle([wx, 68, wx + 56, 148], fill=(48, 56, 58), outline=(162, 152, 128), width=3)
    d.ellipse([236, 56, 276, 96], fill=(142, 148, 152), outline=(228, 224, 214), width=3)
    d.text((256, 76), "C", font=font(SERIF, 24), fill=(242, 240, 236), anchor="mm")
    d.rectangle([232, 106, 280, H], fill=(44, 48, 52))
    return dim(add_noise(im, 4), 0.96)


def fire_station_21st():
    """Bakersfield Central Fire Station at NW 21st & H: cream stucco, red lettering & 4 white apparatus doors (fblk_209)."""
    W, H = 512, 192
    im = Image.new("RGB", (W, H), (226, 216, 198))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 16], fill=(184, 168, 148))
    d.text((W // 2, 42), "BAKERSFIELD CENTRAL FIRE STATION", font=font(SERIF, 20), fill=(188, 44, 38), anchor="mm")
    for i in range(4):
        bx = 28 + i * 118
        d.rectangle([bx, 68, bx + 96, H], fill=(240, 240, 238), outline=(156, 148, 136), width=3)
        for py in range(82, H, 22):
            d.line([(bx + 4, py), (bx + 92, py)], fill=(208, 208, 204), width=2)
        d.rectangle([bx + 8, 98, bx + 88, 118], fill=(56, 66, 74))
    return add_noise(im, 3)


def legion_banners():
    """American Legion Post 26 grey facade with red/white/blue band & 5 military service portrait banners (fblk_196)."""
    W, H = 512, 192
    im = Image.new("RGB", (W, H), (186, 188, 190))
    d = ImageDraw.Draw(im)
    # 5 vertical portrait banners along upper half
    for i in range(5):
        bx = 28 + i * 96
        d.rectangle([bx, 12, bx + 64, 96], fill=(214, 216, 220), outline=(128, 130, 134), width=2)
        # Uniformed silhouette + flag stripe
        d.ellipse([bx + 22, 22, bx + 42, 44], fill=(92, 74, 62))
        ucol = [(34, 44, 68), (42, 54, 44), (232, 232, 234), (36, 52, 82), (56, 62, 52)][i]
        d.polygon([(bx + 10, 94), (bx + 18, 46), (bx + 46, 46), (bx + 54, 94)], fill=ucol)
    # Red & blue stripe separating lower stone wall
    d.rectangle([0, 102, W // 2, 112], fill=(196, 36, 38))
    d.rectangle([W // 2, 102, W, 112], fill=(32, 64, 148))
    d.rectangle([0, 112, W, H], fill=(156, 158, 162))
    d.text((W // 2, 132), "AMERICAN LEGION POST 26", font=font(BOLD, 16), fill=(32, 48, 96), anchor="mm")
    return add_noise(im, 4)


def today_pylon():
    """Today Cleaners pylon sign: 'TODAY CLEANERS / IN BY 10 READY AT 4' (2033 H St, fblk_199)."""
    W, H = 128, 96
    im = Image.new("RGB", (W, H), (238, 204, 64))
    glow = Image.new("RGB", (W, H), (40, 34, 10))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([3, 3, W - 4, H - 4], outline=(38, 42, 46), width=4)
    d.text((W // 2, 26), "TODAY", font=font(BLACK, 22), fill=(26, 28, 30), anchor="mm")
    d.text((W // 2, 48), "CLEANERS", font=font(BLACK, 18), fill=(26, 28, 30), anchor="mm")
    d.rectangle([8, 64, W - 9, 86], fill=(242, 240, 234))
    d.text((W // 2, 75), "IN BY 10 READY AT 4", font=font(BOLD, 10), fill=(186, 34, 34), anchor="mm")
    gd.rectangle([8, 8, W - 9, 86], fill=(165, 140, 45))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(0.8))


def caa_gear_mural():
    """Vibrant blue, orange, yellow gear-and-ribbon street mural on SE corner of 18th & H St (padre_052 / fblk_343)."""
    return load_art("caa_gear_mural.jpg", (512, 256), sat=1.05, contrast=1.05, bright=0.88)


def bldg_1701_18th():
    """2-story commercial building across 18th St from Padre Hotel: dark upper windows + bright sky-blue band (fblk_091)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (226, 224, 220))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 24, W, 92], fill=(72, 68, 66))
    for wx in range(28, W - 28, 64):
        d.rectangle([wx, 32, wx + 42, 84], fill=(48, 56, 66), outline=(188, 186, 182), width=2)
    # Signature bright cerulean-blue horizontal band
    d.rectangle([0, 96, W, 128], fill=(42, 142, 212))
    for gx in (32, 196, 360):
        d.rectangle([gx, 152, gx + 118, H], fill=(44, 50, 58), outline=(168, 168, 164), width=3)
    return add_noise(im, 4)


def bldg_1715_18th():
    """1715 18th St: warm mottled cream Spanish Revival 2-story apartment/office facing Padre Hotel (fblk_093)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (218, 202, 174))
    d = ImageDraw.Draw(im)
    for wx in (32, 108, 184):
        d.rectangle([wx, 42, wx + 40, 94], fill=(64, 72, 82), outline=(238, 232, 220), width=3)
    # Center pedimented entrance portal '1715'
    d.polygon([(84, 146), (128, 118), (172, 146)], fill=(188, 172, 146), outline=(146, 132, 108), width=2)
    d.rectangle([96, 146, 160, H], fill=(58, 52, 46), outline=(188, 172, 146), width=4)
    d.text((128, 138), "1715", font=font(BOLD, 14), fill=(42, 38, 34), anchor="mm")
    for wx in (22, 174):
        d.rectangle([wx, 168, wx + 60, 212], fill=(198, 202, 206), outline=(238, 236, 230), width=3)
    return add_noise(im, 5)


def sw_frieze_18th():
    """Southwestern geometric terracotta/teal frieze building at SW corner of 18th & Eye St (fblk_349)."""
    W, H = 512, 192
    im = Image.new("RGB", (W, H), (206, 188, 166))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 12, W, 36], fill=(62, 54, 52))
    for x in range(8, W, 28):
        d.polygon([(x + 14, 16), (x + 24, 24), (x + 14, 32), (x + 4, 24)], fill=(218, 116, 54))
    d.rectangle([24, 72, W - 24, 148], fill=(78, 116, 112), outline=(228, 224, 218), width=3)
    d.rectangle([0, 148, W, H], fill=(156, 72, 58))
    for px in (16, 172, 328, 484):
        d.rectangle([px, 56, px + 18, H], fill=(68, 128, 78))
    return add_noise(im, 4)


def kccd_facade():
    """Kern Community College District bronze-and-ribbed-metal 2-story facade along 21st St (fblk_226)."""
    W, H = 512, 192
    im = Image.new("RGB", (W, H), (92, 86, 84))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 38], fill=(74, 68, 66))
    d.text((W // 2, 20), "KERN COMMUNITY COLLEGE DISTRICT", font=font(BOLD, 20), fill=(238, 236, 232), anchor="mm")
    d.rectangle([0, 38, W, 52], fill=(178, 134, 112))
    for x in range(0, W, 12):
        d.line([(x, 52), (x, 118)], fill=(68, 64, 62), width=2)
    d.rectangle([0, 118, W, H], fill=(48, 42, 38))
    return add_noise(im, 3)


def wild_mama_mural():
    """Bright sky-blue 'WILD MAMA' eye-mural building at 21st St & Chester (fblk_227)."""
    W, H = 256, 160
    im = Image.new("RGB", (W, H), (52, 148, 218))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 36), "WILD MAMA", font=font(BLACK, 20), fill=(244, 238, 228), anchor="mm")
    for cx in (72, 184):
        d.ellipse([cx - 34, 68, cx + 34, 112], fill=(244, 242, 238), outline=(28, 32, 38), width=3)
        d.ellipse([cx - 14, 76, cx + 14, 104], fill=(92, 62, 42))
        d.ellipse([cx - 6, 84, cx + 6, 96], fill=(18, 20, 24))
    return add_noise(im, 4)


def guarantee_shoe():
    """Guarantee Shoe Center at SW corner of 21st St & Chester Ave (tan stucco + blue awning, fblk_423)."""
    W, H = 256, 160
    im = Image.new("RGB", (W, H), (208, 194, 152))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 38), "GUARANTEE", font=font(BLACK, 22), fill=(188, 44, 38), anchor="mm")
    d.text((W // 2, 60), "SHOE CENTER", font=font(BOLD, 16), fill=(38, 44, 68), anchor="mm")
    d.rectangle([12, 78, W - 12, 104], fill=(28, 68, 148))
    d.rectangle([18, 104, W - 18, H], fill=(44, 48, 54))
    return add_noise(im, 4)


def get_bus_side():
    """Golden Empire Transit ('GET bus') blue, yellow & green city bus livery (fblk_418)."""
    W, H = 512, 160
    im = Image.new("RGB", (W, H), (28, 124, 214))
    d = ImageDraw.Draw(im)
    # Tinted passenger windows
    for wx in range(36, W - 64, 72):
        d.rectangle([wx, 34, wx + 58, 86], fill=(34, 46, 58), outline=(196, 204, 212), width=3)
    d.text((420, 22), "Bakersfield", font=font(SCRIPT, 22), fill=(242, 246, 252), anchor="mm")
    # Yellow & green swoop stripe + 'GET bus'
    d.polygon([(0, 96), (W, 108), (W, H), (0, H)], fill=(238, 196, 42))
    d.polygon([(0, 118), (W, 126), (W, H), (0, H)], fill=(58, 168, 76))
    d.text((196, 134), "GET bus", font=font(BLACK, 28), fill=(246, 248, 242), anchor="mm")
    return add_noise(im, 3)


def yellow_crosswalk():
    """High-visibility yellow ladder crosswalk at 18th St & H St (padre_052 / fblk_103)."""
    W, H = 128, 128
    im = Image.new("RGB", (W, H), (104, 106, 110))
    d = ImageDraw.Draw(im)
    yel = (218, 172, 48)
    d.rectangle([0, 6, W, 16], fill=yel)
    d.rectangle([0, H - 16, W, H - 6], fill=yel)
    for x in range(12, W, 32):
        d.rectangle([x, 16, x + 14, H - 16], fill=yel)
    return dim(add_noise(im, 6), 0.92)


def stop_sign_oct():
    """Alpha-cutout octagonal red 'STOP' street sign ({fn_stopsg)."""
    S = 128
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(42, 10), (86, 10), (118, 42), (118, 86), (86, 118), (42, 118), (10, 86), (10, 42)]
    d.polygon(pts, fill=(244, 244, 242, 255))
    ipts = [(45, 15), (83, 15), (113, 45), (113, 83), (83, 113), (45, 113), (15, 83), (15, 45)]
    d.polygon(ipts, fill=(198, 32, 34, 255))
    d.text((S // 2, S // 2), "STOP", font=font(BLACK, 32), fill=(248, 248, 246, 255), anchor="mm")
    return im


def oneway_sign():
    """Black-and-white 'ONE WAY' arrow sign (20th St, K St, H St — fblk_038/105/378)."""
    W, H = 128, 64
    im = Image.new("RGB", (W, H), (28, 30, 32))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, W - 4, H - 4], outline=(242, 242, 240), width=3)
    d.polygon([(14, 32), (38, 14), (38, 23), (114, 23), (114, 41), (38, 41), (38, 50)], fill=(244, 244, 242))
    d.text((72, 32), "ONE WAY", font=font(BLACK, 14), fill=(24, 26, 28), anchor="mm")
    return add_noise(im, 2)


def build_extra_textures():
    nmq, nmq_g = nile_marquee_2026()
    wsg, wsg_g = woolworth_sign()
    mnt, mnt_g = mint_bar_facade()
    tpy, tpy_g = today_pylon()
    tht, tht_g = thirst_trap_billboard()

    tex = {
        "fn_nilemq": nmq,
        "fn_nileup": nile_upper_deco(),
        "fn_nilebl": nile_blue_tile(),
        "fn_fporch": front_porch_music(),
        "fn_thirst": tht,
        "fn_ovation": ovation_theatre(),
        "fn_zama": zama_brick_facade(),
        "fn_artctr": art_center_facade(),
        "fn_bvm": buena_vista_museum(),
        "fn_aura": aura_facade(),
        "fn_woolsg": wsg,
        "fn_woolup": woolworth_upper(),
        "fn_kress": kress_art_deco(),
        "fn_kressbl": kress_blade(),
        "fn_antiq": antique_mall(),
        "fn_micasa": micasa_furniture(),
        "fn_mint": mnt,
        "fn_tikiko": tiki_ko_facade(),
        "fn_bobby": bobby_cloud_law(),
        "fn_h1800": h1800_chester(),
        "fn_chain": chain_cohn_clark(),
        "fn_firest": fire_station_21st(),
        "fn_legban": legion_banners(),
        "fn_tdpyl": tpy,
        "fn_caamur": caa_gear_mural(),
        "fn_b1701": bldg_1701_18th(),
        "fn_b1715": bldg_1715_18th(),
        "fn_swfrz": sw_frieze_18th(),
        "fn_kccd": kccd_facade(),
        "fn_wildm": wild_mama_mural(),
        "fn_guarsh": guarantee_shoe(),
        "fn_getbus": get_bus_side(),
        "fn_ylwxw": yellow_crosswalk(),
        "{fn_stopsg": stop_sign_oct(),
        "fn_oneway": oneway_sign(),
        "fn_st_18th": street_blade("18th Street"),
        "fn_st_gst": street_blade("G Street"),
        "fn_st_kst": street_blade("K Street"),
        "fn_rd_18th": road_name_stencil("18TH ST"),
        "fn_rd_19th": road_name_stencil("19TH ST"),
        "fn_rd_21st": road_name_stencil("21ST ST"),
        "fn_rd_gst": road_name_stencil("G ST"),
        "fn_rd_kst": road_name_stencil("K ST"),
        "fn_rd_stop": road_name_stencil("STOP"),
    }
    glows = {
        "fn_nilemq": nmq_g,
        "fn_woolsg": wsg_g,
        "fn_mint": mnt_g,
        "fn_tdpyl": tpy_g,
        "fn_thirst": tht_g,
    }
    for name in tex:
        assert len(name) <= 15, f"Extra texture name too long ({len(name)}): {name}"
    return tex, glows
