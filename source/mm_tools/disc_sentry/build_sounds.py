"""Synthesize over-the-top, scary, aggressive sound effects for the Disc Sentry Gun.

Outputs 22050 Hz, 16-bit mono PCM WAVs to source/mm_tools/out/disc_sentry/sounds/:
  - activate_deploy.wav  (Disc slam -> CRT degauss BWOOOOM -> hydraulic leg locks -> demonic BIOS roar)
  - spot_klaxon.wav      (Aggressive target-acquisition radar klaxon + servo snap)
  - fire_heavy.wav       (Over-the-top floppy cannon blast + sub-thump + spinning disc whiz)
  - fire_msdos_mg.wav    (Ferocious rapid-fire MS-DOS machine gun floppy shredder bark)
  - explode_mega.wav     (Apocalyptic CRT implosion + tectonic blast + electric arc + floppy rain)
  - floppy_clatter.wav   (Crisp plastic + steel shutter bounce clack for dynamic 3D floor bounces)

Usage:
    python source/mm_tools/disc_sentry/build_sounds.py
"""
from __future__ import annotations

import json
import os
import wave
from typing import Dict

import numpy as np

SR = 22050
HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.abspath(os.path.join(HERE, ".."))
OUT_DIR = os.path.join(MM_TOOLS, "out", "disc_sentry", "sounds")


def _t(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR)), dtype=np.float32) / float(SR)


def _lp1(x: np.ndarray, fc: float) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32)
    n = len(arr)
    if n < 2:
        return arr
    alpha = float(np.exp(-2.0 * np.pi * fc / SR))
    nfft = 1 << max(1, (n * 2 - 1)).bit_length()
    w = 2.0 * np.pi * np.fft.rfftfreq(nfft)
    h = (1.0 - alpha) / (1.0 - alpha * np.exp(-1j * w))
    return np.fft.irfft(np.fft.rfft(arr, nfft) * h, nfft)[:n].astype(np.float32)


def _hp1(x: np.ndarray, fc: float) -> np.ndarray:
    return (np.asarray(x, dtype=np.float32) - _lp1(x, fc)).astype(np.float32)


def _bp(x: np.ndarray, flo: float, fhi: float) -> np.ndarray:
    return _lp1(_hp1(x, flo), fhi)


def _saturate(x: np.ndarray, drive: float = 2.4) -> np.ndarray:
    return np.tanh(np.asarray(x, dtype=np.float32) * drive).astype(np.float32)


def _bitcrush(x: np.ndarray, levels: int = 18, hold: int = 2) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32).copy()
    if hold > 1:
        idx = (np.arange(len(arr)) // hold) * hold
        arr = arr[idx]
    return np.round(arr * levels) / float(levels)


def _mix_at(base: np.ndarray, over: np.ndarray, t_sec: float, gain: float = 1.0) -> np.ndarray:
    off = max(0, int(round(t_sec * SR)))
    out = base
    if off + len(over) > len(out):
        out = np.pad(out, (0, off + len(over) - len(out)))
    out[off : off + len(over)] += float(gain) * np.asarray(over, dtype=np.float32)
    return out


def _sweep_sine(t: np.ndarray, f0: float, f1: float, exp_curve: bool = True) -> np.ndarray:
    u = np.clip(t / max(t[-1], 1e-6), 0.0, 1.0)
    if exp_curve and f0 > 0 and f1 > 0:
        freq = f0 * ((f1 / f0) ** u)
    else:
        freq = f0 + (f1 - f0) * u
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    return np.sin(phase).astype(np.float32)


def _fade(x: np.ndarray, fin: float = 0.004, fout: float = 0.04) -> np.ndarray:
    out = np.asarray(x, dtype=np.float32).copy()
    na = min(int(fin * SR), len(out) // 3)
    nb = min(int(fout * SR), len(out) // 3)
    if na > 1:
        out[:na] *= np.linspace(0.0, 1.0, na, dtype=np.float32)
    if nb > 1:
        out[-nb:] *= np.linspace(1.0, 0.0, nb, dtype=np.float32)
    return out


def _write_wav(path: str, audio: np.ndarray, peak: float = 0.94) -> Dict:
    arr = np.asarray(audio, dtype=np.float32)
    mx = float(np.max(np.abs(arr))) if len(arr) else 0.0
    if mx > 1e-7:
        arr = arr * (peak / mx)
    pcm = np.clip(np.round(arr * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    rms = float(np.sqrt(np.mean(arr ** 2)))
    rms_db = round(20.0 * np.log10(max(rms, 1e-6)), 1)
    return {"file": os.path.basename(path), "dur": round(len(arr) / float(SR), 2), "rms_db": rms_db}


def synth_floppy_clatter(seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = _t(0.16)
    # Hard ABS plastic double-tap + stainless shutter metallic ping
    n1 = _bp(rng.standard_normal(len(t)), 700, 3800) * np.exp(-t * 68.0)
    shutter = np.sin(2.0 * np.pi * 2450.0 * t) * np.exp(-t * 95.0) * 0.45
    shutter += np.sin(2.0 * np.pi * 4120.0 * t) * np.exp(-t * 110.0) * 0.30
    hit1 = n1 * 0.9 + shutter
    t2 = _t(0.10)
    n2 = _bp(rng.standard_normal(len(t2)), 950, 4400) * np.exp(-t2 * 85.0) * 0.55
    out = _mix_at(hit1, n2, 0.022, 0.75)
    return _fade(_saturate(out, 1.8), 0.001, 0.025)


def synth_activate_deploy() -> np.ndarray:
    rng = np.random.default_rng(101)
    out = np.zeros(int(1.70 * SR), dtype=np.float32)

    # 1. Disc slam onto floor (0.00s)
    ts = _t(0.18)
    slam = _sweep_sine(ts, 210.0, 44.0) * np.exp(-ts * 24.0)
    slam += _bp(rng.standard_normal(len(ts)), 400, 3600) * np.exp(-ts * 45.0) * 0.65
    out = _mix_at(out, _saturate(slam, 2.5), 0.0, 0.95)

    # 2. Terrifying CRT High-Voltage Degauss BWOOOONG + Flyback Scream (0.14s .. 0.95s)
    td = _t(0.90)
    env_d = np.sin(np.pi * np.clip(td / 0.14, 0.0, 1.0)) * np.exp(-np.maximum(0.0, td - 0.10) * 3.4)
    wob = np.sin(2.0 * np.pi * 11.0 * td) * 14.0
    degauss = (
        0.55 * np.sin(2.0 * np.pi * (62.0 + wob * 0.3) * td)
        + 0.45 * np.sin(2.0 * np.pi * (124.0 + wob) * td)
        + 0.30 * np.sign(np.sin(2.0 * np.pi * 186.0 * td))
    ) * env_d
    # High-voltage CRT flyback whine sweeping down angrily
    flyback = _sweep_sine(td, 6400.0, 1850.0) * np.exp(-td * 4.5) * 0.32
    arc = _bp(rng.standard_normal(len(td)), 1800, 6800) * (np.sin(2.0 * np.pi * 28.0 * td) > 0.2) * np.exp(-td * 4.0) * 0.45
    out = _mix_at(out, _saturate(degauss * 1.4 + flyback + arc, 2.2), 0.14, 0.92)

    # 3. Three heavy hydraulic tripod leg slams (0.50s, 0.64s, 0.78s)
    for idx, t_leg in enumerate((0.50, 0.64, 0.78)):
        tl = _t(0.18)
        f_top = 260.0 + idx * 35.0
        clank = _sweep_sine(tl, f_top, 42.0) * np.exp(-tl * 26.0)
        clank += _bp(rng.standard_normal(len(tl)), 900, 4800) * np.exp(-tl * 55.0) * 0.7
        clank += np.sin(2.0 * np.pi * (520.0 + idx * 60.0) * tl) * np.exp(-tl * 38.0) * 0.45
        out = _mix_at(out, _saturate(clank, 2.8), t_leg, 0.85)

    # 4. Aggressive Distorted BIOS-from-Hell Triple Surge + Servo Lock (0.98s .. 1.62s)
    tb = _t(0.62)
    servo = _sweep_sine(tb, 140.0, 740.0) * np.exp(-tb * 3.8) * 0.42
    out = _mix_at(out, _saturate(servo, 2.0), 0.96, 0.8)
    for bi, freq in enumerate((220.0, 330.0, 440.0)):
        tp = _t(0.14)
        tone = (
            np.sign(np.sin(2.0 * np.pi * freq * tp)) * 0.55
            + np.sin(2.0 * np.pi * (freq * 0.5) * tp) * 0.55
            + np.sin(2.0 * np.pi * (freq * 1.505) * tp) * 0.35
        ) * np.exp(-tp * 14.0)
        out = _mix_at(out, _saturate(_bitcrush(tone, 14, 2), 2.4), 1.06 + bi * 0.14, 0.78)

    return _fade(out, 0.003, 0.06)


def synth_spot_klaxon() -> np.ndarray:
    rng = np.random.default_rng(202)
    out = np.zeros(int(0.76 * SR), dtype=np.float32)

    # Sharp metallic turret snap
    ts = _t(0.09)
    snap = _bp(rng.standard_normal(len(ts)), 1100, 5200) * np.exp(-ts * 65.0) + _sweep_sine(ts, 320, 68) * np.exp(-ts * 40.0)
    out = _mix_at(out, _saturate(snap, 2.6), 0.0, 0.9)

    # Aggressive dual-tone scary target lock siren (2 urgent stabs!)
    for bi, (t0, f0, f1) in enumerate(((0.06, 760.0, 1420.0), (0.30, 1480.0, 620.0))):
        tk = _t(0.28)
        fm = np.sin(2.0 * np.pi * 46.0 * tk) * 90.0
        u = np.clip(tk / tk[-1], 0.0, 1.0)
        freq = f0 + (f1 - f0) * u + fm
        ph = 2.0 * np.pi * np.cumsum(freq) / SR
        screech = np.sign(np.sin(ph)) * 0.55 + np.sin(ph * 0.5) * 0.55 + np.sin(ph * 1.49) * 0.30
        growl = np.sin(2.0 * np.pi * 68.0 * tk) * 0.55
        env = np.sin(np.pi * np.clip(tk / 0.025, 0.0, 1.0)) * np.exp(-tk * 7.5)
        sig = _saturate((screech + growl) * env, 2.7)
        out = _mix_at(out, sig, t0, 0.95)

    return _fade(out, 0.002, 0.05)


def synth_fire_heavy() -> np.ndarray:
    rng = np.random.default_rng(303)
    t = _t(0.38)
    # Huge sub-bass cannon punch + industrial bolt slam
    sub = _sweep_sine(t, 175.0, 34.0) * np.exp(-t * 16.0) * 1.25
    bolt = _bp(rng.standard_normal(len(t)), 280, 4200) * np.exp(-t * 36.0) * 0.95
    # Digital shredder crunch + spinning aerodynamic floppy whoosh
    crunch = _bitcrush(np.sin(2.0 * np.pi * 240.0 * t + 3.2 * np.sin(2.0 * np.pi * 58.0 * t)), 10, 3) * np.exp(-t * 22.0) * 0.65
    whiz = _bp(rng.standard_normal(len(t)), 1400, 6500) * np.exp(-np.maximum(0.0, t - 0.03) * 14.0) * (0.6 + 0.4 * np.sin(2.0 * np.pi * 42.0 * t)) * 0.55
    sig = _saturate(sub + bolt + crunch + whiz, 2.6)
    return _fade(sig, 0.001, 0.04)


def synth_fire_msdos_mg() -> np.ndarray:
    rng = np.random.default_rng(404)
    t = _t(0.24)
    # Ultra-punchy rapid machine-gun bark + PC speaker harsh square snap + floppy zip
    sub = _sweep_sine(t, 240.0, 46.0) * np.exp(-t * 24.0) * 1.15
    crack = _bp(rng.standard_normal(len(t)), 550, 6200) * np.exp(-t * 44.0) * 1.05
    dos_bark = np.sign(np.sin(2.0 * np.pi * _sweep_sine(t, 640, 180) * 0.0 + np.cumsum(2.0 * np.pi * np.linspace(640.0, 170.0, len(t)) / SR)))
    dos_bark *= np.exp(-t * 26.0) * 0.45
    zip_tail = _bp(rng.standard_normal(len(t)), 1900, 7400) * np.exp(-t * 19.0) * 0.50
    sig = _saturate(_bitcrush(sub + crack + dos_bark + zip_tail, 16, 2), 2.8)
    return _fade(sig, 0.001, 0.03)


def synth_explode_mega() -> np.ndarray:
    rng = np.random.default_rng(505)
    out = np.zeros(int(2.85 * SR), dtype=np.float32)

    # 1. Pre-blast 80ms CRT capacitor overload screech
    tp = _t(0.09)
    overload = _sweep_sine(tp, 420.0, 2600.0) * np.exp(-tp * 8.0) * 0.65
    out = _mix_at(out, _saturate(overload, 2.2), 0.0, 0.85)

    # 2. Tectonic Boom + Sub-Bass Shockwave (0.07s)
    tb = _t(2.20)
    sub = _sweep_sine(tb, 130.0, 26.0) * np.exp(-tb * 2.8) * 1.45
    rumble = _lp1(rng.standard_normal(len(tb)), 240.0) * np.exp(-tb * 2.4) * 1.35
    mid_blast = _bp(rng.standard_normal(len(tb)), 220.0, 1800.0) * np.exp(-tb * 4.6) * 1.10
    boom = _saturate(sub + rumble + mid_blast, 2.7)
    out = _mix_at(out, boom, 0.07, 1.0)

    # 3. CRT Picture-Tube Implosion & Glass Shatter (0.08s .. 0.65s)
    tg = _t(0.65)
    shatter = _bp(rng.standard_normal(len(tg)), 2200.0, 8800.0) * np.exp(-tg * 12.0)
    # Add razor-sharp glass tinkle spikes
    for gi in range(14):
        gt = 0.09 + gi * 0.032 + float(rng.uniform(-0.01, 0.01))
        t_sh = _t(0.08)
        f_g = float(rng.uniform(2600.0, 7400.0))
        ping = np.sin(2.0 * np.pi * f_g * t_sh) * np.exp(-t_sh * 65.0) * 0.35
        out = _mix_at(out, ping, gt, 0.65)
    out = _mix_at(out, shatter, 0.08, 0.85)

    # 4. Violent electrical arc snaps (0.14s .. 1.05s)
    for ai in range(6):
        ta = _t(0.11)
        zap = _bp(rng.standard_normal(len(ta)), 1200, 7000) * np.sign(np.sin(2.0 * np.pi * 95.0 * ta)) * np.exp(-ta * 28.0)
        out = _mix_at(out, _saturate(zap, 3.0), 0.14 + ai * 0.15 + float(rng.uniform(0, 0.05)), 0.72)

    # 5. Massive Floppy Disk Scatter & Bounce Clatter Rain (0.45s .. 2.75s)!
    clatter_base = synth_floppy_clatter(seed=77)
    for fi in range(32):
        # Dense at 0.45..1.35s, tapering out to 2.70s
        u = fi / 31.0
        t_hit = 0.42 + (u ** 1.25) * 2.25 + float(rng.uniform(-0.04, 0.04))
        gain = (1.0 - 0.68 * u) * float(rng.uniform(0.32, 0.68))
        # Slight pitch-shift via resampling
        rate = float(rng.uniform(0.82, 1.28))
        n_new = max(16, int(len(clatter_base) / rate))
        resamp = np.interp(np.linspace(0, len(clatter_base) - 1, n_new), np.arange(len(clatter_base)), clatter_base).astype(np.float32)
        out = _mix_at(out, resamp, max(0.35, t_hit), gain)

    return _fade(out, 0.002, 0.09)


def build_all_sounds() -> Dict:
    os.makedirs(OUT_DIR, exist_ok=True)
    specs = [
        ("activate", "activate_deploy.wav", "Throw-to-Sentry Transform (CRT Degauss + Hydraulic Slams + BIOS Roar)", synth_activate_deploy()),
        ("spot", "spot_klaxon.wav", "Aggressive Target Lock Klaxon (Radar Screech + Sub Growl)", synth_spot_klaxon()),
        ("fire_heavy", "fire_heavy.wav", "Heavy Floppy Cannon Blast (Sub-Thump + Bolt Slam + Disc Whiz)", synth_fire_heavy()),
        ("fire_msdos", "fire_msdos_mg.wav", "MS-DOS Machine Gun Floppy Shredder (High-RPM Industrial Bark)", synth_fire_msdos_mg()),
        ("explode", "explode_mega.wav", "Mega Destruction & Floppy Rain (Tectonic Boom + CRT Shatter + 32 Clatters)", synth_explode_mega()),
        ("clatter", "floppy_clatter.wav", "3D Floppy Floor Bounce Clack (Dynamic Scatter Impact)", synth_floppy_clatter()),
    ]
    manifest = {"sample_rate": SR, "sounds": {}}
    print("[disc_sentry] Synthesizing scary/aggressive sentry sound effects...")
    for key, fname, desc, audio in specs:
        p = os.path.join(OUT_DIR, fname)
        info = _write_wav(p, audio)
        info["desc"] = desc
        manifest["sounds"][key] = info
        print(f"  [OK] {fname:20s} | {info['dur']:.2f}s | RMS {info['rms_db']} dBFS")

    with open(os.path.join(OUT_DIR, "sounds_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


if __name__ == "__main__":
    build_all_sounds()
