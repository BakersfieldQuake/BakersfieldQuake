"""Builds the textures for bklan (the 2001 B-LAN warehouse, unit 130A off E 21st St, Bakersfield) from frames of
bklan.wmv. Photo surfaces are cut from the 320x240 video frames, made tileable and darkened (the mod runs
r_hdr_scenebrightness 2.5); small props use flat colours sampled from the footage.
Writes  out/maps/bklan.wad                    (64-128 px palette versions, so qbsp knows names and sizes)
        BakersfieldQuake/textures/<name>.png  (full-size versions DarkPlaces draws instead, plus _glow masks)
Street-side materials (front facade, road, LMC's corrugated wall, the breeze-block wall across the street, the road-end
backdrops) come from the user's Street View gallery of 118 E 21st St (larry-warehouse-gallery-self-contained*.html,
images unpacked to a folder).
Run: python build_bklan_textures.py <frames dir> <gallery dir>
     frames dir = ffmpeg -i bklan.wmv -vf fps=1 %05d.jpg (file number = second + 1)"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wad2 import write_wad  # noqa: E402

FRAMES = sys.argv[1]
GALLERY = sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
WAD_OUT = os.path.join(HERE, "out", "maps", "bklan.wad")
TEX_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
GAIN = 0.90          # balanced albedo for standard DarkPlaces overbright lighting (matches DM3 / goldenwest)
HI = 4               # full-size PNGs are HI x the WAD size

random.seed(2001)


def frame(sec):
    return Image.open(os.path.join(FRAMES, "%05d.jpg" % (sec + 1))).convert("RGB")


def crop(sec, box):
    return frame(sec).crop(box)


def gal(name):
    for f in os.listdir(GALLERY):
        if f.startswith(name):
            return Image.open(os.path.join(GALLERY, f)).convert("RGB")
    raise IOError(name)


def gphoto(name, box, size, tile=False, gain=GAIN, sat=1.18):
    """Like photo(), from a Street View picture."""
    im = gal(name).crop(box).resize((size[0] * HI, size[1] * HI), Image.LANCZOS)
    if tile:
        im = seamless(im)
    im = ImageEnhance.Color(im).enhance(sat)
    return ImageEnhance.Brightness(im).enhance(gain)


def gquad(name, corners, size, gain=GAIN):
    """Perspective-corrected crop from a Street View picture: corners TL, TR, BR, BL in pixels."""
    w, h = size[0] * HI, size[1] * HI
    (a, b), (c, d), (e, f), (g, hh) = corners
    im = gal(name).transform((w, h), Image.QUAD, (a, b, g, hh, e, f, c, d), Image.BICUBIC)
    return ImageEnhance.Brightness(im).enhance(gain)


def keyed(im, size, gain=GAIN):
    """Backdrop card: bright, grey pixels (the overcast sky) become see-through, filled down from the top so light walls stay."""
    im = im.resize((size[0] * HI, size[1] * HI), Image.LANCZOS)
    w, h = im.size
    px = im.load()
    a = Image.new("L", (w, h), 255)
    ap = a.load()
    for x in range(w):
        for y in range(h):
            r, g, b = px[x, y]
            if min(r, g, b) > 150 and max(r, g, b) - min(r, g, b) < 40:
                ap[x, y] = 0
            else:
                break
    im = ImageEnhance.Brightness(im).enhance(gain)
    im.putalpha(a)
    return im


def seamless(im):
    """Wraps the edges: cross-fade with a copy shifted half a tile sideways (seam hidden in the middle), then the same
    up-down. Each pass only fades across its own axis, so neither copy's seam ever shows."""
    w, h = im.size
    mx = Image.linear_gradient("L").rotate(90, expand=True).resize((w, h))      # 0..255 left to right
    mx = mx.point(lambda v: int(255 * min(1, abs(v - 127.5) / 127.5) ** 2))       # 255 at the side edges, 0 mid
    my = mx.rotate(90).resize((w, h))
    im = Image.composite(_roll(im, w // 2, 0), im, mx)
    return Image.composite(_roll(im, 0, h // 2), im, my)


def _roll(im, dx, dy):
    w, h = im.size
    out = Image.new(im.mode, (w, h))
    for ox in (dx - w, dx):
        for oy in (dy - h, dy):
            out.paste(im, (ox, oy))
    return out


def concrete(size, rgb):
    """Bare slab: sampled colour with big soft stains and fine grain (the daylight floor at 94 s)."""
    w, h = size[0] * HI, size[1] * HI
    stains = Image.effect_noise((w // 32, h // 32), 70).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(10))
    grain = Image.effect_noise((w, h), 30)
    im = Image.new("RGB", (w, h), rgb)
    px, sp, gp = im.load(), stains.load(), grain.load()
    for y in range(h):
        for x in range(w):
            n = (sp[x, y] - 128) * 0.35 + (gp[x, y] - 128) * 0.15
            px[x, y] = tuple(max(0, min(255, int(c + n))) for c in rgb)
    return ImageEnhance.Brightness(seamless(im)).enhance(GAIN)


def photo(sec, box, size, tile=True, gain=GAIN, sat=1.18, blur=0):
    im = crop(sec, box).resize((size[0] * HI, size[1] * HI), Image.LANCZOS)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    im = im.filter(ImageFilter.UnsharpMask(2, 60, 2))
    if tile:
        im = seamless(im)
    im = ImageEnhance.Color(im).enhance(sat)
    return ImageEnhance.Brightness(im).enhance(gain)


def flat(rgb, size, noise=10, gain=GAIN):
    """Flat sampled colour with a little grain so it doesn't look like a dev texture."""
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), rgb)
    px = im.load()
    for y in range(h):
        for x in range(w):
            n = random.randint(-noise, noise)
            px[x, y] = tuple(max(0, min(255, c + n)) for c in rgb)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def sample(sec, box):
    """Mean colour of a frame region."""
    im = crop(sec, box).resize((1, 1), Image.BOX)
    return im.getpixel((0, 0))


def grey(rgb, k):
    """Pulls a colour k of the way to its own grey (video white balance is off)."""
    m = sum(rgb) / 3
    return tuple(int(m * k + c * (1 - k)) for c in rgb)


def wood(size):
    """Folding-table laminate: the tan wood grain of the tables (1916 s)."""
    base = sample(1916, (120, 132, 170, 146))
    w, h = size[0] * HI, size[1] * HI
    im = flat(base, size, 6, 1.0)
    d = ImageDraw.Draw(im)
    for _ in range(90):
        y = random.uniform(0, h)
        c = tuple(max(0, v - random.randint(10, 35)) for v in base)
        pts = [(x, y + 3 * random.random() + 2 * ((x / w) - .5)) for x in range(0, w + 8, 8)]
        d.line(pts, fill=c, width=random.choice((1, 1, 2)))
    return ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(0.7))).enhance(GAIN)


def slats(size, rgb, dark):
    """Roll-up door: horizontal steel slats."""
    w, h = size[0] * HI, size[1] * HI
    im = flat(rgb, size, 5, 1.0)
    d = ImageDraw.Draw(im)
    step = h // 16
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=dark, width=max(2, HI))
        d.line([(0, y + HI * 2), (w, y + HI * 2)], fill=tuple(min(255, c + 25) for c in rgb), width=HI)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def deck(size):
    """Roof deck seen from below: light grey corrugated steel."""
    base = (150, 150, 146)
    w, h = size[0] * HI, size[1] * HI
    im = flat(base, size, 6, 1.0)
    d = ImageDraw.Draw(im)
    step = w // 8
    for x in range(0, w, step):
        d.rectangle([x, 0, x + step // 3, h], fill=(122, 122, 118))
        d.line([(x + step // 3, 0), (x + step // 3, h)], fill=(175, 175, 170), width=HI)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def block(size, rgb):
    """Painted concrete block, 16 x 8 in coursing (8 x 4 texels at 12 units per foot... ~ 16 x 8 units)."""
    w, h = size[0] * HI, size[1] * HI
    im = flat(rgb, size, 7, 1.0)
    d = ImageDraw.Draw(im)
    cw, ch = 16 * HI, 8 * HI
    joint = tuple(max(0, c - 28) for c in rgb)
    for r, y in enumerate(range(0, h, ch)):
        d.line([(0, y), (w, y)], fill=joint, width=HI // 2 + 1)
        off = (cw // 2) * (r % 2)
        for x in range(-off, w, cw):
            d.line([(x, y), (x, y + ch)], fill=joint, width=HI // 2 + 1)
    return ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(0.6))).enhance(GAIN)


def crt_front(size):
    """A CRT from the front: beige bezel round a screen showing the game (screen cut from 122 s)."""
    w, h = size[0] * HI, size[1] * HI
    bez = sample(122, (82, 150, 92, 200))
    im = flat(bez, size, 4, 1.0)
    scr = crop(122, (88, 160, 118, 192)).resize((int(w * .74), int(h * .70)), Image.LANCZOS)
    scr = ImageEnhance.Brightness(scr).enhance(0.8)
    im.paste(scr, (int(w * .13), int(h * .10)))
    d = ImageDraw.Draw(im)
    d.rectangle([w * .4, h * .88, w * .6, h * .92], fill=tuple(c - 40 for c in bez))
    return ImageEnhance.Brightness(im).enhance(GAIN), scr


def crt_glow(size, scr):
    w, h = size[0] * HI, size[1] * HI
    g = Image.new("RGB", (w, h), (0, 0, 0))
    g.paste(ImageEnhance.Brightness(scr).enhance(0.6), (int(w * .13), int(h * .10)))
    return g


def tower(size):
    """Beige mid-tower front: drive bays, power button."""
    base = sample(122, (142, 135, 156, 160))
    w, h = size[0] * HI, size[1] * HI
    im = flat(base, size, 4, 1.0)
    d = ImageDraw.Draw(im)
    for i in range(3):
        y = h * (0.08 + i * 0.09)
        d.rectangle([w * .12, y, w * .88, y + h * .07], outline=tuple(c - 50 for c in base), width=HI)
    d.rectangle([w * .3, h * .42, w * .7, h * .46], fill=tuple(c - 30 for c in base))
    d.ellipse([w * .42, h * .55, w * .58, h * .6], fill=(60, 140, 60))
    for y in range(int(h * .7), int(h * .95), HI * 3):
        d.line([(w * .2, y), (w * .8, y)], fill=tuple(c - 40 for c in base), width=HI)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def tube(size):
    """Fluorescent strip: white diffuser in a metal channel."""
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), (235, 240, 245))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * .15], fill=(150, 150, 150))
    d.rectangle([0, h * .85, w, h], fill=(150, 150, 150))
    return im


def kbd(size):
    base = sample(122, (180, 205, 210, 215))
    w, h = size[0] * HI, size[1] * HI
    im = flat(base, size, 3, 1.0)
    d = ImageDraw.Draw(im)
    for r in range(5):
        for c in range(15):
            x, y = w * (0.03 + c * .064), h * (0.1 + r * .17)
            d.rectangle([x, y, x + w * .05, y + h * .13], fill=tuple(c2 - 25 for c2 in base))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def sky(size):
    """Quake sky: left half the moving cloud layer (black = see-through, left empty), right half the back layer: flat
    Bakersfield overcast, soft grey-white blotches."""
    w, h = size[0] * HI, size[1] * HI
    half = w // 2
    im = Image.new("RGB", (w, h))
    clouds = Image.effect_noise((half // 32, h // 32), 40).resize((half, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(12))
    back = Image.merge("RGB", [clouds.point(lambda v, k=k: int(118 + (v - 128) * 0.5 + k)) for k in (0, 4, 12)])
    im.paste(seamless(back), (half, 0))
    return im


def corrugated(size, rgb, trim=None):
    """Vertical-rib metal siding (LMC Paint Supply's long white wall, blue trim at the top)."""
    w, h = size[0] * HI, size[1] * HI
    im = flat(rgb, size, 3, 1.0)
    d = ImageDraw.Draw(im)
    step = w // 8
    for x in range(0, w, step):
        d.rectangle([x, 0, x + step // 4, h], fill=tuple(max(0, c - 22) for c in rgb))
        d.line([(x + step // 4, 0), (x + step // 4, h)], fill=tuple(min(255, c + 15) for c in rgb), width=HI)
    if trim:
        d.rectangle([0, 0, w, h * .06], fill=trim)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def fence(size, kind):
    """See-through fences: chain-link, black iron bars, the brown breeze-block lattice across the street."""
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kind == "chain":
        c = (150, 152, 150, 255)
        for i in range(-h, w + h, 6 * HI):
            d.line([(i, 0), (i + h, h)], fill=c, width=HI // 2 + 1)
            d.line([(i, h), (i + h, 0)], fill=c, width=HI // 2 + 1)
    elif kind == "iron":
        c = (18, 18, 20, 255)
        for x in range(0, w, 5 * HI):
            d.rectangle([x, 0, x + HI, h], fill=c)
        for y in (2 * HI, h - 6 * HI):
            d.rectangle([0, y, w, y + 2 * HI], fill=c)
    else:   # lattice: 16 in decorative blocks, a pierced quatrefoil in each
        base = gal("sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw180").crop((60, 330, 120, 380)).resize((1, 1), Image.BOX).getpixel((0, 0))
        c = tuple(int(v * 0.9) for v in base) + (255,)
        im.paste(c, (0, 0, w, h))
        cell = w // 4
        for cy in range(0, h, cell):
            for cx in range(0, w, cell):
                m = cell // 6
                d.ellipse([cx + m, cy + m, cx + cell // 2 - 1, cy + cell // 2 - 1], fill=(0, 0, 0, 0))
                d.ellipse([cx + cell // 2 + 1, cy + m, cx + cell - m, cy + cell // 2 - 1], fill=(0, 0, 0, 0))
                d.ellipse([cx + m, cy + cell // 2 + 1, cx + cell // 2 - 1, cy + cell - m], fill=(0, 0, 0, 0))
                d.ellipse([cx + cell // 2 + 1, cy + cell // 2 + 1, cx + cell - m, cy + cell - m], fill=(0, 0, 0, 0))
    r, g, b, a = im.split()
    rgb = ImageEnhance.Brightness(Image.merge("RGB", (r, g, b))).enhance(GAIN)
    rgb.putalpha(a)
    return rgb


def sign(size, text, bg, fg, font_px):
    from PIL import ImageFont
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("arialbd.ttf", font_px * HI)
    except OSError:
        f = ImageFont.load_default()
    box = d.multiline_textbbox((0, 0), text, font=f, align="center")
    d.multiline_text(((w - box[2]) / 2, (h - box[3]) / 2), text, font=f, fill=fg, align="center")
    return ImageEnhance.Brightness(im).enhance(GAIN)


def roof(size):
    """Flat roof: light grey cap sheet, a few patches."""
    im = flat((175, 178, 180), size, 12, 1.0)
    d = ImageDraw.Draw(im)
    w, h = im.size
    for _ in range(6):
        x, y = random.uniform(0, w), random.uniform(0, h)
        d.rectangle([x, y, x + random.uniform(20, 120), y + random.uniform(20, 80)], fill=(160, 163, 165))
    return ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(1))).enhance(GAIN)


def plywood(size):
    base = (170, 135, 90)
    w, h = size[0] * HI, size[1] * HI
    im = flat(base, size, 10, 1.0)
    d = ImageDraw.Draw(im)
    for _ in range(40):
        y = random.uniform(0, h)
        d.line([(0, y), (w, y + random.uniform(-6, 6))], fill=(150, 115, 75), width=HI // 2 + 1)
    d.rectangle([0, 0, w - 1, h - 1], outline=(110, 85, 55), width=HI)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def unitwall(size, _unused=None):
    """Generic industrial unit, one bay = 20 ft wide x 20 ft tall: painted block with a 12 x 12 ft roll-up and a black
    man door (what the units round the lot look like in the tape at 40-42 s)."""
    w, h = size[0] * HI, size[1] * HI
    im = block(size, (196, 194, 186))
    im = ImageEnhance.Brightness(im).enhance(1 / GAIN)
    ft = w / 20
    door = slats((32, 32), (190, 192, 195), (150, 155, 160)).resize((int(12 * ft), int(12 * ft)))
    im.paste(ImageEnhance.Brightness(door).enhance(1 / GAIN), (int(1.5 * ft), int(h - 12 * ft)))
    man = gphoto("sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45.", (286, 346, 329, 431), (16, 32), gain=1.0)
    im.paste(man.resize((int(3 * ft), int(7 * ft))), (int(15.5 * ft), int(h - 7 * ft)))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def shopwall(size):
    """Generic shopfront bay, 20 ft: stucco, a dark window and a door."""
    w, h = size[0] * HI, size[1] * HI
    im = ImageEnhance.Brightness(gphoto("sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45.", (165, 356, 280, 440),
                                        size, tile=True, gain=1.0)).enhance(1.0)
    ft = w / 20
    win = gphoto("sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45.", (438, 346, 497, 389), (32, 16), gain=1.0)
    im.paste(win.resize((int(9 * ft), int(4.5 * ft))), (int(1.5 * ft), int(h - 8 * ft)))
    door = gphoto("sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45.", (286, 346, 329, 431), (16, 32), gain=1.0)
    im.paste(door.resize((int(3.2 * ft), int(7 * ft))), (int(13 * ft), int(h - 7 * ft)))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def motelwall(size):
    """Capri Motel: brown, two floors of windows, 20 ft bay."""
    w, h = size[0] * HI, size[1] * HI
    im = flat((158, 114, 72), size, 8, 1.0)
    d = ImageDraw.Draw(im)
    ft = w / 20
    for fl in (1.5, 11.5):
        d.rectangle([3 * ft, h - (fl + 5) * ft, 9 * ft, h - (fl + 1.5) * ft], fill=(35, 40, 48))
        d.rectangle([13 * ft, h - (fl + 7) * ft, 16 * ft, h - fl * ft], fill=(120, 88, 62))
    d.rectangle([0, h - 10.6 * ft, w, h - 10 * ft], fill=(96, 68, 48))
    return ImageEnhance.Brightness(im).enhance(GAIN)


REF = os.path.join(HERE, "ref_v2")      # frames of 2026-10-30 22-56-37.mp4 (the sign, the Crystal Palace, 1608 Manning St)


def ref(sec):
    return Image.open(os.path.join(REF, "%d.jpg" % sec)).convert("RGB")


def rsample(sec, box):
    return ref(sec).crop(box).resize((1, 1), Image.BOX).getpixel((0, 0))


def rphoto(sec, box, size, tile=False, gain=GAIN, sat=1.18):
    im = ref(sec).crop(box).resize((size[0] * HI, size[1] * HI), Image.LANCZOS)
    if tile:
        im = seamless(im)
    im = ImageEnhance.Color(im).enhance(sat)
    return ImageEnhance.Brightness(im).enhance(gain)


def quad(sec, corners, size, gain=GAIN):
    """Perspective-corrected crop: corners TL, TR, BR, BL in frame pixels."""
    w, h = size[0] * HI, size[1] * HI
    (a, b), (c, d), (e, f), (g, hh) = corners
    im = ref(sec).transform((w, h), Image.QUAD, (a, b, g, hh, e, f, c, d), Image.BICUBIC)
    return ImageEnhance.Brightness(im).enhance(gain)


def sign_band(size):
    """The arch band of the Bakersfield Sign as one picture over the whole tower-centre span (bklan_sign.py): yellow, a
    darker gold edge along the curved top and bottom, BAKERSFIELD in navy with a lighter tube outline, each letter
    stood upright on the curve as on the real sign."""
    import math
    from PIL import ImageFont
    import bklan_sign as BS
    w, h = size[0] * HI, size[1] * HI
    yellow = (248, 194, 36)
    im = Image.new("RGB", (w, h), yellow)
    d = ImageDraw.Draw(im)
    for yy in range(h):
        k = yy / max(1, h - 1)
        row = (min(255, int(254 - 18 * k)), min(255, int(206 - 26 * k)), max(0, int(48 - 20 * k)))
        d.line([(0, yy), (w, yy)], fill=row)
    X = lambda s: (s + BS.HALF) / BS.SPACING * w
    Y = lambda z: (BS.ZMAX - z) / (BS.ZMAX - BS.ZMIN) * h
    edge = (198, 142, 20)
    for fn, off in ((BS.zt, -0.25), (BS.zb, 0.25)):
        pts = [(X(s), Y(fn(s) + off)) for s in [BS.HALF * (k / 50 - 1) for k in range(101)]]
        d.line(pts, fill=edge, width=max(3, h // 40))
    try:
        font = ImageFont.truetype("ariblk.ttf", 400)
    except OSError:
        font = ImageFont.load_default()
    navy, tube = (20, 30, 78), (212, 222, 246)
    px_ft = h / (BS.ZMAX - BS.ZMIN)
    # proportional spacing, as on the sign: each letter's advance plus a fixed gap, scaled to fill LETTER_SPAN
    adv = [font.getbbox(ch)[2] - font.getbbox(ch)[0] for ch in BS.LETTERS]
    gap = 0.45 * font.getbbox("H")[3]
    total = sum(adv) + gap * (len(adv) - 1)
    k = BS.SPACING * BS.LETTER_SPAN / total
    centres, x = [], -BS.SPACING * BS.LETTER_SPAN / 2
    for a in adv:
        centres.append(x + a * k / 2)
        x += (a + gap) * k
    for ch, s in zip(BS.LETTERS, centres):
        zc = (BS.zt(s) + BS.zb(s)) / 2
        slope = (BS.zt(s + 0.5) - BS.zt(s - 0.5))                     # rise per foot along the span
        ang = math.degrees(math.atan(slope))
        box = font.getbbox(ch)
        gw, gh = box[2] - box[0], box[3] - box[1]
        g = Image.new("RGBA", (gw + 60, gh + 60), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.text((30 - box[0], 30 - box[1]), ch, font=font, fill=navy + (255,), stroke_width=14, stroke_fill=tube + (255,))
        sc = BS.LETTER_H * px_ft / gh
        g = g.resize((max(1, int(g.width * sc)), max(1, int(g.height * sc))), Image.LANCZOS)
        g = g.rotate(ang, resample=Image.BICUBIC, expand=True)
        im.paste(g, (int(X(s) - g.width / 2), int(Y(zc) - g.height / 2)), g)
    return im


def cpsign(size):
    """Buck Owens' Crystal Palace pylon face: navy box, the red and blue guitar outline (perspective-corrected from the
    photo at 65 s), the lettering redrawn in a condensed white serif (the photo has the mouse pointer over it)."""
    from PIL import ImageFont
    w, h = size[0] * HI, size[1] * HI
    photo_ = quad(65, ((858, 378), (1291, 428), (1283, 556), (846, 566)), size, gain=1.0)
    px = sorted(photo_.resize((64, 32)).get_flattened_data(), key=sum)
    navy = tuple(sum(c[i] for c in px[150:450]) // 300 for i in range(3))           # the darker pixels: the box colour
    im = Image.new("RGB", (w, h), navy)
    for x0, x1 in ((0.0, 0.47), (0.84, 1.0)):                                     # the guitar logo, left and right
        im.paste(photo_.crop((int(w * x0), int(h * .06), int(w * x1), int(h * .95))), (int(w * x0), int(h * .06)))
    try:
        f = ImageFont.truetype("georgiab.ttf", 200)
    except OSError:
        f = ImageFont.load_default()
    for text, y0, y1 in (("Buck Owens'", 0.12, 0.30), ("Crystal", 0.30, 0.62), ("Palace", 0.62, 0.92)):
        b = f.getbbox(text)
        g = Image.new("RGBA", (b[2] - b[0] + 20, b[3] - b[1] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((10 - b[0], 10 - b[1]), text, font=f, fill=(225, 228, 232, 255))
        th = int(h * (y1 - y0))
        g = g.resize((int(min(w * 0.29, g.width * th / g.height * 0.72)), th), Image.LANCZOS)
        im.paste(g, (int(w * 0.68 - g.width / 2), int(h * y0)), g)
    return ImageEnhance.Brightness(im).enhance(0.8)


def medallion(size):
    """The city seal on the towers: cut from the photo (right tower at 0 s), set in the tower's stucco."""
    w, h = size[0] * HI, size[1] * HI
    cx, cy, r = 1636, 530, 34
    crop = ref(0).crop((cx - r, cy - r, cx + r, cy + r)).resize((w, h), Image.LANCZOS)
    stucco = Image.new("RGB", (w, h), rsample(0, (1600, 490, 1615, 505)))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([1, 1, w - 2, h - 2], fill=255)
    stucco.paste(crop, (0, 0), m.filter(ImageFilter.GaussianBlur(1)))
    return ImageEnhance.Brightness(stucco).enhance(GAIN)


def office(size):
    """The 4-storey office on Sillect Ave beside the sign: cream precast bands, dark blue-grey glass, 14 ft floors
    (one texture repeat = one floor, 20 ft wide)."""
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), (205, 200, 185))
    d = ImageDraw.Draw(im)
    d.rectangle([0, h * 0.18, w, h * 0.70], fill=(52, 64, 78))
    for k in range(5):
        x = k * w / 4
        d.rectangle([x - HI, h * 0.18, x + HI, h * 0.70], fill=(150, 152, 150))
    d.rectangle([0, h * 0.15, w, h * 0.18], fill=(120, 116, 106))
    for y in range(int(h * 0.20), int(h * 0.68), 6):
        d.line([(0, y), (w, y)], fill=(60, 74, 90), width=1)
    return ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(0.6))).enhance(GAIN)


def office_dark(size):
    """Lower two storeys of the 4-storey Sillect Ave office (0 s, 14 s): dark charcoal spandrels and tinted glass."""
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), (58, 62, 68))
    d = ImageDraw.Draw(im)
    d.rectangle([0, h * 0.14, w, h * 0.78], fill=(34, 42, 52))
    for k in range(5):
        x = k * w / 4
        d.rectangle([x - HI, 0, x + HI, h], fill=(74, 78, 84))
    d.rectangle([0, 0, w, h * 0.08], fill=(92, 94, 98))
    return ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(0.6))).enhance(GAIN)


def stop_sign(size):
    """Standard octagonal STOP sign at the north end of the LAN lot (bklan.wmv 1324 s)."""
    from PIL import ImageFont
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), (150, 155, 160))
    d = ImageDraw.Draw(im)
    k = int(w * 0.29)
    oct_pts = [(k, 4), (w - k, 4), (w - 4, k), (w - 4, h - k), (w - k, h - 4), (k, h - 4), (4, h - k), (4, k)]
    d.polygon(oct_pts, fill=(185, 28, 28), outline=(238, 238, 236))
    k2 = int(w * 0.30)
    oct_in = [(k2, 12), (w - k2, 12), (w - 12, k2), (w - 12, h - k2), (w - k2, h - 12), (k2, h - 12), (12, h - k2), (12, k2)]
    d.polygon(oct_in, fill=(185, 28, 28), outline=(238, 238, 236))
    f = ImageFont.truetype("arialbd.ttf", int(h * 0.33))
    b = d.textbbox((0, 0), "STOP", font=f)
    d.text(((w - b[2]) / 2, (h - b[3]) / 2 - b[1] / 2), "STOP", font=f, fill=(242, 242, 240))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def cone_striped(size):
    """Tall orange traffic delineator post with two white reflective bands (bklan.wmv 64, 112, 1334, 2710 s)."""
    w, h = size[0] * HI, size[1] * HI
    im = flat((232, 86, 26), size, 5, 1.0)
    d = ImageDraw.Draw(im)
    for y0, y1 in ((0.16, 0.30), (0.40, 0.54)):
        d.rectangle([0, int(h * y0), w, int(h * y1)], fill=(236, 238, 236))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def dumpster_tex(size):
    """Tan/mustard commercial metal dumpster with horizontal ribs (bklan.wmv 58 s, 1110 s)."""
    base = (194, 166, 98)
    w, h = size[0] * HI, size[1] * HI
    im = flat(base, size, 8, 1.0)
    d = ImageDraw.Draw(im)
    for ry in (0.28, 0.56, 0.82):
        y = int(h * ry)
        d.rectangle([0, y, w, y + HI * 2], fill=(150, 125, 68))
        d.line([(0, y), (w, y)], fill=(215, 190, 122), width=HI)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def brick_tex(size):
    """Red-brown brick coursing for 1608 Manning St's entry walk border (154 s) and Capri Motel planter (118 s)."""
    base = (154, 78, 62)
    w, h = size[0] * HI, size[1] * HI
    im = flat(base, size, 10, 1.0)
    d = ImageDraw.Draw(im)
    cw, ch = 16 * HI, 5 * HI
    mortar = (182, 174, 162)
    for r, y in enumerate(range(0, h, ch)):
        d.line([(0, y), (w, y)], fill=mortar, width=max(2, HI // 2))
        off = (cw // 2) * (r % 2)
        for x in range(-off, w, cw):
            d.line([(x, y), (x, y + ch)], fill=mortar, width=max(2, HI // 2))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def gci_sign(size):
    """GCI equipment rental pylon sign at Union Ave & E 21st St (118 s, sv-west-110e21st-yaw270)."""
    from PIL import ImageFont
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), (232, 232, 228))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, w - 5, h - 5], outline=(38, 76, 152), width=6)
    d.rectangle([8, int(h * 0.76), w - 9, h - 9], fill=(192, 42, 42))
    try:
        f = ImageFont.truetype("ariblk.ttf", int(h * 0.56))
    except OSError:
        f = ImageFont.truetype("arialbd.ttf", int(h * 0.56))
    b = d.textbbox((0, 0), "GCI", font=f)
    d.text(((w - b[2]) / 2, int(h * 0.06)), "GCI", font=f, fill=(76, 80, 88), stroke_width=5, stroke_fill=(192, 42, 42))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def capri_signs(t):
    """Capri Motel NW corner monument wall and yellow marquee (118 s), redrawn without the mouse cursor."""
    from PIL import ImageFont
    stucco = rsample(118, (1660, 445, 1730, 465))
    w, h = 128 * HI, 96 * HI
    im = flat(stucco, (128, 96), 5, 1.0)
    d = ImageDraw.Draw(im)
    try:
        fs = ImageFont.truetype("georgiai.ttf", int(h * 0.30))
    except OSError:
        fs = ImageFont.truetype("ariali.ttf", int(h * 0.30))
    fb = ImageFont.truetype("arialbd.ttf", int(h * 0.19))
    b1 = d.textbbox((0, 0), "Capri", font=fs)
    d.text(((w - b1[2]) / 2, int(h * 0.14)), "Capri", font=fs, fill=(168, 32, 38), stroke_width=3, stroke_fill=(110, 22, 26))
    b2 = d.textbbox((0, 0), "M O T E L", font=fb)
    d.text(((w - b2[2]) / 2, int(h * 0.52)), "M O T E L", font=fb, fill=(168, 32, 38))
    t["bk_capriwall"] = ImageEnhance.Brightness(im).enhance(GAIN)

    w, h = 128 * HI, 48 * HI
    im2 = Image.new("RGB", (w, h), (218, 198, 64))
    d2 = ImageDraw.Draw(im2)
    d2.rectangle([4, 4, w - 5, h - 5], outline=(40, 40, 38), width=5)
    f1 = ImageFont.truetype("georgiai.ttf", int(h * 0.42))
    f2 = ImageFont.truetype("arialbd.ttf", int(h * 0.34))
    b1 = d2.textbbox((0, 0), "Capri", font=f1)
    d2.text(((w - b1[2]) / 2, int(h * 0.04)), "Capri", font=f1, fill=(165, 28, 30))
    b2 = d2.textbbox((0, 0), "MOTEL", font=f2)
    d2.text(((w - b2[2]) / 2, int(h * 0.52)), "MOTEL", font=f2, fill=(28, 30, 32))
    t["bk_capriylw"] = ImageEnhance.Brightness(im2).enhance(GAIN)


def garage(size):
    """1608 Manning St's garage door: white sectional, 16 x 7 ft, the row of small arched windows across the top (the
    photo at 163 s, above the cars), raised panels below."""
    w, h = size[0] * HI, size[1] * HI
    white = rsample(163, (1300, 420, 1340, 460))
    im = Image.new("RGB", (w, h), white)
    d = ImageDraw.Draw(im)
    rows = 4
    for r in range(rows):
        y0, y1 = h * r / rows, h * (r + 1) / rows
        d.line([(0, y1 - 2), (w, y1 - 2)], fill=tuple(c - 45 for c in white), width=3)
        if r == 0:
            top = ref(163).crop((830, 345, 1460, 395)).resize((w, int(y1 - y0)), Image.LANCZOS)
            im.paste(top, (0, int(y0)))
            continue
        for k in range(8):
            x0 = w * k / 8 + 6
            d.rectangle([x0, y0 + 8, x0 + w / 8 - 12, y1 - 10], outline=tuple(c - 30 for c in white), width=3)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def solar(size):
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), (22, 30, 58))
    d = ImageDraw.Draw(im)
    for x in range(0, w, w // 6):
        d.line([(x, 0), (x, h)], fill=(140, 150, 165), width=2)
    for y in range(0, h, h // 10):
        d.line([(0, y), (w, y)], fill=(60, 70, 100), width=1)
    d.rectangle([0, 0, w - 1, h - 1], outline=(170, 175, 180), width=4)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def tower_faces(t):
    """Two faces of the sign's towers, each stretched over one face in the map: the base's top band (10 ft wide,
    z 7-10.5) with the tan trim round the pass-through arch, and the upper shaft (9.5 ft wide, z 16.3-26.4) with the
    city seal centred 5.2 ft up."""
    stucco, tan = (234, 220, 186), (216, 186, 126)
    w, h = 64 * HI, 32 * HI                                    # 10 ft x 3.5 ft
    im = Image.new("RGB", (w, h), stucco)
    d = ImageDraw.Draw(im)
    px = w / 10.0
    cx, zi = w / 2, 7.0                                        # impost at the bottom edge (z 7)
    for r_out, col in ((2.1 + 0.75, tan), (2.1, (14, 14, 16))):
        d.ellipse([cx - r_out * px, h - (1.6 + (r_out - 2.1)) * px * 2 - 2, cx + r_out * px, h + (1.6 + (r_out - 2.1)) * px * 2],
                  fill=col)
    t["bk_btrim"] = ImageEnhance.Brightness(im).enhance(GAIN)
    w, h = 64 * HI, 64 * HI                                    # 9.5 ft x 10.1 ft
    im = Image.new("RGB", (w, h), stucco)
    seal = medallion((64, 64))
    seal = ImageEnhance.Brightness(seal).enhance(1 / GAIN)
    sz = int(w * 6.4 / 9.5)
    seal = seal.resize((sz, sz), Image.LANCZOS)
    m = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(m).ellipse([0, 0, sz - 1, sz - 1], fill=255)
    cy = h - h * 5.2 / 10.1
    im.paste(seal, (int(w / 2 - sz / 2), int(cy - sz / 2)), m)
    t["bk_bupper"] = ImageEnhance.Brightness(im).enhance(GAIN)


def street_sign(size, text, bg=(28, 70, 150), fg=(240, 240, 240)):
    from PIL import ImageFont
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, w - 4, h - 4], outline=fg, width=4)
    f = ImageFont.truetype("arialbd.ttf", int(h * 0.56))
    b = d.textbbox((0, 0), text, font=f)
    d.text(((w - b[2]) / 2, (h - b[3]) / 2 - b[1] / 2), text, font=f, fill=fg)
    return ImageEnhance.Brightness(im).enhance(GAIN)


def speed35(size):
    from PIL import ImageFont
    w, h = size[0] * HI, size[1] * HI
    im = Image.new("RGB", (w, h), (235, 235, 235))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w - 7, h - 7], outline=(20, 20, 20), width=6)
    f1, f2 = ImageFont.truetype("arialbd.ttf", int(h * 0.15)), ImageFont.truetype("arialbd.ttf", int(h * 0.42))
    for txt, f, y in (("SPEED", f1, 0.10), ("LIMIT", f1, 0.28), ("35", f2, 0.48)):
        b = d.textbbox((0, 0), txt, font=f)
        d.text(((w - b[2]) / 2, h * y), txt, font=f, fill=(20, 20, 20))
    return ImageEnhance.Brightness(im).enhance(GAIN)


def roof1608(t):
    """1608 Manning St's roof seen from above (the aerials at 199-217 s): brown composition shingle with the solar
    arrays - a long one on the back (east) slope, two on the front slope of the north part, one on the garage wing.
    Covers local x 130-190 ft, y 72-143 ft (bklan_osm frame of the Manning extract), north up."""
    w, h = 128 * HI, 128 * HI
    base = ImageEnhance.Brightness(t["bk_shingle"]).enhance(1 / GAIN).resize((w // 2, h // 2))
    im = Image.new("RGB", (w, h))
    for x in (0, w // 2):
        for y in (0, h // 2):
            im.paste(base, (x, y))
    X = lambda x: (x - 130) / 60 * w
    Y = lambda y: (143 - y) / 71 * h
    pv = ImageEnhance.Brightness(solar((16, 16))).enhance(1 / GAIN)
    for x0, y0, x1, y1 in ((168, 92, 184, 132), (139, 118, 150, 136), (152, 96, 160, 108), (135, 80, 146, 98)):
        p = pv.resize((int(X(x1) - X(x0)), int(Y(y0) - Y(y1))))
        im.paste(p, (int(X(x0)), int(Y(y1))))
    t["bk_h1608roof"] = ImageEnhance.Brightness(im).enhance(GAIN)


ORC = os.path.join(HERE, "ref_orcom")   # frames of Orcom 2.mpg (Dec 2002, 720x480), file = video second


def ocrop(sec, box, size, gain=GAIN, tile=False):
    im = Image.open(os.path.join(ORC, "%d.jpg" % sec)).convert("RGB").crop(box)
    im = im.resize((size[0] * HI, size[1] * HI), Image.LANCZOS)
    if tile:
        im = seamless(im)
    return ImageEnhance.Brightness(im).enhance(gain)


def osample(sec, box):
    return Image.open(os.path.join(ORC, "%d.jpg" % sec)).convert("RGB").crop(box).resize((1, 1), Image.BOX).getpixel((0, 0))


def build_orcom(t, glow):
    """The ORCOM CONNECT LAN PARTY hall (make_bklan_orcom.py): a church / lodge banquet hall, Dec 2002. Photo crops from
    the tape where they are legible, the rest drawn to match it."""
    from PIL import ImageFont
    t["oc_wall"] = ocrop(1866, (40, 4, 330, 88), (128, 64), gain=1.0, tile=True)    # cream sponge-painted plaster (the tape is dim)
    t["oc_floor"] = flat((206, 200, 184), (64, 64), 9, gain=0.8)                     # cream speckled vinyl tile
    t["oc_band"] = flat((26, 26, 26), (16, 16), 4)
    t["oc_bandgrey"] = flat((120, 116, 110), (16, 16), 5)
    w, h = 64 * HI, 64 * HI                                                           # lay-in ceiling, 4 x 4 ft
    im = Image.new("RGB", (w, h), (226, 224, 216))
    d = ImageDraw.Draw(im)
    for x in (0, w // 2):
        d.line([(x, 0), (x, h)], fill=(170, 168, 160), width=3)
    d.line([(0, 0), (w, 0)], fill=(170, 168, 160), width=3)
    t["oc_ceiling"] = ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(0.5))).enhance(GAIN)
    w, h = 32 * HI, 64 * HI                                                           # 2 x 4 ft troffer
    im = Image.new("RGB", (w, h), (250, 250, 245))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(180, 180, 175), width=6)
    for y in range(12, h, 10):
        d.line([(6, y), (w - 6, y)], fill=(228, 228, 222), width=1)
    t["oc_troffer"] = im
    glow["oc_troffer"] = ImageEnhance.Brightness(im).enhance(0.7)
    w, h = 32 * HI, 32 * HI
    im = Image.new("RGB", (w, h), (200, 200, 196))
    d = ImageDraw.Draw(im)
    for y in range(8, h - 4, 7):
        d.line([(8, y), (w - 8, y)], fill=(110, 110, 108), width=3)
    d.rectangle([0, 0, w - 1, h - 1], outline=(150, 150, 146), width=5)
    t["oc_grille"] = ImageEnhance.Brightness(im).enhance(GAIN)
    t["oc_bawls"] = ocrop(1880, (30, 45, 335, 185), (128, 64), gain=0.75)            # "OrCom Connect / Is Fueled By / BAWLS"
    t["oc_exitdoor"] = ocrop(1880, (380, 22, 553, 392), (64, 128), gain=0.7)        # cream steel door, panic bar
    t["oc_carved"] = ocrop(94, (505, 0, 700, 300), (64, 128), gain=0.9)             # carved entrance door leaf
    t["oc_photos"] = ocrop(726, (410, 98, 560, 170), (128, 64), gain=1.1)           # the board of framed portraits
    t["oc_whiteboard"] = ocrop(656, (100, 0, 690, 470), (128, 96), gain=0.8)        # tournament brackets ("Server 3")
    t["oc_clock"] = ocrop(1122, (470, 15, 555, 95), (32, 32))
    t["oc_picture"] = ocrop(1122, (345, 40, 440, 110), (32, 32))
    t["oc_tv"] = ocrop(726, (272, 142, 342, 192), (64, 48), gain=0.9)
    glow["oc_tv"] = ocrop(726, (272, 142, 342, 192), (64, 48), gain=0.5)
    t["oc_chair"] = flat((112, 42, 56), (32, 32), 8)                                 # burgundy banquet chairs
    t["oc_oak"] = flat(osample(20, (160, 250, 300, 320)), (64, 32), 10)              # the honey-oak counter
    t["oc_white"] = flat((230, 230, 226), (32, 32), 4)
    t["oc_red"] = flat((190, 40, 36), (16, 16), 5)
    t["oc_blue"] = flat((40, 70, 160), (16, 16), 5)
    t["oc_wood"] = flat((150, 96, 52), (32, 32), 10)                                 # the orange-wood exit door
    w, h = 64 * HI, 32 * HI                                                           # blue gingham tablecloth
    im = Image.new("RGB", (w, h), (235, 235, 235))
    d = ImageDraw.Draw(im)
    for k in range(0, w, 16):
        d.rectangle([k, 0, k + 7, h], fill=(150, 170, 215))
    for k in range(0, h, 16):
        d.rectangle([0, k, w, k + 7], fill=(150, 170, 215))
    for x in range(0, w, 16):
        for y in range(0, h, 16):
            d.rectangle([x, y, x + 7, y + 7], fill=(60, 90, 170))
    t["oc_gingham"] = ImageEnhance.Brightness(im).enhance(GAIN)
    w, h = 64 * HI, 16 * HI                                                           # EXIT sign
    im = Image.new("RGB", (w, h), (235, 235, 230))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("arialbd.ttf", int(h * 0.75))
    b = d.textbbox((0, 0), "EXIT", font=f)
    d.text(((w - b[2]) / 2, (h - b[3]) / 2 - b[1] / 2), "EXIT", font=f, fill=(210, 20, 20))
    t["oc_exit"] = im
    g = Image.new("RGB", (w, h), (0, 0, 0))
    ImageDraw.Draw(g).text(((w - b[2]) / 2, (h - b[3]) / 2 - b[1] / 2), "EXIT", font=f, fill=(200, 20, 20))
    glow["oc_exit"] = g
    w, h = 128 * HI, 48 * HI                                                          # the sponsor banner on the north wall (684 s)
    im = Image.new("RGB", (w, h), (236, 235, 230))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, w - 3, h - 3], outline=(195, 192, 185), width=3)
    fb = ImageFont.truetype("arialbd.ttf", int(h * 0.40))
    fr = ImageFont.truetype("arialbd.ttf", int(h * 0.11))
    fi = ImageFont.truetype("ariali.ttf", int(h * 0.10))
    fs = ImageFont.truetype("arialbd.ttf", int(h * 0.085))
    xcur = int(w * 0.07)
    for ch, col in (("C", (20, 20, 22)), ("o", (28, 108, 58)), ("mputer", (20, 20, 22))):
        d.text((xcur, int(h * 0.06)), ch, font=fb, fill=col)
        xcur += d.textbbox((0, 0), ch, font=fb)[2]
    d.text((int(w * 0.48), int(h * 0.45)), "R E N A I S S A N C E", font=fr, fill=(35, 35, 38))
    d.text((int(w * 0.08), int(h * 0.61)), "Where Computers Suddenly Make Sense", font=fi, fill=(45, 45, 48))
    d.text((int(w * 0.09), int(h * 0.80)), "Westchester Village, Stockdale and California", font=fs, fill=(30, 30, 32))
    t["oc_computer"] = ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(0.5))).enhance(GAIN)
    w, h = 64 * HI, 48 * HI                                                           # glass-front display case
    im = Image.new("RGB", (w, h), (196, 188, 160))
    d = ImageDraw.Draw(im)
    d.rectangle([w * .06, h * .2, w * .94, h * .94], fill=(70, 80, 84))
    for y in (0.45, 0.7):
        d.line([(w * .06, h * y), (w * .94, h * y)], fill=(170, 180, 182), width=4)
    fs = ImageFont.truetype("arialbd.ttf", int(h * 0.05))
    for k, line in enumerate(("ORTHODOX", "CHRISTIAN", "MISSIONS", "CENTER")):
        b = d.textbbox((0, 0), line, font=fs)
        d.text(((w - b[2]) / 2, h * (0.02 + k * 0.045)), line, font=fs, fill=(40, 30, 20))
    t["oc_case"] = ImageEnhance.Brightness(im).enhance(GAIN)
    w, h = 64 * HI, 32 * HI                                                           # US flag
    im = Image.new("RGB", (w, h), (235, 235, 235))
    d = ImageDraw.Draw(im)
    for k in range(13):
        if k % 2 == 0:
            d.rectangle([0, h * k / 13, w, h * (k + 1) / 13], fill=(178, 34, 52))
    d.rectangle([0, 0, w * .4, h * 7 / 13], fill=(60, 59, 110))
    t["oc_flag"] = ImageEnhance.Brightness(im).enhance(GAIN)
    w, h = 32 * HI, 64 * HI                                                           # white louvered door
    im = Image.new("RGB", (w, h), (232, 230, 224))
    d = ImageDraw.Draw(im)
    for y0, y1 in ((0.06, 0.4), (0.6, 0.94)):
        for y in range(int(h * y0), int(h * y1), 8):
            d.line([(w * .15, y), (w * .85, y)], fill=(170, 168, 160), width=3)
    t["oc_louver"] = ImageEnhance.Brightness(im).enhance(GAIN)
    w, h = 64 * HI, 64 * HI                                                           # cream accordion partition
    im = Image.new("RGB", (w, h), (222, 214, 190))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 24):
        d.rectangle([x, 0, x + 6, h], fill=(190, 182, 160))
    t["oc_accordion"] = ImageEnhance.Brightness(im).enhance(GAIN)


def build_v2(t, glow):
    """Textures for the 2026-10-30 22:56 additions: the Bakersfield Sign, Buck Owens' Crystal Palace and Sillect Ave,
    1608 Manning St and Amberton Park."""
    # the sign (warm Spanish-Revival pale cream towers, sandstone trim, marigold yellow arch)
    t["bk_bstucco"] = flat((234, 220, 186), (64, 64), 6)
    t["bk_btan"] = flat((216, 186, 126), (32, 32), 5)
    t["bk_broof"] = flat((132, 96, 70), (32, 32), 8)
    t["bk_bseal"] = medallion((64, 64))
    t["bk_bband"] = flat((244, 188, 34), (32, 32), 4, gain=1.0)
    t["bk_bsign"] = sign_band((512, 80))
    t["bk_dark"] = flat((14, 14, 16), (16, 16), 2)                                     # the pass-throughs' shade
    # Buck Owens' Crystal Palace: the pylon (65 s), the front on Buck Owens Blvd (80 s), KUZZ van (69 s)
    t["bk_cpsign"] = cpsign((224, 96))
    t["bk_cpfront"] = rphoto(80, (560, 395, 1340, 705), (256, 96))
    t["bk_cpwall"] = flat(rsample(80, (700, 470, 740, 520)), (64, 64), 5)
    t["bk_cppink"] = flat(rsample(80, (1180, 650, 1230, 690)), (32, 32), 5)
    t["bk_cpshingle"] = flat((128, 102, 86), (64, 32), 14)
    t["bk_office"] = office((64, 64))
    t["bk_officedk"] = office_dark((64, 64))
    t["bk_kuzz"] = quad(69, ((812, 608), (938, 610), (935, 735), (812, 718)), (128, 64))
    t["bk_brick"] = brick_tex((64, 32))
    t["bk_gcisign"] = gci_sign((128, 64))
    t["bk_floralbox"] = rphoto(118, (462, 600, 514, 700), (64, 96))
    capri_signs(t)
    # 1608 Manning St (163 s) and the street
    t["bk_hstucco"] = flat((214, 206, 190), (64, 64), 5)                                 # light beige stucco (sunlit, 163 s)
    t["bk_shingle"] = rphoto(163, (840, 200, 1380, 262), (128, 64), tile=True)
    t["bk_garage"] = garage((128, 64))
    t["bk_lawn"] = flat(grey(rsample(163, (1560, 780, 1820, 940)), 0.2), (128, 128), 16)
    t["bk_solar"] = solar((64, 64))
    t["bk_lime"] = flat((150, 205, 60), (32, 32), 6)                                    # the lime-green car
    t["bk_hedge"] = flat((48, 78, 38), (32, 32), 18)
    t["bk_leaf"] = flat((66, 98, 48), (32, 32), 20)
    t["bk_bark"] = flat((86, 70, 56), (16, 16), 10)
    t["bk_pool"] = flat((70, 190, 210), (64, 64), 6)
    t["bk_flagstone"] = flat((168, 150, 128), (64, 64), 18)
    # Amberton Park (240 s, 243 s)
    t["bk_drygrass"] = rphoto(243, (1180, 840, 1820, 1000), (128, 128), tile=True)
    t["bk_sand"] = flat((176, 160, 132), (64, 64), 12)
    t["bk_playgreen"] = flat((90, 190, 140), (32, 32), 5)
    t["bk_playred"] = flat((200, 80, 50), (32, 32), 5)
    t["bk_playteal"] = flat((40, 110, 100), (32, 32), 5)
    tower_faces(t)
    roof1608(t)
    t["bk_snbuck"] = street_sign((128, 16), "BUCK OWENS BLVD")
    t["bk_snsillect"] = street_sign((128, 16), "SILLECT AVE")
    t["bk_speed35"] = speed35((32, 48))


def build():
    t = {}
    glow = {}
    build_v2(t, glow)
    build_orcom(t, glow)
    # --- street side, from the Street View gallery (Feb 2026) ---
    FRONT = "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45."
    SV135 = "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw135"
    W110 = "sv-west-110e21st-pano-3JI52yTJxq_XrO4WDd2NCQ-yaw0"
    t["bk_stucco"] = gphoto(FRONT, (165, 356, 280, 440), (128, 128), tile=True)       # front wall panels (left of the "BATERIAS" sign)
    t["bk_fascia"] = gphoto(FRONT, (300, 252, 560, 298), (128, 32), tile=True)        # the tall blank parapet
    t["bk_blkdoor"] = gphoto(FRONT, (286, 346, 329, 431), (64, 128))
    t["bk_darkwin"] = gphoto(FRONT, (438, 346, 497, 389), (128, 64))
    t["bk_door120"] = gphoto(FRONT, (502, 334, 538, 416), (64, 128))                 # "120A" door + number
    t["bk_baterias"] = gphoto(FRONT, (226, 311, 284, 350), (64, 64))
    t["bk_redp"] = gphoto(FRONT, (684, 324, 699, 396), (32, 128))
    t["bk_bluep"] = gphoto(FRONT, (630, 324, 652, 396), (32, 128))
    t["bk_road"] = gphoto(FRONT, (600, 570, 1000, 680), (128, 128), tile=True, sat=0.75, gain=0.82)
    t["bk_walk"] = gphoto(FRONT, (160, 455, 320, 505), (128, 128), tile=True, sat=0.80, gain=0.88)
    t["bk_dirt"] = gphoto("sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw180", (570, 415, 760, 470), (128, 128), tile=True)
    t["bk_lmc"] = corrugated((128, 128), (205, 208, 210), (40, 70, 160))
    t["bk_lmcdoor"] = gphoto("sv-east-217e21st-pano-SXPieXYETR2XBRFy0NGVhA-yaw270", (214, 332, 258, 434), (64, 128))
    red105 = gal(SV135).crop((445, 275, 480, 345)).resize((1, 1), Image.BOX).getpixel((0, 0))
    t["bk_redcorr"] = corrugated((128, 128), red105)
    t["bk_pdsign"] = gphoto(SV135, (408, 280, 426, 307), (64, 64))
    t["bk_121sign"] = sign((96, 24), "121 E. 21st", (235, 235, 232), (24, 24, 26), 11)
    tan110 = gal(W110).crop((595, 315, 630, 390)).resize((1, 1), Image.BOX).getpixel((0, 0))
    t["bk_110tan"] = corrugated((128, 128), tan110)
    t["bk_110sale"] = gquad(W110, ((658, 250), (786, 236), (788, 297), (659, 300)), (128, 64))
    t["bk_stop"] = stop_sign((64, 64))
    t["bk_unionsn"] = street_sign((128, 32), "UNION AVE ->", bg=(30, 96, 62), fg=(238, 238, 235))
    t["bk_conestr"] = cone_striped((32, 64))
    t["bk_dumpster"] = dumpster_tex((64, 64))
    t["bk_sign120b"] = sign((64, 32), "120B", (220, 220, 215), (30, 30, 30), 14)
    t["bk_blansign"] = photo(1334, (95, 55, 265, 165), (64, 64), tile=False)          # B-LAN sign taped to the cone
    t["bk_130a"] = photo(1347, (75, 30, 205, 238), (64, 128), tile=False)             # plywood door sprayed "130 A"
    t["bk_yline"] = flat((200, 165, 40), (16, 16), 6)
    t["bk_wline"] = flat((215, 215, 210), (16, 16), 6)
    t["bk_grass"] = flat((95, 110, 60), (32, 32), 14)
    t["bk_roof"] = roof((128, 128))
    t["bk_crate"] = plywood((64, 64))
    t["bk_green"] = flat((40, 75, 50), (32, 32), 8)                                   # dumpster
    t["bk_lift"] = flat((40, 90, 170), (32, 32), 8)                                   # blue Genie boom lifts
    t["bk_pole"] = flat((90, 70, 50), (16, 16), 10)
    t["bk_brown"] = flat((120, 85, 60), (32, 32), 10)                                 # motel / lattice wall caps
    t["{chain"] = fence((64, 64), "chain")
    t["{iron"] = fence((64, 64), "iron")
    t["{lattice"] = fence((64, 64), "lattice")
    t["clip"] = flat((255, 0, 255), (16, 16), 0, 1.0)
    t["skip"] = flat((128, 128, 128), (64, 64), 0, 1.0)
    # the Celebrity Bodyworks building (Sacramento St side and the E 21st corner) and the rest of the block
    SAC = "sv-sacramento-848-pano-0xhYYQLO2ibyNjLvSd2Lgw-yaw270"
    SAC2 = "sv-sacramento-848-pano-0xhYYQLO2ibyNjLvSd2Lgw-yaw225"
    red = gal(SAC).crop((10, 300, 70, 400)).resize((1, 1), Image.BOX).getpixel((0, 0))
    green = gal(SAC2).crop((376, 318, 392, 380)).resize((1, 1), Image.BOX).getpixel((0, 0))
    t["bk_redwall"] = flat(red, (64, 64), 5)
    t["bk_greenwall"] = flat(green, (64, 64), 5)
    t["bk_celeb"] = gphoto(SAC, (254, 291, 334, 319), (128, 64))                       # "Celebrity" sign up on the north wall
    t["bk_gravel"] = flat((105, 98, 88), (64, 64), 22)                                  # rail ballast
    t["bk_unitwall"] = unitwall((128, 128))
    t["bk_shopwall"] = shopwall((128, 128))
    t["bk_motel"] = motelwall((128, 128))
    t["bk_tentblue"] = flat((40, 80, 170), (32, 32), 6)
    # --- building shell (photo) ---
    t["bk_wall"] = photo(1916, (110, 8, 250, 92), (128, 128))                 # cream painted interior wall
    t["bk_floor"] = concrete((128, 128), grey(sample(94, (100, 60, 200, 100)), 0.7))   # bare stained slab, camera blue cast taken out
    t["bk_mural"] = photo(1952, (230, 10, 310, 120), (128, 128), gain=0.8)     # side room's painted sky wall
    t["bk_rollup"] = photo(1622, (36, 18, 172, 80), (128, 128), tile=False, sat=0.4)  # roll-up from inside
    t["bk_door"] = photo(1738, (6, 40, 104, 232), (64, 128), tile=False)       # white flush door with knob
    t["bk_panel"] = photo(84, (118, 4, 234, 222), (64, 128), tile=False, gain=0.7)    # breaker panel, cover off
    t["bk_mbox"] = photo(122, (242, 150, 300, 200), (64, 64), tile=False, gain=0.75)  # "MONITOR" box
    t["bk_asphalt"] = photo(42, (228, 168, 318, 236), (128, 128), sat=0.75, gain=0.70)
    t["bk_extwall"] = block((128, 128), sample(64, (40, 40, 140, 120)))        # painted block outside
    t["bk_blockgr"] = block((128, 128), (140, 142, 140))                       # grey block wall at the lot's end
    t["bk_rollupx"] = slats((128, 128), sample(42, (220, 62, 252, 98)), (150, 155, 160))  # neighbours' roll-ups
    t["bk_deck"] = deck((128, 128))
    t["bk_steel"] = flat((58, 58, 62), (32, 32), 6)                            # joists, beams, door track
    t["bk_duct"] = photo(122, (198, 6, 226, 26), (64, 64), sat=0.3, gain=0.75)  # galvanized duct
    t["bk_trim"] = flat(sample(1738, (6, 40, 104, 140)), (32, 32), 4)          # white office box / frames
    t["bk_glass"] = flat((40, 50, 60), (64, 64), 3)                            # storefront glass at night
    # --- LAN props (sampled colours) ---
    t["bk_wood"] = wood((128, 64))
    t["bk_leg"] = flat((30, 30, 32), (16, 16), 4)
    t["bk_beige"] = flat(sample(122, (82, 150, 92, 200)), (32, 32), 4)
    t["bk_crt"], scr = crt_front((64, 64))
    glow["bk_crt"] = crt_glow((64, 64), scr)
    t["bk_tower"] = tower((32, 64))
    t["bk_kbd"] = kbd((64, 16))
    t["bk_chairbl"] = flat((40, 70, 140), (32, 32), 8)                         # blue camp/folding chair seats
    t["bk_chairbk"] = flat((28, 28, 30), (32, 32), 6)                          # black office chairs
    t["bk_white"] = flat((215, 215, 210), (32, 32), 5)                         # patio chairs, whiteboard
    t["bk_cone"] = flat((230, 90, 30), (16, 16), 6)
    t["bk_red"] = flat((150, 30, 30), (32, 32), 8)                             # pickup paint
    t["bk_blue"] = flat((140, 170, 200), (32, 32), 8)                          # light blue F-150
    t["bk_tire"] = flat((22, 22, 22), (16, 16), 4)
    t["bk_tube"] = tube((64, 16))
    glow["bk_tube"] = tube((64, 16))
    t["bk_neon"] = flat((255, 60, 220), (16, 16), 2, 1.0)                      # the magenta neon on the rack
    glow["bk_neon"] = t["bk_neon"]
    t["sky_bk"] = sky((256, 128))
    return t, glow


def main():
    t, glow = build()
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(WAD_OUT), exist_ok=True)
    small = {}
    for name, im in t.items():
        if not name.startswith("sky") and name not in ("clip", "skip"):
            im.save(os.path.join(TEX_DIR, name + ".png"))
        small[name] = im.resize((im.width // HI, im.height // HI), Image.LANCZOS)
    for name, im in glow.items():
        im.save(os.path.join(TEX_DIR, name + "_glow.png"))
    write_wad(WAD_OUT, small)
    import build_bklan_sky
    build_bklan_sky.main()
    print("wrote", WAD_OUT, len(small), "textures;", TEX_DIR)


def skybox(out_dir):
    """DarkPlaces skybox (worldspawn "skyname" "bklan_"): clear Bakersfield day, deep blue overhead fading to a pale hazy
    horizon, a few soft white cumulus. Baked at about half brightness: the mod's r_hdr_scenebrightness doubles the sky too."""
    import numpy as np
    os.makedirs(out_dir, exist_ok=True)
    S = 512

    def clouds(seed, cover):
        r = np.random.default_rng(seed)
        n = np.zeros((S, S))
        for o, amp in ((4, 1.0), (8, 0.5), (16, 0.25), (32, 0.12)):
            g = r.random((o, o))
            n += amp * np.asarray(Image.fromarray((g * 255).astype("uint8")).resize((S, S), Image.BICUBIC), float) / 255
        n /= 1.87
        return np.clip((n - (1 - cover)) * 4, 0, 1)

    for si, side in enumerate(("rt", "bk", "lf", "ft", "up", "dn")):
        yy = np.linspace(0, 1, S)[:, None] * np.ones((1, S))      # 0 top .. 1 horizon
        if side == "dn":
            im = np.ones((S, S, 3)) * np.array([62, 58, 50])
        else:
            top, hor = np.array([16, 44, 98]), np.array([62, 88, 116])
            k = (yy ** 1.6)[..., None] if side != "up" else np.zeros((S, S, 1))
            im = top + (hor - top) * k
            xx = np.linspace(0, 1, S)[None, :]
            edge = np.clip(np.minimum(xx, 1 - xx) * 7, 0, 1)             # puffs fade out at the face edges: no seams
            c = clouds(40 + si, 0.42) * (0.25 + 0.75 * yy) * edge * (side != "up")
            im = im + (np.array([98, 99, 102]) - im) * c[..., None] * 0.85
        Image.fromarray(np.clip(im, 0, 255).astype("uint8")).save(os.path.join(out_dir, "bklan_%s.png" % side))


if __name__ == "__main__":
    main()
