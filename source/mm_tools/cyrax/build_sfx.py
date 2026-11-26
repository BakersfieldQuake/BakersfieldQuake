"""Build the 7 Cyrax Net sounds from the MK3 cyborg effects clips.

The clips in assets/src_sfx/ are cut from the sound-effects video the weapon's
sounds are meant to come from. They are used as they are: only trimmed, layered,
faded and levelled. To try a different clip for a sound, edit SOUNDS below.

Output: mono 22050 Hz 16-bit PCM in assets/sfx/. Stdlib + NumPy only, so it
works under `python -I` in CI.

Usage:
    python -I source/mm_tools/cyrax/build_sfx.py [--verify]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import wave

import numpy as np

SR = 22050
HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, "assets", "src_sfx")
OUT_DIR = os.path.join(HERE, "assets", "sfx")

# name: (length_s, rms_db, start_gain, [(clip, delay_s, gain), ...])
# start_gain below 1.0 makes the sound swell toward the end.
SOUNDS = {
    "charge.wav":      (1.10, -12.5, 0.35, [(5, 0.00, 1.00)]),  # matches CY_CHARGE_TIME
    "fire.wav":        (0.55, -11.0, 1.00, [(6, 0.00, 1.00), (1, 0.00, 0.60)]),
    "vent.wav":        (0.50, -13.0, 1.00, [(8, 0.00, 1.00)]),
    "capture.wav":     (0.65, -11.8, 1.00, [(1, 0.00, 1.00)]),
    "pull.wav":        (0.80, -12.8, 1.00, [(3, 0.00, 1.00)]),
    "hold_beep.wav":   (0.25, -13.0, 1.00, [(4, 0.00, 1.00)]),
    "bonk_launch.wav": (0.80, -11.0, 1.00, [(6, 0.00, 1.00), (7, 0.05, 0.80)]),
}


def read_clip(number: int) -> np.ndarray:
    with wave.open(os.path.join(SRC_DIR, f"clip{number}.wav"), "rb") as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, SR)
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    x = x.astype(np.float64) / 32768.0
    return x - x.mean()


def build(length_s: float, rms_db: float, start_gain: float, layers) -> np.ndarray:
    y = np.zeros(int(round(length_s * SR)))
    for number, delay_s, gain in layers:
        clip = read_clip(number)
        start = int(round(delay_s * SR))
        n = min(len(clip), len(y) - start)
        y[start:start + n] += gain * clip[:n]
    y *= np.linspace(start_gain, 1.0, len(y))
    # short fades so trimmed edges do not click
    fade_in, fade_out = int(0.003 * SR), int(0.030 * SR)
    y[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
    y[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)
    # level to the target loudness, soft-limiting the peaks
    target = 10.0 ** (rms_db / 20.0)
    for _ in range(4):
        y *= target / np.sqrt(np.mean(y ** 2))
        y = 0.89 * np.tanh(y / 0.89)
    return y


def write_wav(path: str, y: np.ndarray) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.round(y * 32767.0).astype("<i2").tobytes())


def generate_all(out_dir: str) -> dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    digests = {}
    for name, spec in SOUNDS.items():
        y = build(*spec)
        path = os.path.join(out_dir, name)
        write_wav(path, y)
        with open(path, "rb") as f:
            digests[name] = hashlib.sha256(f.read()).hexdigest()
        rms = 20.0 * np.log10(np.sqrt(np.mean(y ** 2)))
        peak = np.abs(y).max()
        assert rms > -24.0 and peak < 0.95, f"{name}: rms {rms:.1f} dB, peak {peak:.3f}"
        print(f"{name:16s} {len(y) / SR:5.2f}s  rms {rms:6.2f} dB  peak {peak:.3f}  {digests[name][:16]}")
    return digests


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--verify", action="store_true", help="check that a second build is identical")
    args = ap.parse_args()
    first = generate_all(args.out_dir)
    if args.verify:
        with tempfile.TemporaryDirectory() as tmp:
            assert generate_all(tmp) == first, "non-deterministic output"
        print("VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
