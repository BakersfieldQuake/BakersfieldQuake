"""Make sound/netsend/ns_beep.wav: the NET SEND beep (two square-wave blips, 22 kHz mono 16-bit), played with each
message (netsend.qc, NS_Send). A placeholder until the user picks a real one.
python source/mm_tools/build_netsend_sound.py"""
import math
import os
import struct
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(GAME, "sound", "netsend", "ns_beep.wav")
RATE = 22050


def blip(freq, dur, vol):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        square = 1.0 if math.sin(2 * math.pi * freq * i / RATE) >= 0 else -1.0
        env = min(1.0, i / 150.0) * min(1.0, (n - i) / 250.0)		# no click at either end
        out.append(square * env * vol)
    return out


samples = blip(880, 0.09, 0.4) + [0.0] * int(RATE * 0.03) + blip(1320, 0.12, 0.4)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
print("wrote", OUT)
