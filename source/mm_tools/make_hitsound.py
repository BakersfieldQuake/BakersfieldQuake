"""Hit sounds: the "tink" the attacker hears when a shot lands, in the spirit of the arena-shooter hit ping
(synthesised from scratch, no samples). Playtest 1.76 asked for a better one than the old bell tick.

A struck small metal bar: three inharmonic partials (free-bar mode ratios 1 : 2.756 : 5.404) that die fast, the
high ones first, over a 2 ms filtered-noise click for the attack. Three pitches, rising with the damage:
  mmhit1.wav  under 25 damage   (lowest)
  mmhit2.wav  25-59
  mmhit3.wav  60 and up         (highest, a touch longer)
hitsound.qc picks the file and plays it only on the attacker's client.

Deterministic (seeded noise, no clock), so zz_hitsound.pk3 is byte-identical on every build.

  python -I make_hitsound.py --wav-dir <dir>                       writes <dir>/misc/mmhit1..3.wav
  python -I make_hitsound.py --pk3 <zz_hitsound.pk3> [--verify-repro]
"""
import argparse
import array
import hashlib
import io
import math
import random
import sys
import wave
import zipfile
from pathlib import Path

RATE = 44100
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
MODES = ((1.0, 1.00, 0.070), (2.756, 0.42, 0.030), (5.404, 0.16, 0.014))   # (ratio, gain, decay seconds)

# file, base frequency, length scale
TIERS = (("misc/mmhit1.wav", 1250.0, 1.00), ("misc/mmhit2.wav", 1600.0, 1.05), ("misc/mmhit3.wav", 2050.0, 1.15))


def tink(f0: float, length: float, seed: int) -> bytes:
    rng = random.Random(seed)
    dur = 0.16 * length
    n = int(RATE * dur)
    s = []
    lp = 0.0
    for i in range(n):
        t = i / RATE
        attack = min(1.0, t / 0.0008)
        v = 0.0
        for ratio, gain, decay in MODES:
            v += gain * math.sin(2 * math.pi * f0 * ratio * t) * math.exp(-t / (decay * length))
        # attack click: a little band-limited noise for the first 2 ms
        if t < 0.002:
            lp += 0.45 * (rng.uniform(-1, 1) - lp)
            v += 0.55 * lp * (1 - t / 0.002)
        # fade the last 4 ms to zero so there is no pop
        tail = min(1.0, (dur - t) / 0.004)
        s.append(attack * tail * v)
    peak = max(abs(x) for x in s)
    pcm = array.array("h", [int(round(x / peak * 29000)) for x in s])
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    return out.getvalue()


def sounds() -> dict:
    return {name: tink(f0, ln, 1760 + k) for k, (name, f0, ln) in enumerate(TIERS)}


def write_pk3(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    snd = sounds()
    with zipfile.ZipFile(path, "w") as z:
        for name in sorted(snd):
            info = zipfile.ZipInfo("sound/" + name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, snd[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"{path}: {', '.join(sorted(snd))} sha256 {digest}")
    return digest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--wav-dir", type=Path, help="write <dir>/misc/mmhit1..3.wav")
    ap.add_argument("--pk3", type=Path, help="write zz_hitsound.pk3")
    ap.add_argument("--verify-repro", action="store_true", help="build the pk3 twice and require identical bytes")
    a = ap.parse_args()
    if not a.wav_dir and not a.pk3:
        ap.error("give --wav-dir and/or --pk3")
    if a.wav_dir:
        for name, data in sounds().items():
            p = a.wav_dir / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            print("wrote", p)
    if a.pk3:
        first = write_pk3(a.pk3)
        if a.verify_repro:
            tmp = a.pk3.with_suffix(".repro.pk3")
            second = write_pk3(tmp)
            tmp.unlink()
            if first != second:
                sys.exit("NOT REPRODUCIBLE: two builds differ")
            print("reproducible: OK")


if __name__ == "__main__":
    main()
