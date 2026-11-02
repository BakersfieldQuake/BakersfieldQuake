"""Goo Gun sounds, synthesised from scratch (no samples):
  goofire.wav   pneumatic thunk + a wet bloop as the glob leaves the nozzle
  goosplat.wav  the glob slapping onto a wall and foaming up
  goopop.wav    a blob bursting (shot apart, or popping when someone is inside it)
  goostick.wav  a heavier wet slap when it lands on a player
python -I make_goo_sounds.py <sound_dir>   (writes <sound_dir>/weapons/goo*.wav)"""
import array
import math
import os
import random
import sys
import wave

RATE = 22050
OUT = os.path.join(sys.argv[1], "weapons")
os.makedirs(OUT, exist_ok=True)


def write(name, s):
    peak = max(abs(x) for x in s) or 1.0
    a = array.array("h", [int(x / peak * 29000) for x in s])
    w = wave.open(os.path.join(OUT, name), "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(a.tobytes())
    w.close()
    print("wrote", os.path.join(OUT, name))


def lowpass(s, cut):
    a = 1 - math.exp(-2 * math.pi * cut / RATE)
    y, out = 0.0, []
    for x in s:
        y += a * (x - y)
        out.append(y)
    return out


def noise(n, seed):
    r = random.Random(seed)
    return [r.uniform(-1, 1) for _ in range(n)]


def sweep(n, f0, f1, decay, start=0):
    out, ph = [0.0] * start, 0.0
    for i in range(n - start):
        t = i / RATE
        f = f0 + (f1 - f0) * min(1.0, t / (n / RATE))
        ph += 2 * math.pi * f / RATE
        out.append(math.sin(ph) * math.exp(-t / decay) * min(1.0, t / 0.002))
    return out


def mix(*parts):
    n = max(len(p) for p, _ in parts)
    out = [0.0] * n
    for p, g in parts:
        for i, x in enumerate(p):
            out[i] += x * g
    return out


def env(s, attack, decay):
    return [x * min(1.0, (i / RATE) / attack) * math.exp(-(i / RATE) / decay) for i, x in enumerate(s)]


def bubbles(n, count, seed, lo=350, hi=1100):
    r = random.Random(seed)
    out = [0.0] * n
    for _ in range(count):
        st = r.randrange(0, int(n * 0.7))
        f = r.uniform(lo, hi)
        b = sweep(int(RATE * 0.04), f, f * 1.8, 0.012)
        g = r.uniform(0.3, 1.0)
        for i, x in enumerate(b):
            if st + i < n:
                out[st + i] += x * g
    return out


n = int(RATE * 0.32)
write("goofire.wav", mix(
    (env(lowpass(noise(n, 1), 900), 0.002, 0.03), 0.9),       # the pneumatic puff
    (sweep(n, 110, 55, 0.05), 0.9),                            # thunk
    (sweep(n, 720, 190, 0.07, start=int(RATE * 0.01)), 0.55),  # bloop
    (bubbles(n, 4, 2, 500, 900), 0.25),
))

n = int(RATE * 0.4)
write("goosplat.wav", mix(
    (env(lowpass(noise(n, 3), 1400), 0.001, 0.045), 1.0),
    (sweep(n, 160, 70, 0.04), 0.6),
    (env(lowpass(noise(n, 4), 3000), 0.03, 0.12), 0.18),       # foam hiss as it swells
    (bubbles(n, 9, 5), 0.35),
))

n = int(RATE * 0.45)
write("goopop.wav", mix(
    (sweep(n, 520, 260, 0.03), 0.8),
    (env(lowpass(noise(n, 6), 2200), 0.001, 0.06), 0.7),
    (env(lowpass(noise(n, 7), 4500), 0.02, 0.18), 0.2),
    (bubbles(n, 7, 8, 600, 1500), 0.3),
))

n = int(RATE * 0.4)
write("goostick.wav", mix(
    (env(lowpass(noise(n, 9), 900), 0.001, 0.06), 1.0),
    (sweep(n, 95, 45, 0.08), 1.0),
    (bubbles(n, 6, 10, 250, 700), 0.4),
))
