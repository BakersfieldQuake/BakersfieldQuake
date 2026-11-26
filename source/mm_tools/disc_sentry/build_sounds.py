"""Synthesize over-the-top, scary, aggressive sound effects for the Disc Sentry Gun.

Outputs 22050 Hz, 16-bit mono PCM WAVs to source/mm_tools/out/disc_sentry/sounds/:
  - dialup_deploy.wav    (AOL-style dial-up connect: dial tone, digits, answer tone, handshake, screech)
  - dart_throw.wav       (thrown-dart fwip)
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


def synth_dialup_deploy() -> np.ndarray:
    """AOL-style dial-up connect, squeezed into the 2.6 s netsend.qc waits before the klaxon:
    dial tone, touch-tone digits, answer tone, handshake warbles, then the carrier screech."""
    rng = np.random.default_rng(101)
    out = np.zeros(int(2.55 * SR), dtype=np.float32)

    def tone(dur: float, *freqs: float) -> np.ndarray:
        t = _t(dur)
        y = sum(np.sin(2.0 * np.pi * f * t) for f in freqs) / len(freqs)
        return _fade(y.astype(np.float32), 0.004, 0.006)

    # dial tone
    out = _mix_at(out, tone(0.28, 350.0, 440.0), 0.00, 0.75)

    # seven touch-tone digits
    dtmf = ((697, 1336), (770, 1209), (852, 1477), (697, 1209), (941, 1336), (770, 1477), (852, 1336))
    for i, (lo, hi) in enumerate(dtmf):
        out = _mix_at(out, tone(0.052, lo, hi), 0.31 + i * 0.072, 0.80)

    # the answering modem: 2100 Hz with its phase flipping
    ta = _t(0.34)
    flip = np.where((ta // 0.11) % 2 == 0, 1.0, -1.0)
    answer = (flip * np.sin(2.0 * np.pi * 2100.0 * ta)).astype(np.float32)
    out = _mix_at(out, _fade(answer, 0.006, 0.008), 0.84, 0.60)

    # handshake: the two "bong" chords, then a fast two-tone warble
    out = _mix_at(out, tone(0.13, 1375.0, 2002.0), 1.20, 0.80)
    out = _mix_at(out, tone(0.13, 1529.0, 2225.0), 1.34, 0.80)
    tw = _t(0.24)
    freq = np.where(np.sin(2.0 * np.pi * 34.0 * tw) > 0, 1180.0, 980.0) + 900.0 * (np.sin(2.0 * np.pi * 8.0 * tw) > 0.6)
    warble = np.sin(2.0 * np.pi * np.cumsum(freq) / SR).astype(np.float32)
    out = _mix_at(out, _fade(warble, 0.004, 0.008), 1.49, 0.70)

    # training screech: scrambled-data hiss over the carriers, in two surges
    ts = _t(0.80)
    hiss = _bp(rng.standard_normal(len(ts)), 900.0, 3200.0)
    hiss /= np.max(np.abs(hiss))
    carriers = np.sin(2.0 * np.pi * 1800.0 * ts) * 0.35 + np.sin(2.0 * np.pi * 2400.0 * ts) * 0.22
    swell = np.where(ts < 0.30, 0.65, 1.0) * (0.88 + 0.12 * np.sin(2.0 * np.pi * 21.0 * ts))
    screech = _saturate((hiss * 1.1 + carriers) * swell, 1.6)
    out = _mix_at(out, _fade(screech, 0.008, 0.07), 1.74, 0.78)

    # telephone-line bandwidth (a hard 300..3400 Hz limit; the first-order _bp is too gentle for this)
    spec = np.fft.rfft(out)
    f = np.fft.rfftfreq(len(out), 1.0 / SR)
    spec *= np.clip((f - 220.0) / 100.0, 0.0, 1.0) * np.clip((3700.0 - f) / 300.0, 0.0, 1.0)
    out = np.fft.irfft(spec, n=len(out))
    return _fade((out * (0.9 / np.max(np.abs(out)))).astype(np.float32), 0.003, 0.05)


def synth_dart_throw() -> np.ndarray:
    """A thrown dart: a tiny flick off the fingers, then a short airy "fwip" that rises and falls away."""
    rng = np.random.default_rng(606)
    t = _t(0.26)
    noise = rng.standard_normal(len(t)).astype(np.float32)
    # air rush: a narrow noise band whose pitch sweeps up fast, then drops as the dart leaves
    low = _bp(noise, 700.0, 1700.0)
    high = _bp(noise, 2200.0, 5200.0)
    blend = np.exp(-(((t - 0.075) / 0.045) ** 2))
    env = np.exp(-(((t - 0.080) / np.where(t < 0.080, 0.032, 0.058)) ** 2))
    rush = (low * (1.0 - blend) + high * blend * 1.3) * env
    rush /= np.max(np.abs(rush))
    tf = _t(0.018)
    flick = _bp(rng.standard_normal(len(tf)), 1800.0, 6000.0) * np.exp(-tf * 320.0)
    flick /= np.max(np.abs(flick))
    out = _mix_at(rush.astype(np.float32), flick, 0.0, 0.45)
    return _fade((out * (0.9 / np.max(np.abs(out)))).astype(np.float32), 0.001, 0.04)


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
    t = _t(0.16)
    # Snappy rapid-fire sub-punch + mechanical bolt slam + high-RPM floppy whiz
    sub = _sweep_sine(t, 210.0, 42.0) * np.exp(-t * 28.0) * 1.25
    bolt = _bp(rng.standard_normal(len(t)), 360, 4800) * np.exp(-t * 48.0) * 1.0
    crunch = _bitcrush(np.sin(2.0 * np.pi * 310.0 * t + 3.0 * np.sin(2.0 * np.pi * 72.0 * t)), 12, 2) * np.exp(-t * 30.0) * 0.6
    whiz = _bp(rng.standard_normal(len(t)), 1600, 6800) * np.exp(-np.maximum(0.0, t - 0.015) * 26.0) * (0.65 + 0.35 * np.sin(2.0 * np.pi * 55.0 * t)) * 0.55
    sig = _saturate(sub + bolt + crunch + whiz, 2.7)
    return _fade(sig, 0.001, 0.025)


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
        ("activate", "dialup_deploy.wav", "Sentry spawn (AOL-style dial-up connect)", synth_dialup_deploy()),
        ("throw", "dart_throw.wav", "Disk throw (thrown-dart fwip)", synth_dart_throw()),
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
