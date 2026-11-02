"""Synthesizes 12 hilarious spoken + foley 22050 Hz 16-bit mono Quake WAV clips in `sound/random_npcs/`
for the 4 Random People NPCs (Random Guy, Afro Guy, Random Lady, Really Big Fat Guy)."""
from __future__ import annotations

import os
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MOD_ROOT = HERE.parent.parent.parent
SND_DIR = MOD_ROOT / "sound" / "random_npcs"
SR = 22050


def write_wav(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = max(1e-4, float(np.max(np.abs(samples))))
    normed = np.clip(samples / peak * 0.92, -1.0, 1.0)
    pcm = (normed * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def tts_render(text: str, female: bool = False, rate: int = 1, pitch_factor: float = 1.0) -> np.ndarray:
    """Renders spoken line via Windows SAPI5 SpeechSynthesizer and resamples cleanly for character voice."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tmp_wav = tf.name
    try:
        gender = "Female" if female else "Male"
        safe_txt = text.replace("'", "''")
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::{gender}); "
            f"$s.Rate = {int(rate)}; "
            f"$s.SetOutputToWaveFile('{tmp_wav}'); "
            f"$s.Speak('{safe_txt}'); "
            "$s.Dispose();"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True)
        with wave.open(tmp_wav, "rb") as wf:
            nch = wf.getnchannels()
            sw = wf.getsampwidth()
            sr_in = wf.getframerate()
            raw = wf.readframes(wf.getnframes())
        arr = np.frombuffer(raw, dtype=np.int16 if sw == 2 else np.uint8).astype(np.float32)
        if sw == 1:
            arr = (arr - 128.0) / 128.0
        else:
            arr /= 32768.0
        if nch > 1:
            arr = arr.reshape(-1, nch).mean(axis=1)
        # Trim leading/trailing silence
        nz = np.nonzero(np.abs(arr) > 0.015)[0]
        if len(nz) > 10:
            arr = arr[max(0, nz[0] - 200) : min(len(arr), nz[-1] + 400)]
        # Resample to SR with pitch_factor (>1 higher/faster, <1 deeper/heavier)
        out_len = max(64, int(round(len(arr) * (SR / float(sr_in)) / pitch_factor)))
        x_old = np.linspace(0.0, 1.0, len(arr), endpoint=False)
        x_new = np.linspace(0.0, 1.0, out_len, endpoint=False)
        return np.interp(x_new, x_old, arr).astype(np.float32)
    finally:
        if os.path.exists(tmp_wav):
            try:
                os.remove(tmp_wav)
            except OSError:
                pass


def foley_straw_slurp(dur: float = 0.34) -> np.ndarray:
    rng = np.random.default_rng(11)
    n = int(SR * dur)
    t = np.linspace(0.0, dur, n, endpoint=False)
    f = 420.0 + 680.0 * (t / dur) ** 1.5 + 95.0 * np.sin(2 * np.pi * 29.0 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    bub = (0.55 * np.sin(ph) + 0.45 * rng.standard_normal(n)) * (0.5 + 0.5 * np.sin(2 * np.pi * 26.0 * t))
    return (bub * np.sin(np.pi * t / dur) ** 0.5).astype(np.float32)


def foley_funk_bass() -> np.ndarray:
    parts = []
    for f0, d in ((110.0, 0.14), (130.8, 0.13), (146.8, 0.14), (220.0, 0.20)):
        n = int(SR * d)
        t = np.linspace(0.0, d, n, endpoint=False)
        sig = (0.7 * np.sin(2 * np.pi * f0 * t) + 0.45 * np.sin(4 * np.pi * f0 * t) + 0.25 * np.sin(6 * np.pi * f0 * t)) * np.exp(-9.5 * t)
        parts.append(sig)
    return np.concatenate(parts).astype(np.float32)


def foley_belly_slap_and_burp() -> np.ndarray:
    rng = np.random.default_rng(44)
    out = np.zeros(int(SR * 0.72), dtype=np.float32)
    for t0 in (0.02, 0.18):
        idx = int(t0 * SR)
        ns = int(0.09 * SR)
        ts = np.linspace(0.0, 0.09, ns, endpoint=False)
        slap = (0.75 * np.sin(2 * np.pi * (165.0 - 900.0 * ts) * ts) + 0.45 * rng.standard_normal(ns)) * np.exp(-38.0 * ts)
        out[idx : idx + ns] += slap
    # Comic low burp at t=0.34..0.68
    idx_b = int(0.34 * SR)
    nb = int(0.34 * SR)
    tb = np.linspace(0.0, 0.34, nb, endpoint=False)
    fb = 92.0 - 18.0 * (tb / 0.34) + 8.0 * np.sin(2 * np.pi * 24.0 * tb)
    ph = 2 * np.pi * np.cumsum(fb) / SR
    burp = np.tanh(2.8 * (np.sin(ph) + 0.65 * np.sin(2 * ph) + 0.4 * np.sin(3 * ph))) * np.sin(np.pi * tb / 0.34) ** 0.4
    out[idx_b : idx_b + nb] += burp * 0.85
    return out


def concat_pad(*clips: np.ndarray, gap: float = 0.05) -> np.ndarray:
    g = np.zeros(int(SR * gap), dtype=np.float32)
    seq = []
    for i, c in enumerate(clips):
        if i > 0:
            seq.append(g)
        seq.append(c)
    return np.concatenate(seq)


def main() -> None:
    SND_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Random Guy
    write_wav(SND_DIR / "randguy_idle.wav", concat_pad(foley_straw_slurp(0.28), tts_render("Wait... why does everybody have rocket launchers?", False, 2, 1.04)))
    write_wav(SND_DIR / "randguy_funny.wav", concat_pad(foley_straw_slurp(0.36), tts_render("Aw man, right on my good shirt!", False, 2, 1.05)))
    write_wav(SND_DIR / "randguy_panic.wav", tts_render("Whoa bro chill! Don't spill my Mega Gulp!", False, 4, 1.12))

    # 2. Black Guy with Afro
    write_wav(SND_DIR / "afroguy_idle.wav", concat_pad(foley_funk_bass() * 0.65, tts_render("Stay cool baby, watch the fro!", False, 1, 0.93)))
    write_wav(SND_DIR / "afroguy_funny.wav", concat_pad(foley_funk_bass() * 0.80, tts_render("Can you dig it? Pure Bakersfield funk!", False, 1, 0.94)))
    write_wav(SND_DIR / "afroguy_panic.wav", tts_render("Whoa man! Watch the hair, watch the fro!", False, 3, 0.98))

    # 3. Random Lady
    write_wav(SND_DIR / "lady_idle.wav", tts_render("Excuse me?! Do you have a permit for that gun?", True, 2, 1.06))
    write_wav(SND_DIR / "lady_funny.wav", tts_render("Unbelievable! I am calling the H O A right now!", True, 2, 1.08))
    write_wav(SND_DIR / "lady_panic.wav", tts_render("Aaaah! I want to speak to the manager!", True, 4, 1.15))

    # 4. Really Big Fat Guy
    write_wav(SND_DIR / "fatguy_idle.wav", tts_render("Mmm, extra cheese carne asada burrito...", False, 0, 0.84))
    write_wav(SND_DIR / "fatguy_funny.wav", concat_pad(foley_belly_slap_and_burp(), tts_render("Haha! Cardio starts tomorrow!", False, 1, 0.85)))
    write_wav(SND_DIR / "fatguy_panic.wav", tts_render("Whoa hey! Not the burrito! Save the burrito!", False, 3, 0.88))

    print(f"SYNTHESIZED 12 NPC VOICE CLIPS IN {SND_DIR}")


if __name__ == "__main__":
    main()
