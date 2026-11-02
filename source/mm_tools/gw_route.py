"""The S Union Ave street from OpenStreetMap (road centrelines, city-GIS building footprints), for one segment of the route
(SEG_Y0 .. SEG_Y1, true feet, casino frame; exec'd by make_goldenwest.py / make_union.py after gwbase.py, inside unscaled()).
Frame: OSM lat/lon -> feet with the casino marker as origin, then shifted (-24.9, +92.2) so Delaware St and Trinity Ave land on the
hand-built casino parcel (both checked: Union Ave's west carriageway then lands 1.6 ft from where it was measured).
Union Ave: the OSM carriageway pairs only give a centre line; the cross-section is the one measured at the casino (3 lanes of
12.9 ft each way, a 15.8 ft red-brick median, 6 ft sidewalks). Cross streets: width by road class. Buildings: footprints, extruded
to a height from the OSM tags or from their size; walls and roofs are generic (no photos of most of them are used here).
Not built: the E Truxtun Ave underpass, the SR-58 freeway deck, signals, per-building signs (see the report)."""
import glob
import pickle
import xml.etree.ElementTree as ET

import numpy as np

_LAT0, _LON0 = 35.345186, -119.0037921
_FX = 111320 * math.cos(math.radians(_LAT0)) * 3.28084
_FY = 110574 * 3.28084
_SHX, _SHY = -24.9, 92.2
_CACHE = os.path.join(HERE, "out", "osm_route.pkl")


def _load_osm():
    if os.path.exists(_CACHE):
        return pickle.load(open(_CACHE, "rb"))
    nodes, ways = {}, []
    for f in sorted(glob.glob(os.path.join(HERE, "ref_sources", "osm_route", "route_*.xml"))):
        t = ET.parse(f).getroot()
        for n in t.findall("node"):
            nodes[n.get("id")] = ((float(n.get("lon")) - _LON0) * _FX + _SHX, (float(n.get("lat")) - _LAT0) * _FY + _SHY)
        for w in t.findall("way"):
            tags = {k.get("k"): k.get("v") for k in w.findall("tag")}
            ways.append((w.get("id"), tags, [n.get("ref") for n in w.findall("nd")]))
    seen, uniq = set(), []
    for w in ways:
        if w[0] not in seen:
            seen.add(w[0])
            uniq.append(w)
    pickle.dump((nodes, uniq), open(_CACHE, "wb"))
    return nodes, uniq


OSM_NODES, OSM_WAYS = _load_osm()
ROAD_W = {"motorway": 40, "trunk": 40, "primary": 40, "secondary": 36, "tertiary": 32, "residential": 26, "unclassified": 24,
          "living_street": 20, "primary_link": 22, "secondary_link": 22, "tertiary_link": 22, "trunk_link": 22, "motorway_link": 24}
CASINO_ZONE = (-175, -180, 165, 410)             # x0 y0 x1 y1 true feet: the hand-built parcel (OSM buildings inside are skipped)
UX0, UY0, UX1, UY1 = -1060.0, SEG_Y0 - 40, 1060.0, SEG_Y1 + 40


def _pts(refs):
    return [OSM_NODES[r] for r in refs if r in OSM_NODES]


def _runs(pts):
    """Parts of a polyline that lie inside the segment's rectangle (whole segments only)."""
    out, cur = [], []
    for p in pts:
        if UX0 <= p[0] <= UX1 and UY0 <= p[1] <= UY1:
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def _inzone(x, y):
    return CASINO_ZONE[0] < x < CASINO_ZONE[2] and CASINO_ZONE[1] < y < CASINO_ZONE[3]


# ---------------------------------------------------------------------------------------------- Union Ave
def _chain(kind_x):
    """(y, x) samples of the Union carriageway ways whose mean x is on the west (-1) or east (+1) side."""
    cand = []
    for wid, tags, refs in OSM_WAYS:
        if "Union" in tags.get("name", "") and tags.get("highway") in ("primary", "trunk"):
            p = _pts(refs)
            if p:
                cand.append(p)
    allx = [q[0] for p in cand for q in p if -400 < q[1] < 13000]
    mid = (min(allx) + max(allx)) / 2 if allx else 200
    pts = sorted({(round(q[1], 1), q[0]) for p in cand if (sum(q[0] for q in p) / len(p) < mid) == (kind_x < 0) for q in p})
    ys = [a for a, b in pts]
    keep = [(a, b) for i, (a, b) in enumerate(pts) if i == 0 or a > pts[i - 1][0] + 0.5]
    return np.array([a for a, b in keep]), np.array([b for a, b in keep])


_wy, _wx = _chain(-1)
_ey, _ex = _chain(1)
_c0 = (np.interp(0.0, _wy, _wx) + np.interp(0.0, _ey, _ex)) / 2


def union_c(y):
    """Centre line x of the carriageway pair at y, nudged so it agrees with the hand-built casino cross-section (207.35 ft at y 0)."""
    return (np.interp(y, _wy, _wx) + np.interp(y, _ey, _ex)) / 2 + (207.35 - _c0)


HALF_SEP = 28.65                                   # carriageway centre to the middle of the median (measured at the casino)
LANE_W = 12.9
CW = 3 * LANE_W
Y_START = max(SEG_Y0, 500.0) if SEG_NAME == "goldenwest" else SEG_Y0
_ys = list(np.arange(Y_START, SEG_Y1 + 1, 20.0))
_C = np.array([union_c(y) for y in _ys])
for _ in range(6):                                                         # the two OSM ways wobble (different vertex spacing): smooth, 220 ft window
    _p = np.pad(_C, 5, mode="edge")
    _C = np.convolve(_p, np.ones(11) / 11, mode="valid")
if SEG_NAME == "goldenwest":                                               # blend into the hand-built section (207.35 ft) at the start
    _C = _C + (207.35 - _C[0]) * np.clip(1 - (np.array(_ys) - _ys[0]) / 400.0, 0, 1)
_C = list(_C)

# ---------------------------------------------------------------------------------------------- the underpass (E Truxtun Ave + the rail line)
# Photos 253-277: Union Ave drops into a concrete trench with blue-fenced retaining walls, passes under the Mojave Subdivision rail bridge
# (OSM bridge ways at y 9913-9961) and under the E Truxtun Ave bridge (y 10255-10315), and climbs out again before 17th St.
TRENCH = SEG_Y0 < 10100 < SEG_Y1
if TRENCH:
    TA, TB, TD, RAMP = 9700.0, 10530.0, 17.0, 150.0          # ramp starts / ends, depth, ramp length (true feet)
    _arr = np.array(_ys)
    _cat = float(np.interp(10100.0, _arr, np.array(_C)))
    _blend = np.clip(1 - np.maximum(np.maximum(TA - 100 - _arr, _arr - (TB + 100)), 0) / 100.0, 0, 1) * (
        (_arr > TA - 100) & (_arr < TB + 100))
    _C = list(np.array(_C) * (1 - _blend) + _cat * _blend)  # straight through the trench, blended in over 100 ft
    CUT = (_cat - 54.0, _cat + 54.0, TA, TB)                # x0 x1 y0 y1: ground and hull floor are cut out here (make_union.py)

    def zdepth(y):
        d = min(max((y - TA) / RAMP, 0.0), max((TB - y) / RAMP, 0.0), 1.0)
        return -TD * d
else:
    CUT = None


def _line(off):
    return [(c + off, y) for c, y in zip(_C, _ys)]


def _regions(pts):
    """Split a polyline into (in_trench, points) runs (one shared point between runs)."""
    if not TRENCH:
        return [(False, pts)]
    runs, cur, cur_t = [], [], None
    for p in pts:
        t = TA - 1 <= p[1] <= TB + 1
        if cur and t != cur_t:
            cur.append(p)
            runs.append((cur_t, cur))
            cur = [cur[-1]]
        else:
            cur.append(p)
        cur_t = t
    if len(cur) > 1:
        runs.append((cur_t, cur))
    return runs


def _ribbon(pts, width, tex, z, ext, side, group, trench_ok=True):
    for in_t, run in _regions(pts):
        if in_t:
            if not trench_ok:
                continue
            ribbon(run, width, tex, z=z, ext=0, side_tex=side, group=group, zprof=lambda x, y, z=z: z + zdepth(y), walls=1.6)
        else:
            ribbon(run, width, tex, z=z, ext=ext, side_tex=side, group=group)


def _strip(off, width, tex, z, side="bk_walk", trench_ok=True):
    _ribbon(_line(off), width, tex, z, 0.5, side, "detail", trench_ok)


def _dashes(off, tex="bk_wline", w=0.35):
    pts = _line(off)
    for i in range(0, len(pts) - 1, 2):
        seg = pts[i:i + 2]
        if TRENCH and TA - 22 <= seg[0][1] <= TB + 22:
            ribbon(seg, w, tex, z=ROADZ + 0.02, ext=0.0, group="illus", zprof=lambda x, y: ROADZ + 0.03 + zdepth(y), walls=0.05)
        else:
            ribbon(seg, w, tex, z=ROADZ + 0.02, ext=0.0, group="illus")


for side in (-1, 1):
    _strip(side * HALF_SEP, CW, "bk_road", ROADZ)
    _strip(side * (HALF_SEP + CW / 2 + 3.5), 6, "bk_walk", WALKZ, trench_ok=False)       # outer sidewalk (none in the trench)
    for k in (-1, 1):
        _dashes(side * HALF_SEP + k * LANE_W / 2 * 1.0)
_strip(0, HALF_SEP * 2 - CW, "gw_brick", WALKZ, side="bk_walk")                              # the red-brick median
for side in (-1, 1):
    _ribbon(_line(side * (HALF_SEP - CW / 2)), 0.5, "bk_yline", ROADZ + 0.02, 0.0, "bk_walk", "illus")
for i in range(0, len(_ys), 5):                                                              # palms on the sidewalks and a lamp on the median
    yy, cc = _ys[i], _C[i]
    if TRENCH and TA - 30 <= yy <= TB + 30:
        continue
    if i % 10 == 0:
        palm(cc - HALF_SEP - CW / 2 - 9, yy, h=24 + (i // 5) % 3 * 3)
    else:
        palm(cc + HALF_SEP + CW / 2 + 9, yy, h=24 + (i // 5) % 3 * 3)
    if i % 15 == 0:
        prop(cc - 0.3, yy - 0.3, 0, cc + 0.3, yy + 0.3, 30, "bk_steel")
        prop(cc - 9.5, yy - 0.3, 30, cc + 0.3, yy + 0.3, 30.6, "bk_steel")
        ent("light", cc - 8, yy, 28, light=180, _color="255 240 210")

# ---------------------------------------------------------------------------------------------- cross streets
_nroad = 0
for wid, tags, refs in OSM_WAYS:
    hw = tags.get("highway")
    nm = tags.get("name", "")
    if hw not in ROAD_W or ("Union" in nm and hw in ("primary", "trunk")) or tags.get("area") == "yes":
        continue
    for run in _runs(_pts(refs)):
        run = [p for p in run if not (CASINO_ZONE[0] < p[0] < CASINO_ZONE[2] and CASINO_ZONE[1] < p[1] < CASINO_ZONE[3] and False)]
        w = ROAD_W[hw]
        ribbon(resample(run, 40), w, "bk_road", z=ROADZ, ext=0.5, group="detail")
        if w >= 26:
            ribbon(resample(run, 40), 0.35, "bk_yline", z=ROADZ + 0.02, ext=0.0, group="illus")
        _nroad += 1

# ---------------------------------------------------------------------------------------------- traffic signals and street signs
# Union Ave signals (mast arms with 3 heads over the lanes, white stop bars and crosswalks) at the cross streets that are
# tertiary or bigger; every named cross street gets a green street-name blade (texture gs_<md5>, drawn by build_gw_textures.py).
import hashlib

JUNCTIONS = []                                              # (y, name, signalled)
for wid, tags, refs in OSM_WAYS:
    hw = tags.get("highway")
    nm = tags.get("name", "")
    if hw not in ROAD_W or ("Union" in nm and hw in ("primary", "trunk")) or tags.get("area") == "yes" or hw.endswith("_link"):
        continue
    P_ = _pts(refs)
    cand = []
    for (xa, ya), (xb, yb) in zip(P_, P_[1:]):
        da, db = xa - union_c(ya), xb - union_c(yb)
        if da * db < 0 and abs(da) < 500 and abs(db) < 500:
            cand.append(ya + (yb - ya) * da / (da - db))
    for xa, ya in (P_[0], P_[-1]):                          # T-junctions: the street ends at Union Ave (OSM stops at the carriageway)
        if abs(xa - union_c(ya)) < 80:
            cand.append(ya)
    for yi in cand:
        if True:
            if Y_START + 40 < yi < SEG_Y1 - 40 and not (TRENCH and TA - 50 < yi < TB + 50) and all(abs(yi - j[0]) > 60 for j in JUNCTIONS):
                JUNCTIONS.append((yi, nm, hw in ("primary", "secondary", "tertiary", "trunk")))
JUNCTIONS.sort()


def sign_tex(name):
    return "gs_" + hashlib.md5(name.encode()).hexdigest()[:10]


def _head(x, y, z, face):
    """One signal head hanging at (x, y) with its top at z; the lenses face north (face=1) or south (face=-1)."""
    prop(x - 0.6, y - 0.5, z - 3.2, x + 0.6, y + 0.5, z, "bk_steel")
    fy = y + face * 0.5
    for k, tex in enumerate(("bk_red", "bk_yline", "bk_lime")):
        zc = z - 0.6 - k * 1.0
        prop(x - 0.35, min(fy, fy + face * 0.15), zc - 0.35, x + 0.35, max(fy, fy + face * 0.15), zc + 0.35, tex)


def _blade(x0, x1, y, z0, z1, name):
    if name and sign_tex(name) in TEXSIZE:
        f = Fit(sign_tex(name))
        prop(x0, y - 0.15, z0, x1, y + 0.15, z1, "bk_steel", {"n": f, "s": f})


for yi, nm, sig in JUNCTIONS:
    cc = float(np.interp(yi, _ys, _C))
    for side, fc, dy in ((-1, 1, -24.0), (1, -1, 24.0)):              # west pole (southbound) south of the junction, east pole north of it
        px, py = cc + side * (HALF_SEP + CW / 2 + 5.0), yi + dy
        prop(px - 0.5, py - 0.5, 0, px + 0.5, py + 0.5, 19 if sig else 11.5, "bk_steel")
        if not sig:
            _blade(px - 3.5, px + 3.5, py, 9.0, 11.4, nm)
            continue
        ax = px - side * 40.0                                           # mast arm reaches over the carriageway
        prop(min(px, ax), py - 0.3, 18.0, max(px, ax), py + 0.3, 18.7, "bk_steel")
        for k in range(3):
            _head(px - side * (12.0 + k * 12.9), py, 18.0, fc)
        xa_, xb_ = sorted((px - side * 2.0, px - side * 9.5))
        _blade(xa_, xb_, py, 15.0, 17.6, nm)
        sx, by = cc + side * HALF_SEP, yi - dy                          # stop bar and crosswalk on this carriageway's approach
        box(sx - CW / 2, by - 0.8, ROADZ + 0.02, sx + CW / 2, by + 0.8, ROADZ + 0.05, "bk_wline", group="illus")
        for k in range(14):
            kx = sx - CW / 2 + 1.5 + k * (CW - 3) / 13
            box(kx - 0.5, by - dy * 0.14 - 4.0, ROADZ + 0.02, kx + 0.5, by - dy * 0.14 + 4.0, ROADZ + 0.05, "bk_wline", group="illus")
    if sig:
        ent("light", cc, yi, 24, light=150, _color="255 240 210")
print("junctions:", len(JUNCTIONS), "signalled:", sum(1 for j in JUNCTIONS if j[2]), [(round(j[0]), j[1], round(float(np.interp(j[0], _ys, _C)))) for j in JUNCTIONS])

# ---------------------------------------------------------------------------------------------- landmarks (gw_landmark_data.py)
exec(compile(open(os.path.join(HERE, "gw_landmark_data.py"), encoding="utf-8").read(), "gw_landmark_data.py", "exec"), globals())


def _lm_anchor(street, dy, side):
    y = STREET_Y[street] + dy
    if not (Y_START + 60 < y < SEG_Y1 - 60) or (TRENCH and TA - 60 < y < TB + 60):
        return None
    cc_ = float(np.interp(y, _ys, _C))
    return cc_, y, (1 if side == "E" else -1)


TINT_OF = {}                                                # OSM way id -> wall colour texture
for street, dy, side, colour in TINTS:
    an = _lm_anchor(street, dy, side)
    if not an:
        continue
    cc_, y_, sd_ = an
    best, bd = None, 1e9
    for wid, tags, refs in OSM_WAYS:
        if "building" not in tags or wid in TINT_OF:
            continue
        pts_ = _pts(refs)
        if len(pts_) < 4:
            continue
        cx_, cy_ = sum(q[0] for q in pts_[:-1]) / (len(pts_) - 1), sum(q[1] for q in pts_[:-1]) / (len(pts_) - 1)
        ar_ = abs(sum(pts_[i][0] * pts_[i + 1][1] - pts_[i + 1][0] * pts_[i][1] for i in range(len(pts_) - 1))) / 2
        if ar_ < 500 or (cx_ - cc_) * sd_ < 50 or abs(cy_ - y_) > 130 or _inzone(cx_, cy_):
            continue
        dd = math.hypot(cx_ - (cc_ + sd_ * 85), cy_ - y_)
        if dd < bd:
            best, bd = wid, dd
    if best:
        TINT_OF[best] = "gw_w_" + colour

# ---------------------------------------------------------------------------------------------- buildings
_BW = (("bk_stucco", 10), ("bk_hstucco", 10), ("bk_shopwall", 20), ("bk_110tan", 16), ("bk_unitwall", 20), ("bk_lmc", 20))
_nb = 0
for wid, tags, refs in OSM_WAYS:
    if "building" not in tags:
        continue
    pts = _pts(refs)
    if len(pts) < 4:
        continue
    cx, cy = sum(p[0] for p in pts[:-1]) / (len(pts) - 1), sum(p[1] for p in pts[:-1]) / (len(pts) - 1)
    if not (UX0 + 30 < cx < UX1 - 30 and UY0 + 30 < cy < UY1 - 30) or _inzone(cx, cy):
        continue
    if cy > UY1 - 40 or cy < UY0 + 40:
        continue
    area = abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1))) / 2
    if area < 150:
        continue
    k = int(wid) % len(_BW)
    try:
        h = float(tags["height"].split()[0]) * 3.28 if "height" in tags else (float(tags["building:levels"]) * 11 if "building:levels" in tags else 0)
    except ValueError:
        h = 0
    house = area < 2800
    if not h:
        h = 10 if house else (14 + (k % 3) * 3 if area < 14000 else 22)
    poly = [tuple(p) for p in pts[:-1]]
    try:
        for part in convex_parts(poly):
            prism(part, 0, h, "bk_roof", side=tspec(TINT_OF.get(wid) or (_BW[k][0] if not house else ("bk_stucco", "bk_hstucco", "bk_110tan")[k % 3]), _BW[k][1]), solid=True)
            if house:
                hiproof(part, h, ("bk_shingle", "bk_cpshingle", "bk_roof")[k % 3], eave=1.2, pitch=0.35)
    except Exception as e:                      # a footprint the convex split cannot handle: leave it out
        print("skipped building", wid, e)
        continue
    _nb += 1
print("route %d..%d: %d roads, %d buildings" % (SEG_Y0, SEG_Y1, _nroad, _nb))


def _lm_clear(x0, y0, x1, y1, z0=0.0, z1=40.0):
    lo, hi = (u(x0, OX), u(y0, OY), u(z0)), (u(x1, OX), u(y1, OY), u(z1))
    return not any(all(lo[i] < b_[i + 3] and hi[i] > b_[i] for i in range(3)) for b_ in SOLIDS)


def _lm_spot(cc_, sd_, y_, hw, hd, back):
    """x of a post (half-width hw along x, half-depth hd along y) behind the kerb; moves out until clear of buildings, or None."""
    for extra in (0, 8, 16, 26, 40):
        x_ = cc_ + sd_ * (HALF_SEP + CW / 2 + 6.5 + back + extra)
        if _lm_clear(x_ - hw, y_ - hd, x_ + hw, y_ + hd, 0.0, 12.0):
            return x_
    return None


_nlm = 0
for street, dy, side, sid, fw, fh, top, back in POLES:
    an = _lm_anchor(street, dy, side)
    if not an or ("gl_" + sid) not in TEXSIZE:
        continue
    cc_, y_, sd_ = an
    x_ = _lm_spot(cc_, sd_, y_, fw / 2 + 0.5, 0.8, back)
    if x_ is None:
        continue
    f_ = Fit("gl_" + sid)
    prop(x_ - 0.4, y_ - 0.4, 0, x_ + 0.4, y_ + 0.4, top - fh, "bk_steel")
    prop(x_ - fw / 2, y_ - 0.4, top - fh, x_ + fw / 2, y_ + 0.4, top, "bk_steel", {"n": f_, "s": f_})
    _nlm += 1
for street, dy, side, sid, top in BILLBOARDS:
    an = _lm_anchor(street, dy, side)
    if not an or ("gl_" + sid) not in TEXSIZE:
        continue
    cc_, y_, sd_ = an
    x_ = _lm_spot(cc_, sd_, y_, 13.0, 1.5, 14)
    if x_ is None:
        continue
    f_ = Fit("gl_" + sid)
    for px_ in (x_ - 8, x_ + 8):
        prop(px_ - 0.6, y_ - 0.6, 0, px_ + 0.6, y_ + 0.6, top - 10, "bk_steel")
    prop(x_ - 12, y_ - 0.5, top - 10, x_ + 12, y_ + 0.5, top, "bk_steel", {"n": f_, "s": f_})
    prop(x_ - 12, y_ - 1.2, top - 10.6, x_ + 12, y_ + 1.2, top - 10, "bk_steel")                  # catwalk
    _nlm += 1
for street, dy, side, band in CANOPIES:
    an = _lm_anchor(street, dy, side)
    if not an:
        continue
    cc_, y_, sd_ = an
    x_ = None
    for extra in (0, 12, 24, 40):
        xc = cc_ + sd_ * (HALF_SEP + CW / 2 + 28 + extra)
        if _lm_clear(xc - 15, y_ - 18, xc + 15, y_ + 18, 0.0, 17.0):
            x_ = xc
            break
    if x_ is None:
        continue
    for px_ in (x_ - 11, x_ + 11):
        for py_ in (y_ - 12, y_ + 12):
            prop(px_ - 0.7, py_ - 0.7, 0, px_ + 0.7, py_ + 0.7, 15.0, "bk_steel")
    box(x_ - 15, y_ - 18, 15.0, x_ + 15, y_ + 18, 17.0, "gw_w_white", {"n": "gw_w_" + band, "s": "gw_w_" + band, "e": "gw_w_" + band, "w": "gw_w_" + band}, group="detail")
    for px_ in (x_ - 7, x_ + 7):
        prop(px_ - 0.9, y_ - 1.2, 0, px_ + 0.9, y_ + 1.2, 3.0, "bk_steel")                      # pumps
    ent("light", x_, y_, 13, light=170, _color="255 245 220")
    _nlm += 1
print("landmarks placed:", _nlm, "tinted buildings:", len(TINT_OF))


if TRENCH:
    xL, xR, yA, yB = CUT
    DEEP = TD + 3
    for in_t, run in _regions(_line(0)):                                                   # a solid floor under everything between the walls (no gaps = no leak)
        if in_t:
            ribbon(run, xR - xL - 2.0, "bk_blockgr", z=-0.06, ext=0, side_tex="bk_blockgr", group="detail", zprof=lambda x, y: -0.06 + zdepth(y), walls=26.0)
    for x0_, x1_ in ((xL, xL + 1.0), (xR - 1.0, xR)):                                      # concrete liner of the retaining walls (the ground itself is 20 ft deep here)
        box(x0_, yA, -DEEP, x1_, yB, 0.0, "bk_blockgr", {"w": tspec("bk_blockgr", 12), "e": tspec("bk_blockgr", 12), "t": "bk_walk"})
    for fx_ in (xL - 0.4, xR + 0.4):                                                       # blue-painted fence along the top of the walls (photos 261-277)
        box(fx_ - 0.1, yA, 0.0, fx_ + 0.1, yB, 4.5, Fit("{chain", ((yB - yA) / 5.3, 4.5 / 5.3)), group="fence")
    # the E Truxtun Ave deck (OSM: two one-way carriageways at y 10270 and 10300, bridge x 121..337)
    box(xL, 10252, -3.2, xR, 10318, 0.0, "bk_blockgr", {"t": "bk_road"})
    for yy in (10252, 10316.6):
        box(xL, yy, 0.0, xR, yy + 1.4, 3.0, "bk_blockgr")                                    # concrete barriers
    box(xL, 10284.2, 0.0, xR, 10285.8, 0.5, "bk_walk")                                       # the median between the two carriageways
    # the Mojave Subdivision rail bridge (OSM bridge ways at y 9913-9961): ballast deck, two rails
    box(xL, 9906, -3.2, xR, 9968, 0.0, "bk_blockgr", {"t": "bk_gravel"})
    for x0_, x1_ in ((UX0, xL), (xR, UX1)):
        box(x0_, 9912, 0.0, x1_, 9962, 1.0, "bk_gravel")
    for rx0, rx1 in ((UX0, UX1),):
        for ry in (9930.0, 9944.0):
            box(rx0, ry - 0.3, 1.0, rx1, ry + 0.3, 1.5, "bk_steel")
    box(xL, 9912, 0.0, xR, 9913, 1.0, "bk_gravel")
    for yy in (9912, 9961):
        box(xL, yy, 0.0, xR, yy + 1.0, 1.6, "bk_blockgr")
    # lights under the bridges
    for lx_ in (xL + 14, (xL + xR) / 2, xR - 14):
        for ly_ in (9937, 10285, 10270, 10300):
            ent("light", lx_, ly_, -TD + 9, light=170, _color="255 240 215")
        for ly_ in (9800, 10100, 10420):
            ent("light", lx_, ly_, -TD + 12, light=150, _color="255 240 215")
    print("underpass: trench %d..%d ft, %d ft deep, walls at x %.0f / %.0f" % (TA, TB, TD, xL, xR))
