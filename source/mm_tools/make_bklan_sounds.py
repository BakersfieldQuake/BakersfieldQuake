"""Sounds for bklan3's movers (bklan_movers.qc):
  sound/bklan/pinkcar.wav  the hot pink supercar's music while someone rides it: an original bouncy chiptune,
                           125 bpm, 10 bars = 19.2 s (BK_MUSIC_LEN), square lead + triangle bass + noise drums
  sound/bklan/notpink.wav  "It's not pink!" in a high voice (made with Windows' Zira voice, pitched up; see
                           out/tts/, rebuilt by hand with ffmpeg, not here)
usage: python make_bklan_sounds.py"""
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "sound", "bklan")
SR = 22050
BPM = 125
BEAT = 60.0 / BPM
STEP = BEAT / 4                      # sixteenth notes
N_STEPS = 10 * 16                    # 10 bars
rng = np.random.default_rng(7)


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12.0)


def square(f, t, duty=0.5):
    return np.where((t * f) % 1.0 < duty, 1.0, -1.0)


def tri(f, t):
    return 2 * np.abs(2 * ((t * f) % 1.0) - 1) - 1


def env(n, a=0.004, r=0.6):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / max(r, 1e-3) * 3)
    return e


# C major, a bouncy hook in two halves; '.' = rest, numbers are MIDI notes per eighth note
LEAD = [
    76, 79, 84, 79, 76, 79, 81, 79,   77, 81, 84, 81, 77, 76, 74, 72,
    76, 79, 84, 86, 88, 86, 84, 81,   79, 77, 76, 74, 76, 0, 79, 0,
    81, 84, 88, 84, 81, 84, 86, 84,   79, 83, 86, 83, 79, 81, 83, 86,
    88, 86, 84, 83, 84, 0, 88, 91,   88, 84, 79, 76, 72, 0, 0, 0,
    76, 79, 84, 79, 76, 79, 81, 79,   84, 88, 91, 88, 84, 0, 96, 0,
]
CHORDS = [48, 53, 48, 43, 45, 41, 43, 43, 48, 48]          # bass root per bar (C F C G Am F G G C C)

n_total = int(round(N_STEPS * STEP * SR))
mix = np.zeros(n_total)
# lead: eighth notes, 25% duty square with a little vibrato
for i, note in enumerate(LEAD):
    if not note:
        continue
    s0 = int(round(i * 2 * STEP * SR))
    n = int(2 * STEP * SR * 0.92)
    t = np.arange(n) / SR
    f = hz(note) * (1 + 0.004 * np.sin(2 * np.pi * 6 * t))
    mix[s0:s0 + n] += 0.22 * square(f, t, 0.25) * env(n, r=0.5)[:n]
# echo of the lead an eighth later, quieter (that chiptune shimmer)
d = int(round(2 * STEP * SR * 1.5))
echo = np.zeros_like(mix)
echo[d:] = mix[:-d] * 0.35
mix += echo
# bass: octave-bouncing triangle on every eighth
for bar, root in enumerate(CHORDS):
    for k in range(8):
        note = root + (12 if k % 2 else 0)
        s0 = int(round((bar * 16 + k * 2) * STEP * SR))
        n = int(2 * STEP * SR * 0.85)
        t = np.arange(n) / SR
        mix[s0:s0 + n] += 0.30 * tri(hz(note), t) * env(n, r=0.35)
# drums: kick on 1 and 3, snare on 2 and 4, hats on the off eighths
for st in range(N_STEPS):
    s0 = int(round(st * STEP * SR))
    if st % 8 == 0:                                       # kick: falling sine
        n = int(0.16 * SR)
        t = np.arange(n) / SR
        f = 150 * np.exp(-t * 28) + 45
        mix[s0:s0 + n] += 0.55 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)
    if st % 8 == 4:                                       # snare: noise burst + tone
        n = int(0.14 * SR)
        t = np.arange(n) / SR
        mix[s0:s0 + n] += (0.30 * rng.uniform(-1, 1, n) + 0.12 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 26)
    if st % 4 == 2:                                       # hat
        n = int(0.04 * SR)
        hat = rng.uniform(-1, 1, n)
        hat = hat - np.convolve(hat, np.ones(4) / 4, "same")
        mix[s0:s0 + n] += 0.16 * hat * np.exp(-np.arange(n) / SR * 90)
mix = mix[:n_total]
mix = np.tanh(mix * 1.1)                                 # glue it
mix = mix / np.max(np.abs(mix)) * 0.89
fade = int(0.01 * SR)
mix[:fade] *= np.linspace(0, 1, fade)
mix[-fade:] *= np.linspace(1, 0, fade)
os.makedirs(OUT, exist_ok=True)
with wave.open(os.path.join(OUT, "pinkcar.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote sound/bklan/pinkcar.wav, %.2f s" % (len(mix) / SR))
