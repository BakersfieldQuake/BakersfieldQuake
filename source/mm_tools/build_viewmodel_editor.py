"""Builds source/viewmodel_editor/index.html: a first-person model editor for every progs/v_*.md3.
The models (the originals, progs/<name>.md3.pre_vmedit once a model has been edited, else the deployed file) and their
textures are embedded, so the page is one file. python -I build_viewmodel_editor.py
Edits made in the page are downloaded as JSON and baked into the models with apply_viewmodel_edits.py."""
import base64
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

ROOT = "G:/Quake/Combat/BakersfieldQuake/"
PROGS = ROOT + "progs/"
OUT = ROOT + "source/viewmodel_editor/index.html"
EDITS = ROOT + "source/viewmodel_editor/edits.json"

# animation clips the QC plays (label, first frame, last frame, fps, loop)
CLIPS = {
    "v_megaman": [("idle", 0, 15, 10, 1), ("fire (whole shot)", 16, 35, 20, 0), ("launch (frame 19)", 19, 19, 1, 1), ("recoil + steam", 19, 24, 12, 0), ("reload lifts next one", 25, 35, 15, 0), ("empty rails", 36, 36, 1, 1)],
    "v_googun": [("idle", 0, 0, 1, 1), ("fire kick", 0, 6, 12, 0)],
    "_fun": [("idle", 0, 15, 10, 1), ("fire kick", 16, 18, 12, 0), ("gone", 19, 19, 1, 1), ("coming back", 20, 21, 6, 0)],
}

models = {}
for f in sorted(glob.glob(PROGS + "v_*.md3")):
    name = os.path.basename(f)[:-4]
    src = f + ".pre_vmedit" if os.path.exists(f + ".pre_vmedit") else f
    m = md3lib.read(src)
    if not sum(len(s["tris"]) for s in m["surfaces"]) > 8:
        continue
    tex = {}
    for s in m["surfaces"]:
        p = ROOT + s["shader"] + ".png"
        if s["shader"] not in tex and os.path.exists(p):
            tex[s["shader"]] = "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
    n = m["nframes"]
    clips = CLIPS.get(name) or (CLIPS["_fun"] if n == 22 else [("all frames", 0, n - 1, 10, 1)])
    clips = [[l, a, min(b, n - 1), fps, lp] for l, a, b, fps, lp in clips if a < n]
    models[name] = dict(md3=base64.b64encode(open(src, "rb").read()).decode(), tex=tex, clips=clips, frames=n)
    print(name, n, "frames,", len(tex), "textures,", "base:", os.path.basename(src))

edits = json.load(open(EDITS)) if os.path.exists(EDITS) else {}
fov = 111.0
for line in open(ROOT + "config.cfg", encoding="utf-8", errors="replace"):
    if line.startswith('"fov"') or line.startswith("fov "):
        fov = float(line.replace('"', " ").split()[1])
print("game fov", fov)
data = dict(models=models, edits=edits, fov=fov, build=str(int(time.time())))
t = open(HERE + "/viewmodel_editor.template.html", encoding="utf-8").read()
js = json.dumps(data).replace("</", "<\\/")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(t.replace("__DATA__", js))
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
