"""Builds source/pickle_compare/index.html: every Pickle Surprise model side by side in 3D (the flat balloon card, the 3D thrown
pickle, the blast pickles, the held card), spinning, with their animated textures, so flat vs 3D is obvious. One self-contained
file (models and textures inline); three.js comes from cdnjs.
python make_pickle_compare.py [out.html]      (needs PIL: run it without -I)"""
import base64
import io
import os
import re
import sys

from PIL import Image

MOD = r"G:\Quake\Combat\BakersfieldQuake"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "pickle_compare", "index.html")

MODELS = [  # (file, title, what the game uses it for)
    ("pickle", "Standing pickle: 16-view sprite (NEW)", "progs/pickle.md3: the balloon. 16 cards, one per view of the turntable; it turns to face you and shows the view from where you stand (orbit it!)"),
    ("pickle_card", "Standing pickle: the OLD single card", "what progs/pickle.md3 was: one card that always shows the front (kept only for this comparison)"),
    ("pickle_bomb", "Thrown pickle (the grenade)", "progs/pickle_bomb.md3: tumbles through the air, sticks to what it hits"),
    ("pickle_gib", "Blast pickles", "progs/pickle_gib.md3: the shower of pickles the explosion throws"),
    ("v_pickle", "Held in your hand", "progs/v_pickle.md3: the view model (the fist and pickle from the hold video)"),
]


def shaders():
    s = open(os.path.join(MOD, "scripts", "pickle.shader"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^(progs/\w+)\s*\{(.*?)^\}", s, re.S | re.M):
        body = m.group(2)
        a = re.search(r"animmap\s+([\d.]+)\s+(.*)", body)
        one = re.search(r"^\s*map\s+(\S+)", body, re.M)
        if a:
            out[m.group(1)] = dict(fps=float(a.group(1)), frames=a.group(2).split(), alpha="alphafunc" in body)
        elif one:
            out[m.group(1)] = dict(fps=0, frames=[one.group(1)], alpha="alphafunc" in body)
        else:
            out[m.group(1)] = None
    return out


def png_uri(name, width=None):
    im = Image.open(os.path.join(MOD, name + ".png")).convert("RGBA")
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode("ascii")


def main():
    sh = shaders()
    tex = {}
    for name, s in sh.items():
        for f in s["frames"]:
            if f in tex:
                continue
            n = int(re.search(r"(\d+)$", f).group(1)) if f.startswith("progs/vpk_") else None
            if n is not None and n % 2:          # the hold video: every other frame is plenty, and 256 px wide
                s["frames"] = [g if g != f else "progs/vpk_%02d" % (n - 1) for g in s["frames"]]
                continue
            tex[f] = png_uri(f, 256 if n is not None else None)
    tex["progs/pickle_skin"] = png_uri("progs/pickle_skin")
    models = []
    for f, title, what in MODELS:
        path = os.path.join(MOD, "progs", f + ".md3")
        if f == "pickle_card":
            path = os.path.join(HERE, "out", "progs", "pickle_card.md3")
        data = open(path, "rb").read()
        models.append(dict(id=f, title=title, what=what, md3=base64.b64encode(data).decode("ascii")))
    # a shader name with no .shader entry is a plain texture
    plain = {"progs/pickle_skin": dict(fps=0, frames=["progs/pickle_skin"], alpha=False)}
    allsh = dict(plain)
    allsh.update({k: v for k, v in sh.items() if v})
    import json
    data = "const MODELS = %s;\nconst SHADERS = %s;\nconst TEX = %s;\n" % (
        json.dumps(models), json.dumps(allsh), json.dumps(tex))
    tpl = open(os.path.join(HERE, "pickle_compare.template.html"), encoding="utf-8").read()
    html = tpl.replace("/*DATA*/", data)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    print("wrote", os.path.abspath(OUT), "%.1f MB" % (len(html) / 1e6), len(tex), "textures")


main()
