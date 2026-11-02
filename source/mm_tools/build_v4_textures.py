"""Textures for make_bklan_v4.py (bklan3: the owner's review of bklan2, 2026-10-31 16:03). bk4_* only, written to
BakersfieldQuake/textures (full size) and out/maps/bklan4.wad (quarter size, for qbsp's names and sizes).
    bk4_win     a plain dark shop window (replaces bk_darkwin, whose photo showed parked cars: "remove these car pictures")
    bk4_quilt   the bedspread, bk4_pillow, bk4_rug, bk4_poster (B-LAN 2001), bk4_carpet (bedroom floor)
usage: python build_v4_textures.py"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402

TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
WAD4 = os.path.join(HERE, "out", "maps", "bklan4.wad")
HI = 4
DIM = 0.92           # balanced albedo for standard DarkPlaces overbright lighting
F = "C:/Windows/Fonts/"


def d(c):
    return tuple(int(v * DIM) for v in c)


def window():
    """512 x 256: dark tinted glass in an aluminium frame, a soft sky reflection, a centre mullion. No pictures."""
    im = Image.new("RGB", (512, 256))
    px = im.load()
    for y in range(256):
        for x in range(512):
            k = y / 255
            sky = 0.22 * (1 - k) ** 2                      # brighter at the top: the sky in the glass
            streak = 0.06 if (x + y * 0.6) % 170 < 26 else 0.0   # a diagonal glint
            v = 0.10 + sky + streak
            px[x, y] = d((int(255 * v * 0.85), int(255 * v * 0.95), int(255 * v * 1.15)))
    dr = ImageDraw.Draw(im)
    al = d((150, 152, 150))
    dr.rectangle([0, 0, 511, 255], outline=al, width=10)
    dr.rectangle([251, 0, 260, 255], fill=al)
    return im.filter(ImageFilter.GaussianBlur(0.6))


def quilt():
    """256 x 256 patchwork bedspread, navy and red with white stitching."""
    im = Image.new("RGB", (256, 256))
    dr = ImageDraw.Draw(im)
    cols = [(30, 50, 120), (150, 30, 40), (40, 90, 160), (200, 180, 140)]
    r = random.Random(3)
    for i in range(4):
        for j in range(4):
            c = cols[(i + j * 2 + r.randint(0, 1)) % 4]
            dr.rectangle([i * 64, j * 64, i * 64 + 63, j * 64 + 63], fill=d(c))
            dr.rectangle([i * 64 + 2, j * 64 + 2, i * 64 + 61, j * 64 + 61], outline=d((235, 235, 230)), width=1)
    return im


def plain(c, size=(64, 64), amt=6, seed=1):
    im = Image.new("RGB", size, d(c))
    px = im.load()
    r = random.Random(seed)
    for y in range(size[1]):
        for x in range(size[0]):
            n = r.randint(-amt, amt)
            px[x, y] = tuple(max(0, min(255, v + n)) for v in px[x, y])
    return im


def rug():
    im = Image.new("RGB", (256, 128), d((120, 30, 40)))
    dr = ImageDraw.Draw(im)
    dr.rectangle([8, 8, 247, 119], outline=d((220, 190, 120)), width=6)
    dr.rectangle([24, 24, 231, 103], outline=d((40, 60, 110)), width=4)
    for k in range(5):
        x = 60 + k * 34
        dr.polygon([(x, 64 - 16), (x + 14, 64), (x, 64 + 16), (x - 14, 64)], fill=d((220, 190, 120)))
    return im


def poster():
    """128 x 192: a B-LAN 2001 LAN party poster for the bedroom wall."""
    im = Image.new("RGB", (128, 192), d((10, 14, 40)))
    dr = ImageDraw.Draw(im)
    for k in range(40):
        y = 192 - k * 5
        dr.line([(0, y), (128, y - 30)], fill=d((20 + k * 2, 30, 90 + k * 3)))
    f1 = ImageFont.truetype(F + "arialbd.ttf", 30)
    f2 = ImageFont.truetype(F + "arialbd.ttf", 13)
    dr.text((64, 50), "B-LAN", font=f1, fill=d((255, 220, 60)), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    dr.text((64, 84), "2001", font=f1, fill=d((255, 255, 255)), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    dr.text((64, 130), "QUAKE  CS  UT", font=f2, fill=d((120, 220, 255)), anchor="mm")
    dr.text((64, 150), "UNIT 130A", font=f2, fill=d((255, 255, 255)), anchor="mm")
    dr.text((64, 168), "118 E 21st ST", font=f2, fill=d((255, 255, 255)), anchor="mm")
    dr.rectangle([0, 0, 127, 191], outline=d((230, 230, 230)), width=3)
    return im


def launch_pad():
    """256 x 256 top of a long-range launch pad: violet ring, magenta core, a big double chevron. (Glow map beside it.)"""
    S = 256
    ring, core = (210, 70, 255), (46, 14, 60)
    im = Image.new("RGB", (S, S), (24, 20, 30))
    g = Image.new("RGB", (S, S), (0, 0, 0))
    d, dg = ImageDraw.Draw(im), ImageDraw.Draw(g)
    for dd in (d, dg):
        dd.ellipse([6, 6, S - 7, S - 7], outline=ring, width=18)
        dd.ellipse([44, 44, S - 45, S - 45], outline=(255, 120, 255), width=7)
    d.ellipse([56, 56, S - 57, S - 57], fill=core)
    for dd in (d, dg):
        for k in range(3):
            y = 158 - k * 36
            dd.line([(80, y + 26), (128, y - 16), (176, y + 26)], fill=(255, 150, 255), width=17, joint="curve")
    return im, g


def launch_sign(text, col):
    """1024 x 320 destination board for a launch pad (as the teleport boards of build_v3_textures.py)."""
    import build_v3_textures as b3
    return b3.dim(b3.sign_board((1024, 320), col, (210, 70, 255), [("LAUNCH PAD", (0.08, 0.38), "arialbd.ttf", (255, 210, 255)),
                                                                   (text, (0.44, 0.9), "arialbd.ttf", (255, 255, 255))]), 0.9)


def main():
    import build_v3_textures as b3
    pad, pad_glow = launch_pad()
    t = {"bk4_win": window(), "bk4_quilt": quilt(), "bk4_pillow": plain((235, 232, 220), seed=2),
         "bk4_rug": rug(), "bk4_poster": poster(), "bk4_carpet": plain((95, 85, 70), (128, 128), 10, 5),
         "bk4_sheet": plain((210, 215, 230), seed=4),
         "bk4_launch": b3.dim(b3.noise(pad, 5), 0.9),
         "bk4_lsign1": launch_sign("TO THE BAKERSFIELD SIGN", (16, 38, 92)),
         "bk4_lsign2": launch_sign("TO MANNING ST", (14, 98, 52)),
         "bk4_lsign3": launch_sign("TO THE PARK", (30, 100, 40)),
         "bk4_lsign4": launch_sign("TO LARRY'S WAREHOUSE", (170, 60, 20))}
    pad_glow.save(os.path.join(TEX, "bk4_launch_glow.png"))
    os.makedirs(os.path.dirname(WAD4), exist_ok=True)
    small = {}
    for nm, im in t.items():
        im.save(os.path.join(TEX, nm + ".png"))
        small[nm] = im.resize((max(16, -(-im.width // HI // 16) * 16), max(16, -(-im.height // HI // 16) * 16)), Image.LANCZOS)
    # the classic Quake teleporter field: id's own "*teleport" (read from DM6, kept in star_teleport.png). The engine warps any
    # "*" texture; the wad only holds the name and size (no PNG: "*" is not allowed in a file name)
    small["*teleport"] = Image.open(os.path.join(HERE, "star_teleport.png")).convert("RGB")
    write_wad(WAD4, small)
    print("wrote", WAD4, len(small), "textures")


if __name__ == "__main__":
    main()
