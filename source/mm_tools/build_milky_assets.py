"""Milky Gun assets, written straight into BakersfieldQuake (the Pink Lady sprite itself is build_pinklady_assets.py):
  sound/milky/song.ogg       the song from SONG_FROM to the end (rebuilt when <song.mp3> is passed)
  sound/milky/fire.wav       the "need sucky sucky now mommy" line (FIRE_CUT), the shot
  progs/milksplat_0..5.png   bright creamy-white splats of milk: 0-2 round (floors/ceilings/globs), 3-5 with rich drips (walls)
  progs/milksplat.md3        6 single-sided cards in one model and 6 frames, 24 units across, facing +X
  scripts/milky.shader       fullbright self-lit soft-edged splats (cull none, polygonoffset, blendfunc blend, rgbGen identity)
  gfx/milkdrips.png          thick glossy creamy-white screen milk drips overlay (csqc/bm_hud.qc)
  effectinfo.txt             the Milky Gun block (from milky_effectinfo.txt), between markers so a rerun replaces it
python3.13 build_milky_assets.py [song.mp3] [BakersfieldQuake dir]"""
import math
import os
import random
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SONG = sys.argv[1] if (len(sys.argv) > 1 and os.path.isfile(sys.argv[1]) and not os.path.isdir(sys.argv[1])) else None
if SONG is not None:
    MOD = sys.argv[2] if len(sys.argv) > 2 else r"G:\Quake\Combat\BakersfieldQuake"
else:
    MOD = sys.argv[1] if (len(sys.argv) > 1 and os.path.isdir(sys.argv[1])) else r"G:\Quake\Combat\BakersfieldQuake"

HERE = os.path.dirname(os.path.abspath(__file__))
PROGS = os.path.join(MOD, "progs")
GFX = os.path.join(MOD, "gfx")
SONG_FROM = 20.1            # picked in the sound inspector page (was 16.0: "crop out the first like 16 seconds")
SONG_TO = 125.3             # the track is silent after this
FIRE_CUT = (68.9, 71.7)     # picked in the sound inspector page: "sucky sucky now mommy"
TEX = 256
HALF = 12.0
MILK_BASE = (242.0, 245.0, 239.0)   # rich creamy milk white in full sRGB (specular peaks at 255, 255, 255)
VARIANTS = 6


def sounds():
    if SONG is None:
        return
    out = os.path.join(MOD, "sound", "milky")
    os.makedirs(out, exist_ok=True)
    dur = SONG_TO - SONG_FROM
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.2f" % SONG_FROM, "-t", "%.2f" % dur, "-i", SONG,
                    "-af", "afade=t=in:st=0:d=0.4,afade=t=out:st=%.2f:d=1.5,loudnorm=I=-8:TP=-0.3,alimiter=limit=0.97" % (dur - 1.5),
                    "-ac", "1", "-ar", "44100", "-c:a", "libvorbis", "-q:a", "4", os.path.join(out, "song.ogg")], check=True)
    a, b = FIRE_CUT
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.2f" % a, "-t", "%.2f" % (b - a), "-i", SONG,
                    "-af", "afade=t=in:st=0:d=0.03,afade=t=out:st=%.2f:d=0.25,loudnorm=I=-9:TP=-0.3" % (b - a - 0.25),
                    "-ac", "1", "-ar", "22050", "-sample_fmt", "s16", os.path.join(out, "fire.wav")], check=True)


def splat(seed, runs):
    """Bright creamy milk splat with 3D pearlescent droplet highlights and lots of wall runs & hanging teardrops."""
    rnd = random.Random(seed)
    big = TEX * 2
    a = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(a)
    cx = big * 0.5
    cy = big * (0.31 if runs else 0.50)
    r0 = big * (0.19 if runs else 0.24)

    # Lumpy thick center splash
    for _ in range(16):
        ang = rnd.uniform(0, 2 * math.pi)
        off = rnd.uniform(0, r0 * 0.58)
        r = r0 * rnd.uniform(0.45, 0.82)
        x, y = cx + math.cos(ang) * off, cy + math.sin(ang) * off
        d.ellipse((x - r, y - r, x + r, y + r), fill=255)

    # Radial splash fingers ending in fat beads
    for _ in range(rnd.randint(12, 18)):
        ang = rnd.uniform(0, 2 * math.pi)
        ln = r0 * rnd.uniform(0.95, 1.95)
        w = big * rnd.uniform(0.012, 0.028)
        x0, y0 = cx + math.cos(ang) * r0 * 0.45, cy + math.sin(ang) * r0 * 0.45
        x1, y1 = cx + math.cos(ang) * ln, cy + math.sin(ang) * ln
        d.line((x0, y0, x1, y1), fill=255, width=max(2, int(w * 2)))
        if rnd.random() < 0.8:
            rr = w * rnd.uniform(1.3, 2.2)
            d.ellipse((x1 - rr, y1 - rr, x1 + rr, y1 + rr), fill=255)

    # Satellite droplets scattered around
    for _ in range(rnd.randint(20, 32)):
        ang = rnd.uniform(0, 2 * math.pi)
        dist = r0 * rnd.uniform(1.12, 2.08)
        rr = big * rnd.uniform(0.007, 0.022)
        x, y = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
        if 8 < x < big - 8 and 8 < y < big - 8:
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)

    # Rich wall runs: 7..10 glossy milk streams running down to fat hanging teardrops + detached falling drops!
    if runs:
        n_runs = rnd.randint(7, 10)
        for i in range(n_runs):
            u = (i + rnd.uniform(0.18, 0.82)) / float(n_runs)
            x = cx + (u * 2.0 - 1.0) * r0 * 1.15
            w = big * rnd.uniform(0.011, 0.026)
            y_start = cy + rnd.uniform(-0.15, 0.35) * r0
            y1 = y_start + rnd.uniform(0.28, 0.96) * (big * 0.90 - y_start)
            d.rectangle((x - w, y_start, x + w, y1), fill=255)
            # Intermediate liquid bead bulge mid-run
            if y1 - y_start > big * 0.22:
                ym = y_start + (y1 - y_start) * rnd.uniform(0.42, 0.68)
                rb = w * rnd.uniform(1.35, 1.75)
                d.ellipse((x - rb, ym - rb * 1.1, x + rb, ym + rb * 1.2), fill=255)
            # Plump teardrop bulb at bottom of run
            rr = w * rnd.uniform(1.65, 2.35)
            d.ellipse((x - rr, y1 - rr * 0.85, x + rr, y1 + rr * 1.35), fill=255)
            # Detached falling milk drop below some runs
            if rnd.random() < 0.60 and y1 + rr * 3.8 < big - 10:
                yd = y1 + rr * rnd.uniform(2.3, 3.6)
                rd = rr * rnd.uniform(0.62, 0.88)
                d.ellipse((x - rd, yd - rd * 1.15, x + rd, yd + rd * 1.15), fill=255)

    m = 6
    a = a.crop((m, m, big - m, big - m)).resize((big, big))
    a = a.filter(ImageFilter.GaussianBlur(2.2)).point(lambda v: 0 if v < 68 else min(255, int((v - 68) * 255 / 118)))
    a = a.resize((TEX, TEX), Image.LANCZOS)

    # 3D liquid milk shading: soft warm-cream meniscus rim + rich bright white core + glossy 255 specular sheen
    a_np = np.array(a, dtype=np.float32) / 255.0
    thick = cv2.GaussianBlur(a_np, (0, 0), 4.2)
    gx = cv2.Sobel(thick, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(thick, cv2.CV_32F, 0, 1, ksize=3)
    spec = np.clip(-0.48 * gx - 0.62 * gy + 0.25 * thick, 0.0, 1.0)
    glint = np.power(spec, 2.2)

    body = 0.90 + 0.10 * np.clip(thick * 1.35, 0.0, 1.0)
    rgb = np.zeros((TEX, TEX, 3), dtype=np.uint8)
    for ch, base_c in enumerate(MILK_BASE):
        val = base_c * body + 22.0 * glint
        rgb[..., ch] = np.clip(np.round(val), 0, 255).astype(np.uint8)

    a_u8 = np.array(a, dtype=np.uint8)
    rgb[a_u8 == 0] = 0
    return Image.fromarray(np.dstack([rgb, a_u8]), "RGBA")


def build_screen_milkdrips():
    """Upgrade gfx/milkdrips.png: bright, thick, glossy creamy-white milk drips & beads running down the screen."""
    os.makedirs(GFX, exist_ok=True)
    W = H = 512
    rnd = random.Random(20261101)
    a = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(a)

    # 38 vertical milk streams + splash blobs + hanging teardrop beads (seamless tile feel top-to-bottom)
    for _ in range(26):
        cx = rnd.uniform(12, W - 12)
        cy = rnd.uniform(16, H - 40)
        rx = rnd.uniform(10, 28)
        ry = rx * rnd.uniform(0.78, 1.12)
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=235)
        n_tails = rnd.randint(1, 3)
        for _ in range(n_tails):
            tx = cx + rnd.uniform(-rx * 0.65, rx * 0.65)
            tw = rnd.uniform(2.2, 6.2)
            tlen = rnd.uniform(45, 210)
            y1 = min(H - 6, cy + tlen)
            d.rectangle((tx - tw, cy, tx + tw, y1), fill=245)
            rb = tw * rnd.uniform(1.45, 2.15)
            d.ellipse((tx - rb, y1 - rb * 0.8, tx + rb, y1 + rb * 1.25), fill=255)

    for _ in range(22):
        tx = rnd.uniform(6, W - 6)
        y0 = rnd.uniform(0, H * 0.55)
        tw = rnd.uniform(1.8, 5.0)
        y1 = min(H - 6, y0 + rnd.uniform(60, 240))
        d.rectangle((tx - tw, y0, tx + tw, y1), fill=240)
        rb = tw * rnd.uniform(1.5, 2.2)
        d.ellipse((tx - rb, y1 - rb * 0.8, tx + rb, y1 + rb * 1.3), fill=255)

    for _ in range(35):
        bx = rnd.uniform(8, W - 8)
        by = rnd.uniform(8, H - 8)
        br = rnd.uniform(2.5, 7.5)
        d.ellipse((bx - br, by - br * 1.15, bx + br, by + br * 1.15), fill=235)

    a = a.filter(ImageFilter.GaussianBlur(1.6))
    a_np = np.array(a, dtype=np.float32) / 255.0
    a_sharp = np.clip((a_np - 0.16) / 0.58, 0.0, 1.0)
    thick = cv2.GaussianBlur(a_sharp, (0, 0), 3.0)
    gx = cv2.Sobel(thick, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(thick, cv2.CV_32F, 0, 1, ksize=3)
    glint = np.power(np.clip(-0.5 * gx - 0.6 * gy + 0.3 * thick, 0.0, 1.0), 2.0)

    r = np.clip(242.0 + 10.0 * thick + 14.0 * glint, 0.0, 255.0).round().astype(np.uint8)
    g = np.clip(245.0 + 8.0 * thick + 12.0 * glint, 0.0, 255.0).round().astype(np.uint8)
    b = np.clip(240.0 + 10.0 * thick + 15.0 * glint, 0.0, 255.0).round().astype(np.uint8)
    a_u8 = np.clip(np.round(a_sharp * 245.0), 0, 255).astype(np.uint8)
    r[a_u8 == 0] = 0
    g[a_u8 == 0] = 0
    b[a_u8 == 0] = 0
    Image.fromarray(np.dstack([r, g, b, a_u8]), "RGBA").save(os.path.join(GFX, "milkdrips.png"))


def textures():
    sheet = Image.new("RGBA", (VARIANTS * 128, 128), (40, 42, 50, 255))
    for k in range(VARIANTS):
        im = splat(100 + k, runs=k >= 3)
        im.save(os.path.join(PROGS, "milksplat_%d.png" % k))
        small = im.resize((128, 128), Image.LANCZOS)
        sheet.paste(small, (k * 128, 0), small)
    out = os.path.join(HERE, "out", "milky")
    os.makedirs(out, exist_ok=True)
    sheet.save(os.path.join(out, "splats.png"))


def shaders():
    os.makedirs(os.path.join(MOD, "scripts"), exist_ok=True)
    with open(os.path.join(MOD, "scripts", "milky.shader"), "w", newline="\n") as f:
        f.write("// written by mm_tools/build_milky_assets.py\n")
        for k in range(VARIANTS):
            f.write(
                "progs/milksplat_v%d\n{\n\tcull none\n\tnopicmip\n\tpolygonoffset\n\t{\n\t\tmap progs/milksplat_%d\n\t\tblendfunc blend\n\t\trgbGen identity\n\t}\n}\n"
                % (k, k)
            )


def model():
    """Single-sided card per variant with `cull none` so `blendfunc blend` never double-blends."""
    card = [(0.0, HALF, -HALF), (0.0, HALF, HALF), (0.0, -HALF, HALF), (0.0, -HALF, -HALF)]
    nothing = [(0.0, 0.0, 0.0)] * 4
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    surfaces = []
    for k in range(VARIANTS):
        frames = [(card if f == k else nothing, [(1.0, 0.0, 0.0)] * 4) for f in range(VARIANTS)]
        surfaces.append(dict(name="splat%d" % k, shader="progs/milksplat_v%d" % k, tris=tris, st=st, frames=frames))
    md3lib.write(os.path.join(PROGS, "milksplat.md3"), dict(name="milksplat", surfaces=surfaces, nframes=VARIANTS))


def effects():
    fx = os.path.join(MOD, "effectinfo.txt")
    begin, end = b"// ---- Milky Gun begin", b"// ---- Milky Gun end"
    raw = open(fx, "rb").read()
    if begin in raw:
        raw = raw[:raw.index(begin)].rstrip(b"\r\n") + b"\r\n" + raw[raw.index(end) + len(end):].lstrip(b"\r\n")
    add = open(os.path.join(HERE, "milky_effectinfo.txt"), "rb").read()
    add = add.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n").rstrip(b"\r\n") + b"\r\n"
    open(fx, "wb").write(raw.rstrip(b"\r\n") + b"\r\n\r\n" + add)


os.makedirs(PROGS, exist_ok=True)
sounds()
textures()
build_screen_milkdrips()
shaders()
model()
effects()
print("milky assets written to", MOD)
