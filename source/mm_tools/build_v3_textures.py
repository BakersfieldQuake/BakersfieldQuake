"""Textures for make_bklan_v3.py (the 2026-10-31 09:36 feedback video): bk3_* only, so the shared bklan textures and
bklan.wad are never rewritten. Writes
    BakersfieldQuake/textures/bk3_*.png and {bk3_*.png    (full size; DarkPlaces draws these)
    out/maps/bklan3.wad                                   (quarter size, so qbsp knows the names and sizes)
Tree sprites are Kenney's "Foliage Pack" (CC0, https://opengameart.org/content/foliage-pack-100x), unpacked in
ref_sources/tree_sprites/pack. Signs are drawn here. usage: python build_v3_textures.py"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402

TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
WAD3 = os.path.join(HERE, "out", "maps", "bklan3.wad")
SPR = os.path.join(HERE, "ref_sources", "tree_sprites", "pack", "PNG", "Default size")
HI = 4
DIM = 0.92           # balanced albedo for standard DarkPlaces overbright lighting


def font(name, px):
    for n in (name, "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except OSError:
            pass
    return ImageFont.load_default()


def fit_text(d, text, box, fnt_name, fill, stroke=None, pad=0.0, anchor="mm", maxpx=400):
    """Largest font that fits `text` in box (x0, y0, x1, y1); drawn centred."""
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) * (1 - pad), (y1 - y0) * (1 - pad)
    px = maxpx
    while px > 6:
        f = font(fnt_name, px)
        b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= w and b[3] - b[1] <= h:
            break
        px -= 2
    f = font(fnt_name, px)
    b = d.textbbox((0, 0), text, font=f)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pos = (cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)
    d.text(pos, text, font=f, fill=fill, stroke_width=stroke[0] if stroke else 0, stroke_fill=stroke[1] if stroke else None)
    return px


def dim(im, k=DIM):
    a = im.getchannel("A") if im.mode == "RGBA" else None
    out = ImageEnhance.Brightness(im.convert("RGB")).enhance(k)
    if a:
        out.putalpha(a)
    return out


def noise(im, amt=6, seed=1):
    import random
    r = random.Random(seed)
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            n = r.randint(-amt, amt)
            p = px[x, y]
            px[x, y] = tuple(max(0, min(255, c + n)) for c in p[:3])
    return im


def sign_board(size, bg, border, lines, rim=(240, 240, 235)):
    im = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(im)
    b = max(6, size[1] // 24)
    d.rectangle([0, 0, size[0] - 1, size[1] - 1], outline=border, width=b)
    d.rectangle([b * 2, b * 2, size[0] - 1 - b * 2, size[1] - 1 - b * 2], outline=rim, width=max(2, b // 3))
    for text, frac, fnt_name, fill in lines:
        y0, y1 = frac
        fit_text(d, text, (b * 4, size[1] * y0, size[0] - b * 4, size[1] * y1), fnt_name, fill, pad=0.04)
    return im


def build():
    t, glow = {}, {}
    # --- Larry's Warehouse: the long wall sign (24 x 4 ft) and the roadside pylon (6 x 9 ft)
    t["bk3_larry"] = dim(sign_board((1536, 256), (16, 38, 92), (235, 185, 40),
                                    [("LARRY'S WAREHOUSE", (0.06, 0.72), "ariblk.ttf", (255, 255, 255)),
                                     ("UNIT 130A  -  118 E 21st ST  -  LAN PARTY", (0.74, 0.94), "arialbd.ttf", (245, 200, 60))]), 0.9)
    pyl = sign_board((512, 768), (16, 38, 92), (235, 185, 40),
                     [("LARRY'S", (0.05, 0.25), "ariblk.ttf", (255, 255, 255)),
                      ("WAREHOUSE", (0.26, 0.42), "ariblk.ttf", (255, 255, 255)),
                      ("UNIT 130A", (0.47, 0.58), "arialbd.ttf", (245, 200, 60)),
                      ("LAN PARTY", (0.62, 0.76), "ariblk.ttf", (245, 200, 60)),
                      ("118 E 21st St", (0.80, 0.92), "arialbd.ttf", (230, 230, 230))])
    t["bk3_pylon"] = dim(pyl, 0.9)
    # --- Manning St: green blade signs and the entry board
    t["bk3_manning"] = dim(sign_board((1024, 192), (14, 98, 52), (240, 240, 240), [("MANNING ST", (0.08, 0.88), "arialbd.ttf", (255, 255, 255))]), 0.9)
    t["bk3_manboard"] = dim(sign_board((1536, 384), (14, 98, 52), (240, 240, 240),
                                       [("MANNING ST", (0.06, 0.64), "ariblk.ttf", (255, 255, 255)),
                                        ("1600 BLOCK  -  1608 MANNING ST AHEAD", (0.68, 0.92), "arialbd.ttf", (235, 235, 150))]), 0.9)
    plaque = sign_board((384, 192), (30, 30, 34), (200, 200, 200), [("1608", (0.1, 0.9), "ariblk.ttf", (240, 240, 240))])
    t["bk3_1608"] = dim(plaque, 0.9)
    # --- teleporter and jump pad tops, plus glow maps
    for nm, ring, core in (("bk3_tp", (60, 230, 255), (10, 40, 60)), ("bk3_jump", (255, 210, 40), (40, 34, 10))):
        S = 256
        im = Image.new("RGB", (S, S), (24, 26, 30))
        g = Image.new("RGB", (S, S), (0, 0, 0))
        d, dg = ImageDraw.Draw(im), ImageDraw.Draw(g)
        for dd, col in ((d, ring), (dg, ring)):
            dd.ellipse([10, 10, S - 11, S - 11], outline=col, width=14)
            dd.ellipse([46, 46, S - 47, S - 47], outline=col, width=6)
        d.ellipse([60, 60, S - 61, S - 61], fill=core)
        if nm == "bk3_jump":
            for dd, col in ((d, ring), (dg, ring)):             # three chevrons: this way up
                for k in range(3):
                    y = 150 - k * 34
                    dd.line([(88, y + 22), (128, y - 14), (168, y + 22)], fill=col, width=14, joint="curve")
        else:
            dg.ellipse([90, 90, S - 91, S - 91], fill=tuple(c // 2 for c in ring))
            d.ellipse([90, 90, S - 91, S - 91], fill=tuple(c // 2 for c in ring))
        t[nm] = dim(noise(im, 5), 0.9)
        glow[nm] = g
    # --- teleporter destination boards
    for nm, text, col in (("bk3_tpsign1", "TELEPORT: LARRY'S WAREHOUSE", (170, 60, 20)),
                          ("bk3_tpsign2", "TELEPORT: BAKERSFIELD SIGN", (16, 38, 92)),
                          ("bk3_tpsign3", "TELEPORT: MANNING ST", (14, 98, 52))):
        t[nm] = dim(sign_board((1024, 320), col, (60, 230, 255), [(text, (0.12, 0.88), "arialbd.ttf", (255, 255, 255))]), 0.9)
    # --- perimeter wall: tan precast sound-wall panels
    S = 256
    wall = Image.new("RGB", (S, S), (176, 166, 148))
    d = ImageDraw.Draw(wall)
    for k in range(0, S, 64):
        d.line([(k, 0), (k, S)], fill=(128, 120, 106), width=3)
    for k in range(0, S, 128):
        d.line([(0, k), (S, k)], fill=(150, 142, 126), width=2)
    t["bk3_sw"] = dim(noise(wall.filter(ImageFilter.GaussianBlur(0.4)), 7), 0.85)
    # --- licence plate
    pl = Image.new("RGB", (192, 96), (236, 236, 228))
    d = ImageDraw.Draw(pl)
    d.rectangle([0, 0, 191, 95], outline=(30, 50, 120), width=5)
    fit_text(d, "CALIFORNIA", (10, 6, 182, 30), "arialbd.ttf", (30, 50, 120))
    fit_text(d, "7XQL308", (10, 30, 182, 88), "arialbd.ttf", (20, 20, 90))
    t["bk3_plate"] = dim(pl, 0.9)
    # --- tree sprites (alpha): Kenney foliage pack, CC0. {name = see-through in qbsp, alpha in DarkPlaces
    spr = {"{bk3_tree1": "006", "{bk3_tree2": "007", "{bk3_tree3": "009", "{bk3_tree4": "010", "{bk3_cyp": "011",
           "{bk3_pine": "004", "{bk3_bush1": "049", "{bk3_bush2": "051"}
    for nm, num in spr.items():
        im = Image.open(os.path.join(SPR, "foliagePack_%s.png" % num)).convert("RGBA")
        bb = im.getbbox()
        im = im.crop(bb)
        s = 2.0                                           # a little more resolution than the 100 px originals
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        al = im.getchannel("A").point(lambda v: 255 if v > 110 else 0)
        rgb = ImageEnhance.Color(ImageEnhance.Brightness(im.convert("RGB")).enhance(0.8)).enhance(0.8)   # less cartoon-bright
        rgb.putalpha(al)
        t[nm] = rgb
    return t, glow


def main():
    t, glow = build()
    os.makedirs(os.path.dirname(WAD3), exist_ok=True)
    small = {}
    for nm, im in t.items():
        im.save(os.path.join(TEX, nm + ".png"))
        small[nm] = im.resize((max(16, -(-im.width // HI // 16) * 16), max(16, -(-im.height // HI // 16) * 16)), Image.LANCZOS)
        if im.mode == "RGBA":
            small[nm] = small[nm].convert("RGBA")
    for nm, im in glow.items():
        im.save(os.path.join(TEX, nm + "_glow.png"))
    write_wad(WAD3, small)
    print("wrote", WAD3, len(small), "textures")
    return t


if __name__ == "__main__":
    main()
