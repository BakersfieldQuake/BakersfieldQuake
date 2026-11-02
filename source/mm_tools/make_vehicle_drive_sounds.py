"""Synthesizes the sounds for DRIVING the van (vehicle_drive.qc) into G:\\Quake\\Combat\\BakersfieldQuake\\sound\\vehicles\\:
  - engine_grain.wav : 0.32 s Hann-windowed diesel firing pulses at a nominal 44 Hz firing rate. The QC replays one every
                       half-length on alternating channels with sound7's pitch following the RPM, so two overlapping grains
                       always sum to a steady engine note whose pitch can change several times a second (a plain loop
                       can only change pitch when it restarts).
  - tire_squeal.wav  : 0.30 s windowed band-passed rubber squeal, same overlap trick, volume follows how much the tyres slip
  - horn.wav         : 0.50 s two-tone van horn (a minor third apart)
  - ignition.wav     : 1.10 s starter cranking, then the diesel catches
python3.13 make_vehicle_drive_sounds.py   (needs numpy)
"""
import os
import struct
import wave

import numpy as np

RATE = 22050
OUT = "G:\\Quake\\Combat\\BakersfieldQuake\\sound\\vehicles\\"
rng = np.random.default_rng(1983)


def write_wav(name, x, peak=0.85):
    x = np.asarray(x, dtype=np.float64)
    x = x * (peak / (np.max(np.abs(x)) or 1.0))
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(OUT + name, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(pcm)
    print("wrote", name, "%.2fs" % (len(x) / RATE))


def lowpass(x, cutoff):
    a = 1.0 - np.exp(-2.0 * np.pi * cutoff / RATE)
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def hann(n):
    return 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / n)


def firing_pulse(n_samples):
    """One cylinder firing: a diesel knock (filtered noise burst) on a low thump."""
    t = np.arange(n_samples) / RATE
    knock = lowpass(rng.standard_normal(n_samples), 1100) * np.exp(-t * 85)
    thump = np.sin(2 * np.pi * 62 * t) * np.exp(-t * 70)
    return knock * 1.4 + thump * 1.0


def engine_pulses(duration, f_start, f_end, jitter=0.04):
    n = int(RATE * duration)
    out = np.zeros(n)
    t = 0.0
    plen = int(RATE * 0.05)
    while t < duration:
        f = f_start + (f_end - f_start) * (t / duration)
        i = int(t * RATE)
        p = firing_pulse(plen) * (0.85 + 0.3 * rng.random())
        end = min(n, i + plen)
        out[i:end] += p[: end - i]
        t += (1.0 / f) * (1 + jitter * (rng.random() - 0.5) * 2)
    return out


def engine_grain():
    dur = 0.32
    n = int(RATE * dur)
    x = engine_pulses(dur, 44, 44)
    t = np.arange(n) / RATE
    x += 0.25 * np.sin(2 * np.pi * 44 * t)			# the body of the block droning at the firing rate
    x += 0.12 * np.sin(2 * np.pi * 88 * t + 0.7)
    x = lowpass(x, 2600)
    write_wav("engine_grain.wav", x * hann(n))


def tire_squeal():
    dur = 0.30
    n = int(RATE * dur)
    t = np.arange(n) / RATE
    noise = highpass(lowpass(rng.standard_normal(n), 3400), 1300)
    tone = np.sin(2 * np.pi * (1850 + 90 * np.sin(2 * np.pi * 7 * t)) * t)
    tone2 = np.sin(2 * np.pi * (2430 + 60 * np.sin(2 * np.pi * 5 * t + 1)) * t)
    x = noise * 0.55 + tone * 0.35 + tone2 * 0.18
    x *= 1.0 + 0.25 * np.sin(2 * np.pi * 31 * t)
    write_wav("tire_squeal.wav", x * hann(n), peak=0.7)


def horn():
    dur = 0.50
    n = int(RATE * dur)
    t = np.arange(n) / RATE

    def note(f):
        w = np.zeros(n)
        for k, a in ((1, 1.0), (2, 0.5), (3, 0.38), (4, 0.2), (5, 0.16)):
            w += a * np.sin(2 * np.pi * f * k * t)
        return w

    x = note(415) + note(494)
    env = np.minimum(1.0, t / 0.012) * np.minimum(1.0, (dur - t) / 0.04)
    x = lowpass(x, 5200) * env
    write_wav("horn.wav", x)


def ignition():
    dur = 1.10
    n = int(RATE * dur)
    t = np.arange(n) / RATE
    crank_end = 0.62
    x = np.zeros(n)
    # starter: a whirring sawtooth, chugging as the engine turns over against compression
    c = t < crank_end
    chug = 0.55 + 0.45 * np.sin(2 * np.pi * (7.0 + 5.0 * t / crank_end) * t) ** 2
    saw = 2 * ((170 + 60 * t / crank_end) * t % 1.0) - 1
    x[c] += (lowpass(saw, 1600) * chug)[c] * 0.5
    # the diesel catches and settles to idle
    i0 = int(crank_end * RATE)
    catch = engine_pulses(dur - crank_end, 16, 27)
    catch *= np.minimum(1.0, np.arange(len(catch)) / (RATE * 0.12))
    x[i0:] += catch[: n - i0] * 0.9
    x = lowpass(x, 3000)
    write_wav("ignition.wav", x * np.minimum(1.0, (dur - t) / 0.08))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    engine_grain()
    tire_squeal()
    horn()
    ignition()
