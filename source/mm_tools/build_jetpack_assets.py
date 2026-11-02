"""The jetpack's swoosh and exhaust effects (see jetpack.qc):
  sound/jetpack/swoosh.wav                       a 2 s seamless loop of soft jet-engine roar (restarted on the beat while it burns)
  effectinfo.txt                                 jp_fire / jp_smoke / jp_dust / jp_burst (from jetpack_effectinfo.txt), between markers
The model (progs/jetpack.md3 + jetpack_*.png, 16 frames: 0-7 thrust, 8-15 idle) is build_jetpack.py's.
The "I'm floating" voice is sound/funny/imfloating.wav, made louder (sound/jetpack/floating.wav).
python -I build_jetpack_assets.py"""
import array
import math
import os
import random
import wave

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib
from PIL import Image, ImageDraw

ROOT = r"G:\Quake\Combat\BakersfieldQuake"
PROGS = os.path.join(ROOT, "progs")
SND = os.path.join(ROOT, "sound", "jetpack")
os.makedirs(SND, exist_ok=True)


def norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


def vnormals(verts, tris):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = [p1[i] - p0[i] for i in range(3)]
        w = [p2[i] - p0[i] for i in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        for i in (a, b, c):
            for k in range(3):
                acc[i][k] += n[k]
    return [norm(a) for a in acc]


class Mesh:
    def __init__(self):
        self.v, self.st, self.t, self.n = [], [], [], []

    def quad(self, p0, p1, p2, p3, n=None, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
        b = len(self.v)
        self.v += [p0, p1, p2, p3]
        self.st += list(uv)
        self.t += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        self.n += [n] * 4

    def tri(self, p0, p1, p2, uv=((0, 0), (1, 0), (0.5, 1))):
        b = len(self.v)
        self.v += [p0, p1, p2]
        self.st += list(uv)
        self.t.append((b, b + 1, b + 2))
        self.n += [None] * 3

    def box(self, cx, cy, cz, w, d, h):
        x, y, z = w / 2, d / 2, h / 2

        def P(a, b, c):
            return (cx + a, cy + b, cz + c)
        self.quad(P(-x, -y, -z), P(-x, y, -z), P(x, y, -z), P(x, -y, -z))
        self.quad(P(-x, -y, z), P(x, -y, z), P(x, y, z), P(-x, y, z))
        self.quad(P(-x, -y, -z), P(x, -y, -z), P(x, -y, z), P(-x, -y, z))
        self.quad(P(x, -y, -z), P(x, y, -z), P(x, y, z), P(x, -y, z))
        self.quad(P(x, y, -z), P(-x, y, -z), P(-x, y, z), P(x, y, z))
        self.quad(P(-x, y, -z), P(-x, -y, -z), P(-x, -y, z), P(-x, y, z))

    def cyl(self, cx, cy, z0, z1, r0, r1, segs=18, cap_top=True):
        """Vertical cylinder / cone frustum from radius r0 at z0 to r1 at z1; u wraps round, v runs up."""
        for i in range(segs):
            a0, a1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
            c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
            b = len(self.v)
            self.v += [(cx + r0 * c0, cy + r0 * s0, z0), (cx + r0 * c1, cy + r0 * s1, z0),
                       (cx + r1 * c1, cy + r1 * s1, z1), (cx + r1 * c0, cy + r1 * s0, z1)]
            self.st += [(i / segs, 0), ((i + 1) / segs, 0), ((i + 1) / segs, 1), (i / segs, 1)]
            self.t += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
            self.n += [(c0, s0, 0), (c1, s1, 0), (c1, s1, 0), (c0, s0, 0)]
        if cap_top and r1 > 0:
            for i in range(segs):
                a0, a1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
                b = len(self.v)
                self.v += [(cx, cy, z1), (cx + r1 * math.cos(a0), cy + r1 * math.sin(a0), z1),
                           (cx + r1 * math.cos(a1), cy + r1 * math.sin(a1), z1)]
                self.st += [(0.5, 0.5), (0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)),
                            (0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1))]
                self.t.append((b, b + 1, b + 2))
                self.n += [(0, 0, 1)] * 3

    def surface(self, name, shader):
        auto = vnormals(self.v, self.t)
        nn = [n if n is not None else a for n, a in zip(self.n, auto)]
        return dict(name=name, shader=shader, tris=self.t, st=self.st, frames=[(self.v, nn)])


# ---- the engine loop (swoosh.wav): soft filtered noise made circular (filter run over two copies, keep the second). Kept smooth on purpose:
# the first version (bright hiss, a 90 Hz hum, a 2 Hz wobble, a 0.5 s restart) was "way too annoying"; the next one, played at a tenth of
# the volume, was too faint ("you should hear a jetpack sound as you float around")
RATE = 22050
N = RATE * 2                               # 2 s, so it restarts rarely (the 0.5 s loop ticked)
rnd = random.Random(5)
noise = [rnd.uniform(-1, 1) for _ in range(N)]


def lowpass_circ(s, cut):
    a = 1 - math.exp(-2 * math.pi * cut / RATE)
    y, out = 0.0, []
    for x in s + s:
        y += a * (x - y)
        out.append(y)
    return out[len(s):]


# a jet engine bed: a soft roar (noise below 700 Hz), a little airy hiss (the band 1.2-3 kHz), a low rumble, and a slow 0.5 Hz breath
roar = lowpass_circ(noise, 700)
air = [a - b for a, b in zip(lowpass_circ(noise, 3000), lowpass_circ(noise, 1200))]
sig = []
for i in range(N):
    t = i / RATE
    rumble = math.sin(2 * math.pi * 56 * t) * 0.5 + math.sin(2 * math.pi * 84 * t + 1) * 0.3     # whole cycles in 2 s, so it loops
    lfo = 1 + 0.05 * math.sin(2 * math.pi * 0.5 * t)
    sig.append((roar[i] * 3.0 + air[i] * 2.2 + rumble) * lfo)
peak = max(abs(x) for x in sig) or 1.0
a = array.array("h", [int(x / peak * 22000) for x in sig])
w = wave.open(os.path.join(SND, "swoosh.wav"), "wb")
w.setnchannels(1)
w.setsampwidth(2)
w.setframerate(RATE)
w.writeframes(a.tobytes())
w.close()
print("wrote sound/jetpack/swoosh.wav")

# ---- "I'm floating" (sound/funny/imfloating.wav, the user's pick over the celeb pack's "Hmm, they seem to be floating.").
# 2026-11-02: "wayyyy quieter and more smooth". The old copy was +21 dB through a hard tanh limiter (harsh, -8 dBFS RMS) played on two
# channels; now there is no limiter, a gentle two-pass low-pass takes the edge off, short fades remove the clicks at both ends, and it is
# levelled to TARGET_RMS_DB. jetpack.qc plays it on one channel at JP_VOICE_VOL.
src_path = os.path.join(ROOT, "sound", "funny", "imfloating.wav")
if not os.path.exists(src_path):
    src_path = r"G:/Quake/Combat/_bakersfield_dev/staged_assets/sound/funny/imfloating.wav"
src = wave.open(src_path)
ch, sr, nfr = src.getnchannels(), src.getframerate(), src.getnframes()
x = array.array("h", src.readframes(nfr))
src.close()
mono = [sum(x[i:i + ch]) / ch for i in range(0, len(x), ch)]		# stereo to mono
if sr == 44100:
    mono = [(mono[i] + mono[i + 1]) / 2 for i in range(0, len(mono) - 1, 2)]		# 44.1 kHz to 22.05 kHz (average pairs)
    sr = 22050


def smooth(s, cut):
    """One-pole low-pass run forward then backward (no phase shift, twice the roll-off)."""
    k = 1 - math.exp(-2 * math.pi * cut / sr)
    for seq in (0, 1):
        y, out = 0.0, []
        for v in (s if seq == 0 else s[::-1]):
            y += k * (v - y)
            out.append(y)
        s = out if seq == 0 else out[::-1]
    return s


TARGET_RMS_DB = -20.0
mono = smooth(mono, 4500)
fin, fout = int(sr * 0.06), int(sr * 0.25)
for i in range(fin):
    mono[i] *= 0.5 - 0.5 * math.cos(math.pi * i / fin)
for i in range(fout):
    mono[len(mono) - 1 - i] *= 0.5 - 0.5 * math.cos(math.pi * i / fout)
cur = math.sqrt(sum(v * v for v in mono) / len(mono)) or 1.0
g = 32768.0 * 10 ** (TARGET_RMS_DB / 20.0) / cur
y = array.array("h", [max(-32767, min(32767, int(v * g))) for v in mono])
w = wave.open(os.path.join(SND, "floating.wav"), "wb")
w.setnchannels(1)
w.setsampwidth(2)
w.setframerate(sr)
w.writeframes(y.tobytes())
w.close()
rms = math.sqrt(sum(v * v for v in y) / len(y))
print("wrote sound/jetpack/floating.wav (rms %.1f dBFS, peak %d, %.2f s)" % (20 * math.log10(rms / 32768.0), max(abs(v) for v in y), len(y) / sr))

# ---- the exhaust effects, into the game's effectinfo.txt between markers so a rerun replaces them
fx = os.path.join(ROOT, "effectinfo.txt")
begin, end = b"// ---- Jetpack begin", b"// ---- Jetpack end"
raw = open(fx, "rb").read()
if begin in raw:
    raw = raw[:raw.index(begin)].rstrip(b"\r\n") + b"\r\n" + raw[raw.index(end) + len(end):].lstrip(b"\r\n")
add = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jetpack_effectinfo.txt"), "rb").read()
add = add.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
open(fx, "wb").write(raw.rstrip(b"\r\n") + b"\r\n\r\n" + begin + b"\r\n" + add + end + b"\r\n")
print("wrote jetpack effects into effectinfo.txt")
