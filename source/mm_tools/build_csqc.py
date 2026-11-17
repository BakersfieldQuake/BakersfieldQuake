"""Compile the Combat+ HUD (decompiled from quake15\csprogs.dat into BakersfieldQuake\source\qc_combat_decomp\csqc, plus bm_hud.qc,
the Bakersfield LAN overlay) and install it as BakersfieldQuake\csprogs.dat (which overrides quake15's).
The decompiled system defs give a different header CRC than the original build; DarkPlaces finds CSQC
globals and fields by name, so the original CRC (23147) is stamped back into the header.
python -I build_csqc.py"""
import shutil
import struct
import subprocess
import sys

import os
D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\csqc\\"
FTEQCC = "D:/vibe/quake1opensource/engines/win64/fteqcc64.exe"
if not os.path.isfile(FTEQCC):
    FTEQCC = "G:/Quake/LOLQuake/tools/fteqcc64.exe"
if not os.path.isfile(FTEQCC):
    FTEQCC = "D:/vibe/fteqw/2025-09-27-github/fteqcc64.exe"
r = subprocess.run([FTEQCC, "-srcfile", "progs.src"], cwd=D)
if r.returncode:
    sys.exit("compile failed")
d = bytearray(open(D + "progs.dat", "rb").read())
struct.pack_into("<i", d, 4, struct.unpack_from("<i", open(D + "csprogs_orig.dat", "rb").read(), 4)[0])
open("G:\Quake\Combat\BakersfieldQuake\csprogs.dat", "wb").write(d)
print("installed csprogs.dat (%d bytes)" % len(d))
