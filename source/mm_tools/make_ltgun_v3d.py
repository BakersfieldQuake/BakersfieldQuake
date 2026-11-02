"""progs/ltg_v3d.md3: a copy of the other agent's 3D laptop viewmodel (progs/v_laptop.md3, build_laptop_gun.py) moved down and a little
to the right and made 10% smaller, so it does not sit on the crosshair and hide the laser dot. Their file is not touched; the copy keeps
their shaders and textures. Re-run it after build_laptop_gun.py. python make_ltgun_v3d.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

PROGS = r"G:\Quake\Combat\BakersfieldQuake\progs"
SCALE = 0.9
DY = -5.0       # +Y is left: negative moves it right
DZ = -6.0       # down

m = md3lib.read(os.path.join(PROGS, "v_laptop.md3"))
for s in m["surfaces"]:
    s["frames"] = [([(x * SCALE, y * SCALE + DY, z * SCALE + DZ) for x, y, z in verts], normals) for verts, normals in s["frames"]]
m["name"] = "ltg_v3d"
md3lib.write(os.path.join(PROGS, "ltg_v3d.md3"), m)
print("wrote progs/ltg_v3d.md3 (%d frames)" % len(m["surfaces"][0]["frames"]))
