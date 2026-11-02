"""The Milky Gun sound inspector: ONE self-contained HTML page (the audio is inside it as base64) to hear, see and re-cut every
sound the gun uses:
  - the whole song (the user's mp3) with draggable markers: where it starts when she flies (SONG_FROM) and the shot line (FIRE_CUT)
  - the shot line, and the burst sounds (afrit/body_explode, misc/h2ohit1, weapons/goopop, goosplat, goostick) at the pitches
    the code plays them at, and "play the whole burst" which layers them like the game does
  - a loudness trial for the layered song (how many copies are playing)
The "copy my picks" box gives the numbers to paste back (build_milky_assets.py SONG_FROM / FIRE_CUT).

python build_milky_sound_page.py <song.mp3> [out.html] [transcript.json]      (no PIL needed)"""
import base64
import json
import os
import struct
import sys
import zipfile

SONG = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else r"G:\Quake\Combat\BakersfieldQuake\source\milky_sound_inspector\index.html"
TRANSCRIPT = sys.argv[3] if len(sys.argv) > 3 else ""
MOD = r"G:\Quake\Combat\BakersfieldQuake"
PK3 = r"G:\Quake\Combat\quake15\q15.pk3"
PAKS = [r"G:\Quake\Combat\id1\pak0.pak", r"G:\Quake\Combat\id1\pak1.pak"]


def from_pak(name):
    for p in PAKS:
        d = open(p, "rb").read()
        magic, off, ln = struct.unpack("<4sii", d[:12])
        for i in range(ln // 64):
            n, o, s = struct.unpack("<56sii", d[off + i * 64: off + i * 64 + 64])
            if n.split(b"\0")[0].decode() == name:
                return d[o:o + s]
    raise SystemExit("not in the paks: " + name)


def sound(name):
    f = os.path.join(MOD, "sound", name)
    if os.path.exists(f):
        return open(f, "rb").read()
    with zipfile.ZipFile(PK3) as z:
        for n in z.namelist():
            if n.lower() == "sound/" + name:
                return z.read(n)
    return from_pak("sound/" + name)


def b64(b):
    return base64.b64encode(b).decode("ascii")


# what the game plays, and how (milky.qc): name, file, pitch (playback rate), volume, what it is for
EFFECTS = [
    ("The shot line (fire.wav)", "milky/fire.wav", 1.0, 1.0, "plays twice (two channels) when you press fire; the windup lasts 1.28 s, she is thrown at the end"),
    ("Burst: body explode", "afrit/body_explode.wav", 0.8, 1.0, "a low thump under the burst (the Afrit's body)"),
    ("Burst: big wet splash", "misc/h2ohit1.wav", 0.6, 1.0, "water hit, slowed to 0.6: a big wet splash"),
    ("Burst: slimy pop", "weapons/goopop.wav", 0.55, 1.0, "the goo gun's pop, slowed to 0.55"),
    ("Burst: goo splat", "weapons/goosplat.wav", 0.7, 0.9, "the goo gun's splat, slowed to 0.7"),
    ("\"No room for her here\"", "weapons/goostick.wav", 1.0, 0.6, "when there is a wall in front of you at the throw"),
]
fx = []
for title, f, pitch, vol, note in EFFECTS:
    fx.append(dict(title=title, file=f, pitch=pitch, vol=vol, note=note, data=b64(sound(f))))

words = []
if TRANSCRIPT and os.path.exists(TRANSCRIPT):
    d = json.load(open(TRANSCRIPT, encoding="utf-8"))
    for s in d["segments"]:
        words.append([round(s["start"], 2), round(s["end"], 2), s["text"].strip()])

page = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "milky_sound_page.template.html"), encoding="utf-8").read()
page = page.replace("/*SONG*/", b64(open(SONG, "rb").read()))
page = page.replace("/*FX*/[]", json.dumps(fx))
page = page.replace("/*WORDS*/[]", json.dumps(words))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(page)
print("wrote %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))
