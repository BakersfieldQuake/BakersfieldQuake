"""Sounds for the floating head monster (sound/floathead/*.wav, 22050 Hz mono 16 bit).
  sight1, sight2 - "Oh! Hello, friend!" / "There you are!"  (Windows TTS, sped up into a squeaky voice)
  charge         - "Hug time!" then a rising "AAAAAAAAH" scream (formant synth) while it rushes you
  pain           - "Ow! My face!"
  idle           - a little "hm hm hmmm" hum
  pop            - cartoon pop layered on the explosion
  boing          - the mini heads bouncing off the floor
python3 -E -P make_floathead_sounds.py <tts_dir> <outdir>
<tts_dir> holds sight1/sight2/hug/pain.wav rendered with System.Speech (Microsoft David, SSML pitch x-high)."""
import os
import sys
import wave

import numpy as np
from scipy import signal

SR = 22050
rng = np.random.default_rng(42)


def read(path):
    w = wave.open(path, "rb")
    assert w.getframerate() == SR and w.getsampwidth() == 2 and w.getnchannels() == 1, path
    x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
    w.close()
    return x


def write(path, x, peak=0.9):
    x = x / (np.abs(x).max() + 1e-9) * peak
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((x * 32767).astype("<i2").tobytes())
    w.close()


def trim(x, thr=0.01):
    idx = np.nonzero(np.abs(x) > thr)[0]
    return x[max(idx[0] - 200, 0):idx[-1] + 400] if len(idx) else x


def faster(x, k):
    """speed up by k (higher and quicker, like a tape)"""
    n = int(len(x) / k)
    return np.interp(np.arange(n) * k, np.arange(len(x)), x).astype(np.float32)


def fade(x, a=0.005, b=0.03):
    e = np.ones_like(x)
    na, nb = int(a * SR), int(b * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nb:] = np.linspace(1, 0, nb)
    return x * e


def resonator(x, f, bw):
    r = np.exp(-np.pi * bw / SR)
    a = [1, -2 * r * np.cos(2 * np.pi * f / SR), r * r]
    return signal.lfilter([1 - r], a, x)


def voice(f0, formants, breath=0.06):
    """glottal buzz at pitch track f0 (Hz per sample) through parallel formant resonators"""
    ph = np.cumsum(f0 / SR)
    saw = 2 * (ph % 1) - 1
    src = signal.lfilter([1], [1, -0.97], np.diff(saw, prepend=0))     # pulses with a soft spectral tilt
    src = src + breath * rng.standard_normal(len(f0))
    return sum(g * resonator(src, f, bw) for f, bw, g in formants)


AH = [(820, 90, 1.0), (1250, 110, 0.7), (2650, 170, 0.35), (3500, 250, 0.15)]


def scream(dur=2.6):
    t = np.arange(int(dur * SR)) / SR
    f0 = 210 * (440 / 210) ** (t / dur) ** 0.8                          # rising panic
    f0 *= 1 + 0.035 * np.sin(2 * np.pi * 6.5 * t) + 0.01 * rng.standard_normal(len(t)).cumsum() / 300
    x = voice(f0, AH, breath=0.12)
    env = np.minimum(t / 0.06, 1) * (0.75 + 0.25 * t / dur)
    x = np.tanh(2.2 * x / (np.abs(x).max() + 1e-9)) * env                # yelled, a bit raspy
    return fade(x, 0.002, 0.04)


def hum():
    notes = [(0.30, 165), (0.08, 0), (0.30, 185), (0.08, 0), (0.60, 147)]
    out = []
    for d, f in notes:
        n = int(d * SR)
        t = np.arange(n) / SR
        if not f:
            out.append(np.zeros(n))
            continue
        f0 = f * (1 + 0.02 * np.sin(2 * np.pi * 5 * t))
        x = voice(f0, [(260, 60, 1.0), (1000, 200, 0.12), (2200, 300, 0.05)], breath=0.02)   # "mmm": nasal, closed
        out.append(x * np.sin(np.pi * np.minimum(t / d, 1)) ** 0.5)
    return np.concatenate(out)


def pop():
    t = np.arange(int(0.18 * SR)) / SR
    f = 950 * np.exp(-t / 0.035) + 160
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05)
    click = rng.standard_normal(len(t)) * np.exp(-t / 0.004)
    return x + 0.6 * click


def boing():
    t = np.arange(int(0.55 * SR)) / SR
    f = 210 * (1 + 0.45 * np.exp(-t / 0.18) * np.sin(2 * np.pi * 11 * t)) * (1 + 0.6 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return x * np.exp(-t / 0.2) * np.minimum(t / 0.004, 1)


def main():
    tts, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    say = lambda name, k: fade(faster(trim(read(os.path.join(tts, name + ".wav"))), k))
    write(os.path.join(out, "sight1.wav"), say("sight1", 1.15))
    write(os.path.join(out, "sight2.wav"), say("sight2", 1.15))
    write(os.path.join(out, "pain.wav"), say("pain", 1.2))
    hug = say("hug", 1.1)
    sc = scream()
    write(os.path.join(out, "charge.wav"), np.concatenate([hug / np.abs(hug).max(), np.zeros(int(0.05 * SR)),
                                                           0.95 * sc / np.abs(sc).max()]))
    write(os.path.join(out, "idle.wav"), fade(hum()), peak=0.6)
    write(os.path.join(out, "pop.wav"), fade(pop(), 0.001, 0.02))
    write(os.path.join(out, "boing.wav"), fade(boing(), 0.001, 0.05), peak=0.7)
    for f in sorted(os.listdir(out)):
        w = wave.open(os.path.join(out, f), "rb")
        print("%-11s %.2fs" % (f, w.getnframes() / SR))
        w.close()


if __name__ == "__main__":
    main()
