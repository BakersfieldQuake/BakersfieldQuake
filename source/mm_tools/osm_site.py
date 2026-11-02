"""OSM extract -> local plan in feet, for transplanting a real site into bklan.
python -I osm_site.py <osm.xml> <lat> <lon> <out.json> [plan.png] [radius_ft]
x = east, y = north, in feet from (lat, lon). Keeps buildings, roads, parks, pitches, playgrounds, barriers, trees and
any node or way with a name. Map data (c) OpenStreetMap contributors, ODbL."""
import json
import math
import sys
import xml.etree.ElementTree as ET

src, LAT0, LON0, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
FT = 3.28084
MX = 111320 * math.cos(math.radians(LAT0)) * FT
MY = 110574 * FT
root = ET.parse(src).getroot()
nodes, ntags = {}, {}
for n in root.iter("node"):
    nodes[n.get("id")] = ((float(n.get("lon")) - LON0) * MX, (float(n.get("lat")) - LAT0) * MY)
    t = {k.get("k"): k.get("v") for k in n.iter("tag")}
    if t:
        ntags[n.get("id")] = t
res = {"ways": [], "points": []}
KEEP = ("building", "highway", "leisure", "landuse", "barrier", "natural", "amenity", "man_made", "tourism", "historic",
        "surface", "parking", "sport")
for w in root.iter("way"):
    t = {k.get("k"): k.get("v") for k in w.iter("tag")}
    if not any(k in t for k in KEEP) and "name" not in t:
        continue
    pts = [[round(c, 1) for c in nodes[nd.get("ref")]] for nd in w.iter("nd") if nd.get("ref") in nodes]
    res["ways"].append({"id": w.get("id"), "tags": t, "pts": pts})
for nid, t in ntags.items():
    res["points"].append({"id": nid, "tags": t, "pt": [round(c, 1) for c in nodes[nid]]})
json.dump(res, open(out, "w"))
print(len(res["ways"]), "ways,", len(res["points"]), "tagged nodes ->", out)

if len(sys.argv) > 5:
    from PIL import Image, ImageDraw
    R = float(sys.argv[6]) if len(sys.argv) > 6 else 700
    S = 1400 / (2 * R)
    im = Image.new("RGB", (1400, 1400), (24, 24, 24))
    d = ImageDraw.Draw(im)
    P = lambda q: ((q[0] + R) * S, (R - q[1]) * S)
    step = 50 if R <= 400 else 100
    for g in range(-int(R) // step * step, int(R) + 1, step):
        c = (60, 60, 60) if g % (step * 5) else (110, 110, 110)
        d.line([P((g, -R)), P((g, R))], fill=c)
        d.line([P((-R, g)), P((R, g))], fill=c)
        if g % (step * 2) == 0:
            d.text(P((g + 3, R - 3)), str(g), fill="yellow")
            d.text(P((-R + 3, g - 3)), str(g), fill="yellow")
    for w in res["ways"]:
        t, pts = w["tags"], [P(q) for q in w["pts"]]
        if len(pts) < 2:
            continue
        if "building" in t:
            d.polygon(pts, outline=(120, 200, 255))
            cx = sum(q[0] for q in w["pts"]) / len(w["pts"])
            cy = sum(q[1] for q in w["pts"]) / len(w["pts"])
            d.text(P((cx, cy)), w["id"][-4:], fill=(160, 230, 255))
        elif "highway" in t:
            d.line(pts, fill=(200, 160, 40) if t["highway"] not in ("service", "footway", "path") else (110, 110, 60),
                   width=3 if t["highway"] not in ("service", "footway", "path") else 1)
        elif t.get("leisure") in ("park", "pitch", "playground") or t.get("landuse") == "grass":
            d.polygon(pts, outline=(80, 200, 80))
        else:
            d.line(pts, fill=(150, 90, 150))
        if t.get("name") and "building" not in t:
            q = w["pts"][len(w["pts"]) // 2]
            d.text(P(q), t["name"][:30], fill=(255, 220, 120))
    for p in res["points"]:
        t = p["tags"]
        if any(k in t for k in ("name", "natural", "addr:housenumber", "leisure", "man_made", "tourism")):
            q = P(p["pt"])
            d.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], fill=(255, 90, 90))
            lab = t.get("name") or t.get("addr:housenumber") or t.get("natural") or t.get("leisure") or ""
            if t.get("natural") != "tree":
                d.text((q[0] + 3, q[1]), lab[:24], fill=(255, 140, 140))
    im.save(sys.argv[5])
