"""OpenStreetMap -> bklan plan: reads an OSM XML extract (api.openstreetmap.org/api/0.6/map?bbox=...) and writes
bklan_osm.json: every building footprint and road centreline in FEET, in the map's frame:
  origin  the north-east corner of E 21st St and Sacramento St (the curb corner by the LMC building)
  x       along E 21st St, pointing east-south-east (the street grid is turned about 16 degrees from true north)
  y       along Sacramento St, pointing north-north-east (away from E 21st)
Map data (c) OpenStreetMap contributors, ODbL.
python -I bklan_osm.py <osm.xml> [plan.png]"""
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

src = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bklan_osm.json")
FT = 3.28084

root = ET.parse(src).getroot()
nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in root.iter("node")}
LAT0, LON0 = 35.3779, -119.0016
MX = 111320 * math.cos(math.radians(LAT0)) * FT     # feet per degree of longitude
MY = 110574 * FT


def en(lat, lon):
    """east, north in feet from LAT0/LON0"""
    return (lon - LON0) * MX, (lat - LAT0) * MY


ways = []
for w in root.iter("way"):
    tags = {t.get("k"): t.get("v") for t in w.iter("tag")}
    pts = [en(*nodes[nd.get("ref")]) for nd in w.iter("nd") if nd.get("ref") in nodes]
    ways.append((tags, pts))


def named(name, kind="highway"):
    return [p for t, p in ways if kind in t and t.get("name") == name]


# street directions from OSM: E 21st and Sacramento set the frame
def direction(polys):
    pts = [p for poly in polys for p in poly]
    (x0, y0), (x1, y1) = min(pts), max(pts)
    return math.atan2(y1 - y0, x1 - x0)


ang = direction(named("East 21st Street"))
ca, sa = math.cos(-ang), math.sin(-ang)


def rot(p):
    return (p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca)


def line_at(polys, k, near=None):
    """median of coordinate k (0 = x, 1 = y) of a street's points in the rotated frame (only points within 600 ft of
    `near` along the other axis, so far-off bends don't pull it)"""
    pts = [rot(p) for poly in polys for p in poly]
    if near is not None:
        pts = [p for p in pts if abs(p[1 - k] - near) < 600] or pts
    v = sorted(p[k] for p in pts)
    return v[len(v) // 2]


# origin: E 21st centreline x Sacramento centreline
xsac = line_at(named("Sacramento Street"), 0)
y21 = line_at(named("East 21st Street"), 1, near=xsac)
out = {"angle_deg": math.degrees(ang), "origin_note": "E 21st x Sacramento centrelines", "buildings": [], "roads": [],
       "rail": []}


def frame(p):
    x, y = rot(p)
    return [round(x - xsac, 1), round(y - y21, 1)]


for t, pts in ways:
    if len(pts) < 2:
        continue
    fp = [frame(p) for p in pts]
    if "building" in t:
        out["buildings"].append({"tags": t, "pts": fp})
    elif "highway" in t:
        out["roads"].append({"name": t.get("name", ""), "kind": t["highway"], "lanes": t.get("lanes"),
                             "oneway": t.get("oneway"), "bridge": t.get("bridge"), "layer": t.get("layer"), "pts": fp})
    elif "railway" in t:
        out["rail"].append({"kind": t["railway"], "name": t.get("name", ""), "pts": fp})
json.dump(out, open(OUT, "w"), indent=0)
print("angle %.2f deg, %d buildings, %d roads -> %s" % (out["angle_deg"], len(out["buildings"]), len(out["roads"]), OUT))

if len(sys.argv) > 2:
    from PIL import Image, ImageDraw
    S, R = 0.5, 1400                      # px per foot, half-size in feet
    im = Image.new("RGB", (int(2 * R * S), int(2 * R * S)), (24, 24, 24))
    d = ImageDraw.Draw(im)
    P = lambda q: ((q[0] + R) * S, (R - q[1]) * S)
    for g in range(-R, R + 1, 100):
        c = (70, 70, 70) if g % 500 else (110, 110, 110)
        d.line([P((g, -R)), P((g, R))], fill=c)
        d.line([P((-R, g)), P((R, g))], fill=c)
        if g % 500 == 0:
            d.text(P((g + 4, R - 14)), str(g), fill="yellow")
            d.text(P((-R + 4, g + 12)), str(g), fill="yellow")
    for r in out["roads"]:
        d.line([P(q) for q in r["pts"]], fill=(200, 160, 40) if r["kind"] not in ("service", "footway") else (90, 90, 60),
               width=3 if r["kind"] not in ("service", "footway") else 1)
    for r in out["rail"]:
        d.line([P(q) for q in r["pts"]], fill=(150, 60, 60), width=1)
    for i, b in enumerate(out["buildings"]):
        d.polygon([P(q) for q in b["pts"]], outline=(120, 200, 255))
        cx = sum(q[0] for q in b["pts"]) / len(b["pts"])
        cy = sum(q[1] for q in b["pts"]) / len(b["pts"])
        d.text(P((cx - 8, cy + 6)), str(i), fill=(160, 230, 255))
    seen = set()
    for r in out["roads"]:
        if r["name"] and r["name"] not in seen and r["kind"] not in ("service",):
            seen.add(r["name"])
            q = r["pts"][len(r["pts"]) // 2]
            d.text(P(q), r["name"], fill=(255, 220, 120))
    im.save(sys.argv[2])
