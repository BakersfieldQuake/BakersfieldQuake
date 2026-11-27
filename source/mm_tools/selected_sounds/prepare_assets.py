"""Prepare enhanced, trimmed, normalized 22050 Hz 16-bit mono WAV assets from selected_sounds.

Active sounds go to:
  source/mm_tools/selected_sounds/assets/sound/<game_rel_path>
Reserved future-character sounds go to:
  source/mm_tools/sound_bank/justin_camera/
  source/mm_tools/sound_bank/charlie/

Usage:
  python3 source/mm_tools/selected_sounds/prepare_assets.py [src_dir]
"""
from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
DEFAULT_SRC = Path("/home/computer/Downloads/Telegram Desktop/selected_sounds")
ACTIVE_OUT = HERE / "assets" / "sound"
BANK_OUT = MM_TOOLS / "sound_bank"
TARGET_SR = 22050

# (source_filename, dest_rel_path, trim_range_s_or_None, target_rms, max_peak, extra_trim_silence)
ACTIVE_SPECS = [
    # John Bird
    ("good-morning.wav", "john_bird/jv_fly14.wav", None, 0.22, 0.92, True),
    ("hello-2.wav", "john_bird/jv_fly15.wav", None, 0.22, 0.92, True),
    # Rob Drone
    ("hello-i-am-good.wav", "robhead/rd_grenade.wav", None, 0.23, 0.92, True),
    ("hello-this-is-rob-i-am-talking-to-gainus-lubus.wav", "robhead/rd_chatter_rob.wav", None, 0.24, 0.92, True),
    ("big-long-strand-of-wires-that-s-paul.wav", "robhead/rd_chatter_paul.wav", None, 0.23, 0.92, True),
    ("BUH2.WAV", "robhead/rd_buh.wav", None, 0.24, 0.92, True),
    ("chicken.wav", "robhead/rd_chicken.wav", None, 0.25, 0.94, True),
    ("fart.wav", "robhead/rd_fart.wav", None, 0.25, 0.94, True),
    ("awimist.wav", "robhead/rd_missed.wav", None, 0.34, 0.96, True),  # extra loud per user request
    # Eric Cannon ("Canis Cannon")
    ("CanisLupusFantasy.wav", "eric_cannon/canislupusfantasy1.wav", None, 0.17, 0.55, True),
    # Woo Cannon: compact first + second burst (~2.5s) from 6.5s clip
    ("eweewew.wav", "wcannon/wc_lrun13.wav", (0.45, 2.95), 0.24, 0.92, True),
    # Mega Man Gun
    ("goooooood.wav", "megaman/boom28.wav", None, 0.24, 0.92, True),
    # Grenades exploding (clean punchy overlay of funny/fart2.wav)
    ("fart2.wav", "funny/fart2.wav", None, 0.28, 0.94, True),
    # Indian Poop Gun (punchy ~4.5s slice of dotdot.wav)
    ("dotdot.wav", "dookie/dk_dotdot.wav", (0.0, 4.5), 0.21, 0.88, True),
]

RESERVED_SPECS = [
    ("gg.wav", "justin_camera/jc_gg.wav", None, 0.22, 0.90, True),
    ("giggles.wav", "justin_camera/jc_giggles.wav", None, 0.22, 0.90, True),
    ("900hour.wav", "justin_camera/jc_900hour.wav", None, 0.22, 0.90, True),
    ("durrR.wav", "charlie/ch_durr.wav", None, 0.22, 0.90, True),
    ("giggleh4x.wav", "charlie/ch_giggleh4x.wav", None, 0.22, 0.90, True),
]


def decode_clean_mono(src: Path, trim: tuple[float, float] | None) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-i", str(src)]
    if trim is not None:
        cmd += ["-ss", f"{trim[0]:.3f}", "-to", f"{trim[1]:.3f}"]
    cmd += [
        "-af", "highpass=f=75,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=60",
        "-ac", "1", "-ar", str(TARGET_SR), "-f", "s16le", "-",
    ]
    res = subprocess.run(cmd, check=True, capture_output=True)
    return np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def trim_silence(arr: np.ndarray, thresh: float = 0.015, pad_s: float = 0.025) -> np.ndarray:
    if len(arr) == 0:
        return arr
    # Windowed envelope so faint pops aren't treated as edge audio, while low speech isn't clipped.
    win = max(1, int(0.012 * TARGET_SR))
    abs_a = np.abs(arr)
    idx = np.where(abs_a > thresh)[0]
    if len(idx) == 0:
        return arr
    pad = int(pad_s * TARGET_SR)
    lo = max(0, int(idx[0]) - pad)
    hi = min(len(arr), int(idx[-1]) + pad + win)
    return arr[lo:hi].copy()


def enhance_and_write(src: Path, dst: Path, trim: tuple[float, float] | None, target_rms: float, max_peak: float, do_trim: bool) -> tuple[float, float, float]:
    arr = decode_clean_mono(src, trim)
    if do_trim:
        arr = trim_silence(arr)
    arr = arr - float(np.mean(arr)) if len(arr) else arr

    # Loudness normalization based on active (non-silent) samples so pauses don't skew gain.
    active = arr[np.abs(arr) > 0.012]
    rms = float(np.sqrt(np.mean(active * active))) if len(active) else (float(np.sqrt(np.mean(arr * arr))) if len(arr) else 0.0)
    if rms > 1e-6:
        gain = min(target_rms / rms, 8.0)
        arr = arr * gain

    # Soft tanh saturation limiter if peaks exceed max_peak, keeping perceived loudness high without harsh clipping.
    peak = float(np.max(np.abs(arr))) if len(arr) else 0.0
    if peak > max_peak:
        arr = max_peak * np.tanh(arr / max_peak)
        # Re-scale exactly to max_peak ceiling.
        p2 = float(np.max(np.abs(arr)))
        if p2 > max_peak:
            arr = arr * (max_peak / p2)

    # Smooth micro-fades (8 ms in, 25 ms out) to avoid click artifacts.
    fade_in = min(len(arr) // 4, int(0.008 * TARGET_SR))
    fade_out = min(len(arr) // 3, int(0.025 * TARGET_SR))
    if trim is not None and trim[1] > trim[0] + 1.0:
        fade_out = min(len(arr) // 3, int(0.25 * TARGET_SR))
    if fade_in > 1:
        arr[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)
    if fade_out > 1:
        arr[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)

    pcm = np.clip(np.round(arr * 32767.0), -32768, 32767).astype(np.int16)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(TARGET_SR)
        wf.writeframes(pcm.tobytes())

    final_rms = float(np.sqrt(np.mean(arr * arr))) if len(arr) else 0.0
    final_peak = float(np.max(np.abs(arr))) if len(arr) else 0.0
    return len(arr) / TARGET_SR, final_rms, final_peak


def main() -> None:
    src_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not src_dir.is_dir():
        sys.exit(f"Source directory not found: {src_dir}")

    print("Preparing active game WAV assets:")
    for src_name, rel, trim, trms, mpk, do_trim in ACTIVE_SPECS:
        src = src_dir / src_name
        dst = ACTIVE_OUT / rel
        dur, rms, pk = enhance_and_write(src, dst, trim, trms, mpk, do_trim)
        print(f"  {rel:42s} <- {src_name:52s} ({dur:.2f}s rms={rms:.3f} peak={pk:.2f})")

    print("\nPreparing reserved future-character WAV assets:")
    for src_name, rel, trim, trms, mpk, do_trim in RESERVED_SPECS:
        src = src_dir / src_name
        dst = BANK_OUT / rel
        dur, rms, pk = enhance_and_write(src, dst, trim, trms, mpk, do_trim)
        print(f"  {rel:42s} <- {src_name:52s} ({dur:.2f}s rms={rms:.3f} peak={pk:.2f})")


if __name__ == "__main__":
    main()
