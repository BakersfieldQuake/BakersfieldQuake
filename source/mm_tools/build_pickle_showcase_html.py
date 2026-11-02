"""Standalone Self-Contained Pickle Surprise Overhaul Showcase (`pickle_surprise_animations.html`).

Generates `G:\Quake\Combat\BakersfieldQuake\pickle_surprise_animations.html` featuring:
  1. Interactive First-Person VIOLENT OVERHAND WHIP-THROW Arena (60fps Quake viewport, click/Space to fire,
     choke-crush windup, 9-tap Gaussian shutter whip, snapping open-claw release, flying tumbling Pickle
     handoff -> sticky surface slap -> automatic giant deforming Diva balloon "PICKLE SURPRISE!" inflation &
     green pickle-shower explosion, slow-motion 0.15x/0.4x/1.0x, and frame-by-frame throw scrubber!).
  2. Interactive 360-Degree Deforming Diva Studio (all 16 angles x 4 expressive pose sets: Sing, Cheeky Pucker
     Wink, Bug-Eyes + Pink Tongue Out, and Full 16-Angle Giant Scream, rendered onto a live S-curve waving &
     balloon-swelling ribbon mesh!).
  3. Interactive WebGL 3D Model Viewer for both the 4-Clip Animated Watertight 3D `pickle3d` Character AND the
     360-Unwrapped 8-Expression 3D `pickle_bomb.md3` Sticky Grenade!
"""
from __future__ import annotations

import base64
import io
import json
import os
import struct
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

MOD = r"G:\Quake\Combat\BakersfieldQuake"
PROGS = os.path.join(MOD, "progs")
SOUND = os.path.join(MOD, "sound")
OUT_DIR = os.path.join(HERE, "out", "pickle_overhaul")
OUT_HTML = os.path.join(MOD, "pickle_surprise_animations.html")


def pil_to_webp_uri(im: Image.Image, quality: int = 86) -> str:
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=quality, method=4)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def file_to_data_uri(path: str, mime: str) -> str:
    raw = open(path, "rb").read()
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def build_grid_atlas(paths: list[str], tile_wh: tuple[int, int], cols: int, quality: int = 86) -> dict:
    tw, th = tile_wh
    rows = (len(paths) + cols - 1) // cols
    aw, ah = cols * tw, rows * th
    assert aw <= 4096 and ah <= 4096, f"Atlas too large: {aw}x{ah}"
    canvas = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
    for idx, p in enumerate(paths):
        im = Image.open(p).convert("RGBA")
        if im.size != (tw, th):
            im = im.resize((tw, th), Image.LANCZOS)
        r, c = divmod(idx, cols)
        canvas.paste(im, (c * tw, r * th))
    return dict(
        uri=pil_to_webp_uri(canvas, quality=quality),
        w=aw,
        h=ah,
        tw=tw,
        th=th,
        cols=cols,
        count=len(paths),
    )


def pack_f32_b64(arr: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(arr, dtype="<f4").tobytes()).decode("ascii")


def pack_u16_b64(arr: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(arr, dtype="<u2").tobytes()).decode("ascii")


def load_pickle_bomb_webgl() -> dict:
    md3 = md3lib.read(os.path.join(PROGS, "pickle_bomb.md3"))
    s = md3["surfaces"][0]
    verts, norms = s["frames"][0]
    v_arr = np.asarray(verts, dtype=np.float32)
    n_arr = np.asarray(norms, dtype=np.float32)
    uv_arr = np.asarray(s["st"], dtype=np.float32)
    tri_arr = np.asarray(s["tris"], dtype=np.uint16)

    face_paths = [os.path.join(OUT_DIR, "bomb_faces", f"bomb_face_{k:02d}.png") for k in range(8)]
    atlas = build_grid_atlas(face_paths, (256, 256), cols=8, quality=88)
    return dict(
        nf=1,
        nv=int(len(v_arr)),
        nt=int(len(tri_arr)),
        vertsB64=pack_f32_b64(v_arr[None, ...]),
        normsB64=pack_f32_b64(n_arr[None, ...]),
        uvsB64=pack_f32_b64(uv_arr),
        trisB64=pack_u16_b64(tri_arr),
        atlas=atlas,
        animFps=7.0,
        clips=[dict(id="wandering", label="👀 8-Expression Live Face Loop (360° Unwrap)", start=0, count=1, fps=7.0)],
    )


def load_pickle3d_webgl() -> dict:
    npz = np.load(os.path.join(OUT_DIR, "pickle3d_anim.npz"), allow_pickle=False)
    verts = npz["verts"].astype(np.float32)
    norms = npz["norms"].astype(np.float32)
    uvs = npz["uvs"].astype(np.float32)
    tris = npz["tris"].astype(np.uint16)
    clips = json.loads(str(npz["clips_json"]))

    # Center vertically around midpoint so orbit camera frames cleanly
    v_mid_z = 0.5 * (float(verts[0, :, 2].min()) + float(verts[0, :, 2].max()))
    verts = verts.copy()
    verts[:, :, 2] -= v_mid_z

    im_tex = Image.open(os.path.join(OUT_DIR, "pickle3d_srgb.png")).convert("RGB")
    if max(im_tex.size) > 1024:
        sc = 1024.0 / max(im_tex.size)
        im_tex = im_tex.resize((int(round(im_tex.width * sc)), int(round(im_tex.height * sc))), Image.LANCZOS)
    return dict(
        nf=int(verts.shape[0]),
        nv=int(verts.shape[1]),
        nt=int(tris.shape[0]),
        vertsB64=pack_f32_b64(verts),
        normsB64=pack_f32_b64(norms),
        uvsB64=pack_f32_b64(uvs),
        trisB64=pack_u16_b64(tris),
        texUri=pil_to_webp_uri(im_tex, quality=88),
        clips=clips,
    )


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pickle Surprise! — Violent Throw &amp; 360° Overhaul Showcase</title>
<style>
:root {
  --bg: #080d0f;
  --panel: #10191d;
  --panel2: #152329;
  --line: #233c44;
  --cyan: #24f0dc;
  --lime: #88ff66;
  --gold: #ffd45c;
  --pink: #ff5ca8;
  --ink: #eaf8f6;
  --mute: #8bb0b6;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: radial-gradient(circle at 20% 0%, #11282e 0%, var(--bg) 55%);
  color: var(--ink);
  font: 14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  overflow-x: hidden;
}
header {
  max-width: 1440px;
  margin: 0 auto;
  padding: 20px 22px 10px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.brand h1 {
  margin: 0;
  font-size: 25px;
  letter-spacing: -0.02em;
  background: linear-gradient(90deg, var(--cyan), var(--lime), var(--gold));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.brand p { margin: 4px 0 0; color: var(--mute); font-size: 13.5px; }
.badges { display: flex; flex-wrap: wrap; gap: 8px; }
.badge {
  padding: 5px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid var(--line);
  background: rgba(36, 240, 220, 0.09);
  color: var(--cyan);
}
.wrap {
  max-width: 1440px;
  margin: 0 auto;
  padding: 8px 22px 48px;
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  gap: 18px;
}
@media (max-width: 1120px) { .wrap { grid-template-columns: 1fr; } }
.card {
  background: linear-gradient(180deg, var(--panel) 0%, #0b1215 100%);
  border: 1px solid var(--line);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 18px 42px rgba(0,0,0,0.45);
  display: flex;
  flex-direction: column;
}
.card-hd {
  padding: 13px 16px;
  border-bottom: 1px solid var(--line);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: rgba(255,255,255,0.02);
}
.card-hd h2 { margin: 0; font-size: 16px; display: flex; align-items: center; gap: 8px; }
.sub { color: var(--mute); font-size: 12.5px; }
.arena-box {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  background: #070b0d;
  cursor: crosshair;
  user-select: none;
}
.arena-box canvas { width: 100%; height: 100%; display: block; }
.hud-overlay {
  position: absolute;
  left: 14px;
  top: 12px;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(6, 12, 14, 0.78);
  border: 1px solid rgba(36, 240, 220, 0.28);
  font-size: 12px;
  color: var(--ink);
}
.controls {
  padding: 12px 16px 15px;
  border-top: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
button {
  font: inherit;
  font-size: 12.5px;
  font-weight: 650;
  padding: 7px 13px;
  border-radius: 9px;
  border: 1px solid var(--line);
  background: var(--panel2);
  color: var(--ink);
  cursor: pointer;
  transition: 0.14s ease;
}
button:hover { border-color: var(--cyan); background: #1a3038; }
button.pri {
  background: linear-gradient(135deg, #16d6c4, #63e85e);
  color: #051614;
  border-color: transparent;
  font-weight: 800;
}
button.pri:hover { filter: brightness(1.08); }
button.act {
  border-color: var(--cyan);
  background: rgba(36, 240, 220, 0.18);
  color: var(--cyan);
}
input[type="range"] { flex: 1; accent-color: var(--cyan); min-width: 140px; }
.phase-lbl {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 12px;
  color: var(--gold);
  min-width: 245px;
}
.right-col { display: flex; flex-direction: column; gap: 18px; }
.stage-split {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10.5;
  background: radial-gradient(circle at 50% 42%, #173138 0%, #091013 72%);
  cursor: grab;
  user-select: none;
}
.stage-split:active { cursor: grabbing; }
.stage-split canvas { width: 100%; height: 100%; display: block; }
</style>
</head>
<body>
<header>
  <div class="brand">
    <h1>🥒 PICKLE SURPRISE! — Violent Throw &amp; 360° Character Overhaul</h1>
    <p>Rim-decontaminated studio sRGB · Rounded sequined crown dome · 9-tap shutter-blurred cross-screen violent throw · 36-frame deforming 64-skin Diva &amp; 4-clip 3D mesh</p>
  </div>
  <div class="badges">
    <span class="badge">v_pickle.md3 · 120 Skins (72 Idle + 48 Violent Throw)</span>
    <span class="badge">pickle.md3 · 36f Deforming Ribbon + 64 Skins (4×16)</span>
    <span class="badge">pickle3d · 4-Clip 3D Hull + 8-Face 3D Sticky Bomb</span>
  </div>
</header>

<div class="wrap">
  <!-- LEFT: INTERACTIVE FIRST-PERSON VIOLENT THROW SIMULATOR -->
  <section class="card">
    <div class="card-hd">
      <div>
        <h2>🥊 First-Person VIOLENT OVERHAND WHIP-THROW Simulator</h2>
        <div class="sub">Click anywhere in the arena (or press <b>Space</b>) to choke-squeeze &amp; violently whip-hurl a Pickle Surprise!</div>
      </div>
      <button class="pri" id="btnThrow">🔥 VIOLENT THROW! (Space)</button>
    </div>
    <div class="arena-box" id="arenaBox">
      <canvas id="arenaCanvas" width="960" height="600"></canvas>
      <div class="hud-overlay">
        <div class="pill" id="hudState">🟢 IDLE (24fps Optical-Flow Ping-Pong · Skin 000)</div>
        <div class="pill" id="hudAmmo">🥒 Pickles: <b>4 / 4</b> · Click viewport to hurl!</div>
      </div>
    </div>
    <div class="controls">
      <div class="row">
        <span style="color:var(--mute);font-size:12.5px">Playback Speed:</span>
        <button class="spd-btn act" data-spd="1">1.0× Real-Time</button>
        <button class="spd-btn" data-spd="0.4">0.4× Slow-Mo</button>
        <button class="spd-btn" data-spd="0.15">0.15× Ultra Slow-Mo</button>
        <button id="btnInfAmmo" class="act">∞ Unlimited Pickles: ON</button>
        <button id="btnSound" class="act">🔊 Sound: ON</button>
      </div>
      <div class="row">
        <span style="color:var(--mute);font-size:12.5px">Inspect Violent Throw Frame:</span>
        <input type="range" id="throwScrub" min="-1" max="47" value="-1">
        <span class="phase-lbl" id="scrubLabel">Live Interactive Mode (drag slider to scrub 0..47)</span>
        <button id="btnResumeLive">▶ Live</button>
      </div>
    </div>
  </section>

  <!-- RIGHT: 360° DEFORMING DIVA STUDIO + 3D WEBGL MODELS -->
  <div class="right-col">
    <section class="card">
      <div class="card-hd">
        <div>
          <h2>💃 360° Deforming Pickle Diva Balloon (64 Skins · Zero Shrinking!)</h2>
          <div class="sub">Drag horizontally to orbit all 16 angles · Base-planted S-curve wave + Pre-blast balloon swell</div>
        </div>
        <button id="btnPlaySurprise" class="pri">🔊 Trigger "Pickle Surprise!"</button>
      </div>
      <div class="stage-split" id="divaBox">
        <canvas id="divaCanvas" width="720" height="470"></canvas>
      </div>
      <div class="controls">
        <div class="row">
          <button class="pose-btn act" data-pose="-1">🎬 Auto Live Cycle</button>
          <button class="pose-btn" data-pose="0">🎵 Singing Diva (16v)</button>
          <button class="pose-btn" data-pose="1">😘 Cheeky Pucker Wink (16v)</button>
          <button class="pose-btn" data-pose="2">👅 Bug-Eyes + Pink Tongue (16v)</button>
          <button class="pose-btn" data-pose="3">😱 360° Giant Scream (16v)</button>
          <button id="btnAutoSpinDiva" class="act">🔄 Turntable Spin</button>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="card-hd">
        <div>
          <h2>🧊 Overhauled 3D Watertight Totem &amp; Sticky Bomb (WebGL)</h2>
          <div class="sub">Drag to orbit 3D · Scroll to zoom · Bright studio sRGB &amp; 360° turquoise gold-studded unwrap</div>
        </div>
      </div>
      <div class="stage-split" id="glBox">
        <canvas id="glCanvas" width="720" height="470"></canvas>
      </div>
      <div class="controls">
        <div class="row" id="glModelRow">
          <button class="gl-mdl-btn act" data-mdl="pickle3d">🗿 3D Pickle Character (4 Clips)</button>
          <button class="gl-mdl-btn" data-mdl="bomb">💣 3D Sticky Pickle Bomb (8 Live Faces)</button>
        </div>
        <div class="row" id="glClipRow"></div>
      </div>
    </section>
  </div>
</div>

<script>
const DATA = /*PAYLOAD_JSON*/;

// ---------------- WEBAUDIO SOUND ENGINE ----------------
let audioCtx = null;
let soundEnabled = true;
const audioBuffers = {};

async function ensureAudio() {
  if (!soundEnabled) return null;
  if (!audioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    audioCtx = new AC();
  }
  if (audioCtx.state === "suspended") await audioCtx.resume();
  for (const [k, uri] of Object.entries(DATA.sounds)) {
    if (!audioBuffers[k]) {
      const bin = atob(uri.split(",")[1]);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      audioBuffers[k] = await audioCtx.decodeAudioData(bytes.buffer.slice(0));
    }
  }
  return audioCtx;
}

function playSample(key, vol = 0.85, rate = 1.0) {
  if (!soundEnabled || !audioCtx || !audioBuffers[key]) return;
  const src = audioCtx.createBufferSource();
  src.buffer = audioBuffers[key];
  src.playbackRate.value = rate;
  const g = audioCtx.createGain();
  g.gain.value = vol;
  src.connect(g).connect(audioCtx.destination);
  src.start();
}

function playWhipWhoosh() {
  if (!soundEnabled || !audioCtx) return;
  const now = audioCtx.currentTime;
  const dur = 0.16;
  const buf = audioCtx.createBuffer(1, Math.floor(audioCtx.sampleRate * dur), audioCtx.sampleRate);
  const ch = buf.getChannelData(0);
  for (let i = 0; i < ch.length; i++) ch[i] = (Math.random() * 2 - 1) * Math.sin(Math.PI * i / ch.length);
  const src = audioCtx.createBufferSource();
  src.buffer = buf;
  const bp = audioCtx.createBiquadFilter();
  bp.type = "bandpass";
  bp.frequency.setValueAtTime(420, now);
  bp.frequency.exponentialRampToValueAtTime(1650, now + 0.06);
  bp.frequency.exponentialRampToValueAtTime(320, now + dur);
  bp.Q.value = 1.6;
  const g = audioCtx.createGain();
  g.gain.value = 0.85;
  src.connect(bp).connect(g).connect(audioCtx.destination);
  src.start(now);
}

function playBlastBoom() {
  if (!soundEnabled || !audioCtx) return;
  const now = audioCtx.currentTime;
  const osc = audioCtx.createOscillator();
  osc.type = "sawtooth";
  osc.frequency.setValueAtTime(135, now);
  osc.frequency.exponentialRampToValueAtTime(28, now + 0.42);
  const g = audioCtx.createGain();
  g.gain.setValueAtTime(0.55, now);
  g.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
  osc.connect(g).connect(audioCtx.destination);
  osc.start(now);
  osc.stop(now + 0.46);
}

// ---------------- LOAD ATLAS IMAGES ----------------
function loadImg(uri) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = rej;
    im.src = uri;
  });
}

function drawAtlasTile(ctx, im, meta, idx, dx, dy, dw, dh) {
  const i = Math.max(0, Math.min(meta.count - 1, idx | 0));
  const c = i % meta.cols;
  const r = (i / meta.cols) | 0;
  ctx.drawImage(im, c * meta.tw, r * meta.th, meta.tw, meta.th, dx, dy, dw, dh);
}

// Draw a vertical ribbon-warped Diva sprite with base planted at (cx, footY)!
function drawDeformingDiva2D(ctx, im, meta, tileIdx, cx, footY, drawW, drawH, waveTime, swellAmt) {
  const i = Math.max(0, Math.min(meta.count - 1, tileIdx | 0));
  const sx0 = (i % meta.cols) * meta.tw;
  const sy0 = ((i / meta.cols) | 0) * meta.th;
  const SLICES = 28;
  const stretch = (1.0 + 0.065 * Math.sin(waveTime * 11.0)) * (1.0 + 0.14 * swellAmt);
  const totalH = drawH * stretch;

  for (let s = 0; s < SLICES; s++) {
    const h0 = s / SLICES;
    const h1 = (s + 1) / SLICES;
    const hm = 0.5 * (h0 + h1); // 0 at bottom, 1 at top
    const srcY = sy0 + (1.0 - h1) * meta.th;
    const srcH = (meta.th / SLICES) + 0.9;

    const waveX = Math.pow(hm, 1.38) * (
      drawW * 0.12 * Math.sin(waveTime * 7.5 - 2.0 * hm) +
      drawW * 0.04 * Math.sin(waveTime * 15.0 - 3.2 * hm)
    ) * (1.0 - 0.5 * swellAmt);
    const shudderX = Math.pow(hm, 1.1) * swellAmt * drawW * 0.06 * Math.sin(waveTime * 48.0);
    const bulge = (1.0 / Math.sqrt(1.0 + 0.065 * Math.sin(waveTime * 11.0))) *
                  (1.0 + 0.36 * swellAmt * Math.sin(Math.PI * Math.pow(hm, 0.82)));

    const wSlice = drawW * bulge;
    const dstY = footY - h1 * totalH;
    const dstH = (totalH / SLICES) + 1.1;
    ctx.drawImage(im, sx0, Math.max(sy0, srcY), meta.tw, Math.min(meta.th, srcH), cx - wSlice * 0.5 + waveX + shudderX, dstY, wSlice, dstH);
  }
}

(async function init() {
  const [imIdle, imThrow, imDiva, imProj] = await Promise.all([
    loadImg(DATA.idleAtlas.uri),
    loadImg(DATA.throwAtlas.uri),
    loadImg(DATA.divaAtlas.uri),
    loadImg(DATA.projAtlas.uri),
  ]);

  // =========================================================================
  // 1. FIRST-PERSON VIOLENT THROW SIMULATOR
  // =========================================================================
  const arenaCv = document.getElementById("arenaCanvas");
  const actx = arenaCv.getContext("2d");
  const hudState = document.getElementById("hudState");
  const hudAmmo = document.getElementById("hudAmmo");
  const scrub = document.getElementById("throwScrub");
  const scrubLbl = document.getElementById("scrubLabel");

  let simSpeed = 1.0;
  let infAmmo = true;
  let ammo = 4;
  let regenTimer = 0;
  let simTime = 0;
  let throwActive = false;
  let throwU = 0;         // 0..1 across 0.65s violent throw cycle
  let launchedThisThrow = false;
  let aimX = 480, aimY = 265;
  let punchPitch = 0, punchRoll = 0;
  const projectiles = [];
  const particles = [];

  const THROW_DUR = 0.65; // 0.19s windup+whip + 0.24s open-claw shudder/slash + 0.22s belt-snatch!
  const RELEASE_U = 16.0 / 48.0; // exact frame 16 open-claw snap!

  function triggerViolentThrow() {
    ensureAudio();
    scrub.value = "-1";
    if (throwActive && throwU < 0.72) return;
    if (!infAmmo && ammo < 1) return;
    if (!infAmmo) ammo--;
    throwActive = true;
    throwU = 0.0;
    launchedThisThrow = false;
    playSample("throw", 0.90, 1.0);
  }

  document.getElementById("btnThrow").addEventListener("click", triggerViolentThrow);
  document.getElementById("arenaBox").addEventListener("pointerdown", (e) => {
    const r = arenaCv.getBoundingClientRect();
    aimX = ((e.clientX - r.left) / r.width) * arenaCv.width;
    aimY = Math.max(95, Math.min(470, ((e.clientY - r.top) / r.height) * arenaCv.height));
    triggerViolentThrow();
  });
  document.getElementById("arenaBox").addEventListener("pointermove", (e) => {
    const r = arenaCv.getBoundingClientRect();
    aimX = ((e.clientX - r.left) / r.width) * arenaCv.width;
    aimY = Math.max(95, Math.min(470, ((e.clientY - r.top) / r.height) * arenaCv.height));
  });
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      triggerViolentThrow();
    }
  });

  document.querySelectorAll(".spd-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".spd-btn").forEach(b => b.classList.remove("act"));
      btn.classList.add("act");
      simSpeed = parseFloat(btn.dataset.spd);
    });
  });
  document.getElementById("btnInfAmmo").addEventListener("click", (e) => {
    infAmmo = !infAmmo;
    if (infAmmo) ammo = 4;
    e.currentTarget.classList.toggle("act", infAmmo);
    e.currentTarget.textContent = infAmmo ? "∞ Unlimited Pickles: ON" : "∞ Unlimited Pickles: OFF";
  });
  document.getElementById("btnSound").addEventListener("click", (e) => {
    soundEnabled = !soundEnabled;
    e.currentTarget.classList.toggle("act", soundEnabled);
    e.currentTarget.textContent = soundEnabled ? "🔊 Sound: ON" : "🔇 Sound: OFF";
  });
  document.getElementById("btnResumeLive").addEventListener("click", () => {
    scrub.value = "-1";
    scrubLbl.textContent = "Live Interactive Mode (drag slider to scrub 0..47)";
  });

  function spawnFlyingPickle() {
    playWhipWhoosh();
    punchPitch = 18.0; // violent downward/forward camera slam!
    punchRoll = -3.8;
    projectiles.push({
      state: "fly",
      t: 0,
      x0: 560, y0: 330,
      tx: aimX, ty: Math.max(210, aimY),
      x: 560, y: 330,
      rot: -0.45,
      scale: 1.0,
      viewOff: Math.floor(Math.random() * 16),
    });
  }

  function spawnExplosion(x, y) {
    playBlastBoom();
    for (let i = 0; i < 42; i++) {
      const ang = Math.random() * Math.PI * 2;
      const spd = 90 + Math.random() * 340;
      particles.push({
        x, y: y - 55,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd - 120,
        r: 4 + Math.random() * 10,
        life: 0.55 + Math.random() * 0.55,
        age: 0,
        col: i % 3 === 0 ? "#ffd85c" : (i % 2 === 0 ? "#24f0dc" : "#7cff50"),
        isGib: i < 10,
        rot: Math.random() * 6.28,
      });
    }
  }

  let lastTs = performance.now();
  function tickArena(now) {
    const rawDt = Math.min(0.05, (now - lastTs) / 1000);
    lastTs = now;
    const dt = rawDt * simSpeed;
    simTime += dt;

    if (!infAmmo && ammo < 4) {
      regenTimer += dt;
      if (regenTimer >= 3.0) { regenTimer = 0; ammo++; }
    }

    const scrubVal = parseInt(scrub.value, 10);
    let vmMode = "idle";
    let vmIdx = 0;
    let lungeX = 0, lungeY = 0, lungeRot = 0;

    if (scrubVal >= 0) {
      vmMode = "throw";
      vmIdx = scrubVal;
      const phaseName = scrubVal < 11 ? "Phase 1: Choke-Crush & High Windup" :
                        scrubVal < 16 ? "Phase 2: 9-Tap Blurred Cross-Screen Whip" :
                        scrubVal < 24 ? "Phase 3a: Splayed Open-Claw Recoil Shudder" :
                        scrubVal < 35 ? "Phase 3b: Empty Follow-Through Slash" :
                                        "Phase 4: Belt-Snatch Fresh Pickle Reload";
      scrubLbl.textContent = `Frame ${String(scrubVal).padStart(2, "0")}/47 (Skin ${72 + scrubVal}) — ${phaseName}`;
      hudState.innerHTML = `🔍 SCRUBBING THROW FRAME <b>${scrubVal}/47</b> (Skin ${72 + scrubVal})`;
    } else if (throwActive) {
      throwU += dt / THROW_DUR;
      if (!launchedThisThrow && throwU >= RELEASE_U) {
        launchedThisThrow = true;
        spawnFlyingPickle();
      }
      if (throwU < 0.22) {
        const w = Math.sin((throwU / 0.22) * Math.PI * 0.5);
        punchPitch = -9.0 * w;
        punchRoll = 2.0 * w;
        lungeX = 18 * w; lungeY = -10 * w; lungeRot = 0.03 * w;
      } else if (throwU < 0.42) {
        const w = Math.sin(((throwU - 0.22) / 0.20) * Math.PI);
        lungeX = -28 * w; lungeY = 8 * w; lungeRot = -0.04 * w;
      }
      if (!infAmmo && ammo < 1 && throwU >= 0.72) {
        throwActive = false;
      } else if (throwU >= 1.0) {
        throwActive = false;
        throwU = 0;
      }
      if (throwActive) {
        vmMode = "throw";
        vmIdx = Math.min(47, Math.floor(throwU * 48));
        hudState.innerHTML = `🔥 VIOLENT THROW · Frame <b>${vmIdx}/47</b> (Skin ${72 + vmIdx})`;
      }
    }

    if (scrubVal < 0 && !throwActive) {
      punchPitch *= Math.pow(0.001, dt);
      punchRoll *= Math.pow(0.001, dt);
      if (!infAmmo && ammo < 1) {
        vmMode = "hidden";
        hudState.innerHTML = `⏳ RECHARGING PICKLE (${(3.0 - regenTimer).toFixed(1)}s)...`;
      } else {
        const cyc = 72 * 2 - 2;
        const st = Math.floor(simTime * 24) % cyc;
        vmIdx = st >= 72 ? cyc - st : st;
        lungeX = Math.sin(simTime * 2.4) * 4.5;
        lungeY = Math.cos(simTime * 4.8) * 3.5;
        hudState.innerHTML = `🟢 24fps OPTICAL-FLOW IDLE · Skin <b>${String(vmIdx).padStart(3, "0")}</b>`;
      }
    } else if (scrubVal < 0) {
      punchPitch *= Math.pow(0.015, dt);
      punchRoll *= Math.pow(0.015, dt);
    }

    hudAmmo.innerHTML = `🥒 Pickles: <b>${infAmmo ? "∞" : ammo + " / 4"}</b> · Click or press Space to hurl!`;

    // Render Quake gothic arena background with camera punch shake
    const W = arenaCv.width, H = arenaCv.height;
    actx.save();
    actx.fillStyle = "#080d10";
    actx.fillRect(0, 0, W, H);
    actx.translate(W * 0.5, H * 0.5 + punchPitch);
    actx.rotate((punchRoll * Math.PI) / 180.0);
    actx.translate(-W * 0.5, -H * 0.5);

    const horizon = 235;
    const skyG = actx.createLinearGradient(0, 0, 0, horizon);
    skyG.addColorStop(0, "#0b171c");
    skyG.addColorStop(1, "#182e35");
    actx.fillStyle = skyG;
    actx.fillRect(-40, -40, W + 80, horizon + 40);

    const flrG = actx.createLinearGradient(0, horizon, 0, H + 40);
    flrG.addColorStop(0, "#122024");
    flrG.addColorStop(1, "#070d0f");
    actx.fillStyle = flrG;
    actx.fillRect(-40, horizon, W + 80, H - horizon + 80);

    // Perspective grid lines
    actx.strokeStyle = "rgba(36, 240, 220, 0.11)";
    actx.lineWidth = 1;
    for (let i = -8; i <= 8; i++) {
      actx.beginPath();
      actx.moveTo(W * 0.5 + i * 28, horizon);
      actx.lineTo(W * 0.5 + i * 195, H + 40);
      actx.stroke();
    }
    for (let r = 1; r <= 7; r++) {
      const yy = horizon + Math.pow(r / 7, 1.8) * (H - horizon);
      actx.beginPath();
      actx.moveTo(-40, yy);
      actx.lineTo(W + 40, yy);
      actx.stroke();
    }

    // Update & render in-world thrown Pickles (flight -> stick -> giant Diva "Pickle Surprise!" -> blast!)
    for (let i = projectiles.length - 1; i >= 0; i--) {
      const p = projectiles[i];
      p.t += dt;
      if (p.state === "fly") {
        const u = Math.min(1.0, p.t / 0.34);
        p.x = p.x0 + (p.tx - p.x0) * u;
        const arc = -115 * Math.sin(Math.PI * u);
        p.y = p.y0 + (p.ty - p.y0) * u + arc;
        p.rot = -0.48 - p.t * 14.0;
        p.scale = 1.0 - 0.58 * u;

        // Sequin trail particles
        if (Math.random() < 0.85) {
          particles.push({
            x: p.x, y: p.y,
            vx: (Math.random() - 0.5) * 40, vy: (Math.random() - 0.5) * 40,
            r: 3 + Math.random() * 4, life: 0.25, age: 0,
            col: Math.random() < 0.35 ? "#ffd85c" : "#24f0dc", isGib: false, rot: 0,
          });
        }
        const sz = 165 * p.scale;
        const pFrame = p.t < 0.05 ? 0 : (Math.floor((p.t - 0.05) * 20) % 8);
        actx.save();
        actx.translate(p.x, p.y);
        actx.rotate(p.rot);
        drawAtlasTile(actx, imProj, DATA.projAtlas, pFrame, -sz * 0.5, -sz * 0.5, sz, sz);
        actx.restore();

        if (u >= 1.0) {
          p.state = "stuck";
          p.t = 0;
          playSample("stick", 0.65, 0.85);
        }
      } else if (p.state === "stuck") {
        const sz = 52;
        actx.save();
        actx.translate(p.tx, p.ty);
        actx.fillStyle = "rgba(0,0,0,0.45)";
        actx.beginPath(); actx.ellipse(0, 8, 24, 8, 0, 0, Math.PI * 2); actx.fill();
        actx.rotate(1.35);
        drawAtlasTile(actx, imProj, DATA.projAtlas, 0, -sz * 0.5, -sz * 0.5, sz, sz);
        actx.restore();
        if (p.t >= 0.42) {
          p.state = "trip";
          p.t = 0;
          playSample("surprise", 0.95, 1.0);
        }
      } else if (p.state === "trip") {
        const inf = Math.min(1.0, p.t / 0.12);
        const ks = inf * inf * (3 - 2 * inf);
        const screamPhase = p.t >= 0.36 ? Math.min(1.0, (p.t - 0.36) / 0.34) : 0.0;
        const expr = screamPhase > 0 ? 3 : [0, 1, 2, 0, 2, 1][Math.floor(p.t * 11) % 6];
        const view = (Math.floor(p.t * 5) + p.viewOff) % 4 === 0 ? 0 : (p.t < 0.35 ? 0 : 1);
        const dH = (55 + 215 * ks);
        const dW = dH;

        actx.fillStyle = "rgba(0,0,0,0.5)";
        actx.beginPath(); actx.ellipse(p.tx, p.ty + 6, 36 * ks, 11 * ks, 0, 0, Math.PI * 2); actx.fill();
        drawDeformingDiva2D(actx, imDiva, DATA.divaAtlas, expr * 16 + view, p.tx, p.ty + 8, dW, dH, simTime, screamPhase);

        if (p.t >= 0.70) {
          spawnExplosion(p.tx, p.ty);
          projectiles.splice(i, 1);
        }
      }
    }

    // Update & render particles / flying pickle gibs
    for (let i = particles.length - 1; i >= 0; i--) {
      const pt = particles[i];
      pt.age += dt;
      if (pt.age >= pt.life) { particles.splice(i, 1); continue; }
      pt.x += pt.vx * dt;
      pt.y += pt.vy * dt;
      if (pt.isGib) pt.vy += 480 * dt;
      const alpha = 1.0 - pt.age / pt.life;
      actx.save();
      actx.globalAlpha = alpha;
      if (pt.isGib) {
        actx.translate(pt.x, pt.y);
        actx.rotate(pt.rot + pt.age * 12);
        drawAtlasTile(actx, imProj, DATA.projAtlas, i % 8, -18, -18, 36, 36);
      } else {
        actx.fillStyle = pt.col;
        actx.beginPath();
        actx.arc(pt.x, pt.y, pt.r * alpha, 0, Math.PI * 2);
        actx.fill();
      }
      actx.restore();
    }

    // Crosshair
    actx.strokeStyle = "rgba(136, 255, 102, 0.88)";
    actx.lineWidth = 2;
    actx.beginPath();
    actx.moveTo(aimX - 11, aimY); actx.lineTo(aimX - 4, aimY);
    actx.moveTo(aimX + 4, aimY);  actx.lineTo(aimX + 11, aimY);
    actx.moveTo(aimX, aimY - 11); actx.lineTo(aimX, aimY - 4);
    actx.moveTo(aimX, aimY + 4);  actx.lineTo(aimX, aimY + 11);
    actx.stroke();

    actx.restore();

    // Draw First-Person Viewmodel (`v_pickle.md3` 640x700 stage anchored flush bottom-right!)
    if (vmMode !== "hidden") {
      const vh = H * 0.94;
      const vw = vh * (640.0 / 700.0);
      const vx = W - vw + 18 + lungeX;
      const vy = H - vh + 14 + lungeY;
      actx.save();
      actx.translate(vx + vw * 0.65, vy + vh * 0.85);
      actx.rotate(lungeRot);
      actx.translate(-(vx + vw * 0.65), -(vy + vh * 0.85));
      if (vmMode === "idle") {
        drawAtlasTile(actx, imIdle, DATA.idleAtlas, vmIdx, vx, vy, vw, vh);
      } else {
        drawAtlasTile(actx, imThrow, DATA.throwAtlas, vmIdx, vx, vy, vw, vh);
      }
      actx.restore();
    }

    requestAnimationFrame(tickArena);
  }
  requestAnimationFrame(tickArena);

  // =========================================================================
  // 2. 360° DEFORMING PICKLE DIVA CHARACTER STUDIO
  // =========================================================================
  const divaCv = document.getElementById("divaCanvas");
  const dctx = divaCv.getContext("2d");
  let divaYaw = 0.0;
  let divaAutoSpin = true;
  let divaPoseMode = -1; // -1 = live cycle, 0..3 = fixed expression set
  let divaSurpriseT = -1;
  let dragDiva = false, lastDX = 0;

  document.getElementById("divaBox").addEventListener("pointerdown", (e) => {
    dragDiva = true; lastDX = e.clientX; divaAutoSpin = false;
    document.getElementById("btnAutoSpinDiva").classList.remove("act");
  });
  window.addEventListener("pointermove", (e) => {
    if (!dragDiva) return;
    divaYaw = (divaYaw + (e.clientX - lastDX) * 0.85 + 360) % 360;
    lastDX = e.clientX;
  });
  window.addEventListener("pointerup", () => { dragDiva = false; });

  document.getElementById("btnAutoSpinDiva").addEventListener("click", (e) => {
    divaAutoSpin = !divaAutoSpin;
    e.currentTarget.classList.toggle("act", divaAutoSpin);
  });
  document.querySelectorAll(".pose-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".pose-btn").forEach(b => b.classList.remove("act"));
      btn.classList.add("act");
      divaPoseMode = parseInt(btn.dataset.pose, 10);
    });
  });
  document.getElementById("btnPlaySurprise").addEventListener("click", async () => {
    await ensureAudio();
    playSample("surprise", 0.95, 1.0);
    divaSurpriseT = 0.0;
  });

  const POSE_NAMES = [
    "Set 0: Singing Diva ('Pickle...')",
    "Set 1: Cheeky Puffed-Cheek Wink",
    "Set 2: Wild Bug-Eyes + Pink Tongue Out",
    "Set 3: 360° Over-Pressurized Giant Scream",
  ];

  let lastDivaTs = performance.now();
  function tickDiva(now) {
    const dt = Math.min(0.05, (now - lastDivaTs) / 1000);
    lastDivaTs = now;
    if (divaAutoSpin) divaYaw = (divaYaw + dt * 42.0) % 360;
    const t = now / 1000;

    let expr = divaPoseMode;
    let swell = 0.0;
    if (divaSurpriseT >= 0) {
      divaSurpriseT += dt;
      if (divaSurpriseT < 0.42) {
        expr = [0, 1, 2, 0][Math.floor(divaSurpriseT * 10) % 4];
      } else if (divaSurpriseT < 0.88) {
        expr = 3;
        swell = Math.min(1.0, (divaSurpriseT - 0.42) / 0.36);
      } else {
        divaSurpriseT = -1;
      }
    }
    if (expr < 0) {
      const cyc = t % 4.4;
      if (cyc < 3.4) {
        expr = [0, 1, 2, 0, 2, 1][Math.floor(cyc * 3.5) % 6];
        swell = 0.0;
      } else {
        expr = 3;
        swell = Math.sin(((cyc - 3.4) / 1.0) * Math.PI);
      }
    } else if (expr === 3 && divaSurpriseT < 0) {
      swell = 0.55 + 0.35 * Math.sin(t * 4.5);
    }

    const view = Math.floor(divaYaw / 22.5 + 0.5) % 16;
    const W = divaCv.width, H = divaCv.height;
    dctx.clearRect(0, 0, W, H);

    // Studio floor ellipse
    dctx.fillStyle = "rgba(36, 240, 220, 0.08)";
    dctx.beginPath(); dctx.ellipse(W * 0.5, H - 36, 135, 26, 0, 0, Math.PI * 2); dctx.fill();
    dctx.strokeStyle = "rgba(36, 240, 220, 0.28)";
    dctx.beginPath(); dctx.ellipse(W * 0.5, H - 36, 135, 26, 0, 0, Math.PI * 2); dctx.stroke();

    drawDeformingDiva2D(dctx, imDiva, DATA.divaAtlas, expr * 16 + view, W * 0.5, H - 30, 395, 395, t, swell);

    dctx.fillStyle = "rgba(8, 14, 18, 0.78)";
    dctx.fillRect(14, 12, 435, 30);
    dctx.fillStyle = "#24f0dc";
    dctx.font = "600 12.5px system-ui, sans-serif";
    dctx.fillText(`Angle ${String(view).padStart(2, "0")}/15 (${Math.round(view * 22.5)}°) · Skin ${expr * 16 + view} · ${POSE_NAMES[expr]}`, 22, 31);

    requestAnimationFrame(tickDiva);
  }
  requestAnimationFrame(tickDiva);

  // =========================================================================
  // 3. WEBGL 3D PICKLE CHARACTER & 3D STICKY PICKLE BOMB VIEWER
  // =========================================================================
  const glCv = document.getElementById("glCanvas");
  const gl = glCv.getContext("webgl", { antialias: true, alpha: true });
  if (gl) {
    function b64ToF32(b64) {
      const bin = atob(b64);
      const u8 = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
      return new Float32Array(u8.buffer);
    }
    function b64ToU16(b64) {
      const bin = atob(b64);
      const u8 = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
      return new Uint16Array(u8.buffer);
    }

    const vsSrc = `
      attribute vec3 aPos0, aPos1, aNrm0, aNrm1;
      attribute vec2 aUv;
      uniform float uLerp;
      uniform mat4 uMVP;
      uniform mat3 uNMat;
      varying vec2 vUv;
      varying vec3 vNrm;
      void main() {
        vec3 p = mix(aPos0, aPos1, uLerp);
        vec3 n = normalize(uNMat * mix(aNrm0, aNrm1, uLerp));
        vUv = aUv;
        vNrm = n;
        gl_Position = uMVP * vec4(p, 1.0);
      }
    `;
    const fsSrc = `
      precision mediump float;
      varying vec2 vUv;
      varying vec3 vNrm;
      uniform sampler2D uTex;
      uniform vec2 uUvScale, uUvOff;
      void main() {
        vec3 n = normalize(vNrm);
        vec3 l1 = normalize(vec3(0.45, 0.35, 0.82));
        vec3 l2 = normalize(vec3(-0.6, -0.3, 0.4));
        float diff = 0.52 + 0.52 * max(dot(n, l1), 0.0) + 0.18 * max(dot(n, l2), 0.0);
        vec3 h = normalize(l1 + vec3(0.0, 0.0, 1.0));
        float spec = pow(max(dot(n, h), 0.0), 28.0) * 0.22;
        vec4 texel = texture2D(uTex, vUv * uUvScale + uUvOff);
        gl_FragColor = vec4(texel.rgb * diff + vec3(spec), 1.0);
      }
    `;
    function comp(type, src) {
      const sh = gl.createShader(type);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      return sh;
    }
    const prog = gl.createProgram();
    gl.attachShader(prog, comp(gl.VERTEX_SHADER, vsSrc));
    gl.attachShader(prog, comp(gl.FRAGMENT_SHADER, fsSrc));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const loc = {
      p0: gl.getAttribLocation(prog, "aPos0"),
      p1: gl.getAttribLocation(prog, "aPos1"),
      n0: gl.getAttribLocation(prog, "aNrm0"),
      n1: gl.getAttribLocation(prog, "aNrm1"),
      uv: gl.getAttribLocation(prog, "aUv"),
      lerp: gl.getUniformLocation(prog, "uLerp"),
      mvp: gl.getUniformLocation(prog, "uMVP"),
      nmat: gl.getUniformLocation(prog, "uNMat"),
      uvS: gl.getUniformLocation(prog, "uUvScale"),
      uvO: gl.getUniformLocation(prog, "uUvOff"),
    };

    async function uploadTex(uri) {
      const im = await loadImg(uri);
      const tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      return tex;
    }

    function prepModel(m, tex) {
      const verts = b64ToF32(m.vertsB64);
      const norms = b64ToF32(m.normsB64);
      const uvs = b64ToF32(m.uvsB64);
      const tris = b64ToU16(m.trisB64);
      const stride = m.nv * 3;
      const frameBufs = [];
      for (let f = 0; f < m.nf; f++) {
        const vb = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, vb);
        gl.bufferData(gl.ARRAY_BUFFER, verts.subarray(f * stride, (f + 1) * stride), gl.STATIC_DRAW);
        const nb = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, nb);
        gl.bufferData(gl.ARRAY_BUFFER, norms.subarray(f * stride, (f + 1) * stride), gl.STATIC_DRAW);
        frameBufs.push({ vb, nb });
      }
      const uvb = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, uvb);
      gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);
      const ib = gl.createBuffer();
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, tris, gl.STATIC_DRAW);
      return { ...m, frameBufs, uvb, ib, tex, idxCount: tris.length };
    }

    const [tex3d, texBomb] = await Promise.all([
      uploadTex(DATA.pickle3d.texUri),
      uploadTex(DATA.pickleBomb.atlas.uri),
    ]);
    const glModels = {
      pickle3d: prepModel(DATA.pickle3d, tex3d),
      bomb: prepModel(DATA.pickleBomb, texBomb),
    };

    let curMdlKey = "pickle3d";
    let curClipIdx = 0;
    let camAz = -0.35, camEl = 0.16, camDist = 66.0;
    let glDrag = false, glLX = 0, glLY = 0;

    function renderClipButtons() {
      const row = document.getElementById("glClipRow");
      row.innerHTML = "";
      const m = glModels[curMdlKey];
      m.clips.forEach((c, idx) => {
        const b = document.createElement("button");
        b.textContent = c.label;
        if (idx === curClipIdx) b.className = "act";
        b.addEventListener("click", () => { curClipIdx = idx; renderClipButtons(); });
        row.appendChild(b);
      });
    }
    renderClipButtons();

    document.querySelectorAll(".gl-mdl-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".gl-mdl-btn").forEach(b => b.classList.remove("act"));
        btn.classList.add("act");
        curMdlKey = btn.dataset.mdl;
        curClipIdx = 0;
        camDist = curMdlKey === "pickle3d" ? 66.0 : 18.0;
        camAz = curMdlKey === "pickle3d" ? -0.35 : 1.57;
        camEl = curMdlKey === "pickle3d" ? 0.16 : 0.25;
        renderClipButtons();
      });
    });

    const glBox = document.getElementById("glBox");
    glBox.addEventListener("pointerdown", (e) => { glDrag = true; glLX = e.clientX; glLY = e.clientY; });
    window.addEventListener("pointermove", (e) => {
      if (!glDrag) return;
      camAz += (e.clientX - glLX) * 0.01;
      camEl = Math.max(-1.2, Math.min(1.2, camEl + (e.clientY - glLY) * 0.01));
      glLX = e.clientX; glLY = e.clientY;
    });
    window.addEventListener("pointerup", () => { glDrag = false; });
    glBox.addEventListener("wheel", (e) => {
      e.preventDefault();
      camDist = Math.max(8.0, Math.min(140.0, camDist * (e.deltaY > 0 ? 1.08 : 0.92)));
    }, { passive: false });

    function mat4Mul(a, b) {
      const o = new Float32Array(16);
      for (let c = 0; c < 4; c++)
        for (let r = 0; r < 4; r++)
          o[c * 4 + r] = a[0 * 4 + r] * b[c * 4 + 0] + a[1 * 4 + r] * b[c * 4 + 1] + a[2 * 4 + r] * b[c * 4 + 2] + a[3 * 4 + r] * b[c * 4 + 3];
      return o;
    }
    function persp(fov, asp, zn, zf) {
      const f = 1.0 / Math.tan(fov * 0.5);
      const o = new Float32Array(16);
      o[0] = f / asp; o[5] = f; o[10] = (zf + zn) / (zn - zf); o[11] = -1; o[14] = (2 * zf * zn) / (zn - zf);
      return o;
    }
    function lookAt(ex, ey, ez) {
      let fx = -ex, fy = -ey, fz = -ez;
      const fl = Math.hypot(fx, fy, fz) || 1; fx /= fl; fy /= fl; fz /= fl;
      let sx = fy * 1 - fz * 0, sy = fz * 0 - fx * 1, sz = fx * 0 - fy * 0;
      // Quake Z-up! up = (0,0,1) => s = f x (0,0,1) = (fy, -fx, 0)
      sx = fy; sy = -fx; sz = 0;
      const sl = Math.hypot(sx, sy, sz) || 1; sx /= sl; sy /= sl;
      const ux = sy * fz - sz * fy, uy = sz * fx - sx * fz, uz = sx * fy - sy * fx;
      const o = new Float32Array(16);
      o[0] = sx; o[4] = sy; o[8] = sz;   o[12] = -(sx * ex + sy * ey + sz * ez);
      o[1] = ux; o[5] = uy; o[9] = uz;   o[13] = -(ux * ex + uy * ey + uz * ez);
      o[2] = -fx; o[6] = -fy; o[10] = -fz; o[14] = (fx * ex + fy * ey + fz * ez);
      o[15] = 1;
      return o;
    }

    gl.enable(gl.DEPTH_TEST);
    function tickGL(now) {
      const t = now / 1000;
      if (!glDrag) camAz += 0.005;
      gl.viewport(0, 0, glCv.width, glCv.height);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      const m = glModels[curMdlKey];
      const clip = m.clips[curClipIdx];
      let f0 = clip.start, f1 = clip.start, lerp = 0.0;
      if (clip.count > 1) {
        const pos = (t * clip.fps) % clip.count;
        const i0 = Math.floor(pos);
        f0 = clip.start + i0;
        f1 = clip.start + ((i0 + 1) % clip.count);
        lerp = pos - i0;
      }

      const ex = -camDist * Math.cos(camEl) * Math.cos(camAz);
      const ey =  camDist * Math.cos(camEl) * Math.sin(camAz);
      const ez =  camDist * Math.sin(camEl);
      const V = lookAt(ex, ey, ez);
      const P = persp(0.72, glCv.width / glCv.height, 1.0, 500.0);
      const MVP = mat4Mul(P, V);
      const NMat = new Float32Array([V[0], V[1], V[2], V[4], V[5], V[6], V[8], V[9], V[10]]);

      gl.useProgram(prog);
      gl.uniform1f(loc.lerp, lerp);
      gl.uniformMatrix4fv(loc.mvp, false, MVP);
      gl.uniformMatrix3fv(loc.nmat, false, NMat);

      if (curMdlKey === "bomb") {
        const fi = Math.floor(t * m.animFps) % 8;
        gl.uniform2f(loc.uvS, 1.0 / 8.0, 1.0);
        gl.uniform2f(loc.uvO, fi / 8.0, 0.0);
      } else {
        gl.uniform2f(loc.uvS, 1.0, 1.0);
        gl.uniform2f(loc.uvO, 0.0, 0.0);
      }

      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, m.tex);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.frameBufs[f0].vb);
      gl.enableVertexAttribArray(loc.p0);
      gl.vertexAttribPointer(loc.p0, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.frameBufs[f1].vb);
      gl.enableVertexAttribArray(loc.p1);
      gl.vertexAttribPointer(loc.p1, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.frameBufs[f0].nb);
      gl.enableVertexAttribArray(loc.n0);
      gl.vertexAttribPointer(loc.n0, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.frameBufs[f1].nb);
      gl.enableVertexAttribArray(loc.n1);
      gl.vertexAttribPointer(loc.n1, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.uvb);
      gl.enableVertexAttribArray(loc.uv);
      gl.vertexAttribPointer(loc.uv, 2, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.ib);
      gl.drawElements(gl.TRIANGLES, m.idxCount, gl.UNSIGNED_SHORT, 0);

      requestAnimationFrame(tickGL);
    }
    requestAnimationFrame(tickGL);
  }
})();
</script>
</body>
</html>
"""


def main() -> None:
    print("[1/3] Packing Violent Throw & Idle sprite atlases...")
    idle_paths = [os.path.join(OUT_DIR, "v_pickle", f"pvm_srgb_{i:03d}.png") for i in range(72)]
    throw_paths = [os.path.join(OUT_DIR, "v_pickle", f"pvm_srgb_{i:03d}.png") for i in range(72, 120)]
    diva_paths = [
        os.path.join(OUT_DIR, "diva_views", f"diva_s{s}_v{v:02d}.png")
        for s in range(4)
        for v in range(16)
    ]
    proj_paths = [os.path.join(OUT_DIR, "throw_sprite", f"pthr_srgb_{k:02d}.png") for k in range(8)]

    idle_atlas = build_grid_atlas(idle_paths, (312, 341), cols=9, quality=84)
    throw_atlas = build_grid_atlas(throw_paths, (384, 420), cols=8, quality=87)
    diva_atlas = build_grid_atlas(diva_paths, (320, 320), cols=8, quality=85)
    proj_atlas = build_grid_atlas(proj_paths, (256, 256), cols=8, quality=86)

    print("[2/3] Packing WebGL 3D `pickle3d` (4-clip) & `pickle_bomb` (8-face) + real game WAVs...")
    payload = dict(
        idleAtlas=idle_atlas,
        throwAtlas=throw_atlas,
        divaAtlas=diva_atlas,
        projAtlas=proj_atlas,
        pickle3d=load_pickle3d_webgl(),
        pickleBomb=load_pickle_bomb_webgl(),
        sounds=dict(
            throw=file_to_data_uri(os.path.join(SOUND, "pickle", "throw.wav"), "audio/wav"),
            surprise=file_to_data_uri(os.path.join(SOUND, "pickle", "surprise.wav"), "audio/wav"),
            stick=file_to_data_uri(os.path.join(SOUND, "weapons", "goopop.wav"), "audio/wav"),
        ),
    )

    print("[3/3] Writing self-contained `pickle_surprise_animations.html`...")
    html_out = HTML_TEMPLATE.replace("/*PAYLOAD_JSON*/", json.dumps(payload, separators=(",", ":")))
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_out)
    sz_mb = os.path.getsize(OUT_HTML) / (1024.0 * 1024.0)
    print(f"Wrote {OUT_HTML} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    main()
