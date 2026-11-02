"""Applies a pose from robdob_viewmodel_tuner.html to progs/v_robdob.mdl, and to the VM_* constants in build_floathead.py
so a later full rebuild keeps it.  Backs both up as *.pre_vmfix (once).

python -E -P apply_robdob_vm.py --pos X Y Z --yaw D --pitch D --roll D --height H [--dry]
  pos     where the head floats in eye space (x forward, y left, z up)
  yaw     turn about the vertical, pitch  nod (+ = face tips up), roll  tilt (+ = left ear up)
  height  the head's height in quake units
"""
import argparse
import os
import re
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import robdob_vm as RV

ap = argparse.ArgumentParser()
ap.add_argument("--pos", type=float, nargs=3, required=True)
ap.add_argument("--yaw", type=float, required=True)
ap.add_argument("--pitch", type=float, default=0.0)
ap.add_argument("--roll", type=float, default=0.0)
ap.add_argument("--height", type=float, required=True)
ap.add_argument("--dry", action="store_true", help="check only, write nothing")
a = ap.parse_args()

cur = RV.current()
md = RV.read()
L = RV.head_local(md, cur)
bobs = RV.bob_locals(md, cur)
h = (L[RV.head_mask(md)] * cur["height"])
size, centre = h.max(0) - h.min(0), (h.max(0) + h.min(0)) / 2
print("on disk: pos %s yaw %.1f pitch %.1f roll %.1f height %.2f  (un-posed head box %s, centre %s)" % (
    cur["pos"], cur["yaw"], cur["pitch"], cur["roll"], cur["height"], np.round(size, 2), np.round(centre, 2)))
if abs(size[2] - cur["height"]) > 0.06 * cur["height"] or np.abs(centre).max() > 0.5:
    sys.exit("the mdl does not match build_floathead.py's VM_* constants (rebuilt by hand?): not touching anything")

frames = RV.pose_frames(L, a.pos, a.yaw, a.pitch, a.roll, a.height, bobs=bobs)
if a.dry:
    sys.exit("dry run: ok, nothing written")

for p in (RV.MDL, RV.FLOATHEAD_PY):
    if not os.path.exists(p + ".pre_vmfix"):
        shutil.copy2(p, p + ".pre_vmfix")
RV.write(md, frames)

t = open(RV.FLOATHEAD_PY, encoding="utf-8").read()
f = lambda v: ("%g" % round(v, 2))
t = re.sub(r"^VM_HEIGHT\s*=\s*[-0-9.]+", "VM_HEIGHT = " + f(a.height), t, flags=re.M)
t = re.sub(r"^VM_POS\s*=\s*\([^)]*\)", "VM_POS = (%s, %s, %s)" % tuple(f(v) for v in a.pos), t, flags=re.M)
t = re.sub(r"^VM_YAW\s*=\s*[-0-9.]+", "VM_YAW = " + f(a.yaw), t, flags=re.M)
t = re.sub(r"^VM_PITCH\s*=\s*[-0-9.]+", "VM_PITCH = " + f(a.pitch), t, flags=re.M)
t = re.sub(r"^VM_ROLL\s*=\s*[-0-9.]+", "VM_ROLL = " + f(a.roll), t, flags=re.M)
open(RV.FLOATHEAD_PY, "w", encoding="utf-8").write(t)
print("wrote %s and the VM_* constants in build_floathead.py" % RV.MDL)
