"""Photo-sampled & photo-matched textures from fox-theater-gallery-self-contained.html (fox_ref/gal_*.jpg)
for both The Historic Bakersfield Fox Theater (Feb 2026 / Threshold 360 Nov 2021) and its 1:1 surrounding
Downtown Bakersfield neighborhood (G St to Chester Ave, Wall St to 21st St).
"""
import math
import os
import random
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "fox_ref")
ART = os.path.join(HERE, "fox_art")
rnd = random.Random(20012026)


def load_art(fname, size, crop=None, sat=1.04, contrast=1.05, bright=0.88, h_seamless=0):
    """Load high-res generated artwork from fox_art/, crop/resize cleanly, and tone for DarkPlaces."""
    p = os.path.join(ART, fname)
    im = Image.open(p).convert("RGB")
    if crop is not None:
        im = im.crop(crop)
    w, h = size
    if h_seamless > 0:
        b = h_seamless
        src = im.resize((w + b, h), Image.LANCZOS)
        out = Image.new("RGB", (w, h))
        spx = src.load()
        opx = out.load()
        for y in range(h):
            for x in range(w):
                if x < b:
                    t = x / b
                    a = t * t * (3.0 - 2.0 * t)
                    r0, g0, b0 = spx[w + x, y]
                    r1, g1, b1 = spx[x, y]
                    opx[x, y] = (
                        int(round(r0 * (1.0 - a) + r1 * a)),
                        int(round(g0 * (1.0 - a) + g1 * a)),
                        int(round(b0 * (1.0 - a) + b1 * a)),
                    )
                else:
                    opx[x, y] = spx[x, y]
        im = out
    else:
        im = im.resize((w, h), Image.LANCZOS)
    if sat != 1.0:
        im = ImageEnhance.Color(im).enhance(sat)
    if contrast != 1.0:
        im = ImageEnhance.Contrast(im).enhance(contrast)
    if bright != 1.0:
        im = ImageEnhance.Brightness(im).enhance(bright)
    return im


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
SCRIPT = ["brushsci.ttf", "segoesc.ttf", "vladimir.ttf", "georgiaz.ttf"]


def add_noise(im, amt=4):
    rgba = im.mode == "RGBA"
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            n = rnd.randint(-amt, amt)
            p = px[x, y]
            if rgba:
                px[x, y] = (max(0, min(255, p[0] + n)), max(0, min(255, p[1] + n)), max(0, min(255, p[2] + n)), p[3])
            else:
                px[x, y] = (max(0, min(255, p[0] + n)), max(0, min(255, p[1] + n)), max(0, min(255, p[2] + n)))
    return im


def dim(im, k=0.92):
    return ImageEnhance.Brightness(im.convert("RGB")).enhance(k)


def load_ref(fname):
    p = os.path.join(REF, fname)
    if os.path.exists(p):
        return Image.open(p).convert("RGB")
    return None


def quad_sample(fname, quad_pts, size=(256, 256), sat=1.12, contrast=1.10, bright=0.96, sharpen=True):
    """Perspective-rectify a 4-corner quadrilateral (UL, LL, LR, UR) directly from a Street View / interior photo."""
    src = load_ref(fname)
    if src is None:
        return Image.new("RGB", size, (180, 172, 156))
    flat = [c for pt in quad_pts for c in pt]
    im = src.transform(size, Image.QUAD, flat, Image.BICUBIC)
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Brightness(im).enhance(bright)
    if sharpen:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=135, threshold=2))
    return im


def make_seamless(im, blend=40):
    """Cross-blend opposing edges over `blend` pixels so photo-sampled surfaces tile seamlessly in Quake."""
    w, h = im.size
    off = ImageChops.offset(im, w // 2, h // 2)
    mask = Image.new("L", (w, h), 255)
    md = ImageDraw.Draw(mask)
    for i in range(blend):
        v = int(255 * (i / blend) ** 0.85)
        cx0, cy0 = w // 2 - blend + i, h // 2 - blend + i
        cx1, cy1 = w // 2 + blend - i, h // 2 + blend - i
        md.rectangle([cx0, 0, cx1, h], fill=255 - v)
        md.rectangle([0, cy0, w, cy1], fill=255 - v)
    # Smooth radial/cross mask around the offset seam at (w//2, h//2)
    m2 = Image.new("L", (w, h), 0)
    px = m2.load()
    for y in range(h):
        dy = abs(y - h // 2)
        wy = max(0.0, 1.0 - dy / blend)
        for x in range(w):
            dx = abs(x - w // 2)
            wx = max(0.0, 1.0 - dx / blend)
            wgt = max(wx, wy)
            px[x, y] = int(255 * (wgt * wgt * (3 - 2 * wgt)))
    return Image.composite(im, off, m2)


# ============================================================================== 1. UPGRADED FOX THEATER PHOTO TEXTURES
def fox_photo_carpet():
    """Photo-sampled crimson & golden-olive acanthus scroll carpet from Threshold 360 Mezzanine (gal_114 & gal_117)."""
    # Sample clean flat carpet patch from bottom-right of gal_117.jpg (800x533) & bottom-center of gal_114.jpg
    im = quad_sample(
        "gal_114.jpg",
        [(235, 390), (205, 525), (495, 525), (435, 390)],
        size=(256, 256), sat=1.28, contrast=1.18, bright=0.92,
    )
    return make_seamless(im, blend=48)


def fox_fresco_ceiling():
    """Sky-blue & rose-medallion frescoed plaster ceiling from Mezzanine lobby (matched to gal_114.jpg & gal_115.jpg)."""
    S = 256
    grain = quad_sample("gal_114.jpg", [(18, 22), (18, 140), (210, 140), (210, 22)], size=(S, S), sat=1.10, contrast=1.05, bright=1.02, sharpen=False)
    im = Image.new("RGB", (S, S), (126, 146, 158))
    d = ImageDraw.Draw(im)
    # Soft clouds & painted circular rose/cream ceiling medallion (gal_114.jpg!)
    for _ in range(90):
        x, y = rnd.randint(-30, S), rnd.randint(-30, S)
        r = rnd.randint(24, 64)
        c = rnd.randint(-12, 12)
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d.ellipse([x + dx, y + dy, x + dx + r, y + dy + r], fill=(122 + c, 144 + c, 158 + c))
    im = im.filter(ImageFilter.GaussianBlur(5.0))
    d = ImageDraw.Draw(im)
    cx, cy = S // 2, S // 2
    d.ellipse([cx - 88, cy - 88, cx + 88, cy + 88], outline=(196, 152, 142), width=12)
    d.ellipse([cx - 72, cy - 72, cx + 72, cy + 72], outline=(224, 212, 186), width=6)
    d.ellipse([cx - 56, cy - 56, cx + 56, cy + 56], outline=(154, 174, 168), width=8)
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(214, 196, 158), outline=(184, 148, 86), width=4)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    im = Image.blend(im, make_seamless(grain, 44), 0.30)
    return dim(add_noise(im, 3), 0.98)


def fox_feb2026_terrazzo():
    """Green-and-cream diamond checkerboard terrazzo with coral-red border (matched directly to gal_110.jpg & gal_021.jpg)."""
    S = 256
    # Sample real weathered surface grain from gal_110.jpg foreground terrazzo
    grain = quad_sample(
        "gal_110.jpg",
        [(40, 415), (10, 528), (560, 528), (470, 415)],
        size=(S, S), sat=1.05, contrast=1.05, bright=1.0, sharpen=False,
    )
    im = Image.new("RGB", (S, S), (206, 212, 198))
    d = ImageDraw.Draw(im)
    # 2x2 diagonal diamond tiles in seafoam-sage green & warm cream with brass divider strips
    half = S // 2
    for ox in (0, half):
        for oy in (0, half):
            pts = [(ox + half // 2, oy), (ox + half, oy + half // 2), (ox + half // 2, oy + half), (ox, oy + half // 2)]
            d.polygon(pts, fill=(102, 148, 136), outline=(176, 158, 112), width=2)
    # Blend 30% real photo patina + aggregate speckle
    im = Image.blend(im, make_seamless(grain, 40), 0.26)
    return dim(add_noise(im, 4), 0.96)


def fox_marquee_chevron():
    """Photo-matched Feb 2026 Fox marquee Art Deco chevron valence: crimson/gold/olive feathered bays (gal_019/gal_020)."""
    W, H = 256, 128
    patch = quad_sample(
        "gal_019.jpg",
        [(70, 148), (70, 184), (240, 200), (240, 168)],
        size=(W, H), sat=1.22, contrast=1.15, bright=1.0,
    )
    im = Image.new("RGB", (W, H), (174, 152, 68))
    d = ImageDraw.Draw(im)
    # 4 crisp Art Deco chevron bays + olive fluted dividers matching gal_019.jpg / gal_020.jpg!
    bw = W // 4
    for i in range(4):
        x0 = i * bw
        # Olive-green fluted rib
        d.rectangle([x0, 0, x0 + 14, H], fill=(108, 134, 74))
        for ry in range(0, H, 10):
            d.line([(x0, ry), (x0 + 14, ry)], fill=(78, 102, 52), width=2)
        # Chevron plume bay (alternating crimson-red, warm gold, coral)
        cx0, cx1 = x0 + 14, x0 + bw
        cmid = (cx0 + cx1) // 2
        d.rectangle([cx0, 0, cx1, H], fill=(192, 64, 58))
        for y in range(-16, H + 16, 22):
            d.polygon([(cx0, y + 14), (cmid, y + 26), (cx1, y + 14), (cx1, y + 4), (cmid, y + 16), (cx0, y + 4)],
                      fill=(232, 188, 74))
            d.polygon([(cx0, y + 4), (cmid, y + 16), (cx1, y + 4), (cx1, y - 2), (cmid, y + 10), (cx0, y - 2)],
                      fill=(146, 36, 42))
    d.rectangle([0, 0, W, 8], fill=(214, 174, 72))
    d.rectangle([0, H - 9, W, H], fill=(198, 96, 74))
    im = Image.blend(im, patch, 0.22)
    return dim(add_noise(im, 3), 0.96)


def fox_marquee_gold_ribs():
    """Stepped gold-and-olive horizontal ribbed center valence directly behind the red cursive 'Fox' sign (gal_020.jpg)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (196, 168, 66))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 12):
        d.rectangle([0, y, W, y + 6], fill=(224, 192, 78))
        d.rectangle([0, y + 6, W, y + 11], fill=(92, 118, 62))
    d.rectangle([0, 0, W, 8], fill=(232, 198, 88))
    return dim(add_noise(im, 4), 0.95)


def fox_script_cutout():
    """Alpha-cutout 3D cursive 'Fox' rooftop channel-letter sign + top Art Deco neon bar (gal_020 & gal_023!)."""
    W, H = 512, 256
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Top horizontal crimson-and-white Art Deco neon crown bar & short support posts (seen in gal_023.jpg!)
    for sx in (118, 256, 394):
        d.rectangle([sx - 5, 24, sx + 5, 62], fill=(58, 20, 22, 255))
    d.rounded_rectangle([54, 10, W - 54, 30], radius=6, fill=(52, 16, 18, 255))
    d.rounded_rectangle([58, 12, W - 58, 27], radius=5, fill=(246, 242, 236, 255), outline=(172, 22, 28, 255), width=4)

    def strokes(dx, dy, col, w):
        d.line([(68 + dx, 64 + dy), (186 + dx, 46 + dy), (254 + dx, 54 + dy)], fill=col, width=w, joint="curve")
        d.line([(166 + dx, 52 + dy), (132 + dx, 144 + dy), (96 + dx, 220 + dy), (66 + dx, 226 + dy)], fill=col, width=w, joint="curve")
        d.line([(84 + dx, 138 + dy), (192 + dx, 130 + dy)], fill=col, width=int(w * 0.85))
        d.ellipse([202 + dx, 98 + dy, 316 + dx, 216 + dy], outline=col, width=w)
        d.line([(328 + dx, 104 + dy), (388 + dx, 160 + dy), (452 + dx, 218 + dy)], fill=col, width=w, joint="curve")
        d.line([(458 + dx, 98 + dy), (386 + dx, 160 + dy), (320 + dx, 220 + dy)], fill=col, width=w, joint="curve")

    # Deep 3D maroon metal return -> crisp white porcelain trim -> rich crimson face -> neon center tube
    strokes(8, 8, (46, 14, 16, 255), 54)
    strokes(0, 0, (46, 14, 16, 255), 54)
    strokes(0, 0, (246, 242, 236, 255), 44)
    strokes(0, 0, (162, 18, 24, 255), 30)
    strokes(0, 0, (238, 86, 82, 255), 7)
    # Guarantee a clean 8-pixel 100% transparent border around all 4 edges so thin brush side faces never show artifacts
    d.rectangle([0, 0, W - 1, 7], fill=(0, 0, 0, 0))
    d.rectangle([0, H - 8, W - 1, H - 1], fill=(0, 0, 0, 0))
    d.rectangle([0, 0, 7, H - 1], fill=(0, 0, 0, 0))
    d.rectangle([W - 8, 0, W - 1, H - 1], fill=(0, 0, 0, 0))
    return im


def fox_marquee_board(cols_lines, w=512, h=160):
    """Feb 2026 backlit white marquee readerboard supporting 1 or 2 show columns + chevron lower lip (gal_020/gal_021)."""
    im = Image.new("RGB", (w, h), (232, 234, 236))
    glow = Image.new("RGB", (w, h), (38, 40, 42))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    # Top thin gold trim & bottom peach/crimson/gold chevron soffit lip (gal_020.jpg!)
    d.rectangle([0, 0, w, 10], fill=(184, 152, 78))
    gd.rectangle([0, 0, w, 10], fill=(12, 10, 6))
    lip_y = h - 24
    d.rectangle([0, lip_y, w, h], fill=(216, 156, 108))
    gd.rectangle([0, lip_y, w, h], fill=(28, 18, 12))
    for x in range(0, w, 28):
        d.polygon([(x, h - 4), (x + 14, lip_y + 4), (x + 28, h - 4)], outline=(178, 48, 46), width=3)
        gd.ellipse([x + 10, lip_y + 8, x + 18, lip_y + 16], fill=(170, 140, 75))
    # Horizontal changeable-letter tracks
    t0, t1 = 12, lip_y - 2
    for r in range(5):
        yy = t0 + int((t1 - t0) * r / 4)
        d.line([(0, yy), (w, yy)], fill=(176, 182, 188), width=2)
    for x in range(64, w, 64):
        d.line([(x, t0), (x, t1)], fill=(202, 206, 212), width=2)
    ncols = len(cols_lines)
    for ci, lines in enumerate(cols_lines):
        if not lines:
            continue
        cx = int(w * (ci + 0.5) / ncols)
        for li, txt in enumerate(lines):
            cy = t0 + (t1 - t0) * (li + 0.5) / len(lines)
            fsz = 29 if ncols == 1 else 25
            f = font(BLACK, fsz)
            d.text((cx, cy), txt, font=f, fill=(96, 10, 16), anchor="mm")
            gd.text((cx, cy), txt, font=f, fill=(0, 0, 0), anchor="mm")
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(0.8))


def gold_wrought_iron():
    """Antique gold-painted wrought-iron scroll balustrade of the Mezzanine & Grand Staircase (gal_114, gal_115, gal_116)."""
    W, H = 256, 128
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    gld = (188, 152, 68, 255)
    hi = (226, 192, 102, 255)
    cap = (58, 42, 30, 255)
    d.rectangle([0, 0, W, 9], fill=cap)
    d.rectangle([0, 9, W, 14], fill=hi)
    d.rectangle([0, H - 10, W, H], fill=gld)
    for x0 in range(0, W, 64):
        d.rectangle([x0, 9, x0 + 6, H], fill=gld)
        d.rectangle([x0 + 30, 14, x0 + 34, H - 10], fill=hi)
        d.arc([x0 + 7, 20, x0 + 30, 66], 35, 330, fill=gld, width=4)
        d.arc([x0 + 34, 20, x0 + 57, 66], 210, 145, fill=gld, width=4)
        d.arc([x0 + 7, 64, x0 + 30, 114], 25, 325, fill=gld, width=4)
        d.arc([x0 + 34, 64, x0 + 57, 114], 215, 155, fill=gld, width=4)
        d.ellipse([x0 + 24, 58, x0 + 40, 74], outline=hi, width=3)
    return im


def hst_transom_arch():
    """Divided multi-pane arched clerestory transom above the 5 H St red awnings (gal_019.jpg & gal_023.jpg)."""
    W, H = 256, 96
    im = Image.new("RGB", (W, H), (228, 218, 200))
    d = ImageDraw.Draw(im)
    d.pieslice([10, 10, W - 10, H * 2 - 12], 180, 360, fill=(44, 54, 60), outline=(196, 142, 112), width=6)
    for x in range(36, W - 24, 28):
        d.line([(x, 12), (x, H - 4)], fill=(224, 214, 196), width=4)
    d.rectangle([0, H - 8, W, H], fill=(196, 142, 112))
    return dim(add_noise(im, 4), 0.94)


def awning_solid(rgb, rib_rgb):
    """Canvas storefront awning in terracotta-red, charcoal-black, or orange (gal_019, gal_016, gal_055)."""
    S = 128
    im = Image.new("RGB", (S, S), rgb)
    d = ImageDraw.Draw(im)
    for x in range(0, S, 16):
        d.line([(x, 0), (x, S)], fill=rib_rgb, width=2)
    d.rectangle([0, S - 10, S, S], fill=rib_rgb)
    return dim(add_noise(im, 4), 0.92)


# ============================================================================== 2. SURROUNDING NEIGHBORHOOD PHOTO TEXTURES
def stacked_stone_2000h():
    """Photo-sampled stacked ledger stone wainscot from 2000 H St across from the Fox (gal_013.jpg)."""
    im = quad_sample(
        "gal_013.jpg",
        [(605, 345), (605, 392), (790, 428), (790, 366)],
        size=(256, 128), sat=1.15, contrast=1.18, bright=0.98,
    )
    return make_seamless(im, blend=28)


def bw_striped_awning():
    """Bold black-and-white vertical-striped wrap-around canopy of 2000 H St (gal_013.jpg & gal_014.jpg)."""
    S = 256
    im = Image.new("RGB", (S, S), (238, 238, 236))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):
        d.rectangle([x, 0, x + 15, S], fill=(28, 30, 34))
        d.rectangle([x + 16, 0, x + 31, S], fill=(238, 238, 234))
    return dim(add_noise(im, 4), 0.94)


def dark_storefront_glass():
    """Dark reflective commercial storefront glass with black aluminum mullions & subtle sky reflection (gal_013.jpg)."""
    W, H = 256, 192
    im = Image.new("RGB", (W, H), (28, 34, 40))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        c = (int(48 - 22 * t), int(58 - 26 * t), int(68 - 30 * t))
        d.line([(0, y), (W, y)], fill=c)
    # Subtle warm Fox marquee reflection hint + mullions
    d.rectangle([18, 68, W - 18, 96], fill=(64, 62, 60))
    for x in (0, 64, 128, 192, W - 5):
        d.rectangle([x, 0, x + 5, H], fill=(20, 22, 24))
    for y in (0, 56, H - 6):
        d.rectangle([0, y, W, y + 5], fill=(20, 22, 24))
    return add_noise(im, 3)


def american_legion_sign():
    """American Legion Post 26 grey pebble-stucco wall & blue/white badge sign (2020 H St, gal_012.jpg & gal_037.jpg)."""
    W, H = 256, 192
    im = Image.new("RGB", (W, H), (194, 192, 186))
    d = ImageDraw.Draw(im)
    for _ in range(280):
        px0, py0 = rnd.randint(0, W), rnd.randint(0, H)
        c = rnd.randint(-12, 12)
        d.ellipse([px0, py0, px0 + rnd.randint(4, 12), py0 + rnd.randint(4, 10)], fill=(194 + c, 192 + c, 186 + c))
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 10], fill=(154, 152, 148))
    d.rectangle([52, 26, 204, 76], fill=(244, 244, 240), outline=(36, 68, 138), width=4)
    d.text((128, 42), "AMERICAN LEGION", font=font(BOLD, 14), fill=(178, 34, 38), anchor="mm")
    d.rectangle([56, 54, 200, 72], fill=(32, 64, 138))
    d.text((128, 63), "POST 26", font=font(BOLD, 14), fill=(248, 248, 244), anchor="mm")
    # Recessed lower entrance bay
    d.rectangle([44, 108, W - 44, H], fill=(42, 46, 52), outline=(136, 134, 130), width=4)
    d.line([(128, 108), (128, H)], fill=(154, 154, 150), width=3)
    return dim(add_noise(im, 4), 0.95)


def us_flag_mural():
    """Waving American Flag mural under American Legion Post 26 canopy & on flagpole (gal_012.jpg & gal_110.jpg)."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (236, 234, 228))
    d = ImageDraw.Draw(im)
    for i in range(13):
        y0, y1 = int(i * H / 13), int((i + 1) * H / 13)
        col = (182, 34, 42) if i % 2 == 0 else (238, 236, 228)
        d.rectangle([0, y0, W, y1], fill=col)
    d.rectangle([0, 0, int(W * 0.42), int(H * 7 / 13)], fill=(28, 52, 112))
    for r in range(5):
        for c in range(6):
            sx, sy = 12 + c * 17, 8 + r * 12
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(244, 244, 240))
    # Subtle wave shading matching painted mural in gal_012.jpg
    px = im.load()
    for x in range(W):
        s = 0.88 + 0.12 * math.sin(x / W * 4 * math.pi)
        for y in range(H):
            r, g, b = px[x, y]
            px[x, y] = (min(255, int(r * s)), min(255, int(g * s)), min(255, int(b * s)))
    return add_noise(im, 3)


def today_cleaners_fascia():
    """Photo-matched 'TODAY CLEANERS' cream canopy fascia with yellow-black text & coat-hanger logo (gal_038.jpg)."""
    W, H = 512, 128
    im = Image.new("RGB", (W, H), (206, 198, 178))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([0, 0, W, 10], fill=(168, 160, 142))
    d.rectangle([0, H - 12, W, H], fill=(142, 134, 118))
    # Coat-hanger logo on left (seen clearly in gal_038.jpg!)
    d.arc([44, 24, 72, 52], 180, 45, fill=(32, 32, 32), width=4)
    d.polygon([(22, 92), (58, 50), (96, 92)], fill=(246, 206, 36), outline=(28, 28, 28), width=5)
    # Bold single-line yellow channel letters with thick black drop-outline (exact match to gal_038.jpg!)
    for dx, dy in ((-3, 3), (3, 3), (-3, -2), (3, -2)):
        d.text((302 + dx, 66 + dy), "TODAY CLEANERS", font=font(BLACK, 38), fill=(24, 24, 24), anchor="mm")
    d.text((302, 66), "TODAY CLEANERS", font=font(BLACK, 38), fill=(250, 212, 38), anchor="mm")
    gd.text((302, 66), "TODAY CLEANERS", font=font(BLACK, 38), fill=(150, 125, 20), anchor="mm")
    return add_noise(im, 4), glow.filter(ImageFilter.GaussianBlur(1.2))


def tevis_brick_wall():
    """Photo-sampled historic tan-terracotta Tevis Block / Kern Land Building brick + arched green awning bay (gal_025/gal_031)."""
    W, H = 256, 256
    brick = quad_sample("gal_025.jpg", [(15, 35), (15, 195), (125, 195), (125, 35)], size=(W, H), sat=1.18, contrast=1.14, bright=0.98)
    brick = make_seamless(brick, 36)
    d = ImageDraw.Draw(brick)
    # Upper rectangular 2nd-story sash windows + dentil stringcourse + lower arched green awning!
    d.rectangle([0, 108, W, 118], fill=(176, 122, 86))
    for wx in (36, 156):
        d.rectangle([wx, 26, wx + 64, 94], fill=(42, 54, 58), outline=(156, 104, 72), width=5)
        d.line([(wx, 60), (wx + 64, 60)], fill=(32, 72, 56), width=4)
        # Arched ground window with forest-green dome awning + sandstone base!
        d.pieslice([wx - 6, 134, wx + 70, 210], 180, 360, fill=(28, 92, 62), outline=(20, 68, 44), width=3)
        d.rectangle([wx + 2, 172, wx + 62, 220], fill=(38, 48, 52), outline=(146, 98, 68), width=4)
    # Rusticated sandstone basement course (gal_025.jpg)
    d.rectangle([0, 224, W, H], fill=(184, 168, 136))
    for sx in range(0, W, 42):
        d.rectangle([sx + 2, 226, sx + 39, H - 2], outline=(142, 128, 98), width=2)
    return dim(add_noise(brick, 3), 0.95)


def red_brick():
    """Photo-matched warm weathered Downtown Bakersfield red-brick masonry (PG&E piers & 21st/Eye warehouse, gal_015 & gal_077)."""
    S = 256
    grain = quad_sample("gal_015.jpg", [(275, 232), (275, 280), (315, 280), (315, 232)], size=(S, S), sat=1.18, contrast=1.10, bright=0.96, sharpen=False)
    im = Image.new("RGB", (S, S), (156, 86, 68))
    d = ImageDraw.Draw(im)
    for row in range(16):
        y0 = row * 16
        off = 0 if row % 2 == 0 else 16
        for x0 in range(-16 + off, S, 32):
            c = rnd.randint(-16, 16)
            rc = rnd.randint(-6, 8)
            d.rectangle([x0 + 1, y0 + 1, x0 + 30, y0 + 14], fill=(max(0, min(255, 158 + c + rc)), max(0, min(255, 84 + c)), max(0, min(255, 66 + c))))
        d.line([(0, y0 + 15), (S, y0 + 15)], fill=(182, 168, 152), width=2)
    im = Image.blend(im, make_seamless(grain, 44), 0.25)
    return dim(add_noise(im, 4), 0.94)


def pge_sign():
    """PG&E blue-and-gold square utility emblem on red-brick pier (SE corner of 20th & H St, gal_015.jpg)."""
    S = 256
    im = red_brick()
    d = ImageDraw.Draw(im)
    d.rectangle([36, 36, 220, 220], fill=(38, 108, 176), outline=(218, 214, 204), width=5)
    d.polygon([(118, 56), (162, 56), (182, 198), (98, 198)], fill=(244, 184, 42))
    d.text((128, 168), "PG&E", font=font(BLACK, 44), fill=(248, 248, 246), anchor="mm")
    return add_noise(im, 3)


def tegeler_wall():
    """Photo-matched 4-story white & terracotta-pink historic Tegeler Hotel window facade (1918 H St, gal_025.jpg)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (222, 220, 224))
    d = ImageDraw.Draw(im)
    # Terracotta-pink cornice band & ground wainscot (gal_025.jpg right side!)
    d.rectangle([0, 0, W, 24], fill=(208, 152, 138))
    d.rectangle([0, H - 28, W, H], fill=(196, 146, 134))
    for wy in (42, 108, 174):
        for wx in (24, 104, 184):
            d.rectangle([wx, wy, wx + 46, wy + 46], fill=(56, 68, 78), outline=(146, 144, 148), width=3)
            d.line([(wx + 23, wy), (wx + 23, wy + 46)], fill=(214, 212, 216), width=3)
    return dim(add_noise(im, 4), 0.95)


def tegeler_sign():
    """Upper north wall of Tegeler Hotel with bold black 'TEGELER' block lettering (gal_015.jpg & gal_016.jpg)."""
    W, H = 512, 128
    im = Image.new("RGB", (W, H), (224, 222, 224))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 12], fill=(198, 148, 136))
    d.text((W // 2, 52), "TEGELER", font=font(BLACK, 58), fill=(32, 34, 38), anchor="mm")
    for wx in (96, 256, 416):
        d.rectangle([wx - 20, 88, wx + 20, 124], fill=(52, 62, 72), outline=(160, 160, 164), width=2)
    return dim(add_noise(im, 4), 0.95)


def linos_ribbon():
    """Smooth cream-tan 2-story wall with continuous dark 2nd-floor ribbon window band (Lino's 1931 H St & NW 19th/Chester)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (218, 206, 186))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=(148, 108, 86))
    # Continuous dark 2nd-story ribbon windows
    d.rectangle([0, 68, W, 124], fill=(38, 44, 52))
    for x in range(0, W, 42):
        d.line([(x, 68), (x, 124)], fill=(76, 82, 88), width=3)
    d.rectangle([0, 124, W, 130], fill=(168, 154, 134))
    # Lower brick piers & white storefront bays (gal_016.jpg)
    for x0 in (0, 128):
        d.rectangle([x0, 168, x0 + 28, H], fill=(138, 82, 68))
        d.rectangle([x0 + 28, 176, x0 + 128, H], fill=(214, 218, 222), outline=(72, 76, 82), width=3)
    return dim(add_noise(im, 4), 0.95)


def jones_building():
    """Curved Streamline Moderne cream parapet reading 'J  ES / BUILDING' + ribbon glass (20th & Eye, gal_055.jpg)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (228, 222, 208))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 34), "J   ES", font=font(BLACK, 28), fill=(34, 32, 30), anchor="mm")
    d.text((W // 2, 64), "BUILDING", font=font(BLACK, 28), fill=(34, 32, 30), anchor="mm")
    # Reflective silver-blue 2nd-story ribbon windows
    d.rectangle([0, 92, W, 186], fill=(118, 138, 152), outline=(176, 170, 158), width=4)
    for x in range(0, W, 64):
        d.rectangle([x, 92, x + 6, 186], fill=(212, 208, 198))
        d.line([(x + 12, 178), (x + 54, 102)], fill=(168, 186, 198), width=5)
    d.rectangle([0, H - 18, W, H], fill=(38, 36, 36))
    return dim(add_noise(im, 4), 0.96)


def coffee_awning():
    """Terracotta-orange canvas awning reading 'COFFEE COMPANY' under the Jones Building (gal_055.jpg)."""
    W, H = 256, 96
    im = Image.new("RGB", (W, H), (196, 104, 62))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 16):
        d.line([(x, 0), (x, H)], fill=(168, 84, 48), width=2)
    d.rectangle([0, H - 28, W, H], fill=(176, 88, 50))
    d.text((W // 2, H - 14), "COFFEE COMPANY", font=font(SERIF, 18), fill=(246, 232, 206), anchor="mm")
    return dim(add_noise(im, 4), 0.94)


def substation_facade():
    """2-story white/cream stucco building at SW corner of 20th & Eye ('Sub Station' + upper windows, gal_054/gal_055)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (226, 220, 212))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 12], fill=(186, 180, 172))
    d.rectangle([0, 118, W, H], fill=(214, 204, 194))
    for wx in (56, 168, 280, 392):
        d.rectangle([wx, 38, wx + 36, 98], fill=(56, 62, 66), outline=(188, 182, 174), width=4)
    # Green 'Sub Station' sign & awning on right half, recessed commercial window on left half
    d.text((370, 140), "Sub Station", font=font(BOLD, 28), fill=(28, 78, 48), anchor="mm")
    d.rectangle([280, 158, 460, 182], fill=(26, 84, 54))
    d.rectangle([290, 182, 450, H], fill=(48, 56, 62), outline=(168, 162, 154), width=4)
    d.rectangle([44, 158, 212, H], fill=(58, 76, 94), outline=(176, 168, 158), width=6)
    d.polygon([(52, H - 8), (112, 196), (176, H - 8)], fill=(218, 224, 232))
    return dim(add_noise(im, 4), 0.95)


def jin_sushi_facade():
    """Taupe & cream 2-story facade of JIN Sushi with 'HAPPY HOUR' banner (NW corner of 19th & Eye, gal_065.jpg)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (222, 214, 190))
    d = ImageDraw.Draw(im)
    # 2nd-story windows in olive-tan band
    d.rectangle([0, 24, W, 108], fill=(184, 172, 142))
    for wx in range(32, W - 32, 80):
        d.rectangle([wx, 38, wx + 48, 96], fill=(92, 112, 126), outline=(228, 224, 214), width=3)
    # Taupe lower fascia + 'JIN Sushi' + 'HAPPY HOUR' banner
    d.rectangle([0, 112, W, 178], fill=(154, 138, 132))
    d.text((W // 2, 146), "JIN Sushi", font=font(SERIF, 32), fill=(246, 244, 238), anchor="mm")
    d.rectangle([0, 178, W, H], fill=(38, 38, 42))
    for x in range(24, W, 64):
        d.rectangle([x, 186, x + 48, H - 4], fill=(54, 62, 68), outline=(28, 28, 30), width=2)
    d.rectangle([28, 184, 118, 232], fill=(246, 242, 232), outline=(186, 38, 36), width=3)
    d.text((73, 200), "HAPPY", font=font(BLACK, 18), fill=(196, 36, 34), anchor="mm")
    d.text((73, 218), "HOUR", font=font(BLACK, 18), fill=(196, 36, 34), anchor="mm")
    return dim(add_noise(im, 4), 0.95)


def toss_it_facade():
    """Photo-matched 'TOSS it' green/white/black logo + taupe stucco & upper windows on Service St (gal_103.jpg)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (226, 218, 196))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 18, W, 102], fill=(186, 174, 142))
    for wx in (48, 216, 384):
        d.rectangle([wx, 28, wx + 80, 92], fill=(138, 158, 168), outline=(236, 236, 232), width=4)
        d.line([(wx + 40, 28), (wx + 40, 92)], fill=(236, 236, 232), width=3)
    d.rectangle([0, 114, W, H], fill=(168, 150, 144))
    # Bold 'TOSS it' green & white sign (exact match to gal_103.jpg!)
    for dx, dy in ((-3, 3), (3, 3)):
        d.text((320 + dx, 152 + dy), "TOSS it", font=font(BLACK, 38), fill=(26, 28, 26), anchor="mm")
    d.text((294, 152), "TOSS", font=font(BLACK, 38), fill=(116, 212, 72), anchor="mm")
    d.text((388, 152), "it", font=font(SCRIPT, 44), fill=(138, 226, 82), anchor="mm")
    d.rectangle([208, 184, 442, H], fill=(56, 62, 66), outline=(228, 226, 220), width=4)
    return dim(add_noise(im, 4), 0.95)


def tina_maries_cafe():
    """Tina Marie's DOWNTOWN CAFE corner storefront (tan upper, black lower, pink/red window neon, gal_065/gal_066)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (218, 192, 148))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    # Upper sign box 'TM | Tina Marie's / DOWNTOWN CAFE' (gal_066.jpg)
    d.rectangle([136, 46, 376, 102], fill=(32, 30, 34), outline=(224, 128, 152), width=3)
    d.ellipse([144, 52, 188, 96], fill=(238, 234, 228), outline=(218, 86, 118), width=4)
    d.text((166, 74), "TM", font=font(BLACK, 20), fill=(36, 32, 36), anchor="mm")
    d.text((280, 65), "Tina Marie's", font=font(SCRIPT, 28), fill=(248, 240, 236), anchor="mm")
    d.rectangle([198, 80, 364, 96], fill=(214, 72, 112))
    d.text((281, 88), "DOWNTOWN CAFE", font=font(BOLD, 13), fill=(252, 246, 246), anchor="mm")
    # Chrome Art Deco trim + black storefront base
    d.rectangle([0, 124, W, 134], fill=(196, 200, 204))
    d.rectangle([0, 134, W, H], fill=(28, 28, 32))
    # Cafe window with glowing pink script & red 'OPEN FOR BREAKFAST LUNCH DINNER' band!
    d.rectangle([64, 146, W - 64, H - 14], fill=(42, 38, 44), outline=(72, 72, 78), width=4)
    d.text((W // 2, 176), "Tina Marie's", font=font(SCRIPT, 34), fill=(238, 96, 132), anchor="mm")
    gd.text((W // 2, 176), "Tina Marie's", font=font(SCRIPT, 34), fill=(175, 55, 85), anchor="mm")
    d.text((W // 2, 204), "DOWNTOWN CAFE", font=font(BOLD, 16), fill=(238, 236, 232), anchor="mm")
    d.rectangle([70, 218, W - 70, 236], fill=(198, 42, 62))
    d.text((W // 2, 227), "OPEN  FOR  BREAKFAST   LUNCH   DINNER", font=font(BOLD, 14), fill=(252, 244, 214), anchor="mm")
    gd.rectangle([70, 218, W - 70, 236], fill=(130, 24, 36))
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.2))


def california_foothills_mural():
    """Eye St mural next to Tina Marie's Cafe: 'WHERE CREATIVITY BLOOMS' floating umbrellas & poppies (fblk_150)."""
    return load_art("eye_umbrellas_mural.jpg", (512, 256), sat=1.05, contrast=1.05, bright=0.88)


def att_building_facade():
    """Photo-matched 4-story grey-green AT&T Central Office precast facade + blue globe emblem on Eye St (gal_077 & gal_065)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (138, 148, 144))
    d = ImageDraw.Draw(im)
    for gy in range(0, H, 64):
        c = rnd.randint(-4, 4)
        d.rectangle([0, gy, W, gy + 62], fill=(138 + c, 148 + c, 144 + c))
        d.line([(0, gy), (W, gy)], fill=(104, 114, 112), width=2)
        for gx in (28, 108, 188):
            if not (gy < 64 and gx == 108):
                d.rectangle([gx, gy + 14, gx + 40, gy + 50], fill=(56, 66, 72), outline=(168, 176, 174), width=3)
                d.line([(gx + 20, gy + 14), (gx + 20, gy + 50)], fill=(154, 162, 160), width=2)
    # Iconic blue-and-white striped AT&T globe logo near top!
    cx, cy = 128, 34
    d.ellipse([cx - 21, cy - 21, cx + 21, cy + 21], fill=(36, 128, 204))
    for sy in range(-15, 17, 6):
        w = int(math.sqrt(max(0, 21 * 21 - sy * sy)))
        d.line([(cx - w + 3, cy + sy), (cx + w - 3, cy + sy)], fill=(238, 246, 252), width=2)
    return dim(add_noise(im, 4), 0.96)


def jalisco_jewelry():
    """3-story historic Chester Ave facade with green awning & 'Jalisco JEWELRY' heart sign (19th & Chester, gal_081.jpg)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (224, 218, 208))
    d = ImageDraw.Draw(im)
    for wy in (22, 82):
        for wx in range(28, W - 28, 76):
            d.rectangle([wx, wy, wx + 46, wy + 46], fill=(186, 182, 174), outline=(152, 146, 138), width=3)
            d.line([(wx + 23, wy), (wx + 23, wy + 46)], fill=(142, 136, 128), width=2)
    d.rectangle([0, 140, W, 150], fill=(168, 156, 138))
    d.rectangle([0, 150, W, H], fill=(198, 186, 166))
    # Signbox 'Jalisco JEWELERS' with red heart + forest-green awning!
    d.rectangle([136, 154, 376, 186], fill=(242, 238, 228), outline=(154, 138, 112), width=3)
    d.text((216, 170), "Jalisco", font=font(SERIF, 24), fill=(34, 54, 108), anchor="mm")
    d.polygon([(266, 166), (272, 160), (278, 166), (272, 176)], fill=(198, 36, 42))
    d.text((326, 170), "JEWELRY", font=font(BOLD, 15), fill=(34, 54, 108), anchor="mm")
    d.rectangle([16, 190, W - 16, 214], fill=(24, 92, 64))
    d.rectangle([28, 214, W - 28, H - 6], fill=(42, 38, 38), outline=(128, 42, 42), width=3)
    return dim(add_noise(im, 4), 0.95)


def woolworths_bank():
    """2-story white commercial building at SW corner of 20th & Chester with tall recessed window bays (gal_063.jpg)."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (228, 228, 226))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=(196, 196, 194))
    # Softly weathered/blurred blue emblem & channel shapes (matching gal_063.jpg without inventing illegible text!)
    sign_layer = Image.new("RGB", (W, 56), (228, 228, 226))
    sd = ImageDraw.Draw(sign_layer)
    sd.rectangle([148, 14, 174, 42], fill=(42, 78, 142))
    for bx, bw in ((186, 54), (248, 68), (324, 48)):
        sd.rectangle([bx, 20, bx + bw, 38], fill=(48, 86, 148))
    im.paste(sign_layer.filter(ImageFilter.GaussianBlur(2.2)), (0, 14))
    for bx in range(36, W - 36, 76):
        d.rectangle([bx, 74, bx + 52, H - 22], fill=(44, 56, 68), outline=(182, 182, 180), width=4)
        for gy in (116, 158, 198):
            d.line([(bx, gy), (bx + 52, gy)], fill=(168, 172, 176), width=2)
    d.rectangle([0, H - 22, W, H], fill=(128, 68, 58))
    return dim(add_noise(im, 4), 0.95)


def encore_boutique():
    """Photo-matched Encore! Boutique: white wall, red-framed upper window, sage-green sign & coral awning (Wall St, gal_095.jpg)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (242, 240, 236))
    d = ImageDraw.Draw(im)
    # Red-orange framed upper 6-pane window (top of gal_095.jpg!)
    d.rectangle([34, 16, W - 20, 108], fill=(244, 244, 242), outline=(216, 86, 68), width=7)
    d.rectangle([42, 24, 148, 100], fill=(72, 84, 92), outline=(146, 156, 152), width=4)
    d.line([(95, 24), (95, 100)], fill=(184, 190, 186), width=4)
    d.line([(42, 62), (148, 62)], fill=(184, 190, 186), width=3)
    # Sage-green curved signboard reading 'Encore! Boutique'
    d.rounded_rectangle([16, 122, W - 12, 176], radius=16, fill=(124, 158, 148))
    d.text((74, 148), "Encore!", font=font(SCRIPT, 26), fill=(248, 248, 246), anchor="mm")
    d.text((186, 149), "Boutique", font=font(BOLD, 18), fill=(248, 248, 246), anchor="mm")
    # Coral-red dome awning + boutique display window + red baseboard
    d.rectangle([18, 168, W - 12, 202], fill=(214, 106, 86))
    d.rectangle([24, 202, W - 18, H - 10], fill=(58, 64, 66), outline=(218, 218, 214), width=3)
    d.rectangle([0, H - 10, W, H], fill=(212, 84, 68))
    return dim(add_noise(im, 3), 0.96)


def garage_spandrel():
    """Photo-sampled tan split-face concrete block & open parking deck spandrel on Wall St (gal_095.jpg)."""
    W, H = 256, 256
    blk = quad_sample("gal_095.jpg", [(120, 320), (120, 395), (195, 395), (195, 320)], size=(W, H), sat=1.08, contrast=1.15, bright=0.98)
    blk = make_seamless(blk, 36)
    d = ImageDraw.Draw(blk)
    # Two parking deck levels per 256px tile: open dark interior band + tan precast spandrel beam + white columns!
    for ly in (0, 128):
        d.rectangle([18, ly + 8, W - 18, ly + 68], fill=(38, 36, 34))
        for ry in (ly + 38, ly + 52):
            d.line([(18, ry), (W - 18, ry)], fill=(78, 82, 80), width=2)
        d.rectangle([0, ly + 68, W, ly + 120], outline=(168, 148, 128), width=2)
        for by in range(ly + 72, ly + 120, 12):
            d.line([(0, by), (W, by)], fill=(164, 144, 124), width=1)
    for cx in (0, 122, W - 16):
        d.rectangle([cx, 0, cx + 16, H], fill=(232, 228, 222))
    return dim(add_noise(blk, 3), 0.96)


def nile_blade():
    """Vertical Art Deco 'NILE' theater blade sign on 19th St (gal_031.jpg)."""
    W, H = 128, 256
    im = Image.new("RGB", (W, H), (224, 212, 184))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)
    d.rectangle([8, 8, W - 9, H - 9], fill=(42, 46, 58), outline=(214, 176, 98), width=6)
    for idx, ch in enumerate("NILE"):
        cy = 44 + idx * 54
        d.text((W // 2, cy), ch, font=font(BLACK, 44), fill=(252, 226, 152), anchor="mm")
        gd.text((W // 2, cy), ch, font=font(BLACK, 44), fill=(195, 155, 75), anchor="mm")
    return add_noise(im, 3), glow.filter(ImageFilter.GaussianBlur(1.4))


def padre_hotel_facade():
    """8-story cream Spanish Revival Padre Hotel window grid (visible looking south down H St in gal_016 & gal_037)."""
    W, H = 256, 256
    im = Image.new("RGB", (W, H), (228, 222, 208))
    d = ImageDraw.Draw(im)
    for wy in range(18, H - 18, 60):
        for wx in range(20, W - 20, 58):
            d.rectangle([wx, wy, wx + 32, wy + 40], fill=(56, 62, 68), outline=(176, 168, 152), width=3)
            d.line([(wx, wy + 20), (wx + 32, wy + 20)], fill=(214, 208, 196), width=2)
    return dim(add_noise(im, 5), 0.95)


def padre_rooftop_sign():
    """Alpha-cutout rooftop framework sign 'PADRE HOTEL' on the 18th & H St skyline (gal_016.jpg)."""
    W, H = 256, 128
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Steel scaffold struts
    for sx in (24, 92, 164, 232):
        d.line([(sx, H), (sx, 14)], fill=(78, 78, 82, 255), width=4)
    for sy in (28, 68, 108):
        d.line([(16, sy), (W - 16, sy)], fill=(78, 78, 82, 255), width=3)
    d.text((W // 2, 42), "PADRE", font=font(BLACK, 42), fill=(218, 54, 48, 255), anchor="mm")
    d.text((W // 2, 88), "HOTEL", font=font(BLACK, 40), fill=(218, 54, 48, 255), anchor="mm")
    return im


def do_not_enter_sign():
    """Crisp red-and-white 'DO NOT ENTER' street sign (Service St, 19th & Eye, Wall St — gal_065, gal_095, gal_103)."""
    S = 128
    im = Image.new("RGB", (S, S), (242, 242, 240))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, S - 3, S - 3], outline=(160, 160, 160), width=3)
    d.ellipse([10, 10, S - 11, S - 11], fill=(204, 34, 36))
    d.rectangle([22, 54, S - 23, 74], fill=(248, 248, 246))
    d.text((S // 2, 34), "DO NOT", font=font(BLACK, 18), fill=(248, 248, 246), anchor="mm")
    d.text((S // 2, 94), "ENTER", font=font(BLACK, 18), fill=(248, 248, 246), anchor="mm")
    return add_noise(im, 2)


def street_blade(label):
    """Downtown Bakersfield mast-arm street-name sign (dark teal/black with Bakersfield crest & white serif/sans text, gal_025/037)."""
    W, H = 256, 64
    im = Image.new("RGB", (W, H), (26, 44, 42))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, W - 4, H - 4], outline=(232, 234, 230), width=3)
    # Sunburst city emblem on left (seen in gal_025.jpg '19th Street' & gal_037.jpg '21st Street'!)
    d.rectangle([8, 8, 48, H - 9], fill=(38, 66, 62), outline=(214, 196, 138), width=2)
    for k in range(7):
        a = -math.pi / 2 + (k - 3) * 0.35
        d.line([(28, 46), (28 + math.cos(a) * 18, 46 + math.sin(a) * 18)], fill=(238, 206, 118), width=2)
    d.text((148, H // 2), label, font=font(BOLD, 28), fill=(246, 246, 242), anchor="mm")
    return add_noise(im, 2)


def road_name_stencil(label):
    """Asphalt pavement with painted white street-name legend (matching 'H St', '20th St', 'Eye St', 'Chester Ave', 'Wall St')."""
    W, H = 256, 128
    im = Image.new("RGB", (W, H), (108, 110, 114))
    d = ImageDraw.Draw(im)
    for _ in range(120):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        c = rnd.randint(-10, 10)
        d.ellipse([x, y, x + rnd.randint(6, 20), y + rnd.randint(4, 14)], fill=(108 + c, 110 + c, 114 + c))
    d.text((W // 2, H // 2), label, font=font(BLACK, 40), fill=(228, 228, 222), anchor="mm")
    return dim(add_noise(im, 5).filter(ImageFilter.GaussianBlur(0.4)), 0.88)


def brick_paver_band():
    """Photo-matched terracotta-red brick sidewalk border / crosswalk accent paving (gal_013, gal_066, gal_081)."""
    S = 128
    im = Image.new("RGB", (S, S), (178, 92, 74))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 16):
        d.line([(0, y), (S, y)], fill=(128, 64, 52), width=2)
        off = 0 if (y // 16) % 2 == 0 else 16
        for x in range(off, S, 32):
            c = rnd.randint(-12, 12)
            d.rectangle([x + 1, y + 2, x + 30, y + 14], fill=(178 + c, 92 + c, 74 + c))
            d.line([(x, y), (x, y + 16)], fill=(128, 64, 52), width=2)
    return dim(add_noise(im, 4), 0.92)


def steel_lattice():
    """Alpha-cutout galvanized steel X-braced lattice tower panel ({fn_lattice — 140ft telecom tower in gal_015/043/055/103)."""
    W, H = 128, 128
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    st = (156, 164, 174, 255)
    dk = (108, 116, 126, 255)
    # Corner legs, horizontal girts & X-diagonals
    d.rectangle([0, 0, 8, H], fill=st)
    d.rectangle([W - 8, 0, W, H], fill=st)
    for y in (0, 64, H - 6):
        d.rectangle([0, y, W, y + 6], fill=dk)
    for y0, y1 in ((4, 64), (68, 124)):
        d.line([(6, y0), (W - 6, y1)], fill=st, width=5)
        d.line([(W - 6, y0), (6, y1)], fill=dk, width=5)
    return im


def fox_vestibule_poster():
    """Triple bronze-and-gold Fox vestibule poster case showing ALI SIDDIQ, SUPER LOVE JAM & COMEDY NIGHT (gal_020.jpg)."""
    W, H = 512, 256
    im = load_art("fox_posters_trio.jpg", (W, H), crop=(68, 42, 1308, 714), sat=1.06, contrast=1.06, bright=0.90)
    # Tint any light backdrop above the stepped Art Deco crown to match Fox vestibule cream stucco
    px = im.load()
    for y in range(28):
        for x in range(W):
            r, g, b = px[x, y]
            if r > 195 and g > 195 and b > 195:
                px[x, y] = (198, 188, 168)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(156, 124, 62), width=4)
    # Warm backlit poster interior glow (dimmed so dark poster shadows stay rich)
    glow = ImageEnhance.Brightness(im).enhance(0.32)
    gd = ImageDraw.Draw(glow)
    gd.rectangle([0, 0, W - 1, 20], fill=(0, 0, 0))
    gd.rectangle([0, H - 17, W - 1, H - 1], fill=(0, 0, 0))
    gd.rectangle([0, 0, 16, H - 1], fill=(0, 0, 0))
    gd.rectangle([W - 17, 0, W - 1, H - 1], fill=(0, 0, 0))
    return im, glow.filter(ImageFilter.GaussianBlur(1.4))


def fox_boxoffice_valance():
    """Central built-in Box Office window & Art Deco diamond-quilted stainless kickplate (gal_020, gal_111, gal_112)."""
    W, H = 192, 256
    im = Image.new("RGB", (W, H), (218, 208, 188))
    d = ImageDraw.Draw(im)
    # Gilded Art Deco scrollwork header frieze
    d.rectangle([4, 4, W - 5, 28], fill=(168, 132, 62), outline=(112, 84, 34), width=2)
    for sx in range(16, W - 16, 28):
        d.arc([sx, 8, sx + 22, 24], 0, 360, fill=(232, 198, 114), width=2)
    # Bronze window frame & dark glass
    d.rectangle([8, 28, W - 9, 178], fill=(38, 44, 52), outline=(182, 148, 78), width=5)
    # Crimson pleated velvet valance inside upper window (gal_020.jpg!)
    d.rectangle([14, 34, W - 15, 82], fill=(172, 34, 34))
    for x in range(20, W - 18, 12):
        d.line([(x, 34), (x, 82)], fill=(116, 18, 20), width=2)
        d.line([(x + 4, 34), (x + 4, 82)], fill=(204, 54, 52), width=1)
    d.rectangle([14, 78, W - 15, 84], fill=(212, 176, 90))
    # Brass circular speaking port & deal tray
    cx = W // 2
    d.ellipse([cx - 20, 112, cx + 20, 152], fill=(64, 56, 44), outline=(206, 170, 88), width=4)
    for r in (8, 14):
        d.ellipse([cx - r, 132 - r, cx + r, 132 + r], outline=(188, 152, 74), width=1)
    d.rectangle([4, 176, W - 5, 186], fill=(198, 188, 168), outline=(128, 116, 98), width=2)
    # Signature Art Deco diamond-quilted brushed stainless-steel kickplate below counter (gal_111/112!)
    d.rectangle([8, 186, W - 9, H - 6], fill=(158, 164, 170), outline=(112, 118, 124), width=3)
    step = 24
    for y in range(186, H - 14, 21):
        for x in range(12, 180, step):
            xm, ym = x + step // 2, y + 10
            d.polygon([(xm, y + 1), (x + step - 2, ym), (xm, y + 19), (x + 2, ym)],
                      fill=(176, 182, 188), outline=(118, 124, 130))
            d.line([(x + 4, ym), (xm, y + 3)], fill=(214, 220, 226), width=1)
    return dim(add_noise(im, 3), 0.94)


def fox_men_sign():
    """Gold-mounted slate-grey Art Deco 'MEN' restroom blade sign on the Mezzanine (gal_114.jpg top right)."""
    W, H = 128, 64
    im = Image.new("RGB", (W, H), (176, 142, 64))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=(198, 162, 74))
    d.rounded_rectangle([10, 12, W - 10, H - 6], radius=10, fill=(76, 86, 88), outline=(218, 194, 132), width=3)
    d.text((W // 2, 36), "MEN", font=font(SERIF, 24), fill=(238, 232, 214), anchor="mm")
    return add_noise(im, 2)


def build_neighborhood_textures():
    mq_s, mq_s_g = fox_marquee_board([["ALI SIDDIQ", "IN THE SHADOWS TOUR", "FEB 14"]], w=512, h=160)
    mq_e, mq_e_g = fox_marquee_board(
        [[], ["BABY BASH MC", "MAGIC LIL ROB", "FEB 15"], ["CARLOS MENCIA", "", "FEB 20"]], w=768, h=160
    )
    mq_b, mq_b_g = fox_marquee_board([[]], w=256, h=160)
    vp, vp_g = fox_vestibule_poster()
    tc, tc_g = today_cleaners_fascia()
    tm, tm_g = tina_maries_cafe()
    nb, nb_g = nile_blade()

    tex = {
        # Upgraded Fox Theater photo-matched textures
        "fx_lobcarp": fox_photo_carpet(),
        "fx_lobceil": fox_fresco_ceiling(),
        "fx_terrazzo": fox_feb2026_terrazzo(),
        "fx_mqwing": fox_marquee_chevron(),
        "fx_mqgold": fox_marquee_gold_ribs(),
        "fx_mqfront": mq_s,
        "fx_mqside": mq_e,
        "fx_mqblank": mq_b,
        "fx_post26": vp,
        "fx_boxval": fox_boxoffice_valance(),
        "fx_mensign": fox_men_sign(),
        "fx_awnred": awning_solid((186, 62, 54), (138, 40, 36)),
        "fx_peach": dim(add_noise(Image.new("RGB", (128, 128), (224, 158, 122)), 5), 0.95),
        "fx_transom": hst_transom_arch(),
        "{fx_irongld": gold_wrought_iron(),
        # 1:1 Surrounding Neighborhood photo-sampled & photo-matched textures
        "fn_stone": stacked_stone_2000h(),
        "fn_bwawn": bw_striped_awning(),
        "fn_darkgl": dark_storefront_glass(),
        "fn_legion": american_legion_sign(),
        "fn_usflag": us_flag_mural(),
        "fn_cleaners": tc,
        "fn_tevis": tevis_brick_wall(),
        "fn_redbrk": red_brick(),
        "fn_pge": pge_sign(),
        "fn_tegeler": tegeler_wall(),
        "fn_tegsign": tegeler_sign(),
        "fn_linos": linos_ribbon(),
        "fn_awnblk": awning_solid((38, 40, 44), (22, 24, 28)),
        "fn_jones": jones_building(),
        "fn_coffee": coffee_awning(),
        "fn_substat": substation_facade(),
        "fn_jinsushi": jin_sushi_facade(),
        "fn_tossit": toss_it_facade(),
        "fn_tinam": tm,
        "fn_mural": california_foothills_mural(),
        "fn_att": att_building_facade(),
        "fn_jalisco": jalisco_jewelry(),
        "fn_woolw": woolworths_bank(),
        "fn_encore": encore_boutique(),
        "fn_garage": garage_spandrel(),
        "fn_nile": nb,
        "fn_padre": padre_hotel_facade(),
        "{fn_padresg": padre_rooftop_sign(),
        "fn_dne": do_not_enter_sign(),
        "fn_st_20th": street_blade("20th Street"),
        "fn_st_19th": street_blade("19th Street"),
        "fn_st_21st": street_blade("21st Street"),
        "fn_st_hst": street_blade("H Street"),
        "fn_st_eye": street_blade("Eye Street"),
        "fn_st_ches": street_blade("Chester Ave"),
        "fn_rd_hst": road_name_stencil("H ST"),
        "fn_rd_20th": road_name_stencil("20TH ST"),
        "fn_rd_eye": road_name_stencil("EYE ST"),
        "fn_rd_ches": road_name_stencil("CHESTER"),
        "fn_rd_wall": road_name_stencil("WALL ST"),
        "fn_brkpave": brick_paver_band(),
        "{fn_lattice": steel_lattice(),
        "{fx_foxscr": fox_script_cutout(),
    }
    glows = {
        "fx_mqfront": mq_s_g,
        "fx_mqside": mq_e_g,
        "fx_mqblank": mq_b_g,
        "fx_post26": vp_g,
        "fn_cleaners": tc_g,
        "fn_tinam": tm_g,
        "fn_nile": nb_g,
    }
    return tex, glows
