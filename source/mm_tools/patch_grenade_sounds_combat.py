"""The grenade bounce plays JG_BounceSound (jg_splash.qc, the voted rubber ball) instead of weapons/bounce.wav.
Marker-guarded (safe to re-run), keeps weapons.qc.pre_gsound.  Then: python -I build_combat.py
The explosion sound lives in JG_Splash itself, so it needs no patch."""
import shutil
import sys

path = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\weapons.qc"
raw = open(path, encoding="utf-8", errors="surrogateescape", newline="").read()
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")
if "JG_BounceSound" in s:
    sys.exit("already patched")
old = "\tsound7(self, CHAN_WEAPON, \"weapons/bounce.wav\", 1, ATTN_NORM, SNDSPD);\n\tJG_GrenadeBounce();\t// tumble\n"
new = "\tJG_BounceSound();\t// voted rubber-ball bounce (jg_splash.qc)\n\tJG_GrenadeBounce();\t// tumble\n"
if s.count(old) != 1:
    sys.exit("anchor found %d times, expected 1" % s.count(old))
shutil.copy(path, path + ".pre_gsound")
open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write((s.replace(old, new)).replace("\n", "\r\n") if crlf else s.replace(old, new))
print("patched", path)
