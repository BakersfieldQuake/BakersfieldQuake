"""Synthesises the joke grenade sounds: 12 shoot, 12 explode, 12 bounce (22050 Hz mono 16-bit wavs, Quake-ready).

python3 -E -P make_grenade_sounds.py [OUT_DIR]      (default: out/sound/grenade_new next to this file)
Everything is made from sine/saw/square oscillators, filtered noise and a little reverb; nothing is sampled.
Names: shoot_NN_*.wav, boom_NN_*.wav, bounce_NN_*.wav.  In game they would live in sound/grenade/.
"""
import os
import sys
import wave

import numpy as np
from scipy import signal

SR = 44100          # synthesis rate; written out at SR // 2
rng = np.random.default_rng(1337)
TAU = 2 * np.pi


# ---------------------------------------------------------------- building blocks
def T(d):
    return np.arange(int(d * SR)) / SR


def osc(freq, shape="sine"):
    p = np.cumsum(freq) / SR
    if shape == "sine":
        return np.sin(TAU * p)
    p = p % 1.0
    if shape == "saw":
        return 2 * p - 1
    if shape == "square":
        return np.where(p < 0.5, 1.0, -1.0)
    return 2 * np.abs(2 * p - 1) - 1


def noise(n):
    return rng.uniform(-1, 1, n)


def sweep(f0, f1, d):
    t = T(d)
    return f0 * (f1 / f0) ** (t / d)


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def formants(x, centres, width=0.12):
    return sum(bp(x, f * (1 - width), f * (1 + width)) for f in centres)


def attack(t, a):
    return np.minimum(1.0, t / a)


def mix(*parts):
    """parts: (start_seconds, samples, gain)"""
    n = max(int(s * SR) + len(x) for s, x, _ in parts)
    out = np.zeros(n)
    for s, x, g in parts:
        i = int(s * SR)
        out[i:i + len(x)] += x * g
    return out


def reverb(x, rt=0.5, wet=0.3):
    n = int(rt * SR)
    ir = noise(n) * np.exp(-np.arange(n) / SR * 6.9 / rt)
    ir = lp(ir, 5000)
    x = np.concatenate([x, np.zeros(n)])
    y = signal.fftconvolve(x, ir)[:len(x)]
    y = y / (np.abs(y).max() + 1e-9) * np.abs(x).max()
    return x + wet * y


# ---------------------------------------------------------------- voices
def boom_core(d, f0=130, f1=38, decay=2.8, noise_amt=0.5, lp_noise=900):
    t = T(d)
    f = f1 + (f0 - f1) * np.exp(-t * 14)
    x = osc(f) * np.exp(-t * decay)
    x += lp(noise(len(t)), lp_noise) * np.exp(-t * decay * 1.4) * noise_amt
    return x * attack(t, 0.002)


def fart(d, f0=65, f1=35, wob=25, bright=900):
    t = T(d)
    k = len(t)
    jit = lp(noise(k), 60) * 25
    f = f0 + (f1 - f0) * t / d + 10 * np.sin(TAU * wob * t) + jit
    x = osc(f, "saw")
    x *= 0.55 + 0.45 * np.sign(np.sin(TAU * wob * t + 0.5 * np.sin(TAU * 3 * t)))
    x = lp(x, bright) + 0.25 * lp(noise(k), 2500) * (0.4 + 0.6 * (t / d))
    return x * attack(t, 0.01) * (1 - (t / d) ** 5)


def horn(f, d, att=0.01, ratios=(1, 1.26, 1.5)):
    t = T(d)
    vib = 1 + 0.003 * np.sin(TAU * 5 * t)
    x = sum(osc(f * r * vib * (1 + 0.002 * i), "saw") for i, r in enumerate(ratios))
    x = np.tanh(lp(x, 3500) * 1.6)
    return x * attack(t, att) * np.minimum(1.0, (d - t) / 0.03)


def duck(d=0.22, f0=380, f1=300):
    t = T(d)
    f = np.linspace(f0, f1, len(t))
    x = osc(f, "saw") * (0.65 + 0.35 * np.sin(TAU * 85 * t))
    x = formants(x, [800, 1700, 2500])
    return x * attack(t, 0.008) * np.exp(-t * 6) * np.minimum(1.0, (d - t) / 0.02)


def kazoo(f0, f1, d):
    t = T(d)
    f = np.linspace(f0, f1, len(t)) * (1 + 0.03 * np.sin(TAU * 7 * t))
    x = osc(f, "saw") + 0.5 * osc(f * 2, "square")
    x = bp(x, 800, 2600) * (0.8 + 0.2 * np.sign(np.sin(TAU * 130 * t)))
    return x * attack(t, 0.02) * np.minimum(1.0, (d - t) / 0.03)


def spring(d=0.55, base=180, kick=140, wob=16, depth=0.55):
    t = T(d)
    f = (base + kick * np.exp(-t * 3)) * (1 + depth * np.exp(-t * 5) * np.sin(TAU * wob * t))
    x = osc(f) + 0.4 * osc(2 * f)
    return x * np.exp(-t * 5) * attack(t, 0.003)


def squeak(f0, d=0.07, rise=0.6):
    t = T(d)
    f = f0 * (1 + rise * t / d)
    x = osc(f) + 0.3 * osc(2 * f)
    return bp(x, 1200, 5000) * np.sin(np.pi * t / d) ** 0.6


def whoosh(d, centre=0.5, spread=0.25):
    """noise bands that peak one after another, so it sounds like it sweeps up and away"""
    t = T(d)
    n = noise(len(t))
    out = np.zeros(len(t))
    for lo, hi, c in ((250, 700, centre - spread), (900, 2500, centre), (3500, 9000, centre + spread)):
        out += bp(n, lo, hi) * np.exp(-((t / d - c) / 0.18) ** 2)
    return out


def tick(d=0.01, lo=2500, hi=9000):
    t = T(d)
    return bp(noise(len(t)), lo, hi) * np.exp(-t * 500 / (d * 100))


# ---------------------------------------------------------------- shooting
def shoot_cork_pop():
    t = T(0.28)
    x = osc(160 + 700 * np.exp(-t * 45)) * np.exp(-t * 20)
    return x + hp(noise(len(t)), 2500) * np.exp(-t * 400) * 0.8


def shoot_slide_whistle():
    d = 0.4
    t = T(d)
    f = sweep(350, 1700, d) * (1 + 0.02 * np.sin(TAU * 6 * t))
    x = osc(f) * attack(t, 0.02) * (1 - (t / d) ** 6)
    return x + 0.06 * bp(noise(len(t)), 1200, 2400)


def shoot_boing():
    return spring(0.55)


def shoot_fart():
    return fart(0.5, f0=90, f1=40, wob=30)


def shoot_rubber_chicken():
    def syl(f0, f1, d):
        t = T(d)
        x = osc(np.linspace(f0, f1, len(t)), "saw") * (0.7 + 0.3 * np.sin(TAU * 70 * t))
        return formants(x, [900, 2200]) * attack(t, 0.01) * np.minimum(1.0, (d - t) / 0.03)
    return mix((0, syl(520, 330, 0.16), 1), (0.2, syl(600, 300, 0.22), 1))


def shoot_bloop():
    t = T(0.2)
    f = 250 + 1100 * (1 - np.exp(-t * 30))
    return osc(f) * np.exp(-t * 14) * attack(t, 0.004)


def shoot_pew():
    d = 0.3
    t = T(d)
    f = sweep(3000, 180, d)
    x = lp(osc(f, "square"), 5000) + 0.3 * osc(f * 2)
    return x * np.exp(-t * 8) * attack(t, 0.002)


def shoot_quack():
    return duck(0.24, 380, 300)


def shoot_toy_gun():
    d = 0.42
    t = T(d)
    parts = [(0.05 * i, tick(0.012) + 0.5 * osc(np.full(int(0.012 * SR), 1800.0)) * np.exp(-T(0.012) * 400), 1) for i in range(3)]
    hiss = bp(noise(len(t)), 3000, 9000) * np.exp(-np.clip(t - 0.16, 0, None) * 12) * (t > 0.16)
    return mix(*parts, (0, hiss, 0.5))


def shoot_airhorn():
    parts = [(0.14 * i, horn(466, 0.1), 1) for i in range(3)]
    parts.append((0.44, horn(622, 0.38), 1))
    return mix(*parts)


def shoot_kazoo():
    return kazoo(330, 430, 0.36)


def shoot_nyoom():
    d = 0.65
    t = T(d)
    f = sweep(1900, 650, d)
    tone = osc(f) * np.exp(-((t / d - 0.45) / 0.3) ** 2) * 0.25
    return whoosh(d, 0.5, 0.22) + tone


# ---------------------------------------------------------------- explosions
def boom_vine():
    x = np.tanh(boom_core(1.6, 150, 48, 2.2, 0.25) * 3)
    x = x + 0.7 * hp(noise(len(x)), 1500) * np.exp(-T(1.6) * 120)
    return reverb(x, 0.6, 0.25)


def boom_airhorn():
    b = np.tanh(boom_core(1.4, 140, 44, 2.0, 0.4) * 4)
    chord = mix(*[(0, horn(f, 0.45, ratios=(1, 1.26, 1.5)), 1) for f in (466, 622)])
    return reverb(np.tanh((mix((0, b, 1), (0.02, chord, 0.45))) * 1.8), 0.4, 0.2)


def boom_scream():
    d = 1.0
    t = T(d)
    f = (280 + 220 * (1 - np.exp(-t * 10)) - 200 * t ** 2) * (1 + 0.03 * np.sin(TAU * 6 * t))
    x = formants(osc(f, "saw"), [800, 1250, 2600])
    x = x * attack(t, 0.03) * (1 - t ** 3) * np.exp(-t * 2)
    return mix((0, boom_core(0.6, 120, 40, 4.0, 0.7) * 1.2, 1), (0.05, x, 0.9))


def boom_mega_fart():
    f = fart(1.0, 75, 30, 22)
    return reverb(mix((0, f, 0.9), (0.9, np.tanh(boom_core(0.9, 100, 36, 3.5, 0.5) * 2), 1)), 0.4, 0.2)


def boom_boing_ka_boom():
    return reverb(mix((0, spring(0.4, 220, 160, 14, 0.5), 0.8), (0.38, np.tanh(boom_core(1.0, 130, 40, 2.8, 0.7) * 2.5), 1)), 0.5, 0.2)


def boom_party_popper():
    t = T(0.25)
    pop = hp(noise(len(t)), 1000) * np.exp(-t * 60) + osc(np.full(len(t), 110.0)) * np.exp(-t * 25)
    parts = [(0, pop, 1)]
    for _ in range(70):
        parts.append((rng.uniform(0.08, 0.9), tick(0.012, rng.uniform(2000, 4000), rng.uniform(6000, 12000)), rng.uniform(0.08, 0.35)))
    for i, (f, d) in enumerate(((392, 0.14), (494, 0.14), (587, 0.4))):
        parts.append((0.14 + 0.16 * i, kazoo(f, f * 1.02, d), 0.55))
    return mix(*parts)


def boom_sad_trombone():
    def note(f0, f1, d):
        t = T(d)
        f = np.linspace(f0, f1, len(t)) * (1 + 0.012 * np.sin(TAU * 5.5 * t) * (t > 0.15))
        x = osc(f, "saw")
        w = np.sin(np.pi * t / d) ** 0.7
        x = lp(x, 500) * (1 - w) + lp(x, 2200) * w
        return x * attack(t, 0.04) * np.minimum(1.0, (d - t) / 0.05)
    notes = ((233, 225, 0.38), (220, 212, 0.38), (208, 200, 0.38), (196, 150, 1.0))
    parts = [(0, boom_core(0.5, 120, 42, 5.0, 0.6), 0.9)]
    s = 0.25
    for f0, f1, d in notes:
        parts.append((s, note(f0, f1, d), 0.7))
        s += d + 0.03
    return reverb(mix(*parts), 0.4, 0.15)


def boom_error_ding():
    def ding(f, d=0.5):
        t = T(d)
        return (osc(np.full(len(t), float(f))) + 0.2 * osc(np.full(len(t), 2.0 * f))) * np.exp(-t * 7) * attack(t, 0.003)
    return mix((0, ding(784), 0.6), (0.18, ding(587, 0.6), 0.6), (0.42, np.tanh(boom_core(1.0, 130, 40, 3.0, 0.6) * 2), 1))


def boom_dishes():
    parts = [(0, osc(np.full(int(0.4 * SR), 90.0)) * np.exp(-T(0.4) * 14), 1.2)]
    for _ in range(40):
        s = rng.uniform(0, 0.6) ** 1.4
        d = rng.uniform(0.05, 0.25)
        t = T(d)
        f = rng.uniform(2000, 7000)
        parts.append((s, osc(np.full(len(t), f)) * np.exp(-t * 25 / d / 4), rng.uniform(0.1, 0.4)))
    for _ in range(24):
        s = rng.uniform(0, 0.5) ** 1.5
        d = rng.uniform(0.02, 0.06)
        t = T(d)
        parts.append((s, bp(noise(len(t)), 2500, 8000) * np.exp(-t * 50), rng.uniform(0.3, 0.7)))
    return reverb(mix(*parts), 0.35, 0.2)


def boom_duck_squeaks():
    parts = []
    s = 0.0
    gap = 0.11
    for i in range(7):
        parts.append((s, squeak(1300 + 180 * i), 0.5))
        s += gap
        gap *= 0.82
    parts.append((s + 0.02, np.tanh(boom_core(1.0, 130, 40, 2.8, 0.7) * 2.5), 1))
    return reverb(mix(*parts), 0.4, 0.2)


def boom_nuke():
    rise = whoosh(0.55, 0.65, 0.2) * np.linspace(0.1, 1.0, int(0.55 * SR)) ** 2
    b = np.tanh(boom_core(2.4, 90, 28, 1.4, 0.9, 500) * 2.2)
    return reverb(mix((0, rise, 0.5), (0.5, b, 1)), 0.9, 0.3)


def boom_dialup():
    parts = []
    s = 0.0
    while s < 0.7:
        d = rng.uniform(0.03, 0.07)
        t = T(d)
        f = rng.choice([980, 1200, 1800, 2100, 2400])
        x = lp(osc(np.full(len(t), float(f)), "square"), 3500) * 0.4 + 0.3 * bp(noise(len(t)), 1500, 3500)
        parts.append((s, x, 0.7))
        s += d
    parts.append((0.72, np.tanh(boom_core(1.0, 130, 40, 2.8, 0.7) * 2.5), 1))
    return reverb(mix(*parts), 0.4, 0.2)


# ---------------------------------------------------------------- bouncing
def bounce_boing():
    return spring(0.4, 250, 120, 18, 0.5)


def bounce_bonk():
    t = T(0.22)
    f = 380 + 140 * np.exp(-t * 60)
    x = osc(f) + 0.35 * osc(f * 1.5) + 0.2 * osc(f * 2.4)
    return x * np.exp(-t * 28) * attack(t, 0.001) + 0.3 * lp(noise(len(t)), 2000) * np.exp(-t * 200)


def bounce_rubber_squeak():
    d = 0.16
    t = T(d)
    f = 1400 + 1000 * np.sin(np.pi * t / d) ** 0.8
    return bp(osc(f) + 0.4 * osc(2 * f), 900, 5000) * np.sin(np.pi * t / d) ** 0.5


def bounce_bloop():
    t = T(0.18)
    f = 350 + 1000 * (1 - np.exp(-t * 28))
    return osc(f) * np.exp(-t * 16) * attack(t, 0.003)


def bounce_quack():
    return duck(0.14, 420, 330)


def bounce_coin():
    def ping(f, d=0.4):
        t = T(d)
        return (osc(np.full(len(t), float(f))) + 0.25 * osc(np.full(len(t), 2.0 * f))) * np.exp(-t * 9) * attack(t, 0.002)
    return mix((0, ping(988, 0.12), 0.8), (0.07, ping(1319, 0.45), 1))


def bounce_slap():
    t = T(0.16)
    return bp(noise(len(t)), 1200, 4500) * np.exp(-t * 70) + osc(np.full(len(t), 190.0)) * np.exp(-t * 40) * 0.8


def bounce_rubber_ball():
    t = T(0.38)
    f = (230 - 90 * t / 0.38) * (1 + 0.25 * np.exp(-t * 12) * np.sin(TAU * 30 * t))
    return (osc(f) + 0.3 * osc(2 * f)) * np.exp(-t * 11) * attack(t, 0.002)


def bounce_xylophone():
    t = T(0.34)
    f = 784.0
    x = osc(np.full(len(t), f)) + 0.5 * osc(np.full(len(t), 3 * f)) * np.exp(-t * 30) + 0.25 * osc(np.full(len(t), 6 * f)) * np.exp(-t * 60)
    return x * np.exp(-t * 12) * attack(t, 0.001)


def bounce_dog_toy():
    d = 0.24
    t = T(d)
    f = np.where(t < 0.1, 1700 + 5000 * t, 2200 - 1000 * (t - 0.1))
    x = bp(osc(f, "saw") * (0.7 + 0.3 * np.sign(np.sin(TAU * 45 * t))), 1200, 4500)
    return x * attack(t, 0.005) * np.minimum(1.0, (d - t) / 0.03) * np.exp(-t * 6)


def bounce_tiny_fart():
    return fart(0.22, 130, 80, 40, 1200)


def bounce_cowbell():
    t = T(0.38)
    x = osc(np.full(len(t), 562.0), "square") + osc(np.full(len(t), 845.0), "square")
    x = bp(x, 400, 2200)
    return x * np.exp(-t * 11) * attack(t, 0.001)


SOUNDS = [
    ("shoot_01_cork_pop", shoot_cork_pop, 0.8),
    ("shoot_02_slide_whistle", shoot_slide_whistle, 0.7),
    ("shoot_03_boing", shoot_boing, 0.75),
    ("shoot_04_fart", shoot_fart, 0.85),
    ("shoot_05_rubber_chicken", shoot_rubber_chicken, 0.75),
    ("shoot_06_bloop", shoot_bloop, 0.75),
    ("shoot_07_pew", shoot_pew, 0.7),
    ("shoot_08_quack", shoot_quack, 0.8),
    ("shoot_09_toy_gun", shoot_toy_gun, 0.75),
    ("shoot_10_airhorn", shoot_airhorn, 0.8),
    ("shoot_11_kazoo", shoot_kazoo, 0.75),
    ("shoot_12_nyoom", shoot_nyoom, 0.75),
    ("boom_01_vine_boom", boom_vine, 0.95),
    ("boom_02_airhorn_boom", boom_airhorn, 0.95),
    ("boom_03_scream_launch", boom_scream, 0.9),
    ("boom_04_mega_fart", boom_mega_fart, 0.95),
    ("boom_05_boing_ka_boom", boom_boing_ka_boom, 0.95),
    ("boom_06_party_popper", boom_party_popper, 0.85),
    ("boom_07_sad_trombone", boom_sad_trombone, 0.9),
    ("boom_08_error_ding", boom_error_ding, 0.95),
    ("boom_09_dishes_crash", boom_dishes, 0.9),
    ("boom_10_duck_squeaks", boom_duck_squeaks, 0.95),
    ("boom_11_nuke", boom_nuke, 0.95),
    ("boom_12_dialup", boom_dialup, 0.95),
    ("bounce_01_boing", bounce_boing, 0.7),
    ("bounce_02_bonk", bounce_bonk, 0.8),
    ("bounce_03_rubber_squeak", bounce_rubber_squeak, 0.65),
    ("bounce_04_bloop", bounce_bloop, 0.7),
    ("bounce_05_quack", bounce_quack, 0.75),
    ("bounce_06_coin", bounce_coin, 0.65),
    ("bounce_07_slap", bounce_slap, 0.8),
    ("bounce_08_rubber_ball", bounce_rubber_ball, 0.75),
    ("bounce_09_xylophone", bounce_xylophone, 0.65),
    ("bounce_10_dog_toy", bounce_dog_toy, 0.65),
    ("bounce_11_tiny_fart", bounce_tiny_fart, 0.75),
    ("bounce_12_cowbell", bounce_cowbell, 0.7),
]


def finish(x, peak):
    x = hp(x - x.mean(), 25, 1)
    m = np.abs(x).max()
    x = x / m
    loud = np.where(np.abs(x) > 0.004)[0]
    x = x[:loud[-1] + 1]
    n = min(len(x), int(0.015 * SR))
    x[-n:] *= np.linspace(1, 0, n)
    x = signal.resample_poly(x, 1, 2) * peak
    return np.int16(np.clip(x, -1, 1) * 32767)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "sound", "grenade_new")
    os.makedirs(out, exist_ok=True)
    for name, fn, peak in SOUNDS:
        pcm = finish(fn(), peak)
        with wave.open(os.path.join(out, name + ".wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR // 2)
            w.writeframes(pcm.tobytes())
        print("%-26s %5.2f s  peak %.2f" % (name, len(pcm) / (SR // 2), np.abs(pcm).max() / 32767))


main()
