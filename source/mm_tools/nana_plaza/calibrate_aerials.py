"""calibrate_aerials.py — Computes exact Web Mercator pixel scale and metric/inch extents
for all 11 aerials (zoom 15..20) and plots/prints all 17 Street View panorama GPS coordinates.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "manifest.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

LAT0, LON0 = 13.7413718, 100.5533082
DEG_LAT_M = 110641.0  # WGS84 meridional meters/deg at 13.74 deg N
DEG_LON_M = 111319.49 * math.cos(math.radians(LAT0))  # ~108135.4 m/deg
INCH_PER_M = 39.37007874015748  # 1 Quake unit = 1 inch (12 units = 1 ft)

print(f"Center pin: ({LAT0}, {LON0})")
print(f"1 deg lat = {DEG_LAT_M:.2f} m, 1 deg lon = {DEG_LON_M:.2f} m")
print(f"Scale: 1 Quake unit = 1 inch = 0.0254 m ({INCH_PER_M:.4f} units/m, 12.0 units/ft)\n")

print("=== AERIAL IMAGES (Web Mercator at lat 13.7413718) ===")
for im in data["images"]:
    if "AERIALS" in im["h2"]:
        cap = im["caption"]
        # Extract zoom level
        import re
        zm = re.search(r"zoom\s+(\d+)", cap)
        z = int(zm.group(1)) if zm else 0
        # Standard Google Static Maps: 256 px tile at scale=1, or 512 px at scale=2 (@2x).
        # Let's print both scale=1 and scale=2 m/px so we can verify against GPS panos!
        mpp_s1 = 156543.03392 * math.cos(math.radians(LAT0)) / (2 ** z)
        mpp_s2 = mpp_s1 / 2.0
        w, h = im["width"], im["height"]
        print(
            f"ref_{im['id']:03d} ({w}x{h}) z={z}: "
            f"if scale=1 -> {mpp_s1:.4f} m/px ({w*mpp_s1:.1f}m x {h*mpp_s1:.1f}m = {w*mpp_s1*INCH_PER_M:.0f}u); "
            f"if scale=2 -> {mpp_s2:.4f} m/px ({w*mpp_s2:.1f}m x {h*mpp_s2:.1f}m = {w*mpp_s2*INCH_PER_M:.0f}u) | {cap}"
        )

print("\n=== STREET VIEW PANORAMA GPS COORDINATES (relative to Center Pin in meters & inches) ===")
seen = set()
for im in data["images"]:
    if im["pano_id"] and im["pano_id"] not in seen:
        seen.add(im["pano_id"])
        dx_m = (im["lon"] - LON0) * DEG_LON_M
        dy_m = (im["lat"] - LAT0) * DEG_LAT_M
        print(
            f"ref_{im['id']:03d}..{im['id']+7:03d} [{im['h3']:26s}] ({im['pano_date']}): "
            f"lat={im['lat']:.7f}, lon={im['lon']:.7f} -> "
            f"E={dx_m:+7.2f} m ({dx_m*INCH_PER_M:+7.0f} u), N={dy_m:+7.2f} m ({dy_m*INCH_PER_M:+7.0f} u)"
        )
