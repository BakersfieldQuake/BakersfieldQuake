"""Sounds for the Hack Attack monitor gun (pure Python, no numpy).
  hm_hacking  - robotised "HACKING. HACKING." over data chatter (from a SAPI voice render)
  hm_launch   - dial-up modem screech + power-on whine
  hm_beep1..3 - computer blips that replay while the monitor flies
  hm_crash    - glass smash + CRT bang + error chord + electric crackle
  hm_zap      - short crackle for the green lightning
  hm_fatal    - robotised "FATAL ERROR"
  hm_imin     - robotised "I'M IN"
python -I make_hackmon_sounds.py <tts_dir> <outdir> [<outdir> ...]
<tts_dir> holds hacking.wav, fatal.wav, imin.wav (22050 Hz mono 16 bit, rendered with System.Speech)."""
import math
import os
import random
import struct
import sys
import wave

SR = 22050
random.seed(1337)


def read_wav(path):
    w = wave.open(path, "rb")
    raw = w.readframes(w.getnframes())
    w.close()
    return [s / 32768.0 for s in struct.unpack("<%dh" % (len(raw) // 2), raw)]


def write_wav(dirs, name, data):
    pk = max(abs(x) for x in data) or 1
    g = min(1.0, 0.92 / pk) if pk > 0.92 else 1.0
    raw = struct.pack("<%dh" % len(data), *[int(max(-1, min(1, x * g)) * 32767) for x in data])
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        w = wave.open(os.path.join(d, name), "wb")
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(raw)
        w.close()


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, x in enumerate(t):
            out[i] += x
    return out


def pad(data, before=0.0, total=None):
    out = [0.0] * int(before * SR) + list(data)
    if total and len(out) < int(total * SR):
        out += [0.0] * (int(total * SR) - len(out))
    return out


def square(freq, dur, vol=0.4, duty=0.5):
    n = int(dur * SR)
    out = []
    for i in range(n):
        ph = (i * freq / SR) % 1.0
        env = min(1.0, i / 60.0) * min(1.0, (n - i) / 80.0)
        out.append((vol if ph < duty else -vol) * env)
    return out


def sine(freq, dur, vol=0.5):
    n = int(dur * SR)
    return [vol * math.sin(2 * math.pi * freq * i / SR) * min(1.0, i / 40.0) * min(1.0, (n - i) / 80.0) for i in range(n)]


def robot(v, ring=70.0, bits=6, hold=2, echo=0.028):
    """ring modulation + bit crush + sample hold + a short metallic echo"""
    out = []
    held = 0.0
    q = 2 ** (bits - 1)
    for i, x in enumerate(v):
        if i % hold == 0:
            held = round(x * q) / q
        out.append(held * (0.45 + 0.55 * math.sin(2 * math.pi * ring * i / SR)))
    d = int(echo * SR)
    for i in range(d, len(out)):
        out[i] += 0.38 * out[i - d]
    pk = max(abs(x) for x in out) or 1
    return [x / pk * 0.95 for x in out]


def chatter(dur, vol=0.18, lo=500, hi=2600, step=0.03):
    """random square blips like a data bus"""
    out = []
    while len(out) < int(dur * SR):
        out += square(random.randint(lo, hi), step * random.uniform(0.6, 1.6), vol, random.choice((0.25, 0.5)))
    return out[: int(dur * SR)]


def modem(dur, vol=0.35):
    out = []
    f = 1200
    while len(out) < int(dur * SR):
        f = random.choice((980, 1180, 1650, 1850, 2100, 2250, 2400))
        seg = random.uniform(0.012, 0.05)
        n = int(seg * SR)
        ph = random.random()
        for i in range(n):
            out.append(vol * math.sin(2 * math.pi * f * i / SR + ph) + random.uniform(-0.08, 0.08))
    return out[: int(dur * SR)]


def noise(dur, vol=1.0, decay=4.0, hp=0.0):
    n = int(dur * SR)
    out = []
    prev = 0.0
    for i in range(n):
        x = random.uniform(-1, 1)
        if hp:
            y = x - prev * hp
            prev = x
            x = y
        out.append(x * vol * math.exp(-decay * i / n))
    return out


def crackle(dur, vol=0.8, rate=700):
    """sparse random clicks over a 100 Hz buzz = arcing electricity"""
    n = int(dur * SR)
    out = [0.0] * n
    env = lambda i: (1 - i / n) ** 0.6
    for i in range(n):
        if random.random() < rate / SR:
            amp = random.uniform(0.4, 1.0) * random.choice((-1, 1))
            L = random.randint(6, 40)
            for k in range(L):
                if i + k < n:
                    out[i + k] += amp * math.exp(-5 * k / L) * random.uniform(0.6, 1.0) * env(i)
        ph = (i * 100 / SR) % 1.0
        out[i] += 0.12 * (2 * ph - 1) * env(i) * (0.5 + 0.5 * math.sin(i * 0.05))
    return [x * vol for x in out]


def sweep(f0, f1, dur, vol=0.5):
    n = int(dur * SR)
    out = []
    ph = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n
        ph += 2 * math.pi * f / SR
        out.append(vol * math.sin(ph) * min(1.0, i / 80.0) * min(1.0, (n - i) / 200.0))
    return out


def main():
    tts = sys.argv[1]
    dirs = sys.argv[2:]

    # --- the voice
    v = read_wav(os.path.join(tts, "hacking.wav"))
    rv = robot(v, ring=70)
    bed = chatter(len(rv) / SR + 0.1, 0.10)
    write_wav(dirs, "hm_hacking.wav", mix(pad(rv), bed))
    write_wav(dirs, "hm_fatal.wav", mix(pad(robot(read_wav(os.path.join(tts, "fatal.wav")), ring=55, bits=5)),
                                        pad(sweep(900, 120, 0.5, 0.15), 0.0)))
    write_wav(dirs, "hm_imin.wav", pad(robot(read_wav(os.path.join(tts, "imin.wav")), ring=85, bits=5)))

    # --- launch: dial-up screech with a power-on whine under it
    write_wav(dirs, "hm_launch.wav", mix(modem(0.7, 0.30), sweep(150, 1400, 0.45, 0.30), pad(chatter(0.4, 0.12), 0.3)))

    # --- in-flight blips
    b1 = []
    for f in (784, 988, 1319, 1568):
        b1 += square(f, 0.055, 0.35, 0.25)
    write_wav(dirs, "hm_beep1.wav", b1 + pad(square(1568, 0.12, 0.30, 0.5), 0.02))
    write_wav(dirs, "hm_beep2.wav", chatter(0.34, 0.30, 400, 3200, 0.028))
    b3 = square(220, 0.07, 0.45, 0.5) + [0.0] * 600 + square(330, 0.07, 0.45, 0.5) + [0.0] * 200 + chatter(0.12, 0.3, 2000, 4000, 0.012)
    write_wav(dirs, "hm_beep3.wav", b3)

    # --- zap
    write_wav(dirs, "hm_zap.wav", mix(crackle(0.45, 0.8, 900), sweep(2400, 300, 0.2, 0.18)))

    # --- the crash: glass + CRT bang, error chord, then arcing
    glass = mix(noise(0.45, 0.8, 5.0, hp=0.9), [x * 0.5 for x in noise(0.25, 1.0, 9.0)])
    bang = sweep(160, 28, 0.35, 0.85)
    err = mix(square(440, 0.28, 0.28, 0.5), square(466, 0.28, 0.28, 0.5), square(622, 0.28, 0.20, 0.5))
    write_wav(dirs, "hm_crash.wav", mix(glass, bang, pad(err, 0.12), pad(crackle(0.9, 0.9, 1100), 0.25),
                                       pad(sweep(1800, 90, 0.5, 0.18), 0.40)))
    print("hackmon sounds written to", dirs)


main()
