"""Builds G:\\Quake\\Combat\\robdob_viewmodel_tuner.html from progs/v_robdob.mdl: the Rob Dob head in first person, with
sliders for where it floats, which way it faces, and how big it is.  Copy the settings it shows, then run
apply_robdob_vm.py (the page prints the exact command).

python -E -P make_robdob_tuner.py
"""
import base64
import io
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import robdob_vm as RV

OUT = r"G:\Quake\Combat\robdob_viewmodel_tuner.html"
TEMPLATE = os.path.join(RV.HERE, "robdob_tuner.template.html")

cur = RV.current()
md = RV.read()
L = RV.head_local(md, cur)
r3 = lambda a: [round(float(v), 3) for v in np.asarray(a).reshape(-1)]
st = md["st"]
uv = np.stack([(st[:, 0] + 0.5) / md["sw"], (st[:, 1] + 0.5) / md["sh"]], 1)
geo = dict(v=r3(L), uv=r3(uv), i=[int(i) for i in md["tri"].reshape(-1)],
           defaults=dict(pos=cur["pos"], yaw=cur["yaw"], pitch=cur["pitch"], roll=cur["roll"], height=cur["height"]),
           command=r"C:\Users\qxdc\AppData\Local\Microsoft\WindowsApps\python3.13.exe -E -P " +
                   os.path.join(RV.HERE, "apply_robdob_vm.py"))
tga = Image.open(RV.MDL + "_0.tga").convert("RGB")
bio = io.BytesIO()
tga.save(bio, "JPEG", quality=90)
html = open(TEMPLATE, encoding="utf-8").read()
html = html.replace("__GEO__", json.dumps(geo, separators=(",", ":"))).replace("__TEX__", base64.b64encode(bio.getvalue()).decode())
open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, len(html), "bytes;", len(L), "verts,", len(md["tri"]), "tris; current pose", cur)
