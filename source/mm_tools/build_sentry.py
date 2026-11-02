"""The sentry gun assets (see sentry.qc), Team Fortress 2.8's own, copied into BakersfieldQuake:
  progs/turrbase.mdl, turrgun.mdl   the tripod and the swivelling gun (frames 3-5 + skin 1 are TF's level 2)
  progs/tgib1-3.mdl                 the pieces it breaks into
  progs/v_span.mdl                  the spanner you hold to build it (0 idle, 1-4 a swing)
  sound/weapons/turrset.wav, turrspot.wav, turridle.wav   built / spotted you / idle sweep (it fires weapons/sniper.wav)
Team Fortress art: Valve owns it now, so keep these to the private LAN (see _reference\\REPORT.md).
Refuses to overwrite anything the game already has under the same name (quake15 or id1).
python -I build_sentry.py"""
import os
import shutil
import struct
import sys
import zipfile

TF = r"G:\Quake\Combat\_reference\TeamFortress\extracted\tf28\FORTRESS\PAK0_pak"
ROOT = r"G:\Quake\Combat\BakersfieldQuake"
FILES = ["progs/turrbase.mdl", "progs/turrgun.mdl", "progs/tgib1.mdl", "progs/tgib2.mdl", "progs/tgib3.mdl", "progs/v_span.mdl",
         "sound/weapons/turrset.wav", "sound/weapons/turrspot.wav", "sound/weapons/turridle.wav"]

taken = set(n.lower() for n in zipfile.ZipFile(r"G:\Quake\Combat\quake15\q15.pk3").namelist())
d = open(r"G:\Quake\Combat\id1\pak0.pak", "rb").read()
off, ln = struct.unpack("<ii", d[4:12])
taken |= {d[off + i * 64:off + i * 64 + 56].split(b"\0")[0].decode().lower() for i in range(ln // 64)}
clash = [f for f in FILES if f in taken]
if clash:
    sys.exit("these names are already used by the game: %s" % clash)

for f in FILES:
    dst = os.path.join(ROOT, f.replace("/", os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(os.path.join(TF, f.replace("/", os.sep)), dst)
    print("copied", dst)
