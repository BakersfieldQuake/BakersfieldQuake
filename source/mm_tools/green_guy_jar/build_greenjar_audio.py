"""Builds the 12-clip Helium-Pitched Giggle/Scream, Muffled Glass-Jar, Smoke-Ignite Shatter,
Shot-Spin Doppler Shriek, and Balloon-Confetti Pop Audio Pack (`sound/greenjar/*.wav`).

Uses authentic LAN-party laugh/giggle/scream recordings from `bakersfield.pk3`
(`funny/giggles.wav`, `funny/giggle2.wav`, `larry/giggle_hacks.wav`, `funny/wewe.wav`,
`wcannon/wc_scream.wav`, `grenade/boom_03_scream_launch.wav`, `lan/glass_tink.wav`,
`floathead/pop.wav`, `floathead/boing.wav`, `bikes/tire_pop.wav`) combined with DSP
pitch-shifting, cylindrical glass-jar resonance filtering, rotary Doppler vibrato,
smoke-ignition synthesis, and confetti-flutter transients.

Outputs standard 16-bit PCM mono 22050 Hz `.wav` files into `G:\Quake\Combat\BakersfieldQuake\sound\greenjar\`.
"""
from __future__ import annotations

import io
import math
import os
import struct
import wave
import zipfile
from typing import Dict

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PK3_PATH = os.path.join(MOD_ROOT, "bakersfield.pk3")
OUT_SND_DIR = os.path.join(MOD_ROOT, "sound", "greenjar")
SR = 22050


def _read_wav_bytes(raw: bytes) -> np.ndarray:
    """Decodes any PCM WAV (8/16/24/32-bit, mono/stereo, any sample rate) to mono float32 at SR=22050."""
    with wave.open(io.BytesIO(raw), "rb") as wf:
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        fr = wf.getframerate()
        nframes = wf.getnframes()
        frames = wf.readframes(nframes)

    if sw == 1:
        arr = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sw == 2:
        arr = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    elif sw == 3:
        b = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
        i32 = (
            b[:, 0].astype(np.int32)
            | (b[:, 1].astype(np.int32) << 8)
            | (b[:, 2].astype(np.int32) << 16)
        )
        i32 = np.where(i32 & 0x800000, i32 - 0x1000000, i32)
        arr = i32.astype(np.float32) / 8388608.0
    else:
        arr = np.frombuffer(frames, dtype="<i4").astype(np.float32) / 2147483648.0

    if nch > 1:
        arr = arr.reshape(-1, nch).mean(axis=1)

    if fr != SR and len(arr) > 4:
        new_len = max(1, int(round(len(arr) * SR / float(fr))))
        arr = signal.resample(arr, new_len).astype(np.float32)
    return arr.astype(np.float32)


def _load_pk3_clips() -> Dict[str, np.ndarray]:
    wanted = {
        "giggles": "sound/funny/giggles.wav",
        "giggle2": "sound/funny/giggle2.wav",
        "giggle_hacks": "sound/larry/giggle_hacks.wav",
        "wewe": "sound/funny/wewe.wav",
        "heh": "sound/funny/heh.wav",
        "scream1": "sound/wcannon/wc_scream.wav",
        "scream2": "sound/grenade/boom_03_scream_launch.wav",
        "tink": "sound/lan/glass_tink.wav",
        "pop": "sound/floathead/pop.wav",
        "boing": "sound/floathead/boing.wav",
        "tire_pop": "sound/bikes/tire_pop.wav",
        "goopop": "sound/weapons/goopop.wav",
    }
    out: Dict[str, np.ndarray] = {}
    with zipfile.ZipFile(PK3_PATH, "r") as zf:
        names = set(zf.namelist())
        for k, path in wanted.items():
            if path in names:
                try:
                    out[k] = _read_wav_bytes(zf.read(path))
                except Exception as exc:
                    print(f"Warning decoding {path}: {exc}")
    return out


def _trim_silence(x: np.ndarray, thresh: float = 0.025) -> np.ndarray:
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) < 16:
        return x
    return x[max(0, idx[0] - 120): min(len(x), idx[-1] + 240)]


def _pitch_shift(x: np.ndarray, factor: float) -> np.ndarray:
    """Resamples by 1/factor so playback at SR raises pitch & speed cleanly like helium!"""
    if len(x) < 8:
        return x
    t_in = np.linspace(0.0, 1.0, len(x), dtype=np.float32)
    out_len = max(8, int(round(len(x) / factor)))
    t_out = np.linspace(0.0, 1.0, out_len, dtype=np.float32)
    return np.interp(t_out, t_in, x).astype(np.float32)


def _pitch_warp_curve(x: np.ndarray, f_start: float, f_end: float, vibrato_hz: float = 0.0, vibrato_depth: float = 0.0) -> np.ndarray:
    """Time-varying pitch + rotary Doppler vibrato."""
    dt = 1.0 / SR
    out = []
    pos = 0.0
    t = 0.0
    n = len(x)
    while pos < n - 2 and len(out) < int(SR * 2.5):
        u = min(1.0, pos / max(1.0, float(n)))
        rate = f_start + (f_end - f_start) * u
        if vibrato_hz > 0.0:
            rate *= 1.0 + vibrato_depth * math.sin(2.0 * math.pi * vibrato_hz * t)
        i0 = int(pos)
        frac = pos - i0
        val = x[i0] * (1.0 - frac) + x[i0 + 1] * frac
        if vibrato_hz > 0.0:
            # Rotary amplitude panning flutter
            val *= 0.78 + 0.22 * math.cos(2.0 * math.pi * vibrato_hz * t)
        out.append(val)
        pos += rate
        t += dt
    return np.array(out, dtype=np.float32)


def _norm_fade(x: np.ndarray, peak: float = 0.90, fade_ms: float = 12.0) -> np.ndarray:
    if len(x) == 0:
        return np.zeros(256, dtype=np.float32)
    x = x - np.mean(x)
    mx = float(np.max(np.abs(x)))
    if mx > 1e-6:
        x = x * (peak / mx)
    fn = min(len(x) // 4, int(SR * fade_ms / 1000.0))
    if fn > 2:
        ramp = np.linspace(0.0, 1.0, fn, dtype=np.float32)
        x[:fn] *= ramp
        x[-fn:] *= ramp[::-1]
    return np.clip(x, -0.99, 0.99)


def _glass_jar_muffle(x: np.ndarray) -> np.ndarray:
    """Simulates hearing a tiny helium maniac trapped inside a thick sealed glass mason jar:
    bandpass (380..2350 Hz) + short 2.9 ms internal glass-wall comb reflection!
    """
    sos = signal.butter(3, [380.0 / (SR * 0.5), 2350.0 / (SR * 0.5)], btype="bandpass", output="sos")
    y = signal.sosfilt(sos, x).astype(np.float32)
    delay = int(0.0029 * SR)
    comb = y.copy()
    if len(y) > delay:
        comb[delay:] += 0.42 * y[:-delay]
    if len(y) > delay * 2:
        comb[delay * 2:] += 0.20 * y[:-delay * 2]
    return comb


def _mix_into(dst: np.ndarray, src: np.ndarray, offset: int, gain: float = 1.0) -> None:
    if offset >= len(dst) or len(src) == 0:
        return
    i0 = max(0, offset)
    s0 = max(0, -offset)
    cnt = min(len(dst) - i0, len(src) - s0)
    if cnt > 0:
        dst[i0:i0 + cnt] += src[s0:s0 + cnt] * gain


def _synth_glass_tap(freq: float = 2850.0, dur: float = 0.055) -> np.ndarray:
    t = np.arange(int(SR * dur), dtype=np.float32) / SR
    env = np.exp(-t * 68.0)
    ring = (
        0.65 * np.sin(2.0 * np.pi * freq * t)
        + 0.35 * np.sin(2.0 * np.pi * (freq * 1.53) * t)
        + 0.22 * np.sin(2.0 * np.pi * (freq * 2.41) * t)
    )
    return (ring * env).astype(np.float32)


def _synth_smoke_ignite(dur: float = 0.92, rng: np.random.Generator = None) -> np.ndarray:
    """Roaring green-smoke FWOOMP ignition puff."""
    if rng is None:
        rng = np.random.default_rng(42)
    n = int(SR * dur)
    t = np.arange(n, dtype=np.float32) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    # Low-mid fwoomp body
    sos_lo = signal.butter(3, [95.0 / (SR * 0.5), 680.0 / (SR * 0.5)], btype="bandpass", output="sos")
    body = signal.sosfilt(sos_lo, noise) * np.exp(-((t - 0.11) ** 2) / 0.032) * 2.2
    # Sizzling green-mist hiss tail
    sos_hi = signal.butter(2, [1400.0 / (SR * 0.5), 6200.0 / (SR * 0.5)], btype="bandpass", output="sos")
    hiss = signal.sosfilt(sos_hi, noise) * np.exp(-t * 3.6) * np.clip(t / 0.03, 0.0, 1.0) * 0.65
    return (body + hiss).astype(np.float32)


def _save_wav(path: str, samples: np.ndarray) -> float:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = np.clip(np.round(samples * 32767.0), -32767, 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    return len(samples) / float(SR)


def build_all_sounds() -> Dict[str, str]:
    rng = np.random.default_rng(20261111)
    clips = _load_pk3_clips()

    g1 = _trim_silence(clips["giggles"])
    g2 = _trim_silence(clips["giggle2"])
    gh = _trim_silence(clips["giggle_hacks"])
    ww = _trim_silence(clips["wewe"])
    sc1 = _trim_silence(clips["scream1"])
    sc2 = _trim_silence(clips["scream2"])
    tink = _trim_silence(clips["tink"])
    pop_s = _trim_silence(clips["pop"])
    tpop = _trim_silence(clips["tire_pop"])
    boing = _trim_silence(clips["boing"])

    # Bright exciter high-shelf for crisp intelligible helium giggles
    sos_bright = signal.butter(2, 520.0 / (SR * 0.5), btype="highpass", output="sos")

    # 1. mini_giggle1..3 + mini_scream1 (the open-air manic helium swarm voices!)
    mg1 = _norm_fade(signal.sosfilt(sos_bright, _pitch_shift(g1[: int(SR * 1.45)], 1.66)), 0.90)
    mg2 = _norm_fade(signal.sosfilt(sos_bright, _pitch_shift(g2[: int(SR * 1.40)], 1.74)), 0.90)

    gh_part = _pitch_shift(gh[: int(SR * 1.15)], 1.68)
    ww_part = _pitch_shift(ww[: int(SR * 0.85)], 1.62)
    mg3_buf = np.zeros(int(SR * 0.92), dtype=np.float32)
    _mix_into(mg3_buf, ww_part, 0, 0.85)
    _mix_into(mg3_buf, gh_part, int(SR * 0.24), 0.95)
    mg3 = _norm_fade(signal.sosfilt(sos_bright, mg3_buf), 0.90)

    sc_hi = _pitch_shift(sc2[: int(SR * 0.95)], 1.82)
    ms1_buf = np.zeros(int(SR * 0.82), dtype=np.float32)
    _mix_into(ms1_buf, sc_hi, 0, 0.85)
    _mix_into(ms1_buf, mg1[: int(SR * 0.45)], int(SR * 0.34), 0.95)
    ms1 = _norm_fade(signal.sosfilt(sos_bright, ms1_buf), 0.90)

    # 2. Muffled inside-the-glass-jar spaz clips (`jar_muffle1.wav`, `jar_muffle2.wav`)
    jm1_buf = np.zeros(int(SR * 1.15), dtype=np.float32)
    _mix_into(jm1_buf, _glass_jar_muffle(mg1), int(SR * 0.04), 0.95)
    _mix_into(jm1_buf, _synth_glass_tap(2780.0), int(SR * 0.18), 0.55)
    _mix_into(jm1_buf, _synth_glass_tap(3120.0), int(SR * 0.31), 0.48)
    _mix_into(jm1_buf, _synth_glass_tap(2640.0), int(SR * 0.76), 0.42)
    jm1 = _norm_fade(jm1_buf, 0.78)

    jm2_buf = np.zeros(int(SR * 1.05), dtype=np.float32)
    _mix_into(jm2_buf, _glass_jar_muffle(mg3), int(SR * 0.02), 0.95)
    _mix_into(jm2_buf, _pitch_shift(tink[: int(SR * 0.25)], 1.85), int(SR * 0.44), 0.38)
    jm2 = _norm_fade(jm2_buf, 0.78)

    # 3. Cocktail-shaker windup (`jar_shake.wav`)
    shk_buf = np.zeros(int(SR * 0.50), dtype=np.float32)
    for k_i, t_off in enumerate([0.02, 0.13, 0.24, 0.35]):
        _mix_into(shk_buf, _synth_glass_tap(2500.0 + k_i * 240.0, 0.06), int(SR * t_off), 0.65)
        _mix_into(shk_buf, _pitch_shift(tink[: int(SR * 0.16)], 1.9 + 0.15 * k_i), int(SR * (t_off + 0.03)), 0.42)
    shk_voice = _glass_jar_muffle(_pitch_warp_curve(sc1[: int(SR * 0.85)], 1.55, 2.20, vibrato_hz=16.0, vibrato_depth=0.14))
    _mix_into(shk_buf, shk_voice, 0, 1.05)
    jar_shake = _norm_fade(shk_buf, 0.88)

    # 4. Whip-throw release (`jar_throw.wav`)
    thr_n = int(SR * 0.36)
    t_thr = np.arange(thr_n, dtype=np.float32) / SR
    whoosh_noise = rng.standard_normal(thr_n).astype(np.float32)
    sos_wh = signal.butter(2, [320.0 / (SR * 0.5), 2600.0 / (SR * 0.5)], btype="bandpass", output="sos")
    whoosh = signal.sosfilt(sos_wh, whoosh_noise) * np.exp(-((t_thr - 0.08) ** 2) / 0.008) * 1.8
    _mix_into(whoosh, _glass_jar_muffle(ms1[: int(SR * 0.32)]), int(SR * 0.03), 0.65)
    jar_throw = _norm_fade(whoosh, 0.88)

    # 5. Glass-Shatter + Igniting Green-Smoke Fireball + 12-Gremlin Burst Chorus (`jar_shatter.wav`)
    shat_buf = np.zeros(int(SR * 1.18), dtype=np.float32)
    # Multi-shard glass crash
    _mix_into(shat_buf, _pitch_shift(tink, 1.05), 0, 1.05)
    _mix_into(shat_buf, _pitch_shift(tink, 1.48), int(SR * 0.018), 0.85)
    _mix_into(shat_buf, _pitch_shift(tink, 2.15), int(SR * 0.045), 0.68)
    for s_i in range(7):
        _mix_into(
            shat_buf,
            _synth_glass_tap(2200.0 + s_i * 430.0, 0.08),
            int(SR * (0.01 + s_i * 0.038)),
            0.42,
        )
    # Green smoke ignition FWOOMP!
    _mix_into(shat_buf, _synth_smoke_ignite(0.95, rng), int(SR * 0.025), 0.92)
    # Unleashed chorus of giggling/screaming gremlins scattering out!
    _mix_into(shat_buf, mg1, int(SR * 0.10), 0.72)
    _mix_into(shat_buf, mg2, int(SR * 0.19), 0.68)
    _mix_into(shat_buf, ms1, int(SR * 0.26), 0.62)
    _mix_into(shat_buf, _pitch_shift(mg3, 1.12), int(SR * 0.35), 0.65)
    jar_shatter = _norm_fade(shat_buf, 0.94)

    # 6. 1-Hit Punctured-Helium-Balloon Death-Spin Shriek (`mini_spin_shriek.wav`)
    spin_src = np.concatenate([sc1[: int(SR * 0.55)], g2[: int(SR * 0.55)]])
    spin_warped = _pitch_warp_curve(spin_src, 1.65, 2.45, vibrato_hz=15.5, vibrato_depth=0.18)
    spin_shriek = _norm_fade(signal.sosfilt(sos_bright, spin_warped[: int(SR * 0.62)]), 0.92)

    # 7. Balloon-Swell & Rainbow Confetti Pop (`mini_pop.wav`)
    pop_buf = np.zeros(int(SR * 0.46), dtype=np.float32)
    # Tight 75 ms rubber balloon stretch squeak right before POP!
    n_sq = int(SR * 0.075)
    t_sq = np.arange(n_sq, dtype=np.float32) / SR
    squeak = np.sin(2.0 * np.pi * (900.0 * t_sq + 4800.0 * (t_sq ** 2))) * np.linspace(0.2, 0.9, n_sq, dtype=np.float32)
    _mix_into(pop_buf, squeak, 0, 0.45)
    # Crisp balloon POP!
    _mix_into(pop_buf, _pitch_shift(tpop[: int(SR * 0.25)], 1.25), int(SR * 0.072), 1.10)
    _mix_into(pop_buf, _pitch_shift(pop_s[: int(SR * 0.25)], 1.35), int(SR * 0.075), 0.95)
    # Sparkling confetti streamer flutter + tiny high-pitched cheer harmonic
    flut_n = int(SR * 0.30)
    t_fl = np.arange(flut_n, dtype=np.float32) / SR
    flut_noise = rng.standard_normal(flut_n).astype(np.float32)
    sos_fl = signal.butter(2, [2800.0 / (SR * 0.5), 8500.0 / (SR * 0.5)], btype="bandpass", output="sos")
    flutter = signal.sosfilt(sos_fl, flut_noise) * np.exp(-t_fl * 10.5) * (0.6 + 0.4 * np.sin(2.0 * np.pi * 28.0 * t_fl))
    _mix_into(pop_buf, flutter.astype(np.float32), int(SR * 0.09), 0.48)
    mini_pop = _norm_fade(pop_buf, 0.94)

    # 8. Weightless rubber-flea pogo bounce (`mini_boing.wav`)
    boing_buf = np.zeros(int(SR * 0.30), dtype=np.float32)
    _mix_into(boing_buf, _pitch_shift(boing[: int(SR * 0.38)], 1.65), 0, 0.85)
    _mix_into(boing_buf, mg2[: int(SR * 0.16)], int(SR * 0.04), 0.55)
    mini_boing = _norm_fade(boing_buf, 0.82)

    manifest = {
        "jar_muffle1.wav": jm1,
        "jar_muffle2.wav": jm2,
        "jar_shake.wav": jar_shake,
        "jar_throw.wav": jar_throw,
        "jar_shatter.wav": jar_shatter,
        "mini_giggle1.wav": mg1,
        "mini_giggle2.wav": mg2,
        "mini_giggle3.wav": mg3,
        "mini_scream1.wav": ms1,
        "mini_spin_shriek.wav": spin_shriek,
        "mini_pop.wav": mini_pop,
        "mini_boing.wav": mini_boing,
    }
    saved: Dict[str, str] = {}
    for fn, arr in manifest.items():
        out_p = os.path.join(OUT_SND_DIR, fn)
        dur = _save_wav(out_p, arr)
        saved[fn] = out_p
        print(f"  -> {fn:22s}: {dur:.2f}s ({os.path.getsize(out_p) / 1024.0:.1f} KB)")
    return saved


if __name__ == "__main__":
    print("Building Green-Guy Jar Helium Voice & SFX Pack...")
    build_all_sounds()
    print("Done!")
