"""Builds the 100% self-contained single-file 60-120 FPS <canvas> HTML Inspector for
Tinfoil-Hat Bryan, His Demons & His DOZEN (12) 360° Conspiracy, Weapon & Nerd Animations:
  G:\\Quake\\Combat\\BakersfieldQuake\\bryan_demons.html

Embeds:
  - 6 Core Sprite Atlases (Solo Run, Solo Detector Scan, Giant-Swing Demon-Whirl,
    3-Demon Trio Surge, 32f Hell Portal Death, DarkPlaces Toned .SPR32)
  - ALL 12 Ultra-High-FPS 360° Conspiracy, Nunchuck, Sword & Nerd Atlases
    (8 angles x 24 frames = 192 frames each -> 2,616 RGBA frames total!)
  - All 6 Bryan & Demon WAV voice clips + procedural WebAudio nerd/weapon SFX
  - Master 12x8 Conspiracy/Weapon/Nerd Poster + Core Turnaround + Death Sheet + 4 In-Game Captures
Zero external dependencies or network requests.
"""
import base64
import io
import json
import os
from PIL import Image

MOD_DIR = r"G:\Quake\Combat\BakersfieldQuake"
WEB_DIR = os.path.join(MOD_DIR, "bryan_sprite")
ATLAS_DIR = os.path.join(WEB_DIR, "atlases")
SND_DIR = os.path.join(MOD_DIR, "sound", "bryan")
OUT_HTML = os.path.join(MOD_DIR, "bryan_demons.html")

MODES_META = [
    # Core Quake Sprites (Main = Solo Bryan!)
    {"id": "run", "group": "core", "tab": "🏃 Solo Bryan Run (Main)", "title": "Solo Bryan 360° Run (No Demons)", "dirs": 8, "frames": 6, "fps": 12, "gy": 263, "sfx": "step"},
    {"id": "scan", "group": "core", "tab": "📡 Solo Detector Scan", "title": "Solo RGB Demon Detector Scan", "dirs": 8, "frames": 6, "fps": 10, "gy": 263, "sfx": "radar"},
    {"id": "whirl", "group": "core", "tab": "🌪️ \"NO WAY!\" Demon-Whirl", "title": "360° Giant-Swing Demon-Whirl", "dirs": 8, "frames": 8, "fps": 15, "gy": 263, "sfx": "whirl"},
    {"id": "surge", "group": "core", "tab": "⚡ 3-Demon Trio Surge", "title": "360° 3-Demon Trio EMF Overload", "dirs": 8, "frames": 8, "fps": 14, "gy": 263, "sfx": "zap"},
    {"id": "death", "group": "core", "tab": "🔥 Hell Portal Death (32f)", "title": "4-Act Hell Portal Drag-Down Death", "dirs": 1, "frames": 32, "fps": 14, "gy": 263, "sfx": "boom"},
    {"id": "spr32", "group": "core", "tab": "🕹️ DarkPlaces .SPR32", "title": "DarkPlaces HDR-Toned .SPR32", "dirs": 8, "frames": 6, "fps": 12, "gy": 263, "sfx": "radar"},

    # THE DOZEN (12) NEW 360° ULTRA-HIGH-FPS CONSPIRACY, WEAPON & NERD ANIMATIONS!
    {"id": "flat_earth", "group": "conspiracy", "tab": "🌍❄️ #1 Flat Earth & Globe Punt", "title": "Flat Earth Ice-Wall Frisbee & Fake-Globe Punt", "dirs": 8, "frames": 24, "fps": 50, "gy": 256, "sfx": "whoosh"},
    {"id": "corkboard", "group": "conspiracy", "tab": "🧶📌 #2 Pepe Silvia Corkboard", "title": "Pepe Silvia Red-String Conspiracy Meltdown", "dirs": 8, "frames": 24, "fps": 56, "gy": 256, "sfx": "radar"},
    {"id": "chemtrails", "group": "conspiracy", "tab": "✈️🐸 #3 Chemtrail Gay-Frogs", "title": "Chemtrail Gay-Frog Hazmat Leafblower Defense", "dirs": 8, "frames": 24, "fps": 50, "gy": 256, "sfx": "blower"},
    {"id": "five_g", "group": "conspiracy", "tab": "📡🐦 #4 5G vs. Faraday Dome", "title": "5G Tower & 'Birds Aren't Real' vs. Faraday Hat", "dirs": 8, "frames": 24, "fps": 60, "gy": 256, "sfx": "zap"},
    {"id": "illuminati", "group": "conspiracy", "tab": "👁️🔺 #5 Illuminati Megaphone", "title": "Reptilian Illuminati Eye & Megaphone Exorcism", "dirs": 8, "frames": 24, "fps": 50, "gy": 256, "sfx": "horn"},
    {"id": "ufo_naruto", "group": "conspiracy", "tab": "🛸🏃 #6 Area-51 Naruto + UFO", "title": "Area-51 45° Naruto-Run & Backup-Tinfoil-Hat UFO", "dirs": 8, "frames": 24, "fps": 60, "gy": 256, "sfx": "ufo"},
    {"id": "nunchuck_god", "group": "weapons", "tab": "🥢🔥 #7 Quad Nunchucks + BONK!", "title": "Mach-3 Flaming Nunchucks + Tinfoil Hat BONK!", "dirs": 8, "frames": 24, "fps": 60, "gy": 256, "sfx": "bonk"},
    {"id": "katana_anime", "group": "weapons", "tab": "⚔️🌸 #8 Dual Katana Anime Cut", "title": "Mall-Ninja Dual Katana Anime Judgment-Cut", "dirs": 8, "frames": 24, "fps": 60, "gy": 256, "sfx": "katana"},
    {"id": "lightsaber_paladin", "group": "weapons", "tab": "🗡️⚡ #9 Greatsword + Lightsaber", "title": "Blue Rune Greatsword & Dual-Plasma Saber Tornado", "dirs": 8, "frames": 24, "fps": 60, "gy": 256, "sfx": "saber"},
    {"id": "dnd_nat20", "group": "nerd", "tab": "🎲🧙 #10 D&D Nat-20 Fireball", "title": "Tinfoil Wizard Critical Nat-20 D20 Fireball", "dirs": 8, "frames": 24, "fps": 52, "gy": 256, "sfx": "boom"},
    {"id": "super_saiyan", "group": "nerd", "tab": "🔥⚡ #11 Super-Tinfoil Saiyan", "title": "Over-9000 Super-Tinfoil Saiyan 3D Kamehameha", "dirs": 8, "frames": 24, "fps": 60, "gy": 256, "sfx": "kame"},
    {"id": "matrix_larp", "group": "nerd", "tab": "🕶️💊 #12 Matrix Bullet-Time", "title": "Matrix 62° Bullet-Time Limbo & Cyber Power-Glove", "dirs": 8, "frames": 24, "fps": 60, "gy": 256, "sfx": "matrix"},
]


def encode_file_b64(path, mime):
    with open(path, "rb") as fp:
        return f"data:{mime};base64," + base64.b64encode(fp.read()).decode("ascii")


def encode_rgb_jpg(path, max_w=1280, quality=88):
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        nh = int(round(im.height * (max_w / im.width)))
        im = im.resize((max_w, nh), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main():
    print("Embedding 18 RGBA WebP atlases (2,616 frames), posters, in-game shots, and WAVs...")
    atlases = {}
    for m in MODES_META:
        p = os.path.join(ATLAS_DIR, f"{m['id']}.webp")
        atlases[m["id"]] = encode_file_b64(p, "image/webp")

    sheets = {
        "dozen_poster": encode_rgb_jpg(os.path.join(WEB_DIR, "bryan_dozen_showcase_sheet.jpg"), max_w=1280, quality=90),
        "turnaround": encode_rgb_jpg(os.path.join(WEB_DIR, "bryan_360_turnaround_sheet.png"), max_w=1360, quality=90),
        "death_sheet": encode_rgb_jpg(os.path.join(WEB_DIR, "bryan_death_contact_sheet.jpg"), max_w=1360, quality=88),
        "ig_scan": encode_rgb_jpg(os.path.join(WEB_DIR, "ingame_scan.jpg"), max_w=920, quality=86),
        "ig_sprint": encode_rgb_jpg(os.path.join(WEB_DIR, "ingame_sprint.jpg"), max_w=920, quality=86),
        "ig_whirl": encode_rgb_jpg(os.path.join(WEB_DIR, "ingame_whirl.jpg"), max_w=920, quality=86),
        "ig_surge": encode_rgb_jpg(os.path.join(WEB_DIR, "ingame_trio_surge.jpg"), max_w=920, quality=86),
    }

    sounds = {
        "sense": encode_file_b64(os.path.join(SND_DIR, "sense.wav"), "audio/wav"),
        "detector": encode_file_b64(os.path.join(SND_DIR, "detector.wav"), "audio/wav"),
        "noway": encode_file_b64(os.path.join(SND_DIR, "noway.wav"), "audio/wav"),
        "whirl": encode_file_b64(os.path.join(SND_DIR, "whirl.wav"), "audio/wav"),
        "slash": encode_file_b64(os.path.join(SND_DIR, "slash.wav"), "audio/wav"),
        "portal_die": encode_file_b64(os.path.join(SND_DIR, "portal_die.wav"), "audio/wav"),
    }

    modes_json = json.dumps(MODES_META, separators=(",", ":"))
    atlases_json = json.dumps(atlases, separators=(",", ":"))
    sounds_json = json.dumps(sounds, separators=(",", ":"))

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tinfoil-Hat Bryan — 360° Solo, Demons &amp; Dozen High-FPS Conspiracy/Weapon/Nerd Animations</title>
<style>
  :root {{
    --bg:#0b0e15; --panel:#151925; --panel2:#1e2436; --ink:#f8fafc; --dim:#94a3b8;
    --accent:#ef4444; --accent2:#38bdf8; --purple:#a855f7; --neon:#4ade80; --warn:#fbbf24;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:13.5px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:10px;
    padding:16px 14px 48px; min-height:100vh;
  }}
  header {{ text-align:center; max-width:1080px; }}
  h1 {{ font-size:23px; margin:0 0 4px; font-weight:800; letter-spacing:-0.015em; }}
  .sub {{ color:var(--dim); font-size:13px; margin:0; }}
  .sub code {{ color:#fca5a5; background:#2b171d; padding:2px 6px; border-radius:4px; font-weight:700; }}
  .pill {{
    display:inline-block; margin-left:6px; padding:2px 8px; border-radius:999px;
    background:#143326; border:1px solid #22c55e; color:#bbf7d0; font-size:11px; font-weight:700;
  }}
  .pill.fps {{ background:#1e1b4b; border-color:#818cf8; color:#e0e7ff; }}

  .deck {{
    width:min(100%, 1080px); background:var(--panel); border:1px solid #293146;
    border-radius:12px; padding:9px 11px; display:flex; flex-direction:column; gap:8px;
  }}
  .deck-hdr {{
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;
    font-size:12px; font-weight:800; color:#cbd5e1; text-transform:uppercase; letter-spacing:0.04em;
  }}
  .tabs {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(164px, 1fr)); gap:6px; }}
  .tab {{
    padding:7px 8px; border-radius:8px; border:1.5px solid #2f384e;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:700; font-size:12px;
    cursor:pointer; transition:all 0.1s ease; text-align:left; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  }}
  .tab:hover {{ border-color:#64748b; transform:translateY(-1px); }}
  .tab.on {{ background:#3a1620; border-color:var(--accent); color:#fecdd3; box-shadow:0 0 14px rgba(239,68,68,0.28); }}
  .tab.dozen.on {{ background:#2b1745; border-color:var(--purple); color:#f3e8ff; box-shadow:0 0 16px rgba(168,85,247,0.34); }}

  .party-btns {{ display:flex; gap:6px; flex-wrap:wrap; }}
  .pbtn {{
    background:linear-gradient(135deg, #7c3aed, #db2777); color:#fff; border:0; border-radius:7px;
    padding:5px 11px; font:inherit; font-size:12px; font-weight:800; cursor:pointer;
  }}
  .pbtn.tour.on {{ background:linear-gradient(135deg, #059669, #0284c7); box-shadow:0 0 12px rgba(56,189,248,0.4); }}

  #stage {{
    width:min(100%, 1080px); height:min(62vh, 520px); min-height:360px;
    border-radius:14px; border:1px solid #363f56; position:relative;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    user-select:none; touch-action:none; cursor:grab;
  }}
  #stage.drag {{ cursor:grabbing; }}
  #stage.checker  {{ background:repeating-conic-gradient(#242936 0% 25%, #191d27 0% 50%) 0 0/24px 24px; }}
  #stage.quake    {{ background:radial-gradient(circle at 50% 70%, #462f20 0%, #1d140f 68%, #0b0807 100%); }}
  #stage.hellfire {{ background:radial-gradient(circle at 50% 78%, #701814 0%, #2a0b10 62%, #09060a 100%); }}
  #stage.cyber    {{ background:radial-gradient(circle at 50% 60%, #0f382a 0%, #09131c 75%, #04070d 100%); }}
  #stage.light    {{ background:#cbd5e1; }}

  #wrap {{
    position:relative; height:93%; aspect-ratio:320/288;
    display:flex; align-items:center; justify-content:center;
    transform-origin:50% 89%;
  }}
  #stageCanvas {{ width:100%; height:100%; display:block; pointer-events:none; }}
  #stageCanvas.pixel {{ image-rendering:pixelated; }}

  #reticle {{ position:absolute; inset:0; pointer-events:none; display:none; }}
  #reticle.on {{ display:block; }}
  .gline {{ position:absolute; left:3%; right:3%; top:89%; border-top:1.5px dashed rgba(251,191,36,0.9); }}
  .aline {{ position:absolute; top:3%; bottom:2%; left:50%; border-left:1.5px dashed rgba(56,189,248,0.72); }}
  .odot  {{ position:absolute; left:50%; top:89%; width:10px; height:10px; margin:-5px 0 0 -5px; border-radius:50%; background:var(--warn); box-shadow:0 0 0 2px #0f172a; }}

  #badge {{
    position:absolute; top:12px; left:14px; background:rgba(10,13,20,0.9);
    border:1px solid #4c3b5c; border-radius:8px; padding:6px 12px;
    font-size:13px; font-weight:800; color:#f3e8ff; pointer-events:none; z-index:5;
  }}
  #meta {{
    position:absolute; top:12px; right:14px; background:rgba(10,13,20,0.88);
    border:1px solid #3c4458; border-radius:8px; padding:5px 11px;
    font-size:12px; color:#bae6fd; pointer-events:none; font-variant-numeric:tabular-nums; z-index:5; font-weight:700;
  }}
  #draghint {{
    position:absolute; bottom:10px; right:14px; background:rgba(10,13,20,0.84);
    border:1px solid #2e3545; border-radius:6px; padding:4px 10px;
    font-size:12px; color:#cbd5e1; pointer-events:none; z-index:5;
  }}

  .row {{
    display:flex; flex-wrap:wrap; gap:9px; align-items:center; justify-content:center;
    width:min(100%, 1080px); background:var(--panel); border:1px solid #2b3347;
    border-radius:10px; padding:9px 12px;
  }}
  button.ctrl {{
    background:var(--accent); color:#fff; border:0; border-radius:6px;
    padding:6px 12px; font:inherit; font-weight:700; cursor:pointer;
  }}
  button.ctrl.spin {{ background:var(--accent2); color:#082f49; }}
  button.ctrl.alt  {{ background:#2c3449; color:var(--ink); font-weight:600; }}
  button.ctrl.alt.on {{ background:#1d3b2f; border:1px solid var(--neon); color:#bbf7d0; }}
  button.ctrl.step {{ background:#252d40; color:#cbd5e1; padding:6px 9px; font-weight:700; }}
  button.snd {{
    background:#232a3c; color:#e2e8f0; border:1px solid #3d4863; border-radius:7px;
    padding:6px 10px; font:inherit; font-size:12px; font-weight:700; cursor:pointer;
  }}
  button.snd:hover, button.snd.playing {{ border-color:var(--neon); color:#bbf7d0; background:#193327; }}
  label {{ color:var(--dim); display:flex; gap:5px; align-items:center; font-size:12.5px; font-weight:600; }}
  input[type=range] {{ accent-color:var(--purple); cursor:pointer; }}

  #strip {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:6px; width:min(100%, 1080px);
  }}
  @media (max-width:740px) {{ #strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  #strip button {{
    padding:4px 4px 3px; background:var(--panel); border:2px solid transparent;
    border-radius:8px; display:flex; flex-direction:column; align-items:center; gap:2px;
    color:var(--dim); font-size:11px; font-weight:700; cursor:pointer;
  }}
  #strip button.on {{ border-color:var(--accent2); color:var(--ink); background:#1c293d; }}
  #strip canvas {{ width:100%; aspect-ratio:320/288; display:block; }}

  .sheets {{
    width:min(100%, 1080px); display:flex; flex-direction:column; gap:14px; margin-top:4px;
  }}
  .card {{
    background:var(--panel); border:1px solid #2b3347; border-radius:12px; padding:14px;
  }}
  .card h2 {{ font-size:15px; margin:0 0 10px; color:#f1f5f9; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; }}
  .card h2 span {{ font-size:12px; color:var(--dim); font-weight:500; }}
  .card > img {{ width:100%; border-radius:8px; display:block; border:1px solid #2d3446; }}

  #framegrid {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(104px, 1fr)); gap:7px;
  }}
  .fcell {{
    background:repeating-conic-gradient(#232834 0% 25%, #191d26 0% 50%) 0 0/16px 16px;
    border:1.5px solid #2f384d; border-radius:8px; padding:4px; cursor:pointer;
    display:flex; flex-direction:column; align-items:center; gap:2px;
  }}
  .fcell.on {{ border-color:var(--warn); box-shadow:0 0 10px rgba(251,191,36,0.32); }}
  .fcell canvas {{ width:100%; aspect-ratio:320/288; display:block; }}
  .fcell span {{ font-size:10.5px; color:var(--dim); font-weight:700; }}

  .ig-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
  @media (max-width:700px) {{ .ig-grid {{ grid-template-columns:1fr; }} }}
  .ig-item {{ position:relative; }}
  .ig-item img {{ width:100%; border-radius:8px; display:block; border:1px solid #323a4f; }}
  .ig-cap {{
    position:absolute; bottom:8px; left:8px; background:rgba(10,13,20,0.88);
    border:1px solid #434d66; border-radius:6px; padding:3px 9px; font-size:11.5px; font-weight:700; color:#f8fafc;
  }}
  p.hint {{ color:var(--dim); margin:0; font-size:12px; text-align:center; }}
</style>
</head>
<body>
  <header>
    <h1>🛸 Tinfoil-Hat Bryan — 360° Solo, Demons &amp; Dozen High-FPS Conspiracy/Nerd Sets
      <span class="pill">100% Self-Contained</span>
      <span class="pill fps">2,616 RGBA Frames &bull; Up to 120 FPS</span>
    </h1>
    <p class="sub">
      Main Sprite: <code>progs/bryan.spr32</code> (Solo Run &amp; Solo Detector Scan + Demon Specials) &bull;
      In-game: <code>impulse 19</code> / <code>mb_force 17</code>
    </p>
  </header>

  <div class="deck">
    <div class="deck-hdr">
      <span>⭐ Core Quake Game Animations (Default = Solo Bryan Alone, Zero Demons)</span>
    </div>
    <div class="tabs" id="coreTabs"></div>

    <div class="deck-hdr" style="margin-top:4px;">
      <span>🛸 Dozen (12) Over-The-Top 360° Ultra-High-FPS Conspiracy, Nunchuck, Sword &amp; Nerd Sets (24f &times; 8 Angles @ 50–120 FPS!)</span>
      <div class="party-btns">
        <button class="pbtn" id="randBtn">🎲 Random Hilarious Set</button>
        <button class="pbtn tour" id="tourBtn">🔁 Auto-Tour All 12: OFF</button>
      </div>
    </div>
    <div class="tabs" id="dozenTabs"></div>
  </div>

  <div id="stage" class="checker">
    <div id="badge">0° Front · Solo Bryan 360° Run</div>
    <div id="meta">Frame 0/5 · 12 FPS</div>
    <div id="wrap">
      <canvas id="stageCanvas" width="320" height="288"></canvas>
      <div id="reticle">
        <div class="gline" id="gline"></div>
        <div class="aline"></div>
        <div class="odot" id="odot"></div>
      </div>
    </div>
    <div id="draghint">↔ Drag horizontally to orbit 360° &bull; Scroll wheel to zoom</div>
  </div>

  <div class="row">
    <button class="ctrl" id="play">Pause</button>
    <button class="ctrl step" id="prevf" title="Previous Frame">◀</button>
    <label>Frame <input id="fscrub" type="range" min="0" max="5" value="0" style="width:105px"></label>
    <button class="ctrl step" id="nextf" title="Next Frame">▶</button>
    <button class="ctrl spin" id="orbit">Auto-Spin 360°: ON</button>
    <label>Angle <input id="ang" type="range" min="0" max="7" value="0" style="width:92px"></label>
    <label>Speed <span id="fpsVal" style="color:#f3e8ff;min-width:46px">12 FPS</span>
      <input id="fps" type="range" min="4" max="120" value="12" style="width:96px">
    </label>
    <button class="ctrl alt on" id="blendBtn" title="Sub-frame 120Hz motion interpolation">120Hz Blend: ON</button>
    <label>Zoom <input id="zoom" type="range" min="100" max="240" value="100" style="width:74px"></label>
    <button class="ctrl alt" id="pixbtn">Filter: Crisp</button>
    <button class="ctrl alt" id="origbtn">Origin: OFF</button>
    <button class="ctrl alt" id="bgbtn">BG: Checker</button>
    <button class="ctrl alt on" id="sfxbtn">Synth SFX: ON</button>
  </div>

  <div class="row">
    <strong style="font-size:12px;color:#fca5a5;">🔊 Bryan Voice &amp; Demon Soundboard:</strong>
    <button class="snd" data-snd="sense">📡 "Demons in here, I can sense it"</button>
    <button class="snd" data-snd="detector">🎛️ "My Demon Detector"</button>
    <button class="snd" data-snd="noway">😱 "A DEMON! NO WAY!"</button>
    <button class="snd" data-snd="whirl">🌪️ 360° Demon Swing Brawl</button>
    <button class="snd" data-snd="slash">⚡ Demon-Trio Surge</button>
    <button class="snd" data-snd="portal_die">🔥 Hell Portal Death</button>
  </div>

  <p class="hint">Drag left/right on stage or press <b>Left/Right Arrows</b> to orbit 360° &bull; <b>Up/Down Arrows</b> step frames &bull; <b>Space</b> pauses &bull; Click any angle or frame cell below to inspect</p>
  <div id="strip"></div>

  <div class="sheets">
    <div class="card">
      <h2>🎞️ Live 360° Frame-by-Frame Strip Inspector <span id="gridlabel">Click any frame cell to freeze &amp; inspect</span></h2>
      <div id="framegrid"></div>
    </div>

    <div class="card">
      <h2>🛸 Master 12-Set &times; 8-Angle Conspiracy, Weapon &amp; Nerd Overview Matrix <span>All 12 new 360° animations across 0°–315°</span></h2>
      <img src="{sheets['dozen_poster']}" alt="Dozen Conspiracy Weapon Nerd 360 Showcase">
    </div>

    <div class="card">
      <h2>🕹️ Live In-Game DarkPlaces Verification (<code>map start</code> &bull; <code>impulse 19</code>) <span>Solo Bryan main animations + Demon specials</span></h2>
      <div class="ig-grid">
        <div class="ig-item"><img src="{sheets['ig_scan']}" alt="In-game Solo Scan"><div class="ig-cap">0° Front · Solo Bryan Detector Scan (No Demons)</div></div>
        <div class="ig-item"><img src="{sheets['ig_sprint']}" alt="In-game Solo Close-up"><div class="ig-cap">Close-Up · Solo Tinfoil-Hat Bryan + Blinking RGB Detector</div></div>
        <div class="ig-item"><img src="{sheets['ig_whirl']}" alt="In-game Whirl"><div class="ig-cap">Special · 360° "A DEMON! NO WAY!" Giant-Swing Whirl</div></div>
        <div class="ig-item"><img src="{sheets['ig_surge']}" alt="In-game Surge"><div class="ig-cap">Special · 360° 3-Demon Trio EMF Overload Surge</div></div>
      </div>
    </div>

    <div class="card">
      <h2>📐 Core Game 360° Turnaround Matrix <span>Rows: Solo Detector Scan &bull; Solo Bryan Run &bull; Giant-Swing Demon-Whirl &bull; 3-Demon Trio Surge</span></h2>
      <img src="{sheets['turnaround']}" alt="Core Bryan 360 Turnaround Matrix">
    </div>

    <div class="card">
      <h2>🔥 32-Frame 4-Act Hell Portal Drag-Down &amp; Smoking Tinfoil Hat Death Sequence <span>SPR32 Frames 232..263</span></h2>
      <img src="{sheets['death_sheet']}" alt="Bryan Hell Portal Death Sheet">
    </div>
  </div>

<script>
const MODES = {modes_json};
const ATLAS_URIS = {atlases_json};
const SOUNDS = {sounds_json};
const LABELS = ["0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left", "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"];
const FW = 320, FH = 288;

const MODE_MAP = {{}};
const ATLAS_IMGS = {{}};
MODES.forEach(m => {{
  MODE_MAP[m.id] = m;
  const im = new Image();
  im.src = ATLAS_URIS[m.id];
  im.onload = () => {{ if (m.id === curMode) {{ rebuildFrameGrid(true); drawAll(0); }} }};
  ATLAS_IMGS[m.id] = im;
}});

let curMode = "run", curDir = 0, curFrame = 0, subPhase = 0.0;
let playing = true, autoSpin = true, autoTour = false, subBlend = true, sfxOn = true;
let showOrigin = false, pixelated = false, bgi = 0;
const bgs = ["checker", "quake", "hellfire", "cyber", "light"];
const bgNames = ["Checker", "Quake Dungeon", "Hellfire", "Matrix Cyber", "Light"];

const stageCanvas = document.getElementById("stageCanvas"),
      sctx = stageCanvas.getContext("2d"),
      wrap = document.getElementById("wrap"),
      badge = document.getElementById("badge"), meta = document.getElementById("meta"),
      stage = document.getElementById("stage"), playBtn = document.getElementById("play"),
      prevBtn = document.getElementById("prevf"), nextBtn = document.getElementById("nextf"),
      fscrub = document.getElementById("fscrub"), orbitBtn = document.getElementById("orbit"),
      angEl = document.getElementById("ang"), fpsEl = document.getElementById("fps"),
      fpsVal = document.getElementById("fpsVal"), blendBtn = document.getElementById("blendBtn"),
      zoomEl = document.getElementById("zoom"), pixBtn = document.getElementById("pixbtn"),
      origBtn = document.getElementById("origbtn"), bgBtn = document.getElementById("bgbtn"),
      sfxBtn = document.getElementById("sfxbtn"), randBtn = document.getElementById("randBtn"),
      tourBtn = document.getElementById("tourBtn"), reticle = document.getElementById("reticle"),
      gline = document.getElementById("gline"), odot = document.getElementById("odot"),
      strip = document.getElementById("strip"), framegrid = document.getElementById("framegrid"),
      gridlabel = document.getElementById("gridlabel");

// Build Core & Dozen Tab Buttons
const coreTabs = document.getElementById("coreTabs"), dozenTabs = document.getElementById("dozenTabs");
const tabBtns = {{}};
MODES.forEach(m => {{
  const b = document.createElement("button");
  b.className = "tab" + (m.group !== "core" ? " dozen" : "") + (m.id === curMode ? " on" : "");
  b.textContent = m.tab;
  b.title = m.title;
  b.onclick = () => selectMode(m.id, false);
  (m.group === "core" ? coreTabs : dozenTabs).appendChild(b);
  tabBtns[m.id] = b;
}});

// Web Audio API Procedural Comedy/Weapon/Conspiracy Sound Synthesizer!
let actx = null;
function playProceduralSFX(kind) {{
  if (!sfxOn) return;
  try {{
    if (!actx) actx = new (window.AudioContext || window.webkitAudioContext)();
    if (actx.state === "suspended") actx.resume();
    const now = actx.currentTime;
    const osc = actx.createOscillator();
    const gain = actx.createGain();
    osc.connect(gain); gain.connect(actx.destination);

    if (kind === "ufo") {{
      osc.type = "sine";
      osc.frequency.setValueAtTime(520, now);
      osc.frequency.exponentialRampToValueAtTime(1180, now + 0.18);
      osc.frequency.exponentialRampToValueAtTime(640, now + 0.36);
      gain.gain.setValueAtTime(0.11, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.38);
      osc.start(now); osc.stop(now + 0.38);
    }} else if (kind === "bonk") {{
      osc.type = "triangle";
      osc.frequency.setValueAtTime(190, now);
      osc.frequency.exponentialRampToValueAtTime(760, now + 0.07);
      osc.frequency.exponentialRampToValueAtTime(280, now + 0.24);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now); osc.stop(now + 0.25);
    }} else if (kind === "katana") {{
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(900, now);
      osc.frequency.exponentialRampToValueAtTime(3400, now + 0.14);
      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now); osc.stop(now + 0.22);
    }} else if (kind === "saber") {{
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(98, now);
      osc.frequency.linearRampToValueAtTime(142, now + 0.16);
      osc.frequency.linearRampToValueAtTime(92, now + 0.34);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.start(now); osc.stop(now + 0.35);
    }} else if (kind === "kame") {{
      osc.type = "square";
      osc.frequency.setValueAtTime(160, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.32);
      gain.gain.setValueAtTime(0.10, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.34);
      osc.start(now); osc.stop(now + 0.34);
    }} else if (kind === "zap" || kind === "radar") {{
      osc.type = "square";
      osc.frequency.setValueAtTime(1250, now);
      osc.frequency.setValueAtTime(1680, now + 0.06);
      osc.frequency.setValueAtTime(980, now + 0.12);
      gain.gain.setValueAtTime(0.07, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.start(now); osc.stop(now + 0.18);
    }} else {{
      osc.type = "triangle";
      osc.frequency.setValueAtTime(340, now);
      osc.frequency.exponentialRampToValueAtTime(110, now + 0.22);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.23);
      osc.start(now); osc.stop(now + 0.23);
    }}
  }} catch (e) {{}}
}}

// Build 8-Direction Live <canvas> Strip
const stripBtns = [], stripCtxs = [];
for (let d = 0; d < 8; d++) {{
  const b = document.createElement("button");
  const cv = document.createElement("canvas");
  cv.width = 160; cv.height = 144;
  const sp = document.createElement("span");
  sp.textContent = (d * 45) + "°";
  b.appendChild(cv); b.appendChild(sp);
  b.onclick = () => {{ autoSpin = false; syncControls(); curDir = d; rebuildFrameGrid(false); drawAll(0); }};
  strip.appendChild(b);
  stripBtns.push(b);
  stripCtxs.push(cv.getContext("2d"));
}}

let lastGridSig = "", gridCells = [];
function rebuildFrameGrid(force) {{
  const m = MODE_MAP[curMode];
  const sig = curMode + ":" + (m.dirs === 1 ? 0 : curDir);
  if (!force && sig === lastGridSig) return;
  lastGridSig = sig;
  framegrid.innerHTML = "";
  gridCells = [];
  const im = ATLAS_IMGS[curMode];
  const row = m.dirs === 1 ? 0 : curDir;

  for (let f = 0; f < m.frames; f++) {{
    const cell = document.createElement("div");
    cell.className = "fcell";
    const cv = document.createElement("canvas");
    cv.width = 160; cv.height = 144;
    if (im && im.complete && im.naturalWidth > 0) {{
      cv.getContext("2d").drawImage(im, f * FW, row * FH, FW, FH, 0, 0, 160, 144);
    }}
    const sp = document.createElement("span");
    sp.textContent = `Frame ${{f}}/${{m.frames - 1}}`;
    cell.appendChild(cv); cell.appendChild(sp);
    cell.onclick = () => {{
      playing = false; autoSpin = false; autoTour = false;
      curFrame = f; subPhase = 0;
      syncControls(); drawAll(0);
    }};
    framegrid.appendChild(cell);
    gridCells.push(cell);
  }}
  gridlabel.textContent = m.dirs === 1
    ? `${{m.title}} · All ${{m.frames}} Frames`
    : `${{LABELS[curDir]}} · ${{m.title}} (${{m.frames}} Frames @ ${{fpsEl.value}} FPS)`;
}}

function selectMode(id, fromTour) {{
  if (!fromTour) autoTour = false;
  curMode = id;
  const m = MODE_MAP[id];
  Object.keys(tabBtns).forEach(k => tabBtns[k].classList.toggle("on", k === id));
  curFrame = 0; subPhase = 0;
  fpsEl.value = m.fps;
  const gpct = (100 * m.gy / FH).toFixed(2) + "%";
  gline.style.top = gpct; odot.style.top = gpct;
  wrap.style.transformOrigin = `50% ${{gpct}}`;
  playProceduralSFX(m.sfx);
  syncControls();
  rebuildFrameGrid(true);
  drawAll(0);
}}

function drawAll(alphaNext) {{
  const m = MODE_MAP[curMode];
  curDir = ((curDir % 8) + 8) % 8;
  curFrame = ((curFrame % m.frames) + m.frames) % m.frames;
  angEl.value = curDir;
  fscrub.max = m.frames - 1;
  fscrub.value = curFrame;

  const im = ATLAS_IMGS[curMode];
  const row = m.dirs === 1 ? 0 : curDir;
  sctx.clearRect(0, 0, FW, FH);
  sctx.imageSmoothingEnabled = !(pixelated || curMode === "spr32");

  if (im && im.complete && im.naturalWidth > 0) {{
    sctx.globalAlpha = 1.0;
    sctx.drawImage(im, curFrame * FW, row * FH, FW, FH, 0, 0, FW, FH);
    if (playing && subBlend && alphaNext > 0.02 && curMode !== "spr32") {{
      const nf = (curFrame + 1) % m.frames;
      sctx.globalAlpha = alphaNext * 0.45;
      sctx.drawImage(im, nf * FW, row * FH, FW, FH, 0, 0, FW, FH);
      sctx.globalAlpha = 1.0;
    }}
  }}

  badge.textContent = m.dirs === 1 ? m.title : `${{LABELS[curDir]}} · ${{m.title}}`;
  meta.textContent = `Frame ${{curFrame}}/${{m.frames - 1}} · ${{fpsEl.value}} FPS`;

  // Update 8-angle thumbnail strip
  const stripM = m.dirs === 1 ? MODE_MAP["scan"] : m;
  const stripIm = ATLAS_IMGS[stripM.id];
  const sf = curFrame % stripM.frames;
  if (stripIm && stripIm.complete && stripIm.naturalWidth > 0) {{
    for (let k = 0; k < 8; k++) {{
      stripCtxs[k].clearRect(0, 0, 160, 144);
      stripCtxs[k].drawImage(stripIm, sf * FW, k * FH, FW, FH, 0, 0, 160, 144);
      stripBtns[k].classList.toggle("on", k === curDir);
    }}
  }}
  gridCells.forEach((c, idx) => c.classList.toggle("on", idx === curFrame));
}}

function syncControls() {{
  playBtn.textContent = playing ? "Pause" : "Play";
  orbitBtn.textContent = "Auto-Spin 360°: " + (autoSpin ? "ON" : "OFF");
  tourBtn.textContent = "🔁 Auto-Tour All 12: " + (autoTour ? "ON" : "OFF");
  tourBtn.classList.toggle("on", autoTour);
  fpsVal.textContent = fpsEl.value + " FPS";
  blendBtn.textContent = "120Hz Blend: " + (subBlend ? "ON" : "OFF");
  blendBtn.classList.toggle("on", subBlend);
  pixBtn.textContent = "Filter: " + ((pixelated || curMode === "spr32") ? "Pixelated" : "Crisp");
  stageCanvas.classList.toggle("pixel", pixelated || curMode === "spr32");
  origBtn.textContent = "Origin: " + (showOrigin ? "ON" : "OFF");
  reticle.classList.toggle("on", showOrigin);
  stage.className = bgs[bgi];
  bgBtn.textContent = "BG: " + bgNames[bgi];
  sfxBtn.textContent = "Synth SFX: " + (sfxOn ? "ON" : "OFF");
  sfxBtn.classList.toggle("on", sfxOn);
  wrap.style.transform = `scale(${{(+zoomEl.value || 100) / 100}})`;
}}

const dozenIds = MODES.filter(m => m.group !== "core").map(m => m.id);
randBtn.onclick = () => {{
  const choices = dozenIds.filter(id => id !== curMode);
  selectMode(choices[Math.floor(Math.random() * choices.length)], false);
}};
tourBtn.onclick = () => {{
  autoTour = !autoTour;
  if (autoTour && !dozenIds.includes(curMode)) selectMode(dozenIds[0], true);
  syncControls();
}};

playBtn.onclick = () => {{ playing = !playing; syncControls(); }};
prevBtn.onclick = () => {{ playing = false; curFrame--; subPhase = 0; syncControls(); drawAll(0); }};
nextBtn.onclick = () => {{ playing = false; curFrame++; subPhase = 0; syncControls(); drawAll(0); }};
fscrub.oninput  = () => {{ playing = false; curFrame = +fscrub.value; subPhase = 0; syncControls(); drawAll(0); }};
orbitBtn.onclick = () => {{ autoSpin = !autoSpin; syncControls(); }};
angEl.oninput = () => {{ autoSpin = false; curDir = +angEl.value; syncControls(); rebuildFrameGrid(false); drawAll(0); }};
fpsEl.oninput = () => {{ syncControls(); rebuildFrameGrid(true); }};
blendBtn.onclick = () => {{ subBlend = !subBlend; syncControls(); drawAll(0); }};
zoomEl.oninput = () => syncControls();
pixBtn.onclick = () => {{ pixelated = !pixelated; syncControls(); drawAll(0); }};
origBtn.onclick = () => {{ showOrigin = !showOrigin; syncControls(); }};
bgBtn.onclick = () => {{ bgi = (bgi + 1) % bgs.length; syncControls(); }};
sfxBtn.onclick = () => {{ sfxOn = !sfxOn; syncControls(); }};

let curAudio = null, curAudioBtn = null;
document.querySelectorAll("button.snd").forEach(btn => {{
  btn.onclick = () => {{
    if (curAudio) {{ curAudio.pause(); curAudio.currentTime = 0; }}
    if (curAudioBtn) curAudioBtn.classList.remove("playing");
    curAudio = new Audio(SOUNDS[btn.dataset.snd]);
    curAudioBtn = btn;
    btn.classList.add("playing");
    curAudio.onended = () => btn.classList.remove("playing");
    curAudio.play();
  }};
}});

let dragStartX = null, dragStartDir = 0;
stage.addEventListener("pointerdown", e => {{
  dragStartX = e.clientX; dragStartDir = curDir;
  stage.classList.add("drag"); stage.setPointerCapture(e.pointerId);
}});
stage.addEventListener("pointermove", e => {{
  if (dragStartX === null) return;
  const step = Math.round((e.clientX - dragStartX) / 38);
  if (step !== 0 && ((dragStartDir + step) % 8 + 8) % 8 !== curDir) {{
    autoSpin = false;
    curDir = ((dragStartDir + step) % 8 + 8) % 8;
    syncControls(); rebuildFrameGrid(false); drawAll(0);
  }}
}});
stage.addEventListener("pointerup", () => {{ dragStartX = null; stage.classList.remove("drag"); }});
stage.addEventListener("wheel", e => {{
  e.preventDefault();
  zoomEl.value = Math.min(240, Math.max(100, (+zoomEl.value || 100) + (e.deltaY < 0 ? 15 : -15)));
  syncControls();
}}, {{ passive:false }});

window.addEventListener("keydown", e => {{
  if (e.key === "ArrowLeft")  {{ autoSpin = false; curDir--; syncControls(); rebuildFrameGrid(false); drawAll(0); }}
  if (e.key === "ArrowRight") {{ autoSpin = false; curDir++; syncControls(); rebuildFrameGrid(false); drawAll(0); }}
  if (e.key === "ArrowUp")    {{ playing = false; curFrame++; subPhase = 0; syncControls(); drawAll(0); }}
  if (e.key === "ArrowDown")  {{ playing = false; curFrame--; subPhase = 0; syncControls(); drawAll(0); }}
  if (e.key === " ")          {{ e.preventDefault(); playing = !playing; syncControls(); }}
}});

let prevTs = 0, spinAcc = 0, tourAcc = 0;
function tick(ts) {{
  if (!prevTs) prevTs = ts;
  const dt = Math.min(0.1, (ts - prevTs) / 1000.0);
  prevTs = ts;

  const fps = +fpsEl.value || 50;
  if (playing) {{
    subPhase += dt * fps;
    if (subPhase >= 1.0) {{
      const adv = Math.floor(subPhase);
      subPhase -= adv;
      const oldF = curFrame;
      curFrame = (curFrame + adv) % MODE_MAP[curMode].frames;
      // Trigger funny *BONK!* audio cue right on frame 16 of Quad Nunchucks!
      if (curMode === "nunchuck_god" && oldF < 16 && curFrame >= 16) playProceduralSFX("bonk");
    }}
    drawAll(subPhase);
  }}

  if (autoSpin && MODE_MAP[curMode].dirs > 1) {{
    spinAcc += dt;
    if (spinAcc >= 0.65) {{
      spinAcc = 0;
      curDir = (curDir + 1) % 8;
      rebuildFrameGrid(false);
      if (!playing) drawAll(0);
    }}
  }}

  if (autoTour) {{
    tourAcc += dt;
    if (tourAcc >= 3.2) {{
      tourAcc = 0;
      const idx = (dozenIds.indexOf(curMode) + 1) % dozenIds.length;
      selectMode(dozenIds[idx], true);
    }}
  }}
  requestAnimationFrame(tick);
}}

syncControls();
rebuildFrameGrid(true);
drawAll(0);
requestAnimationFrame(tick);
</script>
</body>
</html>
"""
    with open(OUT_HTML, "w", encoding="utf-8") as fp:
        fp.write(html)
    print(f"Wrote 100% self-contained 60-120 FPS HTML: {OUT_HTML} ({os.path.getsize(OUT_HTML) / (1024 * 1024):.2f} MB)")


if __name__ == "__main__":
    main()
