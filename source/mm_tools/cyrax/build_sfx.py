"""Build authentic Mortal Kombat 3 Cyrax robotic + Bonk SFX for BakersfieldQuake.

Generates 7 deterministic, reproducible, mono 22050 Hz 16-bit PCM WAV files in
source/mm_tools/cyrax/assets/sfx/:
  - charge.wav      (~1.80s) robotic servo/plasma charge ramp
  - fire.wav        (~0.56s) MK3 Cyrax net launch + punchy robotic blast
  - vent.wav        (~0.50s) pressurized steam/plasma vent hiss
  - capture.wav     (~0.55s) MK3 Cyrax net wrap/capture hit + electro-lock pulse
  - pull.wav        (~0.80s) rhythmic robotic tether/winch hum pulse
  - hold_beep.wav   (~0.25s) crisp MK3 cyborg HUD/lock confirmation beep
  - bonk_launch.wav (~0.62s) heavy robotic servo + Bonk frying-pan megasmack

Uses only Python stdlib + NumPy (works under `python -I` in CI). Embeds the
cleaned, denoised 22050 Hz MK3 Cyrax net audio stem extracted from the user's
MK3 Cyrax gameplay reference video, layered with deterministic pure-NumPy DSP.

Usage:
    python -I source/mm_tools/cyrax/build_sfx.py [--verify]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import tempfile
import wave
import zlib

import numpy as np

SR = 22050
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT_DIR = os.path.join(HERE, "assets", "sfx")

# Cleaned 22050 Hz mono int16 PCM stem of MK3 Cyrax's chest net launch & capture
# (extracted by multi-shot STFT spectral-masking across 4 aligned net fires in
# the MK3 Cyrax gameplay reference, high-pass cleaned >450 Hz to strip stage
# music while preserving the iconic 1.9-7.6 kHz metallic electro-mesh snaps).
MK3_NET_STEM_ZLIB_B64 = (
    "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"
)


def decode_mk3_stem() -> np.ndarray:
    """Decode embedded cleaned 22050 Hz MK3 Cyrax net audio stem to float64 [-1, 1]."""
    raw = zlib.decompress(base64.b64decode(MK3_NET_STEM_ZLIB_B64))
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0


# ---------------------------------------------------------------------------
# Pure-NumPy DSP primitives
# ---------------------------------------------------------------------------

def make_time(dur_s: float, sr: int = SR) -> np.ndarray:
    n = int(round(dur_s * sr))
    return np.arange(n, dtype=np.float64) / float(sr)


def remove_dc(x: np.ndarray) -> np.ndarray:
    return x - float(np.mean(x))


def apply_edge_fades(x: np.ndarray, fade_in_s: float = 0.004, fade_out_s: float = 0.015, sr: int = SR) -> np.ndarray:
    out = x.copy()
    fi = min(int(round(fade_in_s * sr)), len(out) // 4)
    fo = min(int(round(fade_out_s * sr)), len(out) // 4)
    if fi > 0:
        out[:fi] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(fi) / fi))
    if fo > 0:
        out[-fo:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(fo) / fo))
    return out


def fft_bandpass(x: np.ndarray, f_lo: float, f_hi: float, sr: int = SR, rolloff_hz: float = 180.0) -> np.ndarray:
    """Smooth cosine-tapered FFT bandpass filter."""
    n = len(x)
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    spec = np.fft.rfft(x)
    mask = np.ones_like(freqs)
    if f_lo > 0.0:
        lo0 = max(0.0, f_lo - rolloff_hz)
        lo_zone = (freqs >= lo0) & (freqs < f_lo)
        mask[freqs < lo0] = 0.0
        if f_lo > lo0:
            mask[lo_zone] = 0.5 * (1.0 - np.cos(np.pi * (freqs[lo_zone] - lo0) / (f_lo - lo0)))
    if f_hi < sr * 0.49:
        hi1 = min(sr * 0.5, f_hi + rolloff_hz)
        hi_zone = (freqs > f_hi) & (freqs <= hi1)
        mask[freqs > hi1] = 0.0
        if hi1 > f_hi:
            mask[hi_zone] = 0.5 * (1.0 + np.cos(np.pi * (freqs[hi_zone] - f_hi) / (hi1 - f_hi)))
    return np.fft.irfft(spec * mask, n=n)


def swept_bandpass_noise(rng: np.random.Generator, n: int, f_start, f_end, bw_hz, sr: int = SR) -> np.ndarray:
    """STFT overlap-add resonant filtered noise along a frequency curve."""
    noise = rng.standard_normal(n)
    nfft = 512
    hop = 128
    win = np.hanning(nfft)
    freqs = np.fft.rfftfreq(nfft, 1.0 / sr)
    padded = np.pad(noise, (nfft, nfft))
    out = np.zeros(len(padded), dtype=np.float64)
    norm = np.zeros(len(padded), dtype=np.float64)
    w2 = win ** 2

    num_frames = (len(padded) - nfft) // hop + 1
    f_curve = f_start if callable(f_start) else None
    for i in range(num_frames):
        pos = i * hop
        t_mid = (pos + nfft * 0.5 - nfft) / sr
        frac = float(np.clip(t_mid / max(n / sr, 1e-6), 0.0, 1.0))
        fc = float(f_curve(frac)) if f_curve is not None else float(f_start + (f_end - f_start) * frac)
        bw = float(bw_hz(frac)) if callable(bw_hz) else float(bw_hz)
        resp = np.exp(-0.5 * ((freqs - fc) / max(bw * 0.5, 35.0)) ** 2)
        resp[0] = 0.0
        frame = padded[pos:pos + nfft] * win
        filt = np.fft.irfft(np.fft.rfft(frame) * resp, n=nfft) * win
        out[pos:pos + nfft] += filt
        norm[pos:pos + nfft] += w2

    res = (out / np.maximum(norm, 1e-8))[nfft:nfft + n]
    mx = float(np.max(np.abs(res)))
    return res / mx if mx > 1e-8 else res


def resample_pitch(x: np.ndarray, factor: float) -> np.ndarray:
    """Linearly resample x by 1/factor so playback at SR shifts pitch by `factor`."""
    if len(x) < 4 or abs(factor - 1.0) < 1e-4:
        return x.copy()
    out_len = max(4, int(round(len(x) / factor)))
    t_in = np.linspace(0.0, 1.0, len(x), dtype=np.float64)
    t_out = np.linspace(0.0, 1.0, out_len, dtype=np.float64)
    return np.interp(t_out, t_in, x)


def sweep_sine(t: np.ndarray, f0: float, f1: float, exp_curve: bool = True) -> np.ndarray:
    u = np.clip(t / max(float(t[-1]), 1e-6), 0.0, 1.0)
    if exp_curve and f0 > 0.0 and f1 > 0.0:
        freq = f0 * ((f1 / f0) ** u)
    else:
        freq = f0 + (f1 - f0) * u
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    return np.sin(phase)


def pitch_drop_thump(t: np.ndarray, t0: float, f_hi: float, f_lo: float, tau_pitch: float, tau_amp: float) -> np.ndarray:
    y = np.zeros_like(t)
    mask = t >= t0
    if not np.any(mask):
        return y
    dt = t[mask] - t0
    phase = 2.0 * np.pi * (f_lo * dt + (f_hi - f_lo) * tau_pitch * (1.0 - np.exp(-dt / tau_pitch)))
    att = 1.0 - np.exp(-dt / 0.0005)
    y[mask] = att * np.exp(-dt / tau_amp) * np.sin(phase)
    return y


def modal_bank(t: np.ndarray, t0: float, modes, rng: np.random.Generator | None = None, phase_jitter: float = 0.25) -> np.ndarray:
    y = np.zeros_like(t)
    mask = t >= t0
    if not np.any(mask):
        return y
    dt = t[mask] - t0
    for f, amp, tau in modes:
        if f >= SR * 0.48 or f <= 15.0:
            continue
        ph = float(rng.uniform(0.0, phase_jitter * np.pi)) if rng is not None else 0.0
        att = 1.0 - np.exp(-dt / 0.0005)
        y[mask] += amp * att * np.exp(-dt / tau) * np.sin(2.0 * np.pi * f * dt + ph)
    return y


def add_at(dst: np.ndarray, src: np.ndarray, t_sec: float, gain: float = 1.0) -> None:
    start = int(round(t_sec * SR))
    if start >= len(dst):
        return
    if start < 0:
        src = src[-start:]
        start = 0
    end = min(len(dst), start + len(src))
    dst[start:end] += gain * src[:end - start]


def trim_noise_floor(x: np.ndarray, thresh_ratio: float = 0.0018, pad_s: float = 0.004) -> np.ndarray:
    pk = float(np.max(np.abs(x))) if len(x) else 0.0
    if pk < 1e-9:
        return x
    idx = np.where(np.abs(x) > thresh_ratio * pk)[0]
    if len(idx) < 16:
        return x
    pad = int(round(pad_s * SR))
    lo = max(0, int(idx[0]) - pad)
    hi = min(len(x), int(idx[-1]) + pad)
    return x[lo:hi]


def finalize_sfx(
    x: np.ndarray,
    target_rms_db: float = -13.5,
    max_peak: float = 0.88,
    drive: float = 1.25,
    fade_in_s: float = 0.003,
    fade_out_s: float = 0.014,
    trim_floor: bool = True,
) -> np.ndarray:
    """DC-strip, noise-floor trim, edge-fade, soft-limit, and normalize with zero clipping."""
    y = fft_bandpass(remove_dc(x), 30.0, SR * 0.48, rolloff_hz=20.0)
    if trim_floor:
        y = trim_noise_floor(y)
    y = apply_edge_fades(y, fade_in_s=fade_in_s, fade_out_s=fade_out_s)
    pk = float(np.max(np.abs(y)))
    if pk < 1e-9:
        return y
    y = y / pk

    if drive > 1.0:
        y = np.tanh(y * drive) / np.tanh(drive)

    target_rms = 10.0 ** (target_rms_db / 20.0)
    for _ in range(4):
        rms = float(np.sqrt(np.mean(y ** 2)))
        if rms < 1e-9:
            break
        y = y * (target_rms / rms)
        cur_pk = float(np.max(np.abs(y)))
        if cur_pk <= max_peak:
            break
        knee = 0.74 * max_peak
        over = np.abs(y) > knee
        if np.any(over):
            sign = np.sign(y[over])
            excess = np.abs(y[over]) - knee
            headroom = max_peak - knee
            y[over] = sign * (knee + headroom * np.tanh(excess / headroom))

    y = apply_edge_fades(y, fade_in_s=fade_in_s, fade_out_s=fade_out_s)
    y = remove_dc(y)
    if len(y) >= 6:
        y[:3] *= np.array([0.0, 0.35, 0.75])
        y[-3:] *= np.array([0.75, 0.35, 0.0])
    cur_pk = float(np.max(np.abs(y)))
    if cur_pk > max_peak:
        y = y * (max_peak / cur_pk)
    return y


# ---------------------------------------------------------------------------
# Sound builders (7 Cyrax Net + Bonk SFX)
# ---------------------------------------------------------------------------

def build_charge(stem: np.ndarray) -> np.ndarray:
    """~1.80s robotic servo/plasma charge ramp rising in pitch & intensity."""
    rng = np.random.default_rng(199501)
    dur = 1.80
    t = make_time(dur)
    u = t / dur
    y = np.zeros_like(t)

    # 1. Chest hatch mechanical unlock clack + pneumatic micro-puff at t=0.00s
    y += 0.65 * pitch_drop_thump(t, 0.0, 380.0, 85.0, 0.014, 0.040)
    latch_slice = apply_edge_fades(stem[:int(0.032 * SR)], 0.001, 0.008)
    add_at(y, resample_pitch(latch_slice, 0.85), 0.006, 0.55)

    # 2. Rising twin-oscillator Lin-Kuei servo turbine (115 Hz -> 680 Hz)
    f_curve = 115.0 * ((680.0 / 115.0) ** (u ** 1.15))
    ph1 = 2.0 * np.pi * np.cumsum(f_curve) / SR
    ph2 = 2.0 * np.pi * np.cumsum(f_curve * 2.01) / SR
    ph_sub = 2.0 * np.pi * np.cumsum(f_curve * 0.5) / SR
    # Mechanical gear flutter (accelerating 18 Hz -> 48 Hz)
    am_freq = 18.0 + 30.0 * u
    am = 0.76 + 0.24 * np.sin(2.0 * np.pi * np.cumsum(am_freq) / SR)
    ramp_env = np.clip(u / 0.06, 0.0, 1.0) * (0.22 + 0.78 * (u ** 1.35))
    servo = (0.50 * np.sin(ph1) + 0.30 * np.sin(ph2) + 0.28 * np.sin(ph_sub)) * am * ramp_env
    # Subtle 90s Midway grit
    servo = np.tanh(servo * 1.45) * 0.72
    y += servo

    # 3. Swept plasma core air/energy whine (520 Hz -> 3900 Hz)
    plasma = swept_bandpass_noise(
        rng, len(t),
        lambda frac: 520.0 * ((3900.0 / 520.0) ** (frac ** 1.2)),
        None,
        lambda frac: 220.0 + 520.0 * frac,
    )
    y += plasma * (0.08 + 0.42 * (u ** 1.6)) * np.clip(u / 0.08, 0.0, 1.0)

    # 4. Accelerating MK3 cyborg capacitor clicks from the real MK3 net stem
    tick_src = apply_edge_fades(stem[int(0.042 * SR):int(0.068 * SR)], 0.001, 0.006)
    tt = 0.14
    step_idx = 0
    while tt < 1.66:
        prog = tt / 1.66
        pitch = 0.80 + 0.72 * prog
        gain = 0.22 + 0.36 * prog
        add_at(y, resample_pitch(tick_src, pitch), tt, gain)
        dt_step = 0.145 * (1.0 - 0.62 * (prog ** 0.85))
        tt += max(0.048, dt_step)
        step_idx += 1

    # 5. Full-charge peak lock swell + crisp harmonic ready chime at 1.64s..1.79s
    y += 0.48 * modal_bank(
        t, 1.64,
        [(1320.0, 0.55, 0.11), (1980.0, 0.48, 0.10), (2640.0, 0.32, 0.08)],
        rng=rng,
    )
    # Gentle tail rolloff on the last 45ms
    y *= np.where(t > 1.74, np.clip((dur - t) / 0.06, 0.0, 1.0), 1.0)

    return finalize_sfx(y, target_rms_db=-13.5, max_peak=0.86, drive=1.22, fade_in_s=0.004, fade_out_s=0.030, trim_floor=False)


def build_fire(stem: np.ndarray) -> np.ndarray:
    """~0.56s authentic MK3 Cyrax net launch + punchy low-end robotic blast."""
    rng = np.random.default_rng(199502)
    dur = 0.56
    t = make_time(dur)
    y = np.zeros_like(t)

    # 1. Punchy low-end robotic chest-cannon blast at t=0.00s
    y += 0.85 * pitch_drop_thump(t, 0.0, 225.0, 44.0, 0.020, 0.105)
    y += 0.55 * pitch_drop_thump(t, 0.0, 460.0, 95.0, 0.011, 0.050)
    punch_noise = fft_bandpass(rng.standard_normal(len(t)), 160.0, 1500.0) * np.exp(-t / 0.032)
    y += 0.38 * punch_noise

    # 2. Real MK3 Cyrax net launch stem layered prominently at t=0.004s
    #    plus slightly pitched-up energy harmonic layer for thick arcade presence
    stem_clean = apply_edge_fades(stem, 0.002, 0.008)
    add_at(y, stem_clean, 0.004, 1.45)
    add_at(y, resample_pitch(stem_clean[:int(0.085 * SR)], 1.12), 0.014, 0.55)

    # 3. Energy-net launch plasma whoosh (2900 Hz -> 580 Hz)
    whoosh = swept_bandpass_noise(
        rng, len(t),
        lambda frac: 2900.0 * ((580.0 / 2900.0) ** (frac ** 0.7)),
        None,
        lambda frac: 550.0 - 250.0 * frac,
    )
    y += whoosh * np.exp(-t / 0.16) * np.clip(t / 0.008, 0.0, 1.0) * 0.58

    # 4. Modulated glowing green mesh flight tail (0.06s..0.52s)
    tail_mask = t >= 0.05
    dt = np.maximum(0.0, t - 0.05)
    buzz = 0.72 + 0.28 * np.sin(2.0 * np.pi * 32.0 * dt)
    mesh_hum = (
        0.48 * np.sin(2.0 * np.pi * 460.0 * dt)
        + 0.32 * np.sin(2.0 * np.pi * 920.0 * dt)
        + 0.22 * np.sin(2.0 * np.pi * 1380.0 * dt)
    ) * buzz * np.exp(-dt / 0.13) * np.clip(dt / 0.015, 0.0, 1.0)
    y[tail_mask] += 0.34 * mesh_hum[tail_mask]

    return finalize_sfx(y, target_rms_db=-11.5, max_peak=0.88, drive=1.35, fade_in_s=0.002, fade_out_s=0.028)


def build_vent(stem: np.ndarray) -> np.ndarray:
    """~0.50s robotic steam/plasma vent hiss for abort & post-shot cooling."""
    rng = np.random.default_rng(199503)
    dur = 0.50
    t = make_time(dur)
    y = np.zeros_like(t)

    # 1. Solenoid valve release pop + tiny metallic latch tick
    y += 0.55 * pitch_drop_thump(t, 0.0, 460.0, 115.0, 0.009, 0.032)
    valve_tick = apply_edge_fades(stem[:int(0.025 * SR)], 0.001, 0.006)
    add_at(y, resample_pitch(valve_tick, 1.18), 0.002, 0.38)

    # 2. Dual-band pressurized steam/plasma vent hiss
    hi_steam = swept_bandpass_noise(
        rng, len(t),
        lambda frac: 4900.0 * ((1350.0 / 4900.0) ** (frac ** 0.85)),
        None,
        lambda frac: 1400.0 - 700.0 * frac,
    )
    mid_steam = swept_bandpass_noise(
        rng, len(t),
        lambda frac: 2200.0 * ((650.0 / 2200.0) ** (frac ** 0.9)),
        None,
        lambda frac: 850.0 - 350.0 * frac,
    )
    # Turbulent pressure flutter (24 Hz valve sputter)
    flutter = 0.82 + 0.18 * np.sin(2.0 * np.pi * 24.0 * t + 0.4 * np.sin(2.0 * np.pi * 9.0 * t))
    steam_env = np.clip(t / 0.012, 0.0, 1.0) * np.exp(-t / 0.165)
    y += (0.68 * hi_steam + 0.52 * mid_steam) * flutter * steam_env

    # 3. Descending reactor power-down turbine whine
    whine = sweep_sine(t, 540.0, 125.0, exp_curve=True) * np.exp(-t / 0.11) * np.clip(t / 0.006, 0.0, 1.0)
    y += 0.28 * whine

    return finalize_sfx(y, target_rms_db=-13.5, max_peak=0.86, drive=1.18, fade_in_s=0.002, fade_out_s=0.035)


def build_capture(stem: np.ndarray) -> np.ndarray:
    """~0.55s authentic MK3 Cyrax net wrap/capture hit + electro-lock pulse."""
    rng = np.random.default_rng(199504)
    dur = 0.55
    t = make_time(dur)
    y = np.zeros_like(t)

    # 1. Elastic net snare impact thump at t=0.00s
    y += 0.85 * pitch_drop_thump(t, 0.0, 265.0, 62.0, 0.018, 0.085)

    # 2. Real MK3 Cyrax net wrap/capture pulses (full stem + emphasized wrap cluster!)
    wrap_cluster = apply_edge_fades(stem[int(0.038 * SR):], 0.002, 0.008)
    add_at(y, wrap_cluster, 0.002, 1.25)
    add_at(y, apply_edge_fades(stem, 0.002, 0.008), 0.042, 0.85)
    add_at(y, resample_pitch(wrap_cluster, 0.92), 0.115, 0.55)

    # 3. Gritty neon-green electro-net binding crackle (0.04s..0.34s)
    spark = swept_bandpass_noise(
        rng, len(t),
        lambda frac: 3600.0 - 1600.0 * frac,
        None,
        900.0,
    )
    spark_gate = (0.5 + 0.5 * np.sin(2.0 * np.pi * 22.0 * t)) ** 1.5
    y += 0.42 * spark * spark_gate * np.exp(-t / 0.16)

    # 4. Electro-lock pulse chord (0.07s..0.52s) that pulses at 16 Hz then locks steady
    dt = np.maximum(0.0, t - 0.07)
    pulse_mod = 0.50 + 0.50 * np.sin(2.0 * np.pi * 16.0 * dt) * np.exp(-dt / 0.18)
    lock_tone = (
        0.38 * np.sin(2.0 * np.pi * 310.0 * dt)
        + 0.34 * np.sin(2.0 * np.pi * 620.0 * dt)
        + 0.28 * np.sin(2.0 * np.pi * 930.0 * dt)
        + 0.24 * np.sin(2.0 * np.pi * 1550.0 * dt)
    )
    lock_env = np.clip((t - 0.07) / 0.015, 0.0, 1.0) * np.exp(-dt / 0.17)
    y += np.where(t >= 0.07, 0.60 * np.tanh(lock_tone * 1.55) * pulse_mod * lock_env, 0.0)
    y += 0.32 * modal_bank(t, 0.15, [(1240.0, 0.6, 0.11), (1860.0, 0.45, 0.09)], rng=rng)

    return finalize_sfx(y, target_rms_db=-12.0, max_peak=0.88, drive=1.30, fade_in_s=0.002, fade_out_s=0.028)


def build_pull(stem: np.ndarray) -> np.ndarray:
    """~0.80s rhythmic robotic tether/winch hum pulse for reeling captured target."""
    rng = np.random.default_rng(199505)
    dur = 0.80
    t = make_time(dur)
    y = np.zeros_like(t)

    # 1. Continuous taut magnetic cable bed (132 Hz + 264 Hz + 528 Hz)
    growl = 0.78 + 0.22 * np.sin(2.0 * np.pi * 26.0 * t)
    cable = (
        0.52 * np.sin(2.0 * np.pi * 132.0 * t)
        + 0.34 * np.sin(2.0 * np.pi * 264.0 * t)
        + 0.20 * np.sin(2.0 * np.pi * 528.0 * t)
    ) * growl
    # 4-beat rhythmic winch pulse envelope (5 Hz cadence)
    beat_lfo = 0.42 + 0.58 * (0.5 - 0.5 * np.cos(2.0 * np.pi * 5.0 * t)) ** 1.3
    y += 0.68 * np.tanh(cable * 1.35) * beat_lfo

    # 2. Rhythmic hydraulic winch strokes + ratchet ticks at 0.00, 0.20, 0.40, 0.60s
    tick = apply_edge_fades(stem[int(0.044 * SR):int(0.068 * SR)], 0.001, 0.006)
    for idx, t_beat in enumerate((0.02, 0.22, 0.42, 0.62)):
        y += 0.45 * pitch_drop_thump(t, t_beat, 260.0 + idx * 12.0, 96.0, 0.015, 0.055)
        add_at(y, resample_pitch(tick, 0.88 + idx * 0.05), t_beat + 0.005, 0.42)
        # Rising winch tension chirp per stroke
        mask = (t >= t_beat) & (t < t_beat + 0.16)
        dt = np.zeros_like(t)
        dt[mask] = t[mask] - t_beat
        u_b = dt[mask] / 0.16
        f_b = 340.0 + 380.0 * u_b
        y[mask] += 0.24 * np.sin(2.0 * np.pi * np.cumsum(f_b) / SR) * np.sin(np.pi * u_b)

    # 3. Filtered magnetic tether air/hum texture
    hum_noise = swept_bandpass_noise(
        rng, len(t),
        lambda frac: 750.0 + 450.0 * np.sin(2.0 * np.pi * 2.5 * frac),
        None,
        360.0,
    )
    y += 0.25 * hum_noise * beat_lfo

    return finalize_sfx(y, target_rms_db=-13.5, max_peak=0.84, drive=1.20, fade_in_s=0.016, fade_out_s=0.032, trim_floor=False)


def build_hold_beep(stem: np.ndarray) -> np.ndarray:
    """~0.25s crisp MK3 cyborg HUD/lock confirmation beep."""
    rng = np.random.default_rng(199506)
    dur = 0.25
    t = make_time(dur)
    y = np.zeros_like(t)

    # Classic dual-tone Lin-Kuei HUD target-lock chirp: 1320 Hz -> 1980 Hz
    def tone_burst(t0: float, length: float, freq: float, gain: float) -> np.ndarray:
        mask = (t >= t0) & (t < t0 + length)
        out = np.zeros_like(t)
        dt = t[mask] - t0
        env = np.clip(dt / 0.003, 0.0, 1.0) * np.clip((length - dt) / 0.008, 0.0, 1.0)
        sig = (
            0.70 * np.sin(2.0 * np.pi * freq * dt)
            + 0.22 * np.sin(2.0 * np.pi * freq * 2.0 * dt)
            + 0.12 * np.sin(2.0 * np.pi * freq * 3.0 * dt)
        )
        out[mask] = gain * np.tanh(sig * 1.25) * env
        return out

    y += tone_burst(0.004, 0.064, 1320.0, 0.82)
    y += tone_burst(0.076, 0.158, 1980.0, 0.92)

    # Micro-relay click at both tone onsets using tiny MK3 transient
    relay = apply_edge_fades(stem[:int(0.012 * SR)], 0.001, 0.004)
    add_at(y, resample_pitch(relay, 1.45), 0.004, 0.28)
    add_at(y, resample_pitch(relay, 1.65), 0.076, 0.28)

    # Subtle high-tech shimmer tail
    y += 0.12 * modal_bank(t, 0.076, [(2970.0, 0.5, 0.08), (3960.0, 0.3, 0.06)], rng=rng)

    return finalize_sfx(y, target_rms_db=-12.5, max_peak=0.86, drive=1.15, fade_in_s=0.002, fade_out_s=0.014, trim_floor=False)


def build_bonk_launch(stem: np.ndarray) -> np.ndarray:
    """~0.62s heavy robotic servo + massive Bonk frying-pan megasmack launch impact."""
    rng = np.random.default_rng(199507)
    dur = 0.62
    t = make_time(dur)
    y = np.zeros_like(t)

    # 1. Rapid heavy hydraulic actuator wind-up slam (0.00s..0.105s)
    m_servo = t < 0.115
    u_s = np.clip(t[m_servo] / 0.105, 0.0, 1.0)
    f_s = 165.0 * ((960.0 / 165.0) ** (u_s ** 1.3))
    y[m_servo] += 0.72 * np.sin(2.0 * np.pi * np.cumsum(f_s) / SR) * np.clip(u_s / 0.1, 0.0, 1.0)
    y += 0.55 * pitch_drop_thump(t, 0.0, 340.0, 88.0, 0.012, 0.038)
    add_at(y, apply_edge_fades(stem[:int(0.035 * SR)], 0.001, 0.008), 0.008, 0.60)

    # 2. MASSIVE BONK FRYING-PAN MEGASMACK at t_hit = 0.098s!
    t_hit = 0.098
    # 2a. Deep kinetic launch boom (feels like 1800 u/s blastoff!)
    y += 1.35 * pitch_drop_thump(t, t_hit, 255.0, 36.0, 0.025, 0.155)
    y += 0.90 * pitch_drop_thump(t, t_hit, 610.0, 115.0, 0.012, 0.055)

    # 2b. Sharp metallic frying-pan strike crack
    dt_hit = np.maximum(0.0, t - t_hit)
    crack_mask = t >= t_hit
    crack = fft_bandpass(rng.standard_normal(len(t)), 700.0, 7800.0) * np.exp(-dt_hit / 0.015)
    y[crack_mask] += 1.15 * crack[crack_mask]

    # 2c. Cast-iron frying pan modal clang bank (signature inharmonic metallic BONK!)
    pan_modes = [
        (468.0,  1.05, 0.36),
        (764.0,  0.96, 0.32),
        (1148.0, 0.82, 0.27),
        (1532.0, 0.72, 0.22),
        (2065.0, 0.54, 0.17),
        (2710.0, 0.42, 0.13),
        (3540.0, 0.28, 0.09),
    ]
    pan_ring = modal_bank(t, t_hit, pan_modes, rng=rng, phase_jitter=0.18)
    y += 1.15 * np.tanh(pan_ring * 1.50)

    # 2d. Real MK3 metallic snap layer right on impact transient
    add_at(y, apply_edge_fades(stem[:int(0.075 * SR)], 0.001, 0.012), t_hit, 0.55)

    # 3. High-velocity wind-whip whoosh as target rockets away at 1800 u/s
    whip = swept_bandpass_noise(
        rng, len(t),
        lambda frac: 900.0 + 2400.0 * np.sin(np.pi * np.clip((frac - 0.16) / 0.65, 0.0, 1.0)),
        None,
        650.0,
    )
    whip_env = np.where(t >= t_hit + 0.015, np.exp(-(t - t_hit - 0.015) / 0.13), 0.0)
    y += 0.45 * whip * whip_env

    return finalize_sfx(y, target_rms_db=-10.8, max_peak=0.89, drive=1.42, fade_in_s=0.002, fade_out_s=0.032)


# ---------------------------------------------------------------------------
# Output & verification
# ---------------------------------------------------------------------------

BUILDERS = [
    ("charge.wav",      build_charge),
    ("fire.wav",        build_fire),
    ("vent.wav",        build_vent),
    ("capture.wav",     build_capture),
    ("pull.wav",        build_pull),
    ("hold_beep.wav",   build_hold_beep),
    ("bonk_launch.wav", build_bonk_launch),
]


def write_wav(path: str, x: np.ndarray, sr: int = SR) -> tuple[int, str]:
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype("<i2")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    return os.path.getsize(path), digest


def inspect_wav(path: str) -> dict:
    with wave.open(path, "rb") as wf:
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        nf = wf.getnframes()
        raw = wf.readframes(nf)
    arr = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    rms = float(np.sqrt(np.mean(arr ** 2))) if len(arr) else 0.0
    pk = float(np.max(np.abs(arr))) if len(arr) else 0.0
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    return {
        "channels": nch,
        "sampwidth": sw,
        "framerate": sr,
        "frames": nf,
        "dur_s": round(nf / sr, 4),
        "rms_db": round(20.0 * np.log10(max(rms, 1e-12)), 2),
        "peak": round(pk, 4),
        "sha256": digest,
    }


def generate_all(out_dir: str) -> dict[str, dict]:
    stem = decode_mk3_stem()
    results = {}
    for fname, fn in BUILDERS:
        audio = fn(stem)
        out_path = os.path.join(out_dir, fname)
        size, _ = write_wav(out_path, audio)
        info = inspect_wav(out_path)
        info["size"] = size
        results[fname] = info
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="Output directory for WAVs")
    ap.add_argument("--verify", action="store_true", help="Verify format, non-clipping, and determinism")
    args = ap.parse_args()

    res1 = generate_all(args.out_dir)
    for fname, info in res1.items():
        print(
            f"{fname:16s} dur={info['dur_s']:6.3f}s  "
            f"rms={info['rms_db']:6.2f} dB  pk={info['peak']:.4f}  "
            f"bytes={info['size']:6d}  sha256={info['sha256'][:16]}..."
        )

    if args.verify:
        with tempfile.TemporaryDirectory() as tmp:
            res2 = generate_all(tmp)
            for fname, info1 in res1.items():
                info2 = res2[fname]
                assert info1["channels"] == 1, f"{fname}: expected mono, got {info1['channels']}"
                assert info1["sampwidth"] == 2, f"{fname}: expected 16-bit PCM, got {info1['sampwidth']*8}-bit"
                assert info1["framerate"] == SR, f"{fname}: expected {SR} Hz, got {info1['framerate']}"
                assert info1["frames"] > 1000, f"{fname}: unexpectedly short ({info1['frames']} frames)"
                assert info1["rms_db"] > -24.0, f"{fname}: too quiet ({info1['rms_db']} dB)"
                assert info1["peak"] < 0.95, f"{fname}: near/at clipping ({info1['peak']})"
                assert info1["sha256"] == info2["sha256"], f"{fname}: non-deterministic output!"
        print("VERIFICATION PASSED: all 7 WAVs valid mono 22050Hz 16-bit PCM, zero clipping, deterministic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
