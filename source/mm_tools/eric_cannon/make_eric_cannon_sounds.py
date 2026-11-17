"""Audio Asset Builder for THE ERIC DEASON CANNON (`sound/eric_cannon/`).

1. Stages `source/sound_bank/random_sounds/canislupusfantasy2.wav` ->
   `sound/eric_cannon/canislupusfantasy2.wav` as clean 16-bit mono PCM WAV calibrated
   for modest, pleasant playback volume when shooting the cannon!
2. Synthesizes bespoke mechanical, cartoon wind-up, artillery blast, giant-ear wingbeat,
   comical Doppler sky-scream, high-altitude wind, and bomb-dive whistle WAVs.
"""
import math
import os
import struct
import wave

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
SRC_FANTASY = os.path.join(MOD_ROOT, "source", "sound_bank", "random_sounds", "canislupusfantasy2.wav")
SND_DIR = os.path.join(MOD_ROOT, "sound", "eric_cannon")
OUT_SND = os.path.join(MM_TOOLS, "out", "eric_cannon", "sounds")


def write_mono_wav(path, samples_f32, sr=22050):
    arr = np.clip(samples_f32, -0.98, 0.98)
    pcm = (arr * 32767.0).astype(np.int16)
    for dst in (path, os.path.join(OUT_SND, os.path.basename(path))):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with wave.open(dst, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm.tobytes())


def stage_canis_lupus_fantasy():
    """Reads `canislupusfantasy2.wav` (handles PCM int16/int24/int32 or IEEE float WAV),
    downmixes to mono for Quake 3D `sound()`/`pointsound()` compatibility, and normalizes
    to a gentle modest peak (`0.48`, RMS ~ `-16 dBFS`) so combined with `EC_FANTASY_VOL = 0.36`
    in QuakeC it plays clearly at a modest, comfortable volume when fired!"""
    assert os.path.exists(SRC_FANTASY), f"Missing {SRC_FANTASY}"
    raw = open(SRC_FANTASY, "rb").read()
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WAVE", "Unexpected WAV header"

    pos = 12
    fmt_tag, nch, sr, bps = 1, 1, 44100, 16
    data_bytes = b""
    while pos + 8 <= len(raw):
        cid = raw[pos:pos + 4]
        csz = struct.unpack_from("<I", raw, pos + 4)[0]
        body = raw[pos + 8:pos + 8 + csz]
        if cid == b"fmt ":
            fmt_tag, nch, sr, _, _, bps = struct.unpack_from("<HHIIHH", body, 0)
        elif cid == b"data":
            data_bytes = body
            break
        pos += 8 + csz + (csz & 1)

    if fmt_tag == 3 and bps == 32:
        arr = np.frombuffer(data_bytes, dtype=np.float32)
    elif bps == 16:
        arr = np.frombuffer(data_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    elif bps == 24:
        b3 = np.frombuffer(data_bytes, dtype=np.uint8).reshape(-1, 3)
        i32 = (b3[:, 0].astype(np.int32) | (b3[:, 1].astype(np.int32) << 8) | (b3[:, 2].astype(np.int32) << 16))
        i32 = np.where(i32 & 0x800000, i32 - 0x1000000, i32)
        arr = i32.astype(np.float32) / 8388608.0
    elif bps == 32:
        arr = np.frombuffer(data_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        arr = (np.frombuffer(data_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0

    if nch > 1:
        arr = arr[: (len(arr) // nch) * nch].reshape(-1, nch).mean(axis=1)

    # Resample cleanly to 22050 Hz if higher so DarkPlaces sound memory stays nimble & crystal clear
    target_sr = 22050
    if sr != target_sr:
        g = math.gcd(sr, target_sr)
        arr = signal.resample_poly(arr, target_sr // g, sr // g).astype(np.float32)
        sr = target_sr

    dur_s = len(arr) / sr
    # Trim if absurdly long (> 14s) with smooth 1.2s fadeout so it naturally spans launch + sky flight!
    max_len = int(12.5 * sr)
    if len(arr) > max_len:
        arr = arr[:max_len].copy()
        fade_n = int(1.4 * sr)
        arr[-fade_n:] *= np.linspace(1.0, 0.0, fade_n, dtype=np.float32)

    peak = float(np.max(np.abs(arr))) or 1.0
    # Modest master calibration (peak = 0.46)
    arr = arr * (0.46 / peak)
    out_p = os.path.join(SND_DIR, "canislupusfantasy2.wav")
    write_mono_wav(out_p, arr, sr=sr)
    print(f"  [WAV OK] canislupusfantasy2.wav ({len(arr)/sr:.2f}s @ {sr}Hz, modest peak=0.46, src={dur_s:.2f}s)")
    return out_p


def build_synthesized_sfx():
    sr = 22050
    rng = np.random.default_rng(2026)

    # 1. `mount.wav` (0.48s): Heavy steel turret breech clunk + hydraulic elevation servo lock
    t = np.linspace(0.0, 0.48, int(0.48 * sr), endpoint=False, dtype=np.float32)
    clunk = (
        0.55 * np.sin(2.0 * np.pi * (145.0 * np.exp(-t * 14.0) + 58.0) * t) * np.exp(-t * 18.0)
        + 0.35 * rng.standard_normal(len(t)).astype(np.float32) * np.exp(-t * 36.0)
    )
    t2 = np.maximum(0.0, t - 0.10)
    servo = 0.24 * np.sin(2.0 * np.pi * (280.0 + 210.0 * np.minimum(1.0, t2 / 0.26)) * t2) * (t > 0.10) * np.exp(-t2 * 6.5)
    latch = 0.42 * np.sin(2.0 * np.pi * 620.0 * np.maximum(0.0, t - 0.34)) * (t > 0.34) * np.exp(-np.maximum(0.0, t - 0.34) * 45.0)
    write_mono_wav(os.path.join(SND_DIR, "mount.wav"), (clunk + servo + latch) * 0.82, sr)

    # 2. `windup.wav` (0.92s): Hilarious rubbery Wew-Cannon barrel stretch/creak + rising cartoon pressure swell!
    t = np.linspace(0.0, 0.92, int(0.92 * sr), endpoint=False, dtype=np.float32)
    # Rubbery creaking groan (FM stick-slip) + rising slide-whistle / turbine charge
    f_rise = 115.0 + 540.0 * ((t / 0.92) ** 2.1)
    phase_rise = 2.0 * np.pi * np.cumsum(f_rise) / sr
    rubber_creak = 0.38 * np.sin(phase_rise * 0.32 + 3.2 * np.sin(2.0 * np.pi * 19.0 * t)) * np.sin(np.pi * np.minimum(1.0, t / 0.85))
    whine = 0.34 * np.sin(phase_rise) * ((t / 0.92) ** 0.7)
    gulp_swell = 0.32 * np.sin(2.0 * np.pi * (75.0 + 95.0 * (t / 0.92)) * t) * np.exp(-(((t - 0.68) / 0.18) ** 2))
    env = np.minimum(1.0, t / 0.04) * np.minimum(1.0, (0.92 - t) / 0.03)
    write_mono_wav(os.path.join(SND_DIR, "windup.wav"), (rubber_creak + whine + gulp_swell) * env * 0.85, sr)

    # 3. `fire_boom.wav` (1.35s): Colossal deep cannon mortar thump + cartoon brassy blat + supersonic crack!
    t = np.linspace(0.0, 1.35, int(1.35 * sr), endpoint=False, dtype=np.float32)
    sub_punch = 0.75 * np.sin(2.0 * np.pi * (92.0 * np.exp(-t * 7.5) + 34.0) * t) * np.exp(-t * 4.2)
    crack_noise = rng.standard_normal(len(t)).astype(np.float32)
    b_lp, a_lp = signal.butter(3, 1800.0 / (0.5 * sr), btype="low")
    boom_roar = signal.lfilter(b_lp, a_lp, crack_noise).astype(np.float32) * np.exp(-t * 3.4) * 0.65
    # Cartoon blunderbuss tube resonance ("THWOOOOMP!")
    thwomp = 0.42 * np.sin(2.0 * np.pi * (240.0 * np.exp(-t * 11.0) + 65.0) * t) * np.exp(-t * 8.5)
    mix_boom = np.tanh((sub_punch + boom_roar + thwomp) * 1.35) * 0.88
    write_mono_wav(os.path.join(SND_DIR, "fire_boom.wav"), mix_boom, sr)

    # 4. `ear_flap1..4.wav` (0.30s each): 4 meaty, leathery giant human ear wingbeat whooshes!
    for idx in range(4):
        t = np.linspace(0.0, 0.30, int(0.30 * sr), endpoint=False, dtype=np.float32)
        nz = rng.standard_normal(len(t)).astype(np.float32)
        fc = (340.0 + idx * 45.0) / (0.5 * sr)
        b_bp, a_bp = signal.butter(2, [max(0.02, fc * 0.45), min(0.92, fc * 1.85)], btype="band")
        whoosh = signal.lfilter(b_bp, a_bp, nz).astype(np.float32)
        env_w = np.exp(-(((t - 0.10) / 0.065) ** 2))
        fleshy_thud = 0.36 * np.sin(2.0 * np.pi * (98.0 - 38.0 * (t / 0.30) + idx * 7.0) * t) * np.exp(-t * 18.0)
        flap = (whoosh * env_w * 1.6 + fleshy_thud) * 0.78
        write_mono_wav(os.path.join(SND_DIR, f"ear_flap{idx+1}.wav"), flap, sr)

    # 5. `sky_wind.wav` (1.60s seamless-friendly wind rush)
    t = np.linspace(0.0, 1.60, int(1.60 * sr), endpoint=False, dtype=np.float32)
    nz = rng.standard_normal(len(t)).astype(np.float32)
    b_w, a_w = signal.butter(2, [180.0 / (0.5 * sr), 1150.0 / (0.5 * sr)], btype="band")
    wind = signal.lfilter(b_w, a_w, nz).astype(np.float32)
    mod = 0.72 + 0.28 * np.sin(2.0 * np.pi * 1.25 * t)
    fade = np.minimum(1.0, t / 0.08) * np.minimum(1.0, (1.60 - t) / 0.08)
    write_mono_wav(os.path.join(SND_DIR, "sky_wind.wav"), wind * mod * fade * 0.55, sr)

    # 6. `doppler_scream.wav` (2.10s): Comical vocal formant Doppler sky-yell ("WAAAAHHHH-ooooh!")
    t = np.linspace(0.0, 2.10, int(2.10 * sr), endpoint=False, dtype=np.float32)
    # Pitch rises on launch excitement, holds with vibrato, then Doppler-drops!
    f0 = (265.0 + 75.0 * np.sin(np.pi * np.minimum(1.0, t / 0.85)) - 95.0 * np.maximum(0.0, (t - 0.95) / 1.15)
          + 9.5 * np.sin(2.0 * np.pi * 6.8 * t))
    ph0 = np.cumsum(f0) / sr
    # Rich glottal sawtooth harmonics filtered through "AAAH" vocal tract formants (F1=760Hz, F2=1220Hz, F3=2480Hz)
    glottal = sum(((-1) ** (h + 1)) * (1.0 / (h ** 0.88)) * np.sin(2.0 * np.pi * h * ph0) for h in range(1, 14)).astype(np.float32)
    vocal = np.zeros_like(glottal)
    for f_form, bw, gain in ((760.0, 140.0, 1.0), (1220.0, 190.0, 0.68), (2480.0, 280.0, 0.30)):
        lo = max(0.02, (f_form - bw) / (0.5 * sr))
        hi = min(0.95, (f_form + bw) / (0.5 * sr))
        bf, af = signal.butter(2, [lo, hi], btype="band")
        vocal += gain * signal.lfilter(bf, af, glottal).astype(np.float32)
    env_v = np.minimum(1.0, t / 0.09) * np.exp(-np.maximum(0.0, t - 1.25) * 2.2) * np.minimum(1.0, (2.10 - t) / 0.12)
    vocal /= (np.max(np.abs(vocal)) + 1e-6)
    write_mono_wav(os.path.join(SND_DIR, "doppler_scream.wav"), vocal * env_v * 0.56, sr)

    # 7. `dive_whistle.wav` (2.20s): Classic cartoon artillery shell / bomb downward whistle!
    t = np.linspace(0.0, 2.20, int(2.20 * sr), endpoint=False, dtype=np.float32)
    f_wh = 1180.0 * np.exp(-0.56 * t) + 18.0 * np.sin(2.0 * np.pi * 11.0 * t)
    ph_w = 2.0 * np.pi * np.cumsum(f_wh) / sr
    whistle = (0.72 * np.sin(ph_w) + 0.18 * np.sin(2.0 * ph_w))
    air_rush = signal.lfilter(*signal.butter(2, 1600.0 / (0.5 * sr), btype="low"), rng.standard_normal(len(t))).astype(np.float32) * 0.16
    env_wh = np.minimum(1.0, t / 0.14) * np.minimum(1.0, (2.20 - t) / 0.08)
    write_mono_wav(os.path.join(SND_DIR, "dive_whistle.wav"), (whistle + air_rush) * env_wh * 0.58, sr)
    print(f"  [WAV OK] Synthesized 10 custom SFX in {SND_DIR}")


def build_nuke_boom():
    """Synthesizes `nuke_boom.wav` (4.0s @ 22050 Hz 16-bit mono PCM WAV):
    deep sub-bass nuclear detonation + crackling shockwave + long rolling thunder rumble."""
    sr = 22050
    dur = 4.0
    n = int(dur * sr)
    rng = np.random.default_rng(1945)
    t = np.linspace(0.0, dur, n, endpoint=False, dtype=np.float32)

    # 1. Punchy sub-bass detonation drop (instant impact slam + deep chest-thump sustain)
    f_sub = 28.0 + 96.0 * np.exp(-t * 9.5) + 42.0 * np.exp(-t * 28.0)
    ph_sub = 2.0 * np.pi * np.cumsum(f_sub) / sr
    sub_body = (
        0.90 * np.sin(ph_sub) * np.exp(-t * 2.15)
        + 0.45 * np.sin(0.5 * ph_sub + 0.3) * np.exp(-t * 1.45)
    )
    sub_punch = np.tanh(sub_body * 1.55) * np.minimum(1.0, t / 0.004)

    # 2. Supersonic shockwave transient + crackling plasma/debris snap
    nz_crack = rng.standard_normal(n).astype(np.float32)
    b_hi, a_hi = signal.butter(2, [750.0 / (0.5 * sr), 4600.0 / (0.5 * sr)], btype="band")
    shock_band = signal.lfilter(b_hi, a_hi, nz_crack).astype(np.float32)
    # Sparse high-energy micro-crackles across the shock front (0.01s..1.35s)
    impulses = (rng.random(n) < 0.014).astype(np.float32) * rng.standard_normal(n).astype(np.float32)
    crackle_filt = signal.lfilter(b_hi, a_hi, impulses).astype(np.float32)
    crack_env = (
        1.15 * np.exp(-t * 14.0)
        + 0.55 * np.exp(-np.maximum(0.0, t - 0.04) * 3.1) * (t >= 0.04)
    )
    shock_crackle = (0.55 * shock_band + 1.35 * crackle_filt) * crack_env

    # 3. Long thunderous nuclear rumble with downtown building echo swells
    nz_rumble = rng.standard_normal(n).astype(np.float32)
    b_low, a_low = signal.butter(3, 210.0 / (0.5 * sr), btype="low")
    deep_roar = signal.lfilter(b_low, a_low, nz_rumble).astype(np.float32)
    deep_roar /= (np.std(deep_roar) + 1e-6)

    nz_mid = rng.standard_normal(n).astype(np.float32)
    b_mid, a_mid = signal.butter(2, [140.0 / (0.5 * sr), 720.0 / (0.5 * sr)], btype="band")
    mid_roar = signal.lfilter(b_mid, a_mid, nz_mid).astype(np.float32)
    mid_roar /= (np.std(mid_roar) + 1e-6)

    # Rolling secondary pressure swells (echoes at ~0.32s, 0.78s, 1.38s, 2.15s)
    echo_swell = (
        1.0
        + 0.42 * np.exp(-(((t - 0.32) / 0.14) ** 2))
        + 0.34 * np.exp(-(((t - 0.78) / 0.22) ** 2))
        + 0.25 * np.exp(-(((t - 1.38) / 0.30) ** 2))
        + 0.16 * np.exp(-(((t - 2.15) / 0.38) ** 2))
    )
    rumble_env = np.minimum(1.0, t / 0.025) * np.exp(-t * 0.88) * echo_swell
    thunder_tail = (0.48 * deep_roar + 0.30 * mid_roar) * rumble_env

    mix = sub_punch + 0.65 * shock_crackle + thunder_tail
    # Soft-saturate and smooth end fadeout (last 0.40s) to guarantee zero tail click
    mix = np.tanh(mix * 1.18)
    fade_out = np.minimum(1.0, (dur - t) / 0.40)
    mix *= fade_out
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = (mix / peak) * 0.92

    out_p = os.path.join(SND_DIR, "nuke_boom.wav")
    write_mono_wav(out_p, mix.astype(np.float32), sr=sr)
    print(f"  [WAV OK] nuke_boom.wav ({dur:.2f}s @ {sr}Hz, 16-bit mono PCM -> {out_p})")
    return out_p


if __name__ == "__main__":
    stage_canis_lupus_fantasy()
    build_synthesized_sfx()
    build_nuke_boom()
