"""Sunny-day pass over the bklan textures (bk_*): the photos came from 2001 tape and a grey February, so push the colour and
lift the brightness. Originals are kept in out/tex_orig so the pass can be re-run with other numbers.
Skips the glow masks (and oc_*, the indoor Orcom room). usage: python sunny_pass.py [brightness] [saturation]"""
import os
import shutil
import sys

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
ORIG = os.path.join(HERE, "out", "tex_orig")
LIFT = float(sys.argv[1]) if len(sys.argv) > 1 else 1.28
SAT = float(sys.argv[2]) if len(sys.argv) > 2 else 1.45

os.makedirs(ORIG, exist_ok=True)
n = 0
for f in sorted(os.listdir(TEX)):
    if not f.startswith(("bk_", "{")) or f.endswith("_glow.png") or not f.endswith(".png"):
        continue
    keep = os.path.join(ORIG, f)
    if not os.path.exists(keep):
        shutil.copy(os.path.join(TEX, f), keep)
    im = Image.open(keep)
    a = im.getchannel("A") if im.mode == "RGBA" else None
    rgb = im.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(SAT)
    rgb = ImageEnhance.Brightness(rgb).enhance(LIFT)
    if a is not None:
        rgb.putalpha(a)
    rgb.save(os.path.join(TEX, f))
    n += 1
print("sunny pass on", n, "textures (lift %.2f, saturation %.2f)" % (LIFT, SAT))
