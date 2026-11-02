"""RETIRED (2026-10-31): The standalone `orcom` map has been merged into `bklan` as an enterable building on Sonora St
(SW corner of Sumner & Sonora, hall at x = 360..436, y = 295..347). Active generator: `make_bklan_orcom.py` (exec'd by
`make_bklan.py`). Use `build_bklan.sh`, `view_bklan.sh`, and `deploy_web_viewer.sh` instead.

Historical standalone generator notes:
Writes orcom.map: the ORCOM CONNECT LAN PARTY (December 2002), rebuilt from the tape "Orcom 2.mpg" (32 min, 720x480).

The venue is a church / lodge banquet hall (an "ORTHODOX CHRISTIAN MISSIONS CENTER" display case, a board of framed
past officers, a kitchen pass-through). Nothing on the tape names it or gives an address. Sizes are scale estimates
from the tape (7 ft doors, 30 in folding tables, people): about 76 x 52 ft, 10 ft lay-in ceiling.

Layout (feet; x from the kitchen wall to the entrance wall, y from the BAWLS wall to the "Computer" banner wall):
  west wall (kitchen)      kitchen door (open), framed picture and clock over the pass-through, the gingham food table
                           under it, a jut in the north-west corner with the orange-wood EXIT door to the hallway
  east wall (entrance)     NE corner: the big TV on a round white table between two ficus; the portrait board flanked by
                           ficus on pedestals; the recessed vestibule with the carved double doors; the switch plates;
                           the honey-oak L counter with the white louvered door behind it; the whiteboard on its easel
  south wall               SE corner: the glass display case under the US flag; the "OrCom Connect / Is Fueled By /
                           BAWLS" banner with the red, white and blue coolers under it; the cream steel EXIT door
  north wall               the "Computer RENAISSANCE" sponsor banner high up
  floor                    cream speckled vinyl, a black-and-grey inlaid border rectangle with corner squares and a cross
  tables                   8 ft woodgrain folding tables in long rows down the room: one along each long wall (players
                           facing the wall) and two double-sided rows down the middle; beige CRTs and towers; burgundy
                           banquet chairs
Guessed: the kitchen's layout behind the pass-through, the hallway behind the exit doors (closed here), how many
stations each row had.

python -I make_orcom.py <out.map>   then qbsp -> vis -> light (ericw-tools); textures: build_bklan_textures.py"""
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WAD = os.path.join(HERE, "out", "maps", "bklan.wad").replace("\\", "/")
out = sys.argv[1]

U = 12
OX, OY = 38, 26
L, W, H = 76, 52, 10                         # the hall, inside the walls

TEXSIZE = {}
with open(WAD, "rb") as f:
    _, n, ofs = struct.unpack("<4sii", f.read(12))
    f.seek(ofs)
    dirs = [struct.unpack("<3i2bh16s", f.read(32)) for _ in range(n)]
    for pos, _, _, _, _, _, name in dirs:
        f.seek(pos)
        nm, w, h = struct.unpack("<16s2I", f.read(24))
        TEXSIZE[name.split(b"\0")[0].decode()] = (w, h)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def u(v, o=0):
    return int(round((v - o) * U))


class Fit:
    """A texture stretched (not tiled) over one face."""
    def __init__(self, name):
        self.name = name


def texline(spec, side, lo, hi):
    """As in make_bklan.py: Quake projects X-facing faces on (y, -z), Y-facing on (x, -z), floors on (x, -y)."""
    if isinstance(spec, str) and " " in spec:
        return spec
    if not isinstance(spec, Fit):
        return "%s 0 0 0 1 1" % spec
    tw, th = TEXSIZE[spec.name]
    a0, a1 = (lo[1], hi[1]) if side in "ew" else (lo[0], hi[0])
    b0, b1 = (-hi[1], -lo[1]) if side in "tb" else (-hi[2], -lo[2])
    xs, ys = (a1 - a0) / tw, (b1 - b0) / th
    if side in ("w", "n"):
        xs, xo = -xs, a1 / xs
    else:
        xo = -a0 / xs
    return "%s %.3f %.3f 0 %.5f %.5f" % (spec.name, xo, -b0 / ys, xs, ys)


def tile(tex, ft):
    """World-projected, one texture repeat = ft feet."""
    s = ft * U / TEXSIZE[tex][1]
    return "%s 0 0 0 %.5f %.5f" % (tex, s, s)


def face(p0, p1, p2, outward, tex):
    n = cross(sub(p0, p1), sub(p2, p1))
    if sum(n[i] * outward[i] for i in range(3)) < 0:
        p0, p2 = p2, p0
    return "%s %s\n" % (" ".join("( %d %d %d )" % p for p in (p0, p1, p2)), tex)


GROUPS = {"world": [], "detail": [], "illus": []}
SOLIDS = []


def box(x1, y1, z1, x2, y2, z2, tex, faces=None, group="world"):
    faces = faces or {}
    X1, X2 = sorted((u(x1, OX), u(x2, OX)))
    Y1, Y2 = sorted((u(y1, OY), u(y2, OY)))
    Z1, Z2 = sorted((u(z1), u(z2)))
    if X1 == X2 or Y1 == Y2 or Z1 == Z2:
        return
    lo, hi = (X1, Y1, Z1), (X2, Y2, Z2)
    t = lambda k: texline(faces.get(k, tex), k, lo, hi)
    s = "{\n"
    s += face((X1, Y1, Z1), (X1, Y2, Z1), (X1, Y1, Z2), (-1, 0, 0), t("w"))
    s += face((X2, Y1, Z1), (X2, Y1, Z2), (X2, Y2, Z1), (1, 0, 0), t("e"))
    s += face((X1, Y1, Z1), (X1, Y1, Z2), (X2, Y1, Z1), (0, -1, 0), t("s"))
    s += face((X1, Y2, Z1), (X2, Y2, Z1), (X1, Y2, Z2), (0, 1, 0), t("n"))
    s += face((X1, Y1, Z1), (X2, Y1, Z1), (X1, Y2, Z1), (0, 0, -1), t("b"))
    s += face((X1, Y1, Z2), (X1, Y2, Z2), (X2, Y1, Z2), (0, 0, 1), t("t"))
    GROUPS[group].append(s + "}\n")
    if group != "illus" and Z2 - Z1 > 2:
        SOLIDS.append((X1, Y1, Z1, X2, Y2, Z2))


def prop(*a, **k):
    k["group"] = k.get("group", "detail")
    box(*a, **k)


def octagon(cx, cy, r, z0, z1, tex, group="detail"):
    """An 8-sided upright prism (round tables, pots)."""
    P = [(u(cx + r * math.cos((k + .5) * math.pi / 4), OX), u(cy + r * math.sin((k + .5) * math.pi / 4), OY)) for k in range(8)]
    Z0, Z1 = u(z0), u(z1)
    s = "{\n"
    for i in range(8):
        a, b = P[i], P[(i + 1) % 8]
        s += face((a[0], a[1], Z0), (b[0], b[1], Z0), (a[0], a[1], Z0 + 64), (b[1] - a[1], -(b[0] - a[0]), 0), "%s 0 0 0 1 1" % tex)
    s += face((P[0][0], P[0][1], Z1), (P[3][0], P[3][1], Z1), (P[6][0], P[6][1], Z1), (0, 0, 1), "%s 0 0 0 1 1" % tex)
    s += face((P[0][0], P[0][1], Z0), (P[3][0], P[3][1], Z0), (P[6][0], P[6][1], Z0), (0, 0, -1), "%s 0 0 0 1 1" % tex)
    GROUPS[group].append(s + "}\n")


ENTS = []
PLACED = []


def ent(classname, x, y, z, **kv):
    s = '{\n"classname" "%s"\n"origin" "%d %d %d"\n' % (classname, u(x, OX), u(y, OY), u(z))
    if classname.startswith(("info_player", "weapon_", "item_")):
        PLACED.append((classname, (u(x, OX), u(y, OY), u(z))))
    for k, v in kv.items():
        s += '"%s" "%s"\n' % (k, v)
    ENTS.append(s + "}\n")


def light(x, y, z, val=200, color=None):
    kv = {"light": val}
    if color:
        kv["_color"] = color
    ent("light", x, y, z, **kv)


def check_placed():
    bad = 0
    for cls, (x, y, z) in PLACED:
        lo, hi = ((x - 16, y - 16, z - 23), (x + 16, y + 16, z + 32)) if cls.startswith("info_player") else \
                 ((x - 16, y - 16, z - 8), (x + 16, y + 16, z + 16))
        for b in SOLIDS:
            if all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)):
                print("BLOCKED %s at %d %d %d by brush %s" % (cls, x, y, z, b))
                bad += 1
                break
    return bad


# ---------------------------------------------------------------------------------------------- the LAN furniture
_FACING_YAW = {"e": 0, "n": 90, "w": 180, "s": 270}
_TBL_SEQ = [0]
_PC_SEQ = [0]
_CHR_SEQ = [0]
_SKIN_RING = (0, 1, 3, 4, 2, 0, 4, 1, 5, 3)
_CHR_RING = (1, 1, 2, 1, 3, 1, 4, 1)


def table(x, y, length=8, depth=2.5, top="bk_wood"):
    """8 ft explodable 3D LAN table along x, (x, y) its min corner."""
    idx = _TBL_SEQ[0]
    _TBL_SEQ[0] = idx + 1
    SOLIDS.append((u(x, OX), u(y, OY), 0, u(x + length, OX), u(y + depth, OY), u(2.5)))
    ent("misc_lan_table", x + length / 2.0, y + depth / 2.0, 0, angles="0 %d 0" % (0 if idx % 2 == 0 else 180), cnt=(idx % 4) + 1)


def pc(x, y, facing, tower=True, z=2.5):
    """Explodable 3D CRT monitor (Q3A / CS / Win98 + 3D kbd+mouse) + explodable 3D PC tower."""
    idx = _PC_SEQ[0]
    _PC_SEQ[0] = idx + 1
    ang = "0 %d 0" % _FACING_YAW[facing]
    mx = (x - 0.18) if tower else x
    ent("misc_lan_monitor", mx, y, z, angles=ang, cnt=(idx % 4) + 1, skin=_SKIN_RING[idx % len(_SKIN_RING)])
    if tower:
        ent("misc_lan_pc", x + 0.94, y, z, angles=ang, cnt=((idx * 3 + 1) % 4) + 1)


def chair(x, y, facing):
    """Explodable 3D LAN chair (mostly burgundy banquet chairs + BYOC rolling/folding/task chairs)."""
    idx = _CHR_SEQ[0]
    _CHR_SEQ[0] = idx + 1
    SOLIDS.append((u(x - 0.85, OX), u(y - 0.85, OY), 0, u(x + 0.85, OX), u(y + 0.85, OY), u(3.0)))
    ent("misc_lan_chair", x, y, 0, angles="0 %d 0" % _FACING_YAW[facing], cnt=_CHR_RING[idx % len(_CHR_RING)])


def ficus(x, y, pedestal=0.0):
    if pedestal:
        octagon(x, y, 0.9, 0, pedestal, "oc_white")
    octagon(x, y, 0.8, pedestal, pedestal + 1.3, "bk_bark")
    prop(x - .15, y - .15, pedestal + 1.3, x + .15, y + .15, pedestal + 4, "bk_bark")
    for dx, dy, z0, r in ((0, 0, 3.4, 1.1), (.6, -.4, 4.3, .8), (-.5, .5, 4.9, .7), (.2, .3, 5.6, .55)):
        box(x + dx - r, y + dy - r, pedestal + z0, x + dx + r, y + dy + r, pedestal + z0 + r * 1.3, "bk_leaf",
            group="illus")


# ================================================================================================= the shell
T = 1.0
box(-16, -1, -1, 86, W + 1, 0, "oc_floor")                                 # one slab under hall, kitchen, vestibule
box(-1, -1, H, L + 1, W + 1, H + 1, tile("oc_ceiling", 4))
box(-1, -1, 0, L + 1, 0, H, "oc_wall")                                     # south (BAWLS) wall
box(-1, W, 0, L + 1, W + 1, H, "oc_wall")                                  # north ("Computer") wall
# east wall with the vestibule opening (8.5 ft wide, 8.5 ft high)
box(L, -1, 0, L + T, 26, H, "oc_wall")
box(L, 34.5, 0, L + T, W + 1, H, "oc_wall")
box(L, 26, 8.5, L + T, 34.5, H, "oc_wall")
# west wall: the kitchen door (y 8-11) and the pass-through (y 15-19, sill 3.75 ft, 2.5 ft tall)
box(-T, -1, 0, 0, 8, H, "oc_wall")
box(-T, 8, 7, 0, 11, H, "oc_wall")
box(-T, 11, 0, 0, 15, H, "oc_wall")
box(-T, 15, 0, 0, 19, 3.75, "oc_wall", {"t": "oc_white"})
box(-T, 15, 6.25, 0, 19, H, "oc_wall")
box(-T, 19, 0, 0, W + 1, H, "oc_wall")
box(0, 0, 9, 2.5, 43, H, "oc_wall")                                        # the dropped soffit along the kitchen wall
# the north-west jut with the orange-wood EXIT door to the hallway
box(0, 43, 0, 3, W, H, "oc_wall")
prop(3, 45.5, 0, 3.12, 48.5, 7, "oc_wood")
prop(3, 45.3, 7, 3.15, 48.7, 7.3, "oc_white")
prop(3, 46.2, 7.6, 3.4, 47.8, 8.2, "oc_white", {"e": Fit("oc_exit")})
light(3.6, 47, 7.9, 12, "1 0.2 0.2")

# the vestibule: 8 ft deep, lower ceiling, the cream accordion panels, the carved double doors
box(L, 25, 0, 85, 26, 9.5, "oc_wall")
box(L, 34.5, 0, 85, 35.5, 9.5, "oc_wall")
box(84, 25, 0, 85, 35.5, 9.5, "oc_wall")
box(L + T, 25, 8.5, 84, 35.5, 9.5, tile("oc_ceiling", 4))
prop(77.5, 26, 0, 83.5, 26.12, 8.2, "oc_white", {"n": Fit("oc_accordion")})
for k in range(2):
    y0 = 27.3 + k * 3.0
    prop(83.85, y0, 0, 84, y0 + 2.95, 7.2, "bk_chairbk", {"w": Fit("oc_carved")})
prop(83.8, 27.0, 7.2, 84, 33.6, 7.6, "bk_chairbk")
for gx in (79, 82):
    box(gx - 1, 29.3, 8.42, gx + 1, 31.3, 8.5, "oc_grille", group="illus")
light(80.5, 30.2, 7.6, 120)

# the kitchen: white walls, a stainless reach-in, the microwave on its cart, shelving, counter under the pass-through
box(-15, 3, 0, -14, 25, 9.5, "oc_wall", {"e": "bk_white"})
box(-15, 3, 0, 0, 4, 9.5, "oc_wall", {"n": "bk_white"})
box(-15, 24, 0, 0, 25, 9.5, "oc_wall", {"s": "bk_white"})
box(-14, 4, 9, -T, 24, 9.5, "bk_white")
box(-14, 4, 0, -T, 24, 0.09, "oc_white", group="illus")
prop(-14, 18, 0, -11.5, 21.5, 7, "bk_duct")
prop(-6.5, 20.5, 0, -3.8, 23, 3, "bk_steel")
prop(-6.2, 20.8, 3, -4.2, 22.4, 4.2, "oc_white", {"w": "bk_glass"})
for z in (0.3, 2.3, 4.3, 6.3):
    prop(-13, 4, z, -4, 5.5, z + .2, "bk_steel")
for x in (-13, -4.2):
    prop(x, 4, 0, x + .2, 5.5, 7, "bk_steel")
prop(-2.5, 13.5, 0, -T, 20.5, 3.0, "oc_white")
prop(-3.1, 8, 0, -T, 8.15, 7, "oc_wood")                                    # the kitchen door, swung open
light(-7, 14, 8.3, 220)

# ================================================================================================= the walls' fixtures
# south: the coolers, the OrCom / BAWLS banner, the steel EXIT door, BAWLS cases; the display case and flag
prop(56, 0, 0, 59.6, 0.12, 7.2, "oc_white", {"n": Fit("oc_exitdoor")})
prop(56.8, 0, 7.6, 58.8, 0.4, 8.2, "oc_white", {"n": Fit("oc_exit")})
light(57.8, 0.8, 7.9, 12, "1 0.2 0.2")
prop(61, 0, 4, 67, 0.08, 7, "oc_white", {"n": Fit("oc_bawls")})
for x0, x1, tex in ((61, 63.4, "oc_red"), (63.7, 66.6, "oc_white"), (66.9, 69, "oc_blue")):
    prop(x0, 0.4, 0, x1, 2.3, 1.7, tex, {"t": "oc_white"})
for z in (0, 0.8, 1.6):
    prop(52.6, 0.4, z, 55, 2.2, z + .8, "oc_blue")
prop(69.6, 0, 0, 75.6, 2, 4.4, "oc_oak", {"n": Fit("oc_case")})
prop(75.3, 2.9, 0, 75.5, 3.1, 8.2, "bk_steel")
prop(72.3, 2.95, 4.6, 75.3, 3.05, 7.6, "oc_flag", {"n": Fit("oc_flag"), "s": Fit("oc_flag")})
# east: the oak counter (L), the louvered door and panel behind it, switch plates, the portrait board between ficus,
# the TV on the round table in the NE corner between two more ficus, the whiteboard on its easel
prop(67, 5, 0, 69.5, 18, 3.4, "oc_oak")
prop(69.5, 18, 0, L, 20.5, 3.4, "oc_oak")
prop(66.8, 4.8, 3.4, 69.7, 18.2, 3.6, "oc_oak")
prop(69.5, 17.8, 3.4, L, 20.7, 3.6, "oc_oak")
# Explodable 3D check-in admin rig & live tournament bracket CRT station on the honey-oak L-counter:
ent("misc_lan_monitor", 68.25, 8.17, 3.62, angles="0 0 0", cnt=2, skin=5)
ent("misc_lan_pc", 68.25, 9.29, 3.62, angles="0 0 0", cnt=4)
ent("misc_lan_chair", 71.4, 8.35, 0, angles="0 180 0", cnt=2)
ent("misc_lan_monitor", 68.30, 12.47, 3.62, angles="0 180 0", cnt=3, skin=0)
ent("misc_lan_pc", 68.30, 13.59, 3.62, angles="0 180 0", cnt=2)
ent("misc_lan_chair", 71.4, 12.65, 0, angles="0 180 0", cnt=4)
for _scy in (38.0, 39.6, 41.2):
    ent("misc_lan_chair", 72.6, _scy, 0, angles="0 180 0", cnt=1)
# (replaced counter brush laptop slab with 3D misc_lan_monitor + misc_lan_pc above)
prop(67.8, 15.5, 3.6, 68.5, 16.2, 4.4, "bk_leaf", group="illus")
prop(L - .12, 8, 0, L, 11, 7, "oc_white", {"w": Fit("oc_louver")})
prop(L - .1, 13, 4, L, 14.5, 6.2, "bk_steel")
for k in range(3):
    prop(L - .05, 24.4 + k * .45, 4.3, L, 24.7 + k * .45, 4.8, "oc_white", group="illus")
prop(L - .15, 37, 5, L, 42, 7.4, "oc_wood", {"w": Fit("oc_photos")})
ficus(74.2, 35.9, pedestal=2.2)
ficus(74.2, 43.2, pedestal=2.2)
octagon(71.4, 48.4, 2.6, 0, 2.45, "oc_white")
prop(70.3, 46.6, 2.45, 72.6, 50.2, 6.6, "bk_chairbk", {"w": Fit("oc_tv")})
prop(69.0, 47.4, 2.45, 69.8, 48.2, 2.75, "bk_leg")                           # consoles
prop(69.0, 48.6, 2.45, 69.8, 49.3, 2.7, "bk_white")
ficus(74.6, 45.2)
ficus(67.6, 50.6)
prop(63.9, 9.3, 3, 64.05, 13.3, 6, "oc_white", {"w": Fit("oc_whiteboard")})
for ly in (9.6, 13.0):
    prop(64.05, ly, 0, 64.2, ly + .15, 6.3, "oc_wood")
prop(64.4, 11.2, 0, 64.55, 11.35, 6.0, "oc_wood")
# west: picture and clock above the pass-through, the gingham-covered food table, the trash can
prop(0, 14.3, 6.8, 0.1, 16.6, 8.4, "oc_wood", {"e": Fit("oc_picture")})
prop(0, 18.0, 7.0, 0.1, 19.4, 8.4, "oc_white", {"e": Fit("oc_clock")})
prop(0.5, 13, 2.35, 3, 21, 2.5, "oc_gingham", {k: Fit("oc_gingham") for k in "nsewt"})
for ly in (13.6, 20.2):
    prop(0.7, ly, 0, 2.8, ly + .15, 2.35, "bk_leg")
octagon(2, 23, 0.9, 0, 2.6, "oc_blue")
# north: the sponsor banner high up, the round table of food by it
prop(28, W - .08, 7, 38, W, 9.5, "oc_white", {"s": Fit("oc_computer")})
octagon(36, 44.5, 2.5, 2.35, 2.5, "oc_white")
prop(35.9, 44.4, 0, 36.1, 44.6, 2.35, "bk_leg")

# ================================================================================================= ceiling and floor
# 2 x 4 troffers paired into 8 ft runs, seven columns of three; square return grilles between
for tx in range(8, 69, 10):
    for y0 in (8, 22, 36):
        box(tx - 1, y0, H - .08, tx + 1, y0 + 8, H, "oc_troffer", {"b": Fit("oc_troffer")}, group="illus")
        light(tx, y0 + 4, H - 1.6, 165, "1 1 0.96")
for gx, gy in ((13, 19), (33, 19), (53, 19), (13, 33), (33, 33), (53, 33), (23, 47), (63, 47), (43, 5)):
    box(gx - 1, gy - 1, H - .05, gx + 1, gy + 1, H, "oc_grille", group="illus")
# the inlaid border: black band, grey band inside it, square motifs at the corners, a cross through the middle
BX0, BY0, BX1, BY1 = 6, 6, 70, 46
F0, F1 = 0, 1 / U


def band(x0, y0, x1, y1, tex="oc_band"):
    box(x0, y0, F0, x1, y1, F1, tex, group="illus")


band(BX0, BY0, BX1, BY0 + .75)
band(BX0, BY1 - .75, BX1, BY1)
band(BX0, BY0, BX0 + .75, BY1)
band(BX1 - .75, BY0, BX1, BY1)
band(BX0 + .75, BY0 + .75, BX1 - .75, BY0 + 1.5, "oc_bandgrey")
band(BX0 + .75, BY1 - 1.5, BX1 - .75, BY1 - .75, "oc_bandgrey")
band(BX0 + .75, BY0 + 1.5, BX0 + 1.5, BY1 - 1.5, "oc_bandgrey")
band(BX1 - 1.5, BY0 + 1.5, BX1 - .75, BY1 - 1.5, "oc_bandgrey")
cy, cx = (BY0 + BY1) / 2, (BX0 + BX1) / 2
band(BX0 + 1.5, cy - .375, BX1 - 1.5, cy + .375)
band(cx - .375, BY0 + 1.5, cx + .375, BY1 - 1.5)
for qx, qy in ((BX0 + 1.5, BY0 + 1.5), (BX1 - 6.5, BY0 + 1.5), (BX0 + 1.5, BY1 - 6.5), (BX1 - 6.5, BY1 - 6.5)):
    band(qx, qy, qx + 5, qy + 5, "oc_bandgrey")
    band(qx, qy, qx + 5, qy + .5)
    band(qx, qy + 4.5, qx + 5, qy + 5)
    band(qx, qy, qx + .5, qy + 5)
    band(qx + 4.5, qy, qx + 5, qy + 5)

# ================================================================================================= the LAN
# rows of 8 ft tables down the room: along the north wall and the south wall (facing the walls), two double rows
EMPTY = {(1, 2), (3, 6), (4, 0), (2, 5), (5, 3)}                           # a few seats still empty


def station(row, k, x, y, facing, chair_y):
    if (row, k % 7) in EMPTY and k % 3 == 1:
        ent("misc_model", x, y, 2.5, mdl="progs/bklan/soda_can.md3", angles="0 0 0")
    else:
        pc(x, y, facing, tower=(k % 4 != 2))
    chair(x, chair_y, "n" if facing == "s" else "s")


for k, tx in enumerate(range(10, 66, 8)):                                   # north wall row
    table(tx, W - 2.5)
    for j, dx in enumerate((1.35, 3.9, 6.45)):
        station(0, k * 3 + j, tx + dx, W - 1.1, "s", W - 4.6)
for k, tx in enumerate(range(6, 54, 8)):                                    # south wall row (stops at the exit door)
    table(tx, 0.1)
    for j, dx in enumerate((1.35, 3.9, 6.45)):
        station(1, k * 3 + j, tx + dx, 1.2, "n", 4.7)
for r, y0 in enumerate((14, 30)):                                           # the two double rows
    for k, tx in enumerate(range(10, 66, 8)):
        table(tx, y0)
        table(tx, y0 + 2.5)
        for j, dx in enumerate((1.35, 3.9, 6.45)):
            station(2 + r * 2, k * 3 + j, tx + dx, y0 + 1.15, "s", y0 - 2.3)
            station(3 + r * 2, k * 3 + j, tx + dx, y0 + 3.85, "n", y0 + 7.3)
# West head-of-aisle Tournament Dedicated Server Desk (compact 5.8-ft Honey-Oak lan_table4s):
SOLIDS.append((u(2.8, OX), u(29.5, OY), 0, u(5.3, OX), u(35.33, OY), u(2.5)))
ent("misc_lan_table", 4.05, 32.42, 0, angles="0 90 0", cnt=5)
ent("misc_lan_monitor", 4.15, 30.92, 2.5, angles="0 0 0", cnt=2, skin=5)
ent("misc_lan_pc", 4.15, 32.04, 2.5, angles="0 0 0", cnt=2)
ent("misc_lan_monitor", 4.15, 33.62, 2.5, angles="0 0 0", cnt=3, skin=3)
ent("misc_lan_pc", 4.15, 34.74, 2.5, angles="0 0 0", cnt=4)
ent("misc_lan_chair", 6.9, 32.4, 0, angles="0 180 0", cnt=4)
ent("misc_model", 3.5, 34.9, 2.5, mdl="progs/bklan/soda_bottle.md3", angles="0 0 0", scale=1.5)

# ================================================================================================= gameplay
for x, y, a in ((5, 8, 0), (5, 40, 0), (72, 27, 180), (80.5, 30, 180), (-7, 12, 0), (30, 25.5, 90), (50, 25.5, 270),
                (20, 7.8, 0), (45, 44, 270), (60, 41.5, 180), (40, 7.6, 90), (68, 25.5, 180)):
    ent("info_player_deathmatch", x, y, 2.2, angle=a)
if os.environ.get("ORCOM_START"):
    sx, sy, sz, sa = (float(v) for v in os.environ["ORCOM_START"].split())
    ent("info_player_start", sx, sy, sz, angle=int(sa))
else:
    ent("info_player_start", 80.5, 30, 2.2, angle=180)                     # in the vestibule, facing the hall
for name, x, y in (("weapon_supershotgun", 38, 25.5), ("weapon_nailgun", 6, 25), ("weapon_grenadelauncher", 66, 25),
                   ("weapon_rocketlauncher", -8, 11), ("item_armor2", 80.5, 33), ("item_health", 20, 25.5),
                   ("item_health", 56, 25.5), ("item_shells", 5.5, 40.5), ("item_spikes", 64, 44), ("item_rockets", 38, 8),
                   ("item_cells", 38, 43)):
    ent(name, x, y, 1)

SPOTS = [("Entrance vestibule", 80.5, 30, 180), ("Down the middle aisle", 72, 24.5, 180), ("Kitchen end", 6, 24.5, 0),
         ("The BAWLS banner and exit", 58, 7, 300), ("TV corner", 64, 42, 45), ("The counter and whiteboard", 60, 24.5, 330),
         ("The kitchen", -8, 12, 0), ("North wall row", 40, 45.5, 270)]
json.dump([{"name": n, "pos": [u(x, OX), u(y, OY), u(2.2)], "yaw": a} for n, x, y, a in SPOTS],
          open(os.path.join(os.path.dirname(os.path.abspath(out)), "orcom.spots.json"), "w"))

with open(out, "w") as f:
    f.write('{\n"classname" "worldspawn"\n"wad" "%s"\n"message" "ORCOM CONNECT LAN PARTY"\n' % WAD)
    f.write('"_minlight" "36"\n"_dirt" "1"\n"_dirtscale" "1.0"\n')
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    f.write('{\n"classname" "func_detail"\n' + "".join(GROUPS["detail"]) + "}\n")
    f.write('{\n"classname" "func_detail_illusionary"\n' + "".join(GROUPS["illus"]) + "}\n")
    f.write("".join(ENTS))
if check_placed():
    sys.exit("spawns / items inside brushes")
print("wrote", out, len(GROUPS["world"]), "world +", len(GROUPS["detail"]), "detail +", len(GROUPS["illus"]),
      "illusionary brushes,", len(ENTS), "entities")
