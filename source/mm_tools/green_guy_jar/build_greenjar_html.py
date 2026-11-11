"""Builds the 100% Self-Contained Single-File HTML5 Showcase (`green_guy_jar_weapon.html`)
for the 'Jar o' Green Guys' Weapon (embeds all 8 60-FPS WebP sprite atlases + all 12 real helium `.wav` clips!),
and polishes `green_guy_jar_weapon/greenjar_poster.jpg` with crisp Windows TrueType typography.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PACK_DIR = os.path.join(MOD_ROOT, "green_guy_jar_weapon")
ATLAS_DIR = os.path.join(PACK_DIR, "atlases")
SND_DIR = os.path.join(MOD_ROOT, "sound", "greenjar")
OUT_HTML = os.path.join(MOD_ROOT, "green_guy_jar_weapon.html")


def _b64_file(path: str, mime: str) -> str:
    with open(path, "rb") as f:
        enc = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{enc}"


def upgrade_poster_typography() -> None:
    """Re-renders clean TrueType header & footer banners on `greenjar_poster.jpg` with zero missing-glyph boxes."""
    p_path = os.path.join(PACK_DIR, "greenjar_poster.jpg")
    if not os.path.exists(p_path):
        return
    im = Image.open(p_path).convert("RGB")
    W, H = im.size
    dr = ImageDraw.Draw(im)

    def _font(sz: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = (
            [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
            if bold
            else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
        )
        for fp in candidates:
            if os.path.exists(fp):
                return ImageFont.truetype(fp, sz)
        return ImageFont.load_default()

    f_h1 = _font(22, bold=True)
    f_sub = _font(15, bold=False)
    f_sec = _font(16, bold=True)
    f_bul = _font(15, bold=False)

    # Clean top header strip
    dr.rectangle([0, 0, W, 66], fill=(12, 18, 22))
    dr.text((26, 12), "JAR O' GREEN GUYS (IMPULSE 62) - 60 FPS LIVE-ACTION DIGITIZED QUAKE SWARM WEAPON", fill=(134, 255, 78), font=f_h1)
    dr.text((26, 40), "4-Antic Spazzing Specimen Jar  |  Igniting Green Smoke Shatter  |  12 Bigger Wheel-Driving Men (Drive 3 Laps First -> Attack!)  |  1-Shot Spin -> Confetti Pop!", fill=(178, 204, 218), font=f_sub)

    # Clean section headers
    dr.rectangle([16, 372, W - 16, 400], fill=(12, 18, 22))
    dr.text((26, 375), "SHATTERING GLASS & IGNITING GREEN SMOKE  ->  12 BIGGER WHEEL-DRIVING GREEN MEN: SWARM & DRIVE 3 LAPS FIRST, THEN ATTACK!", fill=(72, 226, 255), font=f_sec)

    dr.rectangle([16, 584, W - 16, 612], fill=(12, 18, 22))
    dr.text((26, 587), "1-HIT LOW-HP COMEDY DEATH: PUNCTURED-HELIUM-BALLOON 360 DEG CARTWHEEL SPIN  ->  1.45x SWELL  ->  RAINBOW CONFETTI POP!", fill=(255, 108, 172), font=f_sec)

    # Clean footer box
    dr.rectangle([24, 804, W - 24, 960], fill=(18, 27, 31), outline=(72, 148, 86), width=2)
    dr.text((42, 814), "BAKERSFIELD QUAKE LIVE WEAPON SPECS (FUN GUN SLOT 2 - IMPULSE 62):", fill=(134, 255, 78), font=f_sec)
    dr.text((42, 842), "* First-Person Sprite (progs/v_greenjar.md3): 4 Manic In-Jar Antics + Hold-Fire Cocktail-Shaker + Whip-Throw + Belt Reload + Muffled Jar Giggles!", fill=(226, 238, 244), font=f_bul)
    dr.text((42, 869), "* Bigger Wheel-Driving Swarm (12x greenguy_mini.spr32, Scale 0.56): Seated Low-Rider Wheelmen on Spinning Pneumatic Tires + Building Wall-Drivers!", fill=(226, 238, 244), font=f_bul)
    dr.text((42, 896), "* Drive 3 Laps First -> Then Attack: Swarms & Drives 3 Full Circles (1080 Deg, 0 Dmg!) Around Enemy FIRST, Then Lunges In (1%-2% Non-Lethal, >= 1 HP)!", fill=(226, 238, 244), font=f_bul)
    dr.text((42, 923), "* 1-Shot Helium Spin & Helium Voice Pack: Shoot Any Green Man for a Shrieking 360-Deg Cartwheel Spin into Rainbow Confetti + High-Pitched Giggling!", fill=(255, 216, 92), font=f_bul)
    im.save(p_path, quality=93)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jar o' Green Guys (Impulse 62) — 60 FPS Quake Weapon & 12 Wheel-Driving Green Men Simulator</title>
<style>
  :root {
    --bg: #0a0f12;
    --panel: #11191f;
    --panel2: #17232b;
    --border: #284238;
    --lime: #84ff46;
    --cyan: #42e3ff;
    --pink: #ff5ca8;
    --gold: #ffd447;
    --txt: #e7f3ef;
    --muted: #93ada5;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
  body {
    background: radial-gradient(circle at 50% 0%, #13241d 0%, var(--bg) 65%);
    color: var(--txt);
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }
  header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 20px;
    background: rgba(12, 20, 24, 0.94);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(8px);
    position: sticky;
    top: 0;
    z-index: 30;
  }
  .brand { display: flex; align-items: center; gap: 12px; }
  .badge {
    background: linear-gradient(135deg, #275e18, #58d624);
    color: #061404;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 0.08em;
    padding: 4px 9px;
    border-radius: 999px;
    text-transform: uppercase;
  }
  h1 { font-size: 19px; font-weight: 800; letter-spacing: -0.01em; color: var(--lime); }
  .sub { font-size: 12px; color: var(--muted); }
  .tabs { display: flex; gap: 8px; flex-wrap: wrap; }
  .tab-btn {
    background: var(--panel2);
    color: var(--txt);
    border: 1px solid var(--border);
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .tab-btn:hover { border-color: var(--lime); }
  .tab-btn.active {
    background: linear-gradient(135deg, #21441b, #2f6b22);
    border-color: var(--lime);
    color: #fff;
    box-shadow: 0 0 14px rgba(132, 255, 70, 0.28);
  }
  main { max-width: 1560px; margin: 0 auto; padding: 14px 18px 28px; }
  .view-sec { display: none; }
  .view-sec.active { display: block; }

  /* Arena Layout */
  .arena-wrap {
    display: grid;
    grid-template-columns: 1fr 330px;
    gap: 14px;
    align-items: start;
  }
  @media (max-width: 1100px) { .arena-wrap { grid-template-columns: 1fr; } }
  .canvas-card {
    position: relative;
    background: #070b0e;
    border: 2px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 14px 40px rgba(0,0,0,0.6);
  }
  #arenaCanvas {
    display: block;
    width: 100%;
    aspect-ratio: 16 / 9;
    cursor: crosshair;
  }
  .hud-top {
    position: absolute;
    top: 10px; left: 12px; right: 12px;
    display: flex;
    justify-content: space-between;
    pointer-events: none;
    gap: 8px;
    flex-wrap: wrap;
  }
  .pill {
    background: rgba(8, 15, 18, 0.82);
    border: 1px solid rgba(132, 255, 70, 0.35);
    padding: 5px 11px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
    color: #d8f8e4;
  }
  .pill b { color: var(--lime); }
  .hud-bottom {
    position: absolute;
    bottom: 10px; left: 14px; right: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    pointer-events: none;
  }
  .quake-bar {
    display: flex;
    gap: 14px;
    background: rgba(10, 16, 20, 0.86);
    border: 1px solid #355948;
    padding: 8px 14px;
    border-radius: 10px;
    align-items: center;
  }
  .stat-num { font-size: 26px; font-weight: 900; font-variant-numeric: tabular-nums; }
  .stat-lbl { font-size: 10px; text-transform: uppercase; color: var(--muted); letter-spacing: 0.08em; }
  .nonlethal-tag {
    font-size: 11px;
    color: var(--gold);
    background: rgba(255, 212, 71, 0.13);
    border: 1px solid rgba(255, 212, 71, 0.4);
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 700;
  }

  .side-panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 11px;
  }
  .side-panel h3 { font-size: 14px; color: var(--lime); text-transform: uppercase; letter-spacing: 0.05em; }
  .act-btn {
    width: 100%;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid #3c6e49;
    background: linear-gradient(135deg, #1b3623, #275332);
    color: #fff;
    font-weight: 800;
    font-size: 13px;
    cursor: pointer;
    text-align: left;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: transform 0.08s ease, border-color 0.15s;
  }
  .act-btn:hover { border-color: var(--lime); transform: translateY(-1px); }
  .act-btn.pink { background: linear-gradient(135deg, #4b1938, #782356); border-color: var(--pink); }
  .act-btn.cyan { background: linear-gradient(135deg, #153747, #1f556e); border-color: var(--cyan); }
  .act-btn.active-mode { box-shadow: 0 0 0 2px var(--gold); border-color: var(--gold); }
  .key-cap {
    background: rgba(0,0,0,0.45);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 5px;
    padding: 2px 6px;
    font-family: Consolas, monospace;
    font-size: 11px;
    color: var(--gold);
  }
  .ctrl-list { font-size: 12px; color: var(--muted); line-height: 1.65; }
  .ctrl-list b { color: var(--txt); }

  /* Studio Tab */
  .studio-grid {
    display: grid;
    grid-template-columns: 310px 1fr;
    gap: 16px;
  }
  @media (max-width: 980px) { .studio-grid { grid-template-columns: 1fr; } }
  .clip-list {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .clip-btn {
    background: var(--panel2);
    border: 1px solid #263b33;
    color: var(--txt);
    padding: 9px 11px;
    border-radius: 7px;
    text-align: left;
    font-size: 12.5px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
  }
  .clip-btn.active { background: #234920; border-color: var(--lime); color: #fff; }
  .studio-stage-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  #studioCanvas {
    width: 100%;
    max-height: 540px;
    aspect-ratio: 16 / 10;
    border-radius: 10px;
    border: 1px solid #2c473c;
    background: #141c21;
  }
  .toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: center;
    background: var(--panel2);
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 12.5px;
  }
  .toolbar label { display: flex; align-items: center; gap: 6px; color: var(--muted); font-weight: 600; }
  input[type=range] { accent-color: var(--lime); }

  /* Soundboard & Specs Tab */
  .snd-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 10px;
    margin-top: 10px;
  }
  .snd-card {
    background: var(--panel2);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 12px;
    cursor: pointer;
    transition: border-color 0.15s, transform 0.08s;
  }
  .snd-card:hover { border-color: var(--lime); transform: translateY(-2px); }
  .snd-card h4 { color: var(--lime); font-size: 13px; margin-bottom: 4px; }
  .snd-card p { color: var(--muted); font-size: 11.5px; }
  .spec-box {
    margin-top: 16px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    line-height: 1.65;
    font-size: 13.5px;
  }
  .spec-box code {
    background: #0b1216;
    color: var(--cyan);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: Consolas, monospace;
  }
</style>
</head>
<body>

<header>
  <div class="brand">
    <span class="badge">Impulse 62 · 60 FPS</span>
    <div>
      <h1>JAR O' GREEN GUYS — QUAKE WHEEL-DRIVING SWARM WEAPON</h1>
      <div class="sub">100% Real Photo-Digitized Specimen Jar · Igniting Green Smoke · 12 Bigger Wheel-Driving Green Men (Swarm &amp; Drive 3 Laps First -> Then Attack!) · 1-Shot Spin -> Confetti Pop!</div>
    </div>
  </div>
  <div class="tabs">
    <button class="tab-btn active" data-tab="arena">1. Playable 3D Swarm &amp; Shooting Gallery</button>
    <button class="tab-btn" data-tab="studio">2. 60 FPS First-Person Jar &amp; Wheel-Driver Studio</button>
    <button class="tab-btn" data-tab="sound">3. Helium Voice Soundboard &amp; Quake Specs</button>
  </div>
</header>

<main>
  <!-- TAB 1: PLAYABLE 3D ARENA -->
  <section id="tab-arena" class="view-sec active">
    <div class="arena-wrap">
      <div class="canvas-card">
        <canvas id="arenaCanvas" width="1280" height="720"></canvas>
        <div class="hud-top">
          <div class="pill" id="hudWeaponPill">WEAPON: <b>[1] JAR O' GREEN GUYS</b> (Hold LMB to Shake -> Release to Throw!)</div>
          <div class="pill" id="hudSwarmCount">ACTIVE GREEN MEN: <b>0</b> &nbsp;|&nbsp; CONFETTI POPS: <b>0</b></div>
        </div>
        <div class="hud-bottom">
          <div class="quake-bar">
            <div>
              <div class="stat-lbl">Health (Never Kills!)</div>
              <div class="stat-num" id="hudHp" style="color:#84ff46">100%</div>
            </div>
            <div style="width:1px;height:32px;background:#2b473a"></div>
            <div>
              <div class="stat-lbl">Jars Ready</div>
              <div class="stat-num" id="hudAmmo" style="color:#42e3ff">∞</div>
            </div>
            <span class="nonlethal-tag" id="hudOrbitStatus">Ready — Throw a Jar or Click "SWARM &amp; DRIVE AROUND ME!"</span>
          </div>
        </div>
      </div>

      <aside class="side-panel">
        <h3>Instant Mastermind Actions</h3>
        <button class="act-btn" id="btnThrowJar">
          <span>Shake &amp; Throw Jar Forward!</span>
          <span class="key-cap">Hold LMB</span>
        </button>
        <button class="act-btn pink" id="btnSwarmMeNow">
          <span>SWARM &amp; DRIVE 3 LAPS AROUND ME!</span>
          <span class="key-cap">G</span>
        </button>
        <button class="act-btn cyan" id="btnToggleWeapon">
          <span id="lblToggleWep">Switch to Rapid Blaster (Shoot 'Em!)</span>
          <span class="key-cap">1 / 2 / RMB</span>
        </button>
        <button class="act-btn" id="btnTargetMode">
          <span id="lblTargetMode">Target: Enemy Bots + Buildings</span>
          <span class="key-cap">T</span>
        </button>
        <button class="act-btn" id="btnAudioToggle">
          <span id="lblAudio">Helium Giggles &amp; Screams: ON 🔊</span>
          <span class="key-cap">M</span>
        </button>

        <hr style="border:none;border-top:1px solid #263d34;margin:2px 0">
        <h3>How It Works In-Game</h3>
        <div class="ctrl-list">
          • <b>Hold Left-Click</b>: Cocktail-shakes the clear jar — neon-green mist flares &amp; tiny Green-Suit Guy pinballs inside!<br>
          • <b>Release Left-Click</b>: Whips jar out of splayed bronze claw -&gt; shatters into <b>igniting green smoke</b> + <b>12 bigger Wheel-Driving Green Men</b>!<br>
          • <b>Bigger Seated Wheel-Driving</b>: Watch them motor across floors on spinning pneumatic tires with tire smoke &amp; chrome sparks, plus <b>vertical building wall-drivers</b>!<br>
          • <b>Swarm 3 Laps FIRST -&gt; Then Attack!</b>: They <b>do NOT attack right away</b> — they drive <b>3 full circles (1080°, 0 dmg!)</b> around the enemy first, and <b>only AFTER 3 laps</b> lunge in to attack (1%–2% non-lethal hits, <b>clamped ≥ 1 HP</b>) -&gt; swell &amp; <b>pop into rainbow confetti</b>!<br>
          • <b>Right-Click / Key [2]</b>: Shoot any Green Man (1 HP!) to trigger a hilarious <b>360° punctured-helium cartwheel spin</b> into confetti!<br>
          • <b>Move / Aim</b>: <b>WASD</b> + Move Mouse (click canvas for 360° pointer-lock, <b>ESC</b> to unlock).
        </div>
      </aside>
    </div>
  </section>

  <!-- TAB 2: 60 FPS SPRITE STUDIO -->
  <section id="tab-studio" class="view-sec">
    <div class="studio-grid">
      <div class="clip-list" id="studioClipList"></div>
      <div class="studio-stage-card">
        <canvas id="studioCanvas" width="960" height="600"></canvas>
        <div class="toolbar">
          <button class="tab-btn" id="stPlayBtn">⏸ Pause</button>
          <label>Speed <input type="range" id="stSpeed" min="0.1" max="1.5" step="0.05" value="1.0"><span id="stSpeedVal">1.00x (60 FPS)</span></label>
          <label>Zoom <input type="range" id="stZoom" min="0.75" max="2.4" step="0.05" value="1.25"></label>
          <label id="stAngleWrap">360° Angle <input type="range" id="stAngle" min="0" max="15" step="1" value="0"><span id="stAngleVal">0.0°</span></label>
          <label>Frame <input type="range" id="stScrub" min="0" max="179" step="1" value="0"><span id="stFrameVal">0</span></label>
        </div>
      </div>
    </div>
  </section>

  <!-- TAB 3: HELIUM VOICE SOUNDBOARD & QUAKE SPECS -->
  <section id="tab-sound" class="view-sec">
    <h2 style="color:var(--lime);font-size:18px">Helium Screaming, Laughing & Giggling Voice Pack (Click Any Card to Play!)</h2>
    <p style="color:var(--muted);font-size:13px;margin-top:4px">All 12 `.wav` files are live in <code>BakersfieldQuake/sound/greenjar/</code> and embedded directly in this page.</p>
    <div class="snd-grid" id="sndBoardGrid"></div>

    <div class="spec-box">
      <h3 style="color:var(--cyan);margin-bottom:8px">BakersfieldQuake Live Integration Summary (`impulse 62` / Fun Gun Slot 2)</h3>
      • <b>First-Person Animated Jar Sprite</b>: <code>progs/v_greenjar.md3</code> + 112 optical-glass RGBA skins (<code>progs/gjvm_000..111.png</code>, <code>scripts/greenjarvm.shader</code>) cycling all 4 in-jar spaz antics, hold-to-shake cocktail windup, overhand whip-throw with splayed open claw, and belt-snatch reload.<br>
      • <b>World Projectile & Igniting Green Smoke</b>: <code>progs/greenjar_proj.spr32</code> (tumbling sealed glass jar) &amp; <code>progs/greenjar_burst.spr32</code> (glittering glass shards + igniting radioactive green smoke cloud).<br>
      • <b>12 Bigger 16-Angle Wheel-Driving Green Men</b>: <code>progs/greenguy_mini.spr32</code> (`160×160` cells, world `scale = 0.56` — ~2.3x larger waist-to-chest height!) across 16-angle seated wheel-driving with spinning pneumatic tires, 16-angle vertical building wall-driving, 16-angle post-3-lap torpedo &amp; sky-point attack lunge, 1-hit punctured-helium 360° cartwheel spin, and pressurized balloon swell -&gt; rainbow confetti pop.<br>
      • <b>Swarm 3 Laps First -&gt; Then Attack AI</b>: <code>source/mm_tools/greenjar_defs.qc</code> &amp; <code>source/mm_tools/greenjar.qc</code> (`GJ_ORBITS_BEFORE_ATK = 1080` — 0 damage while wheeling 3 full laps around the enemy, then switches to `gj_state = 6` leaping attack frenzy clamped `>= 1 HP`, wired into <code>funguns.qc</code> `impulse 62` + `bm_reload.qc` `BM_FG2`).
    </div>
  </section>
</main>

<script>
const MANIFEST = __MANIFEST_JSON__;
const ATLAS_B64 = __ATLAS_B64_JSON__;
const AUDIO_B64 = __AUDIO_B64_JSON__;

// ---------------------------------------------------------------------------
// 1. WebAudio Engine (Decodes all 12 embedded WAVs for overlap & pitch-jitter!)
// ---------------------------------------------------------------------------
let audioCtx = null;
let audioMuted = false;
const audioBuffers = {};

function ensureAudio() {
  if (!audioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (AC) audioCtx = new AC();
  }
  if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  if (audioCtx && ! ensureAudio._decoding) {
    ensureAudio._decoding = true;
    for (const [k, uri] of Object.entries(AUDIO_B64)) {
      const b64 = uri.split(',')[1];
      const bin = atob(b64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      audioCtx.decodeAudioData(bytes.buffer.slice(0), buf => { audioBuffers[k] = buf; }, () => {});
    }
  }
}
window.addEventListener('pointerdown', ensureAudio, { passive: true });
window.addEventListener('keydown', ensureAudio, { passive: true });

function playSfx(name, vol = 0.7, rate = 1.0, pan = 0.0) {
  if (audioMuted) return;
  ensureAudio();
  const buf = audioBuffers[name];
  if (!audioCtx || !buf) return;
  const src = audioCtx.createBufferSource();
  src.buffer = buf;
  src.playbackRate.value = Math.max(0.5, Math.min(1.8, rate));
  const gain = audioCtx.createGain();
  gain.gain.value = Math.max(0, Math.min(1.2, vol));
  if (audioCtx.createStereoPanner) {
    const panner = audioCtx.createStereoPanner();
    panner.pan.value = Math.max(-1, Math.min(1, pan));
    src.connect(gain); gain.connect(panner); panner.connect(audioCtx.destination);
  } else {
    src.connect(gain); gain.connect(audioCtx.destination);
  }
  src.start(0);
}

// ---------------------------------------------------------------------------
// 2. Load Embedded 60 FPS WebP Sprite Atlases
// ---------------------------------------------------------------------------
const images = {};
let loadedCount = 0;
const totalImages = Object.keys(ATLAS_B64).length;
for (const [k, uri] of Object.entries(ATLAS_B64)) {
  const im = new Image();
  im.onload = () => { loadedCount++; };
  im.src = uri;
  images[k] = im;
}

function drawAtlasCell(ctx, key, idx, dx, dy, dw, dh) {
  const im = images[key];
  const m = MANIFEST[key];
  if (!im || !im.complete || !m) return;
  const c = idx % m.cols;
  const r = Math.floor(idx / m.cols);
  ctx.drawImage(im, c * m.w, r * m.h, m.w, m.h, dx, dy, dw, dh);
}

// ---------------------------------------------------------------------------
// 3. Tab Switching & Soundboard Init
// ---------------------------------------------------------------------------
let activeTab = 'arena';
document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
  btn.addEventListener('click', () => {
    activeTab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn[data-tab]').forEach(b => b.classList.toggle('active', b === btn));
    document.querySelectorAll('.view-sec').forEach(s => s.classList.toggle('active', s.id === 'tab-' + activeTab));
  });
});

const SOUND_META = [
  ['jar_muffle1', 'Muffled Jar Giggle #1', 'Inside-the-glass muffled helium cackle & tap while held'],
  ['jar_muffle2', 'Muffled Jar Giggle #2', 'Resonant glass-filtered high-pitched laugh'],
  ['jar_shake',   'Cocktail-Shaker Rattle', 'Violent glass & lid rattle when holding Fire'],
  ['jar_throw',   'Overhand Whip-Throw', 'High-velocity gauntlet whip whoosh'],
  ['jar_shatter', 'Glass Shatter + Smoke Ignition!', 'Crisp mason jar burst + roaring neon-green smoke'],
  ['mini_giggle1','Helium Gremlin Giggle #1', 'Hyper chipmunk LAN-party giggle'],
  ['mini_giggle2','Helium Gremlin Cackle #2', 'Manic rapid-fire high-pitched laugh'],
  ['mini_giggle3','Helium Gremlin Laugh #3', 'Bouncy gremlin swarm chorus laugh'],
  ['mini_scream1','High-Pitched Gremlin Scream!', 'Frantic helium shriek while climbing & orbiting'],
  ['mini_spin_shriek','1-Shot Punctured Spin Shriek!', 'Warbling Doppler helium balloon spin-out'],
  ['mini_pop',    'Balloon Swell -> Confetti POP!', 'Crisp party-balloon snap & confetti flutter'],
  ['mini_boing',  'Rubber-Flea Pogo Boing', 'Weightless building-vault & face-jump bounce']
];
const sbGrid = document.getElementById('sndBoardGrid');
SOUND_META.forEach(([id, title, desc]) => {
  const d = document.createElement('div');
  d.className = 'snd-card';
  d.innerHTML = `<h4>▶ ${title}</h4><p>${desc}</p><p style="margin-top:5px;color:#42e3ff;font-family:monospace">sound/greenjar/${id}.wav</p>`;
  d.onclick = () => playSfx(id, 0.9, 1.0);
  sbGrid.appendChild(d);
});

// ---------------------------------------------------------------------------
// 4. TAB 2: 60 FPS Sprite Studio
// ---------------------------------------------------------------------------
const STUDIO_CLIPS = [
  { id: 'idle_all',   name: 'Held Jar: Full 4-Antic Loop (180f)', atlas: 'vm_idle', start: 0, len: 180, angled: false },
  { id: 'antic0',     name: 'Antic 1: Hamster-Wheel Wall & Lid Flip', atlas: 'vm_idle', start: 0, len: 45, angled: false },
  { id: 'antic1',     name: 'Antic 2: Grin/Scream Glass-Squish + Fog', atlas: 'vm_idle', start: 45, len: 45, angled: false },
  { id: 'antic2',     name: 'Antic 3: Crane-Kick Pogo Lid-Bonk!', atlas: 'vm_idle', start: 90, len: 45, angled: false },
  { id: 'antic3',     name: 'Antic 4: 360° Whirlwind Tornado Spaz', atlas: 'vm_idle', start: 135, len: 45, angled: false },
  { id: 'vm_shake',   name: 'Held Jar: Cocktail-Shaker Windup (24f)', atlas: 'vm_action', start: 0, len: 24, angled: false },
  { id: 'vm_throw',   name: 'Held Jar: Whip-Throw & Open Claw (18f)', atlas: 'vm_action', start: 24, len: 18, angled: false },
  { id: 'vm_reload',  name: 'Held Jar: Belt-Snatch Reload (18f)', atlas: 'vm_action', start: 42, len: 18, angled: false },
  { id: 'proj_jar',   name: 'Thrown Tumbling Specimen Jar (24f)', atlas: 'proj_jar', start: 0, len: 24, angled: false },
  { id: 'smoke_burst',name: 'Glass Shatter + Green Smoke Fireball (36f)', atlas: 'smoke_burst', start: 0, len: 36, angled: false },
  { id: 'scurry',     name: 'Green Man: 16-Angle Seated Wheel-Drive!', atlas: 'scurry', start: 0, len: 12, angled: true },
  { id: 'wall_climb', name: 'Green Man: 16-Angle Building Wall-Drive!', atlas: 'wall_climb', start: 0, len: 12, angled: true },
  { id: 'pogo_jump',  name: 'Green Man: Post-3-Lap Torpedo & Jump Attack!', atlas: 'pogo_jump', start: 0, len: 12, angled: true },
  { id: 'shot_spin',  name: '1-Hit Death: Punctured-Helium Spin (24f)', atlas: 'mini_fx', start: 0, len: 24, angled: false, once: false },
  { id: 'balloon_pop',name: 'Post-Attack / Death: 1.45x Swell -> Confetti Pop!', atlas: 'mini_fx', start: 24, len: 24, angled: false }
];

let stClip = STUDIO_CLIPS[0];
let stPlaying = true;
let stCursor = 0;
let stAngle = 0;
const stListEl = document.getElementById('studioClipList');
const stScrub = document.getElementById('stScrub');
const stAngleIn = document.getElementById('stAngle');
const stAngleWrap = document.getElementById('stAngleWrap');

function selectStudioClip(c) {
  stClip = c;
  stCursor = 0;
  stScrub.max = c.len - 1;
  stAngleWrap.style.display = c.angled ? 'flex' : 'none';
  document.querySelectorAll('.clip-btn').forEach((b, i) => b.classList.toggle('active', STUDIO_CLIPS[i] === c));
}
STUDIO_CLIPS.forEach((c, idx) => {
  const b = document.createElement('button');
  b.className = 'clip-btn' + (idx === 0 ? ' active' : '');
  b.innerHTML = `<span>${c.name}</span><span style="color:#84ff46">${c.len}f</span>`;
  b.onclick = () => selectStudioClip(c);
  stListEl.appendChild(b);
});
selectStudioClip(STUDIO_CLIPS[0]);

document.getElementById('stPlayBtn').onclick = (e) => {
  stPlaying = !stPlaying;
  e.target.textContent = stPlaying ? '⏸ Pause' : '▶ Play';
};
stAngleIn.oninput = () => {
  stAngle = parseInt(stAngleIn.value, 10);
  document.getElementById('stAngleVal').textContent = (stAngle * 22.5).toFixed(1) + '°';
};
stScrub.oninput = () => {
  stPlaying = false;
  document.getElementById('stPlayBtn').textContent = '▶ Play';
  stCursor = parseInt(stScrub.value, 10);
};
document.getElementById('stSpeed').oninput = (e) => {
  document.getElementById('stSpeedVal').textContent = parseFloat(e.target.value).toFixed(2) + 'x (60 FPS)';
};

const stCanvas = document.getElementById('studioCanvas');
const stCtx = stCanvas.getContext('2d');

function renderStudio(dt) {
  const spd = parseFloat(document.getElementById('stSpeed').value);
  const zoom = parseFloat(document.getElementById('stZoom').value);
  if (stPlaying) {
    stCursor = (stCursor + dt * 60 * spd) % stClip.len;
  }
  const fIdx = Math.floor(stCursor) % stClip.len;
  stScrub.value = fIdx;
  document.getElementById('stFrameVal').textContent = `${fIdx + 1}/${stClip.len}`;

  const W = stCanvas.width, H = stCanvas.height;
  // Subtle studio checker + emerald radial glow
  stCtx.fillStyle = '#11181d';
  stCtx.fillRect(0, 0, W, H);
  const grd = stCtx.createRadialGradient(W * 0.5, H * 0.54, 20, W * 0.5, H * 0.54, 340);
  grd.addColorStop(0, 'rgba(92, 225, 64, 0.16)');
  grd.addColorStop(1, 'rgba(10, 16, 20, 0)');
  stCtx.fillStyle = grd;
  stCtx.fillRect(0, 0, W, H);

  const m = MANIFEST[stClip.atlas];
  if (!m) return;
  const atlasIdx = stClip.angled ? (stAngle * 12 + fIdx) : (stClip.start + fIdx);
  const dw = m.w * zoom * 1.45;
  const dh = m.h * zoom * 1.45;
  drawAtlasCell(stCtx, stClip.atlas, atlasIdx, (W - dw) * 0.5, (H - dh) * 0.5, dw, dh);

  stCtx.fillStyle = '#93ada5';
  stCtx.font = 'bold 14px Consolas, monospace';
  stCtx.fillText(`${stClip.name}  |  60 FPS Live-Action Optical Sprite`, 18, 28);
}

// ---------------------------------------------------------------------------
// 5. TAB 1: PLAYABLE 3D BUILDING COURTYARD, 5x FACE-SWARM & SHOOTING GALLERY!
// ---------------------------------------------------------------------------
const aCanvas = document.getElementById('arenaCanvas');
const aCtx = aCanvas.getContext('2d');

const cam = { x: 0, y: 26, z: -230, yaw: 0, pitch: 0.03 };
const keys = {};
let weaponSlot = 1; // 1 = Jar o' Green Guys, 2 = Rapid Blaster
let targetSelfMode = false;
let playerHp = 100;
let confettiPopTotal = 0;

// First-person Jar state machine
let vmState = 'idle'; // 'idle' | 'shake' | 'throw' | 'reload'
let vmTimer = 0;
let shakeHeldTime = 0;
let thrownInSwing = false;
let mouseLeftDown = false;
let nextMuffleT = 2.2;
let nextShakeSndT = 0;
let blasterRecoil = 0;
let muzzleFlashT = 0;
const tracers = [];

// 3D Climbable Buildings (AABB boxes in X, Z, with roof height H)
const BUILDINGS = [
  { x0: -185, x1: -95, z0: 40,  z1: 130, h: 145, col1: '#23323d', col2: '#1a252e', trim: '#53d843', name: 'West Tower' },
  { x0:  95,  x1:  185, z0: 40,  z1: 130, h: 165, col1: '#26303b', col2: '#1c242d', trim: '#42e3ff', name: 'East Tower' },
  { x0: -65,  x1:  65,  z0: 185, z1: 275, h: 195, col1: '#2b2938', col2: '#1f1d29', trim: '#ff5ca8', name: 'LAN Citadel' },
  { x0: -220, x1: -155, z0: -115,z1: -50, h: 105, col1: '#21332d', col2: '#182621', trim: '#ffd447', name: 'Pillar A' },
  { x0:  155, x1:  220, z0: -115,z1: -50, h: 105, col1: '#21332d', col2: '#182621', trim: '#ffd447', name: 'Pillar B' }
];

// Roaming Enemy Bots to get swarmed & annoyed!
const bots = [
  { id: 1, x: -75, y: 0, z: -20, vx: 42, vz: 28, hp: 100, ang: 0, label: 'Quake Ranger' },
  { id: 2, x:  80, y: 0, z:  15, vx: -36, vz: 44, hp: 100, ang: 2.2, label: 'LAN Opponent' }
];

const jars = [];
const bursts = [];
const gremlins = [];

function spawnJar(fromSelfSwarm = false) {
  if (fromSelfSwarm) {
    // Shatter right in front of the player so 12 bigger Green Men immediately drive 3 laps around YOU, then attack!
    const sx = cam.x + Math.sin(cam.yaw) * 68;
    const sz = cam.z + Math.cos(cam.yaw) * 68;
    shatterJarAt(sx, 8, sz, true);
    return;
  }
  const dirX = Math.sin(cam.yaw) * Math.cos(cam.pitch);
  const dirY = -Math.sin(cam.pitch);
  const dirZ = Math.cos(cam.yaw) * Math.cos(cam.pitch);
  const spd = 290 + Math.min(1.0, shakeHeldTime) * 120;
  jars.push({
    x: cam.x + dirX * 22 + Math.cos(cam.yaw) * 6,
    y: cam.y - 4 + dirY * 18,
    z: cam.z + dirZ * 22 - Math.sin(cam.yaw) * 6,
    vx: dirX * spd,
    vy: dirY * spd + 95,
    vz: dirZ * spd,
    t: 0
  });
}

function shatterJarAt(x, y, z, forceSelfTarget = false) {
  playSfx('jar_shatter', 0.92, 0.97 + Math.random() * 0.08);
  bursts.push({ x, y: Math.max(12, y), z, t: 0 });

  // Unleash 12 bigger Wheel-Driving Green Men!
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2 + (Math.random() - 0.5) * 0.30;
    const outSpd = 85 + Math.random() * 95;
    gremlins.push({
      x: x + Math.cos(a) * 10,
      y: Math.max(0, y),
      z: z + Math.sin(a) * 10,
      vx: Math.cos(a) * outSpd,
      vy: 65 + Math.random() * 55,
      vz: Math.sin(a) * outSpd,
      yaw: a,
      role: i % 3, // 0 = cruiser, 1 = sprinter, 2 = building wall-driver
      state: forceSelfTarget ? 'orbit' : 'search', // 'search' | 'wall' | 'orbit' (3 laps, 0 dmg!) | 'attack' | 'spin' | 'pop'
      target: forceSelfTarget ? 'player' : null,
      orbitAng: a,
      orbitDir: (i % 2 === 0 ? 1 : -1),
      orbitRad: (forceSelfTarget ? 44 : 46) + (i % 4) * 6.5,
      orbitDeg: 0,
      attackEnd: 0,
      animT: Math.random() * 2.0,
      stepT: 0,
      wallBox: null,
      nextLaugh: 0.06 * i + Math.random() * 0.35,
      nextPoke: 0.25 + Math.random() * 0.35,
      age: 0
    });
  }
  // Cap total active Green Men at 48 so spamming stays buttery 60 FPS
  while (gremlins.length > 48) {
    const g0 = gremlins.shift();
    if (g0) confettiPopTotal++;
  }
}

function fireBlaster() {
  blasterRecoil = 1.0;
  muzzleFlashT = 0.07;
  playSfx('mini_boing', 0.35, 1.65);

  const dirX = Math.sin(cam.yaw) * Math.cos(cam.pitch);
  const dirY = -Math.sin(cam.pitch);
  const dirZ = Math.cos(cam.yaw) * Math.cos(cam.pitch);
  tracers.push({
    x0: cam.x + Math.cos(cam.yaw) * 7, y0: cam.y - 6, z0: cam.z - Math.sin(cam.yaw) * 7,
    x1: cam.x + dirX * 520, y1: cam.y + dirY * 520, z1: cam.z + dirZ * 520,
    t: 0.09
  });

  // Hit-scan check against nearest Green Man within generous hitbox!
  let bestG = null, bestDist = 9999;
  for (const g of gremlins) {
    if (g.state === 'pop') continue;
    const gx = g.x - cam.x, gy = (g.y + 18) - cam.y, gz = g.z - cam.z;
    const proj = gx * dirX + gy * dirY + gz * dirZ;
    if (proj < 8 || proj > 680) continue;
    const px = gx - dirX * proj, py = gy - dirY * proj, pz = gz - dirZ * proj;
    const perp = Math.hypot(px, py, pz);
    const hitRad = (proj < 75 ? 28 : 23);
    if (perp < hitRad && proj < bestDist) {
      bestDist = proj;
      bestG = g;
    }
  }
  if (bestG) {
    if (bestG.state === 'spin') {
      // 2nd shot mid-spin -> immediate rainbow confetti pop!
      bestG.state = 'pop';
      bestG.stepT = 6 / 40.0;
      confettiPopTotal++;
      playSfx('mini_pop', 0.95, 0.95 + Math.random() * 0.15);
    } else {
      // 1st shot -> hilarious 360° Punctured-Helium-Balloon Cartwheel Spin!
      bestG.state = 'spin';
      bestG.stepT = 0;
      const pushA = Math.atan2(bestG.z - cam.z, bestG.x - cam.x) + (Math.random() - 0.5) * 1.1;
      bestG.vx = Math.cos(pushA) * 190;
      bestG.vz = Math.sin(pushA) * 190;
      bestG.vy = 145 + Math.random() * 85;
      playSfx('mini_spin_shriek', 0.95, 0.95 + Math.random() * 0.14);
    }
  }
}

// Controls
window.addEventListener('keydown', e => {
  keys[e.code] = true;
  if (e.code === 'Digit1') { weaponSlot = 1; updateWeaponUI(); }
  if (e.code === 'Digit2') { weaponSlot = 2; updateWeaponUI(); }
  if (e.code === 'KeyG') { spawnJar(true); }
  if (e.code === 'KeyT') { toggleTargetMode(); }
  if (e.code === 'KeyM') { toggleAudio(); }
});
window.addEventListener('keyup', e => { keys[e.code] = false; });

aCanvas.addEventListener('contextmenu', e => e.preventDefault());
aCanvas.addEventListener('mousedown', e => {
  if (activeTab !== 'arena') return;
  if (document.pointerLockElement !== aCanvas && e.button === 0) {
    aCanvas.requestPointerLock?.();
  }
  if (e.button === 2 || weaponSlot === 2) {
    fireBlaster();
  } else if (e.button === 0 && weaponSlot === 1) {
    mouseLeftDown = true;
    if (vmState === 'idle') {
      vmState = 'shake';
      vmTimer = 0;
      shakeHeldTime = 0;
      playSfx('jar_shake', 0.85, 1.0);
      nextShakeSndT = 0.38;
    }
  }
});
window.addEventListener('mouseup', e => {
  if (e.button === 0) mouseLeftDown = false;
});
window.addEventListener('mousemove', e => {
  if (activeTab !== 'arena') return;
  if (document.pointerLockElement === aCanvas) {
    cam.yaw += e.movementX * 0.0028;
    cam.pitch = Math.max(-0.55, Math.min(0.55, cam.pitch + e.movementY * 0.0022));
  } else if (e.buttons === 1 && weaponSlot === 2) {
    cam.yaw += e.movementX * 0.003;
  }
});

function updateWeaponUI() {
  document.getElementById('hudWeaponPill').innerHTML = weaponSlot === 1
    ? 'WEAPON: <b>[1] JAR O\' GREEN GUYS</b> (Hold LMB to Shake · RMB to Shoot!)'
    : 'WEAPON: <b>[2] RAPID BLASTER</b> (1-Shot Punctured-Helium Spin -> Confetti!)';
  document.getElementById('lblToggleWep').textContent = weaponSlot === 1
    ? 'Switch to Rapid Blaster (Shoot \'Em!)'
    : 'Switch to Jar o\' Green Guys';
}
function toggleTargetMode() {
  targetSelfMode = !targetSelfMode;
  document.getElementById('lblTargetMode').textContent = targetSelfMode
    ? 'Target: SWARM ME! (3 Laps -> Attack)'
    : 'Target: Enemy Bots + Buildings';
  document.getElementById('btnTargetMode').classList.toggle('active-mode', targetSelfMode);
}
function toggleAudio() {
  audioMuted = !audioMuted;
  document.getElementById('lblAudio').textContent = audioMuted
    ? 'Helium Giggles & Screams: MUTED 🔇'
    : 'Helium Giggles & Screams: ON 🔊';
}

document.getElementById('btnThrowJar').onclick = () => {
  weaponSlot = 1; updateWeaponUI();
  vmState = 'throw'; vmTimer = 0; thrownInSwing = false; shakeHeldTime = 0.4;
  playSfx('jar_throw', 0.9, 1.0);
};
document.getElementById('btnSwarmMeNow').onclick = () => spawnJar(true);
document.getElementById('btnToggleWeapon').onclick = () => { weaponSlot = weaponSlot === 1 ? 2 : 1; updateWeaponUI(); };
document.getElementById('btnTargetMode').onclick = toggleTargetMode;
document.getElementById('btnAudioToggle').onclick = toggleAudio;

// Seed an immediate lively demo jar 0.6s after load so the user sees green smoke + wall-climbing gremlins right away!
setTimeout(() => { shatterJarAt(0, 14, 25, false); }, 550);

// 3D Projection Helpers
const FOV_F = 640;
function worldToCam(wx, wy, wz) {
  const dx = wx - cam.x, dy = wy - cam.y, dz = wz - cam.z;
  const cy = Math.cos(-cam.yaw), sy = Math.sin(-cam.yaw);
  const x1 = dx * cy + dz * sy;
  const z1 = -dx * sy + dz * cy;
  const cp = Math.cos(cam.pitch), sp = Math.sin(cam.pitch);
  const y2 = dy * cp - z1 * sp;
  const z2 = dy * sp + z1 * cp;
  return { x: x1, y: y2, z: z2 };
}
function projectPt(wx, wy, wz, W, H) {
  const c = worldToCam(wx, wy, wz);
  if (c.z <= 4) return null;
  return {
    sx: W * 0.5 + (c.x / c.z) * FOV_F,
    sy: H * 0.5 - (c.y / c.z) * FOV_F,
    z: c.z,
    scale: FOV_F / c.z
  };
}

function updateArena(dt) {
  // Player WASD movement
  const moveSpd = 145 * dt;
  let fwd = (keys['KeyW'] || keys['ArrowUp'] ? 1 : 0) - (keys['KeyS'] || keys['ArrowDown'] ? 1 : 0);
  let str = (keys['KeyD'] ? 1 : 0) - (keys['KeyA'] ? 1 : 0);
  if (keys['ArrowLeft']) cam.yaw -= 1.8 * dt;
  if (keys['ArrowRight']) cam.yaw += 1.8 * dt;
  if (fwd || str) {
    const nx = cam.x + (Math.sin(cam.yaw) * fwd + Math.cos(cam.yaw) * str) * moveSpd;
    const nz = cam.z + (Math.cos(cam.yaw) * fwd - Math.sin(cam.yaw) * str) * moveSpd;
    cam.x = Math.max(-290, Math.min(290, nx));
    cam.z = Math.max(-310, Math.min(310, nz));
  }

  // Roaming Bots
  for (const b of bots) {
    b.x += b.vx * dt;
    b.z += b.vz * dt;
    if (b.x < -230 || b.x > 230) b.vx *= -1;
    if (b.z < -170 || b.z > 155) b.vz *= -1;
    for (const bd of BUILDINGS) {
      if (b.x > bd.x0 - 16 && b.x < bd.x1 + 16 && b.z > bd.z0 - 16 && b.z < bd.z1 + 16) {
        b.vx *= -1; b.vz *= -1;
        b.x += b.vx * dt * 2; b.z += b.vz * dt * 2;
      }
    }
    b.ang += dt * 2.5;
  }

  // First-person Jar State Machine
  if (weaponSlot === 1) {
    if (vmState === 'idle') {
      vmTimer = (vmTimer + dt) % 3.0;
      nextMuffleT -= dt;
      if (nextMuffleT <= 0) {
        playSfx(Math.random() < 0.5 ? 'jar_muffle1' : 'jar_muffle2', 0.42, 0.96 + Math.random() * 0.08);
        nextMuffleT = 3.6 + Math.random() * 2.2;
      }
    } else if (vmState === 'shake') {
      vmTimer += dt;
      shakeHeldTime += dt;
      nextShakeSndT -= dt;
      if (nextShakeSndT <= 0) {
        playSfx('jar_shake', 0.85, 1.0 + Math.min(0.25, shakeHeldTime * 0.15));
        nextShakeSndT = 0.36;
      }
      if ((!mouseLeftDown && shakeHeldTime >= 0.12) || shakeHeldTime >= 1.35) {
        vmState = 'throw';
        vmTimer = 0;
        thrownInSwing = false;
        playSfx('jar_throw', 0.92, 1.0);
      }
    } else if (vmState === 'throw') {
      vmTimer += dt;
      if (!thrownInSwing && vmTimer >= (8 / 60)) {
        thrownInSwing = true;
        spawnJar(false);
      }
      if (vmTimer >= (18 / 60)) {
        vmState = 'reload';
        vmTimer = 0;
      }
    } else if (vmState === 'reload') {
      vmTimer += dt;
      if (vmTimer >= (18 / 60)) {
        vmState = 'idle';
        vmTimer = 0;
      }
    }
  }
  blasterRecoil = Math.max(0, blasterRecoil - dt * 6.5);
  muzzleFlashT = Math.max(0, muzzleFlashT - dt);
  for (let i = tracers.length - 1; i >= 0; i--) {
    tracers[i].t -= dt;
    if (tracers[i].t <= 0) tracers.splice(i, 1);
  }

  // Thrown Jars
  for (let i = jars.length - 1; i >= 0; i--) {
    const j = jars[i];
    j.t += dt;
    j.vy -= 360 * dt;
    j.x += j.vx * dt;
    j.y += j.vy * dt;
    j.z += j.vz * dt;
    let hit = (j.y <= 4);
    for (const bd of BUILDINGS) {
      if (j.x >= bd.x0 && j.x <= bd.x1 && j.z >= bd.z0 && j.z <= bd.z1 && j.y <= bd.h) hit = true;
    }
    if (hit || j.t > 4.0) {
      shatterJarAt(j.x, Math.max(6, j.y), j.z, targetSelfMode);
      jars.splice(i, 1);
    }
  }

  // Green Smoke Bursts
  for (let i = bursts.length - 1; i >= 0; i--) {
    bursts[i].t += dt;
    if (bursts[i].t >= 0.65) bursts.splice(i, 1);
  }

  // 12 Bigger Wheel-Driving Green Men AI:
  //   1) Grounded Wheel-Driving ('search') + Vertical Building Wall-Drive ('wall')
  //   2) Swarm & Drive 3 Full Laps Around Enemy FIRST ('orbit', 0..1080 deg, ZERO damage!)
  //   3) ONLY After 3 Laps -> Leaping Torpedo & Sky-Point Attack Frenzy ('attack', 1%-2% non-lethal >= 1 HP) -> Confetti Pop!
  let activeOrbiters = 0;
  let activeAttackers = 0;
  let maxOrbitLaps = 0;
  for (let i = gremlins.length - 1; i >= 0; i--) {
    const g = gremlins[i];
    g.age += dt;
    g.animT += dt;

    if (g.state === 'pop') {
      g.stepT += dt;
      if (g.stepT >= 24 / 38.0) gremlins.splice(i, 1);
      continue;
    }

    if (g.state === 'spin') {
      g.stepT += dt;
      g.vy -= 260 * dt;
      g.x += g.vx * dt;
      g.y += g.vy * dt;
      g.z += g.vz * dt;
      if (g.y < 0) { g.y = 0; g.vy = Math.abs(g.vy) * 0.8 + 60; g.vx += (Math.random()-0.5)*90; }
      for (const bd of BUILDINGS) {
        if (g.x > bd.x0 - 8 && g.x < bd.x1 + 8 && g.z > bd.z0 - 8 && g.z < bd.z1 + 8 && g.y < bd.h) {
          g.vx *= -0.9; g.vz *= -0.9;
        }
      }
      if (g.stepT >= 0.60) {
        g.state = 'pop';
        g.stepT = 0;
        confettiPopTotal++;
        setTimeout(() => playSfx('mini_pop', 0.85, 0.95 + Math.random() * 0.16), 130);
      }
      continue;
    }

    // Random helium giggling & screaming chorus!
    g.nextLaugh -= dt;
    if (g.nextLaugh <= 0) {
      const clips = ['mini_giggle1', 'mini_giggle2', 'mini_giggle3', 'mini_scream1'];
      const pick = clips[Math.floor(Math.random() * clips.length)];
      const cPos = worldToCam(g.x, g.y, g.z);
      const dist = Math.hypot(cPos.x, cPos.y, cPos.z);
      const vol = Math.max(0.08, Math.min(0.62, 110 / Math.max(55, dist)));
      const pan = Math.max(-0.9, Math.min(0.9, cPos.x / 120));
      playSfx(pick, vol, 0.94 + Math.random() * 0.16, pan);
      g.nextLaugh = 0.85 + Math.random() * 1.15;
    }

    if (g.age > 17.5) {
      g.state = 'pop'; g.stepT = 0; confettiPopTotal++;
      setTimeout(() => playSfx('mini_pop', 0.7, 1.0), 120);
      continue;
    }

    // Target coordinates
    let tx = 0, ty = 0, tz = 0;
    if (g.target === 'player' || targetSelfMode) {
      g.target = 'player';
      tx = cam.x; ty = 14; tz = cam.z;
    } else {
      let bBest = bots[0], dBest = 99999;
      for (const b of bots) {
        const d = Math.hypot(b.x - g.x, b.z - g.z);
        if (d < dBest) { dBest = d; bBest = b; }
      }
      g.target = bBest;
      tx = bBest.x; ty = 16; tz = bBest.z;
    }

    if (g.state === 'wall' && g.wallBox) {
      // Drive straight UP the 3D building wall on spinning tires!
      g.y += 130 * dt;
      if (g.y >= g.wallBox.h) {
        g.y = g.wallBox.h + 2;
        g.state = 'search';
        const angTo = Math.atan2(tz - g.z, tx - g.x);
        g.vx = Math.cos(angTo) * 165;
        g.vz = Math.sin(angTo) * 165;
        g.vy = 115;
        playSfx('mini_boing', 0.45, 1.08);
        g.wallBox = null;
      }
      continue;
    }

    // POST-3-LAP ATTACK FRENZY ('attack') — Unleashed ONLY after 3 full driving laps (1080 deg)!
    if (g.state === 'attack') {
      activeAttackers++;
      if (g.age >= g.attackEnd) {
        g.state = 'pop';
        g.stepT = 0;
        confettiPopTotal++;
        setTimeout(() => playSfx('mini_pop', 0.85, 0.95 + Math.random() * 0.16), 130);
        continue;
      }
      const angTo = Math.atan2(tz - g.z, tx - g.x);
      g.yaw = angTo;
      const distT = Math.hypot(tx - g.x, tz - g.z);
      const chgSpd = 175 + g.role * 16;
      g.vx = Math.cos(angTo) * chgSpd;
      g.vz = Math.sin(angTo) * chgSpd;
      g.vy -= 360 * dt;
      g.x += g.vx * dt;
      g.y += g.vy * dt;
      g.z += g.vz * dt;
      if (g.y <= 0) {
        g.y = 0;
        g.vy = 125 + Math.random() * 55;
        playSfx('mini_boing', 0.28, 1.02 + Math.random() * 0.16);
      }
      if (distT < 36) {
        g.nextPoke -= dt;
        if (g.nextPoke <= 0) {
          g.nextPoke = 0.72 + Math.random() * 0.40;
          if (g.target === 'player') {
            if (playerHp > 1) playerHp = Math.max(1, playerHp - 1);
          } else if (g.target && g.target.hp > 1) {
            g.target.hp = Math.max(1, g.target.hp - 1);
          }
          // Bounce slightly back after ramming so they keep lunging repeatedly!
          g.x -= Math.cos(angTo) * 14;
          g.z -= Math.sin(angTo) * 14;
        }
      }
      continue;
    }

    // SWARM & WHEEL-DRIVE 3 FULL LAPS FIRST ('orbit') — ZERO attacks / ZERO damage during Laps 1..3!
    if (g.state === 'orbit') {
      activeOrbiters++;
      const angSpd = (5.4 + g.role * 0.65) * g.orbitDir; // ~0.92 laps/sec -> 3 full laps in ~3.2s!
      g.orbitAng += angSpd * dt;
      g.orbitDeg += Math.abs(angSpd * dt) * (180 / Math.PI);
      maxOrbitLaps = Math.max(maxOrbitLaps, g.orbitDeg / 360);

      const gx = tx + Math.cos(g.orbitAng) * g.orbitRad;
      const gz = tz + Math.sin(g.orbitAng) * g.orbitRad;
      g.x += (gx - g.x) * Math.min(1, dt * 12);
      g.z += (gz - g.z) * Math.min(1, dt * 12);
      g.y = Math.max(0, g.y - 280 * dt); // Tires stay smoothly planted on the floor while driving!

      // Face forward along the driving circle tangent so they visibly MOTOR around the enemy!
      const tangX = -Math.sin(g.orbitAng) * g.orbitDir;
      const tangZ =  Math.cos(g.orbitAng) * g.orbitDir;
      g.yaw = Math.atan2(tangZ, tangX);

      // Completed 3 full driving laps (3 * 360 = 1080°) -> UNLEASH SWARM ATTACK!
      if (g.orbitDeg >= 1080) {
        g.state = 'attack';
        g.attackEnd = g.age + 4.2 + Math.random() * 1.2;
        g.vy = 135 + Math.random() * 45;
        playSfx('mini_scream1', 0.45, 1.04 + Math.random() * 0.10);
      }
      continue;
    }

    // State === 'search': Smooth grounded Seated Wheel-Driving + Building Wall-Drive!
    const distT = Math.hypot(tx - g.x, tz - g.z);
    if (distT < 74 && g.y < 36) {
      g.state = 'orbit';
      g.orbitAng = Math.atan2(g.z - tz, g.x - tx);
      continue;
    }

    // Steer smoothly like a low-rider go-kart toward target (role 2 visits nearby building wall first!)
    let goalX = tx, goalZ = tz;
    if (g.role === 2 && g.age < 3.4) {
      const bNear = BUILDINGS[i % BUILDINGS.length];
      goalX = (bNear.x0 + bNear.x1) * 0.5;
      goalZ = bNear.z0 - 4;
    }
    const wantYaw = Math.atan2(goalZ - g.z, goalX - g.x) + Math.sin(g.animT * 3.8) * 0.18;
    let dYaw = wantYaw - g.yaw;
    while (dYaw > Math.PI) dYaw -= Math.PI * 2;
    while (dYaw < -Math.PI) dYaw += Math.PI * 2;
    g.yaw += Math.max(-7.5 * dt, Math.min(7.5 * dt, dYaw));

    const driveSpd = 148 + g.role * 18;
    g.vx = Math.cos(g.yaw) * driveSpd;
    g.vz = Math.sin(g.yaw) * driveSpd;
    g.vy -= 380 * dt;

    // Ground / Rooftop support (tires stay smoothly planted on floor!)
    let floorH = 0;
    for (const bd of BUILDINGS) {
      if (g.x >= bd.x0 && g.x <= bd.x1 && g.z >= bd.z0 && g.z <= bd.z1 && g.y >= bd.h - 8) {
        floorH = Math.max(floorH, bd.h);
      }
    }
    g.x += g.vx * dt;
    g.y += g.vy * dt;
    g.z += g.vz * dt;

    if (g.y <= floorH) {
      g.y = floorH;
      g.vy = 0;
    }

    // Building collision -> Drive straight UP the vertical building wall!
    for (const bd of BUILDINGS) {
      if (g.x > bd.x0 - 6 && g.x < bd.x1 + 6 && g.z > bd.z0 - 6 && g.z < bd.z1 + 6 && g.y < bd.h - 6) {
        g.state = 'wall';
        g.wallBox = bd;
        const dL = Math.abs(g.x - bd.x0), dR = Math.abs(g.x - bd.x1);
        const dF = Math.abs(g.z - bd.z0), dB = Math.abs(g.z - bd.z1);
        const mMin = Math.min(dL, dR, dF, dB);
        if (mMin === dF) g.z = bd.z0 - 6;
        else if (mMin === dB) g.z = bd.z1 + 6;
        else if (mMin === dL) g.x = bd.x0 - 6;
        else g.x = bd.x1 + 6;
        break;
      }
    }
  }

  // Update HUD
  document.getElementById('hudHp').textContent = playerHp + '%';
  document.getElementById('hudSwarmCount').innerHTML = `ACTIVE GREEN MEN: <b>${gremlins.length}</b> &nbsp;|&nbsp; CONFETTI POPS: <b>${confettiPopTotal}</b>`;
  const stEl = document.getElementById('hudOrbitStatus');
  if (activeAttackers > 0) {
    stEl.textContent = `3 LAPS COMPLETE — SWARM ATTACKING! (${activeAttackers} Lunging · Clamped >= 1 HP!)`;
  } else if (activeOrbiters > 0) {
    stEl.textContent = `WHEEL-DRIVING LAP ${Math.min(3.0, maxOrbitLaps).toFixed(1)} / 3.0 AROUND TARGET (0 DMG) -> THEN ATTACK!`;
  } else {
    stEl.textContent = 'Drives 3 Laps Around Enemy First (0 Dmg) -> Then Attacks! · Shoot for Spin!';
  }
}

function drawBoxFace(pts3d, fillCol, strokeCol, W, H) {
  const proj = pts3d.map(p => projectPt(p[0], p[1], p[2], W, H));
  if (proj.some(p => p === null)) return null;
  aCtx.beginPath();
  aCtx.moveTo(proj[0].sx, proj[0].sy);
  for (let i = 1; i < proj.length; i++) aCtx.lineTo(proj[i].sx, proj[i].sy);
  aCtx.closePath();
  aCtx.fillStyle = fillCol;
  aCtx.fill();
  if (strokeCol) {
    aCtx.strokeStyle = strokeCol;
    aCtx.lineWidth = 1.4;
    aCtx.stroke();
  }
  return (proj[0].z + proj[1].z + proj[2].z + proj[3].z) * 0.25;
}

function renderArena() {
  const W = aCanvas.width, H = aCanvas.height;
  const horizonY = H * 0.5 + Math.tan(cam.pitch) * FOV_F;

  // Sky & Quake Arena Horizon
  const skyG = aCtx.createLinearGradient(0, 0, 0, Math.max(10, horizonY));
  skyG.addColorStop(0, '#071117');
  skyG.addColorStop(1, '#162b24');
  aCtx.fillStyle = skyG;
  aCtx.fillRect(0, 0, W, Math.max(0, horizonY));

  const flrG = aCtx.createLinearGradient(0, Math.max(0, horizonY), 0, H);
  flrG.addColorStop(0, '#14201c');
  flrG.addColorStop(1, '#0b1114');
  aCtx.fillStyle = flrG;
  aCtx.fillRect(0, Math.max(0, horizonY), W, H);

  // Perspective Floor Grid
  aCtx.strokeStyle = 'rgba(92, 180, 120, 0.16)';
  aCtx.lineWidth = 1;
  for (let gx = -300; gx <= 300; gx += 50) {
    const p0 = projectPt(gx, 0, -300, W, H);
    const p1 = projectPt(gx, 0, 320, W, H);
    if (p0 && p1) { aCtx.beginPath(); aCtx.moveTo(p0.sx, p0.sy); aCtx.lineTo(p1.sx, p1.sy); aCtx.stroke(); }
  }
  for (let gz = -300; gz <= 300; gz += 50) {
    const p0 = projectPt(-300, 0, gz, W, H);
    const p1 = projectPt(300, 0, gz, W, H);
    if (p0 && p1) { aCtx.beginPath(); aCtx.moveTo(p0.sx, p0.sy); aCtx.lineTo(p1.sx, p1.sy); aCtx.stroke(); }
  }

  // Depth-sorted 3D drawables (building faces + bots + jars + smoke bursts + 12 mini-gremlins!)
  const drawables = [];

  for (const b of BUILDINGS) {
    const { x0, x1, z0, z1, h } = b;
    const faces = [
      { pts: [[x0,0,z0],[x1,0,z0],[x1,h,z0],[x0,h,z0]], col: b.col1 },
      { pts: [[x1,0,z1],[x0,0,z1],[x0,h,z1],[x1,h,z1]], col: b.col1 },
      { pts: [[x0,0,z1],[x0,0,z0],[x0,h,z0],[x0,h,z1]], col: b.col2 },
      { pts: [[x1,0,z0],[x1,0,z1],[x1,h,z1],[x1,h,z0]], col: b.col2 },
      { pts: [[x0,h,z0],[x1,h,z0],[x1,h,z1],[x0,h,z1]], col: '#1f3330' }
    ];
    for (const f of faces) {
      const cx = (f.pts[0][0] + f.pts[2][0]) * 0.5;
      const cy = (f.pts[0][1] + f.pts[2][1]) * 0.5;
      const cz = (f.pts[0][2] + f.pts[2][2]) * 0.5;
      const c = worldToCam(cx, cy, cz);
      if (c.z > 8) {
        drawables.push({ z: c.z, draw: () => drawBoxFace(f.pts, f.col, b.trim, W, H) });
      }
    }
  }

  // Enemy Bots (rendered using full-size Green-Suit / Arena Target hologram + orbit counter!)
  for (const b of bots) {
    const p = projectPt(b.x, 0, b.z, W, H);
    if (!p) continue;
    drawables.push({
      z: p.z,
      draw: () => {
        const bh = 46 * p.scale;
        const bw = 24 * p.scale;
        aCtx.fillStyle = 'rgba(0,0,0,0.45)';
        aCtx.beginPath(); aCtx.ellipse(p.sx, p.sy, bw * 0.7, bw * 0.25, 0, 0, Math.PI * 2); aCtx.fill();
        // Stylish Quake Bot Armor Silhouette
        aCtx.fillStyle = '#3c556e';
        aCtx.strokeStyle = '#7ce2ff';
        aCtx.lineWidth = 2;
        aCtx.fillRect(p.sx - bw * 0.45, p.sy - bh, bw * 0.9, bh * 0.85);
        aCtx.strokeRect(p.sx - bw * 0.45, p.sy - bh, bw * 0.9, bh * 0.85);
        aCtx.fillStyle = '#ffd447';
        aCtx.beginPath(); aCtx.arc(p.sx, p.sy - bh * 1.12, bw * 0.34, 0, Math.PI * 2); aCtx.fill();
        aCtx.fillStyle = '#fff';
        aCtx.font = `bold ${Math.max(10, Math.min(15, 12 * p.scale))}px Segoe UI`;
        aCtx.textAlign = 'center';
        aCtx.fillText(`${b.label} (${b.hp} HP)`, p.sx, p.sy - bh * 1.38);
        aCtx.textAlign = 'left';
      }
    });
  }

  // Thrown Jars
  for (const j of jars) {
    const p = projectPt(j.x, j.y, j.z, W, H);
    if (!p) continue;
    drawables.push({
      z: p.z,
      draw: () => {
        const sz = 28 * p.scale;
        const idx = Math.floor(j.t * 48) % 24;
        drawAtlasCell(aCtx, 'proj_jar', idx, p.sx - sz * 0.5, p.sy - sz * 0.5, sz, sz);
      }
    });
  }

  // Igniting Green Smoke Bursts
  for (const b of bursts) {
    const p = projectPt(b.x, b.y, b.z, W, H);
    if (!p) continue;
    drawables.push({
      z: p.z - 2,
      draw: () => {
        const sz = 92 * p.scale;
        const idx = Math.min(35, Math.floor((b.t / 0.65) * 36));
        drawAtlasCell(aCtx, 'smoke_burst', idx, p.sx - sz * 0.5, p.sy - sz * 0.65, sz, sz);
      }
    });
  }

  // 12 Bigger Wheel-Driving Green Men (16-Angle Seated Wheel-Drive / Wall-Drive / Post-3-Lap Attack / Spin / Confetti Pop!)
  for (const g of gremlins) {
    const p = projectPt(g.x, g.y, g.z, W, H);
    if (!p) continue;
    drawables.push({
      z: p.z,
      draw: () => {
        const sz = (g.state === 'pop' || g.state === 'spin' ? 60 : 52) * p.scale;
        if (g.state === 'spin') {
          const idx = Math.min(23, Math.floor((g.stepT / 0.60) * 24));
          drawAtlasCell(aCtx, 'mini_fx', idx, p.sx - sz * 0.5, p.sy - sz * 0.86, sz, sz);
        } else if (g.state === 'pop') {
          const idx = 24 + Math.min(23, Math.floor(g.stepT * 38));
          drawAtlasCell(aCtx, 'mini_fx', idx, p.sx - sz * 0.5, p.sy - sz * 0.86, sz, sz);
        } else {
          const viewYaw = Math.atan2(cam.z - g.z, cam.x - g.x);
          let rel = ((viewYaw - g.yaw) * 180 / Math.PI) % 360;
          if (rel < 0) rel += 360;
          const d16 = Math.floor(rel / 22.5 + 0.5) % 16;
          const f12 = Math.floor(g.animT * 34) % 12;
          const key = g.state === 'wall' ? 'wall_climb' : (g.state === 'attack' ? 'pogo_jump' : 'scurry');
          drawAtlasCell(aCtx, key, d16 * 12 + f12, p.sx - sz * 0.5, p.sy - sz * 0.89, sz, sz);
        }
      }
    });
  }

  drawables.sort((a, b) => b.z - a.z);
  for (const d of drawables) d.draw();

  // Blaster Tracers
  for (const tr of tracers) {
    const p0 = projectPt(tr.x0, tr.y0, tr.z0, W, H);
    const p1 = projectPt(tr.x1, tr.y1, tr.z1, W, H);
    if (p0 && p1) {
      aCtx.strokeStyle = `rgba(255, 230, 90, ${tr.t / 0.09})`;
      aCtx.lineWidth = 3;
      aCtx.beginPath(); aCtx.moveTo(p0.sx, p0.sy); aCtx.lineTo(p1.sx, p1.sy); aCtx.stroke();
    }
  }

  // Crosshair
  aCtx.strokeStyle = weaponSlot === 2 ? '#ff5ca8' : '#84ff46';
  aCtx.lineWidth = 2;
  aCtx.beginPath();
  aCtx.moveTo(W * 0.5 - 10, H * 0.5); aCtx.lineTo(W * 0.5 - 3, H * 0.5);
  aCtx.moveTo(W * 0.5 + 3, H * 0.5);  aCtx.lineTo(W * 0.5 + 10, H * 0.5);
  aCtx.moveTo(W * 0.5, H * 0.5 - 10); aCtx.lineTo(W * 0.5, H * 0.5 - 3);
  aCtx.moveTo(W * 0.5, H * 0.5 + 3);  aCtx.lineTo(W * 0.5, H * 0.5 + 10);
  aCtx.stroke();

  // First-Person Weapon Viewmodel Overlay!
  const walkBobX = (keys['KeyW'] || keys['KeyS'] || keys['KeyA'] || keys['KeyD']) ? Math.sin(performance.now() * 0.01) * 9 : 0;
  const walkBobY = (keys['KeyW'] || keys['KeyS'] || keys['KeyA'] || keys['KeyD']) ? Math.abs(Math.cos(performance.now() * 0.01)) * 7 : 0;

  if (weaponSlot === 1) {
    const vw = 435, vh = 465;
    const vx = W - vw - 38 + walkBobX;
    const vy = H - vh + 14 + walkBobY;
    if (vmState === 'idle') {
      const idx = Math.floor((vmTimer / 3.0) * 180) % 180;
      drawAtlasCell(aCtx, 'vm_idle', idx, vx, vy, vw, vh);
    } else if (vmState === 'shake') {
      const idx = Math.floor(vmTimer * 60) % 24;
      drawAtlasCell(aCtx, 'vm_action', idx, vx, vy, vw, vh);
    } else if (vmState === 'throw') {
      const idx = 24 + Math.min(17, Math.floor(vmTimer * 60));
      drawAtlasCell(aCtx, 'vm_action', idx, vx, vy, vw, vh);
    } else {
      const idx = 42 + Math.min(17, Math.floor(vmTimer * 60));
      drawAtlasCell(aCtx, 'vm_action', idx, vx, vy, vw, vh);
    }
  } else {
    // Sleek Quake Rapid Blaster Viewmodel for 1-Shot Gremlin Spinning!
    const rx = W - 310 + walkBobX + blasterRecoil * 18;
    const ry = H - 185 + walkBobY + blasterRecoil * 22;
    if (muzzleFlashT > 0) {
      const fg = aCtx.createRadialGradient(rx + 28, ry + 18, 4, rx + 28, ry + 18, 68);
      fg.addColorStop(0, 'rgba(255,255,200,0.95)');
      fg.addColorStop(0.5, 'rgba(255,140,40,0.65)');
      fg.addColorStop(1, 'rgba(255,80,20,0)');
      aCtx.fillStyle = fg;
      aCtx.beginPath(); aCtx.arc(rx + 28, ry + 18, 68, 0, Math.PI * 2); aCtx.fill();
    }
    aCtx.save();
    aCtx.translate(rx, ry);
    aCtx.rotate(0.22);
    aCtx.fillStyle = '#25313a';
    aCtx.strokeStyle = '#5ee6ff';
    aCtx.lineWidth = 3;
    aCtx.fillRect(0, 0, 290, 64);
    aCtx.strokeRect(0, 0, 290, 64);
    aCtx.fillStyle = '#ff5ca8';
    aCtx.fillRect(18, 16, 120, 14);
    aCtx.restore();
  }
}

// Main 60 FPS Loop
let lastT = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000);
  lastT = now;
  if (activeTab === 'arena') {
    updateArena(dt);
    renderArena();
  } else if (activeTab === 'studio') {
    renderStudio(dt);
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
</body>
</html>
"""


def main() -> None:
    upgrade_poster_typography()

    with open(os.path.join(PACK_DIR, "manifest.json"), "r", encoding="utf-8") as mf:
        manifest = json.load(mf)

    atlas_files = {
        "vm_idle": "vm_idle.webp",
        "vm_action": "vm_action.webp",
        "proj_jar": "proj_jar.webp",
        "smoke_burst": "smoke_burst.webp",
        "scurry": "mini_scurry.webp",
        "wall_climb": "mini_wall.webp",
        "pogo_jump": "mini_pogo.webp",
        "mini_fx": "mini_fx.webp",
    }
    atlas_b64 = {k: _b64_file(os.path.join(ATLAS_DIR, fn), "image/webp") for k, fn in atlas_files.items()}

    wav_names = [
        "jar_muffle1", "jar_muffle2", "jar_shake", "jar_throw", "jar_shatter",
        "mini_giggle1", "mini_giggle2", "mini_giggle3", "mini_scream1",
        "mini_spin_shriek", "mini_pop", "mini_boing",
    ]
    audio_b64 = {k: _b64_file(os.path.join(SND_DIR, f"{k}.wav"), "audio/wav") for k in wav_names}

    html = (
        HTML_TEMPLATE
        .replace("__MANIFEST_JSON__", json.dumps(manifest))
        .replace("__ATLAS_B64_JSON__", json.dumps(atlas_b64))
        .replace("__AUDIO_B64_JSON__", json.dumps(audio_b64))
    )

    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    # Also save as index.html inside `green_guy_jar_weapon/` for clean `/green-guy-jar/` directory URL!
    shutil.copy(OUT_HTML, os.path.join(PACK_DIR, "index.html"))
    sz_mb = os.path.getsize(OUT_HTML) / (1024.0 * 1024.0)
    print(f"Wrote self-contained {OUT_HTML} ({sz_mb:.2f} MB) + {os.path.join(PACK_DIR, 'index.html')}")


if __name__ == "__main__":
    main()
