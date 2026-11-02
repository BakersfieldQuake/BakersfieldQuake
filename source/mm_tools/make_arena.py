"""Writes bfarena.map: a big open test arena (2560 x 2560, 640 high) with grid dev textures, a few pillars,
low cover walls and a stepped platform, 8 deathmatch spawns. Compile with ericw-tools:
python -I make_arena.py <out.map>"""
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


H = 1280      # half size
Z = 640
T = 32        # wall thickness
brushes = [
    box(-H - T, -H - T, -T, H + T, H + T, 0, "02_grey", "32_check"),       # floor
    box(-H - T, -H - T, Z, H + T, H + T, Z + T, "96_bright"),               # ceiling
    box(-H - T, -H - T, 0, -H, H + T, Z, "21_blue"),
    box(H, -H - T, 0, H + T, H + T, Z, "21_blue"),
    box(-H, -H - T, 0, H, -H, Z, "25_pink"),
    box(-H, H, 0, H, H + T, Z, "25_pink"),
]
# pillars
for x, y in ((-640, -640), (640, -640), (-640, 640), (640, 640)):
    brushes.append(box(x - 64, y - 64, 0, x + 64, y + 64, Z, "13_gold"))
# low cover walls
for x1, y1, x2, y2 in ((-160, -900, 160, -868), (-160, 868, 160, 900), (-900, -160, -868, 160), (868, -160, 900, 160)):
    brushes.append(box(x1, y1, 0, x2, y2, 64, "29_red"))
# stepped platform in the middle: 3 steps of 16 on every side
for i, h in enumerate((16, 32, 48)):
    r = 320 - i * 48
    brushes.append(box(-r, -r, 0, r, r, h, "15_green", "34_grid"))

ents = []
for x, y, a in ((-1000, -1000, 45), (1000, -1000, 135), (1000, 1000, 225), (-1000, 1000, 315),
                (0, -1100, 90), (1100, 0, 180), (0, 1100, 270), (-1100, 0, 0)):
    ents.append('{\n"classname" "info_player_deathmatch"\n"origin" "%d %d 24"\n"angle" "%d"\n}\n' % (x, y, a))
ents.append('{\n"classname" "info_player_start"\n"origin" "-1100 0 24"\n"angle" "0"\n}\n')
for x in (-800, 0, 800):
    for y in (-800, 0, 800):
        ents.append('{\n"classname" "light"\n"origin" "%d %d 560"\n"light" "600"\n}\n' % (x, y))

with open(out, "w") as f:
    f.write('{\n"classname" "worldspawn"\n"wad" "%s"\n"message" "Bakersfield Arena"\n"_minlight" "90"\n' % WAD)
    f.write("".join(brushes))
    f.write("}\n")
    f.write("".join(ents))
print("wrote", out, len(brushes), "brushes")
