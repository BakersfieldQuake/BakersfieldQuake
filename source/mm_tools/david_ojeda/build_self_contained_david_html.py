"""Builds the 100% Self-Contained Single-File <canvas> 360° HTML Inspector for
David Ojeda & the 3 Running Pregnant Hispanic Women:
  G:\\Quake\\Combat\\BakersfieldQuake\\david_ojeda_sprites.html

Embeds everything directly as base64 data URIs (ZERO external file/network requests):
  - All 14 RGBA WebP Sprite Atlases (David: fast_run, turbo_sprint, money_hold, money_run,
    slot_spin, slot_jackpot, slot_bust, idle; Pregnant Runners 1..3: run & idle)
  - Live "Full Chase Squad 360°" composite mode (David + all 3 pregnant women running together!)
  - All 6 custom WAV voice & casino sound clips
  - All 4 animated 360° turntable GIFs + 2 master contact sheets + 4 live DarkPlaces screenshots
"""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path

from PIL import Image

MOD_DIR = Path(r"G:\Quake\Combat\BakersfieldQuake")
WEB_DIR = MOD_DIR / "david_sprite"
SND_DIR = MOD_DIR / "sound" / "david"
OUT_HTML = MOD_DIR / "david_ojeda_sprites.html"

FW, FH = 320, 360
GY = round(492.0 * FH / 540.0)  # 328 px

MODES_META = [
    # Special Live Squad Mode (uses money_run + preg1_run + preg2_run + preg3_run atlases!)
    {"id": "squad_chase", "group": "david", "tab": "🏃💰🤰 Full Chase Squad 360°", "title": "Full 360° Chase Squad (David + All 3 Pregnant Runners!)", "dirs": 8, "frames": 8, "fps": 15, "gy": GY, "snd": "shower_love"},
    # David Ojeda's 8 Full-360° Modes
    {"id": "fast_run",     "group": "david", "tab": "🏃 Fast Run 360°",            "title": "David Ojeda — Fast Run 360°",                       "dirs": 8, "frames": 8, "fps": 16, "gy": GY, "snd": "sprint_rush"},
    {"id": "turbo_sprint", "group": "david", "tab": "⚡💨 Turbo Sprint 360°",      "title": "David Ojeda — Turbo Speed-Burst Sprint 360°",       "dirs": 8, "frames": 8, "fps": 18, "gy": GY, "snd": "sprint_rush"},
    {"id": "money_hold",   "group": "david", "tab": "💰💵 Holding Money Bag 360°", "title": "David Ojeda — Holding & Flexing Bag of Money 360°", "dirs": 8, "frames": 8, "fps": 13, "gy": GY, "snd": "money_bag"},
    {"id": "money_run",    "group": "david", "tab": "🏃💰 Money-Bag Sprint 360°",  "title": "David Ojeda — Heist Sprint w/ Bag of Money 360°",   "dirs": 8, "frames": 8, "fps": 16, "gy": GY, "snd": "money_bag"},
    {"id": "slot_spin",    "group": "david", "tab": "🎰🕹️ Slot Machine Spin 360°", "title": "David Playing Slot Machine — Lever Pull & Spin 360°", "dirs": 8, "frames": 8, "fps": 14, "gy": GY, "snd": "slot_spin"},
    {"id": "slot_jackpot", "group": "david", "tab": "🎰💎 Slot 7-7-7 JACKPOT 360°","title": "David Playing Slot Machine — 7-7-7 JACKPOT! 360°",  "dirs": 8, "frames": 8, "fps": 14, "gy": GY, "snd": "slot_jackpot"},
    {"id": "slot_bust",    "group": "david", "tab": "🎰💢 Slot Machine BUST 360°", "title": "David Playing Slot Machine — Near-Miss BUST/Tilt 360°", "dirs": 8, "frames": 8, "fps": 14, "gy": GY, "snd": "slot_bust"},
    {"id": "idle",         "group": "david", "tab": "🧍 Standing Idle 360°",       "title": "David Ojeda — Standing Idle Turnaround 360°",       "dirs": 8, "frames": 1, "fps": 8,  "gy": GY, "snd": "shower_love"},
    # 3 Running Pregnant Hispanic Women
    {"id": "preg1_run",    "group": "preg",  "tab": "🏃‍♀️🤰 Runner #1 (Coral) Run",  "title": "Pregnant Hispanic Runner #1 (Coral Top) — 360° Run",    "dirs": 8, "frames": 8, "fps": 15, "gy": GY, "snd": "sprint_rush"},
    {"id": "preg2_run",    "group": "preg",  "tab": "🏃‍♀️🤰 Runner #2 (Teal) Run",   "title": "Pregnant Hispanic Runner #2 (Teal Top) — 360° Run",     "dirs": 8, "frames": 8, "fps": 15, "gy": GY, "snd": "sprint_rush"},
    {"id": "preg3_run",    "group": "preg",  "tab": "🏃‍♀️🤰 Runner #3 (Yellow) Run", "title": "Pregnant Hispanic Runner #3 (Yellow Top) — 360° Run",   "dirs": 8, "frames": 8, "fps": 15, "gy": GY, "snd": "sprint_rush"},
    {"id": "preg1_idle",   "group": "preg",  "tab": "🧍‍♀️ Runner #1 Idle 360°",      "title": "Pregnant Hispanic Runner #1 (Coral Top) — 360° Idle",   "dirs": 8, "frames": 1, "fps": 8,  "gy": GY, "snd": ""},
    {"id": "preg2_idle",   "group": "preg",  "tab": "🧍‍♀️ Runner #2 Idle 360°",      "title": "Pregnant Hispanic Runner #2 (Teal Top) — 360° Idle",    "dirs": 8, "frames": 1, "fps": 8,  "gy": GY, "snd": ""},
    {"id": "preg3_idle",   "group": "preg",  "tab": "🧍‍♀️ Runner #3 Idle 360°",      "title": "Pregnant Hispanic Runner #3 (Yellow Top) — 360° Idle",  "dirs": 8, "frames": 1, "fps": 8,  "gy": GY, "snd": ""},
]


def encode_file_b64(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def encode_rgb_jpg(path: Path, max_w: int = 1360, quality: int = 88) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        nh = int(round(im.height * (max_w / im.width)))
        im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build_webp_atlas_b64(mode_meta: dict) -> tuple[str, str]:
    mid = mode_meta["id"]
    nf = mode_meta["frames"]
    atlas = Image.new("RGBA", (FW * nf, FH * 8), (0, 0, 0, 0))

    for d in range(8):
        for f in range(nf):
            if mid == "idle":
                fn = WEB_DIR / f"david_idle_d{d}.png"
            elif mid.startswith("preg") and mid.endswith("_idle"):
                p_num = mid[4]
                fn = WEB_DIR / f"preg{p_num}_idle_d{d}.png"
            elif mid.startswith("preg") and mid.endswith("_run"):
                p_num = mid[4]
                fn = WEB_DIR / f"preg{p_num}_run_d{d}_f{f}.png"
            else:
                fn = WEB_DIR / f"david_{mid}_d{d}_f{f}.png"

            cell = Image.open(fn).convert("RGBA").resize((FW, FH), Image.Resampling.LANCZOS)
            atlas.paste(cell, (f * FW, d * FH))

    buf = io.BytesIO()
    atlas.save(buf, format="WEBP", quality=90, method=4)
    return mid, "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    atlas_modes = [m for m in MODES_META if m["id"] != "squad_chase"]
    print(f"Packing {len(atlas_modes)} RGBA WebP 360° atlases in parallel...")
    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        pairs = list(ex.map(build_webp_atlas_b64, atlas_modes))
    atlases = dict(pairs)

    print("Embedding WAV soundboard, animated GIFs, contact sheets, and DarkPlaces captures...")
    sounds = {
        "shower_love": encode_file_b64(SND_DIR / "shower_love.wav", "audio/wav"),
        "sprint_rush": encode_file_b64(SND_DIR / "sprint_rush.wav", "audio/wav"),
        "money_bag":   encode_file_b64(SND_DIR / "money_bag.wav", "audio/wav"),
        "slot_spin":   encode_file_b64(SND_DIR / "slot_spin.wav", "audio/wav"),
        "slot_jackpot":encode_file_b64(SND_DIR / "slot_jackpot.wav", "audio/wav"),
        "slot_bust":   encode_file_b64(SND_DIR / "slot_bust.wav", "audio/wav"),
    }

    media = {
        "gif_run":    encode_file_b64(WEB_DIR / "david_fast_run_360.gif", "image/gif"),
        "gif_money":  encode_file_b64(WEB_DIR / "david_money_bag_360.gif", "image/gif"),
        "gif_slot":   encode_file_b64(WEB_DIR / "david_slot_machine_360.gif", "image/gif"),
        "gif_preg":   encode_file_b64(WEB_DIR / "pregnant_runners_360.gif", "image/gif"),
        "sheet_david":encode_rgb_jpg(WEB_DIR / "david_360_turnaround_sheet.png", max_w=1440, quality=90),
        "sheet_preg": encode_rgb_jpg(WEB_DIR / "pregnant_runners_360_sheet.png", max_w=1440, quality=90),
        "ig_1":       encode_rgb_jpg(WEB_DIR / "david_ig_1_squad.png", max_w=960, quality=88),
        "ig_2":       encode_rgb_jpg(WEB_DIR / "david_ig_2_slot_jackpot.png", max_w=960, quality=88),
        "ig_3":       encode_rgb_jpg(WEB_DIR / "david_ig_3_slot_spin_360.png", max_w=960, quality=88),
        "ig_4":       encode_rgb_jpg(WEB_DIR / "david_ig_4_live_chase.png", max_w=960, quality=88),
    }

    modes_json = json.dumps(MODES_META, separators=(",", ":"))
    atlases_json = json.dumps(atlases, separators=(",", ":"))
    sounds_json = json.dumps(sounds, separators=(",", ":"))
    gpct = round(100.0 * GY / FH, 2)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>David Ojeda &amp; 3 Running Pregnant Women — 100% Self-Contained 360° Sprite Inspector</title>
<style>
  :root {{
    --bg:#0b0e15; --panel:#151a26; --panel2:#1e2536; --ink:#f8fafc; --dim:#94a3b8;
    --accent:#f59e0b; --accent2:#10b981; --sky:#38bdf8; --slot:#ef4444; --purple:#a855f7;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:13.5px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:11px;
    padding:16px 14px 52px; min-height:100vh;
  }}
  header {{ text-align:center; max-width:1100px; }}
  h1 {{ font-size:23px; margin:0 0 5px; font-weight:800; letter-spacing:-0.015em; }}
  .sub {{ color:var(--dim); font-size:13px; margin:0; }}
  .sub code {{ color:#fde68a; background:#2c2210; padding:2px 6px; border-radius:4px; font-weight:700; }}
  .pill {{
    display:inline-block; margin-left:6px; padding:2px 8px; border-radius:999px;
    background:#143326; border:1px solid #22c55e; color:#bbf7d0; font-size:11px; font-weight:700;
  }}
  .pill.gold {{ background:#36260c; border-color:#f59e0b; color:#fef3c7; }}

  .deck {{
    width:min(100%, 1100px); background:var(--panel); border:1px solid #293246;
    border-radius:12px; padding:10px 12px; display:flex; flex-direction:column; gap:8px;
  }}
  .deck-hdr {{
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;
    font-size:12px; font-weight:800; color:#cbd5e1; text-transform:uppercase; letter-spacing:0.04em;
  }}
  .tabs {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(185px, 1fr)); gap:6px; }}
  .tab {{
    padding:8px 10px; border-radius:8px; border:1.5px solid #2f384e;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:700; font-size:12.5px;
    cursor:pointer; transition:all 0.1s ease; text-align:left; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  }}
  .tab:hover {{ border-color:#64748b; transform:translateY(-1px); }}
  .tab.on {{ background:#36260d; border-color:var(--accent); color:#fef3c7; box-shadow:0 0 14px rgba(245,158,11,0.28); }}
  .tab.preg.on {{ background:#0f2e25; border-color:var(--accent2); color:#d1fae5; box-shadow:0 0 14px rgba(16,185,129,0.28); }}

  .party-btns {{ display:flex; gap:6px; flex-wrap:wrap; }}
  .pbtn {{
    background:linear-gradient(135deg, #d97706, #dc2626); color:#fff; border:0; border-radius:7px;
    padding:5px 12px; font:inherit; font-size:12px; font-weight:800; cursor:pointer;
  }}
  .pbtn.tour.on {{ background:linear-gradient(135deg, #059669, #0284c7); box-shadow:0 0 12px rgba(56,189,248,0.4); }}

  #stage {{
    width:min(100%, 1100px); height:min(64vh, 540px); min-height:380px;
    border-radius:14px; border:1px solid #363f56; position:relative;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    user-select:none; touch-action:none; cursor:grab;
  }}
  #stage.drag {{ cursor:grabbing; }}
  #stage.casino  {{ background:radial-gradient(circle at 50% 62%, #522916 0%, #2a1310 58%, #0e090c 100%); }}
  #stage.checker {{ background:repeating-conic-gradient(#242936 0% 25%, #191d27 0% 50%) 0 0/24px 24px; }}
  #stage.quake   {{ background:radial-gradient(circle at 50% 70%, #462f20 0%, #1d140f 68%, #0b0807 100%); }}
  #stage.slate   {{ background:radial-gradient(circle at 50% 55%, #1e293b 0%, #0f172a 85%); }}
  #stage.light   {{ background:#cbd5e1; }}

  #wrap {{
    position:relative; height:94%; aspect-ratio:16/9;
    display:flex; align-items:center; justify-content:center;
    transform-origin:50% {gpct}%;
  }}
  #stageCanvas {{ width:100%; height:100%; display:block; pointer-events:none; object-fit:contain; }}
  #stageCanvas.pixel {{ image-rendering:pixelated; }}

  #reticle {{ position:absolute; inset:0; pointer-events:none; display:none; }}
  #reticle.on {{ display:block; }}
  .gline {{ position:absolute; left:6%; right:6%; top:{gpct}%; border-top:1.5px dashed rgba(245,158,11,0.9); }}
  .aline {{ position:absolute; top:4%; bottom:2%; left:50%; border-left:1.5px dashed rgba(56,189,248,0.72); }}
  .odot  {{ position:absolute; left:50%; top:{gpct}%; width:10px; height:10px; margin:-5px 0 0 -5px; border-radius:50%; background:var(--accent); box-shadow:0 0 0 2px #0f172a; }}

  #badge {{
    position:absolute; top:12px; left:14px; background:rgba(10,13,20,0.92);
    border:1px solid #57411d; border-radius:8px; padding:6px 12px;
    font-size:13px; font-weight:800; color:#fde68a; pointer-events:none; z-index:5;
  }}
  #meta {{
    position:absolute; top:12px; right:14px; background:rgba(10,13,20,0.88);
    border:1px solid #3c4458; border-radius:8px; padding:5px 11px;
    font-size:12px; color:#bae6fd; pointer-events:none; font-variant-numeric:tabular-nums; z-index:5; font-weight:700;
  }}
  #draghint {{
    position:absolute; bottom:10px; right:14px; background:rgba(10,13,20,0.86);
    border:1px solid #2e3545; border-radius:6px; padding:4px 10px;
    font-size:12px; color:#cbd5e1; pointer-events:none; z-index:5;
  }}

  .row {{
    display:flex; flex-wrap:wrap; gap:9px; align-items:center; justify-content:center;
    width:min(100%, 1100px); background:var(--panel); border:1px solid #2b3347;
    border-radius:10px; padding:9px 12px;
  }}
  button.ctrl {{
    background:var(--accent); color:#1c1203; border:0; border-radius:6px;
    padding:6px 12px; font:inherit; font-weight:800; cursor:pointer;
  }}
  button.ctrl.spin {{ background:var(--sky); color:#082f49; }}
  button.ctrl.alt  {{ background:#2c3449; color:var(--ink); font-weight:600; }}
  button.ctrl.alt.on {{ background:#153629; border:1px solid #22c55e; color:#bbf7d0; }}
  button.ctrl.step {{ background:#252d40; color:#cbd5e1; padding:6px 10px; font-weight:700; }}
  button.snd {{
    background:#232a3c; color:#e2e8f0; border:1px solid #3d4863; border-radius:7px;
    padding:6px 11px; font:inherit; font-size:12px; font-weight:700; cursor:pointer;
  }}
  button.snd:hover, button.snd.playing {{ border-color:var(--accent2); color:#bbf7d0; background:#143025; }}
  label {{ color:var(--dim); display:flex; gap:5px; align-items:center; font-size:12.5px; font-weight:600; }}
  input[type=range] {{ accent-color:var(--accent); cursor:pointer; }}

  #strip {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:6px; width:min(100%, 1100px);
  }}
  @media (max-width:740px) {{ #strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  #strip button {{
    padding:4px 4px 3px; background:var(--panel); border:2px solid transparent;
    border-radius:8px; display:flex; flex-direction:column; align-items:center; gap:2px;
    color:var(--dim); font-size:11px; font-weight:700; cursor:pointer;
  }}
  #strip button.on {{ border-color:var(--accent); color:var(--ink); background:#2b2111; }}
  #strip canvas {{ width:100%; aspect-ratio:320/360; display:block; }}

  .sheets {{
    width:min(100%, 1100px); display:flex; flex-direction:column; gap:14px; margin-top:4px;
  }}
  .card {{
    background:var(--panel); border:1px solid #2b3347; border-radius:12px; padding:14px;
  }}
  .card h2 {{ font-size:15px; margin:0 0 10px; color:#f1f5f9; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; }}
  .card h2 span {{ font-size:12px; color:var(--dim); font-weight:500; }}
  .card > img {{ width:100%; border-radius:8px; display:block; border:1px solid #2d3446; }}

  #framegrid {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(118px, 1fr)); gap:7px;
  }}
  .fcell {{
    background:repeating-conic-gradient(#232834 0% 25%, #191d26 0% 50%) 0 0/16px 16px;
    border:1.5px solid #2f384d; border-radius:8px; padding:4px; cursor:pointer;
    display:flex; flex-direction:column; align-items:center; gap:2px;
  }}
  .fcell.on {{ border-color:var(--accent); box-shadow:0 0 10px rgba(245,158,11,0.34); }}
  .fcell canvas {{ width:100%; aspect-ratio:320/360; display:block; }}
  .fcell span {{ font-size:11px; color:var(--dim); font-weight:700; }}

  .ig-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
  .gif-grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; }}
  @media (max-width:820px) {{ .gif-grid {{ grid-template-columns:repeat(2, 1fr); }} }}
  @media (max-width:700px) {{ .ig-grid {{ grid-template-columns:1fr; }} }}
  .ig-item {{ position:relative; }}
  .ig-item img, .gif-grid img {{ width:100%; border-radius:8px; display:block; border:1px solid #323a4f; }}
  .ig-cap {{
    position:absolute; bottom:8px; left:8px; background:rgba(10,13,20,0.88);
    border:1px solid #434d66; border-radius:6px; padding:3px 9px; font-size:11.5px; font-weight:700; color:#f8fafc;
  }}
  p.hint {{ color:var(--dim); margin:0; font-size:12px; text-align:center; }}
</style>
</head>
<body>
  <header>
    <h1>🎰💰 David Ojeda &amp; 3 Running Pregnant Women — Full 360° Quake Sprites
      <span class="pill">100% Self-Contained Offline HTML</span>
      <span class="pill gold">672 RGBA Frames + 6 WAVs Embedded</span>
    </h1>
    <p class="sub">
      <code>progs/david.spr32</code> (344f) &bull; <code>progs/preg_1..3.spr32</code> (56f each) &bull;
      In-Game: <code>impulse 22</code> (Squad), <code>impulse 23</code> (Solo David),
      <code>impulse 24</code> (Slot Machine), <code>impulse 25</code> (3 Runners) &bull; Mystery Box <code>mb_force 23..26</code>
    </p>
  </header>

  <div class="deck">
    <div class="deck-hdr">
      <span>💰🎰 David Ojeda — Full 360° Animations (+ Live Chase Squad)</span>
      <div class="party-btns">
        <button class="pbtn tour" id="tourBtn">🔁 Auto-Tour All Modes: OFF</button>
      </div>
    </div>
    <div class="tabs" id="davidTabs"></div>

    <div class="deck-hdr" style="margin-top:4px;">
      <span>🏃‍♀️🤰 3 Running Pregnant Hispanic Women — Full 360° Sprites</span>
    </div>
    <div class="tabs" id="pregTabs"></div>
  </div>

  <div id="stage" class="casino">
    <div id="badge">0° Front · Full 360° Chase Squad</div>
    <div id="meta">Frame 1/8 · 15 FPS</div>
    <div id="wrap">
      <canvas id="stageCanvas" width="640" height="360"></canvas>
      <div id="reticle">
        <div class="gline"></div>
        <div class="aline"></div>
        <div class="odot"></div>
      </div>
    </div>
    <div id="draghint">↔ Drag horizontally or press ◀ / ▶ to orbit 360° &bull; Scroll wheel to zoom</div>
  </div>

  <div class="row">
    <button class="ctrl" id="playBtn">⏸ Pause</button>
    <button class="ctrl step" id="prevF" title="Previous Frame">◀ Frame</button>
    <label>Scrub <input id="fscrub" type="range" min="0" max="7" value="0" style="width:95px"></label>
    <button class="ctrl step" id="nextF" title="Next Frame">Frame ▶</button>
    <button class="ctrl spin" id="orbitBtn">🔄 Auto-Orbit 360°: ON</button>
    <label>Angle <input id="angEl" type="range" min="0" max="7" value="0" style="width:88px"></label>
    <label>Speed <span id="fpsVal" style="color:#fde68a;min-width:44px">15 FPS</span>
      <input id="fpsEl" type="range" min="4" max="36" value="15" style="width:88px">
    </label>
    <label>Zoom <input id="zoomEl" type="range" min="100" max="240" value="100" style="width:74px"></label>
    <button class="ctrl alt" id="pixBtn">Filter: Crisp</button>
    <button class="ctrl alt" id="origBtn">Origin: OFF</button>
    <button class="ctrl alt" id="bgBtn">BG: Casino</button>
  </div>

  <div class="row">
    <strong style="font-size:12px;color:#fde68a;">🔊 Embedded Soundboard:</strong>
    <button class="snd" data-snd="shower_love">🎤 "Shower Me With Your Love!"</button>
    <button class="snd" data-snd="sprint_rush">💨 Fast Sprint Rush</button>
    <button class="snd" data-snd="money_bag">💰 Money Bag Ka-Ching</button>
    <button class="snd" data-snd="slot_spin">🎰 Slot Lever &amp; Spin</button>
    <button class="snd" data-snd="slot_jackpot">💎 7-7-7 JACKPOT!</button>
    <button class="snd" data-snd="slot_bust">💢 Slot BUST Buzzer</button>
  </div>

  <p class="hint">Drag left/right on stage or press <b>Left/Right Arrows</b> to orbit 360° &bull; <b>Up/Down Arrows</b> step frames &bull; <b>Space</b> pauses &bull; Click any angle or frame cell below to inspect</p>
  <div id="strip"></div>

  <div class="sheets">
    <div class="card">
      <h2>🎞️ Live 360° Frame-by-Frame Strip Inspector <span id="gridlabel">Click any frame cell to freeze &amp; inspect</span></h2>
      <div id="framegrid"></div>
    </div>

    <div class="card">
      <h2>🕹️ Live In-Game DarkPlaces Verification (<code>map start</code> &bull; <code>impulse 22 / 24</code>) <span>Captured directly from compiled progs.dat</span></h2>
      <div class="ig-grid">
        <div class="ig-item"><img src="{media['ig_1']}" alt="In-game Squad"><div class="ig-cap">impulse 22 · David Money-Bag Sprint + 3 Pregnant Runners</div></div>
        <div class="ig-item"><img src="{media['ig_2']}" alt="In-game Slot Jackpot"><div class="ig-cap">dv_mode 7 · 360° Slot Machine 7-7-7 JACKPOT Celebration</div></div>
        <div class="ig-item"><img src="{media['ig_3']}" alt="In-game Slot 360"><div class="ig-cap">315° Angled View · Vegas 777 Slot Machine Lever Pull</div></div>
        <div class="ig-item"><img src="{media['ig_4']}" alt="In-game Live Chase"><div class="ig-cap">Live Gameplay · All 3 Pregnant Hispanic Women Running on start</div></div>
      </div>
    </div>

    <div class="card">
      <h2>🔄 Embedded Animated 360° Turntable GIFs</h2>
      <div class="gif-grid">
        <img src="{media['gif_run']}" alt="David Fast Run 360 GIF">
        <img src="{media['gif_money']}" alt="David Money Bag 360 GIF">
        <img src="{media['gif_slot']}" alt="David Slot Machine 360 GIF">
        <img src="{media['gif_preg']}" alt="3 Pregnant Runners 360 GIF">
      </div>
    </div>

    <div class="card">
      <h2>📋 David Ojeda — Master 8-Mode &times; 8-Angle (360°) Contact Sheet</h2>
      <img src="{media['sheet_david']}" alt="David 360 Turnaround Sheet">
    </div>

    <div class="card">
      <h2>📋 3 Running Pregnant Hispanic Women — Master 360° Running Sheet</h2>
      <img src="{media['sheet_preg']}" alt="3 Pregnant Runners 360 Sheet">
    </div>
  </div>

<script>
const MODES = {modes_json};
const ATLAS_URIS = {atlases_json};
const SOUNDS = {sounds_json};
const LABELS = ["0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left", "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"];
const FW = {FW}, FH = {FH};

const MODE_MAP = {{}};
const ATLAS_IMGS = {{}};
MODES.forEach(m => {{
  MODE_MAP[m.id] = m;
  if (ATLAS_URIS[m.id]) {{
    const im = new Image();
    im.src = ATLAS_URIS[m.id];
    im.onload = () => {{ rebuildFrameGrid(true); drawAll(); }};
    ATLAS_IMGS[m.id] = im;
  }}
}});

let curMode = "squad_chase", curDir = 0, curFrame = 0, subPhase = 0.0;
let playing = true, autoSpin = true, autoTour = false, showOrigin = false, pixelated = false, bgi = 0;
const bgs = ["casino", "checker", "quake", "slate", "light"];
const bgNames = ["Casino", "Checker", "Quake", "Slate", "Light"];

const stageCanvas = document.getElementById("stageCanvas"),
      sctx = stageCanvas.getContext("2d"),
      wrap = document.getElementById("wrap"),
      badge = document.getElementById("badge"),
      meta = document.getElementById("meta"),
      stage = document.getElementById("stage"),
      playBtn = document.getElementById("playBtn"),
      prevBtn = document.getElementById("prevF"),
      nextBtn = document.getElementById("nextF"),
      fscrub = document.getElementById("fscrub"),
      orbitBtn = document.getElementById("orbitBtn"),
      angEl = document.getElementById("angEl"),
      fpsEl = document.getElementById("fpsEl"),
      fpsVal = document.getElementById("fpsVal"),
      zoomEl = document.getElementById("zoomEl"),
      pixBtn = document.getElementById("pixBtn"),
      origBtn = document.getElementById("origBtn"),
      bgBtn = document.getElementById("bgBtn"),
      tourBtn = document.getElementById("tourBtn"),
      reticle = document.getElementById("reticle"),
      strip = document.getElementById("strip"),
      framegrid = document.getElementById("framegrid"),
      gridlabel = document.getElementById("gridlabel");

const davidTabs = document.getElementById("davidTabs"), pregTabs = document.getElementById("pregTabs");
const tabBtns = {{}};
MODES.forEach(m => {{
  const b = document.createElement("button");
  b.className = "tab" + (m.group === "preg" ? " preg" : "") + (m.id === curMode ? " on" : "");
  b.textContent = m.tab;
  b.title = m.title;
  b.onclick = () => selectMode(m.id, false);
  (m.group === "david" ? davidTabs : pregTabs).appendChild(b);
  tabBtns[m.id] = b;
}});

const stripBtns = [], stripCtxs = [];
for (let d = 0; d < 8; d++) {{
  const b = document.createElement("button");
  const cv = document.createElement("canvas");
  cv.width = 160; cv.height = 180;
  const sp = document.createElement("span");
  sp.textContent = LABELS[d];
  b.appendChild(cv); b.appendChild(sp);
  b.onclick = () => {{ autoSpin = false; curDir = d; syncControls(); rebuildFrameGrid(false); drawAll(); }};
  strip.appendChild(b);
  stripBtns.push(b);
  stripCtxs.push(cv.getContext("2d"));
}}

// Draws either a single character frame OR the synchronized 4-character 360° Chase Squad!
function renderSceneToCtx(ctx, cw, ch, modeId, d, f) {{
  ctx.clearRect(0, 0, cw, ch);
  ctx.imageSmoothingEnabled = !pixelated;
  if (modeId === "squad_chase") {{
    const dvIm = ATLAS_IMGS["money_run"];
    const p1Im = ATLAS_IMGS["preg1_run"];
    const p2Im = ATLAS_IMGS["preg2_run"];
    const p3Im = ATLAS_IMGS["preg3_run"];
    if (!dvIm || !dvIm.complete || !p1Im || !p1Im.complete || !p2Im || !p2Im.complete || !p3Im || !p3Im.complete) return;

    // 3D local positions (lx = forward, ly = lateral): David in front (+62, 0), 3 runners fanned out chasing (-58, -88 / 0 / +88)
    const phi = d * Math.PI / 4.0;
    const actors = [
      {{ im: dvIm, lx:  58, ly:   0, sc: 0.88, fi: f % 8 }},
      {{ im: p1Im, lx: -48, ly: -94, sc: 0.80, fi: (f + 2) % 8 }},
      {{ im: p2Im, lx: -74, ly:   4, sc: 0.78, fi: (f + 5) % 8 }},
      {{ im: p3Im, lx: -48, ly:  94, sc: 0.80, fi: (f + 7) % 8 }},
    ].map(a => {{
      const sx = -a.lx * Math.sin(phi) + a.ly * Math.cos(phi);
      const dz = -a.lx * Math.cos(phi) - a.ly * Math.sin(phi);
      return {{ ...a, sx, dz }};
    }}).sort((a, b) => b.dz - a.dz);

    const scaleBase = ch / FH;
    actors.forEach(a => {{
      const psc = a.sc * (1.0 - 0.0012 * a.dz) * scaleBase;
      const dw = FW * psc, dh = FH * psc;
      const cx = cw * 0.5 + a.sx * (cw / 420.0);
      const gy = ch * 0.88 - a.dz * 0.11 * scaleBase;
      ctx.drawImage(a.im, a.fi * FW, d * FH, FW, FH, cx - dw * 0.5, gy - dh * ({gpct} / 100.0), dw, dh);
    }});
    return;
  }}

  const im = ATLAS_IMGS[modeId];
  if (!im || !im.complete || !im.naturalWidth) return;
  const nf = MODE_MAP[modeId].frames;
  const fi = ((f % nf) + nf) % nf;
  const scale = Math.min(cw / FW, ch / FH);
  const dw = FW * scale, dh = FH * scale;
  ctx.drawImage(im, fi * FW, d * FH, FW, FH, (cw - dw) * 0.5, (ch - dh) * 0.5, dw, dh);
}}

let lastGridSig = "", gridCells = [];
function rebuildFrameGrid(force) {{
  const m = MODE_MAP[curMode];
  const sig = curMode + ":" + curDir;
  if (!force && sig === lastGridSig) return;
  lastGridSig = sig;
  framegrid.innerHTML = "";
  gridCells = [];

  for (let f = 0; f < m.frames; f++) {{
    const cell = document.createElement("div");
    cell.className = "fcell";
    const cv = document.createElement("canvas");
    cv.width = 160; cv.height = 180;
    renderSceneToCtx(cv.getContext("2d"), 160, 180, curMode, curDir, f);
    const sp = document.createElement("span");
    sp.textContent = `Frame ${{f + 1}}/${{m.frames}}`;
    cell.appendChild(cv); cell.appendChild(sp);
    cell.onclick = () => {{
      playing = false; autoSpin = false; autoTour = false;
      curFrame = f; subPhase = 0;
      syncControls(); drawAll();
    }};
    framegrid.appendChild(cell);
    gridCells.push(cell);
  }}
  gridlabel.textContent = `${{LABELS[curDir]}} · ${{m.title}} (${{m.frames}} Frame${{m.frames > 1 ? "s" : ""}})`;
}}

function selectMode(id, fromTour) {{
  if (!fromTour) autoTour = false;
  curMode = id;
  const m = MODE_MAP[id];
  Object.keys(tabBtns).forEach(k => tabBtns[k].classList.toggle("on", k === id));
  curFrame = 0; subPhase = 0;
  fpsEl.value = m.fps;
  syncControls();
  rebuildFrameGrid(true);
  drawAll();
}}

function drawAll() {{
  const m = MODE_MAP[curMode];
  curDir = ((curDir % 8) + 8) % 8;
  curFrame = ((curFrame % m.frames) + m.frames) % m.frames;
  angEl.value = curDir;
  fscrub.max = Math.max(0, m.frames - 1);
  fscrub.value = curFrame;

  renderSceneToCtx(sctx, stageCanvas.width, stageCanvas.height, curMode, curDir, curFrame);
  badge.textContent = `${{LABELS[curDir]}} · ${{m.title}}`;
  meta.textContent = `Frame ${{curFrame + 1}}/${{m.frames}} · ${{fpsEl.value}} FPS`;

  for (let d = 0; d < 8; d++) {{
    renderSceneToCtx(stripCtxs[d], 160, 180, curMode, d, curFrame);
    stripBtns[d].classList.toggle("on", d === curDir);
  }}
  gridCells.forEach((c, idx) => c.classList.toggle("on", idx === curFrame));
}}

function syncControls() {{
  playBtn.textContent = playing ? "⏸ Pause" : "▶ Play";
  orbitBtn.textContent = "🔄 Auto-Orbit 360°: " + (autoSpin ? "ON" : "OFF");
  tourBtn.textContent = "🔁 Auto-Tour All Modes: " + (autoTour ? "ON" : "OFF");
  tourBtn.classList.toggle("on", autoTour);
  fpsVal.textContent = fpsEl.value + " FPS";
  pixBtn.textContent = "Filter: " + (pixelated ? "Pixelated" : "Crisp");
  stageCanvas.classList.toggle("pixel", pixelated);
  origBtn.textContent = "Origin: " + (showOrigin ? "ON" : "OFF");
  reticle.classList.toggle("on", showOrigin);
  stage.className = bgs[bgi];
  bgBtn.textContent = "BG: " + bgNames[bgi];
  wrap.style.transform = `scale(${{(+zoomEl.value || 100) / 100}})`;
}}

playBtn.onclick = () => {{ playing = !playing; syncControls(); }};
prevBtn.onclick = () => {{ playing = false; curFrame--; subPhase = 0; syncControls(); drawAll(); }};
nextBtn.onclick = () => {{ playing = false; curFrame++; subPhase = 0; syncControls(); drawAll(); }};
fscrub.oninput  = () => {{ playing = false; curFrame = +fscrub.value; subPhase = 0; syncControls(); drawAll(); }};
orbitBtn.onclick = () => {{ autoSpin = !autoSpin; syncControls(); }};
angEl.oninput = () => {{ autoSpin = false; curDir = +angEl.value; syncControls(); rebuildFrameGrid(false); drawAll(); }};
fpsEl.oninput = () => {{ syncControls(); }};
zoomEl.oninput = () => syncControls();
pixBtn.onclick = () => {{ pixelated = !pixelated; syncControls(); rebuildFrameGrid(true); drawAll(); }};
origBtn.onclick = () => {{ showOrigin = !showOrigin; syncControls(); }};
bgBtn.onclick = () => {{ bgi = (bgi + 1) % bgs.length; syncControls(); }};
tourBtn.onclick = () => {{ autoTour = !autoTour; syncControls(); }};

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
  const nd = ((dragStartDir + step) % 8 + 8) % 8;
  if (nd !== curDir) {{
    autoSpin = false; curDir = nd;
    syncControls(); rebuildFrameGrid(false); drawAll();
  }}
}});
stage.addEventListener("pointerup", () => {{ dragStartX = null; stage.classList.remove("drag"); }});
stage.addEventListener("wheel", e => {{
  e.preventDefault();
  zoomEl.value = Math.min(240, Math.max(100, (+zoomEl.value || 100) + (e.deltaY < 0 ? 15 : -15)));
  syncControls();
}}, {{ passive:false }});

window.addEventListener("keydown", e => {{
  if (e.key === "ArrowLeft")  {{ autoSpin = false; curDir--; syncControls(); rebuildFrameGrid(false); drawAll(); }}
  if (e.key === "ArrowRight") {{ autoSpin = false; curDir++; syncControls(); rebuildFrameGrid(false); drawAll(); }}
  if (e.key === "ArrowUp")    {{ playing = false; curFrame++; subPhase = 0; syncControls(); drawAll(); }}
  if (e.key === "ArrowDown")  {{ playing = false; curFrame--; subPhase = 0; syncControls(); drawAll(); }}
  if (e.key === " ")          {{ e.preventDefault(); playing = !playing; syncControls(); }}
}});

let prevTs = 0, spinAcc = 0, tourAcc = 0;
function tick(ts) {{
  if (!prevTs) prevTs = ts;
  const dt = Math.min(0.1, (ts - prevTs) / 1000.0);
  prevTs = ts;

  const fps = +fpsEl.value || 15;
  if (playing) {{
    subPhase += dt * fps;
    if (subPhase >= 1.0) {{
      const adv = Math.floor(subPhase);
      subPhase -= adv;
      curFrame = (curFrame + adv) % MODE_MAP[curMode].frames;
      drawAll();
    }}
  }}

  if (autoSpin) {{
    spinAcc += dt;
    if (spinAcc >= 0.72) {{
      spinAcc = 0;
      curDir = (curDir + 1) % 8;
      rebuildFrameGrid(false);
      drawAll();
    }}
  }}

  if (autoTour) {{
    tourAcc += dt;
    if (tourAcc >= 3.6) {{
      tourAcc = 0;
      const idx = (MODES.findIndex(x => x.id === curMode) + 1) % MODES.length;
      selectMode(MODES[idx].id, true);
    }}
  }}
  requestAnimationFrame(tick);
}}

syncControls();
rebuildFrameGrid(true);
drawAll();
requestAnimationFrame(tick);
</script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote 100% self-contained HTML: {OUT_HTML} ({OUT_HTML.stat().st_size / 1048576:.2f} MB)")


if __name__ == "__main__":
    main()
