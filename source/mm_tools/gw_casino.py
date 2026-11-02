"""The inside of Golden West Casino and its entrance plaza, exec'd by make_goldenwest.py (after gwbase.py). Everything here is in
TRUE feet (build_casino() runs under unscaled()); the building's footprints come from make_goldenwest.py's traced feet x K.
Reference: the card-room photos (tan rubble-stone walls, timber beams, dark carpet, red-felt oval tables with black rails and
black chairs, numbered placards, wall TVs, white ceiling tiles, slate-blue doors, white shutters) and Street View Feb 2017
(the glass gable over the doors, the bronze bucking-horse statue in its round flower bed, the 'wet floor' signs, stamped paving).
Rooms: the card room (the old main hall, y 14 .. 108), the lobby with the cage counter (the east block), the high-limit room and
bar (the north wing). Two entrances, both walk-in: the glass doors under the gable (x 35 .. 43) and the west door (x -22.6 .. -15.4).
Textures: build_gw_casino_textures.py (gwcasino.wad).  The statue: make_gw_horse.py (progs/gw_horse.md3)."""
import math as _m
import random as _rd

# the footprints make_goldenwest.py must not fill with solid blocks any more (traced feet, as in its walls() calls)
CASINO_HOLLOW = {(-24, 9, 21, 31), (-24, 31, 21, 68), (21, 9, 59, 31), (-6, 68, 14, 109)}

_cw = os.path.join(HERE, "out", "maps", "gwcasino.wad")
if not os.path.exists(_cw):
    sys.path.insert(0, HERE)
    import build_gw_casino_textures as _bct
    _bct.main()
with open(_cw, "rb") as _f:
    _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
    _f.seek(_ofs)
    for _pos, _, _, _, _, _, _name in [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]:
        _f.seek(_pos)
        _nm, _w2, _h2 = struct.unpack("<16s2I", _f.read(24))
        TEXSIZE[_name.split(b"\0")[0].decode()] = (_w2, _h2)

CH = tuple(v * K for v in (-24, 9, 21, 68))          # card room: x0 y0 x1 y1
CE = tuple(v * K for v in (21, 9, 59, 31))           # lobby (the east block)
CW = tuple(v * K for v in (-6, 68, 14, 109))         # north wing
C_T = 1.0                                            # wall thickness
C_ZC, C_ZT = 11.5, 13.0                              # ceiling underside, wall top (hall, lobby)
C_ZW, C_ZWT = 10.5, 12.0                             # the same in the wing
C_FL = 0.17                                          # floor covering
C_LOBBY_N = 44.0                                     # the lobby's north wall: a thick block (the turret bulges in there)
C_IN = tspec("gw_istone", 5)
C_OUT = tspec("gw_stone", 6)
C_LC = "255 232 205"
C_LV = 185
_cr = _rd.Random(77)


# ---------------------------------------------------------------------------------------------- shell
def c_slab(x0, y0, x1, y1, z0, z1, outer="", group="world"):
    faces = {"t": "bk_roof", "b": "bk_roof"}
    for s in outer:
        faces[s] = C_OUT
    box(x0, y0, z0, x1, y1, z1, C_IN, faces, group=group)


def c_wall_x(x0, x1, y, z0, z1, outer, holes=()):
    """A wall along x occupying y .. y + C_T; holes = (a, b, top of the opening)."""
    cur = x0
    for a, b, zt in sorted(holes):
        if a > cur:
            c_slab(cur, y, a, y + C_T, z0, z1, outer)
        c_slab(a, y, b, y + C_T, zt, z1, outer)
        cur = b
    if x1 > cur:
        c_slab(cur, y, x1, y + C_T, z0, z1, outer)


def c_wall_y(x, y0, y1, z0, z1, outer, holes=()):
    """A wall along y occupying x .. x + C_T."""
    cur = y0
    for a, b, zt in sorted(holes):
        if a > cur:
            c_slab(x, cur, x + C_T, a, z0, z1, outer)
        c_slab(x, a, x + C_T, b, zt, z1, outer)
        cur = b
    if y1 > cur:
        c_slab(x, cur, x + C_T, y1, z0, z1, outer)


def c_band(axis, at, a0, a1, side, holes=(), z1=3.0):
    """Cream plaster dado with a brown cap on the inner face of a wall (photo 1). side: +1 / -1 = which way the room lies."""
    cur = a0
    for a, b in list(sorted(holes)) + [(a1, a1)]:
        if a > cur:
            lo, hi = sorted((at, at + side * 0.12))
            cl, ch = sorted((at, at + side * 0.2))
            if axis == "x":
                box(cur, lo, C_FL, a, hi, z1, tspec("gw_stucco", 4), group="detail")
                box(cur, cl, z1, a, ch, z1 + 0.15, "gw_trim", group="detail")
            else:
                box(lo, cur, C_FL, hi, a, z1, tspec("gw_stucco", 4), group="detail")
                box(cl, cur, z1, ch, a, z1 + 0.15, "gw_trim", group="detail")
        cur = max(cur, b)


def c_flat(axis, at, a0, a1, z0, z1, face, tex, th=0.1, back="bk_steel"):
    """A panel hung on a wall (axis 'x': the wall plane is x = at, spanning y a0..a1) showing `tex` stretched over `face`."""
    f = Fit(tex)
    if axis == "x":
        x0, x1 = (at, at + th) if face == "e" else (at - th, at)
        prop(x0, a0, z0, x1, a1, z1, back, {face: f})
    else:
        y0, y1 = (at, at + th) if face == "n" else (at - th, at)
        prop(a0, y0, z0, a1, y1, z1, back, {face: f})


def c_tv(axis, at, mid, z0, face, n, w=4.2, h=2.4):
    c_flat(axis, at, mid - w / 2, mid + w / 2, z0, z0 + h, face, "gw_tv%d" % (n % 4 + 1), th=0.3)


def c_exit(axis, at, mid, z0, face):
    c_flat(axis, at, mid - 0.9, mid + 0.9, z0, z0 + 0.9, face, "gw_exit", th=0.2)


def c_light(x, y, zc, val=C_LV):
    prop(x - 2, y - 1, zc - 0.12, x + 2, y + 1, zc, "gw_lightp")
    ent("light", x, y, zc - 1.0, light=val, _color=C_LC)


def c_dome(x, y, zc):
    prism(circle(x, y, 0.5, 8), zc - 0.45, zc, "gw_leather", group="detail")


def c_plant(x, y, h=6.0):
    prop(x - 0.7, y - 0.7, C_FL, x + 0.7, y + 0.7, 1.5, "gw_trim")
    name, w, hh = "{bk3_tree2", 122, 208
    wd = w * h / hh
    f = Fit(name)
    box(x - wd / 2, y - 0.06, 1.4, x + wd / 2, y + 0.06, 1.4 + h, name, {"n": f, "s": f}, group="illus")
    box(x - 0.06, y - wd / 2, 1.4, x + 0.06, y + wd / 2, 1.4 + h, name, {"e": f, "w": f}, group="illus")


# ---------------------------------------------------------------------------------------------- poker tables
def c_stadium(cx, cy, L, W, along, n=6):
    r = W / 2
    pts = []
    for i in range(n + 1):
        a = -_m.pi / 2 + _m.pi * i / n
        pts.append((L / 2 - r + r * _m.cos(a), r * _m.sin(a)))
    for i in range(n + 1):
        a = _m.pi / 2 + _m.pi * i / n
        pts.append((-L / 2 + r + r * _m.cos(a), r * _m.sin(a)))
    return [(cx + py, cy + px) for px, py in pts] if along == "y" else [(cx + px, cy + py) for px, py in pts]


def c_top_spec(name, poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return texline(Fit(name), "t", (u(min(xs), OX), u(min(ys), OY), 0), (u(max(xs), OX), u(max(ys), OY), 0))


def c_chair(x, y, face):
    """Black padded chair; face = the way the sitter looks."""
    prop(x - 0.8, y - 0.8, 1.45, x + 0.8, y + 0.8, 1.85, "gw_leather")
    prop(x - 0.12, y - 0.12, C_FL, x + 0.12, y + 0.12, 1.45, "bk_steel")
    prop(x - 0.65, y - 0.65, C_FL, x + 0.65, y + 0.65, 0.4, "bk_steel")
    if face == "n":
        prop(x - 0.75, y - 0.95, 1.85, x + 0.75, y - 0.65, 3.4, "gw_leather")
    elif face == "s":
        prop(x - 0.75, y + 0.65, 1.85, x + 0.75, y + 0.95, 3.4, "gw_leather")
    elif face == "e":
        prop(x - 0.95, y - 0.75, 1.85, x - 0.65, y + 0.75, 3.4, "gw_leather")
    else:
        prop(x + 0.65, y - 0.75, 1.85, x + 0.95, y + 0.75, 3.4, "gw_leather")


def c_table(cx, cy, num, along="x", L=9.5, W=4.4):
    """Oval poker table: black leather rail round a red felt (the Golden West logo), one pedestal, a dealer's tray, chip stacks, cups, up to
    nine black chairs round it and the numbered placard hung over it (photos 1 and 2)."""
    outer = c_stadium(cx, cy, L, W, along)
    inner = c_stadium(cx, cy, L - 1.1, W - 1.1, along)
    m = len(outer)
    for i in range(m):                                                           # the rail: a ring of trapezoids
        quad = [outer[i], outer[(i + 1) % m], inner[(i + 1) % m], inner[i]]
        prism(quad, 2.35, 2.95, "gw_leather", group="detail", solid=True)
    prism(inner, 2.35, 2.78, c_top_spec("gw_felt" if along == "x" else "gw_feltv", inner), "gw_leather", group="detail", solid=True)
    if along == "x":
        prop(cx - 0.7, cy - 0.7, C_FL, cx + 0.7, cy + 0.7, 2.35, "gw_leather")
        prop(cx - 2.0, cy - 0.45, C_FL, cx + 2.0, cy + 0.45, 0.45, "gw_leather")
    else:
        prop(cx - 0.7, cy - 0.7, C_FL, cx + 0.7, cy + 0.7, 2.35, "gw_leather")
        prop(cx - 0.45, cy - 2.0, C_FL, cx + 0.45, cy + 2.0, 0.45, "gw_leather")
    at = (lambda lx, ly: (cx + lx, cy + ly)) if along == "x" else (lambda lx, ly: (cx + ly, cy + lx))
    face = {"n": "n", "s": "s", "e": "e", "w": "w"} if along == "x" else {"n": "e", "s": "w", "e": "n", "w": "s"}
    x, y = at(0, -1.1)
    ax = (0.9, 0.35) if along == "x" else (0.35, 0.9)
    prop(x - ax[0], y - ax[1], 2.78, x + ax[0], y + ax[1], 2.9, "bk_steel")      # dealer's tray
    for lx in (-3.4, -1.1, 1.1, 3.4):                                            # seats on the far side, the dealer's side gets three
        if _cr.random() < 0.88:
            sx, sy = at(lx, W / 2 + 1.35)
            c_chair(sx, sy, face["s"])
            px, py = at(lx * 0.8, W / 2 - 1.0)
            for k, tx in enumerate(("gw_chipr", "gw_chipb", "gw_chipk")[: _cr.randint(1, 3)]):
                a, b = at(lx * 0.8 + k * 0.32, W / 2 - 1.0 + _cr.uniform(-0.2, 0.2))
                prop(a - 0.13, b - 0.13, 2.78, a + 0.13, b + 0.13, 2.78 + 0.1 * _cr.randint(2, 6), tx)
    for lx in (-3.4, -1.1, 3.4):
        if _cr.random() < 0.9:
            sx, sy = at(lx, -(W / 2 + 1.35))
            c_chair(sx, sy, face["n"])
    for sgn in (-1, 1):
        if _cr.random() < 0.9:
            sx, sy = at(sgn * (L / 2 + 1.35), 0)
            c_chair(sx, sy, face["w"] if sgn > 0 else face["e"])
    for lx in (-2.2, 2.6):                                                       # paper cups on the rail
        a, b = at(lx, W / 2 - 0.4 if lx < 0 else -(W / 2 - 0.4))
        prop(a - 0.19, b - 0.19, 2.95, a + 0.19, b + 0.19, 3.55, "bk_white")
    zc = C_ZC
    prop(cx - 0.03, cy - 0.03, 9.9, cx + 0.03, cy + 0.03, zc, "bk_steel")      # the placard on its cord
    f = Fit("gw_n%02d" % num)
    prop(cx - 0.65, cy - 0.06, 8.7, cx + 0.65, cy + 0.06, 9.95, "bk_steel", {"n": f, "s": f})
    prop(cx - 0.06, cy - 0.65, 8.7, cx + 0.06, cy + 0.65, 9.95, "bk_steel", {"e": f, "w": f})


# ---------------------------------------------------------------------------------------------- the rooms
def _hall():
    x0, y0, x1, y1 = CH
    ex_w = (-22.6, -15.4)                                # west entrance
    arch = (20.0, 40.0)                                  # to the lobby
    wing = (-3.0, 15.0)                                  # to the north wing
    c_wall_x(x0, x1, y0, 0, C_ZT, "s", holes=[(ex_w[0], ex_w[1], 8.4)])
    c_wall_x(x0, x1, y1 - C_T, 0, C_ZT, "n", holes=[(wing[0], wing[1], 9.6)])
    c_wall_y(x0, y0 + C_T, y1 - C_T, 0, C_ZT, "w")
    c_wall_y(x1 - C_T, y0 + C_T, C_LOBBY_N, 0, C_ZT, "", holes=[(arch[0], arch[1], 9.5)])
    c_wall_y(x1 - C_T, C_LOBBY_N, y1 - C_T, 0, C_ZT, "e")
    box(x0, y0, C_ZC, x1, y1, C_ZT, "bk_roof", {"b": tspec("gw_ceil", 4)})
    box(x0, y0, 0, x1, y1, C_FL, "bk_roof", {"t": tspec("gw_icarpet", 8)}, group="detail")
    # plaster dado and the stone pilasters either side of the archway to the lobby
    c_band("y", x0 + C_T, y0 + C_T, y1 - C_T, +1)
    c_band("x", y0 + C_T, x0 + C_T, x1 - C_T, +1, holes=[ex_w])
    c_band("x", y1 - C_T, x0 + C_T, x1 - C_T, -1, holes=[wing])
    c_band("y", x1 - C_T, y0 + C_T, y1 - C_T, -1, holes=[arch])
    for a, b in ((arch[0] - 1.6, arch[0]), (arch[1], arch[1] + 1.6)):
        c_slab(x1 - C_T - 1.4, a, x1 - C_T, b, 0, C_ZC, group="detail")
    prop(x1 - C_T - 1.4, arch[0], 9.5, x1 - C_T, arch[1], 10.6, "gw_beam")
    # timber beams across the ceiling every 14 ft
    for y in (22, 36, 50, 64, 78, 92, 106):
        prop(x0 + C_T, y - 0.45, C_ZC - 1.0, x1 - C_T, y + 0.45, C_ZC, "gw_beam")
    for xb in (-24, -2.4, 19.2):
        prop(xb - 0.35, y0 + C_T, C_ZC - 0.5, xb + 0.35, y1 - C_T, C_ZC, "gw_beam")
    # lights, security domes
    for y in (29, 43, 57, 71, 85, 99):
        for x in (-30.5, -17.5, -3.5, 10.5, 24.5):
            c_light(x, y, C_ZC)
    for x, y in ((-30, 28), (22, 28), (-30, 70), (22, 70), (-5, 100), (-5, 18)):
        c_dome(x, y, C_ZC)
    # walls: slate doors with framed pictures between them (west), white louvred shutters (north), TVs
    for y in (40, 60, 80):
        c_flat("x", x0 + C_T, y - 1.6, y + 1.6, C_FL, 7.2, "e", "gw_door", th=0.15)
    for y in (50, 70, 90):
        c_flat("x", x0 + C_T, y - 1.2, y + 1.2, 4.2, 7.9, "e", "gw_frame1", th=0.15, back="gw_trim")
    for xa in (-35.5, -25.5, -15.5, 20.0):
        if xa + 6 < wing[0] or xa > wing[1]:
            c_flat("y", y1 - C_T, xa, xa + 6.0, C_FL, 8.5, "s", "gw_shutter", th=0.15)
    for k, y in enumerate((30, 50, 70, 90)):
        c_tv("x", x0 + C_T, y, 7.4, "e", k)
    for k, y in enumerate((62, 82, 98)):
        c_tv("x", x1 - C_T, y, 7.4, "w", k + 2)
    c_exit("y", y0 + C_T, -19, 9.1, "n")
    c_exit("x", x1 - C_T, 30, 10.6, "w")
    for x, y in ((x0 + 2.5, y1 - 2.5), (-12.5, y1 - 2.0), (x1 - 2.5, y1 - 2.5), (x0 + 2.5, y0 + 2.5), (x1 - 2.5, y0 + 2.5)):
        c_plant(x, y)
    # the tables: five rows, the middle column left open as the long aisle of photo 1
    num = iter((3, 5, 7, 9, 11, 4, 6, 8, 10, 17, 19, 21))
    for cx in (-24, -2.4, 19.2):
        for cy in (34, 49, 64, 79, 94):
            if (cx == 19.2 and cy == 34) or (cx == -2.4 and cy in (34, 64, 94)):
                continue
            c_table(cx, cy, next(num))
    for y in (22, 103):
        ent("info_player_deathmatch", -2.4 if y == 22 else -30.5, y, 2.2, angle=90 if y == 22 else 0)
    ent("info_player_deathmatch", 22, 103, 2.2, angle=180)
    ent("weapon_rocketlauncher", -2.4, 56.5, 1)
    ent("item_health", 21, 56.5, 1)
    ent("item_shells", -30.5, 56.5, 1)
    SPOTS.extend([("Golden West: inside the card room", -2.4 / K, 24 / K, 2.2, 90), ("Golden West: the card room, from the back", -2.4 / K, 100 / K, 2.2, 270)])


def _lobby():
    x0, y0, x1, y1 = CE
    c_wall_x(x0, x1, y0, 0, C_ZT, "s", holes=[(35.2, 42.8, 8.4)])
    c_wall_y(x1 - C_T, y0 + C_T, C_LOBBY_N, 0, C_ZT, "e")
    c_slab(x0, C_LOBBY_N, x1, y1, 0, C_ZT, "n")
    box(x0, y0, C_ZC, x1, C_LOBBY_N, C_ZT, "bk_roof", {"b": tspec("gw_ceil", 4)})
    box(x0, y0, 0, x1, C_LOBBY_N, C_FL, "bk_roof", {"t": tspec("gw_itile", 4)}, group="detail")
    c_band("x", y0 + C_T, x0 + 1.0, x1 - C_T, +1, holes=[(35.2, 42.8)])
    c_band("y", x1 - C_T, y0 + C_T, C_LOBBY_N, -1)
    c_band("x", C_LOBBY_N, x0, x1 - C_T, -1)
    for xb in (40, 54, 68, 82):
        prop(xb - 0.4, y0 + C_T, C_ZC - 0.9, xb + 0.4, C_LOBBY_N, C_ZC, "gw_beam")
    for x in (40, 54, 68, 82):
        for y in (22, 36):
            c_light(x, y, C_ZC, 195)
    c_dome(60, 24, C_ZC)
    c_dome(86, 40, C_ZC)
    # the cage: a counter with a glass screen, the cabinets behind it
    cf = tspec("gw_cwood", 4)
    box(56, 37.0, C_FL, 86, 39.2, 3.6, cf, {"t": "gw_leather"}, group="detail")
    box(55.7, 36.8, 3.6, 86.3, 39.4, 3.8, "gw_leather", group="detail")
    box(56, 37.2, 3.8, 86, 37.35, 6.8, "bk_glass", {"n": Fit("bk_glass"), "s": Fit("bk_glass")}, group="illus")
    for xp in (56, 66, 76, 86):
        prop(xp - 0.1, 37.1, 3.8, xp + 0.1, 37.4, 6.8, "bk_steel")
    box(56, C_LOBBY_N - 1.6, C_FL, 86, C_LOBBY_N, 7.8, cf, group="detail")
    # TVs, benches, plants, the plaque
    for k, y in enumerate((22, 34)):
        c_tv("x", x1 - C_T, y, 7.4, "w", k + 1)
    c_tv("y", C_LOBBY_N, 46, 7.4, "s", 0)
    c_tv("y", C_LOBBY_N, 89, 7.4, "s", 3)
    for yb in (16.5, 28.5):
        prop(86.4, yb, C_FL, 91.0, yb + 7.5, 1.55, "gw_leather")
        prop(90.2, yb, 1.55, 91.0, yb + 7.5, 3.2, "gw_leather")
    for x, y in ((35.2, 42.2), (90.3, 42.2), (49, 16.8), (80, 16.8)):
        c_plant(x, y)
    c_exit("y", y0 + C_T, 39.0, 9.2, "n")
    ent("info_player_deathmatch", 62, 24, 2.2, angle=90)
    ent("item_armor2", 46, 26, 1)
    ent("item_rockets", 80, 24, 1)
    ent("item_health", 62, 30, 1)
    SPOTS.append(("Golden West: the lobby", 62 / K, 22 / K, 2.2, 90))


def _wing():
    x0, y0, x1, y1 = CW
    c_wall_y(x0, y0, y1, 0, C_ZWT, "w")
    c_wall_y(x1 - C_T, y0, y1, 0, C_ZWT, "e")
    c_wall_x(x0, x1, y1 - C_T, 0, C_ZWT, "n")
    box(x0, y0, C_ZW, x1, y1, C_ZWT, "bk_roof", {"b": tspec("gw_ceil", 4)})
    box(x0, y0, 0, x1, y1, C_FL, "bk_roof", {"t": tspec("gw_icarpet", 8)}, group="detail")
    c_band("y", x0 + C_T, y0, y1 - C_T, +1)
    c_band("y", x1 - C_T, y0, y1 - C_T, -1)
    c_band("x", y1 - C_T, x0 + C_T, x1 - C_T, -1)
    for y in (116, 130, 144, 158):
        prop(x0 + C_T, y - 0.4, C_ZW - 0.9, x1 - C_T, y + 0.4, C_ZW, "gw_beam")
    for y in (123, 137, 151, 165):
        for x in (0.5, 12.5):
            c_light(x, y, C_ZW, 175)
    # the bar along the north wall: counter, stools, the back shelves
    cf = tspec("gw_cwood", 4)
    box(-5, 162.6, C_FL, 18, 164.4, 3.6, cf, {"t": "gw_leather"}, group="detail")
    box(-5.3, 162.4, 3.6, 18.3, 164.7, 3.8, "gw_leather", group="detail")
    for x in (-3.5, 0.5, 4.5, 8.5, 12.5, 16.5):
        prop(x - 0.7, 160.6, 2.1, x + 0.7, 161.9, 2.3, "gw_leather")
        prop(x - 0.1, 161.0, C_FL, x + 0.1, 161.2, 2.1, "bk_steel")
    box(-6, y1 - C_T - 1.5, C_FL, 19, y1 - C_T, 7.5, cf, group="detail")
    c_tv("x", x0 + C_T, 130, 6.8, "e", 2)
    c_tv("x", x0 + C_T, 148, 6.8, "e", 3)
    c_tv("x", x1 - C_T, 140, 6.8, "w", 1)
    c_flat("x", x1 - C_T, 119, 123, 4.4, 7.4, "w", "gw_frame1", th=0.15, back="gw_trim")
    c_plant(-6.5, 112.5)
    c_plant(19.2, 112.5)
    num = iter((12, 14, 16))
    for cy in (122, 138, 154):
        c_table((x0 + x1) / 2, cy, next(num))
    ent("weapon_nailgun", (x0 + x1) / 2 + 0.0, 130, 1)
    ent("item_health", (x0 + x1) / 2, 146, 1)
    ent("info_player_deathmatch", (x0 + x1) / 2, 112, 2.2, angle=90)
    SPOTS.append(("Golden West: the high-limit room and bar", (x0 + x1) / 2 / K, 114 / K, 2.2, 90))


# ---------------------------------------------------------------------------------------------- outside
def _entrance():
    """The glass-gabled portico over the doors, the stamped-paving plaza, the round flower bed with the bronze horse (photo 3)."""
    cx, cy = 38.9, -10.0
    box(28, -24, 0, 50, 14.3, 0.1, "gw_flag", {"t": tspec("gw_flag", 6)}, group="detail")
    # door frames and the open sliding glass panes
    for xa, xb in ((35.2, 36.5), (41.5, 42.8)):
        box(xa, 14.45, 0, xb, 14.6, 8.3, "bk_glass", {"s": Fit("bk_glass"), "n": Fit("bk_glass")}, group="illus")
    prop(35.0, 14.265, 0, 35.2, 15.265, 8.4, "bk_steel")
    prop(42.8, 14.265, 0, 43.0, 15.265, 8.4, "bk_steel")
    for xa, xb in ((-22.6, -21.5), (-16.5, -15.4)):
        box(xa, 14.45, 0, xb, 14.6, 8.2, "bk_glass", {"s": Fit("bk_glass"), "n": Fit("bk_glass")}, group="illus")
    c_flat("y", 14.265, 36.0, 42.0, 9.8, 10.7, "s", "gw_1001", th=0.1)
    # portico: two stone piers, a beam and the glass gable (a tile roof, the end wall glazed)
    for px in (29.6, 46.7):
        box(px, 8.0, 0, px + 1.5, 9.5, 12.0, tspec("gw_stone", 3), {"t": "gw_stone"})
    prop(29.6, 8.0, 12.0, 48.2, 9.5, 13.0, "gw_trim")
    gable_rect(29.6, 8.0, 48.2, 14.3, 13.0, tspec("gw_tile", 5), tspec("gw_gable", 3), pitch=0.85, eave=1.2, rake=0.4)
    ent("light", 38.9, 4.0, 11.5, light=150, _color="255 240 215")
    # the round bed: a stone kerb, pansies, the boulder and the statue
    prism(circle(cx, cy, 7.2, 20), 0, 0.9, tspec("gw_stone", 3), group="detail", solid=True)
    prism(circle(cx, cy, 6.6, 20), 0.9, 1.0, tspec("gw_flowers", 4), tspec("gw_stone", 3), group="detail")
    ent("misc_model", cx, cy, 1.4, mdl="progs/gw_horse.md3", angles="0 315 0")
    box(cx - 3.2, cy - 2.7, 0, cx + 3.2, cy + 2.7, 10, "clip")
    ent("light", cx, cy - 8, 12, light=170, _color="255 240 220")
    # wet-floor signs
    for x, y in ((33.2, 4.6), (44.8, 4.2)):
        f = Fit("gw_cone")
        prop(x - 0.55, y - 0.4, 0.1, x + 0.55, y + 0.4, 0.3, "gw_cone")
        prop(x - 0.4, y - 0.3, 0.3, x + 0.4, y + 0.3, 2.3, "gw_cone", {"n": f, "s": f, "e": f, "w": f})


def build_casino():
    with unscaled():
        _hall()
        _lobby()
        _wing()
        _entrance()
