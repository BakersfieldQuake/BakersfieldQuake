"""Generates custom Quake 16-bit mono 22050 Hz WAV sound effects for David Ojeda
in G:\\Quake\\Combat\\BakersfieldQuake\\sound\\david\\."""

import math
import os
import wave
import numpy as np

MOD_DIR = r"G:\Quake\Combat\BakersfieldQuake"
REF_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "ref", "david_ojeda")
SND_DIR = os.path.join(MOD_DIR, "sound", "david")
os.makedirs(SND_DIR, exist_ok=True)

SR = 22050


def read_wav_mono(path: str) -> np.ndarray:
    with wave.open(path, "rb") as wf:
        n = wf.getnframes()
        raw = np.frombuffer(wf.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
        ch = wf.getnchannels()
        if ch > 1:
            raw = raw.reshape(-1, ch).mean(axis=1)
    return raw


def write_wav_mono(path: str, samples: np.ndarray, peak: float = 0.88) -> None:
    mx = float(np.max(np.abs(samples))) if len(samples) else 1.0
    if mx > 1e-5:
        samples = samples * (peak / mx)
    fade = min(int(0.02 * SR), len(samples) // 8)
    if fade > 1:
        ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
        samples[:fade] *= ramp
        samples[-fade:] *= ramp[::-1]
    pcm = np.clip(np.round(samples * 32767.0), -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"Wrote {os.path.basename(path)} ({len(samples)/SR:.2f}s, {os.path.getsize(path)} bytes)")


def main() -> None:
    rng = np.random.default_rng(20261101)

    # 1. shower_love.wav — real vocal hook from v2_audio.wav ("Shower me with your love!")
    v2_path = os.path.join(REF_DIR, "v2_audio.wav")
    if os.path.exists(v2_path):
        v2 = read_wav_mono(v2_path)
        s0, s1 = int(0.45 * SR), min(len(v2), int(2.95 * SR))
        clip = v2[s0:s1].copy()
        write_wav_mono(os.path.join(SND_DIR, "shower_love.wav"), clip, peak=0.90)

    # 2. sprint_rush.wav — v1 casino panic rush + fast turbo sneaker steps
    v1_path = os.path.join(REF_DIR, "v1_audio.wav")
    dur_s = 1.65
    t = np.arange(int(dur_s * SR), dtype=np.float32) / SR
    rush = np.zeros_like(t)
    if os.path.exists(v1_path):
        v1 = read_wav_mono(v1_path)
        s0 = int(6.8 * SR)  # includes gasp at ~7s!
        seg = v1[s0:min(len(v1), s0 + len(t))]
        rush[:len(seg)] += seg * 0.65
    # Add crisp fast cartoon/athletic footstep thuds (9 steps/sec!)
    for step_t in np.arange(0.04, dur_s - 0.05, 0.11):
        i0 = int(step_t * SR)
        ln = min(int(0.055 * SR), len(t) - i0)
        if ln <= 0:
            break
        lt = np.arange(ln, dtype=np.float32) / SR
        freq = 135.0 * np.exp(-lt * 34.0) + 52.0
        thud = np.sin(2.0 * np.pi * np.cumsum(freq) / SR) * np.exp(-lt * 42.0)
        scuff = rng.normal(0.0, 1.0, ln).astype(np.float32) * np.exp(-lt * 65.0) * 0.28
        rush[i0:i0 + ln] += (thud * 0.65 + scuff)
    write_wav_mono(os.path.join(SND_DIR, "sprint_rush.wav"), rush, peak=0.88)

    # 3. money_bag.wav — heavy canvas sack thump + crisp $100 bill riffle + ka-ching register bell!
    dur_m = 1.15
    tm = np.arange(int(dur_m * SR), dtype=np.float32) / SR
    mb = np.zeros_like(tm)
    # Canvas sack thump at t=0.03
    lt0 = np.clip(tm - 0.03, 0.0, None)
    mb += (tm >= 0.03) * np.sin(2 * np.pi * (95.0 * lt0 + 35.0 * lt0 * lt0)) * np.exp(-lt0 * 24.0) * 0.7
    # Crisp paper bill flutter bursts
    for bt in (0.14, 0.21, 0.28, 0.36):
        i0 = int(bt * SR)
        ln = int(0.05 * SR)
        lt = np.arange(ln, dtype=np.float32) / SR
        noise = np.diff(rng.normal(0.0, 1.0, ln + 1)).astype(np.float32)
        mb[i0:i0 + ln] += noise * np.exp(-lt * 55.0) * 0.35
    # Bright Ka-Ching dual bell (2093 Hz C7 + 2637 Hz E7 + shimmer harmonics) at t=0.40
    ltb = np.clip(tm - 0.40, 0.0, None)
    mask_b = (tm >= 0.40).astype(np.float32)
    bell = (
        0.55 * np.sin(2 * np.pi * 2093.0 * ltb) * np.exp(-ltb * 5.5)
        + 0.48 * np.sin(2 * np.pi * 2637.0 * ltb) * np.exp(-ltb * 4.8)
        + 0.28 * np.sin(2 * np.pi * 4186.0 * ltb) * np.exp(-ltb * 8.0)
    ) * mask_b
    mb += bell
    write_wav_mono(os.path.join(SND_DIR, "money_bag.wav"), mb, peak=0.88)

    # 4. slot_spin.wav — mechanical lever pull clunk + whirring reel ticks + retro casino arpeggio!
    dur_sp = 1.50
    ts = np.arange(int(dur_sp * SR), dtype=np.float32) / SR
    sp = np.zeros_like(ts)
    # Lever pull spring-clunk (0.02..0.22s)
    for ct, cf in ((0.03, 220.0), (0.09, 340.0), (0.16, 165.0)):
        lt = np.clip(ts - ct, 0.0, None)
        sp += (ts >= ct) * np.sin(2 * np.pi * cf * lt) * np.exp(-lt * 48.0) * 0.65
    # Rapid mechanical reel clicks + arcade synth notes (0.22..1.46s)
    notes = [523.25, 659.25, 783.99, 1046.50, 783.99, 659.25]
    k_idx = 0
    ct = 0.22
    while ct < dur_sp - 0.04:
        i0 = int(ct * SR)
        ln = min(int(0.042 * SR), len(ts) - i0)
        lt = np.arange(ln, dtype=np.float32) / SR
        f_n = notes[k_idx % len(notes)] * (1.0 + 0.12 * (k_idx // 6))
        tone = (0.65 * np.sin(2 * np.pi * f_n * lt) + 0.25 * np.sign(np.sin(2 * np.pi * f_n * lt))) * np.exp(-lt * 32.0)
        click = np.sin(2 * np.pi * 1450.0 * lt) * np.exp(-lt * 140.0) * 0.45
        sp[i0:i0 + ln] += tone * 0.45 + click
        ct += 0.048
        k_idx += 1
    write_wav_mono(os.path.join(SND_DIR, "slot_spin.wav"), sp, peak=0.86)

    # 5. slot_jackpot.wav — 3 reel locks + triumphant 7-7-7 casino bell siren + cascading coin shower!
    dur_jp = 1.95
    tj = np.arange(int(dur_jp * SR), dtype=np.float32) / SR
    jp = np.zeros_like(tj)
    # 3 crisp reel lock clacks (C6, E6, G6!)
    for ct, nf in ((0.04, 1046.5), (0.19, 1318.5), (0.34, 1568.0)):
        lt = np.clip(tj - ct, 0.0, None)
        m = (tj >= ct).astype(np.float32)
        jp += m * (
            0.65 * np.sin(2 * np.pi * nf * lt) * np.exp(-lt * 11.0)
            + 0.50 * np.sin(2 * np.pi * 290.0 * lt) * np.exp(-lt * 55.0)
        )
    # Rapid casino jackpot bell ring (0.48..1.90s, 18 Hz hammer strike on brass bell)
    for bt in np.arange(0.48, 1.86, 0.056):
        lt = np.clip(tj - bt, 0.0, None)
        m = (tj >= bt).astype(np.float32)
        jp += m * (
            0.34 * np.sin(2 * np.pi * 2349.3 * lt) * np.exp(-lt * 22.0)
            + 0.24 * np.sin(2 * np.pi * 3136.0 * lt) * np.exp(-lt * 28.0)
        )
    # Cascading metal coins clinking into chrome tray!
    for _ in range(34):
        ct = float(rng.uniform(0.52, 1.82))
        cf = float(rng.uniform(3200.0, 5800.0))
        i0 = int(ct * SR)
        ln = min(int(0.07 * SR), len(tj) - i0)
        lt = np.arange(ln, dtype=np.float32) / SR
        coin = (np.sin(2 * np.pi * cf * lt) + 0.6 * np.sin(2 * np.pi * cf * 1.41 * lt)) * np.exp(-lt * 45.0)
        jp[i0:i0 + ln] += coin * 0.22
    write_wav_mono(os.path.join(SND_DIR, "slot_bust_tmp.wav"), jp, peak=0.88)
    os.replace(os.path.join(SND_DIR, "slot_bust_tmp.wav"), os.path.join(SND_DIR, "slot_jackpot.wav"))
    print("Renamed to slot_jackpot.wav")

    # 6. slot_bust.wav — 2 promising dings + sour 3rd buzz/sad descend!
    dur_bu = 1.10
    tb = np.arange(int(dur_bu * SR), dtype=np.float32) / SR
    bu = np.zeros_like(tb)
    for ct, nf in ((0.04, 1046.5), (0.19, 1318.5)):
        lt = np.clip(tb - ct, 0.0, None)
        bu += (tb >= ct) * 0.55 * np.sin(2 * np.pi * nf * lt) * np.exp(-lt * 14.0)
    # Sour buzz + downward pitch slide at 0.35s
    lt = np.clip(tb - 0.35, 0.0, None)
    m = (tb >= 0.35).astype(np.float32)
    f_slide = np.maximum(95.0, 235.0 - 145.0 * lt)
    phase = 2 * np.pi * np.cumsum(f_slide) / SR
    buzz = (0.55 * np.sin(phase) + 0.35 * np.sin(2 * phase) + 0.25 * np.sin(3 * phase)) * np.exp(-lt * 2.8)
    bu += m * buzz
    write_wav_mono(os.path.join(SND_DIR, "slot_bust.wav"), bu, peak=0.86)


if __name__ == "__main__":
    main()
