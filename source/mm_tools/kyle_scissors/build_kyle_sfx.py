"""Synthesize game-ready 22050 Hz 16-bit mono PCM WAV SFX for Kyle Tillet (Scissors).

Uses pure NumPy DSP (modal metallic synthesis, swept STFT noise shaping,
biquad filtering, transient modeling, and soft limiting) with deterministic seeds
for byte-identical reproducible output. Also indexes the cleaned Kyle voice clips
in scratch/kyle_clips/ into sfx/manifest.json for the showcase builder.
"""

import argparse
import importlib.util
import json
import os
import wave

import numpy as np

SR = 22050

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sfx")
DEFAULT_VOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "clips")


# ---------------------------------------------------------------------------
# Pure-NumPy DSP primitives
# ---------------------------------------------------------------------------

def make_time(dur_s, sr=SR):
    n = int(round(dur_s * sr))
    return np.arange(n, dtype=np.float64) / sr


def remove_dc(x):
    return x - float(np.mean(x))


def apply_edge_fades(x, fade_in_s=0.004, fade_out_s=0.012, sr=SR):
    out = x.copy()
    fi = min(int(round(fade_in_s * sr)), len(out) // 4)
    fo = min(int(round(fade_out_s * sr)), len(out) // 4)
    if fi > 0:
        out[:fi] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(fi) / fi))
    if fo > 0:
        out[-fo:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(fo) / fo))
    return out


def fft_bandpass(x, f_lo, f_hi, sr=SR, rolloff_hz=250.0):
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


def swept_bandpass_noise(rng, n, f_start, f_end, bw_hz, sr=SR):
    """STFT overlap-add noise swept cleanly from f_start(t) to f_end(t)."""
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
        frac = np.clip(t_mid / max(n / sr, 1e-6), 0.0, 1.0)
        fc = float(f_curve(frac)) if f_curve is not None else float(f_start + (f_end - f_start) * frac)
        bw = float(bw_hz(frac)) if callable(bw_hz) else float(bw_hz)
        # Gaussian-squared spectral bell for smooth resonant airflow/scrape
        resp = np.exp(-0.5 * ((freqs - fc) / max(bw * 0.5, 40.0)) ** 2)
        resp[0] = 0.0  # kill DC
        frame = padded[pos:pos + nfft] * win
        filt = np.fft.irfft(np.fft.rfft(frame) * resp, n=nfft) * win
        out[pos:pos + nfft] += filt
        norm[pos:pos + nfft] += w2

    res = (out / np.maximum(norm, 1e-8))[nfft:nfft + n]
    mx = np.max(np.abs(res))
    return res / mx if mx > 1e-8 else res


def modal_bank(t, t0, modes, rng=None, phase_jitter=0.4):
    """Sum damped sinusoidal partials starting at t0.

    modes: list of (freq_hz, amp, tau_s)
    """
    y = np.zeros_like(t)
    mask = t >= t0
    if not np.any(mask):
        return y
    dt = t[mask] - t0
    for f, amp, tau in modes:
        if f >= SR * 0.48 or f <= 10.0:
            continue
        ph = float(rng.uniform(0.0, phase_jitter * np.pi)) if rng is not None else 0.0
        # 0.8ms attack ramp prevents step-click at t0 while keeping crisp transient
        att = 1.0 - np.exp(-dt / 0.0006)
        y[mask] += amp * att * np.exp(-dt / tau) * np.sin(2.0 * np.pi * f * dt + ph)
    return y


def pitch_drop_thump(t, t0, f_hi, f_lo, tau_pitch, tau_amp):
    """Exponentially swept sine body impact (mechanical clack / handle thud)."""
    y = np.zeros_like(t)
    mask = t >= t0
    if not np.any(mask):
        return y
    dt = t[mask] - t0
    # Integral of f_lo + (f_hi - f_lo)*exp(-dt/tau_pitch)
    phase = 2.0 * np.pi * (
        f_lo * dt + (f_hi - f_lo) * tau_pitch * (1.0 - np.exp(-dt / tau_pitch))
    )
    att = 1.0 - np.exp(-dt / 0.0005)
    y[mask] = att * np.exp(-dt / tau_amp) * np.sin(phase)
    return y


def add_at(dst, src, start_sample):
    """Add src into dst starting at start_sample with bounds clipping."""
    if start_sample >= len(dst):
        return
    if start_sample < 0:
        src = src[-start_sample:]
        start_sample = 0
    end = min(len(dst), start_sample + len(src))
    dst[start_sample:end] += src[:end - start_sample]


def soft_limit_and_normalize(
    x, target_rms_db=-14.0, max_peak=0.86, drive=1.35, fade_in_s=0.003, fade_out_s=0.015
):
    """Remove DC, apply edge fades, gentle soft-clipping, and normalize to target RMS."""
    # High-pass sub-30 Hz DC/rumble before edge fades so zero-mean holds without shifting endpoints
    y = fft_bandpass(remove_dc(x), 35.0, SR * 0.48, rolloff_hz=25.0)
    y = apply_edge_fades(y, fade_in_s=fade_in_s, fade_out_s=fade_out_s)
    pk = float(np.max(np.abs(y)))
    if pk < 1e-9:
        return y
    y = y / pk

    # Gentle soft saturation (tanh) so transients don't force RMS too low
    if drive > 1.0:
        y = np.tanh(y * drive) / np.tanh(drive)

    # Iteratively level to target RMS; if peak exceeds max_peak, softly compress peaks
    target_rms = 10.0 ** (target_rms_db / 20.0)
    for _ in range(4):
        rms = float(np.sqrt(np.mean(y ** 2)))
        if rms < 1e-9:
            break
        gain = target_rms / rms
        y = y * gain
        cur_pk = float(np.max(np.abs(y)))
        if cur_pk <= max_peak:
            break
        knee = 0.72 * max_peak
        over = np.abs(y) > knee
        if np.any(over):
            sign = np.sign(y[over])
            excess = np.abs(y[over]) - knee
            headroom = max_peak - knee
            y[over] = sign * (knee + headroom * np.tanh(excess / headroom))

    # Re-apply edge fades and remove tiny residual DC (<1e-5) without shifting edges
    y = apply_edge_fades(y, fade_in_s=fade_in_s, fade_out_s=fade_out_s)
    y = remove_dc(y)
    # Taper just the outer 3 samples to 0 so exact endpoints are always 0
    y[:3] *= np.array([0.0, 0.35, 0.75])
    y[-3:] *= np.array([0.75, 0.35, 0.0])
    cur_pk = float(np.max(np.abs(y)))
    if cur_pk > max_peak:
        y = y * (max_peak / cur_pk)
    return y


def write_wav(path, x, sr=SR):
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype("<i2")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return os.path.getsize(path)


def audio_stats(x, sr=SR):
    rms = float(np.sqrt(np.mean(x ** 2)))
    pk = float(np.max(np.abs(x)))
    dc = float(np.mean(x))
    return {
        "duration": round(len(x) / sr, 4),
        "samples": len(x),
        "sample_rate": sr,
        "channels": 1,
        "bit_depth": 16,
        "rms_db": round(float(20.0 * np.log10(max(rms, 1e-12))), 2),
        "peak_linear": round(pk, 4),
        "peak_db": round(float(20.0 * np.log10(max(pk, 1e-12))), 2),
        "dc_offset": round(dc, 6),
    }


def waveform_peaks(seg, bars=48):
    if len(seg) < bars:
        return [0.0] * bars
    chunks = np.array_split(np.abs(seg), bars)
    vals = np.array([float(np.max(c)) for c in chunks])
    mx = max(float(np.max(vals)), 1e-6)
    return [round(v / mx, 3) for v in vals]


# ---------------------------------------------------------------------------
# Individual SFX synthesizers
# ---------------------------------------------------------------------------

def synth_snip_fast(rng):
    """~0.18s sharp metallic scissor SNIP! (blade slide + high-Q steel ring + crisp snap)."""
    t = make_time(0.18)
    n = len(t)

    # 1. Steel blade-on-blade friction slide (0.00s - 0.042s)
    slide = swept_bandpass_noise(rng, n, 2600.0, 6400.0, 1400.0)
    slide_env = np.exp(-((t - 0.018) / 0.013) ** 2) * (t < 0.046)
    slide *= slide_env * 0.48

    # 2. Crisp blade tip snap + mechanical handle clack at t=0.030s
    t_snap = 0.030
    snap_noise = fft_bandpass(rng.standard_normal(n), 1800.0, 9200.0)
    snap_env = np.where(t >= t_snap, np.exp(-(t - t_snap) / 0.0045), 0.0)
    snap = snap_noise * snap_env * 0.95
    thump = pitch_drop_thump(t, t_snap, 420.0, 115.0, 0.006, 0.016) * 0.55

    # 3. High-Q stainless-steel blade ring with subtle beating pairs
    steel_modes = [
        (2460.0, 0.42, 0.055),
        (2478.0, 0.30, 0.052),
        (3920.0, 0.36, 0.046),
        (5240.0, 0.28, 0.038),
        (6890.0, 0.22, 0.030),
        (8410.0, 0.16, 0.022),
        (9780.0, 0.10, 0.016),
    ]
    ring = modal_bank(t, t_snap, steel_modes, rng=rng)

    raw = slide + snap + thump + ring
    return soft_limit_and_normalize(
        raw, target_rms_db=-14.0, max_peak=0.86, drive=1.5, fade_in_s=0.003, fade_out_s=0.018
    )


def synth_snip_heavy(rng):
    """~0.32s heavy double-blade barber shear CHOP! for big hits & wing shred."""
    t = make_time(0.32)
    n = len(t)

    # 1. Heavy steel draw scrape (0.00s - 0.072s)
    draw = swept_bandpass_noise(rng, n, 1400.0, 4400.0, 1200.0)
    draw_env = np.exp(-((t - 0.032) / 0.022) ** 2) * (t < 0.078)
    draw *= draw_env * 0.52

    # 2. Double-stage shear slam: base pivot clank at 0.052s + heavy tip chop at 0.068s
    noise_hi = fft_bandpass(rng.standard_normal(n), 950.0, 8200.0)
    snap1 = noise_hi * np.where(t >= 0.052, np.exp(-(t - 0.052) / 0.0055), 0.0) * 0.65
    snap2 = noise_hi * np.where(t >= 0.068, np.exp(-(t - 0.068) / 0.0075), 0.0) * 1.05
    thump1 = pitch_drop_thump(t, 0.052, 260.0, 78.0, 0.010, 0.026) * 0.72
    thump2 = pitch_drop_thump(t, 0.068, 195.0, 58.0, 0.012, 0.038) * 0.85

    # 3. Heavy tailor-shear steel resonance
    shear_modes = [
        (680.0, 0.25, 0.048),
        (1340.0, 0.44, 0.095),
        (1354.0, 0.30, 0.090),
        (2210.0, 0.38, 0.082),
        (3190.0, 0.32, 0.068),
        (4520.0, 0.24, 0.052),
        (6110.0, 0.16, 0.036),
        (7740.0, 0.10, 0.024),
    ]
    ring = modal_bank(t, 0.066, shear_modes, rng=rng)

    raw = draw + snap1 + snap2 + thump1 + thump2 + ring
    return soft_limit_and_normalize(
        raw, target_rms_db=-13.8, max_peak=0.87, drive=1.55, fade_in_s=0.004, fade_out_s=0.028
    )


def synth_snip_latch_loop(rng):
    """~1.35s seamless looping frantic snip-snip-snip rhythm for latched Kyle."""
    dur = 1.35
    n_total = int(round(dur * SR))
    out = np.zeros(n_total, dtype=np.float64)

    # 9 frantic snips across 1.35s (every 150ms) with comedic syncopated accents
    # Pattern: BIG-small-MED-small-BIG-small-BIG-small-MED
    accents = [1.00, 0.68, 0.86, 0.64, 1.05, 0.70, 0.96, 0.66, 0.88]
    pitch_mults = [1.00, 1.12, 0.96, 1.16, 0.93, 1.10, 1.04, 1.15, 0.98]
    step = n_total // len(accents)
    snip_dur = 0.145
    t_s = make_time(snip_dur)
    n_s = len(t_s)

    for idx, (amp_sc, p_sc) in enumerate(zip(accents, pitch_mults)):
        # Slight human/manic micro-timing jitter (except first/last kept clear of boundary)
        jitter = int(rng.integers(-65, 65)) if 0 < idx < len(accents) - 1 else 0
        # Start 18ms in so sample 0 sits in the quiet inter-snip valley
        start = idx * step + int(0.018 * SR) + jitter

        # Mini blade open-scrape + crisp snip
        slide = swept_bandpass_noise(rng, n_s, 2300.0 * p_sc, 5800.0 * p_sc, 1300.0)
        slide *= np.exp(-((t_s - 0.012) / 0.009) ** 2) * (t_s < 0.032) * 0.36
        snap_n = fft_bandpass(rng.standard_normal(n_s), 1900.0, 9000.0)
        snap_n *= np.where(t_s >= 0.022, np.exp(-(t_s - 0.022) / 0.004), 0.0) * 0.85
        thump = pitch_drop_thump(t_s, 0.022, 380.0 * p_sc, 105.0, 0.005, 0.014) * 0.45
        modes = [
            (2420.0 * p_sc, 0.38, 0.034),
            (3840.0 * p_sc, 0.30, 0.028),
            (5180.0 * p_sc, 0.22, 0.022),
            (7120.0 * p_sc, 0.14, 0.016),
        ]
        ring = modal_bank(t_s, 0.022, modes, rng=rng)
        hit = (slide + snap_n + thump + ring) * amp_sc

        # Circular wrap-around add so loop boundary is seamless
        idx_arr = (start + np.arange(n_s)) % n_total
        out[idx_arr] += hit

    # Very short 2ms edge taper guarantees sample[0]==0 & sample[-1]==0 without audible dip
    return soft_limit_and_normalize(
        out, target_rms_db=-14.2, max_peak=0.86, drive=1.45, fade_in_s=0.002, fade_out_s=0.003
    )


def synth_lock_tick(rng):
    """~0.09s snappy mechanical/register lock-on blip while hovering crosshair."""
    t = make_time(0.09)
    n = len(t)

    # Crisp ratchet click
    click_n = fft_bandpass(rng.standard_normal(n), 2200.0, 7800.0)
    click = click_n * np.exp(-t / 0.0028) * 0.55
    mech = pitch_drop_thump(t, 0.0, 980.0, 310.0, 0.004, 0.010) * 0.45

    # Snappy bright register key-blip (1760 Hz + octave + metallic fifth)
    blip_modes = [
        (1760.0, 0.55, 0.022),
        (3520.0, 0.36, 0.017),
        (5280.0, 0.20, 0.012),
        (6920.0, 0.12, 0.009),
    ]
    blip = modal_bank(t, 0.002, blip_modes, rng=rng)

    raw = click + mech + blip
    return soft_limit_and_normalize(
        raw, target_rms_db=-14.0, max_peak=0.85, drive=1.35, fade_in_s=0.0015, fade_out_s=0.012
    )


def synth_lock_ready(rng):
    """~0.38s sharp steel SHING! + register ding when lock-on completes."""
    t = make_time(0.38)
    n = len(t)

    # 1. Rising steel SHING! draw (0.00s - 0.14s)
    shing_noise = swept_bandpass_noise(rng, n, 2400.0, 8600.0, 1100.0)
    shing_env = (1.0 - np.exp(-t / 0.012)) * np.exp(-np.maximum(0.0, t - 0.05) / 0.042)
    shing_sweep = shing_noise * shing_env * 0.62

    # Blooming harmonic steel glint sliding up to lock
    f_glint = 2200.0 + 2600.0 * (1.0 - np.exp(-t / 0.055))
    phase_glint = 2.0 * np.pi * np.cumsum(f_glint) / SR
    shing_tone = (
        0.25 * np.sin(phase_glint) + 0.18 * np.sin(1.48 * phase_glint)
    ) * np.exp(-t / 0.055) * (1.0 - np.exp(-t / 0.006))

    # 2. Register lock DING! at t=0.075s (bright dual brass chime)
    ding_modes = [
        (1975.5, 0.56, 0.110),  # B6
        (2637.0, 0.48, 0.105),  # E7
        (3951.0, 0.24, 0.075),
        (5440.0, 0.18, 0.055),
        (7410.0, 0.11, 0.036),
    ]
    ding = modal_bank(t, 0.075, ding_modes, rng=rng)
    clapper = fft_bandpass(rng.standard_normal(n), 2800.0, 8800.0)
    clapper *= np.where(t >= 0.075, np.exp(-(t - 0.075) / 0.003), 0.0) * 0.45

    raw = shing_sweep + shing_tone + ding + clapper
    return soft_limit_and_normalize(
        raw, target_rms_db=-14.2, max_peak=0.86, drive=1.35, fade_in_s=0.003, fade_out_s=0.035
    )


def synth_cash_register(rng):
    """~0.85s classic mechanical cash-register CHA-CHING! (spring drawer + dual brass bell + coin rattle)."""
    t = make_time(0.85)
    n = len(t)

    # 1. "CHA-" Mechanical key-lever click (0.00s) + spring drawer slide & bumper slam (0.115s)
    key_click = fft_bandpass(rng.standard_normal(n), 1500.0, 6800.0)
    key_click *= np.exp(-t / 0.006) * 0.55
    key_clack = pitch_drop_thump(t, 0.002, 540.0, 140.0, 0.008, 0.020) * 0.50

    drawer_slide = swept_bandpass_noise(rng, n, 900.0, 3400.0, 1200.0)
    drawer_slide *= np.exp(-((t - 0.060) / 0.038) ** 2) * (t < 0.135) * 0.55

    # Spring twang inside the drawer mechanism
    spring_f = 290.0 + 135.0 * (1.0 - np.exp(-t / 0.04))
    spring_ph = 2.0 * np.pi * np.cumsum(spring_f) / SR
    spring = 0.24 * np.sin(spring_ph) * np.exp(-t / 0.065) * (t > 0.015)

    drawer_slam = pitch_drop_thump(t, 0.115, 240.0, 68.0, 0.012, 0.035) * 0.72
    slam_rattle = fft_bandpass(rng.standard_normal(n), 600.0, 4200.0)
    slam_rattle *= np.where(t >= 0.115, np.exp(-(t - 0.115) / 0.018), 0.0) * 0.55

    # 2. "-CHING!" Iconic dual-strike brass register bell at 0.120s & 0.142s
    bell_1 = [
        (2093.0, 0.54, 0.260),  # C7
        (2637.0, 0.42, 0.240),  # E7
        (4186.0, 0.26, 0.165),
        (5780.0, 0.20, 0.115),
        (7920.0, 0.12, 0.075),
    ]
    bell_2 = [
        (2106.0, 0.46, 0.270),  # slight detune for classic shimmering brass bell
        (2651.0, 0.38, 0.250),
        (4212.0, 0.22, 0.175),
        (5830.0, 0.16, 0.120),
        (8050.0, 0.10, 0.078),
    ]
    bells = modal_bank(t, 0.120, bell_1, rng=rng) + modal_bank(t, 0.142, bell_2, rng=rng)

    # 3. Coin tray jingle rattle (0.14s - 0.62s)
    coins = np.zeros_like(t)
    for k in range(14):
        tk = 0.145 + k * 0.030 + float(rng.uniform(-0.008, 0.010))
        base_f = float(rng.uniform(3900.0, 6800.0))
        amp_k = 0.14 * (0.91 ** k)
        c_modes = [
            (base_f, amp_k, 0.038),
            (base_f * 1.43, amp_k * 0.72, 0.028),
            (base_f * 1.91, amp_k * 0.45, 0.020),
        ]
        coins += modal_bank(t, tk, c_modes, rng=rng)

    raw = key_click + key_clack + drawer_slide + spring + drawer_slam + slam_rattle + bells + coins
    return soft_limit_and_normalize(
        raw, target_rms_db=-14.0, max_peak=0.86, drive=1.35, fade_in_s=0.003, fade_out_s=0.045
    )


def synth_cash_flutter(rng):
    """~0.65s fluttering paper dollar bills + bright coin clinks."""
    t = make_time(0.65)
    n = len(t)

    # 1. Crisp paper bill burst & flutter (amplitude-modulated crisp paper noise)
    paper_base = fft_bandpass(rng.standard_normal(n), 1100.0, 6200.0)
    # Rapid fluttering modulation (28 Hz + 41 Hz warble for overlapping bills)
    flutter_mod = (
        0.55
        + 0.30 * np.sin(2.0 * np.pi * 29.0 * t + 0.4)
        + 0.22 * np.sin(2.0 * np.pi * 43.0 * t + 1.7)
    )
    flutter_mod = np.clip(flutter_mod, 0.12, 1.15)
    burst_env = (1.0 - np.exp(-t / 0.015)) * np.exp(-t / 0.22)
    paper = paper_base * flutter_mod * burst_env * 0.85

    # Individual paper snap flicks
    snaps = np.zeros_like(t)
    for k in range(9):
        tk = 0.012 + k * 0.042 + float(rng.uniform(-0.008, 0.008))
        snap_n = fft_bandpass(rng.standard_normal(n), 1600.0, 5600.0)
        snaps += snap_n * np.where(t >= tk, np.exp(-(t - tk) / 0.009), 0.0) * (0.42 * (0.90 ** k))

    # 2. Bright scattering coin clinks
    coins = np.zeros_like(t)
    for k in range(12):
        tk = 0.045 + k * 0.044 + float(rng.uniform(-0.010, 0.010))
        f0 = float(rng.uniform(4100.0, 6900.0))
        amp_k = 0.22 * (0.93 ** k)
        c_modes = [
            (f0, amp_k, 0.055),
            (f0 * 1.38, amp_k * 0.75, 0.040),
            (f0 * 1.87, amp_k * 0.45, 0.026),
        ]
        coins += modal_bank(t, tk, c_modes, rng=rng)

    raw = paper + snaps + coins
    return soft_limit_and_normalize(
        raw, target_rms_db=-14.2, max_peak=0.86, drive=1.35, fade_in_s=0.004, fade_out_s=0.040
    )


def synth_plane_whoosh(rng):
    """~0.45s funny aerodynamic paper-plane launch whoosh + scissor glint."""
    t = make_time(0.45)
    n = len(t)

    # 1. Crisp paper-plane launch flick at t=0.012s
    flick_thump = pitch_drop_thump(t, 0.010, 390.0, 130.0, 0.008, 0.022) * 0.58
    flick_snap = fft_bandpass(rng.standard_normal(n), 1800.0, 6400.0)
    flick_snap *= np.where(t >= 0.010, np.exp(-(t - 0.010) / 0.008), 0.0) * 0.55

    # 2. Aerodynamic Doppler swoop whoosh (rises rapidly then banks downward)
    def doppler_f(frac):
        if frac < 0.34:
            u = frac / 0.34
            return 380.0 + 1420.0 * np.sin(u * np.pi * 0.5)
        u = (frac - 0.34) / 0.66
        return 1800.0 - 1380.0 * (u ** 0.85)

    whoosh = swept_bandpass_noise(rng, n, doppler_f, None, 520.0)
    whoosh_env = np.sin(np.pi * np.clip(t / 0.43, 0.0, 1.0)) ** 0.85
    whoosh *= whoosh_env * 0.92

    # Subtle comedic whistling paper-wing glide tone
    glide_f = 540.0 + 480.0 * np.exp(-((t - 0.14) / 0.09) ** 2) - 180.0 * (t / 0.45)
    glide_ph = 2.0 * np.pi * np.cumsum(glide_f) / SR
    whistle = 0.17 * np.sin(glide_ph) * np.exp(-((t - 0.17) / 0.11) ** 2)

    # 3. Scissor glint mid-flight (at t=0.11s)
    glint_modes = [
        (4680.0, 0.24, 0.065),
        (4702.0, 0.18, 0.060),
        (6940.0, 0.18, 0.048),
        (8820.0, 0.11, 0.032),
    ]
    glint = modal_bank(t, 0.110, glint_modes, rng=rng)

    raw = flick_thump + flick_snap + whoosh + whistle + glint
    return soft_limit_and_normalize(
        raw, target_rms_db=-14.0, max_peak=0.86, drive=1.30, fade_in_s=0.005, fade_out_s=0.038
    )


# ---------------------------------------------------------------------------
# Voice clip indexing from scratch/kyle_clips/ + cut_kyle_sounds.py
# ---------------------------------------------------------------------------

def load_voice_clips_metadata(voice_dir):
    """Read cleaned Kyle voice WAVs from voice_dir and enrich from cut_kyle_sounds.py."""
    meta_by_id = {}
    cut_script = os.path.join(HERE, "cut_kyle_sounds.py")
    if os.path.exists(cut_script):
        spec = importlib.util.spec_from_file_location("cut_kyle_sounds", cut_script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for cid, cat, title, transcript, role, t0, t1, notes in getattr(mod, "TAKES", []):
            meta_by_id[cid] = {
                "category": cat,
                "title": title,
                "transcript": transcript,
                "role": role,
                "src_range": f"{t0:.2f}s-{t1:.2f}s",
                "notes": notes,
            }

    # Add the 3 bonus edited variants defined in cut_kyle_sounds.py
    edit_meta = {
        "edit_01_hey_man_tight": {
            "category": "edits",
            "title": "Hey man, you gonna give me a cut? (No 'uh')",
            "transcript": "Hey man, you gonna give me a cut?",
            "role": "Idle / Approach",
            "src_range": "19.67s-21.36s (edited)",
            "notes": "Spliced out the drawn-out 'uhhh' pause (20.19s-20.52s) with a 25ms crossfade.",
        },
        "edit_02_whoa_give_cut": {
            "category": "edits",
            "title": "Whoa! Give me a cut! (Combo)",
            "transcript": "Whoa! Give me a cut!",
            "role": "Aggro / Attack",
            "src_range": "whoa_04 + cut_02",
            "notes": "Combined loud 'Whoa!' + 80ms gap + 'Give me a cut!' for a punchy lunge cue.",
        },
        "edit_03_kyle_clients": {
            "category": "edits",
            "title": "Hey, it's Kyle! Will stole my clients!",
            "transcript": "Hey, it's Kyle! Will stole my clients!",
            "role": "Spawn / Intro Taunt",
            "src_range": "kyle_02 + clients_02",
            "notes": "Combined bright 'Hey, it's Kyle!' + 110ms gap + screaming 'Will stole my clients!'.",
        },
    }
    meta_by_id.update(edit_meta)

    clips = []
    if not os.path.isdir(voice_dir):
        return clips

    for fname in sorted(os.listdir(voice_dir)):
        if not fname.lower().endswith(".wav"):
            continue
        cid = os.path.splitext(fname)[0]
        fpath = os.path.join(voice_dir, fname)
        with wave.open(fpath, "rb") as wf:
            sr = wf.getframerate()
            ch = wf.getnchannels()
            sw = wf.getsampwidth()
            nframes = wf.getnframes()
            raw = wf.readframes(nframes)
        samples = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
        stats = audio_stats(samples, sr=sr)
        info = meta_by_id.get(cid, {})
        clips.append({
            "id": cid,
            "filename": fname,
            "path": fpath,
            "wav_bytes": os.path.getsize(fpath),
            "category": info.get("category", "voice"),
            "title": info.get("title", cid),
            "transcript": info.get("transcript", ""),
            "role": info.get("role", ""),
            "src_range": info.get("src_range", ""),
            "notes": info.get("notes", ""),
            "peaks": waveform_peaks(samples),
            "sample_rate": sr,
            "channels": ch,
            "bit_depth": sw * 8,
            **stats,
        })
    return clips


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------

SFX_SPECS = [
    (
        "snip_fast",
        "snip_fast.wav",
        "Fast Scissor Snip",
        "Rapid lock-on charge & melee chops",
        "Sharp metallic steel blade slide + high-Q stainless ring + crisp tip snap.",
        101,
        synth_snip_fast,
    ),
    (
        "snip_heavy",
        "snip_heavy.wav",
        "Heavy Barber Shear Chop",
        "Big hits & John Bird wing shred",
        "Heavy double-blade barber shear CHOP with pivot clank and deep steel resonance.",
        202,
        synth_snip_heavy,
    ),
    (
        "snip_latch_loop",
        "snip_latch_loop.wav",
        "Frantic Snip Latch Loop",
        "Kyle latched in victim's peripheral FOV",
        "Seamless 1.35s looping frantic snip-snip-snip rhythm with comedic syncopation.",
        303,
        synth_snip_latch_loop,
    ),
    (
        "lock_tick",
        "lock_tick.wav",
        "Lock-On Tick Blip",
        "Hovering crosshair over target",
        "Snappy mechanical escapement click + bright brass register key blip.",
        404,
        synth_lock_tick,
    ),
    (
        "lock_ready",
        "lock_ready.wav",
        "Lock-On Ready SHING!",
        "Lock-on complete & ready to launch",
        "Rising steel SHING! shimmer + dual-tone register lock ding.",
        505,
        synth_lock_ready,
    ),
    (
        "cash_register",
        "cash_register.wav",
        "Cash Register CHA-CHING!",
        "Chopping registers & cash burst score",
        "Spring drawer slide + bumper slam + classic dual brass bell ring + coin tray rattle.",
        606,
        synth_cash_register,
    ),
    (
        "cash_flutter",
        "cash_flutter.wav",
        "Cash & Coin Spray",
        "Dollar bills & coins spraying from victim",
        "Rapidly fluttering crisp paper dollar bills + scattering bright coin clinks.",
        707,
        synth_cash_flutter,
    ),
    (
        "plane_whoosh",
        "plane_whoosh.wav",
        "Paper-Plane Launch Whoosh",
        "Kyle homing paper-plane launch",
        "Paper-fold launch flick + aerodynamic Doppler whoosh + mid-flight scissor glint.",
        808,
        synth_plane_whoosh,
    ),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--voice-dir", default=DEFAULT_VOICE_DIR)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    sfx_entries = []

    print(f"Synthesizing {len(SFX_SPECS)} SFX WAVs -> {args.out_dir}")
    for sid, fname, title, role, desc, seed, fn in SFX_SPECS:
        rng = np.random.default_rng(seed)
        samples = fn(rng)
        fpath = os.path.join(args.out_dir, fname)
        nbytes = write_wav(fpath, samples, sr=SR)
        stats = audio_stats(samples, sr=SR)
        print(
            f"  {fname:22s} dur={stats['duration']:.3f}s  "
            f"rms={stats['rms_db']:6.2f} dBFS  peak={stats['peak_linear']:.3f} "
            f"({stats['peak_db']:5.2f} dBFS)  dc={stats['dc_offset']:+.6f}"
        )
        sfx_entries.append({
            "id": sid,
            "filename": fname,
            "path": fpath,
            "title": title,
            "role": role,
            "description": desc,
            "looping": sid == "snip_latch_loop",
            "wav_bytes": nbytes,
            "peaks": waveform_peaks(samples),
            **stats,
        })

    voice_clips = load_voice_clips_metadata(args.voice_dir)
    print(f"Indexed {len(voice_clips)} Kyle voice clips from {args.voice_dir}")

    manifest = {
        "format": {
            "sample_rate": SR,
            "channels": 1,
            "bit_depth": 16,
            "encoding": "PCM",
        },
        "sfx_dir": args.out_dir,
        "voice_dir": args.voice_dir,
        "sfx": sfx_entries,
        "voice_clips": voice_clips,
    }
    manifest_path = os.path.join(args.out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"Wrote manifest: {manifest_path}")


if __name__ == "__main__":
    main()
