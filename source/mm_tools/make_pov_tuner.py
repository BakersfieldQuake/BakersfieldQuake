"""Assembles pov_tuner.html from pov_tuner.template.html + exported geometry + texture.
Export geometry first:  MM_EXPORT=tuner_geo.json python -I build_viewmodel.py mm_parts.json outdir
python -I make_pov_tuner.py <geo.json> <tex.b64> <out.html>"""
import sys
geo, tex, out = sys.argv[1:4]
t = open("G:\Quake\Combat\BakersfieldQuake\source\mm_tools\pov_tuner.template.html", encoding="utf-8").read()
t = t.replace("__GEO__", open(geo, encoding="utf-8").read()).replace("__TEX__", open(tex).read())
assert "</script>" not in open(geo).read()
open(out, "w", encoding="utf-8").write(t)
print("wrote", out, len(t), "bytes")
