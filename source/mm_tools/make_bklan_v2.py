"""Box B of bklan: the additions from the user's video of 2026-10-30 22:56 (exec'd by make_bklan.py, which has all
the helpers and the map frame). Everything is transplanted from its real place with its real shape and size, laid
out east of Sonora St so E 21st St runs straight on into it:

  Sillect Ave + the Bakersfield Sign   E 21st St becomes Sillect Ave past Buck Owens Blvd; the sign arches over it
                                        ~1100 ft east of Larry's warehouse, in plain view down the street (the user
                                        wanted the sign near the warehouse). Buck Owens' Crystal Palace stands behind it
                                        on the south side as in reality, the 4-storey office on the north side, the
                                        palace's pylon on the corner. Geometry: OSM (osm_site.py, centred 35.3856,
                                        -119.0425) shifted by (+920, -203) ft.
  1608 Manning St + Amberton Park       south of the palace: the house with the white van out front, its backyard,
                                        Manning St, School House Rd, Placer Ct and the park. OSM / city GIS (centred
                                        35.3400, -119.0790) shifted by (+1500, -690) ft.
Measurements and sources: bklan_sign.py (the sign), build_bklan_textures.py build_v2 (the photos)."""

sys.path.insert(0, HERE)
import bklan_sign as BS  # noqa: E402

SITE_P = json.load(open(os.path.join(HERE, "bklan_site_palace.json")))
SITE_M = json.load(open(os.path.join(HERE, "bklan_site_manning.json")))
DXP, DYP = 920, -203
DXM, DYM = 1500, -690
BO_X0, BO_X1 = 677, 763                     # Buck Owens Blvd curbs (86 ft)
SIL_Y0, SIL_Y1 = -34, 28                    # Sillect Ave curbs (62 ft), same centre line as E 21st (y -3)
SIGN_X = 915                                # the arch: 195 ft east of Buck Owens' centre line (satellite)
MAN_X = 80 + DXM                            # Manning St centre line


def P(pt):
    return (pt[0] + DXP, pt[1] + DYP)


def M(pt):
    return (pt[0] + DXM, pt[1] + DYM)


def site_way(site, wid):
    return next(w for w in site["ways"] if w["id"] == wid)


def brush(faces, group="world", solid=True):
    """A convex brush from (p0, p1, p2, outward, texspec) faces, points in units."""
    GROUPS[group].append("{\n" + "".join(face(a, b, c, o, t) for a, b, c, o, t in faces) + "}\n")
    if solid and group != "illus":
        pts = [p for f in faces for p in f[:3]]
        SOLIDS.append(tuple(min(p[i] for p in pts) for i in range(3)) + tuple(max(p[i] for p in pts) for i in range(3)))


def spec(t):
    return t if " " in t else "%s 0 0 0 1 1" % t


def wspec(tex, a0, a1, ztop, zbot, flip, along="y"):
    """A texture laid over a fixed world rectangle on x-facing faces (along="y": s runs along y) or y-facing faces
    (along="x"), feet: a0..a1 across, ztop..zbot down. flip mirrors it for the faces seen from the other side."""
    W, H = TEXSIZE[tex]
    o = OY if along == "y" else OX
    A0, A1 = u(a0, o), u(a1, o)
    xs = (A1 - A0) / W
    if flip:
        xs, xo = -xs, A1 / xs
    else:
        xo = -A0 / xs
    ys = (u(ztop) - u(zbot)) / H
    return "%s %.3f %.3f 0 %.5f %.5f" % (tex, xo, u(ztop) / ys, xs, ys)


def plan_spec(tex, x0, y0, x1, y1):
    """A texture laid over a world rectangle seen from above (floor projection), north up."""
    W, H = TEXSIZE[tex]
    X0_, X1_, Y0_, Y1_ = u(x0, OX), u(x1, OX), u(y0, OY), u(y1, OY)
    sx, sy = (X1_ - X0_) / W, (Y1_ - Y0_) / H
    return "%s %.3f %.3f 0 %.5f %.5f" % (tex, -X0_ / sx, Y1_ / sy, sx, sy)


def offset_convex(poly, d):
    """Grows a convex counter-clockwise polygon by d feet (each edge pushed out, corners re-intersected)."""
    n = len(poly)
    lines = []
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay) or 1
        nx, ny = (by - ay) / L, -(bx - ax) / L
        lines.append(((ax + nx * d, ay + ny * d), (bx - ax, by - ay)))
    out = []
    for i in range(n):
        (p, r), (q, s_) = lines[i - 1], lines[i]
        den = r[0] * s_[1] - r[1] * s_[0]
        if abs(den) < 1e-9:
            out.append(q)
            continue
        t_ = ((q[0] - p[0]) * s_[1] - (q[1] - p[1]) * s_[0]) / den
        out.append((p[0] + r[0] * t_, p[1] + r[1] * t_))
    return out


def ccw(poly):
    a = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if a > 0 else poly[::-1]


def hiproof(poly, z0, tex, eave=1.5, pitch=4 / 12, top=None, group="detail"):
    """Hip roof over a convex footprint: the eave line grown by `eave`, sides rising at `pitch` to a ridge polygon
    shrunk toward the middle (a frustum, flat-topped when the footprint is long). tex: plain name or full spec."""
    base = offset_convex(ccw([tuple(p) for p in poly]), eave)
    cx = sum(p[0] for p in base) / len(base)
    cy = sum(p[1] for p in base) / len(base)
    # inradius-ish: the nearest edge to the middle sets the rise
    dmin = 1e9
    for i in range(len(base)):
        (ax, ay), (bx, by) = base[i], base[(i + 1) % len(base)]
        L = math.hypot(bx - ax, by - ay) or 1
        dmin = min(dmin, abs((bx - ax) * (ay - cy) - (by - ay) * (ax - cx)) / L)
    k = 0.85
    rise = dmin * k * pitch
    topp = [(cx + (x - cx) * (1 - k), cy + (y - cy) * (1 - k)) for x, y in base]
    B = [(u(x, OX), u(y, OY)) for x, y in base]
    Tp = [(u(x, OX), u(y, OY)) for x, y in topp]
    Z0, Z1 = u(z0), u(z0 + rise)
    ts = spec(top or tex)
    fs = []
    n = len(B)
    for i in range(n):
        a, b = B[i], B[(i + 1) % n]
        ta = Tp[i]
        fs.append(((a[0], a[1], Z0), (b[0], b[1], Z0), (ta[0], ta[1], Z1), (b[1] - a[1], -(b[0] - a[0]), 0), spec(tex)))
    fs.append(((B[0][0], B[0][1], Z0), (B[1][0], B[1][1], Z0), (B[2][0], B[2][1], Z0), (0, 0, -1), spec(tex)))
    fs.append(((Tp[0][0], Tp[0][1], Z1), (Tp[1][0], Tp[1][1], Z1), (Tp[2][0], Tp[2][1], Z1), (0, 0, 1), ts))
    brush(fs, group, solid=False)
    return z0 + rise


def pyramid(x0, y0, x1, y1, z0, z1, tex, group="detail"):
    X0_, X1_, Y0_, Y1_, Z0_, Z1_ = u(x0, OX), u(x1, OX), u(y0, OY), u(y1, OY), u(z0), u(z1)
    ax, ay = (X0_ + X1_) // 2, (Y0_ + Y1_) // 2
    c = [(X0_, Y0_), (X1_, Y0_), (X1_, Y1_), (X0_, Y1_)]
    fs = [((X0_, Y0_, Z0_), (X1_, Y0_, Z0_), (X0_, Y1_, Z0_), (0, 0, -1), spec(tex))]
    for i in range(4):
        a, b = c[i], c[(i + 1) % 4]
        fs.append(((a[0], a[1], Z0_), (b[0], b[1], Z0_), (ax, ay, Z1_), (b[1] - a[1], -(b[0] - a[0]), 0), spec(tex)))
    brush(fs, group, solid=False)


def flat_poly(poly, z0, z1, tex, group="detail", side=None):
    for part in convex_parts([tuple(p) for p in poly]):
        prism(part, z0, z1, tex, side=side, group=group)


def lines_x(x0, x1, y, tex="bk_wline", w=0.35, dash=None):
    """Paint along x (dashed: (on, off) feet), not solid."""
    if not dash:
        box(x0, y - w / 2, ROADZ, x1, y + w / 2, ROADZ + 0.02, tex, group="illus")
        return
    x = x0
    while x < x1:
        box(x, y - w / 2, ROADZ, min(x + dash[0], x1), y + w / 2, ROADZ + 0.02, tex, group="illus")
        x += dash[0] + dash[1]


def lines_y(y0, y1, x, tex="bk_wline", w=0.35, dash=None):
    if not dash:
        box(x - w / 2, y0, ROADZ, x + w / 2, y1, ROADZ + 0.02, tex, group="illus")
        return
    y = y0
    while y < y1:
        box(x - w / 2, y, ROADZ, x + w / 2, min(y + dash[0], y1), ROADZ + 0.02, tex, group="illus")
        y += dash[0] + dash[1]


def tree(x, y, h=None, r=None, seed=0):
    """Trunk (solid) and two leaf masses (seen, not solid)."""
    rnd = (seed * 2654435761) % 1000 / 1000
    h = h or 9 + 8 * rnd
    r = r or 6 + 6 * ((rnd * 7) % 1)
    prop(x - .6, y - .6, 0, x + .6, y + .6, h, "bk_bark")
    box(x - r, y - r, h - 1, x + r, y + r, h + r * 0.9, "bk_leaf", group="illus")
    box(x - r * .65, y - r * .65, h + r * 0.9, x + r * .65, y + r * .65, h + r * 1.5, "bk_leaf", group="illus")


def palm(x, y, h=15):
    prop(x - .45, y - .45, 0, x + .45, y + .45, h, "bk_bark")
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        box(min(x, x + dx * 6), min(y, y + dy * 6) - (0.8 if dy == 0 else 0), h - 0.6 - .3,
            max(x, x + dx * 6) + (0 if dx else 0.8), max(y, y + dy * 6) + (0.8 if dy == 0 else 0), h + .2, "bk_leaf",
            group="illus")
    box(x - 2.5, y - 2.5, h - .4, x + 2.5, y + 2.5, h + 1.4, "bk_leaf", group="illus")


def van(x, y, along="y", body="bk_white", side_tex=None):
    """High-roof cargo van (Ram ProMaster in front of 1608 Manning at 154-167 s; KUZZ radio van at 69 s):
    20 x 6.9 x 8.5 ft, black lower cladding/bumpers, cab glass, driver-side rear dark window, rear double-door glass +
    vertical red tail lights, and low-profile roof solar panel."""
    L, W = 10, 3.45
    def bx(a0, a1, b0, b1, z0, z1, tex, faces=None):
        if along == "x":
            prop(x + a0, y + b0, z0, x + a1, y + b1, z1, tex, faces)
        else:
            prop(x + b0, y + a0, z0, x + b1, y + a1, z1, tex, faces)
    side_faces = ({"n": Fit(side_tex), "s": Fit(side_tex)} if along == "x" else {"e": Fit(side_tex), "w": Fit(side_tex)}) if side_tex else None
    bx(-L, L - 3, -W, W, 1.85, 8.5, body, side_faces)
    bx(-L - 0.15, L + 0.15, -W - 0.04, W + 0.04, 0.95, 1.85, "bk_chairbk")       # black plastic lower skirt & bumpers
    bx(L - 3, L, -W, W, 1.85, 4.4, body)
    bx(L - 0.22, L + 0.2, -W + 0.7, W - 0.7, 2.1, 3.6, "bk_chairbk")             # front grille
    bx(L - 3.2, L - 2.2, -W + .25, W - .25, 4.4, 7.6, "bk_glass")                # sloped windshield
    bx(L - 5.4, L - 3.0, -W - .04, W + .04, 4.3, 6.9, "bk_glass", {"t": body})   # cab side windows
    if not side_tex:
        # ProMaster driver-side rear cargo window (154 s, 167 s) + roof solar array
        bx(-L + 1.2, -L + 6.4, -W - .05, -W + .1, 4.6, 6.9, "bk_glass")
        bx(-L + 2.0, L - 4.5, -W + 0.9, W - 0.9, 8.5, 8.68, "bk_solar")
    # Rear double-door windows & vertical red tail-light pillars (154 s)
    for b0, b1 in ((-W + 0.55, -0.15), (0.15, W - 0.55)):
        bx(-L - 0.06, -L + 0.1, b0, b1, 4.6, 7.0, "bk_glass")
    for b0, b1 in ((-W + 0.05, -W + 0.4), (W - 0.4, W - 0.05)):
        bx(-L - 0.06, -L + 0.1, b0, b1, 3.2, 5.8, "bk_red")
    for a in (-L + 2.2, L - 4.4):
        for b in (-W - .08, W - .72):
            bx(a, a + 2.4, b, b + .8, 0, 2.4, "bk_tire")


# ================================================================================================= Sillect Ave
# E 21st St (36 ft) runs on from box A to Buck Owens Blvd; past it, Sillect Ave's 62 ft
for y0, y1, tex in E21:
    box(X1, y0, 0, BO_X0, y1, ROADZ, tex, {"n": "bk_walk", "s": "bk_walk"}, group="detail")
box(X1, 15, 0, BO_X0 - 8, 23, WALKZ, "bk_walk", group="detail")
box(X1, -27, 0, BO_X0 - 8, -21, WALKZ, "bk_walk", group="detail")
box(BO_X0, SIL_Y0 - 6, 0, BO_X1, SIL_Y1 + 6, ROADZ, "bk_road", group="detail")         # the intersection
box(BO_X1, SIL_Y0, 0, XB, SIL_Y1, ROADZ, "bk_road", {"n": "bk_walk", "s": "bk_walk"}, group="detail")
lines_x(BO_X1 + 14, XB, -3.25, "bk_yline")
lines_x(BO_X1 + 14, XB, -2.75 + 0.5, "bk_yline")
for y in (-15, 9):
    lines_x(BO_X1 + 14, XB, y, dash=(10, 30))
for y in (SIL_Y0 + 3, SIL_Y1 - 3):
    lines_x(BO_X1 + 6, XB, y)
for y0, y1 in ((SIL_Y1, SIL_Y1 + 6), (SIL_Y0 - 6, SIL_Y0)):
    box(BO_X1 + 8, y0, 0, XB, y1, WALKZ, "bk_walk", group="detail")
for y0, y1 in ((SIL_Y1 + 6, SIL_Y1 + 30), (SIL_Y0 - 28, SIL_Y0 - 6)):
    box(BO_X1 + 8, y0, 0, XB, y1, WALKZ + 0.05, "bk_lawn", {"n": "bk_walk", "s": "bk_walk", "e": "bk_walk", "w": "bk_walk"}, group="detail")

# Buck Owens Blvd: 86 ft, raised median except at the turn pockets, edge to edge of box B
for y0, y1 in ((YB, SIL_Y0 - 6), (SIL_Y1 + 6, Y1)):
    box(BO_X0, y0, 0, BO_X1, y1, ROADZ, "bk_road", {"e": "bk_walk", "w": "bk_walk"}, group="detail")
    for x0, x1 in ((BO_X0 - 8, BO_X0), (BO_X1, BO_X1 + 8)):
        box(x0, y0, 0, x1, y1, WALKZ, "bk_walk", group="detail")
box(BO_X0 - 8, SIL_Y0 - 6, 0, BO_X0, -27, WALKZ, "bk_walk", group="detail")
box(BO_X0 - 8, 23, 0, BO_X0, SIL_Y1 + 6, WALKZ, "bk_walk", group="detail")
for y0, y1 in ((YB, -110), (100, Y1)):
    box(715, y0, 0, 725, y1, WALKZ, "bk_walk", {"t": "bk_lawn"}, group="detail")
    for x in (694, 705.5, 734.5, 746):
        lines_y(y0, y1, x, dash=(10, 30))
lines_y(-110, SIL_Y0 - 6, 720, "bk_yline")
lines_y(SIL_Y1 + 6, 100, 720, "bk_yline")
# crosswalks (two white bars per leg, OSM: crossing:markings=lines)
for x in (BO_X0 - 4, BO_X1 + 4):
    lines_y(SIL_Y0 - 6, SIL_Y1 + 6, x - 4, w=1)
    lines_y(SIL_Y0 - 6, SIL_Y1 + 6, x + 4, w=1)
for y in (SIL_Y0 - 10, SIL_Y1 + 10):
    lines_x(BO_X0, BO_X1, y - 4, w=1)
    lines_x(BO_X0, BO_X1, y + 4, w=1)


def signal_pole(x, y, arm_dx, arm_dy, length, name_tex):
    """Signal mast: pole, arm at 19 ft, three signal heads, blue street-name sign, high luminaire arm (14 s)."""
    prop(x - .5, y - .5, 0, x + .5, y + .5, 27.5, "bk_steel")
    lx, ly = x + arm_dx * 10, y + arm_dy * 10
    prop(min(x, lx) - .18, min(y, ly) - .18, 27.2, max(x, lx) + .18, max(y, ly) + .18, 27.6, "bk_steel")
    prop(lx - .6, ly - .6, 26.8, lx + .6, ly + .6, 27.2, "bk_white")
    ex, ey = x + arm_dx * length, y + arm_dy * length
    prop(min(x, ex) - .3, min(y, ey) - .3, 18.7, max(x, ex) + .3, max(y, ey) + .3, 19.3, "bk_steel")
    for k in (0.45, 0.7, 0.95):
        hx, hy = x + arm_dx * length * k, y + arm_dy * length * k
        prop(hx - .65, hy - .65, 15, hx + .65, hy + .65, 18.7, "bk_leg")
        light(hx, hy, 14.5, 40, "1 0.2 0.15")
    sx, sy = x + arm_dx * length * 0.25, y + arm_dy * length * 0.25
    if arm_dx:
        prop(sx - 4, sy - .1, 16.4, sx + 4, sy + .1, 18.2, "bk_steel", {"n": Fit(name_tex), "s": Fit(name_tex)})
    else:
        prop(sx - .1, sy - 4, 16.4, sx + .1, sy + 4, 18.2, "bk_steel", {"e": Fit(name_tex), "w": Fit(name_tex)})


signal_pole(BO_X1 + 4, SIL_Y0 - 8, 0, 1, 34, "bk_snbuck")       # over eastbound Sillect
signal_pole(BO_X0 - 4, SIL_Y1 + 8, 0, -1, 34, "bk_snbuck")      # over westbound E 21st
signal_pole(BO_X0 - 4, SIL_Y0 - 8, 1, 0, 40, "bk_snsillect")    # over northbound Buck Owens
signal_pole(BO_X1 + 4, SIL_Y1 + 8, -1, 0, 40, "bk_snsillect")   # over southbound
# speed limit 35, by the south tower, facing eastbound traffic (0 s)
prop(SIGN_X + 30, SIL_Y0 - 3.4, 0, SIGN_X + 30.25, SIL_Y0 - 3.15, 9.8, "bk_steel")
prop(SIGN_X + 29.85, SIL_Y0 - 4.5, 7, SIGN_X + 30.0, SIL_Y0 - 2.0, 10, "bk_white", {"w": Fit("bk_speed35"), "e": "bk_white"})

# ================================================================================================= the Bakersfield Sign


def tower(tx, ty, inner):
    """One tower. inner: 'n' or 's', the face toward the road (the arch meets it; no seal there)."""
    h = BS.BASE / 2
    # base: four corner piers round a pass-through in each face, its top stepped to the arch curve
    pier = (BS.BASE - 4.2) / 2
    trim_ns = wspec("bk_btrim", tx - h, tx + h, 10.5, 7.0, False, along="x")
    trim_ns_f = wspec("bk_btrim", tx - h, tx + h, 10.5, 7.0, True, along="x")
    trim_ew = wspec("bk_btrim", ty - h, ty + h, 10.5, 7.0, False)
    trim_ew_f = wspec("bk_btrim", ty - h, ty + h, 10.5, 7.0, True)
    trim = {"n": trim_ns_f, "s": trim_ns, "e": trim_ew, "w": trim_ew_f}
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0 = tx + sx * h, ty + sy * h
            xs_ = sorted((x0, x0 - sx * pier))
            ys_ = sorted((y0, y0 - sy * pier))
            box(xs_[0], ys_[0], 0, xs_[1], ys_[1], 7, "bk_bstucco", group="detail")
            box(xs_[0], ys_[0], 7, xs_[1], ys_[1], 8.6, "bk_bstucco", trim, group="detail")
    steps = ((7.0, 7.6, 1.95), (7.6, 8.0, 1.64), (8.0, 8.3, 1.22), (8.3, 8.5, 0.73), (8.5, 8.6, 0.0))
    for z0, z1, hw in steps:
        for sx in (-1, 1):                         # fill over the x-running passage, beside it
            box(min(tx + sx * 2.1, tx + sx * hw) if hw else tx - 2.1, ty - h, z0,
                max(tx + sx * 2.1, tx + sx * hw) if hw else tx + 2.1, ty + h, z1, "bk_bstucco",
                {"n": trim_ns_f, "s": trim_ns}, group="detail")
            if not hw:
                break
        for sy in (-1, 1):
            box(tx - h, min(ty + sy * 2.1, ty + sy * hw) if hw else ty - 2.1, z0,
                tx + h, max(ty + sy * 2.1, ty + sy * hw) if hw else ty + 2.1, z1, "bk_bstucco",
                {"e": trim_ew, "w": trim_ew_f}, group="detail")
            if not hw:
                break
    box(tx - h, ty - h, 8.6, tx + h, ty + h, 10.5, "bk_bstucco", trim, group="detail")
    box(tx - h, ty - h, 10.5, tx + h, ty + h, 14.3, "bk_bstucco", group="detail")
    box(tx - h, ty - h, 0, tx + h, ty + h, 0.3, "bk_btan", group="detail")             # plinth
    box(tx - 5.3, ty - 5.3, 14.3, tx + 5.3, ty + 5.3, 16.3, "bk_btan", group="detail")  # ledge
    s2 = BS.SHAFT / 2
    up = {k: Fit("bk_bupper") for k in "nsew" if k != inner}
    up[inner] = "bk_bstucco"
    box(tx - s2, ty - s2, 16.3, tx + s2, ty + s2, 26.4, "bk_bstucco", up, group="detail")
    box(tx - 5.0, ty - 5.0, 26.4, tx + 5.0, ty + 5.0, 28.9, "bk_btan", group="detail")   # cap band
    box(tx - 7, ty - 7, 28.9, tx + 7, ty + 7, 29.3, "bk_broof", group="detail")          # eaves
    pyramid(tx - 7, ty - 7, tx + 7, ty + 7, 29.3, 31.0, "bk_broof")


tower(SIGN_X, -3 + BS.HALF, "s")
tower(SIGN_X, -3 - BS.HALF, "n")
# the arch band: 24 segments from tower centre to tower centre, the photo-matched band texture laid over the span
yc = -3
xa, xb = u(SIGN_X - BS.DEPTH / 2, OX), u(SIGN_X + BS.DEPTH / 2, OX)
east = wspec("bk_bsign", yc - BS.HALF, yc + BS.HALF, BS.ZMAX, BS.ZMIN, False)
west = wspec("bk_bsign", yc - BS.HALF, yc + BS.HALF, BS.ZMAX, BS.ZMIN, True)
N = 24
for k in range(N):
    sa, sb = -BS.HALF + BS.SPACING * k / N, -BS.HALF + BS.SPACING * (k + 1) / N
    ya, yb = u(yc + sa, OY), u(yc + sb, OY)
    zba, zta, zbb, ztb = u(BS.zb(sa)), u(BS.zt(sa)), u(BS.zb(sb)), u(BS.zt(sb))
    band = spec("bk_bband")
    brush([((xa, ya, zba), (xa, yb, zbb), (xa, ya, zta), (-1, 0, 0), west),
           ((xb, ya, zba), (xb, ya, zta), (xb, yb, zbb), (1, 0, 0), east),
           ((xa, ya, zba), (xb, ya, zba), (xa, ya, zta), (0, -1, 0), band),
           ((xa, yb, zbb), (xb, yb, zbb), (xa, yb, ztb), (0, 1, 0), band),
           ((xa, ya, zta), (xb, ya, zta), (xa, yb, ztb), (0, 0, 1), band),
           ((xa, ya, zba), (xb, ya, zba), (xa, yb, zbb), (0, 0, -1), band)], "detail")

# ================================================================================================= the palace block
# Buck Owens' Crystal Palace: two storeys of western false fronts and porches (80 s), shingle hip roofs
cp = ccw([P(q) for q in site_way(SITE_P, "59574412")["pts"][:-1]])
cp_parts = convex_parts(cp)
for part in cp_parts:
    prism(part, 0, 24, "bk_roof", side=tspec("bk_cpfront", 24), solid=True)
for part in cp_parts:
    hiproof(part, 24, "bk_cpshingle", eave=1.2, pitch=5 / 12)
for (x0, y0), (x1, y1) in zip(cp, cp[1:] + cp[:1]):     # porches along the street-facing walls (west and north)
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 30:
        continue
    nx, ny = (y1 - y0) / L, -(x1 - x0) / L                # outward for a counter-clockwise ring
    if not (nx < -0.9 or ny > 0.9):
        continue
    if abs(nx) > 0.9:
        xw = min(x0, x1)
        box(xw - 8, min(y0, y1), 10.5, xw, max(y0, y1), 11.2, "bk_cpshingle", {"b": "bk_cpwall"}, group="detail")
        box(xw - 8, min(y0, y1), 13.8, xw - 7.7, max(y0, y1), 14.2, "bk_cpwall", group="detail")
        yy = min(y0, y1) + 2
        while yy < max(y0, y1) - 1:
            prop(xw - 7.8, yy, 0, xw - 7.2, yy + .6, 10.5, "bk_cpwall")
            prop(xw - 7.9, yy, 11.2, xw - 7.7, yy + .2, 13.8, "bk_cpwall")
            yy += 9
    else:
        yw = max(y0, y1)
        box(min(x0, x1), yw, 10.5, max(x0, x1), yw + 8, 11.2, "bk_cpshingle", {"b": "bk_cpwall"}, group="detail")
        box(min(x0, x1), yw + 7.7, 13.8, max(x0, x1), yw + 8, 14.2, "bk_cpwall", group="detail")
        xx = min(x0, x1) + 2
        while xx < max(x0, x1) - 1:
            prop(xx, yw + 7.2, 0, xx + .6, yw + 7.8, 10.5, "bk_cpwall")
            xx += 9
# lawn and wrought-iron fence along Buck Owens, Sillect south edge + shaped hedge round the south sign tower (0 s),
# north service drive, KUZZ arched 2-storey porte-cochere & KUZZ van (69 s), and western false-front parapets (80 s)
box(BO_X1 + 8, -430, 0, 790, SIL_Y0 - 28, WALKZ + 0.05, "bk_lawn", {"e": "bk_walk", "w": "bk_walk"}, group="detail")
for y0, y1 in ((-430, -300), (-280, SIL_Y0 - 30)):
    box(790, y0, 0, 790.3, y1, 6, Fit("{iron", ((y1 - y0) / 5.3, 1)), group="fence")
# Shaped green hedge wrapping the south Bakersfield Sign tower base + black iron fence along Sillect Ave (0 s)
st_y = -3 - BS.HALF
for hx0, hy0, hx1, hy1 in ((SIGN_X - 7.5, st_y - 7.6, SIGN_X + 7.5, st_y - 5.3),
                           (SIGN_X - 7.5, st_y - 5.3, SIGN_X - 5.3, st_y - 1.0),
                           (SIGN_X + 5.3, st_y - 5.3, SIGN_X + 7.5, st_y - 1.0)):
    prop(hx0, hy0, WALKZ, hx1, hy1, 3.8, "bk_hedge")
for fx0, fx1 in ((792, SIGN_X - 9), (SIGN_X + 9, 1020)):
    box(fx0, SIL_Y0 - 27.5, WALKZ, fx1, SIL_Y0 - 27.2, 6.2, Fit("{iron", ((fx1 - fx0) / 5.3, 1)), group="fence")
# Crystal Palace western false-front stepped parapets rising above the 24 ft eave (80 s)
for fy0, fy1, fz, ftex in ((-254, -228, 29.0, "bk_cpwall"), (-226, -202, 27.2, "bk_cppink"), (-198, -184, 28.2, "bk_cpwall")):
    box(856.6, fy0, 24.0, 858.2, fy1, fz, ftex, {"t": "bk_btan"}, group="detail")
# Crystal Palace north service drive, semicircular concrete apron, 2-storey arched KUZZ porte-cochere & KUZZ van (69 s)
box(792, -92, 0, 1020, -68, ROADZ, "bk_road", group="detail")
box(846, -120, 0, 888, -88, WALKZ * 0.5, "bk_walk", group="detail")
# Porte-cochere columns, 2nd-floor balustrade & arched gable canopy projecting north from NW wing (850..884, -118..-95)
for px_ in (850, 860, 874, 884):
    prop(px_, -96.5, 0, px_ + 1.6, -94.9, 11.5, "bk_hstucco")
    prop(px_ + .2, -96.3, 12.2, px_ + 1.4, -95.1, 20.5, "bk_hstucco")
box(849.5, -118, 11.5, 885.5, -94.5, 12.2, "bk_hstucco", group="detail")
# 2nd-floor white balustrade flanking the central arch (850..860 and 874..885)
for rx0, rx1 in ((850.2, 860.0), (875.6, 884.0)):
    prop(rx0, -95.8, 14.8, rx1, -95.4, 15.1, "oc_white")
    xx_ = rx0 + 0.5
    while xx_ < rx1 - 0.3:
        prop(xx_, -95.7, 12.2, xx_ + 0.2, -95.5, 14.8, "oc_white")
        xx_ += 0.9
# Upper arch spandrel & gabled shingle roof over the porte-cochere
for ax0, ax1, az0 in ((849.5, 861.6, 20.5), (861.6, 864.5, 21.6), (864.5, 871.1, 22.4), (871.1, 874.0, 21.6), (874.0, 885.5, 20.5)):
    box(ax0, -118, az0, ax1, -94.5, 23.2, "bk_hstucco", group="detail")
hiproof([(849.5, -118), (885.5, -118), (885.5, -94.5), (849.5, -94.5)], 23.2, "bk_cpshingle", eave=1.0, pitch=4.5 / 12)
# KUZZ AM 55 / FM 107.9 radio van parked under the north porte-cochere (69 s)
van(867.5, -103.5, along="x", body="oc_blue", side_tex="bk_kuzz")

prop(781.2, -104, 0, 782.8, -102.4, 26, "bk_white")
prop(780.5, -117, 26, 783.5, -89, 38, "bk_chairbk", {"e": Fit("bk_cpsign"), "w": Fit("bk_cpsign")})
# the 4-storey office north of the sign: dark lower 2 floors (0-27 ft) and cream precast upper 2 floors (27-55 ft, 0 & 14 s)
for part in convex_parts([P(q) for q in site_way(SITE_P, "59589538")["pts"][:-1]]):
    prism(part, 0, 27, "bk_roof", side=tspec("bk_officedk", 13.5), solid=True)
    prism(part, 27, 55, "bk_roof", side=tspec("bk_office", 14), solid=False)
    prism(offset_convex(ccw(part), 0.7), 55, 56.4, "bk_roof", side="bk_hstucco", group="detail")
for wid, h, wt in (("59567975", 18, "bk_shopwall"), ("59589678", 20, "bk_unitwall")):
    for part in convex_parts([P(q) for q in site_way(SITE_P, wid)["pts"][:-1]]):
        prism(part, 0, h, "bk_roof", side=tspec(wt, 20), solid=True)
# the palace's parking east of it (OSM aisles at local x 150-311), with cars
for k, cx in enumerate(range(1030, 1230, 20)):
    lines_y(-250, -150, cx, w=0.3)
    if k % 3 != 1:
        car(cx + 10, -200 + (k % 2) * 30, "y", ("bk_white", "bk_red", "bk_chairbk", "bk_blue")[k % 4], 16)

# ================================================================================================= Manning St
# Manning St runs from the south edge up to Sillect Ave; School House Rd west to Buck Owens; Placer Ct; Vallecito Ln
box(MAN_X - 18, YB, 0, MAN_X + 18, SIL_Y0 - 6, ROADZ, "bk_road", {"e": "bk_walk", "w": "bk_walk"}, group="detail")
for x0, x1 in ((MAN_X - 23, MAN_X - 18), (MAN_X + 18, MAN_X + 23)):
    box(x0, YB, 0, x1, -40, WALKZ, "bk_walk", group="detail")
lines_y(-470, SIL_Y0 - 6, MAN_X, "bk_yline")
schoolhouse = [(BO_X1, -786)] + [M(q) for q in ((-714, -88), (-675, -70), (-597, -39), (-518, -14), (-436, 6),
                                               (-354, 20), (-261, 29), (-219, 30), (80, 29))]
road(schoolhouse, 36, group="detail")
for off in (20.5, -20.5):
    ribbon(schoolhouse, 5, "bk_walk", z=WALKZ, offset=off, group="detail",
           skip=lambda x, y: abs(x - MAN_X) < 26 or abs(x - M((-261, 0))[0]) < 26 or x < BO_X1 + 30)
placer = [M((-261, 29)), M((-261, -337))]
road(placer, 36, group="detail")
pcx, pcy = M((-261, -337))
prism([(pcx + 42 * math.cos(a * math.pi / 4), pcy + 42 * math.sin(a * math.pi / 4)) for a in range(8)], 0, ROADZ,
      "bk_road", group="detail")
for off in (20.5, -20.5):
    ribbon(placer, 5, "bk_walk", z=WALKZ, offset=off, group="detail", skip=lambda x, y: y > M((0, 0))[1] - 20 or y < pcy + 40)
vallecito = [M(q) for q in ((-714, -88), (-634, -255), (-619, -302), (-610, -342), (-606, -391), (-605, -440))]
road(vallecito, 36, group="detail")

# the houses: city GIS footprints, single-storey ranch houses (9 ft walls, hip roofs), stucco and shingle varied
ZONE_M = lambda q: -720 <= q[0] <= 360 and -420 <= q[1] <= 230
HERO = "60015084"
walls = ("bk_hstucco", "bk_stucco", "bk_cpwall", "bk_hstucco")
roofs = ("bk_shingle", "bk_cpshingle", "bk_roof", "bk_shingle")
for k, w in enumerate(SITE_M["ways"]):
    if "building" not in w["tags"] or not all(ZONE_M(q) for q in w["pts"]) or w["id"] == HERO:
        continue
    fp = [M(q) for q in w["pts"][:-1]]
    for part in convex_parts(fp):
        prism(part, 0, 9, "bk_roof", side=tspec(walls[k % 4], 10), solid=True)
        hiproof(part, 9, roofs[(k // 2) % 4])
    xs = [p[0] for p in fp]
    ys = [p[1] for p in fp]
    if abs(min(xs) - (MAN_X + 23)) < 60 and min(xs) > MAN_X:      # driveways to Manning St, east side
        cy = sum(ys) / len(ys) - 12
        box(MAN_X + 23, cy - 9, 0, min(xs), cy + 9, 0.06, "bk_walk", group="detail")
    elif abs(max(xs) - (MAN_X - 23)) < 60 and max(xs) < MAN_X:    # west side
        cy = sum(ys) / len(ys) - 12
        box(max(xs), cy - 9, 0, MAN_X - 23, cy + 9, 0.06, "bk_walk", group="detail")

# ---------------------------------------------------------------------------------------------- 1608 Manning St
# The house (GIS 60015084, 55 x 67 ft): garage wing at the south end of the front with the white sectional door,
# entry in the recess beside it, brown hip roof with the solar arrays, big lawn backyard with a flagstone patio and
# trees, block walls on the lot lines (aerials 199-217 s, Street View 153-170 s).
hero = [M(q) for q in site_way(SITE_M, HERO)["pts"][:-1]]
roof_tex = plan_spec("bk_h1608roof", *M((130, 72)), *M((190, 143)))
for part in convex_parts(hero):
    prism(part, 0, 9, "bk_roof", side=tspec("bk_hstucco", 10), solid=True)
    hiproof(part, 9, roof_tex)
gx = M((132.4, 0))[0]
_, gy0 = M((0, 79.5))
_, gy1 = M((0, 95.5))
prop(gx - 0.12, gy0, 0, gx, gy1, 7, "bk_garage", {"w": Fit("bk_garage")})
ex = M((149.9, 0))[0]
_, ey0 = M((0, 105.5))
prop(ex - 0.12, ey0, 0, ex, ey0 + 3, 6.9, "bk_blkdoor", {"w": Fit("bk_door")})
fx = M((137.4, 0))[0]
for wy in (117, 129):
    _, y0 = M((0, wy))
    prop(fx - 0.1, y0, 3, fx, y0 + 7, 7, "bk_darkwin", {"w": Fit("bk_darkwin")})
# driveway, the lime-green car, the grey hatchback and the blue pickup in it, the white ProMaster van parked at the
# north lawn curb (154, 163, 167 s), two black trash carts south of the driveway (163 s), brick-edged front walk & trees
_, dy0 = M((0, 77))
_, dy1 = M((0, 97))
box(MAN_X + 23, dy0, 0, gx, dy1, 0.08, "bk_walk", group="detail")
# Front entry concrete walkway with low red-brick step border walls leading to the recessed front door (154 s, 163 s)
_, wy0 = M((0, 105.0))
_, wy1 = M((0, 111.0))
box(MAN_X + 23, wy0, 0, ex, wy1, 0.10, "bk_walk", group="detail")
for by_0, by_1 in ((wy0 - 0.7, wy0), (wy1, wy1 + 0.7)):
    prop(M((130, 0))[0], by_0, 0, ex - 0.5, by_1, 1.3, "bk_brick")
car(M((118, 0))[0], M((0, 92.5))[1], "x", "bk_lime", 16.5, 6.3)
car(M((121, 0))[0], M((0, 82))[1], "x", "bk_blue", 18, 6.6, pickup=True)
car(M((106, 0))[0], M((0, 86))[1], "x", "bk_white", 13.5, 5.8, cab_h=2.2)
# White Ram ProMaster van parked at the east curb in front of the north lawn, nose facing north (+y), clear of driveway!
van(M((93.5, 0))[0], M((0, 126))[1], "y")
# Two black wheeled trash carts in the street at the east curb SOUTH of the driveway (163 s)
for by in (67.5, 71.5):
    prop(M((95.5, 0))[0] - 1, M((0, by))[1] - 1, 0, M((95.5, 0))[0] + 1, M((0, by))[1] + 1, 3.6, "bk_chairbk")
prop(M((101, 0))[0] - .15, M((0, 103.5))[1] - .15, 0, M((101, 0))[0] + .15, M((0, 103.5))[1] + .15, 3.4, "bk_bark")
prop(M((101, 0))[0] - .6, M((0, 103.5))[1] - .35, 3.4, M((101, 0))[0] + .6, M((0, 103.5))[1] + .35, 4.3, "bk_chairbk")
palm(*M((126, 136)), h=17)
tree(*M((114, 118)), h=10.5, r=7.5, seed=16)                                     # mature front-lawn shade trees (154 s)
tree(*M((112, 134)), h=11.5, r=8.0, seed=18)
for hy in range(112, 140, 4):                                                    # shrubs along the front
    prop(fx - 3, M((0, hy))[1], 0, fx - .2, M((0, hy + 3.5))[1], 3, "bk_hedge")
# backyard: lawn (the zone's), flagstone patio + covered rear patio overhang on SE side (217 s), trees, block walls
box(*M((188, 112)), 0, *M((203, 138)), 0.12, "bk_flagstone", group="detail")
box(*M((186, 75)), 0, *M((204, 104)), 0.12, "bk_walk", group="detail")
box(*M((186, 74)), 8.3, *M((205, 105)), 8.9, "bk_shingle", {"b": "bk_hstucco"}, group="detail")
for py_ in (75.5, 90.0, 103.5):
    prop(*M((203.5, py_)), 0.12, *M((204.2, py_ + 0.7)), 8.3, "bk_bark")
for q, h in (((205, 75), 13), ((224, 80), 15), ((226, 134), 12), ((212, 128), 10)):
    tree(*M(q), h=h, seed=int(q[0] + q[1]))
for (ax, ay), (bx, by) in (((140, 66), (233, 66)), ((140, 143), (233, 143)), ((233, -50), (233, 230))):
    (x0, y0), (x1, y1) = M((ax, ay)), M((bx, by))
    box(min(x0, x1), min(y0, y1), 0, max(x0, x1) + (0.67 if x0 == x1 else 0), max(y0, y1) + (0.67 if y0 == y1 else 0), 6,
        "bk_blockgr", group="detail")
# the neighbours' pools (1604 behind its house, the house across the back wall)
for (x0, y0), (x1, y1) in (((200, 14), (222, 34)), ((240, 95), (262, 117))):
    box(*M((x0 - 2, y0 - 2)), 0, *M((x1 + 2, y1 + 2)), 0.15, "bk_walk", group="detail")
    box(*M((x0, y0)), 0.15, *M((x1, y1)), 0.2, "bk_pool", group="illus")

# ---------------------------------------------------------------------------------------------- Amberton Park
park = [M(q) for q in site_way(SITE_M, "60113897")["pts"][:-1]]
flat_poly(park, 0, 0.08, "bk_drygrass", side="bk_walk")
flat_poly([M(q) for q in site_way(SITE_M, "60647048")["pts"][:-1]], 0, 0.14, "bk_sand", side="bk_walk")
for wid in ("60644823", "60645180", "60645415", "60645771", "60646979"):
    pad = [M(q) for q in site_way(SITE_M, wid)["pts"][:-1]]
    flat_poly(pad, 0, 0.16, "bk_walk")
    cx = sum(p[0] for p in pad) / len(pad)
    cy = sum(p[1] for p in pad) / len(pad)
    if wid == "60644823":                                          # the restroom building
        prism(ccw([(cx - 9, cy - 8), (cx + 9, cy - 8), (cx + 9, cy + 8), (cx - 9, cy + 8)]), 0.16, 9, "bk_roof",
              side=tspec("bk_extwall", 10), solid=True)
        hiproof([(cx - 9, cy - 8), (cx + 9, cy - 8), (cx + 9, cy + 8), (cx - 9, cy + 8)], 9, "bk_cpshingle")
        continue
    if wid == "60646979":                                          # foreground utility pad: red backflow pipe + bushes (240 s)
        prop(cx - 2.2, cy - 0.15, 0.16, cx + 2.2, cy + 0.15, 2.6, "bk_playred")
        for bdx, bdy in ((-5, -3), (4, 2)):
            prop(cx + bdx - 1.8, cy + bdy - 1.8, 0.16, cx + bdx + 1.8, cy + bdy + 1.8, 3.0, "bk_hedge")
        continue
    if wid == "60645771":                                          # picnic shade shelter: low-slope white metal roof on brown posts (240, 243 s)
        for px_, py_ in ((-16, -16), (16, -16), (16, 16), (-16, 16)):
            prop(cx + px_ - .4, cy + py_ - .4, 0.16, cx + px_ + .4, cy + py_ + .4, 9.5, "bk_bark")
        box(cx - 17.5, cy - 17.5, 9.2, cx + 17.5, cy + 17.5, 9.6, "oc_white", group="detail")
        hiproof([(cx - 16, cy - 16), (cx + 16, cy - 16), (cx + 16, cy + 16), (cx - 16, cy + 16)], 9.6, "oc_white",
                eave=1.5, pitch=1.6 / 12)
        # Tan concrete planter box & shrub under the shelter corner (240 s, 243 s)
        prop(cx + 9, cy + 9, 0.16, cx + 14.5, cy + 14.5, 2.2, "bk_btan")
        prop(cx + 9.6, cy + 9.6, 2.2, cx + 13.9, cy + 13.9, 4.6, "bk_hedge")
    for tx_ in (-4, 4):                                            # picnic tables
        prop(cx + tx_ - 1.25, cy - 3, 2.4, cx + tx_ + 1.25, cy + 3, 2.6, "bk_wood")
        prop(cx + tx_ - .2, cy - .2, 0.16, cx + tx_ + .2, cy + .2, 2.4, "bk_steel")
        for bx_ in (-2.1, 1.6):
            prop(cx + tx_ + bx_, cy - 3, 1.4, cx + tx_ + bx_ + .5, cy + 3, 1.55, "bk_wood")
# play structure: three decks with teal roofs, green slides, red panels; 2-bay swing set, benches & light poles (240 s)
px0, py0 = M((-405, -215))
for dx, dy in ((0, 0), (8, 0), (8, 8)):
    x, y = px0 + dx, py0 + dy
    for ox, oy in ((0, 0), (5, 0), (5, 5), (0, 5)):
        prop(x + ox - .25, y + oy - .25, 0.14, x + ox + .25, y + oy + .25, 9, "bk_playgreen")
    prop(x, y, 4, x + 5, y + 5, 4.4, "bk_playred")
    pyramid(x - .6, y - .6, x + 5.6, y + 5.6, 9, 11.2, "bk_playteal")
    prop(x - .05, y + .5, 4.4, x + .05, y + 4.5, 6.5, "bk_playred")
prism([(px0 - 9, py0 + 1), (px0, py0 + 1), (px0, py0 + 4), (px0 - 9, py0 + 4)], [0.5, 3.7, 3.7, 0.5], [0.9, 4.1, 4.1, 0.9],
      "bk_playgreen", group="detail")
prism([(px0 + 13, py0 + 13), (px0 + 16, py0 + 13), (px0 + 16, py0 + 22), (px0 + 13, py0 + 22)], [3.7, 3.7, 0.5, 0.5],
      [4.1, 4.1, 0.9, 0.9], "bk_playgreen", group="detail")
sx_, sy_ = M((-438, -270))
for ox in (0, 11, 22):                                             # 2-bay swing set (3 dark arch frames, 4 swings, 240 s)
    for oy in (-2, 2):
        prop(sx_ + ox - .2, sy_ + oy - .2, 0.14, sx_ + ox + .2, sy_ + oy + .2, 9, "bk_leg")
    prop(sx_ + ox - .2, sy_ - 2.2, 8.8, sx_ + ox + .2, sy_ + 2.2, 9.2, "bk_leg")
prop(sx_ - .3, sy_ - .3, 9, sx_ + 22.3, sy_ + .3, 9.4, "bk_leg")
for ox in (2.5, 7.0, 13.5, 18.0):
    prop(sx_ + ox, sy_ - .7, 1.8, sx_ + ox + 2, sy_ + .7, 2.0, "bk_chairbk")
    prop(sx_ + ox + .9, sy_ - .05, 2.0, sx_ + ox + 1.0, sy_ + .05, 9, "bk_leg", group="illus")
# Park benches & tall park light poles round the sand border (240 s)
for bx_, by_ in (M((-382, -205)), M((-422, -286))):
    prop(bx_ - 3, by_ - .8, 1.4, bx_ + 3, by_ + .8, 1.6, "bk_bark")
    prop(bx_ - 3, by_ + .6, 1.6, bx_ + 3, by_ + .85, 2.9, "bk_bark")
    for lx_ in (-2.2, 2.0):
        prop(bx_ + lx_, by_ - .7, 0.14, bx_ + lx_ + .25, by_ + .7, 1.4, "bk_leg")
for lx_, ly_ in (M((-372, -192)), M((-448, -252))):
    prop(lx_ - .25, ly_ - .25, 0.14, lx_ + .25, ly_ + .25, 20, "bk_steel")
    prop(lx_ - .9, ly_ - .9, 20, lx_ + .9, ly_ + .9, 20.6, "bk_white")
# paths from the streets to the pads
for path in (((-291, -150), (-372, -200), (-394, -255)), ((-430, -15), (-410, -120), (-415, -200)),
             ((-600, -200), (-500, -250), (-445, -280))):
    ribbon([M(q) for q in path], 6, "bk_walk", z=0.12, side_tex="bk_walk", group="detail")

# trees: every OSM tree in the zone (the park's and the yards')
for k, p in enumerate(SITE_M["points"]):
    if p["tags"].get("natural") == "tree" and ZONE_M(p["pt"]):
        tree(*M(p["pt"]), seed=k + 1)
for k, q in enumerate(((-90, 60), (-40, 140), (40, 180), (200, 200), (300, 30), (-150, 100), (-200, -100),
                       (-120, -250), (20, -300), (250, -200), (310, -340), (-60, -380))):
    tree(*M(q), seed=k + 101)

# parked cars along the residential streets
for k, y in enumerate(range(-1080, -480, 70)):
    car(MAN_X - 13, y, "y", ("bk_white", "bk_chairbk", "bk_red", "bk_blue")[k % 4], 15.5, 6.2)

# ================================================================================================= gameplay, viewer spots
for x, y, a in ((SIGN_X - 60, -3, 0), (SIGN_X + 40, 10, 180), (800, -300, 90), (1000, -200, 90), (900, 66, 270),
                (MAN_X + 10, -500, 270), (*M((165, 60)), 180), (*M((210, 100)), 180), (*M((-400, -120)), 270),
                (*M((-500, -300)), 45), (*M((-261, -250)), 90), (1400, 250, 180), (1700, -200, 180)):
    ent("info_player_deathmatch", x, y, 2.2, angle=a)
for name, x, y, z in (("weapon_rocketlauncher", SIGN_X, -3, 0), ("item_armor2", *M((-405, -250)), 0.2),
                      ("weapon_supernailgun", *M((210, 110)), 0), ("item_health", 840, -80, 0),
                      ("item_health", *M((-300, -100)), 0), ("item_shells", 1100, 120, 0),
                      ("item_rockets", *M((112, 60)), 0), ("item_cells", 1500, -250, 0),
                      ("weapon_grenadelauncher", *M((-600, -150)), 0), ("item_spikes", MAN_X, -300, 0)):
    ent(name, x, y, z + 1)
V2_SPOTS = [("The Bakersfield Sign", SIGN_X - 120, -3, 2.2, 0), ("Under the arch", SIGN_X + 3, 6, 2.2, 180),
            ("Buck Owens' Crystal Palace", 800, -200, 2.2, 0), ("Buck Owens Blvd & Sillect", 700, 60, 2.2, 315),
            ("1608 Manning St", MAN_X - 8, *M((0, 70))[1:], 2.2, 0), ("1608's backyard", *M((222, 105)), 2.2, 180),
            ("Amberton Park", *M((-330, -150)), 2.2, 225), ("Placer Ct", *M((-261, -100)), 2.2, 270)]
