import json
import math
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))


def latlon_to_img(lat, lon, z, start_tx, start_ty, tiles_n, img_px):
    n = (2.0 ** z) * 256.0
    gx = (lon + 180.0) / 360.0 * n
    s = math.sin(math.radians(lat))
    gy = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    scale = img_px / (tiles_n * 256.0)
    return (gx - start_tx * 256.0) * scale, (gy - start_ty * 256.0) * scale


im = Image.open(os.path.join(HERE, "ref_images", "ref_016.jpg")).convert("RGB")
d = ImageDraw.Draw(im)
cx, cy = latlon_to_img(13.7413718, 100.5533082, 20, 817168, 483872, 5, 800)
d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(255, 0, 0), outline=(255, 255, 255), width=2)
print(f"Google Pin on ref_016 (z=20): ({cx:.2f}, {cy:.2f})")

seen = set()
for item in data["images"]:
    if item["pano_id"] and item["pano_id"] not in seen:
        seen.add(item["pano_id"])
        px, py = latlon_to_img(item["lat"], item["lon"], 20, 817168, 483872, 5, 800)
        col = (0, 255, 255) if "Ext" in item["h3"] else (255, 230, 0)
        d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=col, outline=(0, 0, 0), width=1)
        d.text((px + 7, py - 6), item["h3"][:16], fill=col)
        print(f"{item['h3']:26s}: ({px:6.1f}, {py:6.1f})")

im.save(os.path.join(HERE, "z20_gps_check.jpg"), quality=92)
