"""make_metric_grids.py — Generates sub-meter calibrated metric coordinate grids overlaid on
z=20 (ref_016, ref_017), z=19 (ref_014, ref_015), and z=18 (ref_011, ref_012) aerials, where
(0, 0) m = Google Pin (13.7413718, 100.5533082), +X = East (m), +Y = North (m).
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "ref_images")
GRID_DIR = os.path.join(HERE, "metric_grids")
os.makedirs(GRID_DIR, exist_ok=True)

LAT0, LON0 = 13.7413718, 100.5533082
COS_LAT = math.cos(math.radians(LAT0))


def global_wm_px(lat, lon, z):
    n = (2.0 ** z) * 256.0
    gx = (lon + 180.0) / 360.0 * n
    s = math.sin(math.radians(lat))
    gy = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return gx, gy


try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 12)
except OSError:
    fnt = ImageFont.load_default()

CONFIGS = [
    ("z20_sat_grid.jpg", "ref_016.jpg", 20, 817168, 483872, 5, 800, 10),
    ("z20_hyb_grid.jpg", "ref_017.jpg", 20, 817168, 483872, 5, 800, 10),
    ("z19_sat_grid.jpg", "ref_014.jpg", 19, 408583, 241935, 5, 800, 25),
    ("z19_hyb_grid.jpg", "ref_015.jpg", 19, 408583, 241935, 5, 800, 25),
    ("z18_sat_grid.jpg", "ref_011.jpg", 18, 204290, 120966, 5, 800, 50),
    ("z18_hyb_grid.jpg", "ref_012.jpg", 18, 204290, 120966, 5, 800, 50),
]

for out_name, src_name, z, stx, sty, tiles_n, img_px, step_m in CONFIGS:
    im = Image.open(os.path.join(IMG_DIR, src_name)).convert("RGB")
    d = ImageDraw.Draw(im)
    gx0, gy0 = global_wm_px(LAT0, LON0, z)
    scale = img_px / (tiles_n * 256.0)
    cx = (gx0 - stx * 256.0) * scale
    cy = (gy0 - sty * 256.0) * scale
    # True ground meters per image pixel at LAT0:
    mpp_native = 156543.03392 * COS_LAT / (2 ** z)
    mpp = mpp_native / scale
    print(f"{out_name}: origin=({cx:.2f}, {cy:.2f}) px, mpp={mpp:.5f} m/px, span=[{-cx*mpp:.1f}..{(img_px-cx)*mpp:.1f}]x[{-((img_px-cy)*mpp):.1f}..{cy*mpp:.1f}] m")

    # Draw vertical lines (constant X in meters)
    for xm in range(-500, 501, step_m):
        px = cx + xm / mpp
        if 0 <= px < img_px:
            major = (xm % (step_m * 2) == 0) or xm == 0
            col = (255, 60, 60) if xm == 0 else ((255, 255, 0) if major else (180, 220, 255))
            d.line([(px, 0), (px, img_px)], fill=col, width=(2 if xm == 0 else 1))
            if major:
                d.rectangle([px + 1, 2, px + 34, 15], fill=(0, 0, 0))
                d.text((px + 2, 2), f"{xm:+d}", fill=col, font=fnt)

    # Draw horizontal lines (constant Y in meters, +Y = North = UP!)
    for ym in range(-500, 501, step_m):
        py = cy - ym / mpp
        if 0 <= py < img_px:
            major = (ym % (step_m * 2) == 0) or ym == 0
            col = (255, 60, 60) if ym == 0 else ((255, 255, 0) if major else (180, 220, 255))
            d.line([(0, py), (img_px, py)], fill=col, width=(2 if ym == 0 else 1))
            if major:
                d.rectangle([2, py + 1, 36, py + 14], fill=(0, 0, 0))
                d.text((3, py + 1), f"{ym:+d}", fill=col, font=fnt)

    im.save(os.path.join(GRID_DIR, out_name), quality=92)
