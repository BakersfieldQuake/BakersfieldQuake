"""The Bonk Hammer assets (it replaces the axe, see hammer.qc), copied from Bonk Jam into BakersfieldQuake:
  progs/v_hammer.mdl        Bonk Jam's v_hammer_default.mdl (255 frames: charge, release, hit, dash, hop, whiff, spin)
  progs/spark_blue.mdl      the air-dash spark (7 frames per charge tier)
  progs/spark_yellow.mdl    the hop spark
  sound/hammer/*.wav        the default hammer's charge, clang, slice and frying-pan sounds, plus Bonk Jam's own
                            axhit1/axhit2 (renamed into hammer/ so Combat+'s weapons/axhit*.wav stay as they are)
Bonk Jam (Kebby, fairweather, spootnik1; ModDB bonkjam.3.zip) has no licence for these: private LAN only, credit them,
ask before sharing (see _reference\\REPORT.md).
python -I build_hammer.py"""
import os
import shutil

BJ = r"G:\Quake\Combat\_reference\BonkJam\extracted\bonkjam"
ROOT = r"G:\Quake\Combat\BakersfieldQuake"

FILES = [
    (r"pak1_pak\progs\v_hammer_default.mdl", r"progs\v_hammer.mdl"),
    (r"pak1_pak\progs\spark_blue.mdl", r"progs\spark_blue.mdl"),
    (r"pak1_pak\progs\spark_yellow.mdl", r"progs\spark_yellow.mdl"),
    (r"pak0_pak\sound\weapons\axhit1.wav", r"sound\hammer\axhit1.wav"),
    (r"pak0_pak\sound\weapons\axhit2.wav", r"sound\hammer\axhit2.wav"),
]
for n in ("charge_med", "charge_full", "hammer_clang", "hammer_clang2", "slice1", "slice2", "slice3", "frying_pan"):
    FILES.append((r"pak1_pak\sound\hammer\%s.wav" % n, r"sound\hammer\%s.wav" % n))

for src, dst in FILES:
    d = os.path.join(ROOT, dst)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copyfile(os.path.join(BJ, src), d)
    print("copied", d)
