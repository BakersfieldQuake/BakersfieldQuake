"""Synthesises the joke "fun gun" weapon sounds (pure Python, no numpy).
  fg_fork_fire    - truck air horn HOOONK
  fg_fork_beep    - forklift reverse alarm BEEP (replayed every 0.5 s)
  fg_fork_hit     - metal CLANG + body thud
  fg_paint_fire   - aerosol PSSHT
  fg_paint_hit    - wet SPLAT + blop
  fg_foam_loop    - 0.25 s extinguisher hiss; replayed every 0.25 s it loops seamlessly
  fg_foam_hit     - foamy FWUMP with bubbles
  fg_bonk_fire    - throw WHOOSH
  fg_bonk_hit     - wood-block BONK + descending slide whistle
  fg_bonk_tweet   - dizzy birdies
  fg_mask_fire    - spooky organ dun-dun-DUNNN
  fg_mask_stick   - ghostly ooOOOooo
  fg_mask_pop     - diminished organ stab + boom
  fg_pong_fire    - paddle TOCK
  fg_pong_bounce  - ball POCK (pitch-shifted by the game)
  fg_pong_hit     - game-show DING
python -I make_fungun_sounds.py <outdir> [<outdir> ...]"""
import math
import os
import random
import struct
import sys
import wave

RATE = 22050
TAU = 2 * math.pi


def write(path, samples, peak):
    m = max(abs(s) for s in samples) or 1.0
    k = peak / m
    data = b"".join(struct.pack("<h", int(max(-1, min(1, s * k)) * 32767)) for s in samples)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(data)
    print("wrote", path, "%.3fs" % (len(samples) / RATE), "%d bytes" % os.path.getsize(path))


def lowpass(x, cutoff):
    a = 1 - math.exp(-2 * math.pi * cutoff / RATE)
    y, out = 0.0, []
    for v in x:
        y += a * (v - y)
        out.append(y)
    return out


def highpass(x, cutoff):
    return [a - b for a, b in zip(x, lowpass(x, cutoff))]


def bandpass(x, fc, q=0.5):
    """Chamberlin state-variable bandpass; fc is a number or a per-sample list, q is damping (1/Q)."""
    fcs = fc if isinstance(fc, list) else [fc] * len(x)
    low = band = 0.0
    out = []
    for v, c in zip(x, fcs):
        f = 2 * math.sin(math.pi * min(c, RATE / 6) / RATE)
        low += f * band
        high = v - low - q * band
        band += f * high
        out.append(band)
    return out


def noise(n):
    return [random.uniform(-1, 1) for _ in range(n)]


def norm(x):
    m = max(abs(v) for v in x) or 1.0
    return [v / m for v in x]


def fade(x, fin, fout):
    """Short linear ramps at each end (seconds) so nothing clicks."""
    a, b = int(RATE * fin), int(RATE * fout)
    for i in range(a):
        x[i] *= i / a
    for i in range(b):
        x[-1 - i] *= i / b
    return x


def reverb(x, mix=0.35):
    """A few feedback combs - enough of a 'church' to keep the organ spooky. Same length out."""
    wet = [0.0] * len(x)
    for d, g in ((0.0297, 0.72), (0.0371, 0.70), (0.0411, 0.68), (0.0437, 0.66)):
        n = int(RATE * d)
        y = [0.0] * len(x)
        for i, v in enumerate(x):
            y[i] = v + (g * y[i - n] if i >= n else 0.0)
        for i in range(len(x)):
            wet[i] += y[i]
    wet = lowpass(wet, 3000)
    return [(1 - mix) * a + mix * 0.25 * b for a, b in zip(x, wet)]


# --- forklift -------------------------------------------------------------------------------

def fork_fire():
    d = 0.7
    n = int(RATE * d)
    out = []
    p1 = p2 = 0.0
    for i in range(n):
        t = i / RATE
        sag = 1.0 - 0.07 * max(0.0, (t - 0.45) / 0.25)    # running out of air
        wob = 1.0 + 0.003 * math.sin(TAU * 7 * t)
        p1 += TAU * 220.0 * sag * wob / RATE
        p2 += TAU * 277.0 * 1.004 * sag * wob / RATE        # slightly detuned major third
        s = 0.0
        for h in range(1, 26):                              # band-limited sawtooths
            s += (math.sin(p1 * h) + 0.85 * math.sin(p2 * h + 0.4)) / h
        env = min(1.0, t / 0.025) * min(1.0, max(0.0, (d - t) / 0.12))
        out.append(env * s)
    out = lowpass(lowpass(out, 2600), 3500)
    out = [math.tanh(s / 2.2) for s in out]
    return fade(out, 0.003, 0.01)


def fork_beep():
    n, on = int(RATE * 0.3), 0.22
    out = []
    for i in range(n):
        t = i / RATE
        if t >= on:
            out.append(0.0)
            continue
        s = sum(math.sin(TAU * 1050 * h * t) / h for h in (1, 3, 5, 7, 9))   # square-ish
        env = min(1.0, t / 0.003) * min(1.0, (on - t) / 0.008)
        out.append(env * s)
    out = lowpass(out, 3500)                                                 # softened
    return fade(out, 0.0, 0.005)


def fork_hit():
    n = int(RATE * 0.6)
    crack = lowpass(noise(n), 3000)
    partials = [(310, 1.0, 0.35), (523, 0.35, 0.30), (787, 0.7, 0.22), (1240, 0.55, 0.16),
                (1913, 0.4, 0.10), (2777, 0.25, 0.06)]
    metal, thump = [], []
    ph = 0.0
    for i in range(n):
        t = i / RATE
        s = 0.0
        for f, a, tau in partials:
            e = a * math.exp(-t / tau)
            s += e * (math.sin(TAU * f * t) + 0.6 * math.sin(TAU * f * 1.006 * t + 1.3))
        metal.append(s)
        ph += TAU * (45 + 65 * math.exp(-t / 0.05)) / RATE
        thump.append(math.exp(-t / 0.12) * math.sin(ph))
    metal, thump = norm(metal), norm(thump)
    crack = norm(crack)
    out = [0.7 * m + 1.0 * th + 0.6 * c * math.exp(-i / RATE / 0.01)
           for i, (m, th, c) in enumerate(zip(metal, thump, crack))]
    out = [math.tanh(1.3 * s) for s in out]
    return fade(out, 0.001, 0.03)


# --- paint gun ------------------------------------------------------------------------------

def paint_fire():
    n = int(RATE * 0.14)
    hiss = norm(highpass(lowpass(noise(n), 7000), 1800))
    puff = norm(lowpass(noise(n), 600))
    out = []
    for i in range(n):
        t = i / RATE
        out.append(min(1.0, t / 0.004) * math.exp(-t / 0.09) * hiss[i]
                   + 0.5 * math.exp(-t / 0.01) * puff[i])
    return fade(out, 0.001, 0.015)


def paint_hit():
    n = int(RATE * 0.22)
    mush = norm(lowpass(noise(n), 1400))
    bits = norm(lowpass(noise(n), 3000))
    out = []
    ph = 0.0
    for i in range(n):
        t = i / RATE
        ph += TAU * (90 + 260 * math.exp(-t / 0.03)) / RATE      # blop: pitch drops fast
        blop = min(1.0, t / 0.002) * math.exp(-t / 0.06) * math.sin(ph)
        out.append(1.0 * math.exp(-t / 0.035) * mush[i] + 0.4 * math.exp(-t / 0.015) * bits[i]
                   + 0.9 * blop)
    return fade(out, 0.001, 0.02)


# --- foam (extinguisher) --------------------------------------------------------------------

def foam_loop():
    n, warm = int(RATE * 0.25), 2000
    nz = noise(n + warm)
    hiss = norm(highpass(lowpass(nz, 6000), 1200)[warm:])
    body = norm(bandpass(nz, 600, 0.8)[warm:])
    out = [h + 0.3 * b for h, b in zip(hiss, body)]
    return fade(out, 0.003, 0.003)                  # steady level, only tiny ramps


def foam_hit():
    n = int(RATE * 0.3)
    puff = norm(lowpass(lowpass(noise(n), 500), 500))
    out = []
    ph = 0.0
    for i in range(n):
        t = i / RATE
        ph += TAU * (70 + 70 * math.exp(-t / 0.04)) / RATE
        out.append(min(1.0, t / 0.012) * math.exp(-t / 0.07) * puff[i]
                   + 0.6 * min(1.0, t / 0.005) * math.exp(-t / 0.06) * math.sin(ph))
    # bubbly crackle: little rising-pitch blips
    for _ in range(16):
        st = random.uniform(0.02, 0.26)
        f0 = random.uniform(500, 1400)
        amp = random.uniform(0.2, 0.5) * (1.0 - st / 0.35)
        s0 = int(st * RATE)
        bp = 0.0
        for j in range(int(0.03 * RATE)):
            if s0 + j >= n:
                break
            tb = j / RATE
            bp += TAU * f0 * (1 + 8 * tb) / RATE
            out[s0 + j] += amp * (1 - math.exp(-tb / 0.001)) * math.exp(-tb / 0.008) * math.sin(bp)
    return fade(out, 0.002, 0.03)


# --- bonk -----------------------------------------------------------------------------------

def bonk_fire():
    T = 0.35
    n = int(RATE * T)
    fcs = [300 + 2200 * math.sin(math.pi * i / n) ** 1.5 for i in range(n)]    # sweep up then down
    x = norm(bandpass(noise(n), fcs, 0.6))
    out = [math.sin(math.pi * i / n) ** 2 * v for i, v in enumerate(x)]
    return fade(out, 0.003, 0.005)


def bonk_hit():
    n = int(RATE * 0.7)
    click = norm(highpass(noise(n), 3000))
    ts, sd = 0.07, 0.6
    breath = norm(bandpass(noise(n), 1500, 0.7))
    out = []
    ph = 0.0
    for i in range(n):
        t = i / RATE
        knock = (math.exp(-t / 0.035) * math.sin(TAU * 900 * t)
                 + 0.4 * math.exp(-t / 0.012) * math.sin(TAU * 2470 * t + 0.5)
                 + 0.6 * math.exp(-t / 0.05) * math.sin(TAU * 450 * t + 0.2)
                 + 0.5 * math.exp(-t / 0.002) * click[i])
        knock *= min(1.0, t / 0.0005)
        slide = 0.0
        if t >= ts:
            u = min(1.0, (t - ts) / sd)
            f = 1800 * (400 / 1800) ** u * (1 + 0.035 * math.sin(TAU * 7 * (t - ts)))
            ph += TAU * f / RATE
            env = min(1.0, (t - ts) / 0.02) * min(1.0, max(0.0, (ts + sd - t) / 0.08))
            slide = env * (math.sin(ph) + 0.08 * math.sin(2 * ph) + 0.04 * breath[i])
        out.append(knock + 0.5 * slide)
    return fade(out, 0.0, 0.02)


def bonk_tweet():
    n = int(RATE * 1.1)
    out = [0.0] * n
    groups = [(0.02, 1.0, 1.0), (0.40, 0.8, 0.94), (0.78, 0.6, 1.05)]   # start, amp, pitch
    for g0, amp, k in groups:
        for c in range(3):
            st = g0 + c * 0.08
            s0, m = int(st * RATE), int(0.06 * RATE)
            f0, f1 = 2500 * k * (1 + 0.03 * c), 4000 * k * (1 + 0.03 * c)
            ph = 0.0
            for j in range(m):
                u = j / m
                f = (f0 + (f1 - f0) * u ** 0.7) * (1 + 0.03 * math.sin(TAU * 40 * j / RATE))
                ph += TAU * f / RATE
                out[s0 + j] += amp * math.sin(math.pi * u) ** 1.5 * math.sin(ph)
    return fade(out, 0.002, 0.01)


# --- spooky mask ----------------------------------------------------------------------------

ORGAN = [(0.5, 0.5), (1, 1.0), (2, 0.7), (3, 0.45), (4, 0.35), (6, 0.2), (8, 0.15)]


def organ_note(buf, start, dur, f, amp, rel=0.08):
    """Pipe-organ voice: several harmonics, a sub-octave, tremolo, flat sustain."""
    i0 = int(start * RATE)
    i1 = min(len(buf), int((start + dur + rel) * RATE))
    hs = [(m, w) for m, w in ORGAN if f * m < 10000]
    for i in range(i0, i1):
        t = i / RATE - start
        env = min(1.0, t / 0.012) * (1.0 if t < dur else max(0.0, 1 - (t - dur) / rel))
        trem = 1 + 0.12 * math.sin(TAU * 5.5 * t)
        s = 0.0
        for m, w in hs:
            s += w * math.sin(TAU * f * m * t + m)
        buf[i] += amp * env * trem * s


def mask_fire():
    n = int(RATE * 1.7)
    buf = [0.0] * n
    A4, G4, D4, F4, D3 = 440.0, 392.0, 293.66, 349.23, 146.83
    # dun-dun-DUNNN (Toccata-ish A-G-A), the last one blooming into a D minor chord
    organ_note(buf, 0.00, 0.12, A4, 1.0, 0.03)
    organ_note(buf, 0.15, 0.12, G4, 1.0, 0.03)
    organ_note(buf, 0.32, 1.05, A4, 1.0, 0.2)
    organ_note(buf, 0.32, 1.05, F4, 0.7, 0.2)
    organ_note(buf, 0.32, 1.05, D4, 0.7, 0.2)
    organ_note(buf, 0.32, 1.05, D3, 0.8, 0.2)
    for st, du, f in ((0.0, 0.12, 220.0), (0.15, 0.12, 196.0)):   # octave-down bass on the pickups
        organ_note(buf, st, du, f, 0.6, 0.03)
    out = norm(reverb(buf, 0.35))
    out = [math.tanh(1.5 * s) for s in out]          # squash so the pickups aren't drowned by the chord
    return fade(out, 0.002, 0.08)


def mask_stick():
    T = 1.3
    n = int(RATE * T)
    wind = norm(bandpass(noise(n), 500, 0.5))
    out = []
    p = p2 = 0.0
    for i in range(n):
        t = i / RATE
        u = t / T
        contour = 420 + 180 * math.sin(math.pi * u) ** 1.5            # ooOOOooo
        p += TAU * contour * (1 + 0.05 * math.sin(TAU * 4.2 * t)) / RATE
        p2 += TAU * contour * 2.01 * (1 + 0.02 * math.sin(TAU * 6.3 * t + 1)) / RATE
        env = math.sin(math.pi * u) ** 1.3
        s = math.sin(p) + 0.25 * math.sin(2 * p) + 0.1 * math.sin(3 * p)
        out.append(env * s + 0.18 * math.sin(math.pi * u) ** 2 * math.sin(p2) + 0.04 * env * wind[i])
    out = lowpass(out, 3000)
    return fade(out, 0.005, 0.02)


def mask_pop():
    n = int(RATE * 0.9)
    org = [0.0] * n
    for f in (277.18, 329.63, 392.00, 466.16):                         # C# diminished 7th
        organ_note(org, 0.0, 0.3, f, 0.5, 0.25)
    organ_note(org, 0.0, 0.3, 138.59, 0.6, 0.25)
    org = norm(reverb(org, 0.4))
    hi, lo = norm(lowpass(noise(n), 2000)), norm(lowpass(noise(n), 400))
    out = []
    ph = 0.0
    for i in range(n):
        t = i / RATE
        ph += TAU * (40 + 60 * math.exp(-t / 0.06)) / RATE
        boom = min(1.0, t / 0.003) * math.exp(-t / 0.18) * math.sin(ph)
        nz = math.exp(-t / 0.05) * hi[i] + 0.7 * math.exp(-t / 0.2) * lo[i]
        out.append(0.8 * org[i] + 0.9 * boom + 0.6 * nz)
    out = [math.tanh(1.2 * s) for s in out]
    return fade(out, 0.001, 0.05)


# --- pong -----------------------------------------------------------------------------------

def pong_fire():
    n = int(RATE * 0.08)
    click = norm(highpass(noise(n), 4000))
    out = []
    for i in range(n):
        t = i / RATE
        out.append(math.exp(-t / 0.012) * math.sin(TAU * 1300 * t)
                   + 0.35 * math.exp(-t / 0.006) * math.sin(TAU * 2900 * t + 0.3)
                   + 0.4 * math.exp(-t / 0.02) * math.sin(TAU * 520 * t)
                   + 0.5 * math.exp(-t / 0.0015) * click[i])
    return fade(out, 0.0005, 0.01)


def pong_bounce():
    n = int(RATE * 0.07)
    click = norm(highpass(noise(n), 5000))
    out = []
    for i in range(n):
        t = i / RATE
        out.append(math.exp(-t / 0.008) * math.sin(TAU * 2000 * t)
                   + 0.3 * math.exp(-t / 0.003) * math.sin(TAU * 4700 * t + 0.7)
                   + 0.3 * math.exp(-t / 0.001) * click[i])
    return fade(out, 0.0005, 0.01)


def pong_hit():
    n = int(RATE * 0.5)
    click = norm(highpass(noise(n), 3000))
    partials = [(1320, 1.0, 0.35), (1323.5, 0.5, 0.35), (1320 * 2.76, 0.45, 0.12),
                (1320 * 5.4, 0.25, 0.05), (660, 0.12, 0.4)]
    out = []
    for i in range(n):
        t = i / RATE
        s = sum(a * math.exp(-t / tau) * math.sin(TAU * f * t + f) for f, a, tau in partials)
        out.append(s + 0.4 * math.exp(-t / 0.0015) * click[i])
    return fade(out, 0.001, 0.05)


if __name__ == "__main__":
    random.seed(20261028)
    sounds = [
        ("fg_fork_fire.wav", fork_fire()),
        ("fg_fork_beep.wav", fork_beep()),
        ("fg_fork_hit.wav", fork_hit()),
        ("fg_paint_fire.wav", paint_fire()),
        ("fg_paint_hit.wav", paint_hit()),
        ("fg_foam_loop.wav", foam_loop()),
        ("fg_foam_hit.wav", foam_hit()),
        ("fg_bonk_fire.wav", bonk_fire()),
        ("fg_bonk_hit.wav", bonk_hit()),
        ("fg_bonk_tweet.wav", bonk_tweet()),
        ("fg_mask_fire.wav", mask_fire()),
        ("fg_mask_stick.wav", mask_stick()),
        ("fg_mask_pop.wav", mask_pop()),
        ("fg_pong_fire.wav", pong_fire()),
        ("fg_pong_bounce.wav", pong_bounce()),
        ("fg_pong_hit.wav", pong_hit()),
    ]
    for d in sys.argv[1:]:
        os.makedirs(d, exist_ok=True)
        for name, s in sounds:
            write(os.path.join(d, name), s, 0.9)
