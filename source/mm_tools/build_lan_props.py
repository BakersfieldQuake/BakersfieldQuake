"""Master asset builder for BakersfieldQuake Explodable LAN Party Props:
  1. Animated CRT Monitor Screens + scripts/lan_props.shader (lan_screens.py)
  2. 4 CRT Monitors, 4 PC Towers, 4 Chairs, 4 (+1 compact) Tables, 6 Debris MD3s (lan_models.py)
  3. 5 custom 22050 Hz 16-bit PCM explosion/shatter WAVs in sound/lan/

Usage:
  python -I source/mm_tools/build_lan_props.py
"""
import math
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lan_models
import lan_screens

MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS_BKLAN = os.path.join(MOD, "progs", "bklan")
SCRIPTS_DIR = os.path.join(MOD, "scripts")
SOUND_LAN = os.path.join(MOD, "sound", "lan")


def _write_wav(path: str, samples: np.ndarray, sr: int = 22050):
    peak = float(np.max(np.abs(samples))) or 1.0
    normed = np.clip(samples / peak * 0.88, -1.0, 1.0)
    pcm = (normed * 32767.0).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def build_sounds(sound_dir: str):
    os.makedirs(sound_dir, exist_ok=True)
    sr = 22050
    rng = np.random.default_rng(1998)

    # 1. crt_implode.wav: vacuum implosion thump + thick glass shatter + HV flyback zap
    dur = 0.78
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    thump = np.sin(2 * np.pi * (145 * np.exp(-t * 14.0) + 38) * t) * np.exp(-t * 9.5) * 1.15
    zap = np.sin(2 * np.pi * (2400 - 1600 * t) * t + 4.0 * np.sin(2 * np.pi * 120 * t)) * np.exp(-t * 15.0) * 0.45
    shatter = rng.normal(0, 1, t.shape) * np.exp(-t * 7.2) * 0.65
    # Add discrete glass shard pings
    pings = np.zeros_like(t)
    for dt_s, freq, amp in ((0.03, 3150, 0.38), (0.08, 4280, 0.32), (0.15, 2790, 0.28), (0.24, 5120, 0.22), (0.36, 3680, 0.16)):
        m = t >= dt_s
        pings[m] += amp * np.sin(2 * np.pi * freq * (t[m] - dt_s)) * np.exp(-(t[m] - dt_s) * 26.0)
    _write_wav(os.path.join(sound_dir, "crt_implode.wav"), thump + zap + shatter + pings, sr)

    # 2. pc_boom.wav: ATX PSU capacitor pop + punchy bass blast + sheet-metal rattle + spark sizzle
    dur = 0.85
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    boom = np.sin(2 * np.pi * (120 * np.exp(-t * 11.0) + 32) * t) * np.exp(-t * 6.8) * 1.3
    crunch = np.tanh(rng.normal(0, 1.8, t.shape)) * np.exp(-t * 8.5) * 0.65
    metal = (np.sin(2 * np.pi * 485 * t) + 0.6 * np.sin(2 * np.pi * 732 * t)) * np.exp(-t * 11.0) * 0.35
    sizzle = rng.normal(0, 1, t.shape) * (np.sin(2 * np.pi * 60 * t) > 0.2) * np.exp(-t * 4.5) * 0.28
    _write_wav(os.path.join(sound_dir, "pc_boom.wav"), boom + crunch + metal + sizzle, sr)

    # 3. chair_break.wav: tubular steel frame clang + plastic base snap
    dur = 0.62
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    pop = np.sin(2 * np.pi * (165 * np.exp(-t * 16.0) + 55) * t) * np.exp(-t * 12.0)
    clang = (
        0.55 * np.sin(2 * np.pi * 590 * t)
        + 0.40 * np.sin(2 * np.pi * 935 * t)
        + 0.28 * np.sin(2 * np.pi * 1410 * t)
    ) * np.exp(-t * 8.5)
    snap = rng.normal(0, 1, t.shape) * np.exp(-t * 18.0) * 0.75
    _write_wav(os.path.join(sound_dir, "chair_break.wav"), pop + clang + snap, sr)

    # 4. table_smash.wav: heavy wood/laminate splintering crack + folding steel leg collapse
    dur = 0.88
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    low = np.sin(2 * np.pi * (105 * np.exp(-t * 9.0) + 35) * t) * np.exp(-t * 6.5) * 1.25
    crack1 = rng.normal(0, 1, t.shape) * np.exp(-t * 11.0) * 0.85
    crack2 = np.where(t > 0.09, rng.normal(0, 1, t.shape) * np.exp(-np.maximum(0, t - 0.09) * 12.0) * 0.55, 0.0)
    legs = (0.45 * np.sin(2 * np.pi * 410 * t) + 0.35 * np.sin(2 * np.pi * 685 * t)) * np.exp(-t * 7.0)
    _write_wav(os.path.join(sound_dir, "table_smash.wav"), low + crack1 + crack2 + legs, sr)

    # 5. glass_tink.wav: crisp bouncing CRT glass / debris clink
    dur = 0.28
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    tink = (
        0.6 * np.sin(2 * np.pi * 3420 * t)
        + 0.4 * np.sin(2 * np.pi * 4890 * t)
        + 0.25 * rng.normal(0, 1, t.shape) * np.exp(-t * 45.0)
    ) * np.exp(-t * 18.0)
    _write_wav(os.path.join(sound_dir, "glass_tink.wav"), tink, sr)
    print(f"Wrote 5 explosion/shatter WAVs to {sound_dir}")


def main():
    lan_screens.build_all_screens(PROGS_BKLAN, SCRIPTS_DIR)
    lan_models.build_all_models(PROGS_BKLAN)
    build_sounds(SOUND_LAN)


if __name__ == "__main__":
    main()
