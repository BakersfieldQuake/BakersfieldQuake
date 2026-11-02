"""Generates both the directory-local `rubber_finger_sprite/index.html` and the 100% self-contained
single-file `rubber_finger_sprite.html` showcase viewer (all frames embedded as lossless base64 data URIs)."""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from PIL import Image


def _encode_lossless_webp_uri(png_path: Path) -> str:
    """Encodes an RGBA PNG into a 100% lossless RGBA WebP data URI (~3.5x smaller than PNG, zero quality loss)."""
    im = Image.open(png_path).convert("RGBA")
    buf = io.BytesIO()
    im.save(buf, format="WEBP", lossless=True, quality=100, method=4)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{b64}"


def _encode_raw_uri(path: Path, mime: str) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_asset_map(sprite_dir: Path, self_contained: bool, asset_prefix: str = ".") -> dict[str, str]:
    """Builds a logical key -> URL/data-URI map for every sprite frame, GIF, and master sheet."""
    pfx = asset_prefix.rstrip("/")
    assets: dict[str, str] = {}

    for d in range(8):
        k_idle = f"idle_d{d}"
        p_idle = sprite_dir / f"finger_idle_d{d}.png"
        assets[k_idle] = _encode_lossless_webp_uri(p_idle) if self_contained else f"{pfx}/finger_idle_d{d}.png"

        for f in range(8):
            k_run = f"run_d{d}_f{f}"
            p_run = sprite_dir / f"finger_d{d}_f{f}.png"
            assets[k_run] = _encode_lossless_webp_uri(p_run) if self_contained else f"{pfx}/finger_d{d}_f{f}.png"

    for f in range(8):
        k_bonk = f"bonk_{f:02d}"
        p_bonk = sprite_dir / f"finger_bonk_{f:02d}.png"
        assets[k_bonk] = _encode_lossless_webp_uri(p_bonk) if self_contained else f"{pfx}/finger_bonk_{f:02d}.png"

    for i in range(56):
        k_spr = f"spr_{i:02d}"
        p_spr = sprite_dir / "spr32" / f"f_{i:02d}.png"
        assets[k_spr] = _encode_raw_uri(p_spr, "image/png") if self_contained else f"{pfx}/spr32/f_{i:02d}.png"

    p_gif = sprite_dir / "rubber_finger_360_spin.gif"
    assets["spin_gif"] = _encode_raw_uri(p_gif, "image/gif") if self_contained else f"{pfx}/rubber_finger_360_spin.gif"

    p_sheet = sprite_dir / "rubber_finger_360_sheet_8x8.png"
    assets["sheet_8x8"] = _encode_lossless_webp_uri(p_sheet) if self_contained else f"{pfx}/rubber_finger_360_sheet_8x8.png"

    return assets


def render_rubber_finger_viewer_html(
    asset_prefix: str = ".",
    sprite_dir: Path | None = None,
    self_contained: bool = False,
) -> str:
    """Returns a complete interactive HTML viewer.
    When `self_contained=True` and `sprite_dir` is provided, every single image/GIF/sheet is embedded inline!
    """
    if self_contained:
        if sprite_dir is None:
            sprite_dir = Path(__file__).resolve().parent.parent.parent / "rubber_finger_sprite"
        assets = build_asset_map(sprite_dir, self_contained=True)
        badge_extra = "2D Digitized Sprite • 100% Self-Contained Inspector"
    else:
        if sprite_dir is None:
            sprite_dir = Path(__file__).resolve().parent.parent.parent / "rubber_finger_sprite"
        assets = build_asset_map(sprite_dir, self_contained=False, asset_prefix=asset_prefix)
        badge_extra = "2D Digitized 360° Sprite + .SPR32"

    assets_json = json.dumps(assets, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Crazy Floppy Worm / Rubber Finger Maniac — 2D Digitized 360° Sprite Inspector</title>
<style>
  :root {{
    --bg: #0b0d13;
    --panel: #141823;
    --panel-2: #1c2232;
    --border: #2c354d;
    --accent: #ff9d3b;
    --accent-2: #4fd1ff;
    --text: #eef2ff;
    --muted: #9aa6c4;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 22px 18px 56px;
    background: radial-gradient(circle at 50% 0%, #1a2135 0%, var(--bg) 68%);
    color: var(--text);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  .wrap {{ max-width: 1260px; margin: 0 auto; }}
  header {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border);
  }}
  h1 {{
    margin: 0;
    font-size: 1.6rem;
    letter-spacing: -0.02em;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
  }}
  .badge {{
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(255, 157, 59, 0.16);
    border: 1px solid rgba(255, 157, 59, 0.45);
    color: var(--accent);
  }}
  .sub {{
    margin: 5px 0 0;
    color: var(--muted);
    font-size: 0.92rem;
  }}
  .grid-top {{
    display: grid;
    grid-template-columns: 1.45fr 1fr;
    gap: 18px;
    align-items: start;
  }}
  @media (max-width: 960px) {{
    .grid-top {{ grid-template-columns: 1fr; }}
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.42);
  }}
  .tabs {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }}
  button {{
    background: var(--panel-2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 7px 12px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.14s ease;
  }}
  button:hover {{ border-color: var(--accent); }}
  button.active {{
    background: linear-gradient(180deg, #ffae52, #e97a17);
    color: #111319;
    border-color: #ffc278;
    box-shadow: 0 0 16px rgba(255, 157, 59, 0.35);
  }}
  .stage {{
    position: relative;
    height: 560px;
    border-radius: 12px;
    border: 1px solid var(--border);
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    user-select: none;
    cursor: grab;
  }}
  .stage:active {{ cursor: grabbing; }}
  .bg-checker {{
    background-color: #1a1e29;
    background-image:
      linear-gradient(45deg, #252b3b 25%, transparent 25%),
      linear-gradient(-45deg, #252b3b 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #252b3b 75%),
      linear-gradient(-45deg, transparent 75%, #252b3b 75%);
    background-size: 28px 28px;
    background-position: 0 0, 0 14px, 14px -14px, -14px 0;
  }}
  .bg-quake {{
    background:
      radial-gradient(ellipse at 50% 78%, rgba(255, 130, 40, 0.2), transparent 60%),
      linear-gradient(180deg, #1b1410 0%, #2b1f17 68%, #16100c 100%);
  }}
  .bg-slate {{
    background: radial-gradient(circle at 50% 42%, #2b3347 0%, #111520 78%);
  }}
  .bg-light {{
    background: radial-gradient(circle at 50% 45%, #f4f6fb 0%, #cfd6e6 100%);
  }}
  #spriteImg {{
    height: 88%;
    width: auto;
    object-fit: contain;
    pointer-events: none;
    transform-origin: center 93%;
    transition: transform 0.06s ease-out;
  }}
  #spriteImg.pixelated {{
    image-rendering: pixelated;
    height: 78%;
  }}
  .hud-overlay {{
    position: absolute;
    top: 12px;
    left: 12px;
    right: 12px;
    display: flex;
    justify-content: space-between;
    pointer-events: none;
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    font-size: 0.8rem;
    z-index: 3;
  }}
  .hud-tag {{
    background: rgba(10, 12, 18, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 5px 10px;
    border-radius: 7px;
    color: #dfe7ff;
  }}
  .origin-reticle {{
    position: absolute;
    left: 50%;
    bottom: 8.8%;
    width: 150px;
    height: 2px;
    background: rgba(79, 209, 255, 0.85);
    transform: translateX(-50%);
    pointer-events: none;
    z-index: 2;
  }}
  .origin-reticle::after {{
    content: "SPR32 FEET ORIGIN (0,0,0)";
    position: absolute;
    top: 5px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 10px;
    font-family: monospace;
    color: var(--accent-2);
    white-space: nowrap;
  }}
  .orbit-strip {{
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 6px;
    margin-top: 12px;
  }}
  .orbit-btn {{
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 5px 4px;
    border-radius: 9px;
    background: var(--panel-2);
    border: 1px solid var(--border);
    cursor: pointer;
  }}
  .orbit-btn img {{
    width: 100%;
    height: 68px;
    object-fit: contain;
    pointer-events: none;
  }}
  .orbit-btn span {{
    font-size: 0.72rem;
    color: var(--muted);
    margin-top: 3px;
  }}
  .orbit-btn.active {{
    border-color: var(--accent);
    background: rgba(255, 157, 59, 0.14);
    box-shadow: inset 0 0 0 1px var(--accent);
  }}
  .orbit-btn.active span {{ color: var(--accent); font-weight: 700; }}
  .ctrl-group {{
    margin-bottom: 14px;
    padding-bottom: 13px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  }}
  .ctrl-group:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
  .ctrl-label {{
    font-size: 0.77rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
  }}
  .row {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
  input[type="range"] {{ width: 100%; accent-color: var(--accent); cursor: pointer; }}
  .sheet-card {{ margin-top: 20px; }}
  .sheet-img {{
    width: 100%;
    height: auto;
    border-radius: 10px;
    border: 1px solid var(--border);
    display: block;
  }}
  .bonk-strip {{
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 8px;
    margin-top: 10px;
  }}
  .bonk-cell {{
    background: #1a1f2e;
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 4px;
    cursor: pointer;
    text-align: center;
    transition: border-color 0.14s;
  }}
  .bonk-cell:hover, .bonk-cell.active {{ border-color: var(--accent); }}
  .bonk-cell img {{ width: 100%; height: auto; display: block; }}
  .bonk-cell span {{ font-size: 0.72rem; color: var(--muted); font-family: monospace; }}
  code {{
    background: #0d1018;
    padding: 2px 6px;
    border-radius: 5px;
    color: var(--accent-2);
    font-size: 0.83rem;
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>
        <span>🤪🪱 Crazy Floppy Worm Maniac (2D Digitized Sprite)</span>
        <span class="badge">{badge_extra}</span>
      </h1>
      <p class="sub">
        Drag left/right on stage to orbit 360° &bull; Scroll wheel or slider to zoom &bull;
        Keys: <code>Space</code> Play/Pause, <code>&larr;</code>/<code>&rarr;</code> Angle, <code>[</code>/<code>]</code> Step Frame
      </p>
    </div>
    <div class="hud-tag">Quake DarkPlaces Sprite: <code>progs/fr_finger.spr32</code> (56 frames, 128&times;144)</div>
  </header>

  <div class="grid-top">
    <div class="card">
      <div class="tabs" id="modeTabs">
        <button data-mode="wag" class="active">🤪 360° Crazy Wag-Run (8&times;8)</button>
        <button data-mode="spin">🌀 Auto 360° Turntable</button>
        <button data-mode="bonk">🤦 "FOREHEAD BONK!" Solo (8f)</button>
        <button data-mode="idle">🧍 360° Crazed Idle (8d)</button>
        <button data-mode="spr32">👾 Quake .SPR32 Pixelated</button>
      </div>

      <div class="stage bg-checker" id="stage">
        <div class="hud-overlay">
          <div class="hud-tag" id="hudLeft">Angle: d0 (0° Front)</div>
          <div class="hud-tag" id="hudRight">Frame: 0 / 7</div>
        </div>
        <img id="spriteImg" alt="Crazy Rubber Finger Sprite" />
        <div class="origin-reticle" id="reticle" style="display:none;"></div>
      </div>

      <div class="orbit-strip" id="orbitStrip"></div>
    </div>

    <div class="card">
      <div class="ctrl-group">
        <div class="ctrl-label">
          <span>Playback &amp; Scrubber</span>
          <span id="fpsLabel">11 FPS</span>
        </div>
        <div class="row" style="margin-bottom:10px;">
          <button id="btnPlay">⏸ Pause</button>
          <button id="btnPrev">&laquo; Prev</button>
          <button id="btnNext">Next &raquo;</button>
        </div>
        <div class="ctrl-label" style="margin-top:6px;">
          <span>Animation Speed</span>
          <span>2 – 24 FPS</span>
        </div>
        <input type="range" id="fpsRange" min="2" max="24" value="11" />
        <div class="ctrl-label" style="margin-top:10px;">
          <span>Frame Scrubber</span>
          <span id="scrubLabel">Frame 0</span>
        </div>
        <input type="range" id="frameScrub" min="0" max="7" value="0" />
      </div>

      <div class="ctrl-group">
        <div class="ctrl-label">
          <span>Inspector Zoom</span>
          <span id="zoomLabel">100%</span>
        </div>
        <input type="range" id="zoomRange" min="50" max="240" value="100" />
      </div>

      <div class="ctrl-group">
        <div class="ctrl-label"><span>Backdrop &amp; Pixel Filters</span></div>
        <div class="row">
          <button data-bg="bg-checker" class="bg-btn active">Checker</button>
          <button data-bg="bg-quake" class="bg-btn">Quake Dungeon</button>
          <button data-bg="bg-slate" class="bg-btn">Slate</button>
          <button data-bg="bg-light" class="bg-btn">Light</button>
        </div>
        <div class="row" style="margin-top:9px;">
          <button id="btnPixel">🔍 Nearest-Neighbor Off</button>
          <button id="btnReticle">🎯 Feet Reticle Off</button>
          <button id="btnResetZoom">↺ Reset Zoom</button>
        </div>
      </div>

      <div class="ctrl-group">
        <div class="ctrl-label"><span>Embedded 360° Showcase GIF</span></div>
        <img id="gifPreview" alt="360 Spin GIF" class="sheet-img bg-slate" style="max-height:225px; object-fit:contain;" />
      </div>
    </div>
  </div>

  <div class="card sheet-card">
    <div class="ctrl-label">
      <span>🤦 Signature 8-Frame "FOREHEAD BONK!" Action Strip (Click any frame to inspect)</span>
      <span>Photo 1 &rarr; Whip &rarr; Photo 2 Forehead Bonk!</span>
    </div>
    <div class="bonk-strip" id="bonkStrip"></div>
  </div>

  <div class="card sheet-card">
    <div class="ctrl-label">
      <span>Master 360° Sprite Sheet — 8 Angles (Rows d0..d7) &times; 8 Crazy Wag-Run Frames (Cols f0..f7)</span>
      <span>Click anywhere on sheet to jump to that angle &amp; frame!</span>
    </div>
    <img id="sheetPreview" alt="8x8 360 Master Sprite Sheet" class="sheet-img bg-checker" style="cursor:crosshair;" />
  </div>
</div>

<script>
const ASSETS = {assets_json};

(() => {{
  const DIR_NAMES = [
    "d0 (0° Front)",
    "d1 (45° Front-Left)",
    "d2 (90° Left Profile)",
    "d3 (135° Back-Left)",
    "d4 (180° Back)",
    "d5 (225° Back-Right)",
    "d6 (270° Right Profile)",
    "d7 (315° Front-Right)"
  ];
  const SHORT_DIRS = ["0° Front", "45° FL", "90° Left", "135° BL", "180° Back", "225° BR", "270° Right", "315° FR"];

  let mode = "wag";
  let dir = 0;
  let frame = 0;
  let playing = true;
  let fps = 11;
  let zoom = 100;
  let spinTick = 0;
  let pixelated = false;
  let showReticle = false;

  const imgEl = document.getElementById("spriteImg");
  const stageEl = document.getElementById("stage");
  const hudLeft = document.getElementById("hudLeft");
  const hudRight = document.getElementById("hudRight");
  const modeBtns = [...document.querySelectorAll("#modeTabs button")];
  const frameScrub = document.getElementById("frameScrub");
  const scrubLabel = document.getElementById("scrubLabel");

  document.getElementById("gifPreview").src = ASSETS.spin_gif;
  const sheetEl = document.getElementById("sheetPreview");
  sheetEl.src = ASSETS.sheet_8x8;

  // Build live 8-angle thumbnail orbit strip
  const orbitStrip = document.getElementById("orbitStrip");
  const orbitBtns = [];
  const orbitThumbImgs = [];
  for (let d = 0; d < 8; d++) {{
    const btn = document.createElement("div");
    btn.className = "orbit-btn" + (d === 0 ? " active" : "");
    const im = document.createElement("img");
    im.src = ASSETS[`run_d${{d}}_f0`];
    const lbl = document.createElement("span");
    lbl.textContent = SHORT_DIRS[d];
    btn.appendChild(im);
    btn.appendChild(lbl);
    btn.addEventListener("click", () => {{
      dir = d;
      if (mode === "bonk" || mode === "spin") setMode("wag");
      render();
    }});
    orbitStrip.appendChild(btn);
    orbitBtns.push(btn);
    orbitThumbImgs.push(im);
  }}

  // Build clickable 8-frame Forehead Bonk Strip
  const bonkStrip = document.getElementById("bonkStrip");
  const bonkCells = [];
  for (let f = 0; f < 8; f++) {{
    const cell = document.createElement("div");
    cell.className = "bonk-cell";
    const im = document.createElement("img");
    im.src = ASSETS[`bonk_0${{f}}`];
    const sp = document.createElement("span");
    sp.textContent = f === 5 || f === 6 ? `f${{f}} *BONK!*` : `f${{f}}`;
    cell.appendChild(im);
    cell.appendChild(sp);
    cell.addEventListener("click", () => {{
      setMode("bonk");
      playing = false;
      document.getElementById("btnPlay").textContent = "▶ Play";
      frame = f;
      render();
      stageEl.scrollIntoView({{ behavior: "smooth", block: "nearest" }});
    }});
    bonkStrip.appendChild(cell);
    bonkCells.push(cell);
  }}

  // Click anywhere on the 8x8 sheet to inspect that exact (d, f) cell!
  sheetEl.addEventListener("click", (e) => {{
    const rect = sheetEl.getBoundingClientRect();
    const col = Math.min(7, Math.max(0, Math.floor(((e.clientX - rect.left) / rect.width) * 8)));
    const row = Math.min(7, Math.max(0, Math.floor(((e.clientY - rect.top) / rect.height) * 8)));
    dir = row;
    frame = col;
    setMode("wag");
    playing = false;
    document.getElementById("btnPlay").textContent = "▶ Play";
    render();
    stageEl.scrollIntoView({{ behavior: "smooth", block: "center" }});
  }});

  function render() {{
    const f8 = ((frame % 8) + 8) % 8;
    if (mode === "wag" || mode === "spin") {{
      imgEl.src = ASSETS[`run_d${{dir}}_f${{f8}}`];
      hudLeft.textContent = `Angle: ${{DIR_NAMES[dir]}}`;
      hudRight.textContent = `Wag-Run Frame: ${{f8}} / 7`;
      frameScrub.max = 7;
      frameScrub.value = f8;
      scrubLabel.textContent = `Frame ${{f8}} / 7`;
    }} else if (mode === "bonk") {{
      imgEl.src = ASSETS[`bonk_0${{f8}}`];
      hudLeft.textContent = `Solo Action: FOREHEAD BONK! (0° Front)`;
      hudRight.textContent = `Bonk Frame: ${{f8}} / 7`;
      frameScrub.max = 7;
      frameScrub.value = f8;
      scrubLabel.textContent = `Bonk ${{f8}} / 7`;
    }} else if (mode === "idle") {{
      imgEl.src = ASSETS[`idle_d${{dir}}`];
      hudLeft.textContent = `Angle: ${{DIR_NAMES[dir]}}`;
      hudRight.textContent = `Crazed Idle Pose`;
      scrubLabel.textContent = `Idle (${{SHORT_DIRS[dir]}})`;
    }} else if (mode === "spr32") {{
      const f6 = ((frame % 6) + 6) % 6;
      const idx = 8 + dir * 6 + f6;
      imgEl.src = ASSETS[`spr_${{String(idx).padStart(2, "0")}}`];
      hudLeft.textContent = `SPR32 Angle: ${{DIR_NAMES[dir]}}`;
      hudRight.textContent = `SPR32 Frame #${{idx}} (run ${{f6}}/5)`;
      frameScrub.max = 5;
      frameScrub.value = f6;
      scrubLabel.textContent = `SPR32 Run ${{f6}} / 5`;
    }}

    // Live-animate all 8 angle thumbnails in the orbit strip!
    for (let k = 0; k < 8; k++) {{
      orbitThumbImgs[k].src = mode === "idle" ? ASSETS[`idle_d${{k}}`] : ASSETS[`run_d${{k}}_f${{f8}}`];
      orbitBtns[k].classList.toggle("active", k === dir);
    }}
    bonkCells.forEach((c, idx) => c.classList.toggle("active", mode === "bonk" && idx === f8));

    const forcePix = pixelated || mode === "spr32";
    imgEl.classList.toggle("pixelated", forcePix);
    imgEl.style.transform = `scale(${{(zoom / 100).toFixed(2)}})`;
  }}

  function setMode(m) {{
    mode = m;
    modeBtns.forEach(b => b.classList.toggle("active", b.dataset.mode === m));
    render();
  }}

  modeBtns.forEach(b => b.addEventListener("click", () => setMode(b.dataset.mode)));

  document.getElementById("btnPlay").addEventListener("click", (e) => {{
    playing = !playing;
    e.target.textContent = playing ? "⏸ Pause" : "▶ Play";
  }});
  document.getElementById("btnPrev").addEventListener("click", () => {{
    playing = false;
    document.getElementById("btnPlay").textContent = "▶ Play";
    frame = frame - 1;
    render();
  }});
  document.getElementById("btnNext").addEventListener("click", () => {{
    playing = false;
    document.getElementById("btnPlay").textContent = "▶ Play";
    frame = frame + 1;
    render();
  }});
  document.getElementById("fpsRange").addEventListener("input", (e) => {{
    fps = parseInt(e.target.value, 10);
    document.getElementById("fpsLabel").textContent = `${{fps}} FPS`;
  }});
  frameScrub.addEventListener("input", (e) => {{
    playing = false;
    document.getElementById("btnPlay").textContent = "▶ Play";
    frame = parseInt(e.target.value, 10);
    render();
  }});

  const zoomRange = document.getElementById("zoomRange");
  const zoomLabel = document.getElementById("zoomLabel");
  function setZoom(z) {{
    zoom = Math.min(240, Math.max(50, z));
    zoomRange.value = zoom;
    zoomLabel.textContent = `${{zoom}}%`;
    render();
  }}
  zoomRange.addEventListener("input", (e) => setZoom(parseInt(e.target.value, 10)));
  document.getElementById("btnResetZoom").addEventListener("click", () => setZoom(100));
  stageEl.addEventListener("wheel", (e) => {{
    e.preventDefault();
    setZoom(zoom + (e.deltaY < 0 ? 10 : -10));
  }}, {{ passive: false }});

  document.querySelectorAll(".bg-btn").forEach(btn => {{
    btn.addEventListener("click", () => {{
      document.querySelectorAll(".bg-btn").forEach(x => x.classList.remove("active"));
      btn.classList.add("active");
      stageEl.className = `stage ${{btn.dataset.bg}}`;
    }});
  }});

  document.getElementById("btnPixel").addEventListener("click", (e) => {{
    pixelated = !pixelated;
    e.target.textContent = pixelated ? "🔍 Nearest-Neighbor On" : "🔍 Nearest-Neighbor Off";
    e.target.classList.toggle("active", pixelated);
    render();
  }});

  document.getElementById("btnReticle").addEventListener("click", (e) => {{
    showReticle = !showReticle;
    document.getElementById("reticle").style.display = showReticle ? "block" : "none";
    e.target.textContent = showReticle ? "🎯 Feet Reticle On" : "🎯 Feet Reticle Off";
    e.target.classList.toggle("active", showReticle);
  }});

  // Drag-to-orbit 360° on the stage
  let dragging = false;
  let dragStartX = 0;
  let dragStartDir = 0;
  stageEl.addEventListener("pointerdown", (e) => {{
    dragging = true;
    dragStartX = e.clientX;
    dragStartDir = dir;
    stageEl.setPointerCapture(e.pointerId);
  }});
  stageEl.addEventListener("pointermove", (e) => {{
    if (!dragging) return;
    const dx = e.clientX - dragStartX;
    const step = Math.round(dx / 38);
    const nextDir = ((dragStartDir - step) % 8 + 8) % 8;
    if (nextDir !== dir) {{
      dir = nextDir;
      if (mode === "bonk") setMode("wag");
      render();
    }}
  }});
  stageEl.addEventListener("pointerup", () => {{ dragging = false; }});

  window.addEventListener("keydown", (e) => {{
    if (e.code === "Space") {{
      e.preventDefault();
      document.getElementById("btnPlay").click();
    }} else if (e.code === "ArrowLeft") {{
      dir = (dir + 1) % 8;
      render();
    }} else if (e.code === "ArrowRight") {{
      dir = (dir + 7) % 8;
      render();
    }} else if (e.key === "[") {{
      document.getElementById("btnPrev").click();
    }} else if (e.key === "]") {{
      document.getElementById("btnNext").click();
    }}
  }});

  let lastTime = performance.now();
  function tick(now) {{
    if (playing && (now - lastTime) >= (1000 / fps)) {{
      lastTime = now;
      frame = (frame + 1) % 2400;
      if (mode === "spin") {{
        spinTick = (spinTick + 1) % 3;
        if (spinTick === 0) dir = (dir + 1) % 8;
      }} else if (mode === "idle") {{
        spinTick = (spinTick + 1) % 4;
        if (spinTick === 0) dir = (dir + 1) % 8;
      }}
      render();
    }}
    requestAnimationFrame(tick);
  }}
  render();
  requestAnimationFrame(tick);
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent.parent
    spr_dir = root / "rubber_finger_sprite"
    out_standalone = root / "rubber_finger_sprite.html"
    out_local = spr_dir / "index.html"

    html_standalone = render_rubber_finger_viewer_html(sprite_dir=spr_dir, self_contained=True)
    out_standalone.write_text(html_standalone, encoding="utf-8")
    print(f"Wrote 100% self-contained HTML: {out_standalone} ({out_standalone.stat().st_size / (1024*1024):.2f} MB)")

    html_local = render_rubber_finger_viewer_html(".", sprite_dir=spr_dir, self_contained=False)
    out_local.write_text(html_local, encoding="utf-8")
    print(f"Wrote folder index.html:        {out_local} ({out_local.stat().st_size / 1024:.1f} KB)")
