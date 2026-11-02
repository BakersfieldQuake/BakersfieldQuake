"""build_fox_models.py — Procedural smooth-shaded 3D MD3 prop & vehicle builder for Fox Theater,
The Padre Hotel, and Downtown Bakersfield (fox.bsp).

Generates:
  - G:/Quake/Combat/BakersfieldQuake/progs/fox/fox_materials.png (+ _glow.png)
  - G:/Quake/Combat/BakersfieldQuake/progs/fox/get_bus_tex.png   (+ _glow.png)
  - 29 smooth-shaded .md3 models + .md3_0.skin files in progs/fox/
  - G:/Quake/Combat/BakersfieldQuake/scripts/fox_props.shader

All dimensions are authored in feet and scaled by FT = 12.0 Quake units/ft.
Orientation convention at angles = '0 0 0' (yaw = 0):
  +X = forward (front of chair/bed/machine/bus), +Y = left, +Z = up.
"""
from __future__ import annotations
import math
import os
import random
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib  # noqa: E402

MOD_DIR = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(MOD_DIR, "progs", "fox")
SHADER_PATH = os.path.join(MOD_DIR, "scripts", "fox_props.shader")

FT = 12.0  # 12 Quake units per foot


def _font(size: int, bold: bool = True, serif: bool = False, script: bool = False):
    if script:
        cands = ["brushsci.ttf", "segoesc.ttf", "vladimir.ttf", "georgiaz.ttf", "arialbd.ttf"]
    elif serif:
        cands = ["georgiab.ttf", "timesbd.ttf", "georgia.ttf", "arialbd.ttf"]
    elif bold:
        cands = ["ariblk.ttf", "arialbd.ttf", "calibrib.ttf"]
    else:
        cands = ["arial.ttf", "calibri.ttf"]
    for c in cands:
        for pref in ("C:/Windows/Fonts/", ""):
            try:
                return ImageFont.truetype(pref + c, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ==============================================================================
# 1. PROCEDURAL 1024x1024 MATERIAL ATLAS + GLOW ATLAS
# ==============================================================================
# 4x4 grid of 256x256 tiles; UV helper insets by 14px so mipmaps never bleed.
ATLAS_SZ = 1024
TILE_SZ = 256


def tile_uv(col: int, row: int, pad: float = 14.0) -> tuple[float, float, float, float]:
    u0 = (col * TILE_SZ + pad) / ATLAS_SZ
    v0 = (row * TILE_SZ + pad) / ATLAS_SZ
    u1 = ((col + 1) * TILE_SZ - pad) / ATLAS_SZ
    v1 = ((row + 1) * TILE_SZ - pad) / ATLAS_SZ
    return (u0, v0, u1, v1)


def subtile_uv(col: int, row: int, sx: int, sy: int, pad: float = 8.0) -> tuple[float, float, float, float]:
    """2x2 sub-quadrant (128x128) inside a 256x256 tile."""
    half = TILE_SZ // 2
    x0 = col * TILE_SZ + sx * half + pad
    y0 = row * TILE_SZ + sy * half + pad
    x1 = col * TILE_SZ + (sx + 1) * half - pad
    y1 = row * TILE_SZ + (sy + 1) * half - pad
    return (x0 / ATLAS_SZ, y0 / ATLAS_SZ, x1 / ATLAS_SZ, y1 / ATLAS_SZ)


UV_YELLOW_TUFT = tile_uv(0, 0)
UV_WHITE_LINEN = tile_uv(1, 0)
UV_COGNAC_TUFT = tile_uv(2, 0)
UV_RED_TUFT = tile_uv(3, 0)

UV_ESPRESSO_LTH = tile_uv(0, 1)
UV_HOUNDSTOOTH = tile_uv(1, 1)
UV_DARK_WOOD = tile_uv(2, 1)
UV_CHROME = tile_uv(3, 1)

UV_BRASS = tile_uv(0, 2)
UV_BRONZE = tile_uv(1, 2)
UV_WHITE_GLOSS = tile_uv(2, 2)
UV_SILVER_MOSAIC = tile_uv(3, 2)

UV_GREEN_FELT = tile_uv(0, 3)
# Palm bark (bottom half of (1,3)) & Palm shag skirt (top half of (1,3))
UV_PALM_SHAG = (
    (1 * TILE_SZ + 14) / ATLAS_SZ,
    (3 * TILE_SZ + 12) / ATLAS_SZ,
    (2 * TILE_SZ - 14) / ATLAS_SZ,
    (3 * TILE_SZ + 116) / ATLAS_SZ,
)
UV_PALM_BARK = (
    (1 * TILE_SZ + 14) / ATLAS_SZ,
    (3 * TILE_SZ + 140) / ATLAS_SZ,
    (2 * TILE_SZ - 14) / ATLAS_SZ,
    (4 * TILE_SZ - 12) / ATLAS_SZ,
)
UV_PALM_FROND = tile_uv(2, 3, pad=10.0)

# Specialty / Emissive sub-tiles in (3, 3):
UV_WARM_LAMP = subtile_uv(3, 3, 0, 0, pad=10.0)
UV_HEATER_GLOW = (
    (3 * TILE_SZ + 128 + 8) / ATLAS_SZ,
    (3 * TILE_SZ + 8) / ATLAS_SZ,
    (4 * TILE_SZ - 8) / ATLAS_SZ,
    (3 * TILE_SZ + 60) / ATLAS_SZ,
)
UV_WATER_BLUE = (
    (3 * TILE_SZ + 128 + 8) / ATLAS_SZ,
    (3 * TILE_SZ + 68) / ATLAS_SZ,
    (3 * TILE_SZ + 190) / ATLAS_SZ,
    (3 * TILE_SZ + 122) / ATLAS_SZ,
)
UV_GYM_SCREEN = (
    (3 * TILE_SZ + 196) / ATLAS_SZ,
    (3 * TILE_SZ + 68) / ATLAS_SZ,
    (4 * TILE_SZ - 8) / ATLAS_SZ,
    (3 * TILE_SZ + 122) / ATLAS_SZ,
)
UV_CLOCK_DIAL = subtile_uv(3, 3, 0, 1, pad=4.0)
UV_BLACK_CLOTH = (
    (3 * TILE_SZ + 128 + 8) / ATLAS_SZ,
    (3 * TILE_SZ + 128 + 8) / ATLAS_SZ,
    (3 * TILE_SZ + 190) / ATLAS_SZ,
    (4 * TILE_SZ - 8) / ATLAS_SZ,
)
UV_ORANGE_ACCENT = (
    (3 * TILE_SZ + 196) / ATLAS_SZ,
    (3 * TILE_SZ + 128 + 8) / ATLAS_SZ,
    (4 * TILE_SZ - 8) / ATLAS_SZ,
    (3 * TILE_SZ + 190) / ATLAS_SZ,
)
UV_SUNBURST = (
    (3 * TILE_SZ + 196) / ATLAS_SZ,
    (3 * TILE_SZ + 196) / ATLAS_SZ,
    (4 * TILE_SZ - 8) / ATLAS_SZ,
    (4 * TILE_SZ - 8) / ATLAS_SZ,
)


def _draw_tufted(base_rgb: tuple[int, int, int], seed: int) -> Image.Image:
    im = Image.new("RGB", (TILE_SZ, TILE_SZ), base_rgb)
    px = im.load()
    rng = random.Random(seed)
    step = 64
    for y in range(TILE_SZ):
        for x in range(TILE_SZ):
            # Pillow puffiness inside each diamond
            u = ((x + y) % step) / step - 0.5
            v = ((x - y) % step) / step - 0.5
            puff = 1.0 - 1.35 * (u * u + v * v)
            n = rng.randint(-5, 5)
            s = max(0.62, min(1.14, 0.86 + 0.24 * puff))
            px[x, y] = tuple(max(0, min(255, int(c * s) + n)) for c in base_rgb)
    d = ImageDraw.Draw(im)
    dark = tuple(max(0, int(c * 0.52)) for c in base_rgb)
    hi = tuple(min(255, int(c * 1.18)) for c in base_rgb)
    for k in range(-TILE_SZ, TILE_SZ * 2, step):
        d.line([(k, 0), (k + TILE_SZ, TILE_SZ)], fill=dark, width=2)
        d.line([(k, TILE_SZ), (k + TILE_SZ, 0)], fill=dark, width=2)
    for gy in range(0, TILE_SZ + 1, step // 2):
        for gx in range(0, TILE_SZ + 1, step // 2):
            if ((gx + gy) // (step // 2)) % 2 == 0:
                d.ellipse([gx - 5, gy - 5, gx + 5, gy + 5], fill=dark, outline=hi, width=1)
    return im


def build_material_atlas() -> tuple[Image.Image, Image.Image]:
    atlas = Image.new("RGB", (ATLAS_SZ, ATLAS_SZ), (64, 64, 64))
    glow = Image.new("RGB", (ATLAS_SZ, ATLAS_SZ), (0, 0, 0))
    rng = random.Random(20261101)

    def paste_tile(col: int, row: int, im: Image.Image):
        atlas.paste(im, (col * TILE_SZ, row * TILE_SZ))

    # (0,0) Mustard tufted leather
    paste_tile(0, 0, _draw_tufted((218, 178, 52), 101))

    # (1,0) Crisp quilted hotel white linen
    linen = Image.new("RGB", (TILE_SZ, TILE_SZ), (242, 240, 235))
    ld = ImageDraw.Draw(linen)
    for y in range(0, TILE_SZ, 32):
        ld.line([(0, y), (TILE_SZ, y)], fill=(224, 221, 214), width=2)
    for x in range(0, TILE_SZ, 32):
        ld.line([(x, 0), (x, TILE_SZ)], fill=(228, 225, 218), width=1)
    paste_tile(1, 0, linen)

    # (2,0) Cognac Chesterfield leather
    paste_tile(2, 0, _draw_tufted((158, 88, 44), 102))

    # (3,0) Crimson tufted leather
    paste_tile(3, 0, _draw_tufted((182, 32, 38), 103))

    # (0,1) Espresso / charcoal leather
    esp = Image.new("RGB", (TILE_SZ, TILE_SZ), (58, 54, 52))
    epx = esp.load()
    for y in range(TILE_SZ):
        for x in range(TILE_SZ):
            n = rng.randint(-6, 6) + int(3 * math.sin(x * 0.25) * math.cos(y * 0.25))
            epx[x, y] = (max(0, 58 + n), max(0, 54 + n), max(0, 52 + n))
    paste_tile(0, 1, esp)

    # (1,1) Houndstooth wool upholstery
    ht = Image.new("RGB", (TILE_SZ, TILE_SZ), (228, 224, 214))
    hd = ImageDraw.Draw(ht)
    blk = (34, 34, 38)
    cell = 16
    for y in range(0, TILE_SZ, cell):
        for x in range(0, TILE_SZ, cell):
            hd.rectangle([x, y, x + cell // 2 - 1, y + cell // 2 - 1], fill=blk)
            hd.polygon([(x + cell // 2, y), (x + cell, y), (x + cell // 2, y + cell // 2)], fill=blk)
            hd.polygon([(x, y + cell // 2), (x + cell // 2, y + cell // 2), (x, y + cell)], fill=blk)
    paste_tile(1, 1, ht)

    # (2,1) Dark walnut wood grain
    wd = Image.new("RGB", (TILE_SZ, TILE_SZ), (82, 52, 34))
    wpx = wd.load()
    for y in range(TILE_SZ):
        grain = int(10 * math.sin(y * 0.22 + 2.0 * math.sin(y * 0.05)))
        for x in range(TILE_SZ):
            n = rng.randint(-4, 4) + grain + int(3 * math.sin(x * 0.08))
            wpx[x, y] = (max(0, min(255, 86 + n)), max(0, min(255, 54 + (n * 2) // 3)), max(0, min(255, 35 + n // 2)))
    paste_tile(2, 1, wd)

    # (3,1) Brushed silver / chrome steel
    ch = Image.new("RGB", (TILE_SZ, TILE_SZ), (188, 194, 202))
    cd = ImageDraw.Draw(ch)
    for y in range(TILE_SZ):
        s = int(24 * math.sin(y / TILE_SZ * math.pi * 2.0))
        c = (max(0, min(255, 186 + s)), max(0, min(255, 192 + s)), max(0, min(255, 200 + s)))
        cd.line([(0, y), (TILE_SZ, y)], fill=c)
    paste_tile(3, 1, ch)

    # (0,2) Burnished antique brass / gold
    br = Image.new("RGB", (TILE_SZ, TILE_SZ), (206, 168, 76))
    bd = ImageDraw.Draw(br)
    for y in range(TILE_SZ):
        s = int(26 * math.sin(y / TILE_SZ * math.pi * 3.0))
        bd.line([(0, y), (TILE_SZ, y)], fill=(min(255, 204 + s), min(255, 166 + s), max(0, 74 + s // 2)))
    paste_tile(0, 2, br)

    # (1,2) Aged cast-iron / dark bronze
    bz = Image.new("RGB", (TILE_SZ, TILE_SZ), (72, 58, 44))
    bzpx = bz.load()
    for y in range(TILE_SZ):
        for x in range(TILE_SZ):
            n = rng.randint(-6, 6)
            bzpx[x, y] = (72 + n, 58 + n, 44 + n)
    paste_tile(1, 2, bz)

    # (2,2) Glossy white acrylic / Tolix enamel
    wg = Image.new("RGB", (TILE_SZ, TILE_SZ), (236, 238, 240))
    wgd = ImageDraw.Draw(wg)
    for y in range(TILE_SZ):
        s = int(8 * math.cos(y / TILE_SZ * math.pi * 2.0))
        wgd.line([(0, y), (TILE_SZ, y)], fill=(min(255, 236 + s), min(255, 238 + s), min(255, 240 + s)))
    paste_tile(2, 2, wg)

    # (3,2) Silver-pewter mosaic tile (suite Jacuzzi surround)
    mos = Image.new("RGB", (TILE_SZ, TILE_SZ), (156, 162, 168))
    md = ImageDraw.Draw(mos)
    for y in range(0, TILE_SZ, 16):
        for x in range(0, TILE_SZ, 24):
            v = rng.randint(128, 198)
            md.rectangle([x + 1, y + 1, x + 22, y + 14], fill=(v, min(255, v + 4), min(255, v + 8)))
    paste_tile(3, 2, mos)

    # (0,3) Tournament green billiard felt / green bike-rack enamel
    grn = Image.new("RGB", (TILE_SZ, TILE_SZ), (34, 126, 72))
    gpx = grn.load()
    for y in range(TILE_SZ):
        for x in range(TILE_SZ):
            n = rng.randint(-5, 5)
            gpx[x, y] = (max(0, 34 + n), max(0, 126 + n), max(0, 72 + n))
    paste_tile(0, 3, grn)

    # (1,3) Palm shag skirt (top half) + ringed palm trunk bark (bottom half)
    plm = Image.new("RGB", (TILE_SZ, TILE_SZ), (122, 102, 78))
    pd = ImageDraw.Draw(plm)
    # Top half: golden-tan fibrous petticoat shag
    pd.rectangle([0, 0, TILE_SZ, 128], fill=(168, 138, 92))
    for x in range(0, TILE_SZ, 4):
        c = rng.randint(-22, 22)
        pd.line([(x, 0), (x + rng.randint(-4, 4), 128)], fill=(168 + c, 138 + c, 92 + c), width=2)
    # Bottom half: ringed grey-brown California fan palm trunk
    for y in range(128, TILE_SZ, 10):
        c = rng.randint(-12, 12)
        pd.rectangle([0, y, TILE_SZ, y + 7], fill=(124 + c, 108 + c, 92 + c))
        pd.line([(0, y + 8), (TILE_SZ, y + 8)], fill=(78, 66, 54), width=2)
    paste_tile(1, 3, plm)

    # (2,3) California Fan Palm leaf frond (sunlit olive-emerald pleated ribs)
    frd = Image.new("RGB", (TILE_SZ, TILE_SZ), (68, 124, 54))
    fd = ImageDraw.Draw(frd)
    for x in range(0, TILE_SZ, 8):
        shade = 16 if (x // 8) % 2 == 0 else -12
        fd.rectangle([x, 0, x + 7, TILE_SZ], fill=(68 + shade, 126 + shade, 54 + shade // 2))
    fd.rectangle([TILE_SZ // 2 - 5, 0, TILE_SZ // 2 + 5, TILE_SZ], fill=(124, 152, 68))
    paste_tile(2, 3, frd)

    # (3,3) Specialty & Emissive 2x2 sub-quadrants
    spec = Image.new("RGB", (TILE_SZ, TILE_SZ), (32, 32, 36))
    sd = ImageDraw.Draw(spec)
    gd = ImageDraw.Draw(glow)
    ox, oy = 3 * TILE_SZ, 3 * TILE_SZ

    # sub(0,0): Warm frosted lamp / chandelier amber-cream diffuser
    sd.rectangle([0, 0, 127, 127], fill=(252, 232, 184))
    for y in range(0, 128, 16):
        sd.line([(0, y), (127, y)], fill=(238, 206, 142), width=2)
    gd.rectangle([ox + 2, oy + 2, ox + 125, oy + 125], fill=(195, 158, 96))

    # sub(1,0) top: Patio heater glowing burner emitter; bottom-left: Blue 5-gal water jug; bottom-right: Gym console
    sd.rectangle([128, 0, 255, 63], fill=(248, 128, 48))
    for y in range(4, 62, 8):
        sd.line([(128, y), (255, y)], fill=(142, 46, 22), width=2)
    gd.rectangle([ox + 130, oy + 2, ox + 253, oy + 61], fill=(225, 102, 32))

    sd.rectangle([128, 64, 191, 127], fill=(74, 158, 228))
    sd.line([(142, 66), (142, 125)], fill=(168, 218, 252), width=4)
    sd.rectangle([192, 64, 255, 127], fill=(26, 30, 38))
    sd.rectangle([198, 72, 249, 102], fill=(38, 118, 196))
    sd.rectangle([202, 108, 245, 118], fill=(72, 214, 112))
    gd.rectangle([ox + 198, oy + 72, ox + 249, oy + 102], fill=(36, 98, 165))
    gd.rectangle([ox + 202, oy + 108, ox + 245, oy + 118], fill=(48, 155, 80))

    # sub(0,1): HOPE Street Clock Roman dial (128x128)
    cx, cy = 64, 192
    sd.rectangle([0, 128, 127, 255], fill=(62, 46, 32))
    sd.ellipse([6, 134, 121, 249], fill=(246, 238, 212), outline=(186, 146, 72), width=5)
    gd.ellipse([ox + 10, oy + 138, ox + 117, oy + 245], fill=(150, 132, 92))
    f_rm = _font(11, bold=True, serif=True)
    romans = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    for i, rm in enumerate(romans):
        ang = math.radians(i * 30 - 90)
        rx = cx + math.cos(ang) * 42
        ry = cy + math.sin(ang) * 42
        sd.text((rx, ry), rm, font=f_rm, fill=(28, 22, 18), anchor="mm")
    sd.line([(cx, cy), (cx + 22, cy - 16)], fill=(22, 18, 14), width=4)
    sd.line([(cx, cy), (cx - 28, cy - 24)], fill=(22, 18, 14), width=3)
    sd.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(168, 128, 58))

    # sub(1,1): Black banquet cloth + burnt-orange pillow + sunburst guitar finish
    sd.rectangle([128, 128, 191, 255], fill=(32, 32, 36))
    for x in range(132, 190, 8):
        sd.line([(x, 128), (x, 255)], fill=(20, 20, 24), width=2)
    sd.rectangle([192, 128, 255, 191], fill=(218, 102, 38))
    sd.rectangle([192, 192, 255, 255], fill=(186, 38, 28))
    sd.ellipse([200, 200, 247, 247], fill=(238, 168, 42))

    paste_tile(3, 3, spec)

    # Tone diffuse to 0.68 so DarkPlaces lightingDiffuse (~2x) renders rich, unclipped colors
    atlas = ImageEnhance.Brightness(atlas).enhance(0.68)
    glow = glow.filter(ImageFilter.GaussianBlur(1.2))
    return atlas, glow


# ==============================================================================
# 2. DEDICATED 512x512 'GET BUS' TRANSIT LIVERY TEXTURE + GLOW (fblk_418.jpg)
# ==============================================================================
BUS_SIDE_UV = (0.02, 0.03, 0.98, 0.42)
BUS_FRONT_UV = (0.03, 0.47, 0.47, 0.88)
BUS_REAR_UV = (0.53, 0.47, 0.97, 0.88)
BUS_ROOF_UV = (0.04, 0.91, 0.46, 0.98)
BUS_TIRE_UV = (0.54, 0.90, 0.74, 0.99)
BUS_HUB_UV = (0.78, 0.90, 0.96, 0.99)


def build_bus_texture() -> tuple[Image.Image, Image.Image]:
    W = H = 512
    im = Image.new("RGB", (W, H), (36, 128, 214))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)

    # --- 1) Side Livery Band (y = 0 .. 224): Golden Empire Transit Blue / Yellow / Green ---
    d.rectangle([0, 0, W, 224], fill=(28, 124, 214))
    d.rectangle([0, 0, W, 22], fill=(236, 238, 242))  # White roof rail cap
    # Cursive 'Bakersfield' header & fleet number
    d.text((112, 38), "Bakersfield", font=_font(26, script=True), fill=(244, 248, 255), anchor="mm")
    d.text((438, 38), "GET  21", font=_font(16, bold=True), fill=(246, 222, 84), anchor="mm")
    # Panoramic dark-tinted transit windows + folding doors
    for wx in range(22, 415, 58):
        d.rounded_rectangle([wx, 54, wx + 50, 126], radius=5, fill=(32, 42, 52), outline=(196, 204, 212), width=2)
        d.line([(wx + 6, 118), (wx + 32, 60)], fill=(64, 82, 98), width=3)
    # Front passenger double glass door on right (towards +x front)
    d.rounded_rectangle([438, 54, 488, 188], radius=5, fill=(28, 36, 44), outline=(210, 214, 220), width=3)
    d.line([(463, 54), (463, 188)], fill=(186, 192, 198), width=2)
    # Sweeping Golden Yellow & Kelly Green wave stripes across lower body (fblk_418.jpg!)
    d.polygon([(0, 136), (434, 148), (434, 224), (0, 224)], fill=(242, 198, 42))
    d.polygon([(0, 166), (434, 174), (434, 224), (0, 224)], fill=(54, 168, 76))
    d.text((228, 182), "GET bus", font=_font(34, bold=True), fill=(248, 250, 246), anchor="mm")
    # Amber side marker reflectors
    for mx in (48, 230, 412):
        d.rectangle([mx, 152, mx + 10, 158], fill=(255, 176, 38))
        gd.rectangle([mx, 152, mx + 10, 158], fill=(160, 100, 18))

    # --- 2) Front Cap (x = 8..248, y = 232..456) ---
    fx0, fy0, fx1, fy1 = 8, 232, 248, 456
    fcx = (fx0 + fx1) // 2
    d.rectangle([fx0, fy0, fx1, fy1], fill=(28, 124, 214))
    # Illuminated black/amber LED route headsign: '21 DOWNTOWN'
    d.rounded_rectangle([fx0 + 20, fy0 + 12, fx1 - 20, fy0 + 46], radius=6, fill=(20, 22, 26), outline=(160, 168, 176), width=2)
    d.text((fcx, fy0 + 29), "21 DOWNTOWN", font=_font(19, bold=True), fill=(255, 194, 54), anchor="mm")
    gd.text((fcx, fy0 + 29), "21 DOWNTOWN", font=_font(19, bold=True), fill=(215, 148, 32), anchor="mm")
    # Wide curved dark windshield with wiper blades
    d.rounded_rectangle([fx0 + 14, fy0 + 54, fx1 - 14, fy0 + 142], radius=12, fill=(30, 40, 50), outline=(48, 56, 66), width=4)
    d.line([(fcx, fy0 + 54), (fcx, fy0 + 142)], fill=(44, 52, 60), width=3)
    d.line([(fx0 + 30, fy0 + 128), (fx0 + 82, fy0 + 68)], fill=(68, 86, 104), width=5)
    # Yellow/green front apron + GET emblem + twin glowing headlights + dark transit bumper
    d.rectangle([fx0, fy0 + 148, fx1, fy0 + 178], fill=(242, 198, 42))
    d.rectangle([fx0, fy0 + 178, fx1, fy1], fill=(54, 168, 76))
    d.text((fcx, fy0 + 166), "GET", font=_font(22, bold=True), fill=(24, 68, 138), anchor="mm")
    for hx in (fx0 + 30, fx1 - 30):
        d.ellipse([hx - 14, fy0 + 162, hx + 14, fy0 + 186], fill=(255, 250, 228), outline=(168, 174, 182), width=3)
        gd.ellipse([hx - 12, fy0 + 164, hx + 12, fy0 + 184], fill=(235, 224, 185))
    d.rounded_rectangle([fx0 + 6, fy1 - 28, fx1 - 6, fy1 - 6], radius=6, fill=(36, 38, 42))

    # --- 3) Rear Cap (x = 264..504, y = 232..456) ---
    rx0, ry0, rx1, ry1 = 264, 232, 504, 456
    rcx = (rx0 + rx1) // 2
    d.rectangle([rx0, ry0, rx1, ry1], fill=(28, 124, 214))
    d.rounded_rectangle([rx0 + 48, ry0 + 14, rx1 - 48, ry0 + 42], radius=5, fill=(22, 24, 28))
    d.text((rcx, ry0 + 28), "21", font=_font(18, bold=True), fill=(255, 194, 54), anchor="mm")
    gd.text((rcx, ry0 + 28), "21", font=_font(18, bold=True), fill=(205, 142, 30), anchor="mm")
    # Engine radiator grille louvers & 'GET bus'
    d.rectangle([rx0 + 28, ry0 + 62, rx1 - 28, ry0 + 132], fill=(42, 78, 134), outline=(22, 54, 98), width=3)
    for ly in range(ry0 + 70, ry0 + 128, 8):
        d.line([(rx0 + 34, ly), (rx1 - 34, ly)], fill=(24, 42, 72), width=3)
    d.rectangle([rx0, ry0 + 142, rx1, ry0 + 174], fill=(242, 198, 42))
    d.rectangle([rx0, ry0 + 174, rx1, ry1], fill=(54, 168, 76))
    d.text((rcx, ry0 + 158), "GET bus", font=_font(24, bold=True), fill=(28, 52, 108), anchor="mm")
    # Vertical brake / amber turn taillights
    for tx in (rx0 + 24, rx1 - 24):
        d.ellipse([tx - 10, ry0 + 144, tx + 10, ry0 + 164], fill=(238, 42, 38))
        d.ellipse([tx - 10, ry0 + 168, tx + 10, ry0 + 188], fill=(246, 164, 34))
        gd.ellipse([tx - 9, ry0 + 145, tx + 9, ry0 + 163], fill=(215, 32, 28))
        gd.ellipse([tx - 9, ry0 + 169, tx + 9, ry0 + 187], fill=(195, 118, 22))
    d.rounded_rectangle([rx0 + 6, ry1 - 28, rx1 - 6, ry1 - 6], radius=6, fill=(36, 38, 42))

    # --- 4) Roof White Band + Rubber Tire + Silver Transit Hubcap (y = 460..511) ---
    d.rectangle([0, 460, 256, 511], fill=(236, 238, 242))
    for lx in range(24, 240, 16):
        d.line([(lx, 468), (lx, 504)], fill=(198, 202, 208), width=2)
    # Rubber tire tread/wall (x=264..384)
    d.rectangle([264, 460, 384, 511], fill=(34, 36, 40))
    for tx in range(268, 382, 10):
        d.line([(tx, 460), (tx, 511)], fill=(22, 24, 26), width=3)
    # Hubcap (x=392..504)
    hcx, hcy = 448, 485
    d.rectangle([392, 460, 511, 511], fill=(34, 36, 40))
    d.ellipse([hcx - 23, hcy - 23, hcx + 23, hcy + 23], fill=(186, 192, 200), outline=(96, 102, 110), width=3)
    d.ellipse([hcx - 10, hcy - 10, hcx + 10, hcy + 10], fill=(72, 76, 84))

    im = ImageEnhance.Brightness(im).enhance(0.68)
    glow = glow.filter(ImageFilter.GaussianBlur(1.2))
    return im, glow


# ==============================================================================
# 3. SMOOTH-SHADED 3D MESH BUILDER (IN FEET, CONVERTED TO QUAKE UNITS ON EXPORT)
# ==============================================================================
def _vnorm(v: tuple[float, float, float]) -> tuple[float, float, float]:
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if l < 1e-8:
        return (0.0, 0.0, 1.0)
    return (v[0] / l, v[1] / l, v[2] / l)


def _vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


class Mesh:
    """Procedural 3D triangle mesh builder in feet (+x forward, +y left, +z up)."""

    def __init__(self, shader: str = "progs/fox/fox_materials"):
        self.shader = shader
        self.verts: list[tuple[float, float, float]] = []
        self.norms: list[tuple[float, float, float]] = []
        self.st: list[tuple[float, float]] = []
        self.tris: list[tuple[int, int, int]] = []

    def add_vert(self, p: tuple[float, float, float], n: tuple[float, float, float], uv: tuple[float, float]) -> int:
        idx = len(self.verts)
        self.verts.append(p)
        self.norms.append(_vnorm(n))
        self.st.append(uv)
        return idx

    def add_quad(self, p0, p1, p2, p3, uv_rect, normal=None):
        """p0=TL, p1=TR, p2=BR, p3=BL when viewed from front."""
        u0, v0, u1, v1 = uv_rect
        if normal is None:
            normal = _vnorm(_vcross(_vsub(p3, p0), _vsub(p1, p0)))
        i0 = self.add_vert(p0, normal, (u0, v0))
        i1 = self.add_vert(p1, normal, (u1, v0))
        i2 = self.add_vert(p2, normal, (u1, v1))
        i3 = self.add_vert(p3, normal, (u0, v1))
        self.tris.append((i0, i3, i2))
        self.tris.append((i0, i2, i1))

    def add_box(self, x0, y0, z0, x1, y1, z1, uv_rect, uv_faces: dict | None = None):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        uf = uv_faces or {}
        # +X (front): viewer at +X looking -X -> left=-Y, right=+Y, top=+Z, bot=-Z
        self.add_quad((x1, y0, z1), (x1, y1, z1), (x1, y1, z0), (x1, y0, z0), uf.get("px", uv_rect), (1, 0, 0))
        # -X (back): viewer at -X looking +X -> left=+Y, right=-Y
        self.add_quad((x0, y1, z1), (x0, y0, z1), (x0, y0, z0), (x0, y1, z0), uf.get("nx", uv_rect), (-1, 0, 0))
        # -Y (right side): viewer at -Y looking +Y -> left=-X, right=+X
        self.add_quad((x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0), uf.get("ny", uv_rect), (0, -1, 0))
        # +Y (left side): viewer at +Y looking -Y -> left=+X, right=-X
        self.add_quad((x1, y1, z1), (x0, y1, z1), (x0, y1, z0), (x1, y1, z0), uf.get("py", uv_rect), (0, 1, 0))
        # +Z (top)
        self.add_quad((x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1), uf.get("pz", uv_rect), (0, 0, 1))
        # -Z (bottom)
        self.add_quad((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), uf.get("nz", uv_rect), (0, 0, -1))

    def add_lathe(self, cx: float, cy: float, profile: list[tuple[float, float]], sides: int,
                  uv_rect, cap_bot: bool = True, cap_top: bool = True, scale_xy: tuple[float, float] = (1.0, 1.0)):
        """Smooth surface of revolution around Z axis from (r, z) profile bottom-to-top."""
        u0, v0, u1, v1 = uv_rect
        sx, sy = scale_xy
        m = len(profile)
        # Slope normals per ring
        rz_norms = []
        for j in range(m):
            r_prev, z_prev = profile[max(0, j - 1)]
            r_next, z_next = profile[min(m - 1, j + 1)]
            dr = r_next - r_prev
            dz = z_next - z_prev
            # Tangent is (dr, dz) -> outward normal in (r, z) plane is (dz, -dr)
            nr, nz = dz, -dr
            if abs(nr) < 1e-6 and abs(nz) < 1e-6:
                nr, nz = 1.0, 0.0
            rz_norms.append((nr, nz))

        rings = []
        for j, (r, z) in enumerate(profile):
            vv = v1 - (v1 - v0) * (j / max(1, m - 1))
            nr, nz = rz_norms[j]
            ring = []
            for i in range(sides + 1):
                ang = 2.0 * math.pi * i / sides
                ca, sa = math.cos(ang), math.sin(ang)
                px = cx + r * ca * sx
                py = cy + r * sa * sy
                nx = nr * ca / max(0.05, sx)
                ny = nr * sa / max(0.05, sy)
                uu = u0 + (u1 - u0) * (i / sides)
                ring.append(self.add_vert((px, py, z), (nx, ny, nz), (uu, vv)))
            rings.append(ring)

        for j in range(m - 1):
            r0_idx, r1_idx = rings[j], rings[j + 1]
            for i in range(sides):
                a, b = r0_idx[i], r0_idx[i + 1]
                c, d = r1_idx[i + 1], r1_idx[i]
                self.tris.append((a, b, c))
                self.tris.append((a, c, d))

        uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
        du, dv = 0.45 * (u1 - u0), 0.45 * (v1 - v0)
        if cap_bot and profile[0][0] > 1e-4:
            r0, z0 = profile[0]
            c_idx = self.add_vert((cx, cy, z0), (0, 0, -1), (uc, vc))
            c_ring = []
            for i in range(sides):
                ang = 2.0 * math.pi * i / sides
                ca, sa = math.cos(ang), math.sin(ang)
                c_ring.append(self.add_vert((cx + r0 * ca * sx, cy + r0 * sa * sy, z0), (0, 0, -1), (uc + du * ca, vc + dv * sa)))
            for i in range(sides):
                self.tris.append((c_idx, c_ring[(i + 1) % sides], c_ring[i]))

        if cap_top and profile[-1][0] > 1e-4:
            r1, z1 = profile[-1]
            c_idx = self.add_vert((cx, cy, z1), (0, 0, 1), (uc, vc))
            c_ring = []
            for i in range(sides):
                ang = 2.0 * math.pi * i / sides
                ca, sa = math.cos(ang), math.sin(ang)
                c_ring.append(self.add_vert((cx + r1 * ca * sx, cy + r1 * sa * sy, z1), (0, 0, 1), (uc + du * ca, vc + dv * sa)))
            for i in range(sides):
                self.tris.append((c_idx, c_ring[i], c_ring[(i + 1) % sides]))

    def add_cyl(self, cx, cy, z0, z1, r0, r1=None, sides=12, uv_rect=UV_CHROME, cap_bot=True, cap_top=True, scale_xy=(1.0, 1.0)):
        if r1 is None:
            r1 = r0
        self.add_lathe(cx, cy, [(r0, z0), (r1, z1)], sides, uv_rect, cap_bot=cap_bot, cap_top=cap_top, scale_xy=scale_xy)

    def add_tube(self, pts: list[tuple[float, float, float]], radii: float | list[float], sides: int = 8,
                 uv_rect=UV_CHROME, cap_ends: bool = True):
        """Sweep circular cross-section along 3D polyline using stable parallel-transport frames."""
        npts = len(pts)
        assert npts >= 2
        r_list = [radii] * npts if isinstance(radii, (int, float)) else list(radii)
        u0, v0, u1, v1 = uv_rect

        tangents = []
        for k in range(npts):
            p_a = pts[max(0, k - 1)]
            p_b = pts[min(npts - 1, k + 1)]
            tangents.append(_vnorm(_vsub(p_b, p_a)))

        # Initial frame normal perpendicular to tangents[0]
        t0 = tangents[0]
        up_ref = (0.0, 0.0, 1.0) if abs(t0[2]) < 0.9 else (1.0, 0.0, 0.0)
        n_vec = _vnorm(_vcross(up_ref, t0))
        b_vec = _vnorm(_vcross(t0, n_vec))

        rings = []
        for k in range(npts):
            tk = tangents[k]
            if k > 0:
                # Project previous n_vec perpendicular to tk
                dot_nt = n_vec[0] * tk[0] + n_vec[1] * tk[1] + n_vec[2] * tk[2]
                proj = (n_vec[0] - dot_nt * tk[0], n_vec[1] - dot_nt * tk[1], n_vec[2] - dot_nt * tk[2])
                if proj[0] ** 2 + proj[1] ** 2 + proj[2] ** 2 > 1e-6:
                    n_vec = _vnorm(proj)
                b_vec = _vnorm(_vcross(tk, n_vec))
            rk = r_list[k]
            px, py, pz = pts[k]
            vv = v1 - (v1 - v0) * (k / (npts - 1))
            ring = []
            for i in range(sides + 1):
                ang = 2.0 * math.pi * i / sides
                ca, sa = math.cos(ang), math.sin(ang)
                nx = ca * n_vec[0] + sa * b_vec[0]
                ny = ca * n_vec[1] + sa * b_vec[1]
                nz = ca * n_vec[2] + sa * b_vec[2]
                uu = u0 + (u1 - u0) * (i / sides)
                ring.append(self.add_vert((px + rk * nx, py + rk * ny, pz + rk * nz), (nx, ny, nz), (uu, vv)))
            rings.append(ring)

        for k in range(npts - 1):
            r0_i, r1_i = rings[k], rings[k + 1]
            for i in range(sides):
                a, b = r0_i[i], r0_i[i + 1]
                c, d = r1_i[i + 1], r1_i[i]
                self.tris.append((a, b, c))
                self.tris.append((a, c, d))

        if cap_ends:
            uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
            if r_list[0] > 1e-4:
                t_start = tangents[0]
                c0 = self.add_vert(pts[0], (-t_start[0], -t_start[1], -t_start[2]), (uc, vc))
                for i in range(sides):
                    self.tris.append((c0, rings[0][i + 1], rings[0][i]))
            if r_list[-1] > 1e-4:
                t_end = tangents[-1]
                c1 = self.add_vert(pts[-1], t_end, (uc, vc))
                for i in range(sides):
                    self.tris.append((c1, rings[-1][i], rings[-1][i + 1]))

    def add_pillow(self, cx, cy, cz, rx, ry, rz, uv_rect, power: float = 0.65, nu: int = 12, nv: int = 6):
        """Plump rounded superellipsoid cushion / pillow / mattress with smooth vertex normals."""
        u0, v0, u1, v1 = uv_rect

        def spow(val: float, e: float) -> float:
            return math.copysign(abs(val) ** e, val)

        grid = []
        for j in range(nv + 1):
            phi = -0.5 * math.pi + math.pi * (j / nv)
            cp, sp = math.cos(phi), math.sin(phi)
            vv = v1 - (v1 - v0) * (j / nv)
            row = []
            for i in range(nu + 1):
                th = 2.0 * math.pi * (i / nu)
                ct, st_a = math.cos(th), math.sin(th)
                lx = rx * spow(cp, power) * spow(ct, power)
                ly = ry * spow(cp, power) * spow(st_a, power)
                lz = rz * spow(sp, power)
                nx = spow(cp, 2.0 - power) * spow(ct, 2.0 - power) / max(0.05, rx)
                ny = spow(cp, 2.0 - power) * spow(st_a, 2.0 - power) / max(0.05, ry)
                nz = spow(sp, 2.0 - power) / max(0.05, rz)
                uu = u0 + (u1 - u0) * (i / nu)
                row.append(self.add_vert((cx + lx, cy + ly, cz + lz), (nx, ny, nz), (uu, vv)))
            grid.append(row)

        for j in range(nv):
            for i in range(nu):
                a, b = grid[j][i], grid[j][i + 1]
                c, d = grid[j + 1][i + 1], grid[j + 1][i]
                self.tris.append((a, b, c))
                self.tris.append((a, c, d))

    def merge(self, other: "Mesh", dx: float = 0.0, dy: float = 0.0, dz: float = 0.0, yaw_deg: float = 0.0):
        rad = math.radians(yaw_deg)
        ca, sa = math.cos(rad), math.sin(rad)
        base = len(self.verts)
        for (x, y, z), (nx, ny, nz), uv in zip(other.verts, other.norms, other.st):
            rx = x * ca - y * sa + dx
            ry = x * sa + y * ca + dy
            rz = z + dz
            rnx = nx * ca - ny * sa
            rny = nx * sa + ny * ca
            self.verts.append((rx, ry, rz))
            self.norms.append(_vnorm((rnx, rny, nz)))
            self.st.append(uv)
        for i0, i1, i2 in other.tris:
            self.tris.append((base + i0, base + i1, base + i2))

    def save_md3(self, name: str):
        assert len(self.verts) <= 4096, f"{name}: too many verts ({len(self.verts)} > 4096)"
        assert len(self.tris) <= 8192, f"{name}: too many tris ({len(self.tris)} > 8192)"
        scaled_verts = [(x * FT, y * FT, z * FT) for (x, y, z) in self.verts]
        surf_name = name[:15]
        surf = {
            "name": surf_name,
            "shader": self.shader,
            "tris": self.tris,
            "st": self.st,
            "frames": [(scaled_verts, self.norms)],
        }
        md3_path = os.path.join(OUT_DIR, f"{name}.md3")
        md3lib.write(md3_path, {"name": f"progs/fox/{name}.md3", "frame_names": ["idle"], "surfaces": [surf]})
        skin_path = os.path.join(OUT_DIR, f"{name}.md3_0.skin")
        with open(skin_path, "w", newline="\n") as f:
            f.write(f"{surf_name},{self.shader}\n")
        return len(self.verts), len(self.tris)


# ==============================================================================
# 4. ALL 29 SMOOTH-SHADED PROP & VEHICLE DEFINITIONS
# ==============================================================================
def build_bed(king: bool = True) -> Mesh:
    """Padre Hotel signature mustard-yellow tufted headboard bed + plush white duvet + pillows + nightstands/lamps.
    Centered at (0, 0) horizontally: headboard back at x = -3.35, foot at x = +3.35."""
    m = Mesh()
    bw = 6.2 if king else 4.8
    hb_w = bw + 1.0 if king else bw + 0.5
    hb_h = 6.2 if king else 5.8
    # Dark wood headboard border & wide landscape mustard-tufted padded cushion
    m.add_box(-3.35, -hb_w / 2, 0.0, -3.05, hb_w / 2, hb_h, UV_DARK_WOOD)
    m.add_pillow(-2.95, 0.0, 3.35, 0.24, hb_w / 2 - 0.18, hb_h / 2 - 0.35, UV_YELLOW_TUFT, power=0.35, nu=12, nv=6)
    # Dark walnut platform base & tapered feet
    m.add_box(-3.05, -bw / 2, 0.35, 3.30, bw / 2, 1.05, UV_DARK_WOOD)
    for fx in (-2.85, 3.05):
        for fy in (-bw / 2 + 0.2, bw / 2 - 0.2):
            m.add_cyl(fx, fy, 0.0, 0.36, 0.09, 0.13, 8, UV_DARK_WOOD)
    # Plush rounded white mattress + folded hotel duvet + foot runner
    m.add_pillow(0.15, 0.0, 1.65, 3.12, bw / 2 - 0.06, 0.68, UV_WHITE_LINEN, power=0.42, nu=14, nv=6)
    m.add_pillow(0.65, 0.0, 1.82, 2.58, bw / 2 + 0.02, 0.62, UV_WHITE_LINEN, power=0.45, nu=14, nv=6)
    m.add_box(2.15, -bw / 2 - 0.04, 1.02, 3.18, bw / 2 + 0.04, 2.38, UV_ESPRESSO_LTH)  # Tailored charcoal bed runner
    # Plump white hotel pillows + crimson accent bolster
    if king:
        for py in (-1.95, -0.68, 0.68, 1.95):
            m.add_pillow(-2.28, py, 2.45, 0.48, 0.62, 0.30, UV_WHITE_LINEN, power=0.58, nu=10, nv=5)
        m.add_pillow(-1.62, 0.0, 2.42, 0.34, 1.15, 0.26, UV_RED_TUFT, power=0.62, nu=10, nv=5)
        ns_ys = (-bw / 2 - 1.15, bw / 2 + 1.15)
    else:
        for py in (-1.18, 1.18):
            m.add_pillow(-2.28, py, 2.42, 0.48, 0.92, 0.30, UV_WHITE_LINEN, power=0.58, nu=10, nv=5)
        m.add_pillow(-1.62, 0.0, 2.40, 0.34, 0.88, 0.26, UV_RED_TUFT, power=0.62, nu=10, nv=5)
        ns_ys = (bw / 2 + 1.05,)

    # Dark walnut bedside nightstand(s) + glowing warm cylinder table lamp(s)
    for ny in ns_ys:
        m.add_box(-3.20, ny - 0.82, 0.0, -1.75, ny + 0.82, 2.15, UV_DARK_WOOD)
        m.add_box(-1.75, ny - 0.65, 1.35, -1.68, ny + 0.65, 1.95, UV_CHROME)  # drawer pull trim
        m.add_cyl(-2.48, ny, 2.15, 2.30, 0.34, 0.28, 10, UV_BRASS)
        m.add_cyl(-2.48, ny, 2.30, 2.85, 0.10, 0.10, 8, UV_BRASS)
        m.add_cyl(-2.48, ny, 2.75, 3.85, 0.48, 0.40, 14, UV_WARM_LAMP)
    return m


def build_chair_yellow() -> Mesh:
    """Conference Room ribbed mustard-yellow leather Eames rolling chair (padre_113.jpg)."""
    m = Mesh()
    # 5-star chrome caster base + pneumatic cylinder
    m.add_cyl(0.0, 0.0, 0.22, 1.52, 0.09, 0.08, 10, UV_CHROME)
    for k in range(5):
        ang = 2.0 * math.pi * k / 5.0
        ex, ey = 1.05 * math.cos(ang), 1.05 * math.sin(ang)
        m.add_tube([(0.0, 0.0, 0.30), (ex, ey, 0.18)], [0.07, 0.05], 6, UV_CHROME)
        m.add_cyl(ex, ey, 0.0, 0.18, 0.09, 0.09, 8, UV_ESPRESSO_LTH)
    # Contoured mustard seat & tall ribbed backrest
    m.add_pillow(0.08, 0.0, 1.62, 0.92, 0.92, 0.16, UV_YELLOW_TUFT, power=0.45, nu=10, nv=5)
    for r in range(5):
        z_rib = 1.92 + r * 0.36
        x_rib = -0.68 - r * 0.05
        m.add_pillow(x_rib, 0.0, z_rib, 0.15, 0.86, 0.17, UV_YELLOW_TUFT, power=0.48, nu=10, nv=4)
    # Chrome side frame rails & curved loop armrests
    for sy in (-0.94, 0.94):
        m.add_tube([(-0.62, sy, 1.62), (-0.92, sy, 3.55)], 0.05, 6, UV_CHROME)
        m.add_tube([(-0.74, sy, 2.38), (0.58, sy, 2.35), (0.68, sy, 1.66)], 0.05, 8, UV_CHROME)
    return m


def build_tolix_stool(yellow: bool = False) -> Mesh:
    """Tapered A-frame Tolix metal barstool (white in Brimstone/Prairie Fire; yellow at Farmacy/sidewalk)."""
    m = Mesh()
    uv = UV_YELLOW_TUFT if yellow else UV_WHITE_GLOSS
    # 4 splayed legs + square footrest ring + dished metal seat + low curved back
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.add_tube([(sx * 0.72, sy * 0.72, 0.0), (sx * 0.50, sy * 0.50, 2.48)], [0.06, 0.05], 6, uv)
    for ang0 in range(4):
        a0 = math.pi * (0.25 + 0.5 * ang0)
        a1 = a0 + 0.5 * math.pi
        r = 0.88
        m.add_tube([(r * math.cos(a0), r * math.sin(a0), 0.85), (r * math.cos(a1), r * math.sin(a1), 0.85)], 0.04, 6, UV_CHROME)
    m.add_box(-0.62, -0.62, 2.46, 0.62, 0.62, 2.58, uv)
    m.add_pillow(0.0, 0.0, 2.58, 0.56, 0.56, 0.07, UV_DARK_WOOD if not yellow else uv, power=0.45, nu=10, nv=4)
    # Low Tolix hoop backrest on -X side
    m.add_tube([(-0.56, -0.54, 2.56), (-0.72, -0.46, 3.28), (-0.76, 0.0, 3.36), (-0.72, 0.46, 3.28), (-0.56, 0.54, 2.56)],
               0.05, 6, uv)
    return m


def build_chesterfield_sofa(red: bool = False) -> Mesh:
    """Tufted Chesterfield 3-seat leather sofa (cognac for Oil Baron/Head Honcho; crimson for Farmer's Daughter/Fox Lobby)."""
    m = Mesh()
    uv = UV_RED_TUFT if red else UV_COGNAC_TUFT
    hw = 3.55  # 7.1 ft total width along Y
    # Turned dark walnut bun feet + plinth base
    for fx in (-1.25, 1.15):
        for fy in (-hw + 0.35, 0.0, hw - 0.35):
            m.add_cyl(fx, fy, 0.0, 0.35, 0.14, 0.18, 8, UV_DARK_WOOD)
    m.add_box(-1.42, -hw + 0.15, 0.32, 1.38, hw - 0.15, 0.88, uv)
    # 3 plump seat cushions
    cw = (2 * hw - 1.3) / 3.0
    for i in range(3):
        cy = -hw + 0.65 + cw * (i + 0.5)
        m.add_pillow(0.18, cy, 1.18, 1.12, cw * 0.49, 0.34, uv, power=0.46, nu=10, nv=5)
    # Deep button-tufted rolled backrest & rolled Chesterfield scroll arms
    m.add_pillow(-1.08, 0.0, 2.02, 0.44, hw - 0.2, 1.08, uv, power=0.42, nu=14, nv=6)
    m.add_tube([(-1.12, -hw, 2.86), (-1.12, hw, 2.86)], 0.38, 10, uv)
    for sy in (-1, 1):
        ay = sy * (hw - 0.32)
        m.add_pillow(0.0, ay, 1.72, 1.36, 0.36, 0.78, uv, power=0.45, nu=10, nv=5)
        m.add_tube([(-1.25, sy * (hw + 0.05), 2.48), (1.35, sy * (hw + 0.05), 2.48)], 0.34, 10, uv)
    return m


def build_club_armchair(houndstooth: bool = False) -> Mesh:
    """Padre Grand Lobby espresso leather club armchair OR Guest Room houndstooth lounge chair w/ orange pillow."""
    m = Mesh()
    uv = UV_HOUNDSTOOTH if houndstooth else UV_ESPRESSO_LTH
    for fx in (-1.15, 1.08):
        for fy in (-1.15, 1.15):
            m.add_cyl(fx, fy, 0.0, 0.42, 0.08, 0.13, 8, UV_DARK_WOOD)
    m.add_box(-1.32, -1.35, 0.38, 1.25, 1.35, 1.02, uv)
    m.add_pillow(0.12, 0.0, 1.32, 1.05, 0.96, 0.32, uv, power=0.46, nu=10, nv=5)
    # Sloped club backrest & wide track/rolled arms
    m.add_pillow(-0.98, 0.0, 2.15, 0.38, 1.22, 1.05, uv, power=0.45, nu=10, nv=6)
    for sy in (-1, 1):
        m.add_pillow(-0.02, sy * 1.16, 1.70, 1.28, 0.28, 0.68, uv, power=0.45, nu=10, nv=5)
    if houndstooth:
        # Signature burnt-orange accent pillow (padre_165.jpg!)
        m.add_pillow(-0.52, 0.0, 1.78, 0.24, 0.66, 0.34, UV_ORANGE_ACCENT, power=0.60, nu=10, nv=5)
    return m


def build_banquet_set() -> Mesh:
    """Floor 2 Event Rooms & Clover 2: 5.4-ft round black-draped banquet table + 6 curved-back banquet chairs + centerpiece."""
    m = Mesh()
    # Floor-length pleated black tablecloth cylinder + bevel top + glowing candle centerpiece
    m.add_cyl(0.0, 0.0, 0.0, 2.52, 2.75, 2.68, 20, UV_BLACK_CLOTH, cap_bot=False, cap_top=True)
    m.add_cyl(0.0, 0.0, 2.52, 2.62, 0.45, 0.40, 12, UV_BRASS)
    m.add_cyl(0.0, 0.0, 2.62, 3.12, 0.28, 0.24, 12, UV_WARM_LAMP)

    # Single banquet chair sub-mesh facing (-1, 0, 0) inward toward table center -> build facing +X and place at yaw+180
    ch = Mesh()
    for sx in (-0.65, 0.65):
        for sy in (-0.68, 0.68):
            ch.add_tube([(sx, sy, 0.0), (sx * 0.9, sy * 0.9, 1.52)], 0.045, 6, UV_BRASS)
    ch.add_pillow(0.0, 0.0, 1.58, 0.72, 0.74, 0.14, UV_ESPRESSO_LTH, power=0.48, nu=8, nv=4)
    ch.add_tube([(-0.66, -0.68, 1.58), (-0.78, -0.64, 3.05), (-0.80, 0.0, 3.22), (-0.78, 0.64, 3.05), (-0.66, 0.68, 1.58)],
                0.05, 6, UV_BRASS)
    ch.add_pillow(-0.72, 0.0, 2.48, 0.10, 0.58, 0.58, UV_HOUNDSTOOTH, power=0.50, nu=8, nv=4)

    for k in range(6):
        ang_deg = k * 60.0
        rad = math.radians(ang_deg)
        r_ch = 3.55
        m.merge(ch, dx=r_ch * math.cos(rad), dy=r_ch * math.sin(rad), dz=0.0, yaw_deg=ang_deg + 180.0)
    return m


def build_treadmill() -> Mesh:
    """Precor commercial treadmill for Padre Basement 24-Hr Gym (padre_190.jpg). Runner faces +X."""
    m = Mesh()
    # Low silver side rails, front motor hood, and charcoal running belt
    m.add_box(-3.15, -1.38, 0.08, 3.15, 1.38, 0.42, UV_CHROME)
    m.add_box(-3.00, -1.06, 0.40, 1.95, 1.06, 0.48, UV_ESPRESSO_LTH)  # tread belt
    m.add_pillow(2.48, 0.0, 0.58, 0.62, 1.32, 0.34, UV_CHROME, power=0.48, nu=10, nv=5)  # motor shroud
    # Angled silver uprights + safety side handrails + inclined LED touch console
    for sy in (-1.24, 1.24):
        m.add_tube([(2.15, sy, 0.42), (1.72, sy, 3.85)], [0.12, 0.09], 8, UV_CHROME)
        m.add_tube([(1.72, sy, 3.55), (0.35, sy, 3.25)], 0.07, 8, UV_ESPRESSO_LTH)
    m.add_box(1.48, -1.32, 3.72, 2.18, 1.32, 4.78, UV_ESPRESSO_LTH, {"nx": UV_GYM_SCREEN})
    return m


def build_elliptical() -> Mesh:
    """Commercial elliptical cross-trainer for Padre Basement Gym."""
    m = Mesh()
    m.add_box(-3.10, -1.15, 0.0, 3.10, 1.15, 0.24, UV_CHROME)
    # Rear flywheel drum shroud
    m.add_cyl(-2.15, 0.0, 0.24, 2.15, 0.92, 0.88, 14, UV_CHROME, scale_xy=(1.0, 0.38))
    # Pedals & stride rails + dual moving stride arms + front console mast
    for sy, x_off in ((-0.58, -0.35), (0.58, 0.35)):
        m.add_tube([(-2.15, sy, 0.65), (1.85, sy, 0.95)], 0.06, 6, UV_CHROME)
        m.add_box(x_off - 0.65, sy - 0.26, 0.78, x_off + 0.65, sy + 0.26, 0.96, UV_ESPRESSO_LTH)
        m.add_tube([(1.65, sy, 0.95), (1.45 + x_off * 0.4, sy * 1.35, 4.65)], 0.06, 8, UV_CHROME)
    m.add_tube([(2.15, 0.0, 0.24), (1.82, 0.0, 4.15)], [0.14, 0.10], 8, UV_CHROME)
    m.add_box(1.58, -0.82, 3.95, 2.08, 0.82, 4.92, UV_ESPRESSO_LTH, {"nx": UV_GYM_SCREEN})
    return m


def build_exercise_bike() -> Mesh:
    """Commercial upright stationary exercise bike for Padre Basement Gym."""
    m = Mesh()
    m.add_box(-1.85, -0.95, 0.0, 1.85, 0.95, 0.20, UV_CHROME)
    # Flywheel/crank shroud
    m.add_pillow(0.15, 0.0, 1.18, 1.15, 0.34, 0.85, UV_CHROME, power=0.52, nu=12, nv=5)
    # Seat post + ergonomic saddle
    m.add_tube([(-0.45, 0.0, 1.55), (-0.85, 0.0, 3.05)], 0.09, 8, UV_CHROME)
    m.add_pillow(-0.90, 0.0, 3.16, 0.48, 0.42, 0.16, UV_ESPRESSO_LTH, power=0.52, nu=10, nv=4)
    # Front handlebar mast + racing bars + LED console
    m.add_tube([(0.95, 0.0, 1.55), (1.28, 0.0, 3.85)], 0.09, 8, UV_CHROME)
    m.add_tube([(1.15, -0.78, 3.95), (1.35, 0.0, 3.82), (1.15, 0.78, 3.95)], 0.06, 8, UV_ESPRESSO_LTH)
    m.add_box(1.12, -0.62, 3.88, 1.52, 0.62, 4.62, UV_ESPRESSO_LTH, {"nx": UV_GYM_SCREEN})
    return m


def build_watercooler() -> Mesh:
    """Gym bottled water dispenser with translucent blue 5-gallon water jug."""
    m = Mesh()
    m.add_box(-0.72, -0.72, 0.0, 0.72, 0.72, 3.15, UV_WHITE_GLOSS)
    m.add_box(0.68, -0.42, 1.95, 0.76, 0.42, 2.68, UV_ESPRESSO_LTH)  # tap recess
    m.add_lathe(0.0, 0.0, [(0.22, 3.15), (0.58, 3.35), (0.58, 4.35), (0.42, 4.55), (0.14, 4.65)], 14, UV_WATER_BLUE)
    return m


def build_jacuzzi() -> Mesh:
    """Suite silver-pewter mosaic whirlpool Jacuzzi tub w/ sculpted oval white basin & chrome Roman spout (padre_141.jpg)."""
    m = Mesh()
    # Outer silver-pewter mosaic tiled deck (8.4 x 5.4 ft, height 2.15 ft) with open center for sunken tub rim
    dx, dy, h = 4.2, 2.7, 2.15
    ix, iy = 3.25, 1.85
    # 4 deck border slabs around tub opening
    m.add_box(-dx, -dy, 0.0, -ix, dy, h, UV_SILVER_MOSAIC)
    m.add_box(ix, -dy, 0.0, dx, dy, h, UV_SILVER_MOSAIC)
    m.add_box(-ix, -dy, 0.0, ix, -iy, h, UV_SILVER_MOSAIC)
    m.add_box(-ix, iy, 0.0, ix, dy, h, UV_SILVER_MOSAIC)
    # Sculpted glossy-white acrylic oval tub rim & concave whirlpool basin (inverted lathe profile!)
    # Lathe from bottom floor (z=0.35, r=0.05 -> 0.72) up to outer molded lip (z=2.28, r=1.06 -> 0.92)
    m.add_lathe(0.0, 0.0, [
        (0.02, 0.42), (0.68, 0.45), (0.84, 1.15), (0.94, 2.18), (1.06, 2.28), (1.08, 2.15)
    ], 24, UV_WHITE_GLOSS, cap_bot=False, cap_top=False, scale_xy=(3.25, 1.85))
    # Plush headrests at both ends + chrome Roman waterfall spout & handles
    for sx in (-3.15, 3.15):
        m.add_pillow(sx, 0.0, 2.34, 0.28, 0.78, 0.16, UV_ESPRESSO_LTH, power=0.52, nu=8, nv=4)
    m.add_tube([(0.0, -2.22, 2.15), (0.0, -2.22, 2.68), (0.0, -1.72, 2.55)], [0.10, 0.09, 0.08], 8, UV_CHROME)
    for hx in (-0.55, 0.55):
        m.add_cyl(hx, -2.22, 2.15, 2.48, 0.08, 0.06, 8, UV_CHROME)
    return m


def build_pooltable() -> Mesh:
    """Brimstone 8-ft dark walnut & emerald-felt billiards table with pockets, ball rack & cue sticks."""
    m = Mesh()
    lx, ly = 4.2, 2.35  # 8.4 x 4.7 ft
    # 4 carved tapered walnut legs
    for sx in (-3.35, 3.35):
        for sy in (-1.65, 1.65):
            m.add_lathe(sx, sy, [(0.16, 0.0), (0.14, 0.35), (0.28, 1.65), (0.34, 2.15)], 10, UV_DARK_WOOD)
    # Deep walnut cabinet apron + emerald felt slate bed + cushioned rails
    m.add_box(-lx + 0.18, -ly + 0.18, 2.05, lx - 0.18, ly - 0.18, 2.62, UV_DARK_WOOD)
    m.add_box(-lx + 0.42, -ly + 0.42, 2.62, lx - 0.42, ly - 0.42, 2.70, UV_GREEN_FELT)
    # 4 mahogany cushion rails
    rw = 0.42
    m.add_box(-lx, -ly, 2.55, lx, -ly + rw, 2.86, UV_DARK_WOOD)
    m.add_box(-lx, ly - rw, 2.55, lx, ly, 2.86, UV_DARK_WOOD)
    m.add_box(-lx, -ly + rw, 2.55, -lx + rw, ly - rw, 2.86, UV_DARK_WOOD)
    m.add_box(lx - rw, -ly + rw, 2.55, lx, ly - rw, 2.86, UV_DARK_WOOD)
    # 6 chrome & dark-leather pockets
    for px in (-lx + 0.22, 0.0, lx - 0.22):
        for py in (-ly + 0.22, ly - 0.22):
            m.add_cyl(px, py, 2.52, 2.89, 0.25, 0.25, 10, UV_ESPRESSO_LTH)
    # Racked billiard balls + cue ball + wooden cue stick resting on table
    for row in range(4):
        for col in range(row + 1):
            bx = 1.65 + row * 0.18
            by = (col - row * 0.5) * 0.19
            uv_b = (UV_YELLOW_TUFT, UV_RED_TUFT, UV_WHITE_GLOSS, UV_ORANGE_ACCENT)[(row + col) % 4]
            m.add_pillow(bx, by, 2.79, 0.09, 0.09, 0.09, uv_b, power=0.95, nu=8, nv=4)
    m.add_pillow(-1.85, 0.0, 2.79, 0.09, 0.09, 0.09, UV_WHITE_GLOSS, power=0.95, nu=8, nv=4)
    m.add_tube([(-3.2, -0.85, 2.76), (1.1, 0.65, 2.76)], [0.04, 0.02], 6, UV_BRASS)
    return m


def build_patio_heater() -> Mesh:
    """Prairie Fire 7.4-ft bronze mushroom patio heater with glowing emitter mesh (padre_174.jpg)."""
    m = Mesh()
    m.add_lathe(0.0, 0.0, [
        (0.92, 0.0), (0.88, 0.18), (0.68, 0.28), (0.68, 2.45), (0.14, 2.65), (0.12, 5.85)
    ], 14, UV_BRONZE)
    # Glowing orange-red burner emitter cage (z = 5.85 .. 6.65)
    m.add_cyl(0.0, 0.0, 5.85, 6.65, 0.34, 0.42, 12, UV_HEATER_GLOW)
    # Wide conical bronze reflector dome (z = 6.65 .. 7.35)
    m.add_lathe(0.0, 0.0, [(1.65, 6.65), (1.68, 6.72), (0.45, 7.28), (0.04, 7.36)], 18, UV_BRONZE, cap_bot=False)
    return m


def build_chand_drum() -> Mesh:
    """Grand Lobby two-tier burnished-gold & warm-linen drum chandelier (z = 0..3.6 ft, canopy at z = 3.6)."""
    m = Mesh()
    m.add_cyl(0.0, 0.0, 3.42, 3.60, 0.42, 0.48, 12, UV_BRASS)
    m.add_cyl(0.0, 0.0, 1.95, 3.45, 0.06, 0.06, 8, UV_BRASS)
    # Outer wide burnished gold drum shade (r = 2.15 ft)
    m.add_cyl(0.0, 0.0, 1.05, 2.15, 2.15, 2.15, 22, UV_BRASS, cap_bot=False, cap_top=False)
    m.add_cyl(0.0, 0.0, 1.08, 2.12, 2.08, 2.08, 22, UV_WARM_LAMP, cap_bot=False, cap_top=True)
    # Lower glowing warm-ivory inner drum tier (r = 1.42 ft)
    m.add_cyl(0.0, 0.0, 0.18, 1.18, 1.42, 1.42, 20, UV_WARM_LAMP, cap_bot=True, cap_top=False)
    m.add_cyl(0.0, 0.0, 0.0, 0.20, 0.14, 0.24, 10, UV_BRASS)
    return m


def build_chand_fringe() -> Mesh:
    """Brimstone 3-tier rectangular gold-fringe chandelier over communal table (z = 0..3.4 ft)."""
    m = Mesh()
    for sx in (-1.45, 1.45):
        m.add_cyl(sx, 0.0, 2.05, 3.40, 0.05, 0.05, 8, UV_BRASS)
        m.add_cyl(sx, 0.0, 3.28, 3.40, 0.28, 0.28, 10, UV_BRASS)
    for lx, ly, z0, z1, uv in [
        (2.65, 1.15, 1.55, 2.35, UV_BRASS),
        (2.15, 0.88, 0.82, 1.62, UV_WARM_LAMP),
        (1.65, 0.62, 0.12, 0.88, UV_WARM_LAMP),
    ]:
        m.add_box(-lx, -ly, z0, lx, ly, z1, uv)
    return m


def build_chand_brass() -> Mesh:
    """Event Rooms & Clover 8-arm curved antique brass chandelier with glowing shades (z = 0..3.2 ft)."""
    m = Mesh()
    m.add_cyl(0.0, 0.0, 3.02, 3.20, 0.36, 0.42, 12, UV_BRASS)
    m.add_lathe(0.0, 0.0, [(0.08, 0.15), (0.36, 0.55), (0.14, 1.15), (0.07, 3.05)], 12, UV_BRASS)
    for k in range(8):
        ang = 2.0 * math.pi * k / 8.0
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [
            (0.22 * ca, 0.22 * sa, 0.72),
            (0.95 * ca, 0.95 * sa, 0.32),
            (1.68 * ca, 1.68 * sa, 0.62),
            (1.82 * ca, 1.82 * sa, 1.05),
        ]
        m.add_tube(pts, 0.045, 6, UV_BRASS)
        gx, gy = 1.82 * ca, 1.82 * sa
        m.add_cyl(gx, gy, 1.02, 1.12, 0.20, 0.16, 8, UV_BRASS)
        m.add_cyl(gx, gy, 1.12, 1.68, 0.18, 0.26, 10, UV_WARM_LAMP)
    return m


def build_chand_linear() -> Mesh:
    """Conference Room 8.4-ft modern brass & glowing frosted-tube linear chandelier (z = 0..2.8 ft, along X)."""
    m = Mesh()
    for sx in (-2.6, 2.6):
        m.add_cyl(sx, 0.0, 0.55, 2.80, 0.04, 0.04, 8, UV_BRASS)
        m.add_cyl(sx, 0.0, 2.68, 2.80, 0.26, 0.26, 10, UV_BRASS)
    m.add_box(-4.2, -0.14, 0.42, 4.2, 0.14, 0.62, UV_BRASS)
    for bx in (-3.2, -1.1, 1.1, 3.2):
        m.add_box(bx - 0.85, -0.32, 0.12, bx + 0.85, 0.32, 0.42, UV_WARM_LAMP)
    return m


def build_fox_chandelier() -> Mesh:
    """Fox Theater Lobby & Mezzanine ornate Spanish wrought-iron & gold scroll chandelier (gal_115.jpg, z = 0..5.2 ft)."""
    m = Mesh()
    m.add_cyl(0.0, 0.0, 4.95, 5.20, 0.48, 0.56, 12, UV_BRONZE)
    m.add_cyl(0.0, 0.0, 2.65, 5.00, 0.10, 0.10, 8, UV_BRONZE)
    # Central glowing carved alabaster bowl + ornate bronze finial
    m.add_lathe(0.0, 0.0, [
        (0.05, 0.0), (0.28, 0.38), (0.16, 0.62), (1.35, 1.15), (1.72, 1.85), (1.62, 1.95)
    ], 18, UV_WARM_LAMP)
    m.add_cyl(0.0, 0.0, 1.82, 2.08, 1.78, 1.78, 18, UV_BRASS, cap_bot=False, cap_top=False)
    # 6 wrought-iron S-scroll arms + 6 glowing Spanish hexagonal/cylindrical lanterns
    for k in range(6):
        ang = 2.0 * math.pi * k / 6.0
        ca, sa = math.cos(ang), math.sin(ang)
        m.add_tube([
            (0.14 * ca, 0.14 * sa, 3.45),
            (1.15 * ca, 1.15 * sa, 3.65),
            (2.25 * ca, 2.25 * sa, 2.55),
            (2.45 * ca, 2.45 * sa, 2.15),
        ], 0.06, 6, UV_BRONZE)
        lx, ly = 2.45 * ca, 2.45 * sa
        m.add_cyl(lx, ly, 2.12, 2.38, 0.38, 0.12, 6, UV_BRONZE)
        m.add_cyl(lx, ly, 1.25, 2.12, 0.28, 0.34, 6, UV_WARM_LAMP)
        m.add_cyl(lx, ly, 1.02, 1.25, 0.06, 0.28, 6, UV_BRONZE)
    return m


def build_fan_palm(height: float = 25.0) -> Mesh:
    """California Fan Palm (Washingtonia filifera): curved ringed trunk, golden shag petticoat & 16 arched 3D fan fronds."""
    m = Mesh()
    s = height / 25.0
    # Gently S-curved ringed trunk up to z = 0.84 * height
    trunk_pts = []
    trunk_r = []
    n_seg = 9
    top_z = height * 0.85
    for k in range(n_seg + 1):
        t = k / n_seg
        curve_x = 0.55 * s * math.sin(t * math.pi * 0.9)
        curve_y = 0.25 * s * (1.0 - math.cos(t * math.pi * 0.7))
        r = (1.15 - 0.46 * (t ** 0.75)) * max(0.72, s)
        trunk_pts.append((curve_x, curve_y, t * top_z))
        trunk_r.append(r)
    m.add_tube(trunk_pts, trunk_r, 12, UV_PALM_BARK, cap_ends=True)

    cx, cy, cz = trunk_pts[-1]
    # Dry golden-tan petticoat shag skirt hanging below green crown
    m.add_lathe(cx, cy, [
        (0.75 * max(0.75, s), cz - 3.6 * s),
        (1.65 * max(0.78, s), cz - 2.2 * s),
        (1.85 * max(0.78, s), cz - 0.6 * s),
        (1.15 * max(0.78, s), cz + 0.5 * s),
    ], 14, UV_PALM_SHAG, cap_bot=True, cap_top=True)

    # 16 3D arched pleated V-section fan fronds in two radial tiers (outer drooping + inner uplifted)
    u0, v0, u1, v1 = UV_PALM_FROND
    tiers = [
        (10, 8.8 * max(0.72, s), 18.0, 3.6 * max(0.72, s), 0.0),
        (6, 6.8 * max(0.72, s), 48.0, 2.2 * max(0.72, s), 18.0),
    ]
    for count, flen, elev_deg, droop, phase in tiers:
        for k in range(count):
            yaw = math.radians(phase + k * (360.0 / count))
            cy_a, sy_a = math.cos(yaw), math.sin(yaw)
            rx_a, ry_a = -sy_a, ca_r if False else cy_a  # perpendicular horizontal vector (-sin, cos)
            elev = math.radians(elev_deg)
            steps = 5
            rings = []
            for j in range(steps + 1):
                f = j / steps
                dist = flen * f * math.cos(elev * (1.0 - 0.35 * f))
                z_pt = cz + 0.35 * s + flen * f * math.sin(elev) - droop * (f ** 2.1)
                px = cx + dist * cy_a
                py = cy + dist * sy_a
                # Fan leaf widens from petiole (f=0.2) to broad palmate fan (f=0.75) then tapers
                w_half = (0.14 + 1.85 * math.sin(f * math.pi * 0.88)) * max(0.72, s)
                ridge = 0.22 * w_half
                vv = v1 - (v1 - v0) * f
                il = m.add_vert((px - w_half * rx_a, py - w_half * ry_a, z_pt - ridge), (-0.2 * rx_a, -0.2 * ry_a, 0.96), (u0, vv))
                ic = m.add_vert((px, py, z_pt + ridge * 0.6), (0.0, 0.0, 1.0), (0.5 * (u0 + u1), vv))
                ir = m.add_vert((px + w_half * rx_a, py + w_half * ry_a, z_pt - ridge), (0.2 * rx_a, 0.2 * ry_a, 0.96), (u1, vv))
                rings.append((il, ic, ir))
            for j in range(steps):
                l0, c0, r0 = rings[j]
                l1, c1, r1 = rings[j + 1]
                m.tris.extend([(l0, c0, c1), (l0, c1, l1), (c0, r0, r1), (c0, r1, c1)])
    return m


def build_streetlamp() -> Mesh:
    """Historic Downtown Bakersfield double-globe cast-iron sidewalk streetlamp (14.6 ft tall, arms along Y)."""
    m = Mesh()
    m.add_lathe(0.0, 0.0, [
        (0.82, 0.0), (0.76, 0.55), (0.52, 0.95), (0.48, 2.85),
        (0.32, 3.25), (0.22, 12.15), (0.34, 12.45), (0.14, 13.35), (0.03, 13.75)
    ], 12, UV_BRONZE)
    # Twin S-scroll cross-arms & glowing frosted-glass acorn globes at y = -2.15 and +2.15
    for sy in (-1, 1):
        m.add_tube([
            (0.0, sy * 0.18, 11.45),
            (0.0, sy * 1.15, 11.20),
            (0.0, sy * 2.15, 12.05),
            (0.0, sy * 2.15, 12.35),
        ], 0.09, 8, UV_BRONZE)
        m.add_tube([(0.0, sy * 0.20, 12.35), (0.0, sy * 2.15, 12.15)], 0.07, 6, UV_BRONZE)
        gy = sy * 2.15
        m.add_lathe(0.0, gy, [
            (0.28, 12.32), (0.64, 12.78), (0.72, 13.38), (0.46, 13.98), (0.08, 14.32)
        ], 14, UV_WARM_LAMP)
        m.add_cyl(0.0, gy, 14.28, 14.52, 0.14, 0.02, 8, UV_BRONZE)
    return m


def build_clockpost() -> Mesh:
    """Historic 4-dial bronze 'HOPE' street post clock in front of the Fox Theater (gal_019.jpg, 15.6 ft tall)."""
    m = Mesh()
    # Molded square bronze pedestal + fluted bronze column
    m.add_box(-1.05, -1.05, 0.0, 1.05, 1.05, 0.65, UV_BRONZE)
    m.add_box(-0.82, -0.82, 0.65, 0.82, 0.82, 3.65, UV_BRONZE)
    m.add_box(-0.92, -0.92, 3.65, 0.92, 0.92, 3.95, UV_BRASS)
    m.add_lathe(0.0, 0.0, [(0.52, 3.95), (0.44, 4.45), (0.36, 10.65), (0.68, 11.15)], 14, UV_BRONZE)
    # 4-sided bronze & brass clock head housing with 4 illuminated Roman-numeral dials!
    m.add_box(-1.32, -1.32, 11.15, 1.32, 1.32, 14.05, UV_BRONZE, {
        "px": UV_CLOCK_DIAL, "nx": UV_CLOCK_DIAL, "py": UV_CLOCK_DIAL, "ny": UV_CLOCK_DIAL,
    })
    # Brass bezel rings around all 4 clock faces + domed finial crown
    m.add_box(-1.42, -1.42, 14.05, 1.42, 1.42, 14.32, UV_BRASS)
    m.add_lathe(0.0, 0.0, [(1.12, 14.32), (0.85, 14.88), (0.28, 15.28), (0.03, 15.68)], 14, UV_BRONZE)
    return m


def build_bikerack() -> Mesh:
    """Buena Vista Museum green bicycle-silhouette sidewalk bike rack (fblk_163.jpg, oriented along X)."""
    m = Mesh()
    uv = UV_GREEN_FELT
    # Base rail anchored to sidewalk
    m.add_box(-3.35, -0.35, 0.0, 3.35, 0.35, 0.08, UV_CHROME)
    # Rear (-1.95) & Front (+1.95) circular green tubular bicycle wheels (r = 1.18 ft, center z = 1.25)
    for wx in (-1.95, 1.95):
        pts = [(wx + 1.18 * math.cos(2 * math.pi * i / 18), 0.0, 1.25 + 1.18 * math.sin(2 * math.pi * i / 18)) for i in range(19)]
        m.add_tube(pts, 0.09, 8, uv, cap_ends=False)
        # Vertical parking U-hoop inside each wheel
        m.add_tube([(wx - 0.45, 0.0, 0.08), (wx - 0.45, 0.0, 2.15), (wx + 0.45, 0.0, 2.15), (wx + 0.45, 0.0, 0.08)], 0.06, 6, uv)
    # Classic diamond bicycle frame, seat post + saddle, head tube + handlebars
    m.add_tube([(-1.95, 0.0, 1.25), (-0.35, 0.0, 1.15), (-0.85, 0.0, 2.75), (-1.95, 0.0, 1.25)], 0.08, 8, uv)
    m.add_tube([(-0.35, 0.0, 1.15), (1.35, 0.0, 2.55), (-0.75, 0.0, 2.55)], 0.08, 8, uv)
    m.add_tube([(1.95, 0.0, 1.25), (1.30, 0.0, 2.85), (1.05, 0.0, 3.35)], 0.08, 8, uv)
    m.add_tube([(1.05, -0.68, 3.38), (1.05, 0.68, 3.38)], 0.07, 6, uv)  # handlebars
    m.add_pillow(-0.92, 0.0, 2.92, 0.42, 0.22, 0.10, uv, power=0.55, nu=8, nv=4)  # saddle
    return m


def build_guitar() -> Mesh:
    """Stage Left Green Room electric guitar resting on an A-frame floor stand (faces +X)."""
    m = Mesh()
    # Black tubular A-frame guitar stand
    for sy in (-0.65, 0.65):
        m.add_tube([(-0.65, sy, 0.0), (0.55, sy * 0.75, 0.08)], 0.04, 6, UV_ESPRESSO_LTH)
        m.add_tube([(-0.55, sy * 0.85, 0.04), (-0.18, 0.0, 1.95)], 0.04, 6, UV_ESPRESSO_LTH)
        m.add_tube([(0.25, sy * 0.48, 0.55), (0.52, sy * 0.48, 0.58)], 0.04, 6, UV_ESPRESSO_LTH)
    # Contoured sunburst/crimson double-cutaway guitar body + white pickguard + maple neck + headstock
    m.add_pillow(0.18, 0.0, 1.18, 0.14, 0.68, 0.62, UV_SUNBURST, power=0.52, nu=12, nv=6)
    m.add_pillow(0.20, 0.22, 1.72, 0.12, 0.34, 0.36, UV_SUNBURST, power=0.55, nu=8, nv=4)
    m.add_pillow(0.20, -0.22, 1.66, 0.12, 0.30, 0.30, UV_SUNBURST, power=0.55, nu=8, nv=4)
    m.add_box(0.28, -0.34, 0.95, 0.33, 0.34, 1.55, UV_WHITE_GLOSS)  # pickguard & pickups
    m.add_box(0.29, -0.18, 0.86, 0.35, 0.18, 0.96, UV_CHROME)       # chrome bridge
    # Slightly reclined neck & headstock
    m.add_tube([(0.18, 0.0, 1.72), (-0.12, 0.0, 3.65)], [0.09, 0.07], 8, UV_DARK_WOOD)
    m.add_box(-0.20, -0.16, 3.62, -0.06, 0.16, 4.18, UV_SUNBURST)
    return m


def build_get_bus() -> Mesh:
    """Golden Empire Transit ('GET bus') 38-ft low-floor city transit bus (fblk_418.jpg).
    Length 38.0 ft (x = -19..+19, +X = front), width 8.5 ft (y = -4.25..+4.25), height 10.4 ft."""
    m = Mesh(shader="progs/fox/get_bus_tex")
    hl, hw = 19.0, 4.25

    # Sculpted bus body cross-section extruded with aerodynamic curved front windshield & rounded roof!
    # Build side skins as a 5-band vertical profile x 7-station longitudinal loft so roof & nose curve smoothly!
    # Stations along X from rear (-19.0) to front (+19.0):
    xs = [-19.0, -18.4, 16.8, 18.2, 19.0]
    # Vertical stations (z, half_y) at main body:
    z_bands = [
        (1.05, 4.18),   # lower skirt bottom
        (1.45, 4.25),   # beltline lower
        (5.45, 4.25),   # window sill
        (9.15, 4.16),   # cantrail above windows
        (9.85, 3.72),   # curved roof shoulder
    ]

    su0, sv0, su1, sv1 = BUS_SIDE_UV
    # Left (+Y) and Right (-Y) lofted body sides
    for side_sign in (-1.0, 1.0):
        grid = []
        for j, (zb, hy) in enumerate(z_bands):
            vv = sv1 - (sv1 - sv0) * (j / (len(z_bands) - 1))
            nj_z = 0.45 if j == len(z_bands) - 1 else (-0.25 if j == 0 else 0.0)
            row = []
            for i, x_raw in enumerate(xs):
                # Rake the upper nose slightly back at the front (+X)
                rake = (0.55 if j >= 3 else 0.0) if i == len(xs) - 1 else 0.0
                tap_y = 0.92 if i in (0, len(xs) - 1) else 1.0
                px = x_raw - rake
                py = side_sign * hy * tap_y
                t_u = (px + hl) / (2.0 * hl)
                # Right side (-Y): rear->front is left->right (u0->u1); Left side (+Y): front->rear is left->right!
                uu = (su0 + (su1 - su0) * t_u) if side_sign < 0 else (su0 + (su1 - su0) * (1.0 - t_u))
                nx = -0.35 if i == 0 else (0.35 if i == len(xs) - 1 else 0.0)
                row.append(m.add_vert((px, py, zb), (nx, side_sign, nj_z), (uu, vv)))
            grid.append(row)
        for j in range(len(z_bands) - 1):
            for i in range(len(xs) - 1):
                a, b = grid[j][i], grid[j][i + 1]
                c, d = grid[j + 1][i + 1], grid[j + 1][i]
                if side_sign < 0:
                    m.tris.extend([(a, b, c), (a, c, d)])
                else:
                    m.tris.extend([(a, c, b), (a, d, c)])

    # Crowned white roof panel + rooftop low-profile HVAC / CNG fairing pod!
    m.add_quad((-18.4, 3.72, 9.85), (18.45, 3.72, 9.85), (18.45, -3.72, 9.85), (-18.4, -3.72, 9.85), BUS_ROOF_UV, (0, 0, 1))
    m.add_box(-9.5, -2.85, 9.82, 8.5, 2.85, 10.55, BUS_ROOF_UV)  # Rooftop white AC / CNG pod (fblk_418!)

    # Front nose cap (+X) with BUS_FRONT_UV (curved lower apron + sloped windshield + destination dome)
    fu0, fv0, fu1, fv1 = BUS_FRONT_UV
    f_prof = [
        (18.85, 1.05, 3.85, fv1),
        (19.05, 4.85, 3.92, fv0 + 0.62 * (fv1 - fv0)),
        (18.55, 8.35, 3.82, fv0 + 0.20 * (fv1 - fv0)),
        (18.35, 9.85, 3.45, fv0),
    ]
    for k in range(len(f_prof) - 1):
        x_a, z_a, y_a, v_a = f_prof[k]
        x_b, z_b, y_b, v_b = f_prof[k + 1]
        m.add_quad((x_b, -y_b, z_b), (x_b, y_b, z_b), (x_a, y_a, z_a), (x_a, -y_a, z_a), (fu0, v_b, fu1, v_a), (1, 0, 0.15))

    # Rear tail cap (-X) with BUS_REAR_UV
    ru0, rv0, ru1, rv1 = BUS_REAR_UV
    m.add_quad((-18.95, 3.85, 9.80), (-18.95, -3.85, 9.80), (-18.95, -3.85, 1.05), (-18.95, 3.85, 1.05),
               (ru0, rv0, ru1, rv1), (-1, 0, 0))

    # Dark undercarriage chassis belly pan + front & rear transit bumpers + side mirrors
    m.add_box(-18.6, -3.75, 0.95, 18.6, 3.75, 1.15, BUS_TIRE_UV)
    m.add_box(18.75, -4.05, 1.02, 19.35, 4.05, 1.92, BUS_TIRE_UV)   # Front energy-absorbing bumper
    m.add_box(-19.30, -4.05, 1.02, -18.75, 4.05, 1.92, BUS_TIRE_UV)  # Rear bumper
    # Twin transit wing mirrors at front corners
    for sy in (-1, 1):
        m.add_tube([(18.35, sy * 3.85, 7.65), (19.45, sy * 4.75, 7.55), (19.45, sy * 4.75, 6.45)], 0.08, 6, BUS_TIRE_UV)
        m.add_box(19.25, sy * 4.55 - 0.18, 5.85, 19.60, sy * 4.55 + 0.18, 6.85, BUS_TIRE_UV)

    # 4 Sculpted cylindrical transit wheels (front & rear axles, r = 1.68 ft, resting cleanly at z = 0.0!)
    wheel = Mesh(shader="progs/fox/get_bus_tex")
    # Build wheel along Z (lathe) then rotate 90 deg around X -> build directly along Y!
    r_tire = 1.68
    sides = 18
    tu0, tv0, tu1, tv1 = BUS_TIRE_UV
    hu0, hv0, hu1, hv1 = BUS_HUB_UV
    hcx, hcy = 0.5 * (hu0 + hu1), 0.5 * (hv0 + hv1)
    hdu, hdv = 0.46 * (hu1 - hu0), 0.46 * (hv1 - hv0)
    ring_in, ring_out = [], []
    for i in range(sides + 1):
        ang = 2.0 * math.pi * i / sides
        ca, sa = math.cos(ang), math.sin(ang)
        uu = tu0 + (tu1 - tu0) * (i / sides)
        ring_in.append(wheel.add_vert((r_tire * ca, -0.48, r_tire + r_tire * sa), (ca, 0.0, sa), (uu, tv0)))
        ring_out.append(wheel.add_vert((r_tire * ca, 0.48, r_tire + r_tire * sa), (ca, 0.0, sa), (uu, tv1)))
    for i in range(sides):
        a, b = ring_in[i], ring_in[i + 1]
        c, d = ring_out[i + 1], ring_out[i]
        wheel.tris.extend([(a, c, b), (a, d, c)])
    # Outer (+Y) & Inner (-Y) hubcap discs
    for wy, ny_s in ((-0.48, -1.0), (0.48, 1.0)):
        c_v = wheel.add_vert((0.0, wy, r_tire), (0.0, ny_s, 0.0), (hcx, hcy))
        rim = []
        for i in range(sides):
            ang = 2.0 * math.pi * i / sides
            ca, sa = math.cos(ang), math.sin(ang)
            rim.append(wheel.add_vert((r_tire * ca, wy, r_tire + r_tire * sa), (0.0, ny_s, 0.0), (hcx + hdu * ca, hcy + hdv * sa)))
        for i in range(sides):
            if ny_s > 0:
                wheel.tris.append((c_v, rim[i], rim[(i + 1) % sides]))
            else:
                wheel.tris.append((c_v, rim[(i + 1) % sides], rim[i]))

    for ax in (-10.8, 11.4):
        for wy in (-3.82, 3.82):
            m.merge(wheel, dx=ax, dy=wy, dz=0.0)
    return m


# ==============================================================================
# 5. WRITE SHADERS, TEXTURES & ALL 29 MD3 PROPS
# ==============================================================================
SHADER_TEXT = """// Generated by source/mm_tools/build_fox_models.py for Fox Theater, Padre Hotel & Downtown Bakersfield props

progs/fox/fox_materials
{
\tcull none
\t{
\t\tmap progs/fox/fox_materials
\t\trgbGen lightingDiffuse
\t}
\t{
\t\tmap progs/fox/fox_materials_glow
\t\tblendfunc add
\t\trgbGen identity
\t}
}

progs/fox/get_bus_tex
{
\tcull none
\t{
\t\tmap progs/fox/get_bus_tex
\t\trgbGen lightingDiffuse
\t}
\t{
\t\tmap progs/fox/get_bus_tex_glow
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(SHADER_PATH), exist_ok=True)

    atlas, atlas_glow = build_material_atlas()
    atlas.save(os.path.join(OUT_DIR, "fox_materials.png"))
    atlas_glow.save(os.path.join(OUT_DIR, "fox_materials_glow.png"))

    bus_tex, bus_glow = build_bus_texture()
    bus_tex.save(os.path.join(OUT_DIR, "get_bus_tex.png"))
    bus_glow.save(os.path.join(OUT_DIR, "get_bus_tex_glow.png"))

    with open(SHADER_PATH, "w", newline="\n") as f:
        f.write(SHADER_TEXT)

    models = {
        "pad_bed_king": build_bed(king=True),
        "pad_bed_queen": build_bed(king=False),
        "pad_chair_yellow": build_chair_yellow(),
        "pad_stool_white": build_tolix_stool(yellow=False),
        "pad_stool_yellow": build_tolix_stool(yellow=True),
        "pad_sofa_leather": build_chesterfield_sofa(red=False),
        "pad_sofa_red": build_chesterfield_sofa(red=True),
        "pad_chair_club": build_club_armchair(houndstooth=False),
        "pad_chair_hound": build_club_armchair(houndstooth=True),
        "pad_banquet_set": build_banquet_set(),
        "pad_treadmill": build_treadmill(),
        "pad_elliptical": build_elliptical(),
        "pad_bike": build_exercise_bike(),
        "pad_watercooler": build_watercooler(),
        "pad_jacuzzi": build_jacuzzi(),
        "pad_pooltable": build_pooltable(),
        "pad_heater": build_patio_heater(),
        "pad_chand_drum": build_chand_drum(),
        "pad_chand_fringe": build_chand_fringe(),
        "pad_chand_brass": build_chand_brass(),
        "pad_chand_linear": build_chand_linear(),
        "fox_chandelier": build_fox_chandelier(),
        "fox_palm": build_fan_palm(25.0),
        "fox_palm_sm": build_fan_palm(15.5),
        "fox_streetlamp": build_streetlamp(),
        "fox_clockpost": build_clockpost(),
        "bvm_bikerack": build_bikerack(),
        "fox_guitar": build_guitar(),
        "get_bus": build_get_bus(),
    }

    total_v = total_t = 0
    for name, mesh in models.items():
        nv, nt = mesh.save_md3(name)
        total_v += nv
        total_t += nt
        print(f"  {name:20s}: {nv:4d} verts, {nt:4d} tris")
    print(f"wrote {len(models)} MD3 models ({total_v} total verts, {total_t} total tris) to {OUT_DIR}")


if __name__ == "__main__":
    main()
