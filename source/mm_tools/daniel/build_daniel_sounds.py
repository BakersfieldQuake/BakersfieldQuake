"""Builds crisp, loudness-normalized 22050 Hz 16-bit mono Quake WAV sound assets
for the Daniel ('4 AM Moving the Table / SHAAA / Justin Berry Webcam / CCC') meme pack
in G:\\Quake\\Combat\\BakersfieldQuake\\sound\\daniel\\.

Copies source MP4s into source/mm_tools/ref/daniel/ if needed so rebuilds are 100% reproducible.
"""

from __future__ import annotations

import os
import subprocess
import wave
from pathlib import Path

import numpy as np

CUR_DIR = Path(__file__).resolve().parent
TOOLS_DIR = CUR_DIR.parent
MOD_DIR = TOOLS_DIR.parent.parent
REF_DIR = TOOLS_DIR / "ref" / "daniel"
SND_DIR = MOD_DIR / "sound" / "daniel"

SR = 22050


def read_wav_mono(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wf:
        n = wf.getnframes()
        raw = np.frombuffer(wf.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
        ch = wf.getnchannels()
        if ch > 1:
            raw = raw.reshape(-1, ch).mean(axis=1)
    return raw


def write_wav_mono(path: Path, samples: np.ndarray, peak: float = 0.90) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = samples.astype(np.float32).copy()
    # Gentle soft-knee compression so quieter words cut through Quake combat!
    rms = float(np.sqrt(np.mean(s * s) + 1e-8))
    if rms > 1e-4:
        s = np.tanh(s / (rms * 3.2)) * (rms * 3.2)
    mx = float(np.max(np.abs(s))) if len(s) else 1.0
    if mx > 1e-5:
        s = s * (peak / mx)
    fade = min(int(0.018 * SR), max(1, len(s) // 12))
    if fade > 1:
        ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
        s[:fade] *= ramp
        s[-fade:] *= ramp[::-1]
    pcm = np.clip(np.round(s * 32767.0), -32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"Wrote {path.name:22s} ({len(s)/SR:5.2f}s, {path.stat().st_size:7,d} bytes)")


def synth_table_screech(dur: float, rng: np.random.Generator) -> np.ndarray:
    """Heavy wooden table legs shuddering & screeching across floor at 4 AM."""
    n = int(dur * SR)
    t = np.linspace(0.0, dur, n, endpoint=False, dtype=np.float32)
    # Stick-slip resonant wood scrape (chattering impulses + 190/385/610 Hz wood modes)
    f0 = 185.0 + 38.0 * np.sin(2.0 * np.pi * 4.5 * t) + 14.0 * np.sin(2.0 * np.pi * 19.0 * t)
    ph = 2.0 * np.pi * np.cumsum(f0) / SR
    chatter = 0.5 + 0.5 * np.tanh(3.5 * np.sin(2.0 * np.pi * 31.0 * t))
    wood = (
        0.55 * np.sin(ph)
        + 0.35 * np.sin(2.04 * ph + 0.5)
        + 0.22 * np.sin(3.18 * ph + 1.1)
    ) * chatter
    # Filtered floor friction grit
    grit = rng.standard_normal(n).astype(np.float32)
    lp = np.zeros_like(grit)
    a = 0.22
    for i in range(1, n):
        lp[i] = (1.0 - a) * lp[i - 1] + a * grit[i]
    env = np.sin(np.pi * np.clip(t / dur, 0.0, 1.0)) ** 0.45
    return (0.62 * wood + 0.38 * lp * chatter) * env


def main() -> None:
    SND_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261101)

    v1 = read_wav_mono(REF_DIR / "v1_table4am.wav")
    v2 = read_wav_mono(REF_DIR / "v2_shaaa.wav")
    v3 = read_wav_mono(REF_DIR / "v3_webcam.wav")
    v4 = read_wav_mono(REF_DIR / "v4_ccc.wav")

    # 1. dad_4am.wav — "What the fuck! It's 4 in the morning, Daniel! What is this noise?!"
    c_dad = v1[int(1.02 * SR):int(4.24 * SR)].copy()
    write_wav_mono(SND_DIR / "dad_4am.wav", c_dad, peak=0.92)

    # 2. sorry_table.wav — "Sorry! I was just moving the table!"
    c_sorry = np.concatenate([v1[int(4.14 * SR):].copy(), np.zeros(int(0.06 * SR), dtype=np.float32)])
    write_wav_mono(SND_DIR / "sorry_table.wav", c_sorry, peak=0.92)

    # 3. table_drag.wav — Authentic 0.70s..1.04s drag sound from v1 + enhanced 4AM wood screech!
    raw_drag = v1[int(0.68 * SR):int(1.05 * SR)].copy()
    syn_drag = synth_table_screech(1.15, rng) * 0.48
    drag_mix = syn_drag.copy()
    drag_mix[:len(raw_drag)] += raw_drag * 1.10
    write_wav_mono(SND_DIR / "table_drag.wav", drag_mix, peak=0.88)

    # 4. shaaa_scream.wav — Massive LAN party "SHAAAAAAAAAAAAAAAAAAA!" rage scream (punchy 4.2s cut)
    c_shaaa = v2[int(2.60 * SR):int(6.85 * SR)].copy()
    write_wav_mono(SND_DIR / "shaaa_scream.wav", c_shaaa, peak=0.93)

    # 5. cant_see_webcam.wav — "Aaaah, I can't see! When is Justin Berry coming? I wanna borrow his webcam!"
    p_a = v3[int(0.65 * SR):int(2.65 * SR)]
    p_b = v3[int(3.05 * SR):int(7.45 * SR)]
    gap = np.zeros(int(0.12 * SR), dtype=np.float32)
    c_webcam = np.concatenate([p_a, gap, p_b])
    write_wav_mono(SND_DIR / "cant_see_webcam.wav", c_webcam, peak=0.91)

    # 6. ccc_chant.wav — Full unhinged "CCC! C-C-C-C-C-C-C-C-C-C!" rapid-fire grin chant
    c_ccc = v4[int(0.02 * SR):int(4.15 * SR)].copy()
    write_wav_mono(SND_DIR / "ccc_chant.wav", c_ccc, peak=0.92)

    # 7. ccc_burst.wav — Tight 1.65s "CCC! C-C-C-C!" attack burst
    c_burst = v4[int(0.02 * SR):int(1.68 * SR)].copy()
    write_wav_mono(SND_DIR / "ccc_burst.wav", c_burst, peak=0.92)


if __name__ == "__main__":
    main()
