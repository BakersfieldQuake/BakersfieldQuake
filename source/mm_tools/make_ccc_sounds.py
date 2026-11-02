"""Synthesises the CCC gun's bounce sound (pure Python, no numpy):
  bounce.wav - a short bright "boing-ding": a fast upward pitch bend that settles on a high C, with a bell overtone
python -I make_ccc_sounds.py <outdir>      (BakersfieldQuake/sound/ccc)"""
import math
import os
import struct
import sys
import wave

RATE = 22050
C6 = 1046.5


def write(path, samples, peak):
    m = max(abs(s) for s in samples) or 1.0
    k = peak / m
    data = b"".join(struct.pack("<h", int(max(-1, min(1, s * k)) * 32767)) for s in samples)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(data)
    print("wrote", path, "%.2fs" % (len(samples) / RATE))


def bounce():
    n = int(RATE * 0.32)
    out = []
    ph = 0.0
    for i in range(n):
        t = i / RATE
        # the boing: starts a fifth below the C and glides up into it in about 50 ms
        bend = 1.0 - 0.33 * math.exp(-t / 0.018)
        ph += 2 * math.pi * C6 * bend / RATE
        env = math.exp(-t / 0.09) * min(1.0, t / 0.002)
        tone = math.sin(ph) + 0.35 * math.sin(2 * ph) + 0.15 * math.sin(3 * ph)
        # the ding: an inharmonic bell partial that rings on after the boing
        bell = math.sin(2 * math.pi * C6 * 2.76 * t) * math.exp(-t / 0.07)
        out.append(env * tone + 0.35 * bell)
    f = int(RATE * 0.004)
    for i in range(f):
        out[-1 - i] *= i / f
    return out


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "G:/Quake/Combat/BakersfieldQuake/sound/ccc"
    os.makedirs(d, exist_ok=True)
    write(os.path.join(d, "bounce.wav"), bounce(), 0.8)
