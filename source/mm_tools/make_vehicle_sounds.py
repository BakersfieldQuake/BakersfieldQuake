"""Synthesizes custom 22050 Hz mono PCM WAV sound effects for BakersfieldQuake's 4 Unique Vehicles
into G:\\Quake\\Combat\\BakersfieldQuake\\sound\\vehicles\\:
  - idle_truck.wav  : Deep V8 cam-lope idle rumble (seamless loop)
  - idle_sedan.wav  : Smooth 90s 4-cylinder street idle purr (seamless loop)
  - idle_van.wav    : Heavy commercial work-van idle chug (seamless loop)
  - idle_coupe.wav  : Tuned high-compression sport exhaust idle (seamless loop)
  - hit_metal1.wav  : Sheet-metal bullet punch + chassis ring
  - hit_metal2.wav  : Fender/door bullet impact + safety-glass crackle
  - fire_burn.wav   : Roaring gasoline engine fire + boiling radiator hiss (seamless loop)
  - car_boom1.wav   : Massive fuel-tank detonation + steel body tear + glass shatter
  - car_boom2.wav   : Heavy secondary vehicle explosion + sub-bass shockwave
  - clang1.wav      : Blown-off hood/door skidding & clanging on asphalt
  - clang2.wav      : Heavy bumper/rollbar metallic crash
  - tire_thud1.wav  : Heavy automotive rubber tire elastic bounce & sidewall slap
  - tire_thud2.wav  : Spinning car tire pavement thump & chirp
"""
import math
import os
import random
import struct
import wave

RATE = 22050


def write_wav(path, samples, peak=0.88):
    m = max(abs(s) for s in samples) or 1.0
    k = peak / m
    raw = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s * k)) * 32767)) for s in samples)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(raw)


def lowpass(x, cutoff):
    a = 1.0 - math.exp(-2.0 * math.pi * cutoff / RATE)
    y = 0.0
    out = []
    for v in x:
        y += a * (v - y)
        out.append(y)
    return out


def fade_ends(samples, ms=6.0):
    nf = max(1, int(RATE * ms / 1000.0))
    out = list(samples)
    for i in range(min(nf, len(out) // 2)):
        w = i / float(nf)
        out[i] *= w
        out[-1 - i] *= w
    return out


def make_engine_idle(kind):
    """1.0s seamless loop with integer pulse counts so loop boundary is click-free."""
    rng = random.Random({"truck": 1, "sedan": 2, "van": 3, "coupe": 4}[kind])
    n = RATE
    noise = lowpass([rng.uniform(-1.0, 1.0) for _ in range(n)], 360.0 if kind != "coupe" else 520.0)
    out = []
    # Integer pulses per 1.0s clip so phase wraps cleanly!
    pulses = {"truck": 14, "sedan": 20, "van": 16, "coupe": 26}[kind]
    base_hz = {"truck": 44.0, "sedan": 58.0, "van": 49.0, "coupe": 74.0}[kind]

    for i in range(n):
        t = i / float(RATE)
        ph = (t * pulses) % 1.0
        tp = ph / pulses
        lope = 1.0 + (0.38 * math.sin(2.0 * math.pi * 2.0 * t) if kind == "truck" else 0.12 * math.sin(2.0 * math.pi * t))
        env = math.exp(-tp / 0.028) * lope
        s = env * (
            math.sin(2.0 * math.pi * base_hz * t)
            + 0.65 * math.sin(2.0 * math.pi * base_hz * 2.0 * t + 0.4)
            + (0.45 * math.sin(2.0 * math.pi * base_hz * 3.0 * t + 0.9) if kind in ("coupe", "truck") else 0.18 * math.sin(2.0 * math.pi * base_hz * 3.0 * t))
        )
        chug = noise[i] * (0.28 + 0.42 * env) * 2.2
        out.append(math.tanh((s + chug) * 0.95))
    return fade_ends(out, ms=5.0)


def make_hit_metal(seed, with_glass=False):
    rng = random.Random(seed)
    n = int(RATE * 0.28)
    nz = lowpass([rng.uniform(-1.0, 1.0) for _ in range(n)], 2600.0)
    hi = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    out = []
    f1 = 215.0 + rng.uniform(-25.0, 35.0)
    f2 = 590.0 + rng.uniform(-50.0, 70.0)
    f3 = 1380.0 + rng.uniform(-120.0, 140.0)
    for i in range(n):
        t = i / float(RATE)
        punch = math.exp(-t / 0.016) * (math.sin(2 * math.pi * 118 * t) + nz[i] * 2.4)
        ring = (
            0.55 * math.exp(-t / 0.065) * math.sin(2 * math.pi * f1 * t)
            + 0.35 * math.exp(-t / 0.045) * math.sin(2 * math.pi * f2 * t + 0.5)
            + 0.22 * math.exp(-t / 0.032) * math.sin(2 * math.pi * f3 * t + 1.2)
        )
        glass = 0.0
        if with_glass:
            glass = math.exp(-t / 0.055) * (
                0.35 * math.sin(2 * math.pi * 3420 * t)
                + 0.28 * math.sin(2 * math.pi * 4890 * t)
                + 0.40 * hi[i] * (1.0 if (i // 85) % 3 == 0 else 0.15)
            )
        out.append(math.tanh((1.35 * punch + ring + glass) * 1.15))
    return fade_ends(out, ms=3.0)


def make_fire_burn():
    rng = random.Random(55)
    n = int(RATE * 1.0)
    raw = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    roar = lowpass(lowpass(raw, 420.0), 340.0)
    hiss = lowpass(raw, 2800.0)
    out = []
    for i in range(n):
        t = i / float(RATE)
        flap = 0.72 + 0.28 * math.sin(2 * math.pi * 5.0 * t) * math.cos(2 * math.pi * 3.0 * t)
        pop = 0.55 if (i % 3150) < 95 else 0.0
        s = roar[i] * 4.2 * flap + hiss[i] * 0.65 + raw[i] * pop * math.exp(-((i % 3150) / 35.0))
        out.append(math.tanh(s * 1.1))
    return fade_ends(out, ms=8.0)


def make_car_boom(seed):
    rng = random.Random(seed)
    dur = 1.65
    n = int(RATE * dur)
    raw = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    sub = lowpass(lowpass(raw, 130.0), 110.0)
    mid = lowpass(raw, 850.0)
    out = []
    ph = 0.0
    for i in range(n):
        t = i / float(RATE)
        f_drop = 38.0 + 92.0 * math.exp(-t / 0.09)
        ph += 2.0 * math.pi * f_drop / RATE
        thump = 1.75 * math.exp(-t / 0.24) * math.sin(ph)
        blast = 4.6 * sub[i] * math.exp(-t / 0.52) + 2.4 * mid[i] * math.exp(-t / 0.26)
        tear = 0.55 * math.exp(-t / 0.19) * (math.sin(2 * math.pi * 285 * t + math.sin(42 * t)) + 0.5 * math.sin(2 * math.pi * 468 * t))
        # Secondary fuel/glass crackle tail
        shatter = 0.45 * raw[i] * math.exp(-max(0.0, t - 0.08) / 0.32) * (0.4 + 0.6 * math.sin(37.0 * t) ** 2)
        out.append(math.tanh((thump + blast + tear + shatter) * 0.92))
    return fade_ends(out, ms=8.0)


def make_clang(seed):
    rng = random.Random(seed)
    n = int(RATE * 0.46)
    nz = lowpass([rng.uniform(-1.0, 1.0) for _ in range(n)], 1800.0)
    freqs = [192.0 + rng.uniform(-20, 25), 348.0 + rng.uniform(-30, 30), 715.0 + rng.uniform(-50, 60), 1290.0 + rng.uniform(-80, 90)]
    out = []
    for i in range(n):
        t = i / float(RATE)
        scrape = nz[i] * 2.1 * math.exp(-t / 0.085)
        bell = sum((0.55 / (k + 1)) * math.exp(-t / (0.19 - 0.03 * k)) * math.sin(2 * math.pi * f * t + k) for k, f in enumerate(freqs))
        out.append(math.tanh((scrape + bell * 1.45) * 1.2))
    return fade_ends(out, ms=4.0)


def make_tire_thud(seed):
    rng = random.Random(seed)
    n = int(RATE * 0.42)
    nz = lowpass([rng.uniform(-1.0, 1.0) for _ in range(n)], 750.0)
    ph = pq = 0.0
    base = 52.0 + rng.uniform(-6.0, 8.0)
    out = []
    for i in range(n):
        t = i / float(RATE)
        f = base * (1.0 + 1.25 * math.exp(-t / 0.035))
        ph += 2.0 * math.pi * f / RATE
        thump = 1.45 * math.exp(-t / 0.085) * math.sin(ph)
        fq = 440.0 * (1.0 + 0.7 * min(1.0, t / 0.07))
        pq += 2.0 * math.pi * fq / RATE
        chirp = 0.24 * math.exp(-t / 0.055) * math.sin(pq)
        slap = nz[i] * 2.6 * math.exp(-t / 0.015)
        out.append(math.tanh((thump + chirp + slap) * 1.25))
    return fade_ends(out, ms=4.0)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(os.path.join(here, "..", "..", "sound", "vehicles"))
    os.makedirs(out_dir, exist_ok=True)

    for k in ("truck", "sedan", "van", "coupe"):
        write_wav(os.path.join(out_dir, f"idle_{k}.wav"), make_engine_idle(k), peak=0.52)
    write_wav(os.path.join(out_dir, "hit_metal1.wav"), make_hit_metal(11, with_glass=False), peak=0.85)
    write_wav(os.path.join(out_dir, "hit_metal2.wav"), make_hit_metal(22, with_glass=True), peak=0.85)
    write_wav(os.path.join(out_dir, "fire_burn.wav"), make_fire_burn(), peak=0.78)
    write_wav(os.path.join(out_dir, "car_boom1.wav"), make_car_boom(77), peak=0.96)
    write_wav(os.path.join(out_dir, "car_boom2.wav"), make_car_boom(88), peak=0.96)
    write_wav(os.path.join(out_dir, "clang1.wav"), make_clang(31), peak=0.84)
    write_wav(os.path.join(out_dir, "clang2.wav"), make_clang(42), peak=0.84)
    write_wav(os.path.join(out_dir, "tire_thud1.wav"), make_tire_thud(61), peak=0.82)
    write_wav(os.path.join(out_dir, "tire_thud2.wav"), make_tire_thud(62), peak=0.82)
    print(f"Wrote 13 custom vehicle WAVs to {out_dir}")


if __name__ == "__main__":
    main()
