"""Spawn-protection aura: progs/aura.md3 (a tall bubble that fits a player, one frame), progs/aura.png and scripts/aura.shader
(additive, scrolling bands). bm_match.qc spawns it around a protected player.
python build_aura_assets.py   (the WindowsApps Python 3.13: it has PIL and numpy)"""
import math
import os

import numpy as np
from PIL import Image

import md3lib

ROOT = "G:/Quake/Combat/BakersfieldQuake/"
RX, RZ = 30.0, 42.0           # a player is 32 wide and 56 tall; the bubble clears them
ZOFF = 4.0
SEG, RINGS = 24, 14

# texture: soft cyan bands that wrap around, brighter at the edges of each band; baked dark (the scene brightness is x2.5, and it is additive)
W = H = 128
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
band = 0.5 + 0.5 * np.sin(y / H * 2 * math.pi * 3 + np.sin(x / W * 2 * math.pi * 4) * 1.2)
hexv = 0.5 + 0.5 * np.sin(x / W * 2 * math.pi * 8) * np.sin(y / H * 2 * math.pi * 6)
v = 0.10 + 0.55 * band ** 3 + 0.25 * hexv ** 4
img = np.zeros((H, W, 3), np.float32)
img[..., 0] = v * 0.25
img[..., 1] = v * 0.75
img[..., 2] = v * 1.0
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(ROOT + "progs/aura.png")

verts, st, tris = [], [], []
for r in range(RINGS + 1):
    lat = math.pi * r / RINGS                      # 0 = top pole
    for s in range(SEG + 1):
        a = 2 * math.pi * s / SEG
        verts.append((RX * math.sin(lat) * math.cos(a), RX * math.sin(lat) * math.sin(a), ZOFF + RZ * math.cos(lat)))
        st.append((s / SEG * 2, r / RINGS))
for r in range(RINGS):
    for s in range(SEG):
        a = r * (SEG + 1) + s
        b = a + SEG + 1
        tris.append((a, b, a + 1))
        tris.append((a + 1, b, b + 1))
norms = [(vx / RX / RX, vy / RX / RX, (vz - ZOFF) / RZ / RZ) for vx, vy, vz in verts]
surf = dict(name="aura", shader="progs/aura", tris=tris, st=st, frames=[(verts, norms)])
md3lib.write(ROOT + "progs/aura.md3", dict(name="aura", surfaces=[surf], nframes=1))

os.makedirs(ROOT + "scripts", exist_ok=True)
open(ROOT + "scripts/aura.shader", "w").write("""// written by mm_tools/build_aura_assets.py
progs/aura
{
	cull none
	{
		map progs/aura
		blendfunc add
		tcmod scroll 0 0.6
	}
}
""")
print("aura assets written")
