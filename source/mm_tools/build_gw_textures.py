"""Textures for make_goldenwest.py (Golden West Casino, 1001 S Union Ave): gw_*.png in BakersfieldQuake/textures and the quarter-size
palette copies in out/maps/goldenwest.wad. Colours and layout are matched to the Street View photos of May 2024 in
ref_sources/golden_west_gallery (043.jpg, 036.jpg, 042.jpg ...) and the zoom-20 aerial (008.jpg). usage: python build_gw_textures.py"""
import hashlib
import os
import pickle
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402

TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
WAD = os.path.join(HERE, "out", "maps", "goldenwest.wad")
DIM = 0.78
rnd = random.Random(5)


def font(names, px):
    for n in names:
        try:
            return ImageFont.truetype(n, px)
        except OSError:
            pass
    return ImageFont.load_default()


def noise(im, amt=6):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            n = rnd.randint(-amt, amt)
            p = px[x, y]
            px[x, y] = tuple(max(0, min(255, c + n)) for c in p[:3])
    return im


def dim(im, k=DIM):
    return ImageEnhance.Brightness(im.convert("RGB")).enhance(k)


def tile_roof():
    """Terracotta barrel tile: courses 8 in apart, each with a darker lower lip (aerial 008: red-brown, 150/80/70)."""
    S = 256
    im = Image.new("RGB", (S, S), (168, 86, 70))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 16):
        d.rectangle([0, y + 11, S, y + 15], fill=(120, 58, 48))
        d.line([(0, y), (S, y)], fill=(188, 104, 86), width=1)
    for x in range(0, S, 32):
        d.line([(x + (x // 32 % 2) * 16, 0), (x + (x // 32 % 2) * 16, S)], fill=(150, 74, 60), width=1)
    return dim(noise(im, 7), 0.8).filter(ImageFilter.GaussianBlur(0.35))


def stucco():
    im = Image.new("RGB", (256, 256), (232, 224, 204))
    return dim(noise(im, 7), 1.0)


def stone():
    """White rubble-stone cladding with grey mortar (photos 035/036: the casino walls, the frontage wall, the gate pillars)."""
    S = 256
    im = Image.new("RGB", (S, S), (150, 146, 138))
    d = ImageDraw.Draw(im)
    y = 0
    while y < S:
        h = rnd.randint(20, 34)
        x = -rnd.randint(0, 30)
        while x < S:
            w = rnd.randint(26, 62)
            c = rnd.randint(-12, 14)
            d.rounded_rectangle([x + 2, y + 2, x + w - 2, y + h - 2], radius=5, fill=(226 + c, 222 + c, 210 + c))
            x += w
        y += h
    return dim(noise(im, 6), 1.5)


def wood():
    """Brown vertical timber siding of the steep gable (photo 036)."""
    S = 128
    im = Image.new("RGB", (S, S), (96, 64, 46))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 12):
        d.line([(x, 0), (x, S)], fill=(62, 40, 28), width=2)
        c = rnd.randint(-8, 8)
        d.rectangle([x + 3, 0, x + 9, S], fill=(100 + c, 68 + c, 48 + c))
    return dim(noise(im, 5), 0.95)


def road():
    """Light grey concrete paving of Union Ave: panel joints every 15 ft and the crack pattern of photo 036."""
    S = 256
    im = Image.new("RGB", (S, S), (170, 168, 160))
    d = ImageDraw.Draw(im)
    for k in range(0, S, 128):
        d.line([(0, k), (S, k)], fill=(120, 118, 112), width=2)
    for _ in range(26):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        for _ in range(rnd.randint(3, 8)):
            nx, ny = x + rnd.randint(-22, 22), y + rnd.randint(-22, 22)
            d.line([(x, y), (nx, ny)], fill=(110, 108, 102), width=1)
            x, y = nx, ny
    return dim(noise(im, 6).filter(ImageFilter.GaussianBlur(0.4)), 0.62)


def lot():
    """Faded grey asphalt of the casino lots (zoom-20 aerial: blue-grey, oil patches)."""
    S = 256
    im = Image.new("RGB", (S, S), (98, 100, 108))
    d = ImageDraw.Draw(im)
    for _ in range(140):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        c = rnd.randint(-14, 10)
        d.ellipse([x, y, x + rnd.randint(8, 30), y + rnd.randint(5, 18)], fill=(98 + c, 100 + c, 108 + c))
    return dim(noise(im, 6).filter(ImageFilter.GaussianBlur(0.6)), 1.0)


def brick():
    """The pink-red pavers of the median and the bike lane (aerial: 210/110/110)."""
    S = 128
    im = Image.new("RGB", (S, S), (176, 98, 92))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 16):
        for x in range(0, S, 32):
            ox = (y // 16 % 2) * 16
            c = rnd.randint(-10, 10)
            d.rectangle([x + ox + 1, y + 1, x + ox + 30, y + 14], fill=(176 + c, 98 + c, 92 + c))
    return dim(noise(im, 5), 0.85)


def dirt():
    S = 256
    im = Image.new("RGB", (S, S), (160, 140, 104))
    d = ImageDraw.Draw(im)
    for _ in range(900):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        c = rnd.randint(-22, 14)
        d.ellipse([x, y, x + rnd.randint(2, 7), y + rnd.randint(2, 5)], fill=(150 + c, 128 + c, 92 + c))
    return dim(noise(im, 6), 0.8).filter(ImageFilter.GaussianBlur(0.5))


def trim():
    im = Image.new("RGB", (64, 64), (92, 62, 44))
    return dim(noise(im, 5), 0.85)


def sign_pylon():
    """The purple pylon (photo 043 / 036): rounded cap with gold script 'Golden West' over 'CASINO', a blue LED board
    ('TOURNAMENT' is the only wording that can be read), then the purple post. 4 x 12 ft face, texture 256 x 768."""
    W, H = 256, 768
    im = Image.new("RGB", (W, H), (96, 52, 128))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, W - 5, 300], radius=60, fill=(104, 58, 136), outline=(70, 36, 96), width=5)
    script = font(["segoesc.ttf", "pala.ttf", "georgiaz.ttf", "ariali.ttf"], 66)
    d.text((W / 2, 96), "Golden West", font=script, fill=(236, 188, 60), anchor="mm", stroke_width=2, stroke_fill=(120, 70, 20))
    d.text((W / 2, 190), "CASINO", font=font(["ariblk.ttf", "arialbd.ttf"], 62), fill=(236, 188, 60), anchor="mm", stroke_width=2, stroke_fill=(70, 36, 96))
    d.rectangle([14, 318, W - 15, 470], fill=(12, 18, 60), outline=(236, 188, 60), width=4)
    d.text((W / 2, 354), "MONDAY", font=font(["arialbd.ttf"], 30), fill=(120, 210, 255), anchor="mm")
    d.text((W / 2, 394), "DRY ICE", font=font(["arialbd.ttf"], 30), fill=(120, 210, 255), anchor="mm")
    d.text((W / 2, 436), "TOURNAMENT", font=font(["arialbd.ttf"], 30), fill=(250, 250, 250), anchor="mm")
    d.rectangle([60, 480, W - 61, H], fill=(86, 44, 116))
    return dim(im, 0.92)


def green_iron():
    """The dark-green wrought-iron fence of the frontage (photo 043), from the shared black {iron fence texture (alpha kept)."""
    im = Image.open(os.path.join(TEX, "{iron.png")).convert("RGBA")
    r, g, b, a = im.split()
    lum = im.convert("L")
    col = Image.merge("RGB", (lum.point(lambda v: 96 + v * 0.1), lum.point(lambda v: 128 + v * 0.2), lum.point(lambda v: 112 + v * 0.1)))
    col.putalpha(a)
    return col


def street_signs():
    """Green street-name blades (white bold lettering, white border) for every named cross street of the OSM route; gs_<md5 of the name>,
    the same naming as sign_tex() in gw_route.py."""
    cache = os.path.join(HERE, "out", "osm_route.pkl")
    if not os.path.exists(cache):
        return {}
    _, ways = pickle.load(open(cache, "rb"))
    names = sorted({t.get("name") for _, t, _ in ways if t.get("highway") in ("primary", "secondary", "tertiary", "residential", "unclassified", "trunk",
                                                                              "living_street") and t.get("name") and "Union" not in t.get("name")})
    out = {}
    for nm in names:
        im = Image.new("RGB", (256, 64), (20, 110, 64))
        d = ImageDraw.Draw(im)
        d.rectangle([2, 2, 253, 61], outline=(235, 235, 225), width=3)
        px = 40
        while px > 12:
            f = font(["arialbd.ttf", "DejaVuSans-Bold.ttf"], px)
            if d.textlength(nm, font=f) <= 236:
                break
            px -= 2
        d.text((128, 32), nm, font=f, fill=(244, 244, 236), anchor="mm")
        out["gs_" + hashlib.md5(nm.encode()).hexdigest()[:10]] = dim(im, 0.95)
    return out


def landmark_textures():
    """gl_<id>: pole-sign / billboard faces of the Union Ave landmarks (gw_landmark_data.SIGNS), gw_w_<colour>: stucco in the colours read off the photos."""
    ns = {}
    exec(compile(open(os.path.join(HERE, "gw_landmark_data.py"), encoding="utf-8").read(), "gw_landmark_data.py", "exec"), ns)
    out = {}
    for sid, (bg, border, lines) in ns["SIGNS"].items():
        im = Image.new("RGB", (256, 192), bg)
        d = ImageDraw.Draw(im)
        d.rectangle([3, 3, 252, 188], outline=border, width=6)
        n = len(lines)
        for i, (txt, col) in enumerate(lines):
            if not txt:
                continue
            cy = 192 * (i + 0.5) / n
            px = 70
            while px > 10:
                f = font(["arialbd.ttf", "DejaVuSans-Bold.ttf"], px)
                if d.textlength(txt, font=f) <= 214 and px <= 192 / n * 0.62:
                    break
                px -= 2
            d.text((128, cy), txt, font=f, fill=col, anchor="mm")
        out["gl_" + sid] = dim(noise(im, 3), 0.95)
    for nm, col in ns["TINT_COLORS"].items():
        out["gw_w_" + nm] = dim(noise(Image.new("RGB", (256, 256), col), 7), 0.9)
    return out


def build():
    t = {"{gw_iron": green_iron(), "gw_tile": tile_roof(), "gw_stucco": stucco(), "gw_stone": stone(), "gw_brick": brick(), "gw_dirt": dirt(),
         "gw_trim": trim(), "gw_pylon": sign_pylon(), "gw_wood": wood(), "gw_road": road(), "gw_lot": lot()}
    t.update(street_signs())
    t.update(landmark_textures())
    return t


def main():
    t = build()
    os.makedirs(os.path.dirname(WAD), exist_ok=True)
    small = {}
    for n, im in t.items():
        im.save(os.path.join(TEX, n + ".png"))
        small[n] = im.resize((max(16, -(-im.width // 4 // 16) * 16), max(16, -(-im.height // 4 // 16) * 16)), Image.LANCZOS)
        if im.mode == "RGBA":
            small[n] = small[n].convert("RGBA")
    write_wad(WAD, small)
    print("wrote", WAD, len(small), "textures")


if __name__ == "__main__":
    main()
