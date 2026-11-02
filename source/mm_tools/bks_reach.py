"""Ground-level reachability of a generated .map (the bots of this mod do not navigate without waypoints, so this stands in for a bot run).
Every brush that is taller than a step (18 units) and starts below head height (60 units) is an obstacle, grown by the player's half width;
a flood fill from the first deathmatch spawn then shows which spawns / items / teleports can be walked to (items up on roofs or
behind jump pads are listed as 'raised' and skipped). Writes a PNG: green = reachable floor, red = enclosed floor, grey = obstacle.
usage: python bks_reach.py in.map out.png ox oy [cell_ft]"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bks_mapio import read_map

src, dst = sys.argv[1], sys.argv[2]
ox, oy = float(sys.argv[3]), float(sys.argv[4])
CELL = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5
GROW = 1.34                                                   # feet: player half width (16 units) plus a little
ents = read_map(src)
obst, ground = [], []
for e in ents:
    if e.cls in ("worldspawn", "func_detail", "func_wall"):
        for b in e.brushes:
            if "sky_bk" in b.texs and b.hi[2] - b.lo[2] > 12 * 100:
                ground.append(b)                              # the sky solids outside the hull
                continue
            if b.hi[2] > 18 and b.lo[2] < 60 and b.hi[2] - b.lo[2] > 6:
                obst.append(b)
sky = [b for b in ground]
xs = [b.lo[0] / 12 + ox for b in obst + sky] + [b.hi[0] / 12 + ox for b in obst + sky]
ys = [b.lo[1] / 12 + oy for b in obst + sky] + [b.hi[1] / 12 + oy for b in obst + sky]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
W, H = int((x1 - x0) / CELL) + 1, int((y1 - y0) / CELL) + 1
grid = np.zeros((H, W), dtype=np.uint8)                       # 1 = blocked
for b in obst + sky:
    grow = GROW if b in obst else 0
    a = int((b.lo[0] / 12 + ox - grow - x0) / CELL)
    c = int((b.hi[0] / 12 + ox + grow - x0) / CELL) + 1
    d = int((b.lo[1] / 12 + oy - grow - y0) / CELL)
    f = int((b.hi[1] / 12 + oy + grow - y0) / CELL) + 1
    grid[max(d, 0):max(f, 0), max(a, 0):max(c, 0)] = 1


def cell(x, y):
    return int((y - y0) / CELL), int((x - x0) / CELL)


spawns = [(e, e.origin()) for e in ents if e.cls == "info_player_deathmatch"]
sx, sy, _ = spawns[0][1]
start = cell(sx / 12 + ox, sy / 12 + oy)
seen = np.zeros_like(grid, dtype=bool)
dq = deque([start])
seen[start] = True
if grid[start]:
    print("start cell blocked (grown obstacle):", start)
while dq:
    r, c = dq.popleft()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < H and 0 <= cc < W and not seen[rr, cc] and not grid[rr, cc]:
            seen[rr, cc] = True
            dq.append((rr, cc))
free = (grid == 0)
print("walkable cells: %d, reachable from the first spawn: %d (%.1f%%)" % (free.sum(), seen.sum(), 100.0 * seen.sum() / max(1, free.sum())))
bad = 0
for e in ents:
    if not (e.cls.startswith(("info_player_deathmatch", "weapon_", "item_", "info_teleport_destination")) or e.cls == "trigger_teleport" or e.cls == "trigger_push"):
        continue
    o = e.origin()
    if o is None and e.brushes:
        b = e.brushes[0]
        o = tuple((b.lo[i] + b.hi[i]) // 2 for i in range(3))
    fx, fy, fz = o[0] / 12 + ox, o[1] / 12 + oy, o[2] / 12
    r, c = cell(fx, fy)
    if fz > 9 and not e.cls.startswith("info_player"):
        status = "raised (z %.0f)" % fz
    elif seen[r, c]:
        status = "ok"
    else:
        # a spawn / item just inside a blocked cell (bench, car) still counts if a neighbour is reachable
        near = seen[max(r - 2, 0):r + 3, max(c - 2, 0):c + 3].any()
        status = "ok (edge)" if near else "UNREACHABLE"
    if status == "UNREACHABLE":
        bad += 1
    if status != "ok" or e.cls.startswith(("info_player", "info_teleport")):
        print("%-28s %7.0f %7.0f %5.1f  %s" % (e.cls, fx, fy, fz, status))
print("unreachable gameplay entities:", bad)
img = np.zeros((H, W, 3), dtype=np.uint8)
img[free & ~seen] = (200, 40, 40)
img[seen] = (50, 160, 70)
img[~free] = (70, 70, 80)
Image.fromarray(img[::-1]).save(dst)
print("saved", dst, (W, H), "origin x0 y0", round(x0), round(y0))
if os.environ.get("BKS_DUMP"):                                # ASCII view of a window (feet): '#' blocked, '.' reachable, 'o' free but enclosed
    a, b, c_, d_ = (float(v) for v in os.environ["BKS_DUMP"].split())
    step = max(1, int(round(0.7 / CELL)))
    for yy in np.arange(d_, b, -CELL * step):
        row = ""
        for xx in np.arange(a, c_, CELL * step):
            r, c = cell(xx, yy)
            row += "#" if grid[r, c] else ("." if seen[r, c] else "o")
        print("%6.0f %s" % (yy, row))
