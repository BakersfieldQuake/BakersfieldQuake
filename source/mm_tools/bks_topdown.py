"""Top-down PNG of a generated .map (brush bounds only), for planning bakolansmall.
usage: python bks_topdown.py in.map out.png ox oy x0 y0 x1 y1 [px_per_ft]     (ox, oy = the map's origin in feet; window in feet)"""
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from bks_mapio import read_map

src, dst = sys.argv[1], sys.argv[2]
ox, oy, x0, y0, x1, y1 = (float(v) for v in sys.argv[3:9])
S = float(sys.argv[9]) if len(sys.argv) > 9 else 1.0
W, H = int((x1 - x0) * S), int((y1 - y0) * S)
im = Image.new("RGB", (W, H), (30, 30, 34))
dr = ImageDraw.Draw(im)
boxes = []
for e in read_map(src):
    for b in e.brushes:
        if "sky_bk" in b.texs or "clip" in b.texs:
            continue
        boxes.append((b.hi[2], b))
boxes.sort(key=lambda t: t[0])
for top, b in boxes:
    fx0, fy0 = b.lo[0] / 12 + ox, b.lo[1] / 12 + oy
    fx1, fy1 = b.hi[0] / 12 + ox, b.hi[1] / 12 + oy
    if fx1 < x0 or fx0 > x1 or fy1 < y0 or fy0 > y1:
        continue
    h = top / 12
    v = int(min(255, 70 + h * 7))
    col = (v, v, v) if h > 0.6 else (60, 70, 60)
    dr.rectangle([(fx0 - x0) * S, H - (fy1 - y0) * S, (fx1 - x0) * S, H - (fy0 - y0) * S], fill=col)
# grid every 100 ft
for gx in range(int(x0 // 100 * 100), int(x1) + 1, 100):
    dr.line([(gx - x0) * S, 0, (gx - x0) * S, H], fill=(90, 40, 40))
    dr.text(((gx - x0) * S + 2, 2), str(gx), fill=(255, 200, 200))
for gy in range(int(y0 // 100 * 100), int(y1) + 1, 100):
    dr.line([0, H - (gy - y0) * S, W, H - (gy - y0) * S], fill=(40, 40, 90))
    dr.text((2, H - (gy - y0) * S + 2), str(gy), fill=(200, 200, 255))
im.save(dst)
print("saved", dst, im.size)
