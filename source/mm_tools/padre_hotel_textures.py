"""Procedural photo-matched textures for The Padre Hotel (1702 18th St, Bakersfield).

Covers exterior Spanish Colonial Revival cream stucco, scalloped frieze, window bays,
canopies, Farmacy Cafe & Brimstone storefronts, neon rooftop & blade signs, and full
interior materials for Basement Gym, Grand Lobby, Farmacy, Brimstone, Clover 1 & 2,
Floor 2 Event Rooms, Prairie Fire Terrace, Guest Rooms (406, 608, 40 Winks, Maverick,
Double Deuce, Corner Pocket), and Suites (Oil Baron, Farmer's Daughter, Head Honcho).

All texture names are strictly <= 15 chars for WAD2 compatibility.
"""
from __future__ import annotations
import math
import random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from fox_neighborhood_textures import load_art


def _font(size: int, bold: bool = True):
    candidates = (
        ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/timesbd.ttf"]
        if bold else
        ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/times.ttf"]
    )
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _serif(size: int, bold: bool = True):
    candidates = (
        ["C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/timesbd.ttf", "C:/Windows/Fonts/arialbd.ttf"]
        if bold else
        ["C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _noise(img: Image.Image, amt: int = 8, seed: int = 101) -> Image.Image:
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    is_rgba = img.mode == "RGBA"
    for y in range(h):
        for x in range(w):
            d = rng.randint(-amt, amt)
            if is_rgba:
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                px[x, y] = (
                    max(0, min(255, r + d)),
                    max(0, min(255, g + d)),
                    max(0, min(255, b + d)),
                    a,
                )
            else:
                r, g, b = px[x, y]
                px[x, y] = (
                    max(0, min(255, r + d)),
                    max(0, min(255, g + d)),
                    max(0, min(255, b + d)),
                )
    return img


def _center_text(d: ImageDraw.ImageDraw, cx: int, cy: int, txt: str, font, fill):
    bb = d.textbbox((0, 0), txt, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((cx - tw // 2, cy - th // 2), txt, fill=fill, font=font)


# ---------------------------------------------------------------------------
# EXTERIOR TEXTURES
# ---------------------------------------------------------------------------

def tex_pad_stucco() -> Image.Image:
    """Warm cream textured Spanish Revival stucco of Padre Hotel upper floors."""
    w = h = 128
    img = Image.new("RGB", (w, h), (229, 221, 204))
    rng = random.Random(1702)
    px = img.load()
    for y in range(h):
        for x in range(w):
            swirl = int(4 * math.sin(x * 0.21 + y * 0.13) + 3 * math.cos(x * 0.17 - y * 0.27))
            d = rng.randint(-6, 6) + swirl
            px[x, y] = (
                max(0, min(255, 229 + d)),
                max(0, min(255, 221 + d)),
                max(0, min(255, 204 + d)),
            )
    return img


def tex_pad_base() -> Image.Image:
    """Warm greige/taupe smooth stone-stucco of Padre ground floor & portal."""
    img = Image.new("RGB", (128, 128), (168, 159, 146))
    d = ImageDraw.Draw(img)
    for y in range(0, 128, 32):
        d.line([(0, y), (127, y)], fill=(150, 141, 129))
    return _noise(img, 5, 1703)


def tex_pad_north() -> Image.Image:
    """Medium warm grey painted stucco on Padre's north Wall St ground wing."""
    img = Image.new("RGB", (128, 128), (132, 129, 126))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 112, 127, 127], fill=(84, 83, 86))
    return _noise(img, 5, 1704)


def tex_pad_frieze() -> Image.Image:
    """Spanish Revival sawtooth/scalloped tan terracotta cornice frieze."""
    w, h = 128, 64
    img = Image.new("RGB", (w, h), (195, 180, 152))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, 12], fill=(170, 152, 122))
    d.rectangle([0, 13, w - 1, 22], fill=(212, 198, 172))
    # Sawtooth / diamond relief band
    for x in range(0, w, 16):
        d.polygon([(x, 44), (x + 8, 24), (x + 16, 44)], fill=(162, 144, 114), outline=(138, 120, 92))
        d.polygon([(x + 4, 44), (x + 8, 32), (x + 12, 44)], fill=(214, 201, 176))
    d.rectangle([0, 45, w - 1, h - 1], fill=(182, 166, 138))
    d.line([(0, 56), (w - 1, 56)], fill=(142, 126, 98), width=2)
    return _noise(img, 5, 1705)


def tex_pad_winbay() -> Image.Image:
    """Single upper-floor Padre Hotel window bay: cream stucco + dark bronze 6-pane window."""
    w, h = 128, 128
    img = tex_pad_stucco()
    d = ImageDraw.Draw(img)
    # Recessed window opening
    wx0, wy0, wx1, wy1 = 30, 22, 98, 104
    d.rectangle([wx0 - 4, wy0 - 4, wx1 + 4, wy1 + 6], fill=(198, 187, 166))
    d.rectangle([wx0, wy0, wx1, wy1], fill=(38, 44, 52))
    # Twin casement / mullion panes with warm curtain glow inside
    for side in range(2):
        px0 = wx0 + 5 + side * 31
        px1 = px0 + 26
        for row in range(3):
            py0 = wy0 + 5 + row * 24
            py1 = py0 + 20
            glow = (82, 92, 104) if row < 2 else (112, 104, 88)
            d.rectangle([px0, py0, px1, py1], fill=glow)
            d.line([(px0 + 2, py0 + 2), (px0 + 9, py1 - 3)], fill=(124, 136, 148), width=1)
    # Center vertical mullion & transom bar
    d.rectangle([62, wy0, 66, wy1], fill=(32, 36, 42))
    d.rectangle([wx0, 48, wx1, 52], fill=(32, 36, 42))
    # Stone sill
    d.rectangle([wx0 - 6, wy1, wx1 + 6, wy1 + 7], fill=(176, 163, 140))
    return _noise(img, 4, 1706)


def tex_pad_winlit() -> Image.Image:
    """Warmly illuminated Padre Hotel upper-floor window bay for evening/occupied rooms."""
    img = tex_pad_winbay()
    d = ImageDraw.Draw(img)
    wx0, wy0 = 30, 22
    for side in range(2):
        px0 = wx0 + 5 + side * 31
        px1 = px0 + 26
        for row in range(3):
            py0 = wy0 + 5 + row * 24
            py1 = py0 + 20
            d.rectangle([px0, py0, px1, py1], fill=(228, 198, 136))
    return _noise(img, 4, 1707)


def tex_pad_canopy() -> Image.Image:
    """Dark navy-slate 'THE PADRE' entrance marquee fascia."""
    w, h = 256, 64
    img = Image.new("RGB", (w, h), (34, 46, 62))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, 5], fill=(58, 74, 94))
    d.rectangle([0, h - 6, w - 1, h - 1], fill=(22, 30, 42))
    f = _serif(24, bold=True)
    _center_text(d, w // 2, h // 2, "THE  PADRE", f, (238, 232, 216))
    return _noise(img, 3, 1708)


def tex_pad_1702() -> Image.Image:
    """Greige stone portal header plaque with '1702' bronze/dark address numerals."""
    w, h = 128, 64
    img = Image.new("RGB", (w, h), (168, 159, 146))
    d = ImageDraw.Draw(img)
    f = _serif(28, bold=True)
    _center_text(d, w // 2 + 1, h // 2 + 1, "1702", f, (96, 88, 78))
    _center_text(d, w // 2, h // 2, "1702", f, (42, 38, 34))
    return _noise(img, 4, 1709)


def tex_pad_awntan() -> Image.Image:
    """Tan-and-cream vertical striped canvas awning (Farmacy Cafe & Brimstone center door)."""
    w, h = 128, 128
    img = Image.new("RGB", (w, h), (228, 216, 192))
    d = ImageDraw.Draw(img)
    for x in range(0, w, 16):
        d.rectangle([x, 0, x + 7, h - 1], fill=(184, 162, 126))
    d.rectangle([0, h - 10, w - 1, h - 1], fill=(156, 136, 102))
    return _noise(img, 5, 1710)


def tex_pad_awnblu() -> Image.Image:
    """Slate-blue canvas awning along Brimstone (18th St & H St)."""
    w, h = 128, 128
    img = Image.new("RGB", (w, h), (92, 114, 138))
    d = ImageDraw.Draw(img)
    for y in range(0, h, 16):
        d.line([(0, y), (w - 1, y)], fill=(82, 102, 126))
    d.rectangle([0, h - 10, w - 1, h - 1], fill=(66, 84, 106))
    return _noise(img, 5, 1711)


def tex_farm_win() -> Image.Image:
    """Farmacy Cafe storefront window with white arched 'FARMACY / CAFE' lettering (padre_180)."""
    w, h = 256, 192
    img = Image.new("RGB", (w, h), (34, 32, 30))
    d = ImageDraw.Draw(img)
    # Warm interior cafe glow visible through glass
    d.rectangle([8, 8, w - 9, h - 9], fill=(78, 62, 46))
    d.rectangle([18, 24, 96, 130], fill=(116, 86, 58))
    d.rectangle([152, 30, 232, 130], fill=(104, 78, 52))
    # White decorative window bars / decal band near bottom
    for x in range(12, w - 12, 14):
        d.rectangle([x, 126, x + 8, 138], fill=(226, 224, 218))
    d.line([(8, 122), (w - 9, 122)], fill=(226, 224, 218), width=2)
    d.line([(8, 142), (w - 9, 142)], fill=(226, 224, 218), width=2)
    # Arched FARMACY lettering (spelled with F!)
    f1 = _serif(34, bold=True)
    f2 = _font(20, bold=True)
    letters = "FARMACY"
    xs = [36, 68, 100, 132, 166, 196, 224]
    ys = [56, 47, 41, 39, 41, 47, 56]
    for ch, lx, ly in zip(letters, xs, ys):
        _center_text(d, lx + 2, ly + 2, ch, f1, (28, 24, 20))
        _center_text(d, lx, ly, ch, f1, (242, 238, 228))
    _center_text(d, w // 2, 86, "C A F E", f2, (240, 236, 226))
    # Dark bronze window mullions
    for mx in [0, 84, 170, w - 6]:
        d.rectangle([mx, 0, mx + 5, h - 1], fill=(38, 36, 34))
    d.rectangle([0, 0, w - 1, 6], fill=(38, 36, 34))
    d.rectangle([0, h - 8, w - 1, h - 1], fill=(38, 36, 34))
    return _noise(img, 4, 1712)


def tex_brim_win() -> Image.Image:
    """Brimstone Bar storefront window with diamond crest & lower privacy band."""
    w, h = 256, 192
    img = Image.new("RGB", (w, h), (30, 32, 36))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, w - 9, h - 9], fill=(46, 52, 62))
    # Warm amber & blue bar glow inside
    d.rectangle([20, 34, 110, 110], fill=(64, 84, 112))
    d.rectangle([140, 40, 232, 112], fill=(96, 74, 48))
    # Gold diamond logo in center pane
    d.polygon([(128, 56), (162, 78), (128, 100), (94, 78)], fill=(176, 148, 96), outline=(222, 198, 142))
    _center_text(d, 128, 78, "BRIMSTONE", _font(10, True), (36, 28, 18))
    # Lower white diamond-tooth band (visible in padre_052)
    for x in range(10, w - 10, 12):
        d.polygon([(x, 146), (x + 6, 134), (x + 12, 146)], fill=(222, 220, 214))
    d.rectangle([0, 148, w - 1, h - 1], fill=(42, 42, 44))
    for mx in [0, 82, 172, w - 6]:
        d.rectangle([mx, 0, mx + 5, h - 1], fill=(32, 34, 36))
    return _noise(img, 4, 1713)


def tex_pad_blade() -> Image.Image:
    """Vertical black blade sign on SE corner: 'P A D R E  H O T E L' in glowing white."""
    w, h = 64, 256
    img = Image.new("RGB", (w, h), (20, 22, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, w - 3, h - 3], outline=(76, 98, 148), width=2)
    f = _font(19, bold=True)
    chars = list("PADRE") + [" "] + list("HOTEL")
    y = 18
    for ch in chars:
        if ch == " ":
            y += 12
            continue
        _center_text(d, w // 2, y, ch, f, (244, 246, 255))
        y += 21
    return _noise(img, 3, 1714)


def tex_pad_neon() -> Image.Image:
    """Alpha-cutout rooftop scaffold neon sign: glowing red 'PADRE / HOTEL' ({pad_neon)."""
    w, h = 256, 128
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Open steel scaffold truss grid (keep 8px border transparent!)
    truss = (92, 86, 82, 255)
    for x in range(12, w - 12, 28):
        d.line([(x, 10), (x, h - 10)], fill=truss, width=2)
    for y in [12, 62, 114]:
        d.line([(12, y), (w - 12, y)], fill=truss, width=2)
    for x in range(12, w - 40, 28):
        d.line([(x, 12), (x + 28, 62)], fill=truss, width=1)
        d.line([(x, 62), (x + 28, 114)], fill=truss, width=1)
    # Bright red-orange neon letters
    f = _font(44, bold=True)
    for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        _center_text(d, w // 2 + ox, 36 + oy, "PADRE", f, (215, 36, 24, 255))
        _center_text(d, w // 2 + ox, 88 + oy, "HOTEL", f, (215, 36, 24, 255))
    _center_text(d, w // 2, 36, "PADRE", f, (255, 168, 124, 255))
    _center_text(d, w // 2, 88, "HOTEL", f, (255, 168, 124, 255))
    return img


def tex_pad_fesc() -> Image.Image:
    """Alpha-cutout white painted steel fire escape railing/grate ({pad_fesc)."""
    w, h = 128, 64
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = (224, 222, 216, 255)
    d.rectangle([8, 8, w - 9, 12], fill=c)
    d.rectangle([8, h - 13, w - 9, h - 9], fill=c)
    for x in range(10, w - 9, 12):
        d.rectangle([x, 8, x + 2, h - 9], fill=c)
    d.line([(10, 10), (w - 11, h - 11)], fill=(198, 196, 190, 255), width=2)
    return img


def tex_clover_arch() -> Image.Image:
    """Spanish Revival arched window bay for Clover Ballroom exterior (padre_087/387)."""
    w, h = 128, 160
    img = Image.new("RGB", (w, h), (224, 215, 196))
    d = ImageDraw.Draw(img)
    # Tall arched window with dark mullion grid
    d.pieslice([24, 18, 104, 98], 180, 360, fill=(186, 174, 152))
    d.rectangle([24, 58, 104, 138], fill=(186, 174, 152))
    d.pieslice([30, 24, 98, 92], 180, 360, fill=(44, 52, 58))
    d.rectangle([30, 58, 98, 134], fill=(44, 52, 58))
    for x in [52, 76]:
        d.line([(x, 28), (x, 134)], fill=(28, 32, 36), width=3)
    for y in [58, 84, 110]:
        d.line([(30, y), (98, y)], fill=(28, 32, 36), width=3)
    d.rectangle([20, 134, 108, 142], fill=(168, 156, 134))
    return _noise(img, 5, 1715)


# ---------------------------------------------------------------------------
# LOBBY, FARMACY, BRIMSTONE & GYM TEXTURES
# ---------------------------------------------------------------------------

def tex_pad_lobflr() -> Image.Image:
    """Grand Lobby interlocking cream-and-black basketweave marble floor (padre_171)."""
    w = h = 128
    img = Image.new("RGB", (w, h), (226, 218, 204))
    d = ImageDraw.Draw(img)
    # Interlocking black marble bars & cream stone tiles
    blk = (30, 30, 34)
    vein = (208, 198, 182)
    for gy in range(0, h, 64):
        for gx in range(0, w, 64):
            d.rectangle([gx, gy, gx + 63, gy + 63], outline=(188, 178, 162))
            d.rectangle([gx + 8, gy + 24, gx + 56, gy + 38], fill=blk)
            d.rectangle([gx + 24, gy + 0, gx + 38, gy + 16], fill=blk)
            d.rectangle([gx + 24, gy + 46, gx + 38, gy + 63], fill=blk)
            d.line([(gx + 4, gy + 8), (gx + 58, gy + 20)], fill=vein, width=1)
    return _noise(img, 4, 1720)


def tex_pad_mural() -> Image.Image:
    """Lobby focal mural behind front desk: cowgirl in cornstalks ('THAT DOG'LL HUNT', padre_170.jpg)."""
    w, h = 512, 512
    img = load_art("pad_cowgirl_mural.jpg", (w, h), sat=1.05, contrast=1.05, bright=0.88)
    d = ImageDraw.Draw(img)
    # Crisp white plaster niche border matching padre_170.jpg
    d.rectangle([0, 0, w - 1, h - 1], outline=(234, 230, 222), width=10)
    d.rectangle([10, 10, w - 11, h - 11], outline=(196, 190, 178), width=2)
    return img


def tex_farm_blade() -> Image.Image:
    """Hanging vintage lobby sign for Farmacy Cafe (padre_171)."""
    w, h = 128, 64
    img = Image.new("RGB", (w, h), (196, 188, 174))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, w - 4, h - 4], outline=(138, 54, 44), width=3)
    _center_text(d, w // 2, 26, "FARMACY", _serif(20, True), (148, 44, 36))
    _center_text(d, w // 2, 46, "CAFE", _font(12, True), (58, 52, 48))
    return _noise(img, 4, 1723)


def tex_farm_sign() -> Image.Image:
    """Alpha-cutout wrought-iron pitchfork + tractor + hanging 'FARMACY / CAFE' plaque ({farm_sign, padre_171.jpg)."""
    w, h = 256, 192
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    iron = (36, 32, 30, 255)
    iron_hi = (68, 62, 58, 255)
    # Horizontal wrought-iron pitchfork handle mounted across top-center (keep >=8px transparent margin!)
    d.rectangle([72, 44, 242, 53], fill=iron)
    d.line([(72, 46), (242, 46)], fill=iron_hi, width=2)
    # Wall mounting bracket on right end (x=234..244)
    d.rectangle([234, 28, 244, 70], fill=iron)
    # 4 curved wrought-iron pitchfork tines on left (x=14..74)
    d.arc([54, 18, 88, 78], 90, 270, fill=iron, width=6)
    for ty in (20, 38, 56, 74):
        d.line([(16, ty), (68, ty)], fill=iron, width=5)
        d.polygon([(10, ty), (20, ty - 3), (20, ty + 3)], fill=iron_hi)
    # Vintage tractor silhouette perched atop handle (padre_171.jpg!)
    d.ellipse([128, 22, 154, 48], fill=iron, outline=iron_hi, width=2)
    d.ellipse([135, 29, 147, 41], fill=(0, 0, 0, 0))
    d.ellipse([172, 30, 190, 48], fill=iron, outline=iron_hi, width=2)
    d.rectangle([142, 20, 178, 36], fill=iron)
    d.rectangle([170, 10, 175, 22], fill=iron)  # tractor exhaust stack
    d.arc([136, 10, 152, 24], 200, 350, fill=iron, width=3)  # steering wheel
    # Two suspension chains holding the embossed cream/crimson tin plaque
    for cx in (110, 204):
        for cy in range(53, 84, 7):
            d.ellipse([cx - 3, cy, cx + 3, cy + 6], outline=iron, width=2)
    # Embossed vintage cream & crimson sign plaque ('FARMACY / CAFE')
    d.rounded_rectangle([82, 82, 232, 172], radius=10, fill=(224, 214, 194, 255), outline=(138, 42, 36, 255), width=5)
    d.rounded_rectangle([90, 90, 224, 164], radius=6, outline=(62, 54, 48, 255), width=2)
    _center_text(d, 157, 116, "FARMACY", _serif(24, True), (146, 38, 32, 255))
    _center_text(d, 157, 145, "C A F E", _font(15, True), (46, 40, 36, 255))
    # Guarantee clean 8px transparent border
    d.rectangle([0, 0, w - 1, 7], fill=(0, 0, 0, 0))
    d.rectangle([0, h - 8, w - 1, h - 1], fill=(0, 0, 0, 0))
    d.rectangle([0, 0, 7, h - 1], fill=(0, 0, 0, 0))
    d.rectangle([w - 8, 0, w - 1, h - 1], fill=(0, 0, 0, 0))
    return img


def tex_farm_art() -> Image.Image:
    """Left pop-art portrait canvas in Farmacy Cafe: lime-green background & lotus hair (padre_172.jpg)."""
    img = load_art("farm_art1.jpg", (256, 256), sat=1.06, contrast=1.05, bright=0.88)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 255, 255], outline=(48, 42, 38), width=4)
    return img


def tex_farm_art2() -> Image.Image:
    """Right pop-art portrait canvas in Farmacy Cafe: hot-pink background & gold crown (padre_172.jpg)."""
    img = load_art("farm_art2.jpg", (256, 256), sat=1.06, contrast=1.05, bright=0.88)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 255, 255], outline=(48, 42, 38), width=4)
    return img


def tex_brim_bar() -> Image.Image:
    """Brimstone glowing cobalt-blue & amber backbar shelves with liquor bottles & TVs."""
    w, h = 256, 128
    img = Image.new("RGB", (w, h), (26, 22, 20))
    d = ImageDraw.Draw(img)
    # Upper sports TVs (padre_188)
    for tx in [18, 142]:
        d.rectangle([tx, 10, tx + 96, 54], fill=(18, 38, 68), outline=(10, 10, 12), width=3)
        d.rectangle([tx + 6, 16, tx + 90, 44], fill=(42, 98, 168))
        d.rectangle([tx + 6, 44, tx + 90, 50], fill=(212, 186, 74))
    # Glowing blue-lit bottle shelves below
    for sy in [64, 92]:
        d.rectangle([10, sy, w - 11, sy + 22], fill=(24, 58, 124))
        rng = random.Random(sy + 1725)
        for bx in range(16, w - 18, 10):
            bh = rng.randint(12, 19)
            bc = rng.choice([(218, 164, 62), (92, 196, 132), (224, 88, 72), (188, 214, 246)])
            d.rectangle([bx, sy + 21 - bh, bx + 6, sy + 21], fill=bc)
        d.line([(10, sy + 22), (w - 11, sy + 22)], fill=(122, 86, 52), width=3)
    return _noise(img, 4, 1725)


def tex_gym_mir() -> Image.Image:
    """Basement Gym wall mirror reflecting treadmills & bright white ceiling panels."""
    w, h = 256, 128
    img = Image.new("RGB", (w, h), (188, 196, 202))
    d = ImageDraw.Draw(img)
    # Ceiling reflection
    d.rectangle([0, 0, w - 1, 32], fill=(218, 224, 228))
    for lx in range(24, w, 64):
        d.rectangle([lx, 6, lx + 36, 18], fill=(248, 250, 252))
    # Wall & gym floor reflection
    d.rectangle([0, 33, w - 1, 88], fill=(172, 178, 184))
    d.rectangle([0, 89, w - 1, h - 1], fill=(74, 78, 84))
    # Subtle mirror panel seams & diagonal sheen
    for sx in [0, 85, 170, 255]:
        d.line([(sx, 0), (sx, h - 1)], fill=(136, 144, 150), width=2)
    d.line([(24, 12), (96, 114)], fill=(214, 222, 228), width=3)
    d.line([(148, 12), (220, 114)], fill=(214, 222, 228), width=3)
    return _noise(img, 3, 1726)


# ---------------------------------------------------------------------------
# FLOOR 2 EVENT ROOMS & PRAIRIE FIRE TEXTURES
# ---------------------------------------------------------------------------

def tex_pad_mat() -> Image.Image:
    """Upper Lobby inset carpet mat reading 'PADRE HOTEL' (padre_083 / 109)."""
    w, h = 256, 128
    img = Image.new("RGB", (w, h), (118, 128, 144))
    d = ImageDraw.Draw(img)
    d.rectangle([6, 6, w - 7, h - 7], outline=(216, 214, 208), width=4)
    d.rectangle([14, 14, w - 15, h - 15], outline=(88, 96, 112), width=2)
    f = _serif(28, bold=True)
    _center_text(d, w // 2, 44, "P A D R E", f, (228, 226, 218))
    _center_text(d, w // 2, 84, "H O T E L", f, (228, 226, 218))
    return _noise(img, 5, 1730)


def tex_pad_hshoe() -> Image.Image:
    """Upper Lobby dark charcoal wall studded with gold horseshoes above white wainscoting (padre_084)."""
    w, h = 128, 192
    img = Image.new("RGB", (w, h), (38, 38, 42))
    d = ImageDraw.Draw(img)
    # Gold horseshoes grid on upper 2/3
    for row, y in enumerate(range(14, 118, 24)):
        off = 10 if row % 2 else 0
        for x in range(8 + off, w - 12, 22):
            d.arc([x, y, x + 14, y + 16], 340, 200, fill=(208, 174, 88), width=3)
    # Crisp white paneled wainscoting on lower 1/3
    d.rectangle([0, 122, w - 1, h - 1], fill=(236, 234, 228))
    d.line([(0, 122), (w - 1, 122)], fill=(196, 192, 184), width=3)
    for px in range(8, w - 8, 30):
        d.rectangle([px, 132, px + 22, h - 12], outline=(204, 200, 192), width=2)
    return _noise(img, 4, 1731)


def tex_pad_dandy() -> Image.Image:
    """Event rooms (Stampede, Fox, Fireside) dandelion seed-head mural above white wainscoting (padre_097.jpg)."""
    return load_art("padre_dandelion_wall.jpg", (512, 512), sat=1.02, contrast=1.05, bright=0.88, h_seamless=36)


def tex_pad_evcarp() -> Image.Image:
    """Abstract charcoal, silver, and cream brushstroke banquet carpet (Stampede/Fox/Fireside)."""
    w = h = 128
    img = Image.new("RGB", (w, h), (72, 74, 78))
    d = ImageDraw.Draw(img)
    rng = random.Random(1733)
    for _ in range(48):
        x0, y0 = rng.randint(0, w), rng.randint(0, h)
        col = rng.choice([(44, 46, 50), (118, 120, 124), (192, 188, 178), (88, 92, 98)])
        d.polygon([(x0, y0), (x0 + rng.randint(14, 38), y0 + rng.randint(-8, 12)),
                   (x0 + rng.randint(8, 30), y0 + rng.randint(10, 26))], fill=col)
    return _noise(img, 6, 1734)


def tex_clov_carp() -> Image.Image:
    """Blue-grey diagonal striped carpet of Clover 2 Ballroom (padre_074)."""
    w = h = 128
    img = Image.new("RGB", (w, h), (86, 98, 112))
    d = ImageDraw.Draw(img)
    for i in range(-h, w + h, 16):
        d.line([(i, 0), (i + h, h)], fill=(118, 130, 144), width=5)
        d.line([(i + 6, 0), (i + 6 + h, h)], fill=(62, 72, 84), width=3)
    return _noise(img, 5, 1735)


def tex_conf_wood() -> Image.Image:
    """Warm cherry/walnut paneled cabinetry wall of Conference Room (padre_113/120)."""
    w, h = 128, 128
    img = Image.new("RGB", (w, h), (138, 86, 44))
    d = ImageDraw.Draw(img)
    for x in range(0, w, 64):
        d.rectangle([x + 4, 6, x + 59, 60], outline=(96, 56, 26), width=3)
        d.rectangle([x + 10, 12, x + 53, 54], fill=(150, 96, 50), outline=(112, 68, 32), width=1)
        d.rectangle([x + 4, 68, x + 59, 122], outline=(96, 56, 26), width=3)
        d.rectangle([x + 10, 74, x + 53, 116], fill=(144, 90, 46), outline=(112, 68, 32), width=1)
    return _noise(img, 5, 1736)


def tex_pad_elev() -> Image.Image:
    """Brushed steel/white hotel elevator double doors with center seam & call plate."""
    w, h = 128, 192
    img = Image.new("RGB", (w, h), (176, 180, 184))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(112, 116, 122), width=8)
    d.line([(w // 2, 8), (w // 2, h - 9)], fill=(82, 86, 92), width=3)
    for y in range(16, h - 16, 12):
        d.line([(12, y), (w - 13, y)], fill=(184, 188, 192), width=1)
    return _noise(img, 3, 1737)


# ---------------------------------------------------------------------------
# GUEST ROOMS, HALLWAYS & SUITES TEXTURES
# ---------------------------------------------------------------------------

def tex_pad_damask() -> Image.Image:
    """Black-and-cream ornate damask wallpaper of Padre guest-floor hallways (padre_085/191)."""
    w, h = 128, 128
    img = Image.new("RGB", (w, h), (222, 216, 204))
    d = ImageDraw.Draw(img)
    blk = (34, 34, 38)
    for cy in [32, 96]:
        for cx in [32, 96]:
            if (cx + cy) % 128 == 0:
                d.polygon([(cx, cy - 24), (cx + 16, cy), (cx, cy + 24), (cx - 16, cy)], fill=blk)
                d.ellipse([cx - 8, cy - 10, cx + 8, cy + 10], fill=(222, 216, 204))
                d.ellipse([cx - 4, cy - 5, cx + 4, cy + 5], fill=blk)
            else:
                d.polygon([(cx, cy - 16), (cx + 11, cy), (cx, cy + 16), (cx - 11, cy)], outline=blk, width=3)
    return _noise(img, 5, 1740)


def tex_pad_oilart() -> Image.Image:
    """Framed vintage sepia Kern River oil-field photograph in guest hallway (padre_191.jpg)."""
    return load_art("padre_oil_archival.jpg", (256, 192), crop=(63, 33, 1136, 867), sat=1.02, contrast=1.06, bright=0.88)


def tex_pad_rococo() -> Image.Image:
    """Farmer's Daughter Suite red/gold diamond wallpaper + gilded baroque mirror + crimson wainscoting (padre_149.jpg)."""
    return load_art("padre_rococo_wall.jpg", (512, 512), sat=1.05, contrast=1.05, bright=0.86)


def tex_pad_tv() -> tuple[Image.Image, Image.Image]:
    """Sleek dark-bezel flat-screen TV in Padre guest rooms & Conference Room."""
    w, h = 256, 128
    img = Image.new("RGB", (w, h), (18, 20, 24))
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    gd = ImageDraw.Draw(glow)
    # Brushed dark gunmetal outer bezel + inner screen
    d.rectangle([2, 2, w - 3, h - 3], outline=(54, 58, 66), width=3)
    d.rectangle([10, 10, w - 11, h - 13], fill=(28, 36, 48))
    # Subtle warm Padre Hotel welcome screen graphic
    for y in range(12, h - 14):
        t = (y - 12) / max(1, h - 26)
        col = (int(44 - 16 * t), int(54 - 18 * t), int(72 - 22 * t))
        d.line([(12, y), (w - 13, y)], fill=col)
    d.line([(20, h - 18), (96, 16)], fill=(62, 76, 96), width=6)
    _center_text(d, w // 2, h // 2 - 10, "THE  PADRE  HOTEL", _serif(18, True), (218, 194, 138))
    _center_text(d, w // 2, h // 2 + 16, "BAKERSFIELD  •  EST. 1928", _font(11, True), (168, 174, 184))
    d.ellipse([w // 2 - 2, h - 8, w // 2 + 2, h - 5], fill=(196, 42, 42))
    gd.rectangle([12, 12, w - 13, h - 15], fill=(22, 26, 34))
    _center_text(gd, w // 2, h // 2 - 10, "THE  PADRE  HOTEL", _serif(18, True), (96, 82, 52))
    return _noise(img, 2, 1751), glow.filter(ImageFilter.GaussianBlur(1.0))


def tex_pad_curtain(base_rgb: tuple[int, int, int], trim_rgb: tuple[int, int, int] | None = None, seed: int = 1752) -> Image.Image:
    """Full-height pleated hotel window drapery panel (dove-grey for rooms, crimson damask for Farmer's Daughter)."""
    w, h = 128, 256
    img = Image.new("RGB", (w, h), base_rgb)
    d = ImageDraw.Draw(img)
    for x in range(w):
        pleat = 0.68 + 0.32 * math.sin(2.0 * math.pi * x / 21.3)
        c = tuple(max(0, min(255, int(v * pleat))) for v in base_rgb)
        d.line([(x, 0), (x, h - 1)], fill=c)
    # Brushed steel grommet header rod band
    d.rectangle([0, 0, w - 1, 10], fill=(58, 60, 64))
    for gx in range(10, w - 6, 22):
        d.ellipse([gx - 4, 2, gx + 4, 10], outline=(168, 172, 178), width=2)
    if trim_rgb is not None:
        for y in range(28, h - 16, 48):
            for x in range(16, w - 12, 32):
                d.polygon([(x, y - 10), (x + 8, y), (x, y + 10), (x - 8, y)], outline=trim_rgb, width=1)
    return _noise(img, 3, seed)


def tex_pad_hboard() -> Image.Image:
    """Signature mustard-yellow button-tufted tall headboard of Padre guest rooms (padre_125)."""
    w, h = 128, 128
    img = Image.new("RGB", (w, h), (198, 166, 52))
    d = ImageDraw.Draw(img)
    for gy in range(16, h, 32):
        for gx in range(16, w, 32):
            d.line([(gx - 16, gy - 16), (gx + 16, gy + 16)], fill=(166, 136, 36), width=1)
            d.line([(gx + 16, gy - 16), (gx - 16, gy + 16)], fill=(166, 136, 36), width=1)
            d.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], fill=(134, 106, 24), outline=(224, 196, 84))
    d.rectangle([0, 0, w - 1, h - 1], outline=(154, 126, 32), width=3)
    return _noise(img, 5, 1742)


def tex_pad_rmcarp() -> Image.Image:
    """Dark navy/charcoal & slate geometric dashed guest-room carpet (padre_126/136)."""
    w = h = 128
    img = Image.new("RGB", (w, h), (38, 46, 54))
    d = ImageDraw.Draw(img)
    for y in range(4, h, 16):
        off = 8 if (y // 16) % 2 else 0
        for x in range(off, w, 24):
            d.rectangle([x, y, x + 12, y + 6], fill=(92, 106, 118))
    return _noise(img, 5, 1743)


def tex_pad_baron() -> Image.Image:
    """Oil Baron Suite dark charcoal architectural wall paneling (padre_143)."""
    w, h = 128, 128
    img = Image.new("RGB", (w, h), (52, 54, 58))
    d = ImageDraw.Draw(img)
    for x in [4, 66]:
        d.rectangle([x, 6, x + 56, 84], outline=(36, 38, 42), width=3)
        d.rectangle([x + 4, 10, x + 52, 80], outline=(68, 70, 76), width=1)
        d.rectangle([x, 90, x + 56, 122], outline=(36, 38, 42), width=3)
    return _noise(img, 3, 1744)


def tex_pad_herr() -> Image.Image:
    """Dark espresso herringbone hardwood floor of Oil Baron & Farmer's Daughter Suites."""
    w = h = 128
    img = Image.new("RGB", (w, h), (62, 48, 38))
    d = ImageDraw.Draw(img)
    for y in range(0, h, 16):
        for x in range(0, w, 32):
            d.polygon([(x, y), (x + 16, y + 8), (x + 16, y + 16), (x, y + 8)], fill=(78, 60, 46), outline=(44, 34, 26))
            d.polygon([(x + 16, y + 8), (x + 32, y), (x + 32, y + 8), (x + 16, y + 16)], fill=(54, 42, 32), outline=(40, 30, 22))
    return _noise(img, 4, 1745)


def tex_pad_fdred() -> Image.Image:
    """Farmer's Daughter Suite bold crimson red accent wall & damask sheen (padre_144/148)."""
    w, h = 128, 128
    img = Image.new("RGB", (w, h), (186, 26, 34))
    d = ImageDraw.Draw(img)
    for cy in [32, 96]:
        for cx in [32, 96]:
            d.polygon([(cx, cy - 18), (cx + 14, cy), (cx, cy + 18), (cx - 14, cy)], outline=(206, 46, 52), width=2)
    return _noise(img, 4, 1746)


def tex_pad_jacuz() -> Image.Image:
    """Silver-pewter mosaic tile & glowing aqua whirlpool tub trim for Padre Suites (padre_141/142)."""
    w, h = 128, 128
    img = Image.new("RGB", (w, h), (146, 152, 156))
    d = ImageDraw.Draw(img)
    rng = random.Random(1747)
    for y in range(0, h, 8):
        for x in range(0, w, 12):
            v = rng.randint(118, 186)
            d.rectangle([x, y, x + 10, y + 6], fill=(v, v + 4, v + 8))
    return _noise(img, 3, 1747)


def tex_pad_shcurt() -> Image.Image:
    """Alpha-cutout sheer window curtain for Room 608 bedroom-view shower ({pad_shcur)."""
    w, h = 128, 128
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Keep 8px border transparent; vertical sheer pleats alternating translucent/open
    for x in range(10, w - 10, 8):
        d.rectangle([x, 8, x + 4, h - 9], fill=(236, 236, 240, 255))
    return img


def build_padre_textures() -> tuple[dict[str, Image.Image], dict[str, Image.Image]]:
    neon = tex_pad_neon()
    # Emissive glow for {pad_neon (red-orange letters only, black elsewhere)
    neon_g = Image.new("RGB", neon.size, (0, 0, 0))
    ngd = ImageDraw.Draw(neon_g)
    f_neon = _font(44, bold=True)
    _center_text(ngd, neon.width // 2, 36, "PADRE", f_neon, (240, 72, 42))
    _center_text(ngd, neon.width // 2, 88, "HOTEL", f_neon, (240, 72, 42))

    blade = tex_pad_blade()
    blade_g = Image.new("RGB", blade.size, (0, 0, 0))
    bgd = ImageDraw.Draw(blade_g)
    bgd.rectangle([2, 2, blade.width - 3, blade.height - 3], outline=(48, 72, 138), width=2)
    f_bl = _font(19, bold=True)
    yy = 18
    for ch in list("PADRE") + [" "] + list("HOTEL"):
        if ch == " ":
            yy += 12
            continue
        _center_text(bgd, blade.width // 2, yy, ch, f_bl, (190, 200, 235))
        yy += 21

    bbar = tex_brim_bar()
    bbar_g = Image.new("RGB", bbar.size, (0, 0, 0))
    bbd = ImageDraw.Draw(bbar_g)
    for tx in [18, 142]:
        bbd.rectangle([tx + 6, 16, tx + 90, 50], fill=(52, 108, 178))
    for sy in [64, 92]:
        bbd.rectangle([10, sy, bbar.width - 11, sy + 22], fill=(28, 68, 148))

    wlit = tex_pad_winlit()
    wlit_g = Image.new("RGB", wlit.size, (0, 0, 0))
    wgd = ImageDraw.Draw(wlit_g)
    for side in range(2):
        px0 = 35 + side * 31
        for row in range(3):
            py0 = 27 + row * 24
            wgd.rectangle([px0, py0, px0 + 26, py0 + 20], fill=(125, 100, 58))

    ptv, ptv_g = tex_pad_tv()

    tex = {
        "pad_stucco": tex_pad_stucco(),
        "pad_base": tex_pad_base(),
        "pad_north": tex_pad_north(),
        "pad_frieze": tex_pad_frieze(),
        "pad_winbay": tex_pad_winbay(),
        "pad_winlit": wlit,
        "pad_canopy": tex_pad_canopy(),
        "pad_1702": tex_pad_1702(),
        "pad_awntan": tex_pad_awntan(),
        "pad_awnblu": tex_pad_awnblu(),
        "farm_win": tex_farm_win(),
        "brim_win": tex_brim_win(),
        "pad_blade": blade,
        "{pad_neon": neon,
        "{pad_fesc": tex_pad_fesc(),
        "clov_arch": tex_clover_arch(),
        "pad_lobflr": tex_pad_lobflr(),
        "pad_mural": tex_pad_mural(),
        "farm_blade": tex_farm_blade(),
        "{farm_sign": tex_farm_sign(),
        "farm_art": tex_farm_art(),
        "farm_art2": tex_farm_art2(),
        "brim_bar": bbar,
        "gym_mir": tex_gym_mir(),
        "pad_mat": tex_pad_mat(),
        "pad_hshoe": tex_pad_hshoe(),
        "pad_dandy": tex_pad_dandy(),
        "pad_evcarp": tex_pad_evcarp(),
        "clov_carp": tex_clov_carp(),
        "conf_wood": tex_conf_wood(),
        "pad_elev": tex_pad_elev(),
        "pad_damask": tex_pad_damask(),
        "pad_oilart": tex_pad_oilart(),
        "pad_rococo": tex_pad_rococo(),
        "pad_tv": ptv,
        "pad_curt_gy": tex_pad_curtain((142, 146, 152), None, 1752),
        "pad_curt_rd": tex_pad_curtain((168, 26, 34), (196, 148, 68), 1753),
        "pad_hboard": tex_pad_hboard(),
        "pad_rmcarp": tex_pad_rmcarp(),
        "pad_baron": tex_pad_baron(),
        "pad_herr": tex_pad_herr(),
        "pad_fdred": tex_pad_fdred(),
        "pad_jacuz": tex_pad_jacuz(),
        "{pad_shcur": tex_pad_shcurt(),
    }
    glows = {
        "{pad_neon": neon_g,
        "pad_blade": blade_g,
        "brim_bar": bbar_g,
        "pad_winlit": wlit_g,
        "pad_tv": ptv_g,
    }
    for name in tex:
        assert len(name) <= 15, f"Padre texture name too long ({len(name)}): {name}"
    return tex, glows
