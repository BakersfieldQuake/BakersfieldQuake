"""One self-contained HTML page about bklan4: the top-down plan with the TVs, casino, launch pads, teleports and jetpacks
marked, a card per TV (where it is, what it faces, the clips it plays), the in-game screenshots of the check runs, and
the list of what the accuracy pass changed. Everything is embedded (base64), so the file can be opened anywhere.
usage: python build_bklan4_page.py   -> BakersfieldQuake/bklan4_overview.html"""
import base64
import html
import io
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import bks_mapio as mio  # noqa: E402

OX, OY, U = -110, 225, 12
PLAN = (-830, -1120, 1880, 800, 0.5)                      # as plan_b4.png was rendered
OUT = os.path.join(ROOT, "bklan4_overview.html")


def ft(o):
    return o[0] / U + OX, o[1] / U + OY, o[2] / U


def px(x, y):
    x0, y0, x1, y1, sc = PLAN
    return (x - x0) * sc, (y1 - y) * sc


def b64(im, q=82, maxw=1280):
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def img(path, q=82, maxw=1280):
    return b64(Image.open(path), q, maxw)


# ------------------------------------------------------------------------------------------------ entities
ents = mio.read_map(os.path.join(HERE, "out", "maps", "bklan4.map"))
tvs, pads, dests, tpads, jets, spawns, cars, vans, weapons = [], [], [], [], [], [], [], [], []
for e in ents:
    o = e.origin()
    if e.cls == "bk_tv":
        tvs.append((ft(o), int(e.kv.get("angle", 0)), float(e.kv.get("scale", 1))))
    elif e.cls == "info_teleport_destination":
        dests.append((e.kv.get("targetname"), ft(o)))
    elif e.cls == "item_armor2":
        jets.append(ft(o))
    elif e.cls == "info_player_deathmatch":
        spawns.append(ft(o))
    elif e.cls.startswith("misc_vehicle_van"):
        vans.append(ft(o))
    elif e.cls.startswith("misc_vehicle"):
        cars.append(ft(o))
    elif e.cls.startswith("weapon_"):
        weapons.append((e.cls, ft(o)))
    elif e.cls == "trigger_push" and e.brushes:
        b = e.brushes[0]
        c = ft(((b.lo[0] + b.hi[0]) / 2, (b.lo[1] + b.hi[1]) / 2, b.lo[2]))
        sp = float(e.kv.get("speed", 0))
        ang = [float(v) for v in e.kv.get("angles", "0 0 0").split()]
        pads.append((c, sp, ang))
    elif e.cls == "trigger_teleport" and e.brushes:
        b = e.brushes[0]
        tpads.append((e.kv.get("target"), ft(((b.lo[0] + b.hi[0]) / 2, (b.lo[1] + b.hi[1]) / 2, b.lo[2]))))
long_pads = [(c, sp, ang) for c, sp, ang in pads if sp > 150]      # the cross-map launch pads (the corner pads are ~ 100)

FACING = {0: "east", 90: "north", 180: "west", 270: "south"}


def tv_where(x, y):
    if x < -600:
        return "Golden West Casino: over the bar's back shelves (high-limit room)", "zb4_tv4_casino.png"
    if y > 150:
        return "Larry's warehouse (the 118/120 hall), north wall over the centre aisle", "zb4_tv1_warehouse.png"
    if x < -180:
        return "The 120A bedroom, on the dresser", "zb4_tv2_bedroom.png"
    return "The LAN lot, on 130A's west wall between two roll-ups", "zb4_tv3_lot.png"


# ------------------------------------------------------------------------------------------------ the plan with markers
plan = Image.open(os.path.join(HERE, "out", "plan_b4.png")).convert("RGB")
d = ImageDraw.Draw(plan)
try:
    F = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 15)
    F2 = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
except OSError:
    F = F2 = ImageFont.load_default()


def mark(x, y, r, fill, outline="black", label=None, shape="circle"):
    X, Y = px(x, y)
    if shape == "circle":
        d.ellipse([X - r, Y - r, X + r, Y + r], fill=fill, outline=outline, width=2)
    elif shape == "square":
        d.rectangle([X - r, Y - r, X + r, Y + r], fill=fill, outline=outline, width=2)
    else:
        d.polygon([(X, Y - r), (X + r, Y + r), (X - r, Y + r)], fill=fill, outline=outline)
    if label:
        d.text((X + r + 3, Y - 8), label, font=F, fill="white", stroke_width=3, stroke_fill="black")


for (x, y, z) in spawns:
    mark(x, y, 3, (255, 255, 255), "black")
for (x, y, z) in cars:
    mark(x, y, 2, (255, 120, 0), (120, 50, 0))
for (x, y, z) in vans:
    mark(x, y, 4, (255, 255, 255), (0, 0, 0), shape="square")
for (x, y, z) in jets:
    mark(x, y, 6, (255, 220, 0), "black", shape="triangle")
for (c, sp, ang) in long_pads:
    mark(c[0], c[1], 7, (210, 70, 255), "white")
for (t, (x, y, z)) in tpads:
    mark(x, y, 6, (60, 230, 255), "black", shape="square")
for (t, (x, y, z)) in dests:
    mark(x, y, 5, (0, 120, 160), "white", shape="square")
for k, ((x, y, z), a, s) in enumerate(tvs):
    mark(x, y, 9, (255, 40, 40), "white", "TV %d" % (k + 1))
# area labels
for name, x, y in (("GOLDEN WEST CASINO", -800, -330), ("LARRY'S WAREHOUSE", -300, 200), ("ORCOM HALL", 330, 360), ("BAKERSFIELD SIGN", 800, 60),
                   ("1608 MANNING ST", 1600, -530), ("AMBERTON PARK", 900, -1000), ("S UNION AVE", -480, -620), ("E 21ST ST", 200, -40)):
    X, Y = px(x, y)
    d.text((X, Y), name, font=F, fill=(255, 255, 160), stroke_width=3, stroke_fill="black")
# legend
leg = [("TV (bk_tv)", (255, 40, 40), "circle"), ("launch pad (cross-map)", (210, 70, 255), "circle"), ("teleport pad", (60, 230, 255), "square"),
       ("teleport arrival", (0, 120, 160), "square"), ("jetpack (yellow armour)", (255, 220, 0), "triangle"), ("spawn", (255, 255, 255), "circle"),
       ("exploding car", (255, 120, 0), "circle"), ("drivable van", (255, 255, 255), "square")]
d.rectangle([plan.width - 232, 8, plan.width - 8, 8 + 20 * len(leg) + 10], fill=(0, 0, 0, 200), outline="white")
for i, (t, col, sh) in enumerate(leg):
    X, Y = plan.width - 218, 20 + 20 * i
    if sh == "circle":
        d.ellipse([X - 6, Y - 6, X + 6, Y + 6], fill=col, outline="white")
    elif sh == "square":
        d.rectangle([X - 6, Y - 6, X + 6, Y + 6], fill=col, outline="white")
    else:
        d.polygon([(X, Y - 7), (X + 7, Y + 6), (X - 7, Y + 6)], fill=col, outline="white")
    d.text((X + 14, Y - 8), t, font=F2, fill="white")
plan_b64 = b64(plan, 88, 1400)

# ------------------------------------------------------------------------------------------------ the clips
CLIPS = ["grok-video-685f8cf0 (1)", "grok-video-18f4eae4", "grok-video-4251788a (3)", "character_showcase", "grok-video-20a5f777 (1)",
         "0217779837418310...", "grok-video-80a3dc6d", "grok-video-0454d933"]
strips = []
for c in range(8):
    frames = sorted(f for f in os.listdir(os.path.join(ROOT, "progs", "bktv")) if f.startswith("v%d_" % c))
    pick = [frames[int(i * (len(frames) - 1) / 5)] for i in range(6)] if frames else []
    strip = Image.new("RGB", (160 * 6, 120), (0, 0, 0))
    for i, f in enumerate(pick):
        im = Image.open(os.path.join(ROOT, "progs", "bktv", f)).convert("RGB")
        # the frames are baked dark (x0.55) for the engine's 2.5x scene brightness: lift them back for the page
        im = im.point(lambda v: min(255, int(v / 0.55)))
        strip.paste(im.resize((160, 120)), (160 * i, 0))
    strips.append((CLIPS[c], len(frames), b64(strip, 80, 960)))

# ------------------------------------------------------------------------------------------------ screenshots
SHOTS = [
    ("The casino", [("zb4_01_entrance.png", "The entrance plaza and portico from the south lot"), ("zb4_02_lobby.png", "The lobby and cage"),
                    ("zb4_03_cardroom.png", "The card room (rocket launcher on the long aisle)"), ("zb4_04_bar_tv.png", "The high-limit room and bar (TV 4 over the shelves)"),
                    ("zb4_05_union_casino.png", "S Union Ave in front of the casino: the pink supercar drives past, a drivable van waits"),
                    ("zb4_07_hub.png", "The north lot: teleport pads to Larry's and the office roof"), ("zb4_06_westroof.png", "On the west wing roof, where the jetpack is"),
                    ("zb4_23_casino_air.png", "From the air over Union Ave"), ("zb4_08_union_south.png", "Union Ave from E 21st, looking south into the new box"),
                    ("zb4_20_landed.png", "Where the Larry's launch pad lands you: the casino's Union Ave sidewalk")]),
    ("The Bakersfield Sign", [("zb4_sign_w.png", "The arch from the west along Sillect Ave; the letters now stand plumb and the band is 2.6 ft deep"),
                              ("zb4_sign_under.png", "Under the arch, looking up at the band"), ("zb4_sign_e.png", "From the east, the Crystal Palace behind"),
                              ("zb4_10_sign_hedge.png", "The south tower: SPEED LIMIT 35 at the curb west of it, the low hedge on its west face, the tan impost at 7 ft")]),
    ("Larry's warehouse", [("zb4_11_larry_front.png", "The front: white fascia, the ORTIZ Auto Body banner, the A-frame mast over 120B"),
                           ("zb4_12_larry_120b.png", "The 120B storefront panels, Larry's pylon, the launch pad to the Sign"),
                           ("zb4_13_lot_tents.png", "Inside the gate: the blue canopy over the pickups, the white pyramid tent, the 130A wall TV (TV 3)"),
                           ("zb4_14_lot_fence.png", "The lot's north end: block wall to the post, the open chain-link gate, chain-link with barbed wire, the walk-out gap")]),
    ("1608 Manning St", [("zb4_15_manning.png", "The house from the street: the van, the magnolia, the pickup back in the driveway, the 1608 sign on the lawn, the palm by the drive"),
                         ("zb4_16_clubview.png", "Club View Drive, the cross street that was missing, with the corner planter and palms")]),
    ("Amberton Park", [("zb4_17_park.png", "The gabled shelter, the swing set turned north-south, the tot-lot canopy, pines and cypresses"),
                       ("zb4_18_park2.png", "From the north-east: the play structure in the west lobe, the launch pad to Larry's")]),
]


def shot(f, cap):
    p = os.path.join(ROOT, f)
    if not os.path.exists(p):
        return ""
    return '<figure><img src="%s" loading="lazy"><figcaption>%s</figcaption></figure>' % (img(p, 80, 1100), html.escape(cap))


# ------------------------------------------------------------------------------------------------ page
tv_cards = []
for k, ((x, y, z), a, s) in enumerate(tvs):
    where, shotf = tv_where(x, y)
    sp = os.path.join(ROOT, shotf)
    im = '<img src="%s" loading="lazy">' % img(sp, 78, 900) if os.path.exists(sp) else '<div class="noshot">no screenshot yet</div>'
    tv_cards.append('''<div class="card"><h3>TV %d</h3><p><b>%s</b></p>
<p>at x %.0f, y %.0f, %.1f ft up &middot; faces %s &middot; screen %.1f x %.1f ft (scale %.1f)</p>%s</div>''' % (
        k + 1, html.escape(where), x, y, z, FACING.get(a, "%d deg" % a), 4 * s, 3 * s, s, im))

acc = {
    "Larry's warehouse (118/120 E 21st, the LAN lot, 130A)": [
        "Black steel-mesh security cage with a barrel roof just inside the fence at the lot's street end (Street View yaw45/yaw90).",
        "The two canopy tents moved to where the aerial has them: the blue one 16 ft square by the gate (x -123, y 34), the white one with a pyramid roof at (-117, 64).",
        "The shopping cart sitting on the fascia over the BATERIAS sign.",
        "The roof mast is an A-frame over the 120B piers, not a pole over the 120A door; two HVAC boxes at the east end of the roof.",
        "The lot's north end as in the 2001 tape: block wall only to x -122, a steel post, an open chain-link gate, chain-link with barbed wire; the walk-out gap from the last review kept.",
        "The 2026 front is bright white: white stucco and fascia on the street face (new textures, same sizes).",
        "120B storefront rhythm: blue | glass | door | red | white | blue | glass | red | door | white | blue.",
        "The lime ORTIZ Auto Body banner on the fascia; B45's E 21st face white with a round monogram and a dark open bay (no red band)."],
    "The Bakersfield Sign": [
        "BAKERSFIELD letters stand plumb (the old texture leaned each glyph to the arc); band 2.6 ft deep instead of 1.6.",
        "SPEED LIMIT 35 moved from 30 ft east of the south tower to the curb just west of it, facing eastbound traffic.",
        "South tower hedge: 2.4 ft tall, along the west face and the south end (was 3.8 ft on the outer face).",
        "Tan impost moulding round every base face at 7.0-7.7 ft; soft green lights on both faces (the sign is green-lit at night).",
        "Low planting at the north tower's base corners and the grey utility cabinet east of it."],
    "1608 Manning St": [
        "The light-blue pickup and the grey Fit are back in the driveway with the lime Charger (the earlier car-thinning had dropped them).",
        "The big magnolia at the lot's street corner (34 ft) and the tall sycamore by the walk; the palm moved from the north wing's windows to between the walk and the driveway.",
        "Club View Drive (the cross street at y -800) added east of Manning with sidewalks, a blade sign and the corner planter with two palms.",
        "The '1608' kerb sign out of the driveway onto the lawn; side-yard wood fence and gate flush with the garage, hedge along the drive; yellow hydrant.",
        "White sectional garage door on the neighbour whose footprint has a straight street wall; white stucco instead of grey panels on the block.",
        "White motorhome in 1600's driveway (aerials); the sedan parked across the School House Rd mouth removed; Italian cypresses opposite; no centre line in the residential stretch."],
    "Amberton Park": [
        "The 'restroom' building was invented: GIS says picnic-table pad. Replaced by a table.",
        "Play structure moved to the west lobe, the swing set (long axis north-south) and a tot-lot canopy to the north-east lobe; the light pole out of the swing pit.",
        "The play area is a concrete plaza with two sand pits, not all sand.",
        "Shelter: 24 x 40 ft gabled brown-shingle roof on six posts with one table, a grill and a bin (was a 32 ft square white one).",
        "The red backflow pad moved to its real spot by Placer Ct (with the irrigation cabinet); one table per pad instead of two.",
        "Benches and drinking fountains at their GIS positions; the invented path from School House Rd dropped, a walk from the shelter to the cul-de-sac added.",
        "Back fences along the south and south-east edges; AMBERTON PARK monument sign on School House Rd; park trees re-kinded to cedars/pines and two cypresses."],
}
acc_html = "".join("<h3>%s</h3><ul>%s</ul>" % (html.escape(k), "".join("<li>%s</li>" % html.escape(v) for v in vs)) for k, vs in acc.items())

n_long = len(long_pads)
page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>bklan4 overview</title>
<style>
:root{--bg:#15171c;--fg:#e8e6df;--mut:#a9a69c;--acc:#f0c040;--card:#1f2229;--line:#2f333c}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 Segoe UI,Arial,sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 60px}
h1{font-size:32px;margin:0 0 4px}h2{font-size:22px;margin:40px 0 12px;color:var(--acc);border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:17px;margin:18px 0 6px}p{margin:6px 0}.mut{color:var(--mut)}
img{max-width:100%%;height:auto;display:block;border-radius:6px}
figure{margin:0 0 14px}figcaption{font-size:14px;color:var(--mut);margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.card h3{margin-top:0}.noshot{height:120px;display:flex;align-items:center;justify-content:center;color:var(--mut);border:1px dashed var(--line);border-radius:6px}
.strip{margin:10px 0}.strip p{margin:2px 0;font-size:14px}
code{background:#0e1013;padding:1px 6px;border-radius:4px;font-size:14px}
ul{margin:4px 0 10px 20px}li{margin:2px 0}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 14px}
.stat b{display:block;font-size:22px;color:var(--acc)}
</style></head><body><main>
<h1>bklan4</h1>
<p class="mut">bklan3 + Golden West Casino + the accuracy pass on Larry's warehouse, the Bakersfield Sign, 1608 Manning St and Amberton Park. Built 2026-10-31 night. Play: <code>+deathmatch 1 +map bklan4</code>.</p>
<div class="stats"><div class="stat"><b>%d</b>TVs</div><div class="stat"><b>%d</b>spawns</div><div class="stat"><b>%d</b>jetpacks</div><div class="stat"><b>%d</b>jump pads</div>
<div class="stat"><b>%d</b>cross-map launch pads</div><div class="stat"><b>%d</b>teleport pads</div><div class="stat"><b>%d</b>exploding cars</div><div class="stat"><b>%d</b>drivable vans</div></div>

<h2>The map</h2>
<p>North is up; 1 pixel is about 2.9 ft. The casino is the new box at the bottom left, where S Union Ave leaves E 21st and runs south (2 miles in reality, 400 ft here). Everything from bklan3 is where it was.</p>
<figure><img src="%s"><figcaption>Top-down plan of bklan4 (brush bounding boxes, roofs hidden above 40 ft) with the gameplay entities marked.</figcaption></figure>

<h2>The TVs</h2>
<p>Four <code>bk_tv</code> entities. Each plays the eight clips from Downloads at low volume, cut into 62-frame chunks (one shader and skin each), a new screen entity every 6.2 s so the per-client animation clock stays in step. TVs 1-3 are bklan3's, TV 4 is new in the casino.</p>
<div class="grid">%s</div>
<h3>What they play</h3>
<p class="mut">Six frames from each clip (160 x 120, 10 fps in game; the stored frames are darkened for the engine and lifted here).</p>
%s

<h2>Golden West Casino</h2>
<p>Cut as-is from the <code>goldenwest</code> map (the photo-measured parcel: rubble-stone walls, tile roofs, the turret, the pylon, the card room with its tables, the lobby and cage, the high-limit bar, the portico and bronze horse) and placed on the west side of Union Ave facing south onto its own lot, as in reality. Its 19 parked cars explode like the rest of the map's.</p>
<ul><li><b>Items:</b> rocket launcher on the card room's long aisle, the map's second lightning gun at the bar (two cell packs), grenade launcher among the cars of the south lot, super shotgun at the entrance, nailgun in the north lot, green armour in the lobby.</li>
<li><b>Roofs:</b> a jump pad in the north lot throws you onto the west wing's flat roof, where the jetpack and rockets are; a pad in the south lot onto the lobby roof (cells, health).</li>
<li><b>Getting there and back:</b> a violet launch pad in Larry's lot flings you to Union Ave by the casino's north lot; one on the casino's north sidewalk flings you back to Larry's. The north lot is a teleport hub (to Larry's warehouse and the office roof by the Sign); the warehouse and the office roof each got a pad to the casino.</li>
<li><b>Vehicles:</b> the pink supercar and the Podracer now drive down Union Ave to the casino and back; the biplane also lands in the strip east of Union; a drivable van in the north lot and one in the east strip.</li>
<li><b>Spawns:</b> 10 at the casino; 7 of the 12 that were crammed into the ORCOM hall removed; new ones at Manning St, by the Sign and on the south blocks; a jetpack added on Manning St.</li></ul>
<div class="grid">%s</div>

<h2>Accuracy pass</h2>
<p class="mut">Four audits against the Street View gallery, the 2001 tape, the review videos (Google Maps / Street View frames) and the city GIS. Each change is a layer on top of bklan3 (<code>make_bklan_v5.py</code>); nothing in bklan/bklan2/bklan3 was touched.</p>
%s
<div class="grid">%s</div>

<h2>Not done / to check in game</h2>
<ul><li>The sign towers' stucco reads olive in game where the photo is pale cream (texture-level, uncertain).</li>
<li>120B's glass panels have no mullions; the lot-side roll-ups keep their 12 ft size (the tape shows ~10 ft).</li>
<li>Crystal Palace was not re-audited.</li>
<li>Only one Manning St neighbour passed the straight-street-wall test for a garage door.</li>
<li>Both casino launch pads land 5-10 %% long, so they are aimed short; measured after the re-aim: Larry's lot &rarr; (-528, -400) on the casino's Union Ave sidewalk, casino &rarr; (-170, 23) on E 21st at Larry's gate.</li></ul>
<p class="mut">Files: <code>source/mm_tools/make_bklan_v5.py</code>, <code>build_v5_textures.py</code>, <code>build_bklan4.sh</code>; test scripts <code>zz_bk4*.cfg</code>; this page from <code>build_bklan4_page.py</code>.</p>
</main></body></html>''' % (
    len(tvs), len(spawns), len(jets), len(pads), n_long, len(tpads), len(cars), len(vans), plan_b64, "".join(tv_cards),
    "".join('<div class="strip"><p><b>Clip %d</b> &middot; %s &middot; %d frames</p><img src="%s" loading="lazy"></div>' % (i + 1, html.escape(n), nf, s)
            for i, (n, nf, s) in enumerate(strips)),
    "".join(shot(f, c) for f, c in SHOTS[0][1]),
    acc_html,
    "".join(shot(f, c) for sec in SHOTS[1:] for f, c in sec[1]))
open(OUT, "w", encoding="utf-8").write(page)
print("wrote", OUT, "%.1f MB" % (os.path.getsize(OUT) / 1e6), "| tvs", [(round(x), round(y), a, s) for (x, y, z), a, s in tvs])
