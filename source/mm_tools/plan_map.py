"""Top-down plan of a .map (brush bounding boxes, coloured by texture, higher ones on top) for checking layouts.
usage: python plan_map.py out/maps/bklan3test.map out/plan.png [x0 y0 x1 y1 scale]   (feet, map frame)"""
import colorsys
import hashlib
import re
import sys

from PIL import Image, ImageDraw, ImageFont

OX, OY, U = (int(__import__("os").environ.get("PLAN_OX", -110)), int(__import__("os").environ.get("PLAN_OY", 225)), 12)
src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7]) if len(sys.argv) > 6 else (-830, -1120, 1880, 800)
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 0.6
ZMAX = float(__import__("os").environ.get("PLAN_ZMAX", 99999))
num = re.compile(r"\(\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*\)")
tex_re = re.compile(r"\)\s+([A-Za-z{_][\w{}.-]*)\s+-?[\d.]+\s+-?[\d.]+")
COL = {"bk_road": (70, 70, 74), "bk_asphalt": (110, 110, 112), "bk_walk": (200, 196, 150), "bk_lawn": (110, 170, 80),
       "bk_grass": (100, 160, 70), "bk_dirt": (140, 110, 80), "bk_roof": (190, 190, 190), "bk3_sw": (120, 100, 60),
       "bk_drygrass": (150, 140, 80), "bk_sand": (220, 200, 140), "bk_leaf": (30, 110, 40), "bk_yline": (250, 210, 0),
       "bk_wline": (240, 240, 240), "bk3_jump": (255, 220, 0), "bk3_tp": (0, 220, 255), "bk_steel": (90, 90, 100)}


def color(t):
    if t in COL:
        return COL[t]
    h = int(hashlib.md5(t.encode()).hexdigest()[:6], 16)
    return tuple(int(v * 255) for v in colorsys.hls_to_rgb((h % 360) / 360, 0.5, 0.35))


text = open(src).read()
ents = []                      # [classname, kv text, [brush text]]
depth, cur, br = 0, None, None
for line in text.split("\n"):
    if line == "{":
        depth += 1
        if depth == 1:
            cur = ["", "", []]
        else:
            br = []
    elif line == "}":
        if depth == 2:
            cur[2].append("\n".join(br))
        elif depth == 1:
            ents.append(cur)
        depth -= 1
    elif depth == 2:
        br.append(line)
    elif depth == 1:
        cur[1] += line + "\n"
items = []
for _, kv, brs in ents:
    m = re.search(r'"classname" "([^"]+)"', kv)
    cls = m.group(1) if m else ""
    for b in brs:
        pts = [tuple(map(int, g)) for g in num.findall(b)]
        if not pts:
            continue
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        tex = [t for t in tex_re.findall(b) if t not in ("clip", "sky_bk")]
        t = tex[-1] if tex else "clip"
        if cls.startswith("trigger"):
            t = "bk3_jump" if cls == "trigger_push" else "bk3_tp"
        if lo[2] / U > ZMAX:
            continue                   # PLAN_ZMAX: leave out roofs and whatever starts above it (see inside buildings)
        items.append((hi[2], lo[0] / U + OX, lo[1] / U + OY, hi[0] / U + OX, hi[1] / U + OY, t, cls))
items.sort(key=lambda r: r[0])
W, H = int((x1 - x0) * sc), int((y1 - y0) * sc)
im = Image.new("RGB", (W, H), (30, 30, 36))
d = ImageDraw.Draw(im)
P = lambda x, y: ((x - x0) * sc, (y1 - y) * sc)
for z, ax, ay, bx, by, t, cls in items:
    if t == "clip" or z < -1:
        continue
    p0, p1 = P(ax, by), P(bx, ay)
    d.rectangle([p0[0], p0[1], max(p1[0], p0[0] + 0.6), max(p1[1], p0[1] + 0.6)], fill=color(t))
f = ImageFont.load_default()
for e in ents:
    m = re.search(r'"classname" "([^"]+)"', e[1])
    o = re.search(r'"origin" "(-?\d+) (-?\d+) (-?\d+)"', e[1])
    if m and o and m.group(1) in ("info_player_deathmatch", "info_player_start", "info_teleport_destination", "item_armor2"):
        p = P(int(o.group(1)) / U + OX, int(o.group(2)) / U + OY)
        d.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], outline=(255, 60, 60) if "player" in m.group(1) else (255, 255, 255))
for gx in range(int(x0 // 200) * 200, int(x1) + 1, 200):
    p = P(gx, y0)
    d.line([p, (p[0], 0)], fill=(60, 60, 70))
    d.text((p[0] + 2, H - 12), str(gx), fill=(230, 230, 230), font=f)
for gy in range(int(y0 // 200) * 200, int(y1) + 1, 200):
    p = P(x0, gy)
    d.line([p, (W, p[1])], fill=(60, 60, 70))
    d.text((2, p[1] + 2), str(gy), fill=(230, 230, 230), font=f)
im.save(dst)
print(dst, im.size, len(items), "brushes")
