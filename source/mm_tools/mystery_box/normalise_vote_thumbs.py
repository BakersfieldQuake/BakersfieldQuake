"""Match the brightness / contrast of the Mystery Box vote thumbnails.

make_vote_thumbs.py writes un-toned, cropped and equal-height frames to vote_thumbs_raw/ and then calls run() here,
which writes the final thumbnails to vote_thumbs/:
  - the luminance of the opaque pixels of every image is moved to ONE shared mean and spread (contrast), so dark 3D
    renders and light sprites look alike on the dark card background (hue kept, highlights clipped softly)
  - the geometry (crop to visible content, same height, common baseline) has already been done upstream.
Run standalone (python normalise_vote_thumbs.py) to redo only the tone step; if vote_thumbs_raw/ does not exist yet it is
filled from the current vote_thumbs/.
Needs numpy + PIL.
"""
import glob
import os
import shutil

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM = os.path.dirname(HERE)
BASE = os.path.join(MM, "out", "mystery_box")
RAW = os.path.join(BASE, "vote_thumbs_raw")
OUT = os.path.join(BASE, "vote_thumbs")
TARGET_MEAN = 0.40     # shared mean luminance of the opaque pixels (readable on the dark card)
TARGET_STD = 0.20      # shared contrast
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def stats(rgb, a):
    y = rgb @ LUMA
    w = a
    m = float((y * w).sum() / max(w.sum(), 1e-6))
    s = float(np.sqrt((((y - m) ** 2) * w).sum() / max(w.sum(), 1e-6)))
    return m, s


def tone(rgb, a, mt, st):
    y = rgb @ LUMA
    m, s = stats(rgb, a)
    k = float(np.clip(st / max(s, 1e-3), 0.7, 1.6))
    y1 = np.clip(mt + k * (y - m), 0, 1)
    chroma = rgb - y[..., None]
    w = a

    def build(g):
        y2 = np.power(y1, g)
        out = np.clip(y2[..., None] + chroma, 0, 1)
        return out

    lo, hi = 0.2, 5.0                      # bisect gamma so the weighted mean luminance hits the target after clipping
    for _ in range(30):
        g = (lo * hi) ** 0.5
        o = build(g)
        mm = float(((o @ LUMA) * w).sum() / max(w.sum(), 1e-6))
        if mm > mt:
            lo = g
        else:
            hi = g
    return build((lo * hi) ** 0.5)


def run():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    if not glob.glob(os.path.join(RAW, "*.png")):
        for f in glob.glob(os.path.join(OUT, "*.png")):
            shutil.copy(f, RAW)
    files = sorted(glob.glob(os.path.join(RAW, "*.png")))
    imgs = {}
    ms, ss = [], []
    for f in files:
        im = np.asarray(Image.open(f).convert("RGBA"), np.float32) / 255.0
        rgb, a = im[..., :3], im[..., 3]
        m, s = stats(rgb, a)
        imgs[f] = (rgb, a, m, s)
        ms.append(m)
        ss.append(s)
    mt, st = TARGET_MEAN, TARGET_STD
    print("shared target luminance mean %.3f  std %.3f (raw medians %.3f / %.3f)" % (mt, st, float(np.median(ms)), float(np.median(ss))))
    for f in files:
        rgb, a, m, s = imgs[f]
        out = tone(rgb, a, mt, st)
        m2, s2 = stats(out, a)
        res = np.dstack([out, a])
        Image.fromarray((res * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, os.path.basename(f)), optimize=True)
        print("%-28s mean %.3f -> %.3f   std %.3f -> %.3f" % (os.path.basename(f), m, m2, s, s2))


if __name__ == "__main__":
    run()
