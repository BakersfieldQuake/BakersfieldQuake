"""Hit sounds: a short bright metallic tick for the attacker when a shot lands (in the spirit of the arena-shooter
hit beep, synthesised from scratch). Three pitches: small hits tick high, big hits lower.
python -I make_hitsound.py <sound_dir>   (writes <sound_dir>/misc/mmhit1.wav .. mmhit3.wav)"""
import array
import math
import os
import sys
import wave

RATE = 22050
OUT = os.path.join(sys.argv[1], "misc")
os.makedirs(OUT, exist_ok=True)


def tick(f0, path):
    n = int(RATE * 0.13)
    s = []
    for i in range(n):
        t = i / RATE
        env = min(1.0, t / 0.0015) * math.exp(-t / 0.032)        # 1.5 ms attack, fast decay
        v = (math.sin(2 * math.pi * f0 * t)
             + 0.45 * math.sin(2 * math.pi * f0 * 2.76 * t) * math.exp(-t / 0.012)   # bell-like overtone, dies first
             + 0.2 * math.sin(2 * math.pi * f0 * 0.5 * t))                            # a little body underneath
        s.append(env * v)
    peak = max(abs(x) for x in s)
    a = array.array("h", [int(x / peak * 30000) for x in s])
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(a.tobytes())
    w.close()
    print("wrote", path)


tick(1900, os.path.join(OUT, "mmhit1.wav"))   # under 25 damage
tick(1500, os.path.join(OUT, "mmhit2.wav"))   # 25-59
tick(1150, os.path.join(OUT, "mmhit3.wav"))   # 60 and up
