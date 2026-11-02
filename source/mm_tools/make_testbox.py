"""Writes testbox.map: a wide open, completely empty box (3072 x 3072, 768 high) for testing guns. Deathmatch spawns round
a ring, and a few health / armor / ammo boxes along one wall. The bots on this map are target dummies (BM_DummyBot in
bm_match.qc): they only walk in small circles and never shoot, and the match is kept at 4 players. Compile + install:
python -I make_testbox.py <out.map>
qbsp -> light -> vis (ericw-tools) -> BakersfieldQuake/maps/testbox.bsp"""
import math
import sys

WAD = "G:/Quake/QBJ3/qbj3/mapsrc/dev_tools_kebby.wad"
out = sys.argv[1]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def face(p0, p1, p2, outward, tex):
    n = cross(sub(p0, p1), sub(p2, p1))
    if sum(n[i] * outward[i] for i in range(3)) < 0:
        p0, p2 = p2, p0
    pts = " ".join("( %d %d %d )" % p for p in (p0, p1, p2))
    return "%s %s 0 0 0 1 1\n" % (pts, tex)


def box(x1, y1, z1, x2, y2, z2, tex, top=None):
    top = top or tex
    s = "{\n"
    s += face((x1, y1, z1), (x1, y2, z1), (x1, y1, z2), (-1, 0, 0), tex)
    s += face((x2, y1, z1), (x2, y1, z2), (x2, y2, z1), (1, 0, 0), tex)
    s += face((x1, y1, z1), (x1, y1, z2), (x2, y1, z1), (0, -1, 0), tex)
    s += face((x1, y2, z1), (x2, y2, z1), (x1, y2, z2), (0, 1, 0), tex)
    s += face((x1, y1, z1), (x2, y1, z1), (x1, y2, z1), (0, 0, -1), tex)
    s += face((x1, y1, z2), (x1, y2, z2), (x2, y1, z2), (0, 0, 1), top)
    return s + "}\n"


H = 1536      # half size
Z = 768
T = 32        # wall thickness
brushes = [
    box(-H - T, -H - T, -T, H + T, H + T, 0, "02_grey", "32_check"),       # floor
    box(-H - T, -H - T, Z, H + T, H + T, Z + T, "96_bright"),               # ceiling
    box(-H - T, -H - T, 0, -H, H + T, Z, "21_blue"),
    box(H, -H - T, 0, H + T, H + T, Z, "21_blue"),
    box(-H, -H - T, 0, H, -H, Z, "25_pink"),
    box(-H, H, 0, H, H + T, Z, "25_pink"),
]

ents = []
# deathmatch spawns on a ring of radius 700, all facing the middle (the bots there walk small circles, so they stay clear of walls)
for i in range(8):
    ang = i * 45
    x, y = round(700 * math.cos(math.radians(ang))), round(700 * math.sin(math.radians(ang)))
    ents.append('{\n"classname" "info_player_deathmatch"\n"origin" "%d %d 24"\n"angle" "%d"\n}\n' % (x, y, (ang + 180) % 360))
ents.append('{\n"classname" "info_player_start"\n"origin" "-700 0 24"\n"angle" "0"\n}\n')

# a row of pickups along the south wall
for i, c in enumerate(("item_health", "item_armor2", "item_shells", "item_spikes", "item_rockets", "item_cells", "item_health")):
    ents.append('{\n"classname" "%s"\n"origin" "%d -1450 24"\n}\n' % (c, -600 + i * 200))

# plenty of light so nothing is dark
for x in (-1000, 0, 1000):
    for y in (-1000, 0, 1000):
        ents.append('{\n"classname" "light"\n"origin" "%d %d 700"\n"light" "700"\n}\n' % (x, y))

with open(out, "w") as f:
    f.write('{\n"classname" "worldspawn"\n"wad" "%s"\n"message" "Test Box"\n"_minlight" "90"\n' % WAD)
    f.write("".join(brushes))
    f.write("}\n")
    f.write("".join(ents))
print("wrote", out, len(brushes), "brushes,", len(ents), "entities")
