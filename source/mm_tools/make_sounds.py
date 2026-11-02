"""Synthesises the Mega Man gun's boat sounds (pure Python, no numpy).
  megamotor.wav - 0.5 s of a deep putt-putt boat motor; replayed every 0.5 s it loops seamlessly
  megahorn.wav  - a low foghorn blast (spotting someone / leaping)
  tire1-3.wav   - a rubber tyre bouncing: a dull thump, a squeak and a short wobbling "boing" (Mega Man's wheels)
python -I make_sounds.py <outdir> [<outdir> ...]"""
import math
import os
import random
import struct
import sys
import wave

RATE = 22050


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


def lowpass(x, cutoff):
    a = 1 - math.exp(-2 * math.pi * cutoff / RATE)
    y, out = 0.0, []
    for v in x:
        y += a * (v - y)
        out.append(y)
    return out


def motor():
    rng = random.Random(7)
    n = int(RATE * 0.5)
    rate = 10.0                      # firing pulses per second: 5 per clip, so it loops
    noise = lowpass(lowpass([rng.uniform(-1, 1) for _ in range(n)], 300), 300)
    out = []
    for i in range(n):
        t = i / RATE
        ph = (t * rate) % 1.0        # time since the last pulse, as a fraction of the period
        tp = ph / rate
        env = math.exp(-tp / 0.035)  # each putt: a fast thump
        thump = env * (math.sin(2 * math.pi * 52 * tp) + 0.6 * math.sin(2 * math.pi * 104 * tp + 0.5)
                       + 0.25 * math.sin(2 * math.pi * 156 * tp + 1.1))
        # engine drone underneath, a bit louder right after each putt
        drone = (0.12 + 0.45 * env) * (math.sin(2 * math.pi * 40 * t) + 0.4 * math.sin(2 * math.pi * 80 * t + 0.3)
                                         + 0.2 * math.sin(2 * math.pi * 120 * t + 0.9))
        chug = noise[i] * (0.5 * env + 0.15) * 6
        out.append(1.6 * thump + 0.5 * drone + chug)
    out = [math.tanh(1.6 * s) for s in out]  # a little grit
    # tiny fades at the ends so the restart never clicks
    f = int(RATE * 0.004)
    for i in range(f):
        out[i] *= i / f
        out[-1 - i] *= i / f
    return out


def horn():
    n = int(RATE * 1.4)
    out = []
    phase1 = phase2 = 0.0
    for i in range(n):
        t = i / RATE
        att = min(1.0, t / 0.09)
        rel = min(1.0, max(0.0, (1.4 - t) / 0.35))
        env = att * rel
        sag = 1.0 - 0.025 * max(0.0, t - 1.0)              # pitch drops as it runs out of air
        vib = 1.0 + 0.004 * math.sin(2 * math.pi * 5.2 * t)
        f1 = 69.0 * sag * vib                               # two reeds a fifth apart, like a ship's horn
        f2 = 103.5 * sag * vib
        phase1 += 2 * math.pi * f1 / RATE
        phase2 += 2 * math.pi * f2 / RATE
        s = 0.0
        for h in range(1, 22):
            # rich, brassy harmonics with a bump around 300-500 Hz
            fh = f1 * h
            w = (1.0 / h ** 0.9) * (1.0 + 1.4 * math.exp(-((fh - 380) / 160) ** 2))
            s += w * math.sin(phase1 * h)
            if h < 15:
                fh = f2 * h
                w = 0.6 * (1.0 / h ** 0.9) * (1.0 + 1.4 * math.exp(-((fh - 380) / 160) ** 2))
                s += w * math.sin(phase2 * h + 0.7)
        out.append(env * s)
    out = lowpass(out, 1400)
    return [math.tanh(0.9 * s / 4.0) for s in out]


def tire(seed):
    """one bounce of a rubber tyre: a dull thump (pitch falling), the squeak of the rubber, a "boing" that wobbles out"""
    rng = random.Random(seed)
    n = int(RATE * 0.38)
    base = 62 + rng.uniform(-8, 12)
    sq0 = 520 + rng.uniform(-60, 120)
    noise = lowpass([rng.uniform(-1, 1) for _ in range(n)], 900)
    out, ph, pq, pb = [], 0.0, 0.0, 0.0
    for i in range(n):
        t = i / RATE
        f = base * (1.0 + 1.1 * math.exp(-t / 0.03))
        ph += 2 * math.pi * f / RATE
        thump = math.exp(-t / 0.07) * math.sin(ph)
        fq = sq0 * (1.0 + 0.9 * min(1.0, t / 0.09)) * (1.0 + 0.05 * math.sin(2 * math.pi * 31 * t))
        pq += 2 * math.pi * fq / RATE
        squeak = 0.22 * min(1.0, t / 0.01) * math.exp(-t / 0.06) * (math.sin(pq) + 0.35 * math.sin(2 * pq))
        fb = 140 * (1.0 + 0.5 * math.sin(2 * math.pi * 14 * t) * math.exp(-t / 0.15)) * (1.0 - 0.3 * t)
        pb += 2 * math.pi * fb / RATE
        boing = 0.55 * math.exp(-t / 0.12) * math.sin(pb)
        slap = noise[i] * 3.0 * math.exp(-t / 0.012)
        out.append(1.2 * thump + squeak + boing + slap)
    out = [math.tanh(1.3 * v) for v in out]
    f = int(RATE * 0.003)
    for i in range(f):
        out[i] *= i / f
        out[-1 - i] *= i / f
    return out


if __name__ == "__main__":
    m, h = motor(), horn()
    for d in sys.argv[1:]:
        os.makedirs(d, exist_ok=True)
        write(os.path.join(d, "megamotor.wav"), m, 0.6)
        write(os.path.join(d, "megahorn.wav"), h, 0.95)
        for k in (1, 2, 3):
            write(os.path.join(d, "tire%d.wav" % k), tire(40 + k), 0.9)
