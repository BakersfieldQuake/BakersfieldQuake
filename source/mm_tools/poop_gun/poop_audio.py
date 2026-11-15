"""Warm-mastered comedic SFX & music pipeline for the Poop Gun simulator
(`source/mm_tools/poop_gun/poop_audio.py`).

Sources real Bakersfield Quake assets + the user-supplied Bhangra track and
masters every clip through high-pass, harsh-mid de-esser EQ, warm low-pass,
soft-knee limiting, and polite RMS leveling into `work/audio/*.wav`:
  - `windup_wew.wav`: Wew Cannon charge windup (`wc_charge.wav`)
  - `fart_1.wav` .. `fart_4.wav`: Real fart sounds from workspace sound folders
  - `yell_1.wav`, `yell_2.wav`, `yell_3.wav`, `wc_scream.wav`: Projectile yells
  - `proj_music.wav`: Uploaded Bhangra chorus drop (loop-ready, warm-mastered)
  - `mud_splat.wav`: Wet mud impact splatter
  - `fly_buzz.wav`: Subtle low-level buzzing fly loop
"""
from __future__ import annotations

import os
import shutil
import subprocess
import wave
from typing import Dict, Tuple

import numpy as np
from scipy import signal

from poop_core import WORK_DIR

REPO_ROOT = r"G:\Quake\Combat\BakersfieldQuake"
WCANNON_SOUND_DIR = r"G:\Quake\Combat\_bakersfield_dev\staged_assets\sound\wcannon"
UPLOADED_MUSIC_M4A = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841"
    r"\.user_uploaded\uploaded_media_1794704465214.m4a"
)
SCRATCH_MUSIC_WAV = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841"
    r"\scratch\uploaded_music_raw.wav"
)

SAMPLE_RATE = 22050

# Real workspace audio sources
WINDUP_SRC = os.path.join(WCANNON_SOUND_DIR, "wc_charge.wav")

FART_SOURCES: Dict[str, str] = {
    "fart_1": os.path.join(REPO_ROOT, "source", "mm_tools", "out", "sound", "grenade_new", "boom_04_mega_fart.wav"),
    "fart_2": os.path.join(REPO_ROOT, "source", "mm_tools", "out", "sound", "grenade_new", "shoot_04_fart.wav"),
    "fart_3": os.path.join(REPO_ROOT, "source", "mbox_sound_vote", "clips", "exp_fart_pop.wav"),
    "fart_4": os.path.join(REPO_ROOT, "source", "sound_bank", "random_sounds", "fart.wav"),
}

YELL_SOURCES: Dict[str, str] = {
    "yell_1": os.path.join(REPO_ROOT, "sound", "beach_uncle", "yell_1.wav"),
    "yell_2": os.path.join(REPO_ROOT, "sound", "beach_uncle", "yell_2.wav"),
    "yell_3": os.path.join(REPO_ROOT, "sound", "beach_uncle", "yell_4.wav"),
    "wc_scream": os.path.join(WCANNON_SOUND_DIR, "wc_scream.wav"),
}

MUD_SPLAT_SRC = os.path.join(REPO_ROOT, "sound", "beach_uncle", "mud_explode.wav")
STAGED_DIR = r"G:\Quake\Combat\_bakersfield_dev\staged_assets\sound"
EXTRA_SOURCES: Dict[str, str] = {
    "yell_4": os.path.join(REPO_ROOT, "sound", "beach_uncle", "yell_3.wav"),
    "mud_hit": os.path.join(REPO_ROOT, "sound", "beach_uncle", "mud_hit.wav"),
    "funny_fart1": os.path.join(STAGED_DIR, "funny", "fart1.wav"),
    "funny_fart2": os.path.join(STAGED_DIR, "funny", "fart2.wav"),
    "tiny_fart": os.path.join(REPO_ROOT, "source", "mm_tools", "out", "sound", "grenade_new", "bounce_11_tiny_fart.wav"),
    "goopop": os.path.join(STAGED_DIR, "weapons", "goopop.wav"),
    "goosplat": os.path.join(STAGED_DIR, "weapons", "goosplat.wav"),
    "burp": os.path.join(STAGED_DIR, "beerguy", "chill_burp.wav"),
    "pain_beer": os.path.join(STAGED_DIR, "beerguy", "pain_beer.wav"),
    "tuktuk": os.path.join(STAGED_DIR, "vehicles", "horn_tuktuk.wav"),
    "bike_bell": os.path.join(STAGED_DIR, "bikes", "bell_ring.wav"),
    "goofire": os.path.join(STAGED_DIR, "weapons", "goofire.wav"),
    "goostick": os.path.join(STAGED_DIR, "weapons", "goostick.wav"),
    "slide_whistle": os.path.join(REPO_ROOT, "source", "mm_tools", "out", "sound", "grenade_new", "shoot_02_slide_whistle.wav"),
    "bloop": os.path.join(REPO_ROOT, "source", "mm_tools", "out", "sound", "grenade_new", "bounce_04_bloop.wav"),
    "sad_trombone": os.path.join(REPO_ROOT, "source", "mm_tools", "out", "sound", "grenade_new", "boom_07_sad_trombone.wav"),
    "vine_boom": os.path.join(REPO_ROOT, "source", "mm_tools", "out", "sound", "grenade_new", "boom_01_vine_boom.wav"),
    "squat_thud": os.path.join(REPO_ROOT, "source", "mbox_sound_vote", "clips", "exp_squat_thud.wav"),
    "heh_fart": os.path.join(REPO_ROOT, "source", "mbox_sound_vote", "clips", "exp_rob_heh_fart.wav"),
    "wheel_wobble": os.path.join(REPO_ROOT, "source", "mbox_sound_vote", "clips", "exp_wheel_wobble.wav"),
}


def _read_wav_mono(path: str) -> Tuple[np.ndarray, int]:
    with wave.open(path, "rb") as wf:
        sr = wf.getframerate()
        n_ch = wf.getnchannels()
        sw = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())
    if sw == 2:
        arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sw == 1:
        arr = np.frombuffer(raw, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
    else:
        raise ValueError(f"Unsupported sample width {sw} in {path}")
    if n_ch > 1:
        arr = arr.reshape(-1, n_ch).mean(axis=1)
    if sr != SAMPLE_RATE:
        n_out = max(1, int(round(len(arr) * SAMPLE_RATE / float(sr))))
        arr = signal.resample_poly(arr, SAMPLE_RATE, sr).astype(np.float32)
        if len(arr) > n_out:
            arr = arr[:n_out]
        sr = SAMPLE_RATE
    return arr.astype(np.float32), sr


def _write_wav_mono(path: str, samples: np.ndarray, sr: int = SAMPLE_RATE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = samples.astype(np.float32)
    x -= float(np.mean(x))
    pcm = np.clip(np.round(x * 32767.0), -32767, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sr))
        wf.writeframes(pcm.tobytes())


def _apply_fades(x: np.ndarray, sr: int, fade_in_s: float, fade_out_s: float) -> np.ndarray:
    out = x.copy()
    n_in = min(len(out) // 3, max(1, int(round(fade_in_s * sr))))
    n_out = min(len(out) // 2, max(1, int(round(fade_out_s * sr))))
    # Smooth half-cosine S-curve fades prevent clicks cleanly
    t_in = np.linspace(0.0, np.pi * 0.5, n_in, dtype=np.float32)
    t_out = np.linspace(0.0, np.pi * 0.5, n_out, dtype=np.float32)
    out[:n_in] *= np.sin(t_in)
    out[-n_out:] *= np.cos(t_out)
    return out


def _bandpass(x: np.ndarray, sr: int, lo_hz: float, hi_hz: float, order: int = 3) -> np.ndarray:
    nyq = 0.5 * sr
    lo = max(12.0, lo_hz) / nyq
    hi = min(nyq * 0.94, hi_hz) / nyq
    sos = signal.butter(order, [lo, hi], btype="bandpass", output="sos")
    return signal.sosfiltfilt(sos, x).astype(np.float32)


def _notch_harsh_mids(x: np.ndarray, sr: int, center_hz: float = 2850.0, q: float = 1.15, cut_mix: float = 0.42) -> np.ndarray:
    """Gently attenuate upper-mid ear-fatigue band (~2.5-3.5 kHz) for smooth non-harsh tone."""
    nyq = 0.5 * sr
    w0 = min(0.88, max(0.05, center_hz / nyq))
    b, a = signal.iirnotch(w0, q)
    notched = signal.filtfilt(b, a, x).astype(np.float32)
    return ((1.0 - cut_mix) * x + cut_mix * notched).astype(np.float32)


def _master_warm(
    x: np.ndarray,
    sr: int,
    *,
    hp_hz: float = 45.0,
    lp_hz: float = 4200.0,
    notch_hz: float | None = 2850.0,
    notch_mix: float = 0.42,
    target_rms: float = 0.16,
    peak_cap: float = 0.68,
    fade_in_s: float = 0.015,
    fade_out_s: float = 0.055,
    drive: float = 1.35,
) -> np.ndarray:
    """Apply broadcast-warm mastering: DC/sub removal, gentle harsh-high roll-off,
    upper-mid de-harsh notch, soft-knee limiting, and polite RMS normalization."""
    if len(x) < 16:
        return x.astype(np.float32)
    y = x.astype(np.float32) - float(np.mean(x))
    y = _bandpass(y, sr, hp_hz, lp_hz, order=2)
    if notch_hz is not None:
        y = _notch_harsh_mids(y, sr, center_hz=notch_hz, q=1.1, cut_mix=notch_mix)

    # Pre-level into gentle soft-knee compressor/saturator so loud transients never spike
    pre_rms = float(np.sqrt(np.mean(y ** 2))) + 1e-6
    y = y * (0.22 / pre_rms)
    y = (np.tanh(y * drive) / math_tanh_norm(drive)).astype(np.float32)

    # Polite target RMS with hard peak ceiling
    cur_rms = float(np.sqrt(np.mean(y ** 2))) + 1e-6
    gain = target_rms / cur_rms
    y = y * gain
    pk = float(np.max(np.abs(y)))
    if pk > peak_cap:
        # Soft-limit excess above 85% of cap
        thresh = peak_cap * 0.82
        over = np.maximum(0.0, np.abs(y) - thresh)
        head = peak_cap - thresh
        y = np.sign(y) * np.where(np.abs(y) > thresh, thresh + head * np.tanh(over / max(1e-4, head)), np.abs(y))

    return _apply_fades(y.astype(np.float32), sr, fade_in_s, fade_out_s)


def math_tanh_norm(drive: float) -> float:
    return float(np.tanh(drive))


def _ensure_music_wav() -> str:
    if os.path.exists(SCRATCH_MUSIC_WAV) and os.path.getsize(SCRATCH_MUSIC_M4A_OR_WAV := SCRATCH_MUSIC_WAV) > 50000:
        return SCRATCH_MUSIC_M4A_OR_WAV
    if not os.path.exists(UPLOADED_MUSIC_M4A):
        raise FileNotFoundError(f"Missing uploaded music file: {UPLOADED_MUSIC_M4A}")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to decode uploaded .m4a music")
    os.makedirs(os.path.dirname(SCRATCH_MUSIC_WAV), exist_ok=True)
    subprocess.run(
        [ffmpeg, "-y", "-i", UPLOADED_MUSIC_M4A, "-ac", "1", "-ar", str(SAMPLE_RATE), SCRATCH_MUSIC_WAV, "-loglevel", "error"],
        check=True,
    )
    return SCRATCH_MUSIC_WAV


def synth_fly_buzz(sr: int = SAMPLE_RATE) -> np.ndarray:
    """Gentle, warm, low-volume loopable fly buzz (never harsh/buzzy)."""
    dur = 1.60
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / sr
    rng = np.random.default_rng(505)
    tau = 2.0 * np.pi
    buzz = np.zeros(n, dtype=np.float32)
    for f_base, fm_hz, ph0, amp in [(182.0, 2.0 / dur, 0.0, 0.50), (206.0, 3.0 / dur, 1.4, 0.36)]:
        lfo = np.sin(tau * fm_hz * t + ph0)
        inst_f = f_base * (1.0 + 0.07 * lfo)
        ph = np.cumsum(tau * inst_f / sr)
        frac = (ph / tau) % 1.0
        pulse = np.exp(-((frac - 0.5) / 0.14) ** 2) - 0.16
        gain = 0.4 + 0.6 * (0.5 + 0.5 * np.cos(tau * fm_hz * t + ph0))
        buzz += amp * pulse * gain
    air = _bandpass(rng.normal(0.0, 1.0, n).astype(np.float32), sr, 600.0, 2200.0, order=2) * 0.08
    return _master_warm(
        buzz + air,
        sr,
        hp_hz=180.0,
        lp_hz=2300.0,
        notch_hz=None,
        target_rms=0.055,
        peak_cap=0.26,
        fade_in_s=0.04,
        fade_out_s=0.04,
        drive=1.1,
    )


def build_all_audio(out_dir: str | None = None) -> Dict[str, str]:
    """Build & warm-master all Poop Gun audio clips into `work/audio/*.wav`."""
    audio_dir = out_dir or os.path.join(WORK_DIR, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    # Remove stale old-synth files no longer used
    for old_name in ("scream_1.wav", "woo.wav", "haha.wav", "yah.wav"):
        old_p = os.path.join(audio_dir, old_name)
        if os.path.exists(old_p):
            os.remove(old_p)

    outputs: Dict[str, str] = {}

    # 1. Wew Cannon windup (`wc_charge.wav`) — smooth pitch rise without shrill whine
    w_arr, sr = _read_wav_mono(WINDUP_SRC)
    w_m = _master_warm(
        w_arr,
        sr,
        hp_hz=90.0,
        lp_hz=3400.0,
        notch_hz=2650.0,
        notch_mix=0.52,
        target_rms=0.135,
        peak_cap=0.55,
        fade_in_s=0.025,
        fade_out_s=0.040,
        drive=1.25,
    )
    dest_w = os.path.join(audio_dir, "windup_wew.wav")
    _write_wav_mono(dest_w, w_m, sr)
    outputs["windup_wew"] = dest_w

    # 2. Real workspace fart blasts — juicy low-end punch, de-clipped & warm
    for key, src_path in FART_SOURCES.items():
        f_arr, sr = _read_wav_mono(src_path)
        f_m = _master_warm(
            f_arr,
            sr,
            hp_hz=38.0,
            lp_hz=3300.0,
            notch_hz=2400.0,
            notch_mix=0.38,
            target_rms=0.195,
            peak_cap=0.70,
            fade_in_s=0.012,
            fade_out_s=0.065,
            drive=1.35,
        )
        dest = os.path.join(audio_dir, f"{key}.wav")
        _write_wav_mono(dest, f_m, sr)
        outputs[key] = dest

    # 3. Projectile yells — funny, clear, and softened against harsh shrill peaks
    for key, src_path in YELL_SOURCES.items():
        y_arr, sr = _read_wav_mono(src_path)
        # Trim slight leading/trailing silence (<1.5% peak)
        pk = float(np.max(np.abs(y_arr))) + 1e-6
        nz = np.where(np.abs(y_arr) > 0.02 * pk)[0]
        if len(nz) > 200:
            pad0 = max(0, int(nz[0]) - int(0.02 * sr))
            pad1 = min(len(y_arr), int(nz[-1]) + int(0.04 * sr))
            y_arr = y_arr[pad0:pad1]
        y_m = _master_warm(
            y_arr,
            sr,
            hp_hz=120.0,
            lp_hz=3800.0,
            notch_hz=2750.0,
            notch_mix=0.48,
            target_rms=0.140,
            peak_cap=0.56,
            fade_in_s=0.015,
            fade_out_s=0.080,
            drive=1.20,
        )
        dest = os.path.join(audio_dir, f"{key}.wav")
        _write_wav_mono(dest, y_m, sr)
        outputs[key] = dest

    # 4. User-uploaded Bhangra track (`Mundian To Bach Ke` chorus hook 37.15s..48.45s)
    music_wav = _ensure_music_wav()
    m_raw, sr = _read_wav_mono(music_wav)
    i0 = int(round(37.15 * sr))
    i1 = min(len(m_raw), int(round(48.45 * sr)))
    m_seg = m_raw[i0:i1]
    m_m = _master_warm(
        m_seg,
        sr,
        hp_hz=65.0,
        lp_hz=4100.0,
        notch_hz=2850.0,
        notch_mix=0.40,
        target_rms=0.125,
        peak_cap=0.50,
        fade_in_s=0.030,
        fade_out_s=0.120,
        drive=1.18,
    )
    dest_m = os.path.join(audio_dir, "proj_music.wav")
    _write_wav_mono(dest_m, m_m, sr)
    outputs["proj_music"] = dest_m

    # 5. Mud impact splat (from `beach_uncle/mud_explode.wav`, warm & weighty)
    spl_arr, sr = _read_wav_mono(MUD_SPLAT_SRC)
    spl_m = _master_warm(
        spl_arr,
        sr,
        hp_hz=45.0,
        lp_hz=3200.0,
        notch_hz=2500.0,
        notch_mix=0.42,
        target_rms=0.170,
        peak_cap=0.62,
        fade_in_s=0.008,
        fade_out_s=0.065,
        drive=1.28,
    )
    dest_s = os.path.join(audio_dir, "mud_splat.wav")
    _write_wav_mono(dest_s, spl_m, sr)
    outputs["mud_splat"] = dest_s

    # 6. Subtle background fly buzz
    dest_f = os.path.join(audio_dir, "fly_buzz.wav")
    _write_wav_mono(dest_f, synth_fly_buzz(SAMPLE_RATE), SAMPLE_RATE)
    outputs["fly_buzz"] = dest_f

    # 7. Three distinct India + Fart + Poop Windup & Fire Vote Packs (warm-mastered)
    vote_clips = build_vote_sound_packs(sr=SAMPLE_RATE, music_raw=m_raw)
    for k, arr in vote_clips.items():
        dest_v = os.path.join(audio_dir, f"{k}.wav")
        _write_wav_mono(dest_v, arr, SAMPLE_RATE)
        outputs[k] = dest_v

    return outputs


def _place(dst: np.ndarray, src: np.ndarray, start_s: float, sr: int, gain: float = 1.0, fade_in_s: float = 0.008, fade_out_s: float = 0.025) -> None:
    if len(src) < 4:
        return
    i0 = max(0, int(round(start_s * sr)))
    if i0 >= len(dst):
        return
    seg = _apply_fades(src.astype(np.float32), sr, fade_in_s, fade_out_s) * float(gain)
    n = min(len(seg), len(dst) - i0)
    dst[i0:i0 + n] += seg[:n]


def _pitch_sweep(src: np.ndarray, rate_start: float, rate_end: float, out_len: int) -> np.ndarray:
    rates = np.linspace(rate_start, rate_end, max(2, out_len), dtype=np.float64)
    pos = np.cumsum(rates) - rates[0]
    src_len = max(1, len(src))
    idx = np.mod(pos, float(src_len))
    x_grid = np.arange(src_len, dtype=np.float64)
    return np.interp(idx, x_grid, src.astype(np.float64)).astype(np.float32)


def _stomach_bubbles(dur_s: float, sr: int, seed: int = 42, intensity_ramp: bool = True) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(round(dur_s * sr))
    out = np.zeros(n, dtype=np.float32)
    t_marks = np.linspace(0.05, max(0.2, dur_s - 0.14), 13)
    for idx, ts in enumerate(t_marks):
        ts_j = float(np.clip(ts + rng.uniform(-0.035, 0.035), 0.0, dur_s - 0.12))
        b_dur = float(rng.uniform(0.06, 0.11))
        bn = int(b_dur * sr)
        tt = np.arange(bn, dtype=np.float32) / sr
        f0 = float(rng.uniform(95.0, 210.0)) * (1.0 + 0.35 * (idx / len(t_marks)))
        f1 = f0 * float(rng.uniform(1.55, 2.35))
        ph = 2.0 * np.pi * np.cumsum(np.linspace(f0, f1, bn) / sr)
        env = np.sin(np.pi * tt / b_dur) * np.exp(-3.2 * tt / b_dur)
        amp = (0.35 + 0.65 * (idx / len(t_marks))) if intensity_ramp else 0.75
        _place(out, (np.sin(ph) * env).astype(np.float32), ts_j, sr, gain=amp * 0.45, fade_in_s=0.004, fade_out_s=0.012)
    # Warm low brown-noise slosh
    noise = _bandpass(rng.normal(0.0, 1.0, n).astype(np.float32), sr, 65.0, 420.0, order=2)
    slosh_env = np.linspace(0.25, 1.0, n, dtype=np.float32) if intensity_ramp else np.ones(n, dtype=np.float32)
    out += noise * slosh_env * 0.18
    return out


def _pungi_swell(dur_s: float, sr: int) -> np.ndarray:
    """Warm nasal snake-charmer reed drone climbing in pitch cleanly without harshness."""
    n = int(round(dur_s * sr))
    t = np.arange(n, dtype=np.float32) / sr
    prog = np.linspace(0.0, 1.0, n, dtype=np.float32)
    vib = 0.018 * np.sin(2.0 * np.pi * 6.5 * t)
    f_inst = (146.8 * (1.0 + 0.50 * (prog ** 1.25)) * (1.0 + vib)).astype(np.float64)
    ph = 2.0 * np.pi * np.cumsum(f_inst / sr)
    reed = (0.62 * np.sin(ph) + 0.28 * np.sin(2.0 * ph + 0.4) + 0.14 * np.sin(3.0 * ph)) * (0.35 + 0.65 * prog)
    drone = 0.30 * np.sin(2.0 * np.pi * 146.8 * t + 0.15 * np.sin(2.0 * np.pi * 4.5 * t))
    return _bandpass((reed + drone).astype(np.float32), sr, 120.0, 2100.0, order=2)


def _sub_thump(dur_s: float, sr: int, f_start: float = 95.0, f_end: float = 38.0) -> np.ndarray:
    n = int(round(dur_s * sr))
    t = np.arange(n, dtype=np.float32) / sr
    freq = f_end + (f_start - f_end) * np.exp(-9.0 * t)
    ph = 2.0 * np.pi * np.cumsum(freq.astype(np.float64) / sr)
    env = np.exp(-4.8 * t)
    return (np.sin(ph) * env).astype(np.float32)


def _sitar_twang(dur_s: float, sr: int, base_hz: float = 130.8, bend_end: float = 1.65) -> np.ndarray:
    """Warm plucked Indian sitar drone with sympathetic buzz climbing cleanly."""
    n = int(round(dur_s * sr))
    t = np.arange(n, dtype=np.float32) / sr
    prog = np.linspace(0.0, 1.0, n, dtype=np.float32)
    freq = base_hz * (1.0 + (bend_end - 1.0) * (prog ** 1.35))
    ph = 2.0 * np.pi * np.cumsum(freq.astype(np.float64) / sr)
    # Jawari-like warm overtones fading softly above 2.5 kHz
    sig = (
        0.55 * np.sin(ph)
        + 0.30 * np.sin(2.0 * ph + 0.35)
        + 0.16 * np.sin(3.0 * ph + 0.7)
        + 0.08 * np.sin(4.0 * ph)
    ) * (0.45 + 0.55 * prog) * (0.75 + 0.25 * np.sin(2.0 * np.pi * 5.0 * t))
    return _bandpass(sig.astype(np.float32), sr, 100.0, 2400.0, order=2)


def build_vote_sound_packs(sr: int, music_raw: np.ndarray) -> Dict[str, np.ndarray]:
    """Synthesize & master 6 distinct India + Fart + Poop windup/fire audio pairs."""
    def _load(path: str) -> np.ndarray:
        arr, _ = _read_wav_mono(path)
        return arr

    wew = _load(WINDUP_SRC)
    mega_fart = _load(FART_SOURCES["fart_1"])
    shoot_fart = _load(FART_SOURCES["fart_2"])
    pop_fart = _load(FART_SOURCES["fart_3"])
    raw_fart = _load(FART_SOURCES["fart_4"])
    funny_f1 = _load(EXTRA_SOURCES["funny_fart1"])
    funny_f2 = _load(EXTRA_SOURCES["funny_fart2"])
    tiny_fart = _load(EXTRA_SOURCES["tiny_fart"])
    goopop = _load(EXTRA_SOURCES["goopop"])
    goosplat = _load(EXTRA_SOURCES["goosplat"])
    goofire = _load(EXTRA_SOURCES["goofire"])
    goostick = _load(EXTRA_SOURCES["goostick"])
    mud_expl = _load(MUD_SPLAT_SRC)
    mud_hit = _load(EXTRA_SOURCES["mud_hit"])
    burp = _load(EXTRA_SOURCES["burp"])
    pain_beer = _load(EXTRA_SOURCES["pain_beer"])
    tuktuk = _load(EXTRA_SOURCES["tuktuk"])
    bike_bell = _load(EXTRA_SOURCES["bike_bell"])
    slide_whistle = _load(EXTRA_SOURCES["slide_whistle"])
    bloop = _load(EXTRA_SOURCES["bloop"])
    sad_trombone = _load(EXTRA_SOURCES["sad_trombone"])
    vine_boom = _load(EXTRA_SOURCES["vine_boom"])
    squat_thud = _load(EXTRA_SOURCES["squat_thud"])
    heh_fart = _load(EXTRA_SOURCES["heh_fart"])
    wheel_wobble = _load(EXTRA_SOURCES["wheel_wobble"])
    uncle_yell = _load(EXTRA_SOURCES["yell_4"])

    # Clean slices from the user's Bhangra track
    tumbi_riff = music_raw[int(0.08 * sr):int(3.20 * sr)]
    dhol_drop = music_raw[int(6.20 * sr):int(9.40 * sr)]
    dhol_hit = music_raw[int(6.20 * sr):int(6.62 * sr)]
    hook_drop = music_raw[int(37.15 * sr):int(40.40 * sr)]

    out: Dict[str, np.ndarray] = {}

    # ------------------------------------------------------------------
    # PACK 1: "Tumbi Bubble & Mega Wet Ripper"
    # ------------------------------------------------------------------
    w1_len = int(1.50 * sr)
    w1 = np.zeros(w1_len, dtype=np.float32)
    tumbi_up = _pitch_sweep(tumbi_riff, 0.96, 1.44, w1_len)
    _place(w1, _bandpass(tumbi_up, sr, 240.0, 3100.0, order=2), 0.0, sr, gain=0.68, fade_in_s=0.03, fade_out_s=0.04)
    _place(w1, _stomach_bubbles(1.50, sr, seed=101, intensity_ramp=True), 0.0, sr, gain=0.85, fade_in_s=0.02, fade_out_s=0.03)
    _place(w1, wew[:min(len(wew), w1_len)], 0.0, sr, gain=0.35, fade_in_s=0.03, fade_out_s=0.04)
    out["windup_v1"] = _master_warm(w1, sr, hp_hz=75.0, lp_hz=3200.0, notch_hz=2600.0, notch_mix=0.48, target_rms=0.135, peak_cap=0.54, fade_in_s=0.025, fade_out_s=0.045, drive=1.22)

    f1 = np.zeros(int(1.45 * sr), dtype=np.float32)
    mf_deep = _pitch_sweep(mega_fart, 0.94, 0.86, len(mega_fart))
    _place(f1, _bandpass(dhol_hit, sr, 50.0, 2600.0, order=2), 0.0, sr, gain=0.72, fade_in_s=0.005, fade_out_s=0.06)
    _place(f1, _sub_thump(0.32, sr, 105.0, 40.0), 0.0, sr, gain=0.75, fade_in_s=0.004, fade_out_s=0.05)
    _place(f1, mf_deep, 0.03, sr, gain=1.00, fade_in_s=0.008, fade_out_s=0.08)
    _place(f1, mud_expl, 0.07, sr, gain=0.62, fade_in_s=0.01, fade_out_s=0.06)
    _place(f1, goosplat, 0.20, sr, gain=0.58, fade_in_s=0.01, fade_out_s=0.05)
    _place(f1, uncle_yell[:min(len(uncle_yell), int(0.85 * sr))], 0.14, sr, gain=0.40, fade_in_s=0.02, fade_out_s=0.12)
    out["fire_v1"] = _master_warm(f1, sr, hp_hz=40.0, lp_hz=3100.0, notch_hz=2450.0, notch_mix=0.42, target_rms=0.195, peak_cap=0.66, fade_in_s=0.010, fade_out_s=0.070, drive=1.30)

    # ------------------------------------------------------------------
    # PACK 2: "Dhol Plunger Pump & Tuk-Tuk Brass Toot"
    # ------------------------------------------------------------------
    w2_len = int(1.50 * sr)
    w2 = np.zeros(w2_len, dtype=np.float32)
    dhol_accel = _pitch_sweep(dhol_drop, 0.92, 1.52, w2_len)
    _place(w2, _bandpass(dhol_accel, sr, 70.0, 2900.0, order=2), 0.0, sr, gain=0.72, fade_in_s=0.025, fade_out_s=0.04)
    for k, ts in enumerate([0.12, 0.48, 0.78, 1.04]):
        gp = _pitch_sweep(goopop, 0.84 + 0.12 * k, 0.95 + 0.12 * k, len(goopop))
        _place(w2, gp, ts, sr, gain=0.58 + 0.12 * k, fade_in_s=0.006, fade_out_s=0.025)
    _place(w2, tiny_fart, 1.24, sr, gain=0.78, fade_in_s=0.006, fade_out_s=0.025)
    out["windup_v2"] = _master_warm(w2, sr, hp_hz=70.0, lp_hz=3100.0, notch_hz=2550.0, notch_mix=0.45, target_rms=0.135, peak_cap=0.55, fade_in_s=0.020, fade_out_s=0.045, drive=1.24)

    f2 = np.zeros(int(1.35 * sr), dtype=np.float32)
    honk_seg = _bandpass(tuktuk[:min(len(tuktuk), int(0.34 * sr))], sr, 240.0, 2600.0, order=2)
    _place(f2, honk_seg, 0.0, sr, gain=0.62, fade_in_s=0.006, fade_out_s=0.045)
    _place(f2, _sub_thump(0.30, sr, 92.0, 36.0), 0.04, sr, gain=0.78, fade_in_s=0.004, fade_out_s=0.05)
    _place(f2, _pitch_sweep(funny_f1, 0.98, 0.82, len(funny_f1)), 0.08, sr, gain=0.95, fade_in_s=0.008, fade_out_s=0.05)
    _place(f2, shoot_fart, 0.24, sr, gain=0.85, fade_in_s=0.010, fade_out_s=0.06)
    _place(f2, mud_hit, 0.56, sr, gain=0.75, fade_in_s=0.008, fade_out_s=0.05)
    out["fire_v2"] = _master_warm(f2, sr, hp_hz=42.0, lp_hz=3000.0, notch_hz=2400.0, notch_mix=0.46, target_rms=0.195, peak_cap=0.66, fade_in_s=0.010, fade_out_s=0.075, drive=1.32)

    # ------------------------------------------------------------------
    # PACK 3: "Pungi Belly-Rumble & Sloppy Stutter Cannon"
    # ------------------------------------------------------------------
    w3_len = int(1.50 * sr)
    w3 = np.zeros(w3_len, dtype=np.float32)
    _place(w3, _pungi_swell(1.50, sr), 0.0, sr, gain=0.68, fade_in_s=0.04, fade_out_s=0.05)
    _place(w3, _bandpass(_pitch_sweep(burp, 0.88, 1.15, int(0.85 * sr)), sr, 60.0, 1800.0, order=2), 0.14, sr, gain=0.65, fade_in_s=0.015, fade_out_s=0.05)
    _place(w3, _stomach_bubbles(1.50, sr, seed=303, intensity_ramp=True), 0.0, sr, gain=0.78, fade_in_s=0.02, fade_out_s=0.03)
    _place(w3, _pitch_sweep(funny_f2, 0.90, 1.25, len(funny_f2)), 1.16, sr, gain=0.68, fade_in_s=0.006, fade_out_s=0.03)
    out["windup_v3"] = _master_warm(w3, sr, hp_hz=65.0, lp_hz=2800.0, notch_hz=2200.0, notch_mix=0.45, target_rms=0.135, peak_cap=0.54, fade_in_s=0.025, fade_out_s=0.045, drive=1.22)

    f3 = np.zeros(int(1.50 * sr), dtype=np.float32)
    _place(f3, funny_f2, 0.00, sr, gain=0.76, fade_in_s=0.006, fade_out_s=0.02)
    _place(f3, tiny_fart, 0.16, sr, gain=0.76, fade_in_s=0.006, fade_out_s=0.02)
    _place(f3, _sub_thump(0.38, sr, 88.0, 34.0), 0.28, sr, gain=0.82, fade_in_s=0.005, fade_out_s=0.06)
    _place(f3, pop_fart, 0.28, sr, gain=0.92, fade_in_s=0.008, fade_out_s=0.06)
    _place(f3, _pitch_sweep(raw_fart, 0.90, 0.72, len(raw_fart)), 0.42, sr, gain=0.78, fade_in_s=0.01, fade_out_s=0.08)
    _place(f3, mud_expl, 0.34, sr, gain=0.55, fade_in_s=0.01, fade_out_s=0.07)
    _place(f3, goosplat, 0.72, sr, gain=0.55, fade_in_s=0.01, fade_out_s=0.06)
    out["fire_v3"] = _master_warm(f3, sr, hp_hz=38.0, lp_hz=3000.0, notch_hz=2350.0, notch_mix=0.45, target_rms=0.195, peak_cap=0.67, fade_in_s=0.010, fade_out_s=0.080, drive=1.32)

    # ------------------------------------------------------------------
    # PACK 4: "Rickshaw Sitar Stretch & Toilet Flush Bomb"
    # ------------------------------------------------------------------
    w4_len = int(1.50 * sr)
    w4 = np.zeros(w4_len, dtype=np.float32)
    _place(w4, _sitar_twang(1.50, sr, base_hz=123.5, bend_end=1.75), 0.0, sr, gain=0.66, fade_in_s=0.03, fade_out_s=0.05)
    for idx, ts in enumerate([0.10, 0.56, 0.94, 1.18]):
        bell_soft = _bandpass(bike_bell, sr, 420.0, 2700.0, order=2)
        _place(w4, _pitch_sweep(bell_soft, 0.88 + 0.08 * idx, 0.92 + 0.08 * idx, int(0.32 * sr)), ts, sr, gain=0.42, fade_in_s=0.008, fade_out_s=0.04)
    _place(w4, _bandpass(_pitch_sweep(slide_whistle, 0.82, 1.32, int(0.9 * sr)), sr, 240.0, 2400.0, order=2), 0.55, sr, gain=0.42, fade_in_s=0.02, fade_out_s=0.04)
    _place(w4, goostick, 0.96, sr, gain=0.65, fade_in_s=0.01, fade_out_s=0.04)
    out["windup_v4"] = _master_warm(w4, sr, hp_hz=75.0, lp_hz=2900.0, notch_hz=2300.0, notch_mix=0.48, target_rms=0.135, peak_cap=0.54, fade_in_s=0.025, fade_out_s=0.045, drive=1.22)

    f4 = np.zeros(int(1.50 * sr), dtype=np.float32)
    _place(f4, _sub_thump(0.42, sr, 98.0, 34.0), 0.0, sr, gain=0.85, fade_in_s=0.005, fade_out_s=0.06)
    _place(f4, _pitch_sweep(mega_fart, 0.85, 0.72, len(mega_fart)), 0.02, sr, gain=0.95, fade_in_s=0.008, fade_out_s=0.07)
    _place(f4, squat_thud, 0.14, sr, gain=0.72, fade_in_s=0.008, fade_out_s=0.06)
    _place(f4, mud_expl, 0.22, sr, gain=0.62, fade_in_s=0.01, fade_out_s=0.06)
    _place(f4, _pitch_sweep(bloop, 0.92, 1.18, len(bloop)), 0.92, sr, gain=0.75, fade_in_s=0.006, fade_out_s=0.03)
    out["fire_v4"] = _master_warm(f4, sr, hp_hz=38.0, lp_hz=2950.0, notch_hz=2350.0, notch_mix=0.44, target_rms=0.195, peak_cap=0.66, fade_in_s=0.010, fade_out_s=0.080, drive=1.32)

    # ------------------------------------------------------------------
    # PACK 5: "Bhangra Hook Strain & Brass Fart Trombone"
    # ------------------------------------------------------------------
    w5_len = int(1.50 * sr)
    w5 = np.zeros(w5_len, dtype=np.float32)
    hook_rise = _pitch_sweep(hook_drop, 0.92, 1.28, w5_len)
    _place(w5, _bandpass(hook_rise, sr, 180.0, 2900.0, order=2), 0.0, sr, gain=0.68, fade_in_s=0.025, fade_out_s=0.04)
    _place(w5, _bandpass(pain_beer, sr, 120.0, 2300.0, order=2), 0.18, sr, gain=0.68, fade_in_s=0.02, fade_out_s=0.06)
    _place(w5, _pitch_sweep(tiny_fart, 1.05, 1.38, len(tiny_fart)), 0.85, sr, gain=0.70, fade_in_s=0.006, fade_out_s=0.02)
    _place(w5, _pitch_sweep(funny_f2, 1.05, 1.32, len(funny_f2)), 1.12, sr, gain=0.75, fade_in_s=0.006, fade_out_s=0.03)
    out["windup_v5"] = _master_warm(w5, sr, hp_hz=70.0, lp_hz=3000.0, notch_hz=2450.0, notch_mix=0.46, target_rms=0.135, peak_cap=0.54, fade_in_s=0.025, fade_out_s=0.045, drive=1.24)

    f5 = np.zeros(int(1.50 * sr), dtype=np.float32)
    _place(f5, _bandpass(dhol_hit, sr, 45.0, 2400.0, order=2), 0.0, sr, gain=0.72, fade_in_s=0.005, fade_out_s=0.05)
    _place(f5, goofire, 0.02, sr, gain=0.65, fade_in_s=0.006, fade_out_s=0.04)
    _place(f5, _pitch_sweep(funny_f1, 0.94, 0.78, len(funny_f1)), 0.05, sr, gain=0.95, fade_in_s=0.008, fade_out_s=0.05)
    _place(f5, _bandpass(_pitch_sweep(sad_trombone, 0.90, 0.76, int(0.95 * sr)), sr, 75.0, 2200.0, order=2), 0.25, sr, gain=0.72, fade_in_s=0.02, fade_out_s=0.08)
    _place(f5, goosplat, 0.42, sr, gain=0.58, fade_in_s=0.01, fade_out_s=0.05)
    out["fire_v5"] = _master_warm(f5, sr, hp_hz=40.0, lp_hz=2900.0, notch_hz=2300.0, notch_mix=0.46, target_rms=0.195, peak_cap=0.66, fade_in_s=0.010, fade_out_s=0.080, drive=1.30)

    # ------------------------------------------------------------------
    # PACK 6: "Fast Tabla Wobble & Street-Food Rocket Shart"
    # ------------------------------------------------------------------
    w6_len = int(1.50 * sr)
    w6 = np.zeros(w6_len, dtype=np.float32)
    # Rapid Punjabi tabla/dhol chops accelerating toward launch
    tabla_hit = _bandpass(dhol_drop[:int(0.28 * sr)], sr, 80.0, 2800.0, order=2)
    for idx, ts in enumerate([0.04, 0.34, 0.60, 0.82, 1.00, 1.15, 1.28, 1.38]):
        _place(w6, tabla_hit[:int(0.16 * sr)], ts, sr, gain=0.48 + 0.06 * idx, fade_in_s=0.005, fade_out_s=0.025)
    _place(w6, _bandpass(_pitch_sweep(wheel_wobble, 0.92, 1.35, int(1.25 * sr)), sr, 85.0, 2200.0, order=2), 0.12, sr, gain=0.55, fade_in_s=0.02, fade_out_s=0.04)
    _place(w6, _stomach_bubbles(1.50, sr, seed=606, intensity_ramp=True), 0.0, sr, gain=0.70, fade_in_s=0.02, fade_out_s=0.03)
    out["windup_v6"] = _master_warm(w6, sr, hp_hz=68.0, lp_hz=2950.0, notch_hz=2400.0, notch_mix=0.46, target_rms=0.135, peak_cap=0.54, fade_in_s=0.020, fade_out_s=0.045, drive=1.24)

    f6 = np.zeros(int(1.45 * sr), dtype=np.float32)
    short_toot = _bandpass(tuktuk[:int(0.14 * sr)], sr, 280.0, 2400.0, order=2)
    _place(f6, short_toot, 0.00, sr, gain=0.58, fade_in_s=0.005, fade_out_s=0.02)
    _place(f6, short_toot, 0.11, sr, gain=0.52, fade_in_s=0.005, fade_out_s=0.025)
    _place(f6, _bandpass(vine_boom[:int(0.55 * sr)], sr, 42.0, 1400.0, order=2), 0.16, sr, gain=0.68, fade_in_s=0.006, fade_out_s=0.07)
    _place(f6, heh_fart, 0.18, sr, gain=0.92, fade_in_s=0.008, fade_out_s=0.06)
    _place(f6, shoot_fart, 0.42, sr, gain=0.78, fade_in_s=0.008, fade_out_s=0.06)
    _place(f6, mud_hit, 0.68, sr, gain=0.72, fade_in_s=0.008, fade_out_s=0.05)
    _place(f6, goopop, 0.92, sr, gain=0.62, fade_in_s=0.006, fade_out_s=0.04)
    out["fire_v6"] = _master_warm(f6, sr, hp_hz=38.0, lp_hz=2950.0, notch_hz=2350.0, notch_mix=0.45, target_rms=0.195, peak_cap=0.66, fade_in_s=0.010, fade_out_s=0.075, drive=1.32)

    return out


if __name__ == "__main__":
    out_map = build_all_audio()
    for k, p in out_map.items():
        with wave.open(p, "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            sr = wf.getframerate()
            arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            dur = len(arr) / float(sr)
            rms = float(np.sqrt(np.mean(arr ** 2)))
            pk = float(np.max(np.abs(arr)))
            print(f"[poop_audio] {k:12s}.wav: dur={dur:5.2f}s rms={rms:.3f} pk={pk:.3f} ({os.path.getsize(p)} B)")
