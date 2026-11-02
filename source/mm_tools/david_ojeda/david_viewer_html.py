"""Generates interactive 360° HTML Sprite Showcases & Soundboards for
David Ojeda & the 3 Running Pregnant Hispanic Women:
  - G:\\Quake\\Combat\\BakersfieldQuake\\david_sprite\\index.html
  - G:\\Quake\\Combat\\BakersfieldQuake\\david_ojeda_sprites.html
"""

from __future__ import annotations

import os
from pathlib import Path


def render_david_showcase_html(img_prefix: str = "", snd_prefix: str = "../sound/david/") -> str:
    ground_pct = round(100.0 * 492.0 / 540.0, 2)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>David Ojeda &amp; 3 Running Pregnant Women — 360° Quake Sprite Showcase</title>
<style>
  :root {{
    --bg:#0d1017; --panel:#171c28; --panel2:#202737; --ink:#f8fafc; --dim:#94a3b8;
    --accent:#f59e0b; --accent2:#10b981; --slot:#ef4444; --sky:#38bdf8;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:12px;
    padding:18px 16px 48px; min-height:100vh;
  }}
  header {{ text-align:center; max-width:1040px; }}
  h1 {{ font-size:24px; margin:0 0 5px; font-weight:800; letter-spacing:-0.015em; }}
  .sub {{ color:var(--dim); font-size:13.5px; margin:0; }}
  .sub code {{ color:#fde68a; background:#2c2210; padding:1px 6px; border-radius:4px; }}

  .section-lbl {{
    width:min(100%, 1040px); font-size:11.5px; font-weight:800; text-transform:uppercase;
    letter-spacing:0.08em; color:var(--dim); margin:4px 0 -6px; padding-left:4px;
  }}
  .tabs {{
    display:flex; flex-wrap:wrap; gap:7px; justify-content:center;
    width:min(100%, 1040px); background:var(--panel); border:1px solid #2b3347;
    border-radius:12px; padding:8px;
  }}
  .tab {{
    flex:1 1 155px; padding:9px 10px; border-radius:8px; border:1.5px solid #313a50;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:700; font-size:12.5px;
    cursor:pointer; transition:all 0.12s ease; text-align:center;
  }}
  .tab:hover {{ border-color:#64748b; }}
  .tab.on {{
    background:#33240d; border-color:var(--accent); color:#fef3c7;
    box-shadow:0 0 14px rgba(245,158,11,0.28);
  }}
  .tab.preg.on {{
    background:#0f2d25; border-color:var(--accent2); color:#d1fae5;
    box-shadow:0 0 14px rgba(16,185,129,0.28);
  }}

  #stage {{
    width:min(100%, 1040px); height:min(64vh, 540px); min-height:380px;
    border-radius:14px; border:1px solid #353f56; position:relative;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    user-select:none; touch-action:none; cursor:grab;
  }}
  #stage.drag {{ cursor:grabbing; }}
  #stage.checker {{ background:repeating-conic-gradient(#252a36 0% 25%, #1a1e28 0% 50%) 0 0/24px 24px; }}
  #stage.casino  {{ background:radial-gradient(circle at 50% 62%, #522916 0%, #2a1310 58%, #0e090c 100%); }}
  #stage.quake   {{ background:radial-gradient(circle at 50% 70%, #3d2c1e 0%, #1b130e 68%, #090706 100%); }}
  #stage.slate   {{ background:radial-gradient(circle at 50% 55%, #1e293b 0%, #0f172a 85%); }}

  #wrap {{
    position:relative; height:94%; aspect-ratio:480/540;
    display:flex; align-items:center; justify-content:center;
  }}
  #view {{ width:100%; height:100%; object-fit:contain; pointer-events:none; }}
  #view.pixel {{ image-rendering:pixelated; }}

  #reticle {{ position:absolute; inset:0; pointer-events:none; display:none; }}
  #reticle.on {{ display:block; }}
  .gline {{ position:absolute; left:5%; right:5%; top:{ground_pct}%; border-top:1.5px dashed rgba(245,158,11,0.88); }}
  .aline {{ position:absolute; top:4%; bottom:2%; left:50%; border-left:1.5px dashed rgba(56,189,248,0.68); }}
  .odot  {{ position:absolute; left:50%; top:{ground_pct}%; width:10px; height:10px; margin:-5px 0 0 -5px; border-radius:50%; background:var(--accent); box-shadow:0 0 0 2px #0f172a; }}

  #badge {{
    position:absolute; top:12px; left:14px; background:rgba(12,15,22,0.90);
    border:1px solid #4a3c24; border-radius:8px; padding:6px 12px;
    font-size:13px; font-weight:800; color:#fde68a; pointer-events:none; z-index:5;
  }}
  #meta {{
    position:absolute; top:12px; right:14px; background:rgba(12,15,22,0.86);
    border:1px solid #3c4458; border-radius:8px; padding:5px 11px;
    font-size:12px; color:var(--dim); pointer-events:none; font-variant-numeric:tabular-nums; z-index:5;
  }}
  #draghint {{
    position:absolute; bottom:10px; right:14px; background:rgba(12,15,22,0.84);
    border:1px solid #2e3545; border-radius:6px; padding:4px 10px;
    font-size:12px; color:#cbd5e1; pointer-events:none; z-index:5;
  }}

  .row {{
    display:flex; flex-wrap:wrap; gap:10px; align-items:center; justify-content:center;
    width:min(100%, 1040px); background:var(--panel); border:1px solid #2b3347;
    border-radius:10px; padding:10px 14px;
  }}
  button.ctrl {{
    background:var(--accent); color:#1c1304; border:0; border-radius:6px;
    padding:7px 13px; font:inherit; font-weight:800; cursor:pointer;
  }}
  button.ctrl.spin {{ background:var(--sky); color:#082f49; }}
  button.ctrl.alt  {{ background:#30384a; color:var(--ink); font-weight:600; }}
  button.snd {{
    background:#242c3e; color:#e2e8f0; border:1px solid #3b4764; border-radius:7px;
    padding:7px 11px; font:inherit; font-size:12.5px; font-weight:700; cursor:pointer;
    transition:all 0.12s;
  }}
  button.snd:hover {{ border-color:var(--accent2); color:#bbf7d0; background:#152e25; }}
  label {{ color:var(--dim); display:flex; gap:6px; align-items:center; font-size:13px; }}
  input[type=range] {{ accent-color:var(--accent); cursor:pointer; }}

  #strip {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:6px; width:min(100%, 1040px);
  }}
  @media (max-width:740px) {{ #strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  #strip button {{
    padding:4px 4px 3px; background:var(--panel); border:2px solid transparent;
    border-radius:8px; display:flex; flex-direction:column; align-items:center; gap:2px;
    color:var(--dim); font-size:11px; font-weight:700; cursor:pointer;
  }}
  #strip button.on {{ border-color:var(--accent); color:var(--ink); background:#2c2314; }}
  #strip img {{ width:100%; aspect-ratio:480/540; object-fit:contain; display:block; }}

  .sheets {{
    width:min(100%, 1040px); display:flex; flex-direction:column; gap:14px; margin-top:8px;
  }}
  .card {{
    background:var(--panel); border:1px solid #2b3347; border-radius:12px; padding:14px;
  }}
  .card h2 {{ font-size:15px; margin:0 0 8px; color:#f1f5f9; }}
  .card img {{ width:100%; border-radius:8px; display:block; border:1px solid #2d3446; }}
  .gif-grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; }}
  @media (max-width:820px) {{ .gif-grid {{ grid-template-columns:repeat(2, 1fr); }} }}
</style>
</head>
<body>
  <header>
    <h1>🎰💰 David Ojeda &amp; 3 Running Pregnant Women — Full 360° Quake Sprites</h1>
    <p class="sub">
      <code>progs/david.spr32</code> (344f) &bull; <code>progs/preg_1..3.spr32</code> (56f each) &bull;
      In-Game: <code>impulse 22</code> (Full Chase Squad), <code>impulse 23</code> (Solo David),
      <code>impulse 24</code> (Slot Machine), <code>impulse 25</code> (3 Runners) &bull; Mystery Box <code>mb_force 23..26</code>
    </p>
  </header>

  <div class="section-lbl">David Ojeda — All 8 Full-360° Animations</div>
  <div class="tabs" id="davidTabs">
    <button class="tab on" data-mode="fast_run">🏃 Fast Run 360° (8&times;8f)</button>
    <button class="tab" data-mode="turbo_sprint">⚡💨 Turbo Sprint 360° (8&times;8f)</button>
    <button class="tab" data-mode="money_hold">💰💵 Holding Money Bag 360° (8&times;8f)</button>
    <button class="tab" data-mode="money_run">🏃💰 Money-Bag Heist Run 360° (8&times;8f)</button>
    <button class="tab" data-mode="slot_spin">🎰🕹️ Slot Machine Spin 360° (8&times;8f)</button>
    <button class="tab" data-mode="slot_jackpot">🎰💎 Slot 7-7-7 JACKPOT! 360° (8&times;8f)</button>
    <button class="tab" data-mode="slot_bust">🎰💢 Slot Machine BUST/Tilt 360° (8&times;8f)</button>
    <button class="tab" data-mode="idle">🧍 Standing Idle 360° (8&times;1f)</button>
  </div>

  <div class="section-lbl">3 Running Pregnant Hispanic Women — Full-360° Sprites</div>
  <div class="tabs" id="pregTabs">
    <button class="tab preg" data-mode="preg1_run">🏃‍♀️🤰 Runner #1 (Coral Top) Run 360°</button>
    <button class="tab preg" data-mode="preg2_run">🏃‍♀️🤰 Runner #2 (Teal Top) Run 360°</button>
    <button class="tab preg" data-mode="preg3_run">🏃‍♀️🤰 Runner #3 (Yellow Top) Run 360°</button>
    <button class="tab preg" data-mode="preg1_idle">🧍‍♀️ Runner #1 Idle 360°</button>
    <button class="tab preg" data-mode="preg2_idle">🧍‍♀️ Runner #2 Idle 360°</button>
    <button class="tab preg" data-mode="preg3_idle">🧍‍♀️ Runner #3 Idle 360°</button>
  </div>

  <div id="stage" class="casino">
    <div id="badge">0° Front · David Fast Run</div>
    <div id="meta">Frame 0/7</div>
    <div id="wrap">
      <img id="view" alt="360 Sprite Preview">
      <div id="reticle">
        <div class="gline"></div>
        <div class="aline"></div>
        <div class="odot"></div>
      </div>
    </div>
    <div id="draghint">↔ Drag horizontally or press ◀ / ▶ to orbit 360°</div>
  </div>

  <div class="row">
    <button class="ctrl" id="playBtn">⏸ Pause</button>
    <button class="ctrl spin" id="spinBtn">🔄 Auto-Orbit 360°: OFF</button>
    <button class="ctrl alt" id="prevDir">◀ -45°</button>
    <button class="ctrl alt" id="nextDir">+45° ▶</button>
    <label>FPS <input type="range" id="fps" min="4" max="30" value="15"><span id="fpsVal">15</span></label>
    <label>Backdrop
      <select id="bgSel" style="background:#242c3e;color:#fff;border:1px solid #3b4764;border-radius:5px;padding:4px 8px;">
        <option value="casino" selected>Golden West Casino</option>
        <option value="checker">Dark Checker</option>
        <option value="quake">Quake Dungeon</option>
        <option value="slate">Studio Slate</option>
      </select>
    </label>
    <label><input type="checkbox" id="retChk"> Origin Reticle</label>
  </div>

  <div class="row">
    <span style="color:var(--dim);font-size:12.5px;font-weight:700;">🔊 Soundboard:</span>
    <button class="snd" data-snd="shower_love.wav">🎤 "Shower Me With Your Love!"</button>
    <button class="snd" data-snd="sprint_rush.wav">💨 Fast Sprint Rush</button>
    <button class="snd" data-snd="money_bag.wav">💰 Money Bag Ka-Ching</button>
    <button class="snd" data-snd="slot_spin.wav">🎰 Slot Lever &amp; Spin</button>
    <button class="snd" data-snd="slot_jackpot.wav">💎 7-7-7 JACKPOT!</button>
    <button class="snd" data-snd="slot_bust.wav">💢 Slot BUST Buzzer</button>
  </div>

  <div id="strip"></div>

  <div class="sheets">
    <div class="card">
      <h2>🕹️ Live In-Game DarkPlaces Verification (<code>map start</code> &bull; <code>impulse 22 / 24</code>)</h2>
      <div class="gif-grid" style="grid-template-columns:repeat(2, 1fr);">
        <img src="{img_prefix}david_ig_1_squad.png" alt="In-game Money Bag Sprint & Squad">
        <img src="{img_prefix}david_ig_2_slot_jackpot.png" alt="In-game Slot Machine 777 Jackpot">
        <img src="{img_prefix}david_ig_3_slot_spin_360.png" alt="In-game Slot Machine 360 Spin">
        <img src="{img_prefix}david_ig_4_live_chase.png" alt="In-game 3 Pregnant Runners Live Chase">
      </div>
    </div>
    <div class="card">
      <h2>🔄 Animated 360° Turntable Showcase GIFs</h2>
      <div class="gif-grid">
        <img src="{img_prefix}david_fast_run_360.gif" alt="David Fast Run 360 GIF">
        <img src="{img_prefix}david_money_bag_360.gif" alt="David Money Bag 360 GIF">
        <img src="{img_prefix}david_slot_machine_360.gif" alt="David Slot Machine 360 GIF">
        <img src="{img_prefix}pregnant_runners_360.gif" alt="3 Pregnant Runners 360 GIF">
      </div>
    </div>
    <div class="card">
      <h2>📋 David Ojeda — Master 360° Animations Contact Sheet</h2>
      <img src="{img_prefix}david_360_turnaround_sheet.png" alt="David 360 Turnaround Sheet">
    </div>
    <div class="card">
      <h2>📋 3 Running Pregnant Hispanic Women — Master 360° Running Sheet</h2>
      <img src="{img_prefix}pregnant_runners_360_sheet.png" alt="3 Pregnant Runners 360 Sheet">
    </div>
  </div>

<script>
const IMG_PRE = {img_prefix!r};
const SND_PRE = {snd_prefix!r};
const DIRS = ["0° Front","45° Front-L","90° Left","135° Back-L","180° Back","225° Back-R","270° Right","315° Front-R"];
const MODES = {{
  fast_run:     {{ label:"David Fast Run",             fn:(d,f)=>`${{IMG_PRE}}david_fast_run_d${{d}}_f${{f}}.png`,     nf:8 }},
  turbo_sprint: {{ label:"David Turbo Sprint",         fn:(d,f)=>`${{IMG_PRE}}david_turbo_sprint_d${{d}}_f${{f}}.png`, nf:8 }},
  money_hold:   {{ label:"Holding Bag of Money",       fn:(d,f)=>`${{IMG_PRE}}david_money_hold_d${{d}}_f${{f}}.png`,   nf:8 }},
  money_run:    {{ label:"Running w/ Bag of Money",    fn:(d,f)=>`${{IMG_PRE}}david_money_run_d${{d}}_f${{f}}.png`,    nf:8 }},
  slot_spin:    {{ label:"Slot Machine Spin",          fn:(d,f)=>`${{IMG_PRE}}david_slot_spin_d${{d}}_f${{f}}.png`,    nf:8 }},
  slot_jackpot: {{ label:"Slot 7-7-7 JACKPOT!",        fn:(d,f)=>`${{IMG_PRE}}david_slot_jackpot_d${{d}}_f${{f}}.png`, nf:8 }},
  slot_bust:    {{ label:"Slot Machine BUST / Tilt",   fn:(d,f)=>`${{IMG_PRE}}david_slot_bust_d${{d}}_f${{f}}.png`,    nf:8 }},
  idle:         {{ label:"David Standing Idle",        fn:(d,f)=>`${{IMG_PRE}}david_idle_d${{d}}.png`,                 nf:1 }},
  preg1_run:    {{ label:"Runner #1 (Coral) Running",  fn:(d,f)=>`${{IMG_PRE}}preg1_run_d${{d}}_f${{f}}.png`,          nf:8 }},
  preg2_run:    {{ label:"Runner #2 (Teal) Running",   fn:(d,f)=>`${{IMG_PRE}}preg2_run_d${{d}}_f${{f}}.png`,          nf:8 }},
  preg3_run:    {{ label:"Runner #3 (Yellow) Running", fn:(d,f)=>`${{IMG_PRE}}preg3_run_d${{d}}_f${{f}}.png`,          nf:8 }},
  preg1_idle:   {{ label:"Runner #1 Standing Idle",    fn:(d,f)=>`${{IMG_PRE}}preg1_idle_d${{d}}.png`,                 nf:1 }},
  preg2_idle:   {{ label:"Runner #2 Standing Idle",    fn:(d,f)=>`${{IMG_PRE}}preg2_idle_d${{d}}.png`,                 nf:1 }},
  preg3_idle:   {{ label:"Runner #3 Standing Idle",    fn:(d,f)=>`${{IMG_PRE}}preg3_idle_d${{d}}.png`,                 nf:1 }},
}};

let curMode = "fast_run", curDir = 0, curFrame = 0, playing = true, autoSpin = false, fps = 15;
let lastTick = performance.now(), spinStep = 0;

const viewEl = document.getElementById("view");
const badgeEl = document.getElementById("badge");
const metaEl = document.getElementById("meta");
const stripEl = document.getElementById("strip");
const stageEl = document.getElementById("stage");

function rebuildStrip() {{
  stripEl.innerHTML = "";
  const m = MODES[curMode];
  for (let d = 0; d < 8; d++) {{
    const b = document.createElement("button");
    if (d === curDir) b.className = "on";
    const im = document.createElement("img");
    im.src = m.fn(d, 0);
    const sp = document.createElement("span");
    sp.textContent = DIRS[d];
    b.appendChild(im);
    b.appendChild(sp);
    b.onclick = () => {{ curDir = d; syncStrip(); drawNow(); }};
    stripEl.appendChild(b);
  }}
}}

function syncStrip() {{
  [...stripEl.children].forEach((b, i) => b.classList.toggle("on", i === curDir));
}}

function drawNow() {{
  const m = MODES[curMode];
  const f = curFrame % m.nf;
  viewEl.src = m.fn(curDir, f);
  badgeEl.textContent = `${{DIRS[curDir]}} · ${{m.label}}`;
  metaEl.textContent = `Frame ${{f + 1}}/${{m.nf}}`;
}}

document.querySelectorAll(".tab").forEach(btn => {{
  btn.onclick = () => {{
    document.querySelectorAll(".tab").forEach(x => x.classList.remove("on"));
    btn.classList.add("on");
    curMode = btn.dataset.mode;
    curFrame = 0;
    rebuildStrip();
    drawNow();
  }};
}});

document.getElementById("playBtn").onclick = e => {{
  playing = !playing;
  e.target.textContent = playing ? "⏸ Pause" : "▶ Play";
}};
document.getElementById("spinBtn").onclick = e => {{
  autoSpin = !autoSpin;
  e.target.textContent = `🔄 Auto-Orbit 360°: ${{autoSpin ? "ON" : "OFF"}}`;
}};
document.getElementById("prevDir").onclick = () => {{ curDir = (curDir + 7) % 8; syncStrip(); drawNow(); }};
document.getElementById("nextDir").onclick = () => {{ curDir = (curDir + 1) % 8; syncStrip(); drawNow(); }};
document.getElementById("fps").oninput = e => {{ fps = +e.target.value; document.getElementById("fpsVal").textContent = fps; }};
document.getElementById("bgSel").onchange = e => {{ stageEl.className = e.target.value; }};
document.getElementById("retChk").onchange = e => {{ document.getElementById("reticle").classList.toggle("on", e.target.checked); }};

document.querySelectorAll("button.snd").forEach(b => {{
  b.onclick = () => {{ const a = new Audio(SND_PRE + b.dataset.snd); a.play(); }};
}});

let dragX = null, dragStartDir = 0;
stageEl.addEventListener("pointerdown", e => {{
  dragX = e.clientX; dragStartDir = curDir;
  stageEl.classList.add("drag");
  stageEl.setPointerCapture(e.pointerId);
}});
stageEl.addEventListener("pointermove", e => {{
  if (dragX === null) return;
  const steps = Math.round((e.clientX - dragX) / 42);
  const nd = ((dragStartDir + steps) % 8 + 8) % 8;
  if (nd !== curDir) {{ curDir = nd; syncStrip(); drawNow(); }}
}});
stageEl.addEventListener("pointerup", () => {{ dragX = null; stageEl.classList.remove("drag"); }});
window.addEventListener("keydown", e => {{
  if (e.key === "ArrowLeft") {{ curDir = (curDir + 7) % 8; syncStrip(); drawNow(); }}
  if (e.key === "ArrowRight") {{ curDir = (curDir + 1) % 8; syncStrip(); drawNow(); }}
}});

function loop(now) {{
  if (playing && now - lastTick >= 1000 / fps) {{
    lastTick = now;
    curFrame = (curFrame + 1) % MODES[curMode].nf;
    if (autoSpin) {{
      spinStep++;
      if (spinStep % 3 === 0) {{ curDir = (curDir + 1) % 8; syncStrip(); }}
    }}
    drawNow();
  }}
  requestAnimationFrame(loop);
}}

rebuildStrip();
drawNow();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""


def write_david_showcases(mod_dir: Path) -> None:
    web_dir = mod_dir / "david_sprite"
    web_dir.mkdir(parents=True, exist_ok=True)
    (web_dir / "index.html").write_text(render_david_showcase_html("", "../sound/david/"), encoding="utf-8")
    (mod_dir / "david_ojeda_sprites.html").write_text(render_david_showcase_html("david_sprite/", "sound/david/"), encoding="utf-8")
