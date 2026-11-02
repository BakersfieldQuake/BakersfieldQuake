"""Captures:
  1) 5-way Lighting Exploration comparison shots (Before Blown-Out vs Soft Daylight, Sunny Balanced, Warm Amber,
     and Cool Twilight Neon) from the EXACT aerial angle of the user's DarkPlaces screenshot!
  2) 12 curated 1280x720 WebGL views of compiled maps/bklan5.bsp + bklan5.lit (Padre Hotel 29-MD3 interiors &
     murals, Fox Theater, Daniel LAN videos/posters, 39 Wild Vehicles, and all 3 Harmless Roaming NPC packs).
  3) Builds:
       - out/bklan5_shots/bklan5_lighting_comparison.jpg  (side-by-side lighting exploration sheet)
       - out/bklan5_shots/bklan5_telegram_collage.jpg     (6-panel hero collage for Telegram)
       - bklan5_showcase.html                             (100% self-contained single-file HTML showcase)

Usage:
  python capture_and_build_bklan5_showcase.py
"""
import base64
import functools
import http.server
import io
import json
import os
import socketserver
import threading
import time

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", ".."))
WEB_DIR = os.path.join(HERE, "out", "web", "warehouse5")
SHOT_DIR = os.path.join(HERE, "out", "bklan5_shots")
PRESET_SUMMARY = os.path.join(HERE, "out", "lighting_presets", "summary.json")
OUT_HTML = os.path.join(MOD, "bklan5_showcase.html")
HERO_JPG = os.path.join(SHOT_DIR, "bklan5_telegram_collage.jpg")
LIGHT_JPG = os.path.join(SHOT_DIR, "bklan5_lighting_comparison.jpg")

# Exact aerial camera matching the user's DarkPlaces screenshot looking NE across Downtown toward Fox & AT&T:
AERIAL_CAM = (-245.0, -1045.0, 128.0, 44.0, -18.0, 0.25)

LIGHT_PRESET_ORDER = [
    ("before_blownout", "Before: Old Blown-Out (Sun 300 + Sky 140)", "Clipped #FFFFFF roofs/walls, chalky pale asphalt & harsh 4.3:1 dark shadows"),
    ("soft_daylight",   "Preset A: Soft Diffused Daylight (Installed Default)", "Sun 38 + Sky 62 + Min 26 + 9° penumbra — 1.35:1 gentle contrast, 0% roof blowout!"),
    ("sunny_balanced",  "Preset B: Balanced Sunny Bakersfield", "Sun 54 + Sky 54 + Min 21 — crisp 1.55:1 sunny architectural relief, 0% roof blowout"),
    ("warm_amber",      "Preset C: Warm Late-Afternoon Amber", "Warm golden-amber sun (48 @ -38°) + cool sky dome — warm facades, soft shadows"),
    ("twilight_neon",   "Preset D: Cool Early-Dusk / Neon Pop", "Muted cool twilight sky (Sun 24 + Sky 46) — Fox Marquee, Padre windows & LAN halls pop!"),
]

# 12 curated viewpoints under the calibrated Soft Daylight default:
SHOTS = [
    (
        "aerial_downtown_fixed",
        "Downtown Aerial Overview — Zero Roof Blowout, Crisp Asphalt & Soft Shadows",
        "Calibrated Lighting",
        "Same aerial vantage over Downtown Bakersfield after calibrating bklan5 for DarkPlaces 4x overbright + v_glslgamma_2d 1: "
        "medium-grey gravel roofs, dark charcoal asphalt, legible crosswalks, and soft 1.35:1 sky-dome shadows.",
        -245.0, -1045.0, 128.0, 44.0, -18.0, 0.25,
    ),
    (
        "fox_marquee_npcs",
        "Fox Theater 20th & H — Marquee, Green-Suit Wheelman, Flamingo Fiend & V8 GT",
        "Fox + Harmless NPCs",
        "Historic 1930 Fox Theater corner with natural cream Spanish stucco (no white clipping), harmless shootable Green-Suit Wheelman "
        "cruising 20th & H, The Flamingo Fiend on the plaza, 1930 HOPE street clock, and parked 5.0L V8 Muscle Car.",
        26.0, -756.0, 7.2, 134.0, 4.0, 0.25,
    ),
    (
        "padre_18th_front",
        "The Padre Hotel (1702 18th St) — Farmacy Pitchfork Sign, V8 GT & Bike Rack",
        "Padre Hotel Exterior",
        "Updated 8-story Padre Hotel facade along 18th St featuring the alpha-cutout {farm_sign pitchfork blade sign, Farmacy patio, "
        "rooftop neon scaffold, green MD3 bicycle rack, and parked 5.0L V8 Supercharged Muscle Car.",
        -120.0, -1402.0, 5.5, 82.0, 14.0, 0.4,
    ),
    (
        "padre_grand_lobby",
        "Padre Hotel Grand Lobby — Gold Drum Chandeliers, Cowgirl Mural & Club Chairs",
        "Padre Hotel Lobby (MD3)",
        "Inside The Padre Hotel's updated Grand Lobby: custom pad_mural cowgirl & oil-derricks mural behind the fluted check-in desk, "
        "glowing two-tier gold drum chandeliers (pad_chand_drum), basketweave marble floor, and 3D club chairs.",
        -113.5, -1322.0, 5.2, 90.0, 2.0, 0.5,
    ),
    (
        "padre_brimstone_bar",
        "Padre Hotel Brimstone Bar — 3D Pool Table, Leather/Red Sofas & Bar TVs",
        "Padre Brimstone Bar (MD3)",
        "Brimstone Bar & Lounge populated with custom 3D MD3 furniture: pad_pooltable billiards table, tufted leather & red sofas, "
        "yellow barstools, glowing blue bar back, and pad_tv screens (with the 24-Hr Basement Gym directly underneath!).",
        -84.0, -1332.0, 5.2, 42.0, 2.0, 0.6,
    ),
    (
        "padre_clover_ballroom",
        "Padre Clover 1 & 2 Ballroom — Fringe Chandeliers & Round Banquet Sets",
        "Padre Ballroom & Suites",
        "Across the west courtyard inside the Clover Ballroom wing: custom 3D fringe chandeliers (pad_chand_fringe), dressed round "
        "banquet table sets (pad_banquet_set), striped ballroom carpet, and arched banquet bays.",
        -238.0, -1318.0, 5.2, 22.0, -2.0, 0.7,
    ),
    (
        "warehouse_daniel_south",
        "Larry's Warehouse (118/120) — SE LAN Party Bay, Daniel TV & 360° LAN Station",
        "Warehouse LAN Party",
        "Inside Larry's Warehouse SE LAN bay: back-to-back 16-ft tournament island + south LAN row with glowing Q3A/CS 1.5/Win98 CRTs, "
        "modded PC towers, live Daniel bk_tv + posters, and 360° LAN Station Daniel.",
        -151.5, 48.5, 6.2, 222.0, -9.0, 1.1,
    ),
    (
        "lan_130a_hall",
        "Unit 130A Main B-LAN Hall — 3D CRT Rows, Modded Towers & Daniel Video TV",
        "Unit 130A LAN Party",
        "Inside the 2001 Unit 130A LAN party hall: explodable 3D CRT monitors (Q3A, CS 1.5, Win98/Winamp, GameSpy), ATX & UV Chieftec "
        "towers, rolling/folding chairs, wall-mounted Daniel bk_tv (Clip 11: CCC!), and eyeball QuickCam on the center podium.",
        -82.5, 169.5, 6.2, 342.0, -7.0, 2.2,
    ),
    (
        "lan_courtyard",
        "Larry's LAN Courtyard — Entrance Daniel TV, Posters, Flamingo Fiend & Wild Cars",
        "Courtyard + Robeguy",
        "Courtyard between 118/120 Warehouse and Unit 130A: outdoor Daniel bk_tv (Justin Berry's Webcam), framed courtyard posters, "
        "harmless shootable Flamingo Fiend (robeguy), 5.0L V8 Muscle Car, and 6.7TD Heavy-Duty Dually Truck.",
        -102.0, 154.0, 5.2, 168.0, 2.0, 0.35,
    ),
    (
        "orcom_hall",
        "ORCOM Connect Banquet LAN Hall — 370+ Explodable 3D LAN Props & Daniel TV",
        "ORCOM LAN Party",
        "Sonora St ORCOM Connect LAN hall: convention rows of burgundy banquet chairs, 8-ft folding tables, animated Q3A/CS/Win98 CRTs, "
        "check-in L-counter & dedicated server desk, plus north-wall Daniel bk_tv and Computer Renaissance banner.",
        426.0, 319.5, 6.4, 162.0, -7.0, 1.6,
    ),
    (
        "e21_bus_dually_wheelman",
        "E 21st St Outside Larry's — School Bus 42, 6.7TD Dually, V8 GT & Wheelman",
        "Wild Vehicles + Wheelman",
        "Looking along E 21st St in front of Larry's Warehouse & Celebrity Bodyworks: Type-C Yellow School Bus ('BAKERSFIELD UNIFIED • BUS 42'), "
        "6.7TD Heavy-Duty Dually Truck, 5.0L V8 Muscle Car, and harmless Green-Suit Wheelman cruising past.",
        -128.0, -5.5, 5.6, 22.0, -1.0, 0.15,
    ),
    (
        "casino_david_squad",
        "Golden West Casino Plaza — Harmless David Ojeda Fleeing the 3 Pregnant Ladies",
        "David + Pregnant Squad",
        "Outside Golden West Casino's North Porte-Cochere: harmless, shootable David Ojeda clutching his money bag & spinning slots "
        "while all 3 pregnant women chase him around the plaza alongside a parked School Bus & 6.7TD Dually.",
        -566.0, -568.0, 4.8, 205.0, -1.0, 0.2,
    ),
]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def b64_jpeg(im: Image.Image, quality: int = 84) -> str:
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def b64_png(path: str, max_dim: int = 0) -> str:
    im = Image.open(path)
    if max_dim > 0 and max(im.size) > max_dim:
        im.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def capture_all():
    os.makedirs(SHOT_DIR, exist_ok=True)
    handler = functools.partial(QuietHandler, directory=WEB_DIR)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()

    preset_shots = {}
    captured = {}
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    try:
        with sync_playwright() as p:
            launch_kw = {"headless": True, "args": ["--use-gl=angle", "--enable-webgl", "--ignore-gpu-blocklist"]}
            if os.path.isfile(chrome_exe):
                launch_kw["executable_path"] = chrome_exe
            browser = p.chromium.launch(**launch_kw)
            page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
            page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle")
            page.wait_for_function("window.__assetsReady === true && typeof window.__jumpTo === 'function'", timeout=35000)
            time.sleep(0.6)

            # 1) Capture all 5 lighting presets at the exact aerial viewpoint:
            ax, ay, az, ayaw, apitch, afsec = AERIAL_CAM
            page.evaluate(f"window.__jumpTo({ax}, {ay}, {az}, {ayaw}, {apitch}, {afsec}, true)")
            for pkey, _, _ in LIGHT_PRESET_ORDER:
                page.evaluate(f"window.__setPreset('{pkey}')")
                time.sleep(0.35)
                im = Image.open(io.BytesIO(page.screenshot(type="png"))).convert("RGB")
                im.save(os.path.join(SHOT_DIR, f"preset_{pkey}.jpg"), quality=90)
                preset_shots[pkey] = im
                print(f"  captured lighting preset [{pkey}]")

            # Restore default soft_daylight preset for all 12 map tour shots:
            page.evaluate("window.__setPreset('soft_daylight')")
            time.sleep(0.25)

            for sid, title, badge, desc, x, y, z, yaw, pitch, fsec in SHOTS:
                page.evaluate(f"window.__jumpTo({x}, {y}, {z}, {yaw}, {pitch}, {fsec}, true)")
                time.sleep(0.28)
                out_p = os.path.join(SHOT_DIR, f"{sid}.jpg")
                im = Image.open(io.BytesIO(page.screenshot(type="png"))).convert("RGB")
                im.save(out_p, quality=90)
                captured[sid] = im
                print(f"  captured {sid}: {im.size}")
            browser.close()
    finally:
        httpd.shutdown()
    return preset_shots, captured


def build_lighting_sheet(preset_shots: dict):
    cw, ch = 620, 349
    # 2x2 of Before + Presets A/B/D (plus Preset C in row 3 or 5-panel layout: let's do 3x2 with stats!)
    canvas = Image.new("RGB", (cw * 2 + 24, ch * 3 + 74), (11, 15, 23))
    dr = ImageDraw.Draw(canvas)
    try:
        f_hdr = ImageFont.truetype("arialbd.ttf", 21)
        f_lbl = ImageFont.truetype("arialbd.ttf", 14)
    except OSError:
        f_hdr = f_lbl = ImageFont.load_default()
    dr.text((16, 14), "bklan5 LIGHTING EXPLORATION — BEFORE (BLOWN-OUT) VS. 4 CALIBRATED PRESETS", fill=(250, 204, 21), font=f_hdr)

    summary = json.load(open(PRESET_SUMMARY, encoding="utf-8")) if os.path.isfile(PRESET_SUMMARY) else {}
    panels = list(LIGHT_PRESET_ORDER) + [("fox_street_ref", "Street-Level Check (Preset A: Fox 20th & H + Padre)", "Natural cream stucco, dark asphalt & 0% blowout")]
    for idx, (pkey, title, _) in enumerate(panels):
        r, c = divmod(idx, 2)
        x0 = 8 + c * (cw + 8)
        y0 = 50 + r * (ch + 8)
        src_im = preset_shots[pkey] if pkey in preset_shots else Image.open(os.path.join(SHOT_DIR, "fox_marquee_npcs.jpg"))
        canvas.paste(src_im.resize((cw, ch), Image.LANCZOS), (x0, y0))
        dr.rectangle([x0, y0 + ch - 30, x0 + cw, y0 + ch], fill=(9, 13, 21))
        stat_s = ""
        if pkey in summary:
            p50, p90 = summary[pkey]["pcts"][2], summary[pkey]["pcts"][4]
            stat_s = f"  [p50={p50:.0f}, p90={p90:.0f}, clip={summary[pkey]['stucco_clip_pct']}%]"
        col = (248, 113, 113) if pkey == "before_blownout" else ((74, 222, 128) if pkey == "soft_daylight" else (241, 245, 249))
        dr.text((x0 + 8, y0 + ch - 23), title + stat_s, fill=col, font=f_lbl)
        dr.rectangle([x0, y0, x0 + cw - 1, y0 + ch - 1], outline=(71, 85, 105), width=2)
    canvas.save(LIGHT_JPG, quality=90)
    print("Built lighting comparison sheet:", LIGHT_JPG)


def build_telegram_collage(captured: dict):
    picks = [
        ("fox_marquee_npcs",       "1. Fox 20th & H: Soft Daylight + Wheelman + Flamingo + V8 GT"),
        ("padre_grand_lobby",      "2. Padre Hotel Lobby: Gold Chandeliers, Cowgirl Mural & MD3s"),
        ("padre_brimstone_bar",    "3. Padre Brimstone Bar: 3D Pool Table, Leather Sofas & TVs"),
        ("warehouse_daniel_south", "4. Larry's Warehouse: Daniel Videos, Posters & LAN Station"),
        ("lan_courtyard",          "5. LAN Courtyard: Daniel TV, Flamingo Fiend & Wild Vehicles"),
        ("casino_david_squad",     "6. Golden West Casino: David Ojeda + 3 Chasing Pregnant Women"),
    ]
    cw, ch = 640, 360
    canvas = Image.new("RGB", (cw * 2 + 24, ch * 3 + 80), (13, 17, 24))
    dr = ImageDraw.Draw(canvas)
    try:
        f_hdr = ImageFont.truetype("arialbd.ttf", 21)
        f_lbl = ImageFont.truetype("arialbd.ttf", 14)
    except OSError:
        f_hdr = f_lbl = ImageFont.load_default()
    dr.text((16, 14), "BAKERSFIELD QUAKE — bklan5 MEGA UPDATE (PADRE HOTEL MD3S, DANIEL LAN, CARS, NPCS & SOFT LIGHT)", fill=(250, 204, 21), font=f_hdr)
    for idx, (sid, label) in enumerate(picks):
        r, c = divmod(idx, 2)
        x0 = 8 + c * (cw + 8)
        y0 = 50 + r * (ch + 8)
        im = captured[sid].resize((cw, ch), Image.LANCZOS)
        canvas.paste(im, (x0, y0))
        dr.rectangle([x0, y0 + ch - 28, x0 + cw, y0 + ch], fill=(10, 14, 22))
        dr.text((x0 + 10, y0 + ch - 22), label, fill=(241, 245, 249), font=f_lbl)
        dr.rectangle([x0, y0, x0 + cw - 1, y0 + ch - 1], outline=(71, 85, 105), width=2)
    canvas.save(HERO_JPG, quality=90)
    print("Built Telegram collage:", HERO_JPG)


def build_html(preset_shots: dict, captured: dict):
    summary = json.load(open(PRESET_SUMMARY, encoding="utf-8")) if os.path.isfile(PRESET_SUMMARY) else {}

    preset_js_data = []
    for pkey, title, desc in LIGHT_PRESET_ORDER:
        im = preset_shots[pkey].resize((1120, 630), Image.LANCZOS)
        st = summary.get(pkey, {"pcts": [0, 0, 0, 0, 0, 0], "stucco_clip_pct": 0})
        preset_js_data.append({
            "key": pkey,
            "title": title,
            "desc": desc,
            "stats": f"Lightmap median (p50): {st['pcts'][2]:.0f}/255 · Sunlit roof (p90): {st['pcts'][4]:.0f}/255 · Stucco white-clip: {st['stucco_clip_pct']}%",
            "src": b64_jpeg(im, 84),
        })

    shot_cards_data = []
    for sid, title, badge, desc, x, y, z, yaw, pitch, _ in SHOTS:
        im = captured[sid].resize((960, 540), Image.LANCZOS)
        shot_cards_data.append({
            "id": sid,
            "title": title,
            "badge": badge,
            "desc": desc,
            "coords": f"({x:.0f}, {y:.0f}, {z:.1f} ft) · yaw {yaw:.0f}°",
            "src": b64_jpeg(im, 82),
        })

    spr_atlases = {}
    for k in ("greensuit", "robeguy", "david", "daniel_lan"):
        spr_atlases[k] = b64_png(os.path.join(WEB_DIR, "tex", f"spr_{k}.png"))

    poster_b64 = {}
    for pnm in ("dan_4am", "dan_shaaa", "dan_webcam", "dan_ccc", "pad_mural", "pad_dandy", "pad_rococo", "fx_tapestry"):
        im_p = Image.open(os.path.join(MOD, "textures", f"{pnm}.png")).convert("RGB")
        im_p.thumbnail((360, 360), Image.LANCZOS)
        poster_b64[pnm] = b64_jpeg(im_p, 85)

    plan_im = Image.open(os.path.join(HERE, "out", "plan_b5.png")).convert("RGB")
    plan_im.thumbnail((1140, 980), Image.LANCZOS)
    plan_b64 = b64_jpeg(plan_im, 82)

    cards_html = []
    for i, sc in enumerate(shot_cards_data):
        cards_html.append(f"""
        <article class="shot-card" onclick="openLightbox({i})">
          <div class="shot-img-wrap">
            <img src="{sc['src']}" alt="{sc['title']}" loading="lazy">
            <span class="shot-badge">{sc['badge']}</span>
            <span class="shot-coords">{sc['coords']}</span>
          </div>
          <div class="shot-body">
            <h3>{sc['title']}</h3>
            <p>{sc['desc']}</p>
          </div>
        </article>""")

    preset_btns = []
    for idx, pd in enumerate(preset_js_data):
        act = " active" if pd["key"] == "soft_daylight" else ""
        short_lbl = pd["title"].split(":")[0] if ":" in pd["title"] else pd["title"]
        if pd["key"] == "soft_daylight":
            short_lbl = "★ Preset A: Soft Daylight (Default)"
        elif pd["key"] == "before_blownout":
            short_lbl = "Before (Blown-Out)"
        elif pd["key"] == "sunny_balanced":
            short_lbl = "Preset B: Sunny Balanced"
        elif pd["key"] == "warm_amber":
            short_lbl = "Preset C: Warm Amber"
        elif pd["key"] == "twilight_neon":
            short_lbl = "Preset D: Cool Twilight"
        preset_btns.append(f'<button class="tab-btn{act}" onclick="pickPreset({idx}, this)">{short_lbl}</button>')

    default_p_idx = 1
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BakersfieldQuake — bklan5 Mega Update Showcase</title>
<style>
  :root {{
    --bg: #0b0f17;
    --panel: #131a27;
    --panel2: #1a2436;
    --border: #2a3954;
    --ink: #f1f5f9;
    --muted: #94a3b8;
    --gold: #facc15;
    --green: #4ade80;
    --cyan: #38bdf8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: radial-gradient(circle at 20% 0%, #172238 0%, var(--bg) 55%);
    color: var(--ink);
    font: 15px/1.55 system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  }}
  .wrap {{ max-width: 1340px; margin: 0 auto; padding: 28px 20px 64px; }}
  header.hero {{
    background: linear-gradient(135deg, rgba(26,36,54,.95), rgba(15,21,33,.96));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px 30px;
    margin-bottom: 28px;
    box-shadow: 0 18px 45px rgba(0,0,0,.45);
  }}
  .eyebrow {{ color: var(--gold); font-weight: 700; font-size: 12px; letter-spacing: .12em; text-transform: uppercase; }}
  h1 {{ margin: 6px 0 10px; font-size: clamp(25px, 3.2vw, 38px); line-height: 1.16; }}
  .hero p {{ margin: 0 0 18px; color: var(--muted); max-width: 980px; font-size: 15.5px; }}
  .cta-row {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 22px; }}
  .btn {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 16px; border-radius: 9px; font-weight: 700; text-decoration: none;
    border: 1px solid var(--border); color: var(--ink); background: var(--panel2);
    transition: transform .12s ease, border-color .12s ease; font-size: 14px;
  }}
  .btn:hover {{ transform: translateY(-1px); border-color: var(--gold); }}
  .btn.primary {{ background: linear-gradient(135deg, #facc15, #f59e0b); color: #111827; border: 0; }}
  .stats {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;
  }}
  .stat {{
    background: rgba(11,15,23,.65); border: 1px solid var(--border); border-radius: 11px; padding: 13px 15px;
  }}
  .stat b {{ display: block; font-size: 20px; color: var(--gold); }}
  .stat span {{ font-size: 13px; color: var(--muted); }}
  h2.sec-title {{
    margin: 36px 0 14px; font-size: 22px; display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid var(--border); padding-bottom: 10px;
  }}
  .light-box {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 20px;
  }}
  .light-stage {{
    position: relative; aspect-ratio: 16/9; max-height: 580px; margin: 0 auto; border-radius: 11px; overflow: hidden;
    border: 1px solid var(--border); background: #070a10;
  }}
  .light-stage img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .light-meta {{
    display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; margin-top: 12px;
    background: rgba(11,15,23,.7); padding: 12px 15px; border-radius: 9px; border: 1px solid var(--border);
  }}
  .grid-shots {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 18px;
  }}
  @media (max-width: 640px) {{ .grid-shots {{ grid-template-columns: 1fr; }} }}
  .shot-card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 13px; overflow: hidden;
    cursor: pointer; transition: transform .15s ease, border-color .15s ease;
  }}
  .shot-card:hover {{ transform: translateY(-3px); border-color: var(--cyan); }}
  .shot-img-wrap {{ position: relative; aspect-ratio: 16/9; background: #070a10; }}
  .shot-img-wrap img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .shot-badge {{
    position: absolute; top: 10px; left: 10px; background: rgba(11,15,23,.86);
    border: 1px solid rgba(250,204,21,.5); color: var(--gold); font-size: 11px; font-weight: 700;
    padding: 4px 9px; border-radius: 999px; letter-spacing: .04em; text-transform: uppercase;
  }}
  .shot-coords {{
    position: absolute; bottom: 10px; right: 10px; background: rgba(11,15,23,.84);
    color: #cbd5e1; font: 12px/1 monospace; padding: 5px 8px; border-radius: 6px;
  }}
  .shot-body {{ padding: 14px 16px 16px; }}
  .shot-body h3 {{ margin: 0 0 6px; font-size: 16.5px; color: #f8fafc; }}
  .shot-body p {{ margin: 0; font-size: 13.5px; color: var(--muted); }}
  .studio-grid {{
    display: grid; grid-template-columns: 1fr 1.15fr; gap: 20px; align-items: stretch;
  }}
  @media (max-width: 900px) {{ .studio-grid {{ grid-template-columns: 1fr; }} }}
  .card-box {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 20px;
  }}
  .tab-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }}
  .tab-btn {{
    background: var(--panel2); color: var(--ink); border: 1px solid var(--border);
    padding: 8px 13px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 13px;
  }}
  .tab-btn.active {{ background: var(--cyan); color: #082f49; border-color: var(--cyan); }}
  #sprCanvas {{
    width: 100%; max-width: 400px; aspect-ratio: 1/1; display: block; margin: 0 auto;
    background: radial-gradient(circle, #22304a 0%, #0d1320 75%);
    border-radius: 12px; border: 1px solid var(--border); cursor: grab;
  }}
  .poster-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
  @media (max-width: 640px) {{ .poster-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  .poster-item {{
    background: #0d1320; border: 1px solid var(--border); border-radius: 10px; padding: 8px; text-align: center;
  }}
  .poster-item img {{ width: 100%; aspect-ratio: 1/1; object-fit: cover; border-radius: 6px; margin-bottom: 5px; }}
  .poster-item b {{ font-size: 12px; color: var(--gold); display: block; }}
  .poster-item span {{ font-size: 11px; color: var(--muted); }}
  .plan-wrap {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 18px; text-align: center;
  }}
  .plan-wrap img {{ max-width: 100%; height: auto; border-radius: 10px; border: 1px solid var(--border); }}
  #lightbox {{
    position: fixed; inset: 0; background: rgba(4,7,12,.92); display: none;
    align-items: center; justify-content: center; z-index: 999; padding: 20px;
  }}
  #lightbox.open {{ display: flex; }}
  #lightbox img {{ max-width: 95vw; max-height: 86vh; border-radius: 10px; border: 1px solid var(--border); }}
  #lbCaption {{ position: fixed; bottom: 18px; left: 20px; right: 20px; text-align: center; color: #e2e8f0; font-weight: 600; }}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="eyebrow">BakersfieldQuake · maps/bklan5.bsp + progs.dat Mega Update</div>
    <h1>bklan5 — Updated Padre Hotel (All 29 MD3s &amp; Murals), Daniel LAN Videos, Wild Vehicles, Harmless NPCs &amp; Calibrated Soft Lighting</h1>
    <p>
      Complete update to <code>maps/bklan5.bsp</code>, <code>maps/bklan5.lit</code>, and <code>progs.dat</code>:
      integrates the full updated 8-story Padre Hotel &amp; Fox Theater (all 29 custom <code>progs/fox/*.md3</code> models, 163 placed instances, 102 interior collision clips, murals &amp; <code>{{farm_sign</code>),
      all 4 Daniel meme videos &amp; 15 framed posters across Larry's Warehouse &amp; LAN halls, 39 shootable Wild Vehicles,
      3 harmless shootable roaming NPC packs, plus calibrated non-blown-out DarkPlaces lighting &amp; windowed 2D Quake HUD gamma fix (<code>v_glslgamma_2d 1</code>).
    </p>
    <div class="cta-row">
      <a class="btn primary" href="warehouse5/">&#9654; Walk Around bklan5 in 3D Browser Viewer (with Live Lighting Switcher!)</a>
      <a class="btn" href="fox_showcase.html">Fox &amp; Padre 29-MD3 Museum</a>
      <a class="btn" href="wild-vehicles/">Wild Vehicles Studio</a>
      <a class="btn" href="greensuit-wheelman/">Green-Suit Wheelman</a>
      <a class="btn" href="robeguy_monster_sprite.html">Flamingo Fiend</a>
    </div>
    <div class="stats">
      <div class="stat"><b>29/29 Padre &amp; Fox MD3s</b><span>163 smooth-shaded MD3 props + 102 interior clips + Cowgirl/Dandelion/Rococo murals &amp; {{farm_sign</span></div>
      <div class="stat"><b>6 Daniel TVs + 15 Posters</b><span>Clips 8–11 cycling across Larry's Warehouse, Courtyard, 130A &amp; ORCOM + 360° LAN Station</span></div>
      <div class="stat"><b>39 Wild Vehicles + 3 NPCs</b><span>7 School Buses, 14 Duallys, 18 V8 GTs + harmless shootable Wheelman, Flamingo Fiend &amp; David Squad</span></div>
      <div class="stat"><b>Zero-Blowout Soft Light + HUD</b><span>p50 dropped 153 &rarr; ~36 (0% roof clip, 1.35:1 soft shadows) + <code>v_glslgamma_2d 1</code> bright Quake HUD</span></div>
    </div>
  </header>

  <h2 class="sec-title">1. Interactive Lighting Exploration — Before (Blown-Out) vs. 4 Calibrated Presets</h2>
  <div class="light-box">
    <div class="tab-row">
      {''.join(preset_btns)}
    </div>
    <div class="light-stage">
      <img id="presetImg" src="{preset_js_data[default_p_idx]['src']}" alt="Lighting preset comparison">
    </div>
    <div class="light-meta">
      <div>
        <strong id="presetTitle" style="color:var(--gold);display:block">{preset_js_data[default_p_idx]['title']}</strong>
        <span id="presetDesc" style="color:var(--muted);font-size:13.5px">{preset_js_data[default_p_idx]['desc']}</span>
      </div>
      <div id="presetStats" style="font:12.5px/1.6 monospace;color:#cbd5e1;align-self:center">{preset_js_data[default_p_idx]['stats']}</div>
    </div>
  </div>

  <h2 class="sec-title">2. Live Compiled <code>bklan5.bsp + bklan5.lit</code> Tour (12 Curated Views — Click to Enlarge)</h2>
  <div class="grid-shots">
    {''.join(cards_html)}
  </div>

  <h2 class="sec-title">3. Interactive 360° Harmless NPC Turntable &amp; Custom Murals / Daniel Posters</h2>
  <div class="studio-grid">
    <div class="card-box">
      <h3 style="margin-top:0">360° 8-Angle In-Game <code>.spr32</code> Turntable (Drag Left/Right to Orbit)</h3>
      <div class="tab-row" id="sprTabs">
        <button class="tab-btn active" onclick="pickSpr('greensuit', this)">Green-Suit Wheelman</button>
        <button class="tab-btn" onclick="pickSpr('robeguy', this)">The Flamingo Fiend</button>
        <button class="tab-btn" onclick="pickSpr('david', this)">David Ojeda (Harmless)</button>
        <button class="tab-btn" onclick="pickSpr('daniel_lan', this)">Daniel 360° LAN Station</button>
      </div>
      <canvas id="sprCanvas" width="380" height="380"></canvas>
      <p id="sprDesc" style="text-align:center;color:var(--muted);font-size:13px;margin:10px 0 0">
        <code>npc_greensuit_wheelman</code> — Cruises Fox 20th &amp; H and E 21st St. 0 damage to players; gib-explodes across all 8 angles when shot (respawns in 25s).
      </p>
    </div>
    <div class="card-box">
      <h3 style="margin-top:0">Daniel Meme Channels (<code>cnt 8..11</code>) &amp; Padre / Fox Boutique Murals</h3>
      <div class="poster-grid">
        <div class="poster-item"><img src="{poster_b64['dan_4am']}" alt="4 AM"><b>dan_4am</b><span>Clip 8 · 4 AM Table</span></div>
        <div class="poster-item"><img src="{poster_b64['dan_shaaa']}" alt="SHAAA"><b>dan_shaaa</b><span>Clip 9 · SHAAAA!</span></div>
        <div class="poster-item"><img src="{poster_b64['dan_webcam']}" alt="Webcam"><b>dan_webcam</b><span>Clip 10 · Webcam</span></div>
        <div class="poster-item"><img src="{poster_b64['dan_ccc']}" alt="CCC"><b>dan_ccc</b><span>Clip 11 · CCC!</span></div>
        <div class="poster-item"><img src="{poster_b64['pad_mural']}" alt="Cowgirl"><b>pad_mural</b><span>Padre Lobby Mural</span></div>
        <div class="poster-item"><img src="{poster_b64['pad_dandy']}" alt="Dandelion"><b>pad_dandy</b><span>Fireside Dandelion</span></div>
        <div class="poster-item"><img src="{poster_b64['pad_rococo']}" alt="Rococo"><b>pad_rococo</b><span>Suite Wallpaper</span></div>
        <div class="poster-item"><img src="{poster_b64['fx_tapestry']}" alt="Tapestry"><b>fx_tapestry</b><span>Fox Lobby Tapestry</span></div>
      </div>
    </div>
  </div>

  <h2 class="sec-title">4. Full <code>bklan5</code> Architectural Plan (1,488 World + 6,692 Detail + 94 Fence Brushes · 1,954 Entities)</h2>
  <div class="plan-wrap">
    <img src="{plan_b64}" alt="bklan5 overhead plan">
    <p style="color:var(--muted);font-size:13px;margin:10px 0 0">
      In-game console: <code>map bklan5</code> (automatically enables <code>v_glslgamma_2d 1</code> for crisp Quake HUD!) &middot;
      Switch baked lighting presets anytime: <code>python source/mm_tools/apply_bklan5_preset.py &lt;soft_daylight|sunny_balanced|warm_amber|twilight_neon&gt;</code>
    </p>
  </div>
</div>

<div id="lightbox" onclick="this.classList.remove('open')">
  <img id="lbImg" src="" alt="">
  <div id="lbCaption"></div>
</div>

<script>
const PRESETS = {json.dumps(preset_js_data)};
function pickPreset(idx, btn) {{
  const p = PRESETS[idx];
  document.getElementById("presetImg").src = p.src;
  document.getElementById("presetTitle").textContent = p.title;
  document.getElementById("presetDesc").textContent = p.desc;
  document.getElementById("presetStats").textContent = p.stats;
  btn.parentElement.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
}}

const SHOTS = {json.dumps([{"src": s["src"], "title": s["title"] + " — " + s["coords"]} for s in shot_cards_data])};
function openLightbox(idx) {{
  document.getElementById("lbImg").src = SHOTS[idx].src;
  document.getElementById("lbCaption").textContent = SHOTS[idx].title;
  document.getElementById("lightbox").classList.add("open");
}}

const SPR_SRCS = {json.dumps(spr_atlases)};
const SPR_INFO = {{
  greensuit: "npc_greensuit_wheelman — Cruises Fox 20th & H and E 21st St outside Larry's Warehouse. Harmless (0 dmg), shootable 8-angle gib explosion!",
  robeguy: "npc_robeguy — The Flamingo Fiend roaming Fox Plaza & Larry's LAN Courtyard. Harmless (0 dmg), 24-frame flamingo feather & gib boom when shot!",
  david: "npc_david_squad — Harmless David Ojeda flexing money bags & spinning slots while fleeing all 3 chasing pregnant women outside Golden West Casino!",
  daniel_lan: "monster_daniel (spawnflags 1) — Harmless stationary 360° Bakersfield LAN Station inside Larry's Warehouse SE bay!"
}};
const imgs = {{}};
for (const [k, src] of Object.entries(SPR_SRCS)) {{
  const im = new Image(); im.src = src; imgs[k] = im;
}}
let curKey = "greensuit", curAngle = 0, autoSpin = true, dragX = null;
const cv = document.getElementById("sprCanvas"), ctx = cv.getContext("2d");
function pickSpr(k, btn) {{
  curKey = k;
  document.querySelectorAll("#sprTabs .tab-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("sprDesc").textContent = SPR_INFO[k];
}}
cv.addEventListener("pointerdown", e => {{ autoSpin = false; dragX = e.clientX; cv.setPointerCapture(e.pointerId); }});
cv.addEventListener("pointermove", e => {{
  if (dragX === null) return;
  const dx = e.clientX - dragX;
  if (Math.abs(dx) > 18) {{ curAngle = (curAngle + (dx > 0 ? 1 : 7)) % 8; dragX = e.clientX; }}
}});
cv.addEventListener("pointerup", () => {{ dragX = null; }});

let tick = 0;
setInterval(() => {{
  tick++;
  if (autoSpin && tick % 7 === 0) curAngle = (curAngle + 1) % 8;
  const im = imgs[curKey];
  ctx.clearRect(0, 0, cv.width, cv.height);
  if (!im || !im.complete || !im.naturalWidth) return;
  const cw = im.naturalWidth / 6, ch = im.naturalHeight / 8;
  const f = tick % 6;
  const scale = Math.min(330 / cw, 330 / ch);
  const dw = cw * scale, dh = ch * scale;
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(im, f * cw, curAngle * ch, cw, ch, (cv.width - dw) / 2, (cv.height - dh) / 2 + 10, dw, dh);
  ctx.fillStyle = "rgba(15,23,42,0.82)";
  ctx.fillRect(12, 12, 148, 28);
  ctx.fillStyle = "#facc15";
  ctx.font = "bold 13px monospace";
  ctx.fillText("Angle " + (curAngle * 45) + "° · Frame " + (f + 1) + "/6", 20, 30);
}}, 95);
</script>
</body>
</html>
"""
    with open(OUT_HTML, "w", encoding="utf-8") as fp:
        fp.write(html)
    print(f"Built self-contained HTML showcase: {OUT_HTML} ({os.path.getsize(OUT_HTML) / 1048576:.2f} MB)")


def main():
    preset_shots, captured = capture_all()
    build_lighting_sheet(preset_shots)
    build_telegram_collage(captured)
    build_html(preset_shots, captured)


if __name__ == "__main__":
    main()
