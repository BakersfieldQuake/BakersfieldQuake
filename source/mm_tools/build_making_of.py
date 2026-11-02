"""Builds "The Making Of Larry's Warehouse": one self-contained HTML page (images embedded as JPEG data URIs) with every
image used to make bklan, in the order the work went: the 2001 tape, the frames studied, finding the building, the
Street View gallery pictures used, the textures, the SimReady props, the in-game passes and the accuracy audit.
python build_making_of.py <scratch dir> <tool-results dir> <gallery dir> <simready dir>
Writes BakersfieldQuake/making_of_larrys_warehouse.html."""
import base64
import glob
import html
import io
import os
import sys

from PIL import Image

SCR, TOOLRES, GAL, SR = sys.argv[1:5]
MOD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(MOD, "making_of_larrys_warehouse.html")
count = [0]


def uri(path, maxw=1280, q=80):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (32, 32, 32))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.getchannel("A"))
        im = bg
    im = im.convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=q)
    count[0] += 1
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def fig(path, cap, maxw=1280, cls=""):
    if not os.path.exists(path):
        return ""
    return '<figure class="%s"><img loading="lazy" src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (
        cls, uri(path, maxw), html.escape(os.path.basename(path)), cap)


def grid(items, cols=2):
    return '<div class="grid g%d">%s</div>' % (cols, "".join(items))


S = os.path.join(SCR, "bklan")
parts = []
add = parts.append

add("""<header><p class="kicker">BakersfieldQuake &middot; map <code>bklan</code></p>
<h1>The Making Of Larry's Warehouse</h1>
<p class="lede">A 53-minute, 320&times;240 home video of a 2001 LAN party (B-LAN, unit 130A of the warehouse at
118 E 21st St, Bakersfield), 100 Street View and aerial photos, and 17 NVIDIA SimReady props, turned into a Quake
deathmatch map. These are the images that went into it, in the order the work went.</p></header>
<nav><a href="#tape">1 The tape</a><a href="#frames">2 Frames studied</a><a href="#place">3 Finding the building</a>
<a href="#street">4 Street View</a><a href="#tex">5 Textures</a><a href="#props">6 SimReady props</a>
<a href="#passes">7 In-game passes</a><a href="#audit">8 Accuracy audit</a><a href="#final">9 The map</a>
<a href="#credits">Credits</a></nav>""")

# 1 the tape
sheets = sorted(glob.glob(os.path.join(S, "sheets", "sheet_*.jpg")))
add('<section id="tape"><h2>1 &nbsp;The tape</h2><p><code>bklan.wmv</code>: 3,174 seconds, 320&times;240, recorded in '
    '2001, captured to WMV in 2004. One frame a second came out of it (3,175 stills), and every second one went onto '
    'a contact sheet: 53 sheets of 30, each tile stamped with its time. Four agents read a quarter each and listed '
    'what every frame shows of the building. The useful building footage is 0&ndash;150 s (daylight), '
    '1,620&ndash;2,330 s and 2,400&ndash;3,000 s (night); the rest is faces, screens, a drive, and a house at the '
    'end.</p>')
add("<details open><summary>Contact sheets 0&ndash;9</summary>" + grid(
    [fig(p, "Sheet %d &middot; %d:%02d&ndash;%d:%02d" % (i, i, 0, i, 58), 1100) for i, p in enumerate(sheets[:10])]) + "</details>")
add("<details><summary>Contact sheets 10&ndash;52 (the rest of the tape)</summary>" + grid(
    [fig(p, "Sheet %d &middot; %d:00&ndash;%d:58" % (i + 10, i + 10, i + 10), 1100) for i, p in enumerate(sheets[10:])]) + "</details></section>")

# 2 frames studied
add('<section id="frames"><h2>2 &nbsp;Frames studied</h2><p>The frames that settled the layout, upscaled 2&times;. '
    'Daylight from the first minutes; the rest at night, some in the camera\'s green night mode.</p>')
add(grid([
    fig(os.path.join(S, "m_a.jpg"), "Daylight, 116&ndash;150 s: the back wall and its door, the duct drop, the strip light, the "
        "drinks table by the door, the &ldquo;MONITOR&rdquo; box"),
    fig(os.path.join(S, "m_b.jpg"), "Night, 2,451&ndash;2,865 s: looking in from the lot, the box by the roll-up, the floor, "
        "the side tables"),
    fig(os.path.join(S, "m_c.jpg"), "Night, 1,622&ndash;2,256 s: the whole hall from the roll-up, the front corner with duct "
        "and heater, the back door, the long empty table row, the storefront door outside"),
], 1))
add("<h3>Gridded frames used to cut the photo textures</h3><p>Each frame at 3&times; with a 20-pixel grid, so crops "
    "could be read off in the original 320&times;240 coordinates.</p>")
add(grid([fig(os.path.join(S, "g%d.jpg" % i), cap) for i, cap in (
    (1, "1,916 s wall + table laminate &middot; 1,622 s roll-up slats + white door"),
    (2, "2,483 s floor &middot; 84 s the breaker panel with its cover off"),
    (3, "42 s the lot and the units across it &middot; 122 s CRT screen, beige plastic, the monitor box"),
    (4, "2,162 s the ceiling &middot; 1,952 s the painted sky wall in the back room"),
    (5, "1,738 s the back door &middot; 64 s the painted block outside"),
    (6, "1,334 s the B-LAN sign &middot; 1,347 s the &ldquo;130 A&rdquo; plywood door &middot; 66 s the salvage yard "
        "&middot; 2,052 s the storefront"),
    (7, "20 s and 94 s, daylight floor"))], 2) + "</section>")

# 3 finding the building
add('<section id="place"><h2>3 &nbsp;Finding the building</h2><p>The tape shows the party unit\'s roll-up opening '
    'onto a lot that ends in a block wall with a salvage yard behind it. On the aerial, only the lot east of the middle '
    'building ends that way, so unit 130A is on that building\'s east side, facing LMC Paint Supply. Sizes came from '
    'Google\'s own scale bar: the building is about 74 &times; 147 ft.</p>')
SHOTS = [("1793349898398", "Zoom 19: the three long buildings north of E 21st St"),
         ("1793349913497", "Zoom 21: the west lot and the middle building's roof"),
         ("1793349927155", "The pin for 118 E 21st St; scale bar read off the page: 10 m = 84 px"),
         ("1793349965667", "Zoom 21 on the pin: measuring the middle building's width (about 23 m)"),
         ("1793350006395", "Street View at the pin, looking north: white stucco front, 120A, the gated lot"),
         ("1793350014991-d4etpm", "Looking west along the front"), ("1793350014991-qzw0v9", "Looking east along the front")]
shots = [(glob.glob(os.path.join(TOOLRES, "mcp-Claude_Browser-blob-%s*.jpg" % k)), c) for k, c in SHOTS]
add(grid([fig(p[0], c) for p, c in shots if p], 3))
add(grid([fig(os.path.join(S, "ag.jpg"), "The close aerial with a 50-pixel grid, used to measure the three buildings and "
                                         "the two lots"),
          fig(os.path.join(GAL, "aerial-z20-close-sat.jpg"), "Aerial, zoom 20 (from the gallery)")], 2) + "</section>")

# 4 street view
used = ["sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45.", "sv-front-115e21st-pano-J7Kbb9uJL5YiN38_3wZi6g-yaw45",
        "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw180", "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw225",
        "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw135", "sv-east-217e21st-pano-SXPieXYETR2XBRFy0NGVhA-yaw270",
        "sv-east-217e21st-pano-SXPieXYETR2XBRFy0NGVhA-yaw315", "sv-west-119e21st-pano-dIfw9VXDm_euY2m8tJ2RrA-yaw90",
        "sv-front-115e21st-pano-J7Kbb9uJL5YiN38_3wZi6g-yaw0", "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw90",
        "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw0", "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45-pitch25"]
notes = {"yaw45.": "The front, the hero shot: the tall blank parapet, BATERIAS $55, the black door, 120A, 120B and the "
                   "red/blue panels. Most of the front textures are cut from this one.",
         "yaw180": "Across the road: the breeze-block wall &ldquo;121 E. 21st&rdquo;, the dirt lot (the backdrop card behind "
                   "the lattice wall)",
         "SXPieXYETR2XBRFy0NGVhA-yaw270": "LMC's corrugated wall with blue trim, the blue door; the road-west backdrop",
         "dIfw9VXDm_euY2m8tJ2RrA-yaw90": "Looking east down E 21st: the road-east backdrop"}
items = []
for u_ in used:
    p = [f for f in glob.glob(os.path.join(GAL, "*.jpg")) if os.path.basename(f).startswith(u_)]
    if p:
        n = next((v for k, v in notes.items() if k in u_), "Street View, Feb 2026")
        items.append(fig(p[0], "<b>%s</b><br>%s" % (html.escape(os.path.basename(p[0])[:60]), n), 1024))
add('<section id="street"><h2>4 &nbsp;Street View (Feb 2026)</h2><p>The 12 photos from your gallery that the street '
    'side was built from. The tape never shows the street front, so this side is 2026, not 2001.</p>' + grid(items, 2))
add(grid([fig(os.path.join(S, "sv45.jpg"), "The hero shot gridded for cutting textures"),
          fig(os.path.join(S, "bdgrid.jpg"), "Gridded backdrop sources: across the road, road west, road east")], 1) + "</section>")

# 5 textures
tex = sorted(glob.glob(os.path.join(MOD, "textures", "*.png")))
add('<section id="tex"><h2>5 &nbsp;Textures</h2><p>65 textures. The photo ones are cut from the tape or the Street '
    'View photos, tiled with a two-pass cross-fade and darkened for the mod\'s ~2&times; scene brightness. The props '
    'and the lines on the road are flat colours sampled from the footage. <code>{</code>-names are see-through '
    'fences; <code>_glow</code> are the lit parts.</p>')
add(grid([fig(os.path.join(S, "texsheet.jpg"), "First pass, all textures"),
          fig(os.path.join(S, "tiles.jpg"), "Tiling check, 2&times;2 each: wall, floor, road, sidewalk, stucco, mural, duct, dirt")], 2))
add('<div class="grid g8">' + "".join(fig(p, html.escape(os.path.basename(p)[:-4]), 256, "small") for p in tex) + "</div>")
sky = sorted(glob.glob(os.path.join(MOD, "gfx", "env", "bklan_*.png")))
add("<h3>The overcast skybox</h3>" + '<div class="grid g6">' + "".join(fig(p, os.path.basename(p)[:-4], 256, "small") for p in sky) + "</div></section>")

# 6 simready
add('<section id="props"><h2>6 &nbsp;SimReady props</h2><p>All 2,677 assets in nvidia/simready-assets were scanned; '
    '114 likely matches were checked by thumbnail, 37 shortlisted, and 17 matched to things seen on the tape were '
    'converted: decimated in Blender, written as MD3 with their colour maps, and placed with the mod\'s '
    '<code>misc_model</code>. The cable bundle was dropped after it rendered as shards.</p>')
add(fig(os.path.join(MOD, "source", "mm_tools", "simready_picks.jpg"), "The shortlist, grouped by where each would go"))
add("<details><summary>The scan: 114 candidate thumbnails</summary>" + grid(
    [fig(p, "Scan sheet %d" % i) for i, p in enumerate(sorted(glob.glob(os.path.join(SR, "sheet*.jpg"))))], 1) + "</details>")
usedp = ["hvac_vent_system_straight_a01", "hvac_vent_system_corner_a01", "climate_heater_electricBox_a01",
         "chair_office_fabric_manager_a01", "warehouse_chair_office_amf_black_a01", "climate_shopFan_pedestal_a01",
         "fireExtinguisher_abc_a03", "trashCan_office_beige_a03", "food_beverage_bottledDrink_a01", "food_beverage_can_b01",
         "dishware_cup_paper_a01", "box_cardboard_large_b01", "equipment_cord_reel_electric_a01", "drum_steel_a02",
         "computer_keyboard_a01", "lighting_taskLight_suspendedLinearBench_a01", "electrical_cable_a01"]
add("<h3>The 17 converted</h3>" + '<div class="grid g6">' + "".join(
    fig(os.path.join(SR, "thumbs", a + ".png"), a, 256, "small") for a in usedp) + "</div>")
add(grid([fig(os.path.join(S, "props1.jpg"), "First placement: the cable came out as black shards and the bottles "
                                              "ghost-white (glass imported with the wrong texture)")], 1) + "</section>")

# 7 passes
add('<section id="passes"><h2>7 &nbsp;In-game passes</h2><p>Every test ran unattended: build, launch DarkPlaces, '
    'screenshot, quit.</p>')
add(grid([
    fig(os.path.join(S, "shots0.jpg"), "Pass 1, random spawns: the hall works, the sky is static, outside is blown out"),
    fig(os.path.join(S, "shots1.jpg"), "Pass 1, outside: lots, LMC, crate stairs, the salvage backdrop"),
    fig(os.path.join(S, "shots2.jpg"), "Pass 2: softer sun; scripted turns didn't aim"),
    fig(os.path.join(S, "shots3.jpg"), "Pass 3, fixed spots: facade, hall, back room, roof, lots"),
    fig(os.path.join(S, "shots4.jpg"), "Pass 4: still the scrolling-sky arcs"),
    fig(os.path.join(S, "sky.jpg"), "Sky probe: it was the mod's 2&times; brightness and a skybox name typo"),
    fig(os.path.join(S, "shots6.jpg"), "Before the skybox fix"),
    fig(os.path.join(S, "shots7.jpg"), "After: overcast skybox"),
], 2) + "</section>")

# 8 audit
add('<section id="audit"><h2>8 &nbsp;Accuracy audit</h2><p>A second pass over the tape against the map. What changed: '
    'the strip lights run parallel to the back wall (122, 2,024 s); the joists run from the roll-up wall to the back '
    '(2,162 s); the &ldquo;pendant light&rdquo; is really a galvanized duct drop with a flared diffuser (138, 150 s); '
    'the roll-up sits about 8 ft open in the night footage (1,622 s); the south row was full of PCs earlier in the '
    'night (1,026, 1,104 s); a tall wooden podium stands at the island (2,020 s); the office box is about 10 ft with a '
    'dark green board (1,622 s); the extinguishers stand on a table (2,653 s); and the building across the lot is '
    'painted block with roll-ups every ~20 ft and man doors between (40, 42 s), not the 2026 corrugated siding. '
    'Checked and kept: the box by the roll-up is an office, not a restroom (2,713&ndash;2,717 s are too murky to show a '
    'toilet).</p>')
add(grid([fig(os.path.join(S, "audit1.jpg"), "Orientation frames: lights, duct, joists, the box, the roll-up"),
          fig(os.path.join(S, "audit2.jpg"), "The rows along the walls, the neon rack, the duct close up"),
          fig(os.path.join(S, "audit3.jpg"), "The restroom question, the extinguishers, the lot across the way"),
          fig(os.path.join(S, "audit_after.jpg"), "After the fixes"),
          fig(os.path.join(S, "audit_after2.jpg"), "Lights too bright at 400"),
          fig(os.path.join(S, "audit_after3.jpg"), "Settled at 290: the white-walled hall of 2,020 and 2,024 s")], 2) + "</section>")

# 9 final
caps = {"01_street": "E 21st St, where single-player starts", "02_front": "The front from across the road, south-west",
        "03_eastlot": "The east lot from the gate, the canopy", "04_lanfacade": "Unit 130A from the lot: the roll-up "
        "run down to 8 ft, the glass door, the B-LAN sign", "05_lanin": "The LAN hall from the roll-up",
        "06_lanback": "From the back wall toward the roll-up", "07_drinks": "The drinks table: 2-litre sodas, cups",
        "08_backroom": "The back room with the painted sky wall", "09_storage": "The storage room",
        "10_store120a": "120A, the battery shop (guessed inside)", "11_autoshop": "The auto shop (guessed inside)",
        "12_unit130c": "130C, storage (guessed inside)", "13_roof": "The roof: AC units, the mast",
        "14_westlot": "The west lot from its gate", "15_salvage": "The block wall and chain-link at the end of the east lot"}
add('<section id="final"><h2>9 &nbsp;The map</h2><p>Final in-game views. Load it with <code>map bklan</code>.</p>' + grid(
    [fig(p, caps.get(os.path.basename(p)[3:-4], "")) for p in sorted(glob.glob(os.path.join(MOD, "source", "mm_tools", "out", "views", "zv_*.png")))], 3) + "</section>")

add("""<section id="credits"><h2>Credits</h2><ul>
<li>The tape: <code>bklan.wmv</code>, B-LAN 2001, Bakersfield.</li>
<li>Street View and aerial imagery &copy; 2026 Google (Airbus, Maxar), from the user's gallery; reference only.</li>
<li>Props: NVIDIA SimReady Assets (huggingface.co/datasets/nvidia/simready-assets), CC-BY 4.0; decimated,
re-textured and converted to MD3 for this map.</li>
<li>Compiled with ericw-tools; runs in DarkPlaces.</li></ul></section>""")

page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Making Of Larry's Warehouse</title><style>
:root{--bg:#121212;--panel:#1c1c1c;--ink:#e9e6df;--muted:#a9a49a;--accent:#e8a33d;--line:#333}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,Arial,sans-serif}
header,section,nav{max-width:1180px;margin:0 auto;padding:0 16px}
header{padding-top:48px}.kicker{color:var(--accent);letter-spacing:.08em;text-transform:uppercase;font-size:13px;margin:0}
h1{font-size:clamp(30px,5vw,52px);line-height:1.05;margin:.2em 0 .3em}.lede{color:var(--muted);max-width:760px;font-size:18px}
nav{display:flex;flex-wrap:wrap;gap:6px 16px;padding-top:12px;padding-bottom:24px;border-bottom:1px solid var(--line)}
nav a{color:var(--ink);text-decoration:none;font-size:14px}nav a:hover{color:var(--accent)}
h2{font-size:26px;margin:56px 0 8px;border-bottom:2px solid var(--line);padding-bottom:6px}h3{font-size:18px;margin:28px 0 8px;color:var(--accent)}
section>p{color:var(--muted);max-width:820px}code{background:#2a2a2a;padding:1px 5px;border-radius:4px;font-size:.9em}
.grid{display:grid;gap:14px;margin:14px 0}.g1{grid-template-columns:1fr}.g2{grid-template-columns:repeat(2,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}.g6{grid-template-columns:repeat(6,1fr)}.g8{grid-template-columns:repeat(8,1fr)}
@media(max-width:800px){.g2,.g3{grid-template-columns:1fr}.g6,.g8{grid-template-columns:repeat(3,1fr)}}
figure{margin:0;background:var(--panel);padding:8px;border-radius:8px}figure img{width:100%;height:auto;display:block;border-radius:4px;cursor:zoom-in}
figcaption{font-size:13px;color:var(--muted);margin-top:6px;line-height:1.4;overflow-wrap:anywhere}figure.small figcaption{font-size:11px}
details{margin:12px 0}summary{cursor:pointer;color:var(--accent);font-weight:600}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;align-items:center;justify-content:center;z-index:9;cursor:zoom-out}
#lb img{max-width:96vw;max-height:94vh}ul{color:var(--muted)}footer{height:60px}
</style></head><body>@@BODY@@<footer></footer><div id="lb"><img alt=""></div><script>
const lb=document.getElementById('lb'),li=lb.querySelector('img');
document.addEventListener('click',e=>{if(e.target.matches('figure img')){li.src=e.target.src;lb.style.display='flex'}else if(lb.contains(e.target)){lb.style.display='none'}});
document.addEventListener('keydown',e=>{if(e.key==='Escape')lb.style.display='none'});
</script></body></html>""".replace("@@BODY@@", "\n".join(parts))
open(OUT, "w", encoding="utf-8").write(page)
print("wrote", OUT, count[0], "images,", round(len(page) / 1e6, 1), "MB")
