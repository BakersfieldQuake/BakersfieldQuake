"""make_tuktuk_sounds.py — Synthesizes 22050 Hz 16-bit mono WAVs for the Bangkok Tuk-Tuk:
  - sound/vehicles/idle_tuktuk.wav        (putt-putt-putt 2-stroke idle loop)
  - sound/vehicles/engine_grain_tuktuk.wav (zippy high-rev 2-stroke expansion-chamber loop)
  - sound/vehicles/horn_tuktuk.wav         (cheerful double-chirp Bangkok scooter horn)
"""
from __future__ import annotations

import os
import wave
import numpy as np

SR = 22050
OUT_DIR = r"G:\Quake\Combat\_bakersfield_dev\staged_assets\sound\vehicles"


def write_wav(path: str, samples: np.ndarray):
    s = np.clip(samples, -0.98, 0.98)
    pcm = (s * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"Wrote {path} ({len(pcm)/SR:.2f}s, {os.path.getsize(path)} bytes)")


def make_idle_tuktuk() -> np.ndarray:
    dur = 2.0
    n = int(SR * dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(101)
    # 16 Hz 2-stroke putt-putt firing cadence (exact integer cycles in 2.0s for seamless loop!)
    f_fire = 16.0
    ph = (t * f_fire) % 1.0
    pulse = np.exp(-ph * 9.5)
    sig = (
        0.52 * pulse * np.sin(2.0 * math.pi * 112.0 * t + 0.6 * np.sin(2.0 * math.pi * 56.0 * t))
        + 0.25 * pulse * np.sin(2.0 * math.pi * 224.0 * t)
        + 0.16 * np.sin(2.0 * math.pi * 56.0 * t)
        + 0.10 * pulse * np.sin(2.0 * math.pi * 448.0 * t)
    )
    # Subtle tinny exhaust flutter
    noise = rng.normal(0.0, 0.04, n) * (0.35 + 0.65 * pulse)
    out = sig + noise
    out /= max(1e-6, np.max(np.abs(out))) * 1.35
    return out


def make_engine_grain_tuktuk() -> np.ndarray:
    dur = 0.60
    n = int(SR * dur)
    t = np.arange(n) / SR
    # 75 Hz fundamental (45 cycles in 0.60s -> seamless grain loop!)
    f0 = 75.0
    ph = (t * f0) % 1.0
    bark = np.exp(-ph * 4.2)
    sig = (
        0.48 * bark * np.sin(2.0 * math.pi * (f0 * 2.0) * t)
        + 0.34 * np.sin(2.0 * math.pi * f0 * t)
        + 0.28 * bark * np.sin(2.0 * math.pi * (f0 * 3.0) * t)
        + 0.18 * bark * np.sin(2.0 * math.pi * (f0 * 5.0) * t)
        + 0.10 * np.sin(2.0 * math.pi * (f0 * 7.0) * t)
    )
    out = np.tanh(sig * 1.45)
    out /= max(1e-6, np.max(np.abs(out))) * 1.15
    return out


def make_horn_tuktuk() -> np.ndarray:
    # Classic Bangkok Tuk-Tuk cheerful double-beep ("BEEP-BEEP!")
    dur = 0.56
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.zeros(n, dtype=np.float64)
    # Chirp 1: 0.02..0.18, Chirp 2: 0.24..0.48
    for a, b in ((0.02, 0.18), (0.24, 0.48)):
        m = (t >= a) & (t <= b)
        u = (t[m] - a) / (b - a)
        att = np.minimum(1.0, u / 0.06)
        rel = np.minimum(1.0, (1.0 - u) / 0.12)
        env[m] = att * rel
    # Nasal dual-tone scooter disc horn (~540 Hz + 675 Hz + metallic brass buzz)
    raw = (
        0.55 * np.sin(2.0 * math.pi * 540.0 * t)
        + 0.42 * np.sin(2.0 * math.pi * 675.0 * t)
        + 0.28 * np.sin(2.0 * math.pi * 1080.0 * t)
        + 0.18 * np.sin(2.0 * math.pi * 1620.0 * t)
    )
    out = np.tanh(raw * 1.6) * env
    out /= max(1e-6, np.max(np.abs(out))) * 1.15
    return out


import math  # used above in functions


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    write_wav(os.path.join(OUT_DIR, "idle_tuktuk.wav"), make_idle_tuktuk())
    write_wav(os.path.join(OUT_DIR, "engine_grain_tuktuk.wav"), make_engine_grain_tuktuk())
    write_wav(os.path.join(OUT_DIR, "horn_tuktuk.wav"), make_horn_tuktuk())


if __name__ == "__main__":
    main()
