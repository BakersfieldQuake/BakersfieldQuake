"""Textures for the inside of Golden West Casino (gw_casino.py) and its entrance plaza: gw_*.png in BakersfieldQuake/textures
(+ _glow copies for the screens and signs) and the quarter-size palette copies in out/maps/gwcasino.wad.
Colours follow the card-room photos: tan rubble-stone walls, brown timber beams, a dark carpet with cream rosettes, white
ceiling tiles, red-felt poker tables with a black rail, slate-blue doors, white louvred shutters.
usage: python build_gw_casino_textures.py"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402

TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
WAD = os.path.join(HERE, "out", "maps", "gwcasino.wad")
rnd = random.Random(1001)
GLOW = ("gw_tv1", "gw_tv2", "gw_tv3", "gw_tv4", "gw_exit", "gw_lightp")          # screens and signs that shine in the dark


def font(names, px):
    for n in names:
        try:
            return ImageFont.truetype(n, px)
        except OSError:
            pass
    return ImageFont.load_default()


BOLD = ["arialbd.ttf", "DejaVuSans-Bold.ttf"]
BLACK = ["ariblk.ttf", "arialbd.ttf"]
SCRIPT = ["segoesc.ttf", "pala.ttf", "georgiaz.ttf", "ariali.ttf"]


def noise(im, amt=6):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            n = rnd.randint(-amt, amt)
            p = px[x, y]
            px[x, y] = tuple(max(0, min(255, c + n)) for c in p[:3])
    return im


def dim(im, k):
    return ImageEnhance.Brightness(im.convert("RGB")).enhance(k)


def wrapped(im, fn):
    """Draw fn(draw, dx, dy) at the nine wrap-around offsets so the tile has no seam."""
    S = im.width
    d = ImageDraw.Draw(im)
    for dx in (-S, 0, S):
        for dy in (-S, 0, S):
            fn(d, dx, dy)


def petal(d, cx, cy, ang, length, width, fill):
    pts = []
    for k in range(13):
        t = k / 12 * math.pi
        a, b = math.cos(t) * length / 2 + length / 2, math.sin(t) * width / 2
        pts.append((a, b))
    for k in range(13):
        t = k / 12 * math.pi
        a, b = math.cos(t) * length / 2 + length / 2, -math.sin(t) * width / 2
        pts.append((a, b))
    ca, sa = math.cos(ang), math.sin(ang)
    d.polygon([(cx + a * ca - b * sa, cy + a * sa + b * ca) for a, b in pts], fill=fill)


def carpet():
    """Dark brown-black carpet with cream-brown rosettes and vines (photos 1 and 2)."""
    S = 256
    im = Image.new("RGB", (S, S), (52, 34, 34))

    def motif(d, dx, dy):
        for cx, cy, big in ((64, 64, 1), (192, 192, 1), (192, 64, 0), (64, 192, 0)):
            cx, cy = cx + dx, cy + dy
            L, col = (46, (150, 108, 78)) if big else (34, (112, 76, 58))
            for k in range(8):
                petal(d, cx, cy, k * math.pi / 4, L, L * 0.42, col)
            for k in range(8):
                petal(d, cx, cy, k * math.pi / 4 + math.pi / 8, L * 0.55, L * 0.2, (52, 34, 34))
            d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(190, 150, 110) if big else (150, 108, 80))
        for a in range(0, 360, 45):                                   # vines between the rosettes
            r = 28
            x0, y0 = 128 + dx + math.cos(math.radians(a)) * r, 128 + dy + math.sin(math.radians(a)) * r
            d.ellipse([x0 - 5, y0 - 5, x0 + 5, y0 + 5], outline=(100, 66, 50), width=3)
        for cx, cy in ((0, 128), (128, 0), (256, 128), (128, 256)):
            d.ellipse([cx + dx - 9, cy + dy - 9, cx + dx + 9, cy + dy + 9], outline=(86, 56, 46), width=3)

    wrapped(im, motif)
    return dim(noise(im, 6).filter(ImageFilter.GaussianBlur(0.5)), 0.9)


def istone():
    """Warm tan rubble stone with grey mortar (photos 1 and 2: the walls of the card room)."""
    S = 256
    im = Image.new("RGB", (S, S), (128, 114, 92))
    d = ImageDraw.Draw(im)
    y = 0
    while y < S:
        h = rnd.randint(22, 36)
        x = -rnd.randint(0, 30)
        while x < S:
            w = rnd.randint(28, 66)
            c = rnd.randint(-16, 16)
            d.rounded_rectangle([x + 2, y + 2, x + w - 2, y + h - 2], radius=6, fill=(214 + c, 188 + c, 142 + c // 2))
            x += w
        y += h
    return dim(noise(im, 7), 1.05)


def itile():
    S = 128
    im = Image.new("RGB", (S, S), (150, 140, 122))
    d = ImageDraw.Draw(im)
    for x in (0, 64):
        for y in (0, 64):
            c = rnd.randint(-6, 6)
            d.rectangle([x + 2, y + 2, x + 61, y + 61], fill=(214 + c, 202 + c, 176 + c))
    return dim(noise(im, 5), 0.95)


def ceil():
    """White acoustic ceiling tiles, 2 x 2 ft (a texture repeat is 4 ft)."""
    S = 128
    im = Image.new("RGB", (S, S), (150, 150, 144))
    d = ImageDraw.Draw(im)
    for x in (0, 64):
        for y in (0, 64):
            d.rectangle([x + 2, y + 2, x + 61, y + 61], fill=(206, 204, 194))
    for _ in range(400):
        x, y = rnd.randint(0, S - 1), rnd.randint(0, S - 1)
        d.point((x, y), fill=(190, 188, 180))
    return noise(im, 4)


def beam():
    S = 64
    im = Image.new("RGB", (S, S), (82, 54, 38))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 4):
        c = rnd.randint(-10, 8)
        d.line([(0, y), (S, y + rnd.randint(-1, 1))], fill=(70 + c, 44 + c, 30 + c), width=1)
    return noise(im, 4)


def leather():
    S = 64
    im = Image.new("RGB", (S, S), (28, 27, 30))
    return noise(im, 5).filter(ImageFilter.GaussianBlur(0.4))


def felt(vertical=False):
    """Red felt of a poker table, 9.5 x 4 ft: the white racetrack line, the gold emblems and 'Golden West Casino' (photo 2)."""
    W, H = 512, 224
    im = Image.new("RGB", (W, H), (150, 28, 34))
    im = noise(im, 8)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([34, 28, W - 35, H - 29], radius=84, outline=(222, 214, 190), width=3)        # racetrack
    d.rounded_rectangle([20, 14, W - 21, H - 15], radius=96, outline=(196, 150, 70), width=2)
    for cx in (74, W - 75):                                                                        # emblems
        d.ellipse([cx - 30, H / 2 - 30, cx + 30, H / 2 + 30], outline=(224, 176, 72), width=4)
        d.ellipse([cx - 20, H / 2 - 20, cx + 20, H / 2 + 20], fill=(224, 176, 72))
        d.ellipse([cx - 12, H / 2 - 12, cx + 12, H / 2 + 12], fill=(150, 28, 34))
    d.text((W / 2, H / 2 - 12), "Golden West", font=font(SCRIPT, 40), fill=(226, 180, 76), anchor="mm")
    d.text((W / 2, H / 2 + 28), "CASINO", font=font(BLACK, 24), fill=(226, 180, 76), anchor="mm")
    for k in range(9):                                                                             # the nine seats' bet boxes
        x = 86 + k * 42
        d.rounded_rectangle([x - 11, 40 - 4, x + 11, 40 + 14], radius=4, outline=(222, 214, 190), width=1)
    im = dim(im, 0.95)
    return im.rotate(90, expand=True) if vertical else im


def tv_scoreboard():
    W, H = 256, 144
    im = Image.new("RGB", (W, H), (10, 22, 78))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 34], fill=(18, 40, 130))
    d.text((10, 17), "BLINDS 200/400", font=font(BOLD, 14), fill=(250, 250, 250), anchor="lm")
    d.text((W - 10, 17), "00:02:16", font=font(BLACK, 22), fill=(80, 255, 110), anchor="rm")
    for i in range(6):
        y = 44 + i * 16
        d.text((12, y), "TABLE %d" % (i + 1), font=font(BOLD, 12), fill=(210, 220, 255))
        d.text((110, y), "%d / 9" % rnd.randint(5, 9), font=font(BOLD, 12), fill=(250, 220, 90))
        d.text((190, y), "NL HOLD'EM", font=font(BOLD, 11), fill=(170, 190, 240))
    return im


def tv_sport():
    W, H = 256, 144
    im = Image.new("RGB", (W, H), (30, 110, 50))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 32):
        d.rectangle([x, 0, x + 15, H], fill=(36, 124, 58))
    d.line([(0, 70), (W, 70)], fill=(230, 240, 230), width=2)
    d.ellipse([W / 2 - 26, 44, W / 2 + 26, 96], outline=(230, 240, 230), width=2)
    for _ in range(14):
        x, y = rnd.randint(20, W - 20), rnd.randint(20, 110)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=rnd.choice([(230, 60, 50), (240, 240, 250)]))
    d.rectangle([0, H - 26, W, H], fill=(14, 18, 40))
    d.text((10, H - 13), "LAL 98   BKN 91   Q4 2:16", font=font(BOLD, 14), fill=(250, 250, 250), anchor="lm")
    return im


def tv_poker():
    W, H = 256, 144
    im = Image.new("RGB", (W, H), (14, 70, 40))
    d = ImageDraw.Draw(im)
    d.ellipse([20, 20, W - 20, H - 14], fill=(24, 110, 62), outline=(120, 80, 40), width=6)
    for k in range(5):
        x = 62 + k * 28
        d.rounded_rectangle([x, 52, x + 22, 86], radius=3, fill=(246, 246, 240))
        d.text((x + 11, 69), rnd.choice("AKQJ10"), font=font(BOLD, 14), fill=rnd.choice([(190, 30, 30), (20, 20, 20)]), anchor="mm")
    d.rectangle([0, 0, W, 22], fill=(120, 20, 28))
    d.text((W / 2, 11), "LIVE POKER", font=font(BLACK, 16), fill=(250, 220, 120), anchor="mm")
    return im


def tv_news():
    W, H = 256, 144
    im = Image.new("RGB", (W, H), (40, 60, 110))
    d = ImageDraw.Draw(im)
    d.ellipse([104, 34, 152, 82], fill=(196, 150, 120))
    d.rectangle([80, 82, 176, H], fill=(30, 30, 44))
    d.rectangle([0, H - 40, W, H - 14], fill=(240, 240, 244))
    d.rectangle([0, H - 40, 54, H - 14], fill=(200, 30, 30))
    d.text((27, H - 27), "CA", font=font(BLACK, 16), fill=(250, 250, 250), anchor="mm")
    d.text((62, H - 27), "CASINO RULES CHANGE APRIL 1", font=font(BOLD, 11), fill=(20, 20, 30), anchor="lm")
    return im


def number(n):
    im = Image.new("RGB", (64, 64), (240, 238, 228))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, 62, 62], outline=(20, 20, 24), width=3)
    d.text((32, 34), str(n), font=font(BLACK, 40 if n < 10 else 34), fill=(14, 14, 18), anchor="mm")
    return im


def door():
    """Slate blue-grey panel door (the left wall of photo 1)."""
    im = Image.new("RGB", (128, 256), (88, 112, 132))
    d = ImageDraw.Draw(im)
    for box in ((12, 12, 115, 110), (12, 124, 115, 243)):
        d.rectangle(box, outline=(60, 78, 96), width=4)
        d.rectangle([box[0] + 6, box[1] + 6, box[2] - 6, box[3] - 6], outline=(112, 138, 158), width=2)
    d.ellipse([100, 126, 110, 136], fill=(196, 176, 120))
    return noise(im, 5)


def shutter():
    """White louvred doors (the back wall of photo 2)."""
    im = Image.new("RGB", (128, 128), (232, 228, 216))
    d = ImageDraw.Draw(im)
    for x0 in (0, 64):
        d.rectangle([x0 + 3, 3, x0 + 60, 124], outline=(176, 172, 160), width=3)
        for y in range(10, 120, 8):
            d.line([(x0 + 8, y), (x0 + 56, y)], fill=(176, 172, 160), width=2)
            d.line([(x0 + 8, y + 2), (x0 + 56, y + 2)], fill=(246, 244, 236), width=1)
    return noise(im, 3)


def frame(w, h, seed):
    r = random.Random(seed)
    im = Image.new("RGB", (w, h), (120, 88, 40))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w - 7, h - 7], fill=(40, 30, 20))
    sky = r.choice([(120, 160, 200), (210, 170, 120), (90, 110, 150)])
    d.rectangle([9, 9, w - 10, h * 0.55], fill=sky)
    d.rectangle([9, h * 0.55, w - 10, h - 10], fill=r.choice([(90, 100, 60), (130, 100, 70), (70, 90, 60)]))
    for _ in range(3):
        x = r.randint(10, w - 20)
        d.polygon([(x, h * 0.55), (x + r.randint(10, 24), h * 0.55 - r.randint(10, 24)), (x + r.randint(24, 40), h * 0.55)], fill=(80, 76, 70))
    return noise(im, 4)


def exit_sign():
    im = Image.new("RGB", (64, 32), (20, 130, 50))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, 62, 30], outline=(230, 250, 230), width=2)
    d.text((32, 17), "EXIT", font=font(BLACK, 20), fill=(240, 255, 240), anchor="mm")
    return im


def lightp():
    im = Image.new("RGB", (64, 32), (250, 244, 224))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 63, 31], outline=(190, 186, 170), width=2)
    return im


def chip(col):
    im = Image.new("RGB", (16, 16), col)
    d = ImageDraw.Draw(im)
    for y in range(0, 16, 4):
        d.line([(0, y), (16, y)], fill=(240, 240, 236), width=1)
    return im


def flag():
    """Stamped flagstone concrete of the entrance plaza (photo 3: wet, warm grey)."""
    S = 256
    im = Image.new("RGB", (S, S), (96, 88, 78))
    d = ImageDraw.Draw(im)
    y = 0
    while y < S:
        h = rnd.randint(40, 64)
        x = -rnd.randint(0, 40)
        while x < S:
            w = rnd.randint(44, 84)
            c = rnd.randint(-14, 14)
            d.rounded_rectangle([x + 3, y + 3, x + w - 3, y + h - 3], radius=9, fill=(156 + c, 144 + c, 128 + c))
            x += w
        y += h
    return dim(noise(im, 6).filter(ImageFilter.GaussianBlur(0.5)), 0.92)


def flowers():
    """The round bed round the horse: pansies in yellow, orange and purple (photo 3)."""
    S = 128
    im = Image.new("RGB", (S, S), (44, 84, 36))
    d = ImageDraw.Draw(im)
    for _ in range(120):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        g = rnd.randint(-16, 20)
        d.ellipse([x - 5, y - 3, x + 5, y + 3], fill=(48 + g, 100 + g, 40 + g))
    for _ in range(150):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        c = rnd.choice([(244, 208, 44), (240, 130, 40), (238, 196, 40), (122, 70, 160), (236, 236, 224)])
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=c)
        d.point((x, y), fill=(60, 30, 20))
    return im


def cone():
    """'CAUTION WET FLOOR / PISO MOJADO' (photo 3): a yellow sign, 2 ft tall."""
    im = Image.new("RGB", (64, 128), (238, 196, 14))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 63, 127], outline=(40, 34, 10), width=3)
    d.polygon([(32, 8), (50, 36), (14, 36)], outline=(20, 20, 10), fill=(250, 220, 40))
    d.text((32, 29), "!", font=font(BLACK, 22), fill=(20, 20, 10), anchor="mm")
    for y, t, s in ((52, "CAUTION", 11), (66, "WET", 12), (80, "FLOOR", 12), (98, "PISO", 11), (112, "MOJADO", 10)):
        d.text((32, y), t, font=font(BLACK, s), fill=(20, 20, 10), anchor="mm")
    return im


def gable():
    """Blue-tinted glazing in beige frames: the glass gable of the entrance (photo 3). One pane = 64 px = 3 ft."""
    S = 128
    im = Image.new("RGB", (S, S), (214, 198, 170))
    d = ImageDraw.Draw(im)
    for x in (0, 64):
        for y in (0, 64):
            for k in range(0, 56):
                t = k / 55
                d.line([(x + 4, y + 4 + k), (x + 59, y + 4 + k)], fill=(int(36 + 60 * t), int(64 + 56 * t), int(104 + 44 * t)))
            d.line([(x + 8, y + 52), (x + 52, y + 8)], fill=(120, 150, 184), width=3)
    return noise(im, 3)


def cwood():
    """Dark red-brown cabinet wood of the cage counter (photo 1, back wall)."""
    S = 128
    im = Image.new("RGB", (S, S), (92, 44, 30))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):
        d.rectangle([x + 3, 3, x + 28, S - 4], outline=(60, 28, 18), width=2)
        d.rectangle([x + 8, 8, x + 23, S - 9], outline=(116, 60, 40), width=1)
    return noise(im, 5)


def plate1001():
    im = Image.new("RGB", (128, 32), (226, 214, 188))
    d = ImageDraw.Draw(im)
    d.text((64, 17), "1001", font=font(BLACK, 26), fill=(40, 30, 24), anchor="mm")
    return im


def build():
    t = {"gw_icarpet": carpet(), "gw_istone": istone(), "gw_itile": itile(), "gw_ceil": ceil(), "gw_beam": beam(), "gw_leather": leather(),
         "gw_felt": felt(), "gw_feltv": felt(True), "gw_tv1": tv_scoreboard(), "gw_tv2": tv_sport(), "gw_tv3": tv_poker(), "gw_tv4": tv_news(),
         "gw_door": door(), "gw_shutter": shutter(), "gw_frame1": frame(64, 96, 1), "gw_frame2": frame(128, 64, 2),
         "gw_exit": exit_sign(), "gw_lightp": lightp(), "gw_chipr": chip((190, 36, 40)), "gw_chipb": chip((40, 70, 170)),
         "gw_chipg": chip((40, 140, 70)), "gw_chipk": chip((30, 30, 34)), "gw_flag": flag(), "gw_flowers": flowers(), "gw_cone": cone(),
         "gw_gable": gable(), "gw_cwood": cwood(), "gw_1001": plate1001()}
    for n in range(1, 25):
        t["gw_n%02d" % n] = number(n)
    return t


def main():
    t = build()
    os.makedirs(os.path.dirname(WAD), exist_ok=True)
    small = {}
    for n, im in t.items():
        im.save(os.path.join(TEX, n + ".png"))
        if n in GLOW:
            im.save(os.path.join(TEX, n + "_glow.png"))
        small[n] = im.resize((max(16, -(-im.width // 4 // 16) * 16), max(16, -(-im.height // 4 // 16) * 16)), Image.LANCZOS)
    write_wad(WAD, small)
    print("wrote", WAD, len(small), "textures")


if __name__ == "__main__":
    main()
