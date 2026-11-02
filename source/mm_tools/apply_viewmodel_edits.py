"""Bakes the poses made in the first-person model editor (source/viewmodel_editor/index.html) into progs/v_*.md3.

python -I apply_viewmodel_edits.py <viewmodel_edits.json> [--dry-run]

The page's "Download edits" button writes the JSON:  {"v_googun": {"pos": [x, y, z], "rot": [roll, pitch, yaw], "scale": 1}, ...}
Each edit is relative to the ORIGINAL model, which is kept as progs/<name>.md3.pre_vmedit (made the first time a model is
edited), so applying the same file twice gives the same result and an all-zero edit restores the original.
The edits that are in force are remembered in source/viewmodel_editor/edits.json; rebuild the page afterwards:
python -I build_viewmodel_editor.py

The maths is the same as the page's:  q = pivot + pos + R * scale * (p - pivot)   (eye space: x forward, y left, z up)
  R = yaw * pitch * roll  (roll first):  roll turns +Y towards +Z, pitch +  = nose up (+X towards +Z), yaw + = turn left (+X towards +Y)
  pivot = centre of the model's bounding box in frame 0 (the same for every frame, so the animation stays rigid)
"""
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

ROOT = "G:/Quake/Combat/BakersfieldQuake/"
PROGS = ROOT + "progs/"
EDITS = ROOT + "source/viewmodel_editor/edits.json"


def pivot_of(model):
    pts = [v for s in model["surfaces"] for v in s["frames"][0][0]]
    return tuple((min(p[k] for p in pts) + max(p[k] for p in pts)) / 2 for k in range(3))


def make_xform(pivot, pos, rot, scale):
    r, p, y = (math.radians(a) for a in rot)
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)

    def rotate(v):
        x, yy, z = v
        yy, z = yy * cr - z * sr, yy * sr + z * cr          # roll
        x, z = x * cp - z * sp, x * sp + z * cp              # pitch (nose up)
        x, yy = x * cy - yy * sy, x * sy + yy * cy           # yaw (left)
        return (x, yy, z)

    def point(v):
        d = rotate(tuple((v[k] - pivot[k]) * scale for k in range(3)))
        return tuple(pivot[k] + d[k] + pos[k] for k in range(3))

    return point, rotate


def bake(base_path, out_path, edit):
    m = md3lib.read(base_path)
    point, rotate = make_xform(pivot_of(m), edit["pos"], edit["rot"], edit["scale"])
    for s in m["surfaces"]:
        s["frames"] = [([point(v) for v in vv], [rotate(n) for n in nn]) for vv, nn in s["frames"]]
    md3lib.write(out_path, m)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        sys.exit(__doc__)
    new = json.load(open(args[0], encoding="utf-8"))
    cur = json.load(open(EDITS)) if os.path.exists(EDITS) else {}
    for name, e in new.items():
        e = dict(pos=[float(v) for v in e["pos"]], rot=[float(v) for v in e["rot"]], scale=float(e["scale"]))
        deployed = PROGS + name + ".md3"
        base = deployed + ".pre_vmedit"
        if not os.path.exists(deployed):
            print("skip", name, "(no such model)")
            continue
        print(name, e, "(dry run)" if dry else "")
        if dry:
            continue
        if not os.path.exists(base):
            shutil.copy(deployed, base)
        bake(base, deployed, e)
        cur[name] = e
    if not dry:
        os.makedirs(os.path.dirname(EDITS), exist_ok=True)
        json.dump(cur, open(EDITS, "w"), indent=1)
        print("wrote", EDITS, "- now run build_viewmodel_editor.py to refresh the page")


if __name__ == "__main__":
    main()
