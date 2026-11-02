"""The JohnWave grenade's water splash (it replaces the explosion): two Darkplaces SPR32 sprites.

  progs/jw_splash.spr32   facing the camera: a wavy blue burst of water with flying droplets (8 frames)
  progs/jw_ripple.spr32   lying flat on the floor: wavy rings spreading out (10 frames)

python3 -E -P build_splash_sprites.py [--preview DIR]
"""
import math
import os
import struct
import sys

import numpy as np
from PIL import Image

PROGS = r"G:\Quake\Combat\BakersfieldQuake\progs"
PREVIEW = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
SS = 2                                           # supersampling

DEEP = np.array([18, 78, 196], np.float32)
MID = np.array([48, 140, 240], np.float32)
FOAM = np.array([190, 236, 255], np.float32)


def ease(p):
    return 1 - (1 - p) ** 3


def polar(n):
    c = (np.arange(n * SS) + 0.5) / SS - n / 2
    X, Y = np.meshgrid(c, -c)
    return np.hypot(X, Y), np.arctan2(Y, X), X, Y


def band(r, inner, outer, soft=1.5):
    """1 between inner and outer radius (arrays allowed), soft edges in pixels"""
    a = np.clip((r - inner) / soft + 0.5, 0, 1)
    b = np.clip((outer - r) / soft + 0.5, 0, 1)
    return a * b


def over(rgb, a, col, alpha):
    """paint col with coverage alpha over (rgb, a), premultiplied-free 'over'"""
    alpha = np.clip(alpha, 0, 1)[..., None]
    col = np.broadcast_to(col, rgb.shape)
    out_a = alpha + a[..., None] * (1 - alpha)
    rgb[:] = np.where(out_a > 1e-6, (col * alpha + rgb * a[..., None] * (1 - alpha)) / np.maximum(out_a, 1e-6), rgb)
    a[:] = out_a[..., 0]


def finish(rgb, a, n):
    img = np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA").resize((n, n), Image.LANCZOS)


def splash_frame(p, n=160, seed=7):
    r, phi, X, Y = polar(n)
    rgb = np.zeros(r.shape + (3,), np.float32)
    a = np.zeros(r.shape, np.float32)
    R = (16 + 58 * ease(p)) * SS / SS
    fade = (1 - p) ** 0.9
    # main body: a wavy blob of water that swells and thins out
    wob = 1 + 0.10 * np.sin(3 * phi + 1.3 + 2 * p) + 0.08 * np.sin(5 * phi + 0.4 - 3 * p) + 0.05 * np.sin(11 * phi + 2 + 6 * p)
    body_r = R * 0.72 * wob
    body = band(r, -1, body_r, 2.5)
    shade = np.clip(r / np.maximum(body_r, 1e-3), 0, 1)
    col = DEEP[None, None] * (1 - shade[..., None]) + MID[None, None] * shade[..., None]
    over(rgb, a, col, body * (0.85 - 0.55 * p) * fade)
    # bright wavy crest round the edge, and a second one lagging inside
    for k, (rad, wd, amp, freq, ph) in enumerate(((R, 6.5, 0.07, 7, 0.0), (R * 0.55, 4.0, 0.09, 5, 1.7))):
        rr = rad * (1 + amp * np.sin(freq * phi + ph + 6 * p) + 0.5 * amp * np.sin(2 * freq * phi - 4 * p)
                     + 0.8 * amp * np.sin(3 * phi + ph * 2 - 2 * p))
        w = wd * (1 - 0.5 * p)
        crest = band(r, rr - w, rr + w * 0.4, 1.8)
        over(rgb, a, MID * 0.4 + FOAM * 0.6, crest * fade * (0.95 if k == 0 else 0.7))
        over(rgb, a, FOAM, band(r, rr - w * 0.35, rr + w * 0.2, 1.2) * fade * 0.8)
    # droplets thrown out past the crest, falling a little
    rng = np.random.default_rng(seed)
    for i in range(30):
        ang = rng.uniform(0, 2 * math.pi)
        dist = R * (1.05 + rng.uniform(0, 0.55)) + 10 * p
        dx, dy = dist * math.cos(ang), dist * math.sin(ang) - 30 * p * p
        sz = rng.uniform(1.6, 3.6) * (1 - 0.4 * p)
        d = np.hypot(X - dx, Y - dy)
        over(rgb, a, FOAM if i % 3 else MID, np.clip((sz - d) / 0.8 + 0.5, 0, 1) * fade)
    # highlight sheen
    sheen = np.exp(-(((X + R * 0.25) / (R * 0.35 + 1)) ** 2 + ((Y - R * 0.3) / (R * 0.18 + 1)) ** 2))
    over(rgb, a, np.array([235, 250, 255], np.float32), sheen * 0.35 * fade * body)
    return finish(rgb, a, n)


def ripple_frame(p, n=256):
    r, phi, X, Y = polar(n)
    rgb = np.zeros(r.shape + (3,), np.float32)
    a = np.zeros(r.shape, np.float32)
    for i in range(3):
        q = p - i * 0.18
        if q <= 0:
            continue
        rr = (12 + 110 * ease(min(q, 1))) * (1 + 0.06 * np.sin(8 * phi + 7 * q + i) + 0.03 * np.sin(15 * phi - 5 * q))
        w = 7 * (1 - 0.6 * q) + 2
        f = (1 - min(q, 1)) ** 1.1 * (1 - 0.25 * i)
        over(rgb, a, MID, band(r, rr - w, rr + w, 2.5) * f * 0.75)
        over(rgb, a, FOAM, band(r, rr - w * 0.3, rr + w * 0.25, 1.5) * f * 0.9)
    # a pool of water in the middle, fading out
    pool = np.clip(1 - r / (30 + 50 * p), 0, 1) ** 0.6 * (1 - p) ** 1.5
    over(rgb, a, DEEP, pool * 0.6)
    return finish(rgb, a, n)


def write_spr32(path, frames, sprite_type):
    w, h = frames[0].size
    rad = math.hypot(w / 2, h / 2)
    out = b"IDSP" + struct.pack("<iifiiifi", 32, sprite_type, rad, w, h, len(frames), 0.0, 0)
    for im in frames:
        out += struct.pack("<i", 0) + struct.pack("<iiii", -w // 2, h // 2, w, h) + im.tobytes()
    open(path, "wb").write(out)
    print("wrote", path, len(frames), "frames", round(len(out) / 1e6, 2), "MB")


def main():
    splash = [splash_frame(i / 7) for i in range(8)]
    ripple = [ripple_frame(i / 9) for i in range(10)]
    write_spr32(os.path.join(PROGS, "jw_splash.spr32"), splash, 2)    # SPR_VP_PARALLEL: faces the camera
    write_spr32(os.path.join(PROGS, "jw_ripple.spr32"), ripple, 3)    # SPR_ORIENTED: lies in the entity's plane
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        for name, fr in (("splash", splash), ("ripple", ripple)):
            w = fr[0].width
            sheet = Image.new("RGBA", (w * len(fr), w), (40, 40, 44, 255))
            for i, im in enumerate(fr):
                sheet.alpha_composite(im, (i * w, 0))
            sheet.convert("RGB").save(os.path.join(PREVIEW, "jw_%s_frames.png" % name))


if __name__ == "__main__":
    main()
