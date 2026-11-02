"""John Wave Grenade assets from MegaKartArena (D:\\vibe\\megamanquake), written into BakersfieldQuake:
  progs/fr_johnhead.spr32   the flying head: 16 views of the head spinning (frame = view)
  progs/fr_johnhand.spr32   John in your hand: 49 frames (0-7 idle sway, 8-48 the throw)
  progs/jw_wave.md3 + jw_wave.png   the tidal wave ring (profile revolved, rippled), scaled up by the game as it spreads
  sound/john/jwthrow.wav, jv00..jv22.wav   the 'John Wave' line and 23 voice clips
python -I build_john_assets.py"""
import math
import os
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib
from PIL import Image

SRC = "D:\\vibe\\megamanquake\\MegaKartArena\\public\\assets\\"
OUT = "G:\\Quake\\Combat\\BakersfieldQuake\\"


def spr32(path, frames, kind=2):
    """frames: list of RGBA images, each centred on the sprite origin. kind 2 = always faces the camera."""
    maxw = max(f.size[0] for f in frames)
    maxh = max(f.size[1] for f in frames)
    rad = math.sqrt((maxw / 2) ** 2 + (maxh / 2) ** 2)
    out = b"IDSP" + struct.pack("<iifiiifi", 32, kind, rad, maxw, maxh, len(frames), 0.0, 0)
    for im in frames:
        w, h = im.size
        out += struct.pack("<i", 0) + struct.pack("<iiii", -w // 2, h // 2, w, h) + im.tobytes()
    open(path, "wb").write(out)
    print("wrote", path, len(frames), "frames", round(len(out) / 1e6, 2), "MB")


def cells(sheet, cols, rows, cw, ch, count):
    im = Image.open(sheet).convert("RGBA")
    out = []
    for i in range(count):
        c, r = i % cols, i // cols
        out.append(im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)))
    return out


os.makedirs(OUT + "progs", exist_ok=True)

# ---- head: 16 views, 4x4 of 256x174. Shrink to 128 wide.
head = [c.resize((128, 87), Image.LANCZOS) for c in cells(SRC + "sprites\\johnhead.webp", 4, 4, 256, 174, 16)]
spr32(OUT + "progs\\fr_johnhead.spr32", head)

# ---- hand: 8 cols x 7 rows of 320x190, 49 frames. Shrink to 240x143.
hand = [c.resize((240, 143), Image.LANCZOS) for c in cells(SRC + "sprites\\johngun_vm.webp", 8, 7, 320, 190, 49)]
spr32(OUT + "progs\\fr_johnhand.spr32", hand)

# ---- sounds
sd = OUT + "sound\\john\\"
os.makedirs(sd, exist_ok=True)


def conv(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af",
                    "silenceremove=start_periods=1:start_threshold=-50dB,loudnorm=I=-16:TP=-2", "-ar", "22050", "-ac", "1", dst], check=True)


conv(SRC + "audio\\john\\johnwave.mp3", sd + "jwthrow.wav")
voices = sorted(f for f in os.listdir(SRC + "audio\\john\\voice") if f.endswith(".mp3"))
for i, f in enumerate(voices):
    conv(SRC + "audio\\john\\voice\\" + f, sd + "jv%02d.wav" % i)
print("sounds:", len(voices), "voice clips")

# ---- the wave: a ring of water. Profile (radius, height) revolved with a ripple, doubled-sided.
R = 100.0
H = 26.0
prof = [(0.24, 0.0), (0.58, 0.14), (0.86, 0.62), (1.00, 1.00), (1.08, 0.88), (0.99, 0.60)]
N = 48
verts, st, tris = [], [], []
for i, (pr, py) in enumerate(prof):
    for j in range(N + 1):
        a = 2 * math.pi * j / N
        rr = R * pr * (1 + 0.085 * math.sin(3 * a + 0.4) + 0.05 * math.sin(7 * a + 1.9))
        hh = H * py * (1 + 0.22 * math.sin(5 * a + 0.7) + 0.13 * math.sin(11 * a + 2.6))
        verts.append((rr * math.cos(a), rr * math.sin(a), hh))
        st.append((j / N * 6.0, i / (len(prof) - 1)))
W = N + 1
for i in range(len(prof) - 1):
    for j in range(N):
        a, b, c, d = i * W + j, i * W + j + 1, (i + 1) * W + j, (i + 1) * W + j + 1
        tris += [(a, b, c), (b, d, c), (a, c, b), (b, c, d)]


def norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


normals = [norm((v[0], v[1], 0.6 * R)) for v in verts]
surf = dict(name="wave", shader="progs/jw_wave", tris=tris, st=st, frames=[(verts, normals)])
md3lib.write(OUT + "progs\\jw_wave.md3", dict(name="jw_wave", surfaces=[surf], nframes=1))
# water texture: deep teal at the base (v=0) to pale foam at the crest (v~0.5-0.7), streaky
im = Image.new("RGB", (128, 64))
px = im.load()
import random
random.seed(3)
for y in range(64):
    v = y / 63.0
    base = (18 + 90 * v, 70 + 120 * v, 100 + 120 * v)
    for x in range(128):
        n = random.random() * 0.25 * (0.4 + v)
        px[x, y] = tuple(min(255, int(c * (0.8 + n) )) for c in base)
im.save(OUT + "progs\\jw_wave.png")
print("wave model written")
