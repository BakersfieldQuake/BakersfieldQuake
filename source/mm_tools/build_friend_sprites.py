"""Bakes the MegaKartArena friends (8-direction photo sprites) into Quake SPR32 sprites, progs/fr_<name>.spr32.

Frame layout (FRIEND_* constants in friends.qc rely on it):
  0-7    idle, one per direction
  8-55   run: direction d uses frames 8 + d*6 .. 8 + d*6 + 5
Direction d is the view from rel = 45*d degrees, measured from the way the friend faces round to the viewer
(d=0 front, d=2 we see their left-facing side, d=4 back). The sprite origin is at the feet.
python -I build_friend_sprites.py <sprites_dir> <outdir> name [name ...]"""
import json
import math
import os
import struct
import sys

from PIL import Image

src, outdir, names = sys.argv[1], sys.argv[2], sys.argv[3:]
HEIGHT = 112        # pixels per cell height in the game sprite (the entity is drawn at .scale 0.5)
RUN = 6             # run frames kept per direction

os.makedirs(os.path.join(outdir, "progs"), exist_ok=True)
for name in names:
    meta = json.load(open(os.path.join(src, name + "_hi.json")))
    pages = [Image.open(os.path.join(src, p["file"])).convert("RGBA") for p in meta["pages"]]
    cw, ch = meta["cellW"], meta["cellH"]
    s = HEIGHT / ch
    ndir = meta["dirCount"]
    step = ndir // 8          # larry has 16 directions: keep every other one

    def cell(page, idx, anchor_x):
        p = meta["pages"][page]
        col, row = idx % p["cols"], idx // p["cols"]
        im = pages[page].crop((col * cw, row * ch, (col + 1) * cw, (row + 1) * ch))
        w = max(1, round(cw * s))
        im = im.resize((w, HEIGHT), Image.LANCZOS)
        ox = -round(anchor_x * s)
        oy = round(meta["anchorY"] * s)
        return im, ox, oy

    frames = []
    for d in range(8):
        e = meta["anims"]["idle"]["dirs"][d * step]
        frames.append(cell(e["page"], e["start"], e["anchorX"]))
    for d in range(8):
        e = meta["anims"]["run"]["dirs"][d * step]
        n = e["count"]
        for k in range(RUN):
            i = min(n - 1, int(k * n / RUN))
            frames.append(cell(e["page"], e["start"] + i, e["anchorX"]))

    maxw = max(f[0].size[0] for f in frames)
    rad = math.sqrt((maxw / 2) ** 2 + HEIGHT ** 2)
    out = b"IDSP" + struct.pack("<iifiiifi", 32, 0, rad, maxw, HEIGHT, len(frames), 0.0, 0)
    for im, ox, oy in frames:
        w, h = im.size
        out += struct.pack("<i", 0) + struct.pack("<iiii", ox, oy, w, h) + im.tobytes()
    path = os.path.join(outdir, "progs", "fr_%s.spr32" % name)
    open(path, "wb").write(out)
    print("wrote", path, len(frames), "frames", round(len(out) / 1e6, 2), "MB")
