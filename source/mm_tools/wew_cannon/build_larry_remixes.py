r"""Builds 70 hilarious custom Larry + Gun sound remixes for the Woo / Wheelman Cannon:
  - 18 Wind-Up / Charge-Up mixes (`rmx_chg_*`): accelerating WEW stutters, funny echo tunnels,
    reverse vacuum sucks, choir arpeggios, robot coils, slow-to-hyper speedups (~1.50-1.60 s)
  - 14 Blast-Off / Gun Shot mixes (`rmx_sht_*`): 155mm cannon, choir WEW, twin double-barrel,
    slow-mo monster, chipmunk blast, DJ scratch, canyon echoes (~1.25-1.65 s)
  - 18 Flying Scream Medleys (`rmx_scr_*`): "screaming a bunch of Larry stuff" mid-flight,
    2x speedruns, slow-mo demons, yo-yo speed rollercoasters, DJ scratches (~2.4-3.8 s)
  - 10 Boom Explosion Remixes (`rmx_boom_*`): sub-bass detonations + slow-mo/hyper/choir shouts (~2.0-2.7 s)
  - 10 Dance / Runner Remixes (`rmx_run_*`): wacky speed-up/slow-down/DJ/wobble runner loops (~1.9-2.8 s)

Outputs 22050 Hz mono 16-bit PCM WAVs to:
  - sound/larry_remixes/*.wav
  - source/sound_bank/larry_remixes/manifest.json
"""
import json
import subprocess
import tempfile
import wave
from pathlib import Path
import numpy as np

SR = 22050
HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
MOD_ROOT = MM_TOOLS.parent.parent

TG_WAV = MOD_ROOT / "sound" / "larry_telegram"
MC_WAV = MOD_ROOT / "source" / "sound_bank" / "larry_mccart_clips"
RS_WAV = MOD_ROOT / "source" / "sound_bank" / "random_sounds"

OUT_DIR = MOD_ROOT / "sound" / "larry_remixes"
BANK_META_DIR = MOD_ROOT / "source" / "sound_bank" / "larry_remixes"

rng = np.random.default_rng(20261120)


def n_of(sec: float) -> int:
    return max(1, int(round(sec * SR)))


def load_wav_mono(path: Path) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tmp = Path(tf.name)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(tmp)],
            check=True,
        )
        with wave.open(str(tmp), "rb") as w:
            return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
    finally:
        if tmp.exists():
            tmp.unlink()


def trim_silence(x: np.ndarray, thr: float = 0.05) -> np.ndarray:
    a = np.abs(x)
    pk = float(a.max())
    if pk < 1e-6:
        return x
    idx = np.nonzero(a > thr * pk)[0]
    if not len(idx):
        return x
    return x[max(0, int(idx[0]) - n_of(0.015)):min(len(x), int(idx[-1]) + n_of(0.04))]


def fft_band(x: np.ndarray, lo_hz: float = 0.0, hi_hz: float = 11025.0) -> np.ndarray:
    if len(x) < 4:
        return x
    n = len(x)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    spec = np.fft.rfft(x)
    mask = np.ones_like(freqs)
    if lo_hz > 0:
        mask *= np.clip((freqs - lo_hz * 0.7) / max(1.0, lo_hz * 0.6), 0.0, 1.0)
    if hi_hz < SR * 0.49:
        mask *= np.clip((hi_hz * 1.25 - freqs) / max(1.0, hi_hz * 0.5), 0.0, 1.0)
    return np.fft.irfft(spec * mask, n=n)


def norm(x: np.ndarray, peak: float = 0.88) -> np.ndarray:
    x = x - np.mean(x)
    m = float(np.max(np.abs(x)))
    return x * (peak / m) if m > 1e-7 else x


def clean_voice(x: np.ndarray) -> np.ndarray:
    x = x - np.mean(x)
    x = trim_silence(x, 0.05)
    x = fft_band(x, 150.0, 7600.0)
    x = x + 0.55 * fft_band(x, 1800.0, 4000.0)
    rms = float(np.sqrt(np.mean(x ** 2))) + 1e-9
    k = 2.6 * rms
    x = np.tanh(x / k) * k
    return norm(x, 0.90)


def fade(x: np.ndarray, fin: float = 0.005, fout: float = 0.025) -> np.ndarray:
    y = x.copy()
    na, nr = min(len(y), n_of(fin)), min(len(y), n_of(fout))
    if na > 1:
        y[:na] *= np.linspace(0.0, 1.0, na)
    if nr > 1:
        y[-nr:] *= np.linspace(1.0, 0.0, nr)
    return y


def warp_pitch(x: np.ndarray, rate0: float, rate1: float, dur: float | None = None) -> np.ndarray:
    if dur is None:
        dur = len(x) / SR / max(0.1, 0.5 * (rate0 + rate1))
    n = n_of(dur)
    rates = np.linspace(rate0, rate1, n)
    pos = np.cumsum(rates)
    return np.interp(pos, np.arange(len(x)), x, right=0.0)


def slice_sec(x: np.ndarray, t0: float, t1: float) -> np.ndarray:
    i0 = max(0, min(len(x), n_of(t0)))
    i1 = max(i0 + 1, min(len(x), n_of(t1)))
    return fade(x[i0:i1], 0.006, 0.015)


def place(out: np.ndarray, x: np.ndarray, at_sec: float, gain: float = 1.0) -> None:
    i = max(0, n_of(at_sec))
    if i >= len(out):
        return
    m = min(len(x), len(out) - i)
    out[i:i + m] += x[:m] * gain


def add_echo(x: np.ndarray, delays_gains: list[tuple[float, float]], band=(320.0, 3400.0)) -> np.ndarray:
    extra = max(d for d, _ in delays_gains) + 0.1
    out = np.zeros(len(x) + n_of(extra), dtype=np.float64)
    out[:len(x)] += x
    wet = fft_band(x, band[0], band[1])
    for d, g in delays_gains:
        place(out, wet, d, g)
    return out


def robotize(x: np.ndarray, mod_hz: float = 78.0, mix: float = 0.72) -> np.ndarray:
    t = np.arange(len(x)) / SR
    car = 0.7 * np.sin(2.0 * np.pi * mod_hz * t) + 0.3 * np.sign(np.sin(2.0 * np.pi * mod_hz * t))
    wet = fft_band(x * car, 250.0, 5200.0) * 1.4
    return x * (1.0 - mix) + wet * mix


def choir_stack(x: np.ndarray, ratios: tuple[float, ...] = (0.78, 1.0, 1.26)) -> np.ndarray:
    out = np.zeros(int(len(x) / min(ratios)) + 32, dtype=np.float64)
    for r in ratios:
        w = warp_pitch(x, r, r)
        place(out, w, 0.0, 1.0 / len(ratios) * 1.65)
    return trim_silence(out, 0.02)


def wobble_pitch(x: np.ndarray, base_rate: float = 1.0, lfo_hz: float = 9.0, depth: float = 0.12) -> np.ndarray:
    n = int(len(x) / base_rate)
    t = np.arange(n) / SR
    rate = base_rate + depth * np.sin(2.0 * np.pi * lfo_hz * t)
    pos = np.cumsum(np.maximum(0.25, rate))
    return np.interp(pos, np.arange(len(x)), x, right=0.0)


def yoyo_speed(x: np.ndarray, dur: float, r_min: float = 0.62, r_max: float = 1.85, cycles: float = 2.0) -> np.ndarray:
    n = n_of(dur)
    t = np.arange(n) / SR
    u = t / dur
    rate = 0.5 * (r_min + r_max) - 0.5 * (r_max - r_min) * np.cos(2.0 * np.pi * cycles * u)
    pos = np.cumsum(rate) % max(1, len(x) - 1)
    return np.interp(pos, np.arange(len(x)), x, right=0.0)


def dj_scratch(seg: np.ndarray, hits: int = 4) -> np.ndarray:
    """Forward -> quick reverse rewind -> forward vinyl scratch."""
    piece = fade(seg[:min(len(seg), n_of(0.24))], 0.004, 0.008)
    rev = warp_pitch(piece[::-1], 1.35, 1.55)
    fwd = warp_pitch(piece, 1.15, 1.35)
    out = []
    for i in range(hits):
        out.append(fwd if i % 2 == 0 else rev)
    return np.concatenate(out)


def stutter_tail(x: np.ndarray, tail_sec: float = 0.20, repeats: int = 5, step_sec: float = 0.13, pitch_step: float = 0.06) -> np.ndarray:
    tail = slice_sec(x, max(0.0, len(x) / SR - tail_sec - 0.05), len(x) / SR)
    dur = len(x) / SR + repeats * step_sec + 0.15
    out = np.zeros(n_of(dur), dtype=np.float64)
    place(out, x, 0.0, 1.0)
    t0 = max(0.0, len(x) / SR - 0.06)
    for i in range(repeats):
        r = 1.0 + i * pitch_step
        place(out, warp_pitch(tail, r, r), t0 + i * step_sec, 0.90 * (0.88 ** i))
    return trim_silence(out, 0.015)


def turbine_whine(dur: float = 1.55) -> np.ndarray:
    t = np.arange(n_of(dur)) / SR
    u = t / dur
    f = 170.0 * (1050.0 / 170.0) ** (u ** 1.35)
    ph = np.cumsum(2.0 * np.pi * f / SR)
    y = 0.50 * np.sin(ph) + 0.25 * np.sin(2.0 * ph) + 0.14 * np.sin(3.0 * ph)
    air = fft_band(rng.standard_normal(len(t)), 600.0, 3200.0) * (0.12 + 0.35 * (u ** 1.5))
    ticks = np.zeros_like(t)
    t_tick, step = 0.05, 0.18
    while t_tick < dur - 0.04:
        tk = np.arange(n_of(0.025)) / SR
        click = np.sin(2 * np.pi * (1600 + 1800 * (t_tick / dur)) * tk) * np.exp(-tk / 0.004)
        place(ticks, click, t_tick, 0.35)
        t_tick += step
        step = max(0.038, step * 0.86)
    env = np.minimum(1.0, t / 0.06) * (0.28 + 0.72 * (u ** 1.1))
    return (y * 0.32 + air + ticks) * env


def laser_whine(dur: float = 1.55) -> np.ndarray:
    t = np.arange(n_of(dur)) / SR
    u = t / dur
    f = 240.0 * (2200.0 / 240.0) ** (u ** 1.6)
    fm = 0.35 * np.sin(2 * np.pi * (14 + 35 * u) * t)
    ph = np.cumsum(2.0 * np.pi * f * (1.0 + 0.08 * fm) / SR)
    return np.sin(ph) * (0.18 + 0.42 * u) * np.minimum(1.0, t / 0.04)


def cannon_thump(dur: float = 0.85, f0: float = 155.0, f1: float = 32.0) -> np.ndarray:
    t = np.arange(n_of(dur)) / SR
    f = f0 * (f1 / f0) ** ((t / dur) ** 0.45)
    sub = np.sin(np.cumsum(2.0 * np.pi * f / SR)) * np.exp(-t / 0.17)
    noise = fft_band(rng.standard_normal(len(t)), 80.0, 1900.0) * np.exp(-t / 0.11)
    ring = (np.sin(2 * np.pi * 620 * t) + 0.5 * np.sin(2 * np.pi * 1380 * t)) * np.exp(-t / 0.20) * 0.18
    return np.tanh((sub * 1.1 + noise * 0.65 + ring) * 1.25) * np.minimum(1.0, t / 0.003)


def laser_zap(dur: float = 0.55) -> np.ndarray:
    t = np.arange(n_of(dur)) / SR
    f = 2400.0 * (120.0 / 2400.0) ** ((t / dur) ** 0.35)
    y = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t / 0.13)
    return np.tanh(y * 1.6) * 0.85


def boom_bed(dur: float = 2.0) -> np.ndarray:
    t = np.arange(n_of(dur)) / SR
    sub = np.sin(np.cumsum(2 * np.pi * (110.0 * (24.0 / 110.0) ** ((t / dur) ** 0.35)) / SR)) * np.exp(-t / 0.48)
    n = rng.standard_normal(len(t))
    lo = fft_band(n, 45.0, 220.0) * np.exp(-t / 0.52)
    mid = fft_band(n, 220.0, 1400.0) * np.exp(-t / 0.24)
    hi = fft_band(n, 1400.0, 6500.0) * np.exp(-t / 0.10)
    return np.tanh((sub * 0.95 + lo * 0.9 + mid * 0.6 + hi * 0.35) * 1.25) * np.minimum(1.0, t / 0.004)


def wind_rush(dur: float) -> np.ndarray:
    t = np.arange(n_of(dur)) / SR
    n = rng.standard_normal(len(t))
    lo = fft_band(n, 180.0, 1400.0) * 0.24
    hi = fft_band(n, 1200.0, 4200.0) * 0.14
    env = np.sin(np.pi * np.clip(t / dur, 0.0, 1.0)) ** 0.55
    return (lo + hi) * env


def chain_clips(parts: list[tuple[np.ndarray, float, float, float]], total_dur: float) -> np.ndarray:
    out = np.zeros(n_of(total_dur), dtype=np.float64)
    for x, at, rate, gain in parts:
        w = warp_pitch(x, rate, rate) if abs(rate - 1.0) > 1e-3 else x
        place(out, fade(w, 0.005, 0.025), at, gain)
    return out


def save_wav(path: Path, x: np.ndarray) -> float:
    path.parent.mkdir(parents=True, exist_ok=True)
    y = norm(fade(x, 0.004, 0.03), 0.90)
    pcm = np.clip(np.round(y * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return len(pcm) / SR


def main():
    # Remove old remix WAVs so clean rebuild
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.wav"):
        old.unlink()

    # Load source building blocks
    wewe = clean_voice(load_wav_mono(RS_WAV / "wewe.wav"))
    eweewew = clean_voice(load_wav_mono(RS_WAV / "eweewew.wav"))
    oooowew = clean_voice(load_wav_mono(RS_WAV / "oooooooewewewewew.wav"))
    quakewew = clean_voice(load_wav_mono(RS_WAV / "quakeahhwewew.wav"))

    feels_wew = clean_voice(load_wav_mono(TG_WAV / "it_feels_so_good_wew.wav"))
    wew_tail = slice_sec(feels_wew, 1.55, 2.65)
    wew3 = clean_voice(load_wav_mono(TG_WAV / "wewwewwew.wav"))
    gowewd = clean_voice(load_wav_mono(TG_WAV / "gowewd.wav"))
    ilovethatecho = clean_voice(load_wav_mono(TG_WAV / "ilovethatecho.wav"))
    oh_i_love_it = clean_voice(load_wav_mono(TG_WAV / "oh_i_love_it.wav"))
    who_are_you = clean_voice(load_wav_mono(TG_WAV / "who_are_youuuuuuu.wav"))
    thats_dbl = clean_voice(load_wav_mono(TG_WAV / "thats_double_good.wav"))
    ur_dbl = clean_voice(load_wav_mono(TG_WAV / "youredoublegood.wav"))
    quad_good = clean_voice(load_wav_mono(TG_WAV / "youre_so_good_quad_good.wav"))
    it_wont_boot = clean_voice(load_wav_mono(TG_WAV / "it_wont_boot.wav"))
    reformat = clean_voice(load_wav_mono(TG_WAV / "should_i_reformat.wav"))
    oh_winme = clean_voice(load_wav_mono(TG_WAV / "oh_windows_me.wav"))
    no_win97 = clean_voice(load_wav_mono(TG_WAV / "i_dont_use_windows_97.wav"))
    winheh = clean_voice(load_wav_mono(TG_WAV / "windowsheh.wav"))
    ahlarry = clean_voice(load_wav_mono(TG_WAV / "ahlarry.wav"))
    johnny = clean_voice(load_wav_mono(TG_WAV / "johnnnny.wav"))
    oh_wow = clean_voice(load_wav_mono(TG_WAV / "larry_oh_wow.wav"))
    bounce = clean_voice(load_wav_mono(TG_WAV / "larry_i_can_bounce_around_for_you.wav"))
    wobble = clean_voice(load_wav_mono(TG_WAV / "larry_i_can_wobble_for_you.wav"))

    dbl_mc = clean_voice(load_wav_mono(MC_WAV / "double_good.wav"))
    octo_mc = clean_voice(load_wav_mono(MC_WAV / "octogood.wav"))
    banana = clean_voice(load_wav_mono(MC_WAV / "banana_cannon.wav"))
    love_quake = clean_voice(load_wav_mono(MC_WAV / "love_to_play_quake.wav"))
    giggle = clean_voice(load_wav_mono(MC_WAV / "giggle_hacks.wav"))
    womanly = clean_voice(load_wav_mono(MC_WAV / "womanly_man.wav"))
    win_me_long = clean_voice(load_wav_mono(MC_WAV / "windows_me_you_ha.wav"))
    dbl_click = clean_voice(load_wav_mono(MC_WAV / "should_i_double_click.wav"))
    another_menu = clean_voice(load_wav_mono(MC_WAV / "another_menu.wav"))
    c_folder = clean_voice(load_wav_mono(MC_WAV / "my_c_folder.wav"))
    commutes = clean_voice(load_wav_mono(MC_WAV / "computer_commutes.wav"))
    dollar = clean_voice(load_wav_mono(MC_WAV / "yesterday_i_made_a_dollar.wav"))

    specs = []

    # =========================================================================
    # 1. WIND-UP / CHARGE MIXES (14 clips, ~1.50-1.60s)
    # =========================================================================
    # 1: WEW-WEW-WEW Gun Turbine Spool
    y = np.zeros(n_of(1.52))
    place(y, turbine_whine(1.52), 0.0, 0.72)
    t_cur, dt_step = 0.02, 0.24
    for idx in range(9):
        rate = 0.92 + idx * 0.075
        seg = slice_sec(wewe if idx % 2 == 0 else wew_tail, 0.0, 0.26)
        place(y, warp_pitch(seg, rate, rate + 0.05), t_cur, 0.75 + idx * 0.04)
        t_cur += dt_step
        dt_step = max(0.085, dt_step * 0.84)
    specs.append(("rmx_chg_wew_turbine", "charge", "Wind-Up 01: WEW-WEW-WEW Gun Turbine Spool", ["wew", "remix"], y))

    # 2: Funny Echo Tunnel
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.48)
    place(y, warp_pitch(slice_sec(ilovethatecho, 0.0, 0.85), 1.02, 1.15), 0.0, 0.85)
    wew_hit = warp_pitch(slice_sec(wewe, 0.0, 0.42), 1.05, 1.32)
    for at, g in [(0.68, 0.90), (0.85, 0.65), (0.99, 0.50), (1.11, 0.42), (1.21, 0.36), (1.30, 0.30)]:
        place(y, warp_pitch(wew_hit, 1.0 + (at - 0.68) * 0.4, 1.05 + (at - 0.68) * 0.4), at, g)
    specs.append(("rmx_chg_echo_tunnel", "charge", "Wind-Up 02: Funny Echo Tunnel (I Love That Echo -> WEW!)", ["wew", "remix"], y))

    # 3: Double -> Quad -> Octogood Escalator
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.55)
    place(y, warp_pitch(dbl_mc, 1.05, 1.08), 0.02, 0.90)
    place(y, warp_pitch(slice_sec(quad_good, 1.25, 2.35), 1.12, 1.22), 0.48, 0.95)
    place(y, warp_pitch(slice_sec(octo_mc, 0.10, 1.10), 1.18, 1.36), 0.96, 1.05)
    specs.append(("rmx_chg_double_octo_ramp", "charge", "Wind-Up 03: Double Good -> Quad Good -> Octogood!", ["double_good", "remix"], y))

    # 4: It Feels So Good... WEW! Overdrive Coil
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.62)
    v = warp_pitch(slice_sec(feels_wew, 0.0, 2.35), 1.15, 1.48, dur=1.50)
    place(y, add_echo(v, [(0.11, 0.30), (0.22, 0.16)])[:n_of(1.55)], 0.02, 0.92)
    specs.append(("rmx_chg_feels_so_good_coil", "charge", "Wind-Up 04: It Feels So Good... WEW! Overdrive Coil", ["wew", "double_good", "remix"], y))

    # 5: Gowewd! Mechanical Crank-Up
    y = np.zeros(n_of(1.52))
    place(y, turbine_whine(1.52), 0.0, 0.60)
    for at, r, g in [(0.02, 0.96, 0.80), (0.38, 1.08, 0.85), (0.70, 1.20, 0.92), (0.98, 1.32, 1.00), (1.22, 1.44, 1.05)]:
        place(y, warp_pitch(slice_sec(gowewd, 0.0, 0.45), r, r + 0.05), at, g)
    specs.append(("rmx_chg_gowewd_ratchet", "charge", "Wind-Up 05: Gowewd! Mechanical Crank-Up", ["wew", "remix"], y))

    # 6: Quake + Banana Cannon + WEW!
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.55)
    place(y, warp_pitch(slice_sec(love_quake, 0.0, 1.05), 1.15, 1.22), 0.02, 0.88)
    place(y, warp_pitch(slice_sec(banana, 0.15, 1.20), 1.18, 1.35), 0.65, 0.95)
    place(y, warp_pitch(slice_sec(wewe, 0.0, 0.45), 1.28, 1.45), 1.18, 0.95)
    specs.append(("rmx_chg_banana_quake", "charge", "Wind-Up 06: Love To Play Quake + Banana Cannon + WEW!", ["wew", "remix"], y))

    # 7: Reverse Vacuum Ghost-WEW Suck-In
    y = np.zeros(n_of(1.55))
    place(y, laser_whine(1.55), 0.0, 0.58)
    rev = add_echo(wew_tail, [(0.12, 0.55), (0.24, 0.35), (0.36, 0.22)])[::-1]
    rev = warp_pitch(rev, 1.2, 0.85, dur=1.08) * np.linspace(0.2, 1.0, n_of(1.08))
    place(y, rev, 0.02, 0.95)
    place(y, warp_pitch(slice_sec(wewe, 0.0, 0.48), 1.18, 1.38), 1.08, 1.05)
    specs.append(("rmx_chg_reverse_suck_wew", "charge", "Wind-Up 07: Reverse Ghost-Suck -> WEW! Snap", ["wew", "remix"], y))

    # 8: WEW! Arcade Fanfare Arpeggio
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.45)
    syl = slice_sec(wewe, 0.0, 0.30)
    for at, ratio in [(0.02, 0.89), (0.26, 1.00), (0.48, 1.12), (0.70, 1.26), (0.92, 1.41), (1.14, 1.59)]:
        place(y, warp_pitch(syl, ratio, ratio), at, 0.95)
    specs.append(("rmx_chg_wew_arpeggio", "charge", "Wind-Up 08: WEW! Musical Arcade Power-Up Scale", ["wew", "remix"], y))

    # 9: Cyber-Robot Larry Coil
    y = np.zeros(n_of(1.55))
    place(y, laser_whine(1.55), 0.0, 0.65)
    place(y, robotize(warp_pitch(slice_sec(oh_winme, 0.0, 0.95), 1.08, 1.25), 74.0, 0.80), 0.03, 0.92)
    place(y, robotize(warp_pitch(slice_sec(wew_tail, 0.0, 0.65), 1.15, 1.45), 96.0, 0.78), 0.88, 1.00)
    specs.append(("rmx_chg_cyber_robot_wew", "charge", "Wind-Up 09: Cyber-Robot Larry (Windows ME -> WEW!)", ["wew", "remix"], y))

    # 10: Ping-Pong Bouncing-Ball Double Good
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.45)
    dg_syl = slice_sec(dbl_mc, 0.0, 0.55)
    at, step, r = 0.02, 0.30, 1.0
    for _ in range(9):
        if at >= 1.42:
            break
        place(y, warp_pitch(dg_syl, r, r + 0.03), at, 0.88)
        at += step
        step = max(0.065, step * 0.76)
        r += 0.06
    specs.append(("rmx_chg_pingpong_doublegood", "charge", "Wind-Up 10: Bouncing-Ball Ping-Pong Double Good!", ["double_good", "remix"], y))

    # 11: Gatling Giggle-Hacks + WEW!
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.52)
    gh_bit = slice_sec(giggle, 0.0, 0.20)
    for k in range(6):
        place(y, warp_pitch(gh_bit, 1.0 + k * 0.08, 1.05 + k * 0.08), 0.04 + k * 0.14, 0.92)
    place(y, warp_pitch(slice_sec(wew_tail, 0.0, 0.60), 1.18, 1.38), 0.92, 1.02)
    specs.append(("rmx_chg_gatling_giggle_wew", "charge", "Wind-Up 11: Gatling Giggle-Hacks -> WEW!", ["wew", "remix"], y))

    # 12: Monster-to-Chipmunk Quad Good!
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.50)
    v = warp_pitch(slice_sec(quad_good, 0.0, 2.50), 0.72, 1.62, dur=1.50)
    place(y, v, 0.02, 1.02)
    specs.append(("rmx_chg_monster_chipmunk_quad", "charge", "Wind-Up 12: Slow-Mo Monster -> Chipmunk Quad Good!", ["double_good", "remix"], y))

    # 13: Who Are You Siren Climb
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.62)
    v = warp_pitch(slice_sec(who_are_you, 0.35, 2.10), 0.95, 1.55, dur=1.45)
    place(y, add_echo(v, [(0.12, 0.32)])[:n_of(1.55)], 0.03, 0.95)
    specs.append(("rmx_chg_who_are_you_siren", "charge", "Wind-Up 13: WHO ARE YOUUUUU Siren Climb", ["remix"], y))

    # 14: Confused IT Meltdown Wind-Up
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.52)
    place(y, warp_pitch(slice_sec(it_wont_boot, 0.0, 0.75), 1.25, 1.30), 0.02, 0.92)
    place(y, warp_pitch(slice_sec(reformat, 0.0, 0.85), 1.30, 1.38), 0.58, 0.95)
    place(y, warp_pitch(slice_sec(wewe, 0.0, 0.38), 1.25, 1.45), 1.18, 1.00)
    specs.append(("rmx_chg_it_meltdown", "charge", "Wind-Up 14: It Won't Boot! Reformat?! WEW!", ["wew", "remix"], y))

    # 15: Slow 0.62x Giant -> 1.85x Hyper Chipmunk "DOUBLE GOOD!"
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.50)
    place(y, warp_pitch(slice_sec(thats_dbl, 0.10, 0.75), 0.62, 0.70), 0.02, 0.95)
    for k, at in enumerate([0.62, 0.84, 1.04, 1.22, 1.36]):
        r = 1.45 + k * 0.12
        place(y, warp_pitch(slice_sec(dbl_mc, 0.0, 0.52), r, r), at, 0.92)
    specs.append(("rmx_chg_slow_to_chipmunk_dbl", "charge", "Wind-Up 15: Slow-Mo Giant -> 1.9x Chipmunk DOUBLE GOOD!", ["double_good", "remix"], y))

    # 16: Cassette Rewind-Scratch -> Fast-Forward WEW!
    y = np.zeros(n_of(1.55))
    place(y, laser_whine(1.55), 0.0, 0.45)
    place(y, dj_scratch(wew_tail, hits=4), 0.03, 0.92)
    place(y, warp_pitch(slice_sec(feels_wew, 0.0, 1.80), 1.65, 2.05, dur=0.72), 0.78, 1.02)
    specs.append(("rmx_chg_dj_scratch_wew", "charge", "Wind-Up 16: DJ Scratch -> 2x Fast-Forward WEW!", ["wew", "remix"], y))

    # 17: Dying Cassette Slowdown ("Gowewd... ewwwwwd...")
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.42)
    v = warp_pitch(slice_sec(gowewd, 0.0, 1.15), 1.35, 0.46, dur=1.48)
    place(y, add_echo(v, [(0.15, 0.30)])[:n_of(1.55)], 0.02, 0.98)
    specs.append(("rmx_chg_tape_slowdown_gowewd", "charge", "Wind-Up 17: Tape-Die Slowdown (Fast -> 0.46x GOWEWWWWD)", ["wew", "remix"], y))

    # 18: 2x Speedrun Tech-Panic Wind-Up
    y = np.zeros(n_of(1.55))
    place(y, turbine_whine(1.55), 0.0, 0.50)
    place(y, warp_pitch(it_wont_boot, 1.75, 1.80), 0.02, 0.92)
    place(y, warp_pitch(no_win97, 1.80, 1.85), 0.48, 0.94)
    place(y, warp_pitch(wewe, 1.55, 1.85), 1.08, 1.00)
    specs.append(("rmx_chg_2x_speedrun_panic", "charge", "Wind-Up 18: 1.8x Speedrun (It Won't Boot + Win97 + WEW!)", ["wew", "remix"], y))

    # =========================================================================
    # 2. BLAST-OFF / SHOOT MIXES (10 clips, ~1.25-1.50s)
    # =========================================================================
    # 1: 155mm Cannon + WEW!
    y = np.zeros(n_of(1.35))
    place(y, cannon_thump(0.85), 0.0, 1.05)
    place(y, add_echo(warp_pitch(slice_sec(wew_tail, 0.0, 0.85), 0.96, 0.92), [(0.14, 0.34), (0.28, 0.16)]), 0.03, 0.95)
    specs.append(("rmx_sht_wew_cannon", "shoot", "Gun Shot 01: 155mm Cannon Blast + WEW!!! (Echo)", ["wew", "remix"], y))

    # 2: Double Good Heavy Mortar
    y = np.zeros(n_of(1.35))
    place(y, cannon_thump(0.80), 0.0, 1.00)
    place(y, add_echo(warp_pitch(dbl_mc, 0.94, 0.94), [(0.13, 0.30)]), 0.04, 0.98)
    specs.append(("rmx_sht_double_good_boom", "shoot", "Gun Shot 02: Double Good! Heavy Mortar Blast", ["double_good", "remix"], y))

    # 3: Banana Cannon Launch
    y = np.zeros(n_of(1.40))
    place(y, cannon_thump(0.75), 0.0, 0.95)
    place(y, add_echo(slice_sec(banana, 0.15, 1.20), [(0.14, 0.32)]), 0.04, 0.98)
    specs.append(("rmx_sht_banana_cannon", "shoot", "Gun Shot 03: Banana Cannon! Pneumatic Launch", ["remix"], y))

    # 4: Gowewd Downrange Echo Shot
    y = np.zeros(n_of(1.35))
    place(y, cannon_thump(0.75), 0.0, 0.95)
    place(y, add_echo(slice_sec(gowewd, 0.0, 0.90), [(0.15, 0.40), (0.30, 0.22), (0.45, 0.12)]), 0.04, 0.95)
    specs.append(("rmx_sht_gowewd_echo", "shoot", "Gun Shot 04: Gowewd! Downrange Echo Shot", ["wew", "remix"], y))

    # 5: 4-Larry Barbershop Choir WEW! Cannon
    y = np.zeros(n_of(1.45))
    place(y, cannon_thump(0.85, 140.0, 28.0), 0.0, 1.05)
    ch = choir_stack(slice_sec(wew_tail, 0.0, 0.78), (0.75, 0.95, 1.15, 1.38))
    place(y, add_echo(ch, [(0.15, 0.32)]), 0.03, 1.00)
    specs.append(("rmx_sht_wew_choir_cannon", "shoot", "Gun Shot 05: 4-Larry Choir WEW! Artillery Blast", ["wew", "remix"], y))

    # 6: Twin Double-Barrel "Thats Double Good!"
    y = np.zeros(n_of(1.45))
    place(y, cannon_thump(0.60, 165.0, 42.0), 0.0, 0.95)
    place(y, cannon_thump(0.75, 145.0, 32.0), 0.18, 1.00)
    place(y, add_echo(slice_sec(thats_dbl, 0.25, 1.30), [(0.15, 0.28)]), 0.04, 0.98)
    specs.append(("rmx_sht_twin_double_good", "shoot", "Gun Shot 06: Twin Double-Barrel (That's Double Good!)", ["double_good", "remix"], y))

    # 7: Cyber-Laser "I Love That Echo!" Shot
    y = np.zeros(n_of(1.45))
    place(y, laser_zap(0.60), 0.0, 0.95)
    place(y, add_echo(robotize(slice_sec(ilovethatecho, 0.0, 1.05), 82.0, 0.55), [(0.13, 0.44), (0.26, 0.26), (0.39, 0.14)]), 0.04, 0.96)
    specs.append(("rmx_sht_cyber_echo_shot", "shoot", "Gun Shot 07: Cyber-Laser (I Love That Echo!)", ["remix"], y))

    # 8: Reverse Pre-Punch + "Oh I Love It! WEW!"
    y = np.zeros(n_of(1.50))
    pre = cannon_thump(0.28, 120.0, 40.0)[::-1] * 0.65
    place(y, pre, 0.0, 0.85)
    place(y, cannon_thump(0.85, 150.0, 30.0), 0.22, 1.08)
    place(y, add_echo(chain_clips([(oh_i_love_it, 0.0, 1.05, 0.95), (wew_tail, 0.55, 1.02, 0.95)], 1.25), [(0.14, 0.30)]), 0.22, 0.95)
    specs.append(("rmx_sht_reverse_love_wew", "shoot", "Gun Shot 08: Vacuum-Snap Mortar (Oh I Love It! WEW!)", ["wew", "remix"], y))

    # 9: Supersonic Octogood Canyon Shot
    y = np.zeros(n_of(1.45))
    place(y, cannon_thump(0.80, 175.0, 34.0), 0.0, 1.00)
    place(y, add_echo(warp_pitch(slice_sec(octo_mc, 0.08, 1.15), 0.92, 0.90), [(0.16, 0.42), (0.32, 0.24), (0.48, 0.12)]), 0.03, 1.02)
    specs.append(("rmx_sht_octogood_canyon", "shoot", "Gun Shot 09: Supersonic OCTOGOOD! Canyon Shot", ["double_good", "remix"], y))

    # 10: Bass-Drop "Ah Larry! WEW!"
    y = np.zeros(n_of(1.40))
    place(y, cannon_thump(0.90, 130.0, 26.0), 0.0, 1.10)
    place(y, add_echo(chain_clips([(ahlarry, 0.0, 1.02, 0.95), (wewe, 0.42, 1.04, 0.98)], 1.15), [(0.14, 0.32)]), 0.04, 0.96)
    specs.append(("rmx_sht_ah_larry_wew", "shoot", "Gun Shot 10: Mega-Bass (Ah Larry! WEW!)", ["wew", "remix"], y))

    # 11: Slow-Mo 0.58x Monster "GOWEWD!" + High Echo
    y = np.zeros(n_of(1.70))
    place(y, cannon_thump(0.95, 115.0, 24.0), 0.0, 1.10)
    slow_g = warp_pitch(slice_sec(gowewd, 0.0, 0.85), 0.58, 0.58)
    place(y, add_echo(slow_g, [(0.18, 0.35), (0.36, 0.18)]), 0.03, 1.00)
    place(y, warp_pitch(slice_sec(wewe, 0.0, 0.42), 1.75, 1.75), 0.95, 0.72)
    specs.append(("rmx_sht_slomo_monster_gowewd", "shoot", "Gun Shot 11: 0.58x Slow-Mo Monster GOWEWD! + Chipmunk Echo", ["wew", "remix"], y))

    # 12: 1.8x Hyper-Speed "WEW-WEW-DOUBLE-GOOD!" Shot
    y = np.zeros(n_of(1.25))
    place(y, cannon_thump(0.70, 180.0, 38.0), 0.0, 1.00)
    fast_v = chain_clips([(wewe, 0.0, 1.75, 0.95), (dbl_mc, 0.32, 1.65, 1.00)], 1.05)
    place(y, add_echo(fast_v, [(0.11, 0.34), (0.22, 0.16)]), 0.03, 0.98)
    specs.append(("rmx_sht_hyper_wew_dbl", "shoot", "Gun Shot 12: 1.7x Hyper-Speed WEW-DOUBLE-GOOD! Blast", ["wew", "double_good", "remix"], y))

    # 13: DJ Scratch Shot ("WEW-wikki-WEW!")
    y = np.zeros(n_of(1.35))
    place(y, cannon_thump(0.80, 150.0, 32.0), 0.0, 1.05)
    place(y, add_echo(dj_scratch(wew_tail, hits=5), [(0.13, 0.30)]), 0.04, 0.98)
    specs.append(("rmx_sht_dj_scratch_wew", "shoot", "Gun Shot 13: DJ Vinyl Scratch WEW-wikki-WEW! Cannon", ["wew", "remix"], y))

    # 14: Broken-Record Stutter "Gowewd-ewd-ewd-ewd!"
    y = np.zeros(n_of(1.65))
    place(y, cannon_thump(0.80, 155.0, 30.0), 0.0, 1.02)
    place(y, stutter_tail(slice_sec(gowewd, 0.0, 0.72), tail_sec=0.16, repeats=6, step_sec=0.12, pitch_step=0.07), 0.04, 0.98)
    specs.append(("rmx_sht_stutter_gowewd", "shoot", "Gun Shot 14: Broken-Record Stutter GOWEWD-ewd-ewd!", ["wew", "remix"], y))

    # =========================================================================
    # 3. FLYING SCREAM MEDLEYS (12 clips, ~2.8-3.7s)
    # =========================================================================
    v = chain_clips([(slice_sec(wew3, 0.0, 1.25), 0.0, 1.08, 0.95), (slice_sec(who_are_you, 0.35, 1.95), 1.05, 1.12, 1.00)], 2.70)
    y = add_echo(v, [(0.15, 0.35), (0.31, 0.18)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.70)
    specs.append(("rmx_scr_wew_who_are_you", "scream", "Flying Scream 01: WEW-WEW-WEW! WHO ARE YOUUUUUU?!", ["wew", "remix"], y))

    v = chain_clips([(slice_sec(ilovethatecho, 0.0, 1.15), 0.0, 1.06, 0.92), (slice_sec(oh_i_love_it, 0.0, 0.78), 0.92, 1.10, 0.95), (slice_sec(feels_wew, 0.05, 1.35), 1.52, 1.12, 1.00)], 2.85)
    y = add_echo(v, [(0.14, 0.42), (0.28, 0.24), (0.42, 0.12)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.65)
    specs.append(("rmx_scr_echo_feels_good", "scream", "Flying Scream 02: I Love That Echo! Oh I Love It! WEW!", ["wew", "double_good", "remix"], y))

    v = chain_clips([(dbl_mc, 0.0, 1.06, 0.95), (slice_sec(ur_dbl, 0.0, 0.95), 0.65, 1.12, 0.95), (slice_sec(quad_good, 1.15, 2.35), 1.45, 1.15, 1.00), (slice_sec(octo_mc, 0.10, 1.15), 2.30, 1.18, 1.05)], 3.25)
    y = add_echo(v, [(0.13, 0.30), (0.26, 0.14)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.65)
    specs.append(("rmx_scr_double_quad_octo", "scream", "Flying Scream 03: Double Good -> Quad Good -> Octogood!", ["double_good", "remix"], y))

    v = chain_clips([(slice_sec(it_wont_boot, 0.0, 0.85), 0.0, 1.12, 0.95), (slice_sec(oh_winme, 0.0, 1.05), 0.72, 1.10, 0.95), (slice_sec(reformat, 0.0, 1.10), 1.55, 1.15, 0.95), (slice_sec(winheh, 0.0, 0.55), 2.48, 1.18, 0.95)], 3.00)
    y = add_echo(v, [(0.15, 0.30)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.68)
    specs.append(("rmx_scr_windows_panic", "scream", "Flying Scream 04: It Won't Boot! Oh Windows ME! Reformat?!", ["remix"], y))

    v = chain_clips([(slice_sec(bounce, 0.0, 1.35), 0.0, 1.10, 0.95), (slice_sec(wobble, 0.0, 1.15), 1.15, 1.12, 0.95), (slice_sec(giggle, 0.0, 0.95), 2.10, 1.14, 1.00)], 2.95)
    y = add_echo(v, [(0.14, 0.32)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.65)
    specs.append(("rmx_scr_bounce_wobble_giggle", "scream", "Flying Scream 05: Bounce Around! Wobble! Giggle Hacks!", ["remix"], y))

    v = chain_clips([(slice_sec(love_quake, 0.0, 1.10), 0.0, 1.08, 0.95), (slice_sec(banana, 0.10, 1.25), 0.90, 1.12, 0.95), (slice_sec(quakewew, 0.0, 1.45), 1.80, 1.05, 1.00)], 3.15)
    y = add_echo(v, [(0.15, 0.34), (0.30, 0.16)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.65)
    specs.append(("rmx_scr_quake_banana_wew", "scream", "Flying Scream 06: Play Quake! Banana Cannon! Quake-Ahh-Wew!", ["wew", "remix"], y))

    v = chain_clips([(slice_sec(eweewew, 0.0, 1.15), 0.0, 1.12, 0.95), (slice_sec(oooowew, 0.0, 1.30), 0.95, 1.10, 0.98), (slice_sec(gowewd, 0.0, 0.95), 2.05, 1.08, 1.00)], 2.95)
    y = add_echo(v, [(0.13, 0.36), (0.26, 0.18)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.68)
    specs.append(("rmx_scr_unhinged_ewew", "scream", "Flying Scream 07: Eweewew! Ooooooewewew! Gowewd!", ["wew", "remix"], y))

    v = chain_clips([(slice_sec(ahlarry, 0.0, 0.70), 0.0, 1.08, 0.95), (slice_sec(johnny, 0.0, 0.80), 0.55, 1.10, 0.95), (slice_sec(oh_wow, 0.0, 0.85), 1.20, 1.12, 0.95), (slice_sec(thats_dbl, 0.30, 1.35), 1.90, 1.10, 1.00)], 2.90)
    y = add_echo(v, [(0.14, 0.32), (0.28, 0.15)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.65)
    specs.append(("rmx_scr_oh_wow_johnny", "scream", "Flying Scream 08: Ah Larry! Johnny! Oh Wow! Double Good!", ["double_good", "remix"], y))

    # 9: Cyber-Robot Flying Rant
    v = chain_clips([(slice_sec(no_win97, 0.0, 1.15), 0.0, 1.12, 0.95), (slice_sec(commutes, 0.0, 1.35), 1.00, 1.15, 0.95), (slice_sec(wewe, 0.0, 0.65), 2.22, 1.10, 1.00)], 2.95)
    y = add_echo(robotize(v, 76.0, 0.65), [(0.14, 0.35), (0.28, 0.18)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.68)
    specs.append(("rmx_scr_cyber_win97_commutes", "scream", "Flying Scream 09: Cyber-Robot (Windows 97 + Computer Commutes + WEW!)", ["wew", "remix"], y))

    # 10: Choir of Larrys Screaming WEW & Quad Good
    v = chain_clips([(slice_sec(feels_wew, 0.0, 1.85), 0.0, 1.06, 0.95), (slice_sec(quad_good, 0.85, 2.30), 1.65, 1.10, 1.00)], 3.15)
    y = add_echo(choir_stack(v, (0.82, 1.02, 1.25)), [(0.15, 0.34), (0.30, 0.16)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.62)
    specs.append(("rmx_scr_choir_feels_quad", "scream", "Flying Scream 10: Larry Choir (It Feels So Good WEW! + Quad Good!)", ["wew", "double_good", "remix"], y))

    # 11: Ping-Pong Canyon Echo Chaos
    v = chain_clips([(slice_sec(gowewd, 0.0, 0.95), 0.0, 1.06, 0.95), (dbl_mc, 0.85, 1.10, 0.95), (slice_sec(oh_wow, 0.0, 0.90), 1.55, 1.12, 0.95), (slice_sec(wewe, 0.0, 0.75), 2.25, 1.15, 1.00)], 2.95)
    y = add_echo(v, [(0.12, 0.48), (0.24, 0.32), (0.36, 0.20), (0.48, 0.11)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.60)
    specs.append(("rmx_scr_canyon_gowewd_dbl", "scream", "Flying Scream 11: Canyon Echo (Gowewd! Double Good! Oh Wow! WEW!)", ["wew", "double_good", "remix"], y))

    # 12: IT Menu Meltdown Flying
    v = chain_clips([(slice_sec(dbl_click, 0.0, 0.95), 0.0, 1.12, 0.95), (slice_sec(another_menu, 0.0, 1.05), 0.82, 1.14, 0.95), (slice_sec(c_folder, 0.0, 1.15), 1.72, 1.15, 0.95), (slice_sec(wewe, 0.0, 0.55), 2.68, 1.20, 1.00)], 3.20)
    y = add_echo(v, [(0.14, 0.32)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.66)
    specs.append(("rmx_scr_it_menu_meltdown", "scream", "Flying Scream 12: Double Click?! Another Menu?! My C Folder?! WEW!", ["wew", "double_good", "remix"], y))

    # 13: 2x Speedrun Everything-At-Once Flying Scream
    v = chain_clips([
        (it_wont_boot, 0.0, 1.75, 0.95),
        (oh_winme, 0.48, 1.75, 0.95),
        (reformat, 1.05, 1.80, 0.95),
        (thats_dbl, 1.65, 1.65, 0.98),
        (wew_tail, 2.28, 1.55, 1.02),
    ], 2.95)
    y = add_echo(v, [(0.12, 0.32), (0.24, 0.15)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.62)
    specs.append(("rmx_scr_2x_speedrun_everything", "scream", "Flying Scream 13: 1.8x Speedrun (Boot! WinME! Reformat! Double Good! WEW!)", ["wew", "double_good", "remix"], y))

    # 14: Slow-Mo 0.58x Giant Demon Flying Scream ("IT FEELS SO GOOOOD... WEEEWWWW")
    v = warp_pitch(slice_sec(feels_wew, 0.0, 2.20), 0.58, 0.62, dur=3.55)
    y = add_echo(v, [(0.20, 0.42), (0.40, 0.22)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.60)
    specs.append(("rmx_scr_slomo_demon_feels_wew", "scream", "Flying Scream 14: 0.58x Slow-Mo Demon (IT FEELS SO GOOOOD... WEW!)", ["wew", "double_good", "remix"], y))

    # 15: Yo-Yo Speed Rollercoaster ("Quad Good -> WEW!")
    src_yoyo = chain_clips([(slice_sec(quad_good, 0.60, 2.40), 0.0, 1.0, 0.95), (wewe, 1.60, 1.0, 1.0)], 2.50)
    v = yoyo_speed(src_yoyo, dur=3.10, r_min=0.60, r_max=1.85, cycles=2.5)
    y = add_echo(v, [(0.14, 0.34)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.62)
    specs.append(("rmx_scr_yoyo_rollercoaster", "scream", "Flying Scream 15: Yo-Yo Speed Rollercoaster (0.6x <-> 1.85x Quad Good + WEW!)", ["wew", "double_good", "remix"], y))

    # 16: Drunk-to-Chipmunk Rocket Acceleration (0.65x -> 1.95x!)
    src_acc = chain_clips([(gowewd, 0.0, 1.0, 0.95), (thats_dbl, 1.15, 1.0, 0.95), (wew3, 2.20, 1.0, 1.0)], 3.40)
    v = warp_pitch(src_acc, 0.65, 1.95, dur=2.90)
    y = add_echo(v, [(0.13, 0.32), (0.26, 0.14)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.65)
    specs.append(("rmx_scr_drunk_to_chipmunk", "scream", "Flying Scream 16: Slow-0.65x -> 1.95x Chipmunk Rocket!", ["wew", "double_good", "remix"], y))

    # 17: Polyrhythm 3-Speed Larry Choir (Slow + Normal + Fast ALL at once!)
    v = chain_clips([(ur_dbl, 0.0, 1.0, 0.95), (wew_tail, 1.50, 1.0, 1.0)], 2.45)
    poly = choir_stack(v, (0.62, 1.00, 1.68))
    y = add_echo(poly, [(0.15, 0.35), (0.30, 0.16)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.58)
    specs.append(("rmx_scr_3speed_polyrhythm", "scream", "Flying Scream 17: 3-Speed Choir (0.62x + 1.0x + 1.68x Double Good + WEW!)", ["wew", "double_good", "remix"], y))

    # 18: UFO Alien Vibrato Warble Scream
    v = wobble_pitch(chain_clips([(who_are_you, 0.0, 1.05, 0.95), (eweewew, 1.50, 1.15, 0.98)], 2.75), base_rate=1.12, lfo_hz=17.0, depth=0.22)
    y = add_echo(v, [(0.14, 0.38), (0.28, 0.20)])
    place(y, wind_rush(len(y) / SR), 0.0, 0.65)
    specs.append(("rmx_scr_ufo_alien_warble", "scream", "Flying Scream 18: UFO Alien 17Hz Warble (WHO ARE YOU + EWEWEW!)", ["wew", "remix"], y))

    # =========================================================================
    # 4. BOOM EXPLOSION REMIXES (6 clips, ~2.0-2.5s)
    # =========================================================================
    y = np.zeros(n_of(2.35))
    place(y, boom_bed(2.15), 0.0, 0.95)
    place(y, add_echo(choir_stack(slice_sec(thats_dbl, 0.20, 1.35), (0.82, 1.0, 1.22)), [(0.16, 0.35)]), 0.04, 1.05)
    specs.append(("rmx_boom_choir_doublegood", "lboom", "Boom Remix 01: Mega-Sub + Larry Choir THAT'S DOUBLE GOOD!", ["double_good", "remix"], y))

    y = np.zeros(n_of(2.45))
    place(y, boom_bed(2.20), 0.0, 0.95)
    place(y, add_echo(slice_sec(quad_good, 0.80, 2.40), [(0.16, 0.42), (0.32, 0.24), (0.48, 0.12)]), 0.03, 1.05)
    specs.append(("rmx_boom_canyon_quadgood", "lboom", "Boom Remix 02: Canyon Echo QUAD GOOD! Detonation", ["double_good", "remix"], y))

    y = np.zeros(n_of(2.20))
    place(y, boom_bed(2.00), 0.0, 0.95)
    place(y, add_echo(chain_clips([(it_wont_boot, 0.0, 1.0, 1.0), (winheh, 0.82, 1.05, 0.95)], 1.50), [(0.15, 0.34)]), 0.04, 1.05)
    specs.append(("rmx_boom_wont_boot_bsod", "lboom", "Boom Remix 03: Blue-Screen Boom (It Won't Boot! Windows Heh)", ["remix"], y))

    y = np.zeros(n_of(2.50))
    place(y, boom_bed(2.25), 0.0, 0.95)
    place(y, add_echo(slice_sec(feels_wew, 0.0, 2.10), [(0.16, 0.40), (0.32, 0.22)]), 0.03, 1.05)
    specs.append(("rmx_boom_feels_wew_nuke", "lboom", "Boom Remix 04: Nuke Echo (It Feels So Good, WEW!)", ["wew", "double_good", "remix"], y))

    y = np.zeros(n_of(2.25))
    place(y, boom_bed(2.05), 0.0, 0.95)
    place(y, add_echo(chain_clips([(banana, 0.10, 1.0, 1.0), (wewe, 1.05, 1.05, 0.95)], 1.75), [(0.15, 0.35)]), 0.04, 1.05)
    specs.append(("rmx_boom_banana_cannon", "lboom", "Boom Remix 05: Banana Cannon! + WEW! Shrapnel Blast", ["wew", "remix"], y))

    y = np.zeros(n_of(2.25))
    place(y, boom_bed(2.05), 0.0, 0.95)
    place(y, add_echo(slice_sec(ilovethatecho, 0.0, 1.35), [(0.15, 0.50), (0.30, 0.34), (0.45, 0.22), (0.60, 0.12)]), 0.04, 1.02)
    specs.append(("rmx_boom_love_echo", "lboom", "Boom Remix 06: Cavernous Boom (I Love That Echo!)", ["remix"], y))

    # 7: Slow-Mo 0.60x Movie-Trailer "BANANA... CANNON..."
    y = np.zeros(n_of(2.65))
    place(y, boom_bed(2.40), 0.0, 0.98)
    place(y, add_echo(warp_pitch(slice_sec(banana, 0.10, 1.30), 0.60, 0.60), [(0.18, 0.36)]), 0.03, 1.08)
    specs.append(("rmx_boom_slomo_banana", "lboom", "Boom Remix 07: 0.60x Slow-Mo Movie-Trailer BANANA CANNON!", ["remix"], y))

    # 8: Hyper 1.75x Double-Quad-Octo Combo Boom
    y = np.zeros(n_of(2.20))
    place(y, boom_bed(2.00), 0.0, 0.95)
    combo = chain_clips([(dbl_mc, 0.0, 1.65, 0.95), (slice_sec(quad_good, 1.20, 2.35), 0.42, 1.70, 0.98), (slice_sec(octo_mc, 0.10, 1.15), 1.00, 1.75, 1.05)], 1.75)
    place(y, add_echo(combo, [(0.12, 0.32)]), 0.03, 1.05)
    specs.append(("rmx_boom_hyper_good_combo", "lboom", "Boom Remix 08: 1.7x Turbo Combo (Double-Quad-Octogood!)", ["double_good", "remix"], y))

    # 9: Tape-Stop Slowdown Boom ("GOWEWD... ewwwd...")
    y = np.zeros(n_of(2.45))
    place(y, boom_bed(2.20), 0.0, 0.95)
    place(y, add_echo(warp_pitch(gowewd, 1.20, 0.45, dur=1.80), [(0.16, 0.35)]), 0.03, 1.04)
    specs.append(("rmx_boom_tape_die_gowewd", "lboom", "Boom Remix 09: Tape-Stop Meltdown (Fast -> 0.45x GOWEWD!)", ["wew", "remix"], y))

    # 10: 4-Pitch Demon+Chipmunk "WHO ARE YOU?!" Boom
    y = np.zeros(n_of(2.55))
    place(y, boom_bed(2.30), 0.0, 0.95)
    place(y, add_echo(choir_stack(slice_sec(who_are_you, 0.25, 1.85), (0.65, 0.95, 1.32, 1.72)), [(0.15, 0.36)]), 0.03, 1.08)
    specs.append(("rmx_boom_choir_who_are_you", "lboom", "Boom Remix 10: 4-Speed Demon+Chipmunk WHO ARE YOU?! Boom", ["remix"], y))

    # =========================================================================
    # 5. DANCE / RUNNER REMIXES (10 clips, ~1.9-2.8s)
    # =========================================================================
    v = chain_clips([(wobble_pitch(slice_sec(bounce, 0.0, 1.10), 1.08, 9.0, 0.14), 0.0, 1.0, 0.95), (wobble_pitch(slice_sec(wobble, 0.0, 1.00), 1.12, 11.0, 0.16), 0.95, 1.0, 0.95), (slice_sec(wewe, 0.0, 0.45), 1.85, 1.15, 1.00)], 2.35)
    specs.append(("rmx_run_bounce_wobble", "lrun", "Dance Remix 01: Wobbly Bouncy Boing + WEW!", ["wew", "remix"], add_echo(v, [(0.12, 0.26)])))

    v = chain_clips([(dbl_mc, 0.0, 1.22, 0.95), (slice_sec(quad_good, 1.20, 2.35), 0.58, 1.30, 0.98), (slice_sec(octo_mc, 0.10, 1.10), 1.30, 1.38, 1.02)], 2.15)
    specs.append(("rmx_run_chipmunk_good", "lrun", "Dance Remix 02: Turbo Chipmunk (Double! Quad! Octogood!)", ["double_good", "remix"], add_echo(v, [(0.11, 0.25)])))

    v = robotize(chain_clips([(slice_sec(womanly, 0.0, 1.20), 0.0, 1.05, 0.95), (slice_sec(giggle, 0.0, 0.90), 1.08, 1.10, 0.98)], 2.00), 72.0, 0.70)
    specs.append(("rmx_run_robot_womanly", "lrun", "Dance Remix 03: Robot Dance (Womanly Man + Giggle Hacks!)", ["remix"], add_echo(v, [(0.13, 0.28)])))

    v = chain_clips([(slice_sec(love_quake, 0.0, 1.05), 0.0, 1.06, 0.95), (slice_sec(dollar, 0.0, 1.35), 0.95, 1.10, 0.95)], 2.25)
    specs.append(("rmx_run_quake_dollar", "lrun", "Dance Remix 04: Love To Play Quake + Made A Dollar!", ["remix"], add_echo(v, [(0.12, 0.25)])))

    # 5: 2x Speedrun Windows ME/You/Heh!
    v = warp_pitch(slice_sec(win_me_long, 0.0, 4.80), 1.85, 2.10, dur=2.40)
    specs.append(("rmx_run_2x_windows_me", "lrun", "Dance Remix 05: 2x Hyper-Speed Windows Me / You / Heh!", ["remix"], add_echo(v, [(0.11, 0.28)])))

    # 6: Yo-Yo Slow/Fast "Made A Dollar!"
    v = yoyo_speed(slice_sec(dollar, 0.0, 1.65), dur=2.35, r_min=0.65, r_max=1.80, cycles=2.0)
    specs.append(("rmx_run_yoyo_dollar", "lrun", "Dance Remix 06: Yo-Yo Speed (0.65x <-> 1.8x Made A Dollar!)", ["remix"], add_echo(v, [(0.13, 0.26)])))

    # 7: DJ Scratch "Ah Larry! Johnny! WEW!"
    v = chain_clips([(dj_scratch(ahlarry, 4), 0.0, 1.0, 0.95), (dj_scratch(johnny, 4), 0.85, 1.0, 0.95), (stutter_tail(wewe, 0.16, 4, 0.11, 0.08), 1.70, 1.1, 1.0)], 2.55)
    specs.append(("rmx_run_dj_larry_johnny", "lrun", "Dance Remix 07: DJ Scratch (Ah Larry! Johnny! WEW-WEW!)", ["wew", "remix"], add_echo(v, [(0.12, 0.28)])))

    # 8: Slow-Mo 0.62x Drunk "It Feels So Good WEW"
    v = warp_pitch(slice_sec(feels_wew, 0.0, 1.60), 0.62, 0.64, dur=2.50)
    specs.append(("rmx_run_slomo_drunk_feels", "lrun", "Dance Remix 08: 0.62x Slow-Mo Drunk (Feels So Good WEW)", ["wew", "double_good", "remix"], add_echo(v, [(0.18, 0.34)])))

    # 9: Stutter Techno "Double-Double-Double Good!"
    v = chain_clips([(stutter_tail(dbl_mc, 0.18, 5, 0.13, 0.07), 0.0, 1.15, 0.98), (stutter_tail(wewe, 0.16, 4, 0.12, 0.09), 1.25, 1.20, 1.0)], 2.30)
    specs.append(("rmx_run_stutter_dbl_wew", "lrun", "Dance Remix 09: Stutter Beat (Double-Good-ood + WEW-ew-ew!)", ["wew", "double_good", "remix"], add_echo(v, [(0.12, 0.28)])))

    # 10: Hyper-Chipmunk Giggle-Chaos
    v = wobble_pitch(warp_pitch(chain_clips([(giggle, 0.0, 1.55, 0.95), (oh_i_love_it, 0.65, 1.65, 0.95), (wewe, 1.30, 1.75, 1.0)], 2.10), 1.15, 1.25), base_rate=1.0, lfo_hz=12.0, depth=0.14)
    specs.append(("rmx_run_hyper_giggle_chaos", "lrun", "Dance Remix 10: Hyper-Chipmunk (Giggle + Oh I Love It + WEW!)", ["wew", "remix"], add_echo(v, [(0.11, 0.28)])))

    manifest = []
    for stem, slot, label, tags, audio in specs:
        out_p = OUT_DIR / f"{stem}.wav"
        dur = save_wav(out_p, audio)
        manifest.append({
            "stem": stem,
            "slot": slot,
            "label": label,
            "tags": tags,
            "dur": round(dur, 2),
            "game_path": f"sound/larry_remixes/{stem}.wav",
        })
        print(f"  [{slot:6s}] {out_p.name:34s} ({dur:4.2f}s) - {label}")

    BANK_META_DIR.mkdir(parents=True, exist_ok=True)
    (BANK_META_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[DONE] Built {len(manifest)} custom Larry gun remixes in {OUT_DIR}")


if __name__ == "__main__":
    main()
