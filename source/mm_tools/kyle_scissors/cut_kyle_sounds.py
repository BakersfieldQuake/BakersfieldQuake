"""Cut, clean, level, and preview Kyle Tillet ("fr_scissors") voice lines.

Reads the source MP3 recording, applies gentle de-rumble/presence EQ, STFT Wiener
noise reduction calibrated from the silent room gap (7.85s-9.05s), soft-knee
vocal compression + noise floor gating, slices all 15 clean takes plus 3 bonus
edited variants, resamples to 22050 Hz 16-bit mono PCM WAV (Quake standard),
and writes a self-contained HTML preview player under docs/.
"""

import argparse
import base64
import html
import io
import json
import os
import struct
import subprocess
import wave
import zipfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DEFAULT_SRC = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671"
    r"\.user_uploaded\uploaded_media_1795056040429.mp3"
)
DEFAULT_OUT_DIR = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671"
    r"\scratch\kyle_clips"
)
DEFAULT_HTML = os.path.join(REPO, "docs", "kyle_scissors_sound_preview.html")

WORK_SR = 48000
GAME_SR = 22050

# 15 clean takes (excluding 1.36s-1.56s broken "...and" fragment at the very start).
# Each entry: (id, category, title, transcript, suggested_role, t_start, t_end, notes)
TAKES = [
    ("whoa_01_short", "whoa", "Whoa! (Short)", "Whoa!", "Sight / Alert", 1.73, 2.24,
     "Short, punchy exclamation. Cleanly isolated after trimming the clipped 1.36s fragment."),
    ("whoa_02_wobble", "whoa", "Whoa-oh-oh! (Wobble)", "Whoa-oh-oh!", "Chase / Idle Loop", 2.57, 3.76,
     "Warbly descending whoa; great comedic chase or idle chatter."),
    ("whoa_03_rise", "whoa", "Whoa-oh-oh-oh! (Rising)", "Whoa-oh-oh-oh!", "Chase / Taunt", 14.07, 15.34,
     "Excited rising warble with steady energy."),
    ("whoa_04_punch", "whoa", "Whoa! (Loud)", "Whoa!", "Aggro / Pain", 16.15, 17.10,
     "Louder, sharper exclamation with strong attack."),
    ("whoa_05_long", "whoa", "Whoa-oooh! (Long Yell)", "Whoa-oooh!", "Spawn / Charge", 22.36, 24.80,
     "Big 2.4s sustained yell. Leading inhale breath at 22.20s removed."),

    ("kyle_01_hey_high", "kyle", "Hey, it's Kyle! (High)", "Hey, it's Kyle!", "Spawn / Sight", 4.25, 5.02,
     "Upbeat high-inflection greeting. Trailing mouth click at 5.20s removed."),
    ("kyle_02_hey_bright", "kyle", "Hey, it's Kyle! (Bright)", "Hey, it's Kyle!", "Spawn / Sight", 5.45, 6.38,
     "Bright, clear delivery with crisp consonants."),
    ("kyle_03_its_kyle", "kyle", "It's Kyle.", "It's Kyle.", "Quick Intro / Ping", 7.09, 7.78,
     "Ultra-snappy 0.6s intro tag."),
    ("kyle_04_hey_fast", "kyle", "Hey, it's Kyle. (Snappy)", "Hey, it's Kyle.", "Spawn / Idle", 25.81, 26.52,
     "Fast conversational take. Pre-speech breath at 25.70s trimmed."),
    ("kyle_05_this_is_kyle", "kyle", "This is Kyle.", "This is Kyle.", "Spawn / Intro", 27.03, 27.88,
     "Direct, slightly deadpan identification."),

    ("cut_01_wheres_my_cut", "cut", "Where's my cut?!", "Whoa man, where's my cut?!", "Attack / Chase", 9.21, 10.52,
     "Panicked, angry demand — fits scissor-wielding pursuit."),
    ("cut_02_give_me_a_cut", "cut", "Give me a cut!", "Give me a cut!", "Melee / Lunge", 17.75, 18.80,
     "Aggressive bark; original peak hit 0.0 dBFS and was cleanly tamed."),
    ("cut_03_hey_man_cut", "cut", "Hey man, uh, cut?", "Hey man, uh, you gonna give me a cut?", "Idle / Approach", 19.67, 21.36,
     "Awkward, creepy barber question; leveled up ~4 dB to match the other lines."),
]


def decode_audio(path, af=None, sr=WORK_SR):
    """Decode audio file to float64 mono numpy array via ffmpeg."""
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if af:
        cmd += ["-af", af]
    cmd += ["-f", "f32le", "-ac", "1", "-ar", str(sr), "pipe:1"]
    proc = subprocess.run(cmd, capture_output=True, check=True)
    return np.frombuffer(proc.stdout, "<f4").astype(np.float64)


def resample_to_game_sr(x, src_sr=WORK_SR, dst_sr=GAME_SR):
    """High-quality ffmpeg resample from src_sr float32 to dst_sr float64."""
    raw = x.astype("<f4").tobytes()
    cmd = [
        "ffmpeg", "-v", "error",
        "-f", "f32le", "-ac", "1", "-ar", str(src_sr), "-i", "pipe:0",
        "-af", f"aresample={dst_sr}:resampler=soxr",
        "-f", "f32le", "-ac", "1", "-ar", str(dst_sr), "pipe:1",
    ]
    try:
        proc = subprocess.run(cmd, input=raw, capture_output=True, check=True)
    except subprocess.CalledProcessError:
        cmd[cmd.index(f"aresample={dst_sr}:resampler=soxr")] = f"aresample={dst_sr}"
        proc = subprocess.run(cmd, input=raw, capture_output=True, check=True)
    return np.frombuffer(proc.stdout, "<f4").astype(np.float64)


def wiener_denoise(x, sr, noise_t0=7.85, noise_t1=9.05, alpha=2.6, floor=0.03):
    """STFT Wiener spectral denoiser using measured noise floor from a silent gap."""
    nfft = 2048
    hop = 512
    win = np.hanning(nfft)
    padded = np.pad(x, (nfft, nfft))
    frames = np.lib.stride_tricks.sliding_window_view(padded, nfft)[::hop]
    Z = np.fft.rfft(frames * win, axis=1)
    mag2 = np.abs(Z) ** 2

    f0 = int((noise_t0 * sr + nfft) / hop)
    f1 = int((noise_t1 * sr + nfft) / hop)
    noise_psd = np.mean(mag2[f0:f1], axis=0, keepdims=True)

    snr_post = mag2 / np.maximum(noise_psd, 1e-18)
    gain = np.maximum(1.0 - alpha / np.maximum(snr_post, 1e-8), floor)

    # 3-tap smoothing in time and frequency avoids musical-noise chirping.
    g = gain.copy()
    g[1:-1] = 0.25 * gain[:-2] + 0.50 * gain[1:-1] + 0.25 * gain[2:]
    g[:, 1:-1] = 0.20 * g[:, :-2] + 0.60 * g[:, 1:-1] + 0.20 * g[:, 2:]

    rec_frames = np.fft.irfft(Z * g, n=nfft, axis=1) * win
    out = np.zeros(len(x) + 2 * nfft + nfft)
    norm = np.zeros_like(out)
    w2 = win ** 2
    for i in range(len(rec_frames)):
        pos = i * hop
        out[pos:pos + nfft] += rec_frames[i]
        norm[pos:pos + nfft] += w2
    return (out / np.maximum(norm, 1e-8))[nfft:nfft + len(x)]


def compress_and_gate(x, sr):
    """Gentle vocal leveling + soft downward gate on silence + soft-clip ceiling."""
    abs_x = np.abs(x)
    att = np.exp(-1.0 / (0.005 * sr))
    rel = np.exp(-1.0 / (0.090 * sr))
    env = np.zeros_like(x)
    cur = 0.0
    for i in range(len(x)):
        v = abs_x[i]
        cur = att * cur + (1.0 - att) * v if v > cur else rel * cur + (1.0 - rel) * v
        env[i] = cur

    env_db = 20.0 * np.log10(np.maximum(env, 1e-8))
    gain_db = np.zeros_like(env_db)

    # Downward compression above -20 dBFS (2.4:1)
    comp_mask = env_db > -20.0
    gain_db[comp_mask] = (-20.0 + (env_db[comp_mask] + 20.0) / 2.4) - env_db[comp_mask]

    # Soft downward expansion below -40 dBFS to keep pauses dead-quiet
    gate_mask = env_db < -40.0
    gain_db[gate_mask] = np.maximum(-18.0, (env_db[gate_mask] + 40.0) * 0.7)

    y = x * (10.0 ** (gain_db / 20.0))
    # Smooth tanh soft limiter above ~0.82
    return 0.90 * np.tanh(y / 0.90)


def trim_silence(seg, sr, thresh_db=-44.0, pad_in=0.012, pad_out=0.028):
    """Trim leading/trailing silence below thresh_db while keeping safe consonant pads."""
    hop = int(0.005 * sr)
    rms = np.array([
        np.sqrt(np.mean(seg[i:i + hop] ** 2))
        for i in range(0, max(1, len(seg) - hop), hop)
    ])
    db = 20.0 * np.log10(np.maximum(rms, 1e-8))
    idx = np.where(db > thresh_db)[0]
    if len(idx) == 0:
        return seg
    s = max(0, idx[0] * hop - int(pad_in * sr))
    e = min(len(seg), (idx[-1] + 1) * hop + int(pad_out * sr))
    return seg[s:e]


def apply_fades(seg, sr, fade_in_s=0.008, fade_out_s=0.024):
    """Apply smooth raised-cosine fade-in and fade-out."""
    out = seg.copy()
    fi = min(int(fade_in_s * sr), len(out) // 4)
    fo = min(int(fade_out_s * sr), len(out) // 4)
    if fi > 0:
        out[:fi] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(fi) / fi))
    if fo > 0:
        out[-fo:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(fo) / fo))
    return out


def level_clip(seg, target_rms_db=-15.5, max_peak=0.88):
    """Level clip to target RMS while enforcing peak ceiling."""
    rms = np.sqrt(np.mean(seg ** 2))
    if rms < 1e-8:
        return seg
    target_rms = 10.0 ** (target_rms_db / 20.0)
    gain = target_rms / rms
    peak = np.max(np.abs(seg))
    if peak * gain > max_peak:
        gain = max_peak / peak
    return seg * gain


def to_wav_bytes(seg, sr=GAME_SR):
    """Convert float64 [-1, 1] mono array to 16-bit PCM WAV bytes."""
    pcm = np.clip(np.round(seg * 32767.0), -32768, 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def crossfade_join(a, b, fade_samples):
    """Join two segments with an equal-power raised-cosine crossfade."""
    f = min(fade_samples, len(a) // 3, len(b) // 3)
    if f <= 0:
        return np.concatenate([a, b])
    t = np.linspace(0.0, np.pi * 0.5, f)
    wa = np.cos(t)
    wb = np.sin(t)
    mid = a[-f:] * wa + b[:f] * wb
    return np.concatenate([a[:-f], mid, b[f:]])


def waveform_peaks(seg, bars=64):
    """Compute normalized peak envelope bars for visual SVG/canvas waveform."""
    if len(seg) < bars:
        return [0.0] * bars
    chunks = np.array_split(np.abs(seg), bars)
    vals = np.array([float(np.max(c)) for c in chunks])
    mx = max(float(np.max(vals)), 1e-6)
    return [round(v / mx, 3) for v in vals]


def extract_kyle_sprite_b64():
    """Extract animated-ready PNG frames (idle + 6 run frames) from bakesfield.pk3 SPR32."""
    pk3_path = os.path.join(REPO, "bakersfield.pk3")
    if not os.path.exists(pk3_path):
        return []
    with zipfile.ZipFile(pk3_path) as zf:
        data = zf.read("progs/fr_scissors.spr32")
    idsp, ver, _typ, _rad, _w, _h, nframes, _beam, _synch = struct.unpack("<4s2if5i", data[:36])
    if idsp != b"IDSP" or ver != 32:
        return []
    pos = 36
    frames_uris = []
    # Front-facing frames: 0 (idle), and 8..13 (front run/snip cycle)
    wanted = {0, 8, 9, 10, 11, 12, 13}
    for idx in range(nframes):
        _grp = struct.unpack("<i", data[pos:pos + 4])[0]
        pos += 4
        _ox, _oy, fw, fh = struct.unpack("<4i", data[pos:pos + 16])
        pos += 16
        pix_len = fw * fh * 4
        if idx in wanted:
            im = Image.frombytes("RGBA", (fw, fh), data[pos:pos + pix_len])
            out = io.BytesIO()
            im.save(out, format="PNG")
            frames_uris.append("data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii"))
        pos += pix_len
    return frames_uris


def build_html(clips_meta, sprite_uris, noise_raw_db, noise_cln_db, out_html):
    """Render a self-contained HTML preview player under docs/."""
    sprite_js = json.dumps(sprite_uris)
    clips_js = json.dumps(clips_meta)
    total_kb = sum(c["wav_bytes"] for c in clips_meta) / 1024.0

    # Group cards HTML
    groups = [
        ("whoa", "Whoa! Exclamations (Weapon Pull-Out / Draw)", "Sight alerts, weapon draw pull-outs, and aggro reactions"),
        ("kyle", "It's Kyle! Intros", "Spawn announcements, greetings, and quick ID tags"),
        ("cut", "Barber / Cut Lines", "Pursuit threats, lunge barks, and creepy approach lines"),
        ("edits", "Bonus Edited Variants", "Tightened / spliced edits ready for direct game use"),
    ]

    sections_html = []
    for cat_key, cat_title, cat_sub in groups:
        cards = []
        for c in clips_meta:
            if c["category"] != cat_key:
                continue
            badge_cls = "badge-edit" if cat_key == "edits" else "badge-role"
            bars_html = "".join(
                f'<span class="bar" style="height:{max(10, int(v * 100))}%"></span>'
                for v in c["peaks"]
            )
            cards.append(f"""
            <article class="clip-card" data-id="{html.escape(c['id'])}" data-cat="{html.escape(cat_key)}">
              <div class="card-top">
                <div>
                  <div class="clip-title">{html.escape(c['title'])}</div>
                  <div class="clip-file"><code>{html.escape(c['filename'])}</code></div>
                </div>
                <span class="badge {badge_cls}">{html.escape(c['role'])}</span>
              </div>
              <div class="transcript">&ldquo;{html.escape(c['transcript'])}&rdquo;</div>
              <div class="wave-wrap" onclick="seekCard(event, '{html.escape(c['id'])}')" title="Click to play / seek">
                <div class="wave-bars">{bars_html}</div>
                <div class="wave-prog"></div>
              </div>
              <div class="meta-row">
                <span>{c['duration']:.2f}s</span>
                <span>RMS {c['rms_db']:.1f} dBFS</span>
                <span>Peak {c['peak_db']:.1f} dBFS</span>
                <span>{c['src_range']}</span>
              </div>
              <p class="clip-note">{html.escape(c['notes'])}</p>
              <div class="card-actions">
                <button class="btn btn-play" onclick="togglePlay('{html.escape(c['id'])}')">&#9654; Play</button>
                <button class="btn btn-loop" onclick="toggleLoop('{html.escape(c['id'])}')" title="Toggle loop">&#128257; Loop</button>
                {"<button class='btn btn-ab' onclick=\"toggleRaw('" + html.escape(c['id']) + "')\" title='Switch Cleaned vs Raw cut'>Cleaned</button>" if c['raw_uri'] else ""}
                <label class="pick-chk"><input type="checkbox" onchange="updatePicks()" value="{html.escape(c['id'])}"> Keep</label>
              </div>
            </article>""")
        sections_html.append(f"""
        <section class="cat-section">
          <div class="cat-head">
            <h2>{html.escape(cat_title)}</h2>
            <span class="cat-sub">{html.escape(cat_sub)}</span>
          </div>
          <div class="clip-grid">{''.join(cards)}</div>
        </section>""")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kyle Tillet (Scissors) — Sound Pack Preview</title>
<style>
  :root {{
    --bg: #0f131a;
    --panel: #171d27;
    --panel2: #1e2633;
    --border: #2c3648;
    --text: #e8edf5;
    --muted: #93a1b8;
    --accent: #38bdf8;
    --accent2: #f59e0b;
    --ok: #34d399;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: radial-gradient(circle at top, #182232 0%, var(--bg) 55%);
    color: var(--text); line-height: 1.45;
  }}
  .wrap {{ max-width: 1220px; margin: 0 auto; padding: 24px 20px 64px; }}
  header.hero {{
    display: grid; grid-template-columns: 128px 1fr; gap: 22px; align-items: center;
    background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
    padding: 20px 24px; margin-bottom: 22px;
  }}
  .sprite-stage {{
    width: 128px; height: 128px; border-radius: 12px;
    background: repeating-conic-gradient(#1b222e 0% 25%, #151a23 0% 50%) 50% / 16px 16px;
    border: 1px solid var(--border); display: flex; align-items: center; justify-content: center;
    cursor: pointer;
  }}
  .sprite-stage img {{ max-width: 112px; max-height: 112px; image-rendering: pixelated; }}
  h1 {{ margin: 0 0 6px; font-size: 1.65rem; letter-spacing: -0.02em; }}
  .hero-sub {{ color: var(--muted); margin: 0 0 12px; font-size: 0.95rem; }}
  .stats-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .pill {{
    background: var(--panel2); border: 1px solid var(--border); border-radius: 999px;
    padding: 4px 11px; font-size: 0.8rem; color: var(--muted);
  }}
  .pill b {{ color: var(--text); }}

  .toolbar {{
    position: sticky; top: 10px; z-index: 20;
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between;
    background: rgba(23, 29, 39, 0.94); backdrop-filter: blur(8px);
    border: 1px solid var(--border); border-radius: 12px; padding: 10px 14px; margin-bottom: 24px;
  }}
  .toolbar-left, .toolbar-right {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
  .cat-section {{ margin-bottom: 28px; }}
  .cat-head {{
    display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
    border-bottom: 1px solid var(--border); padding-bottom: 6px; margin-bottom: 14px;
  }}
  .cat-head h2 {{ margin: 0; font-size: 1.2rem; color: var(--accent); }}
  .cat-sub {{ color: var(--muted); font-size: 0.88rem; }}
  .clip-grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 14px;
  }}
  .clip-card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
    padding: 14px 16px; display: flex; flex-direction: column; gap: 8px;
    transition: border-color 0.15s, box-shadow 0.15s;
  }}
  .clip-card.playing {{
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent), 0 8px 24px rgba(56, 189, 248, 0.15);
  }}
  .clip-card.picked {{ border-color: var(--ok); }}
  .card-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }}
  .clip-title {{ font-weight: 700; font-size: 1rem; }}
  .clip-file code {{ font-size: 0.76rem; color: var(--muted); }}
  .badge {{
    font-size: 0.72rem; font-weight: 600; padding: 3px 8px; border-radius: 6px; white-space: nowrap;
  }}
  .badge-role {{ background: rgba(56, 189, 248, 0.14); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3); }}
  .badge-edit {{ background: rgba(245, 158, 11, 0.14); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.3); }}
  .transcript {{
    font-size: 0.96rem; color: #f8fafc; font-style: italic;
    background: var(--panel2); padding: 7px 10px; border-radius: 8px; border-left: 3px solid var(--accent);
  }}
  .wave-wrap {{
    position: relative; height: 42px; background: #10151e; border: 1px solid var(--border);
    border-radius: 8px; overflow: hidden; cursor: pointer; padding: 4px 6px;
  }}
  .wave-bars {{
    display: flex; align-items: center; justify-content: space-between; gap: 2px; height: 100%; position: relative; z-index: 2;
  }}
  .wave-bars .bar {{
    flex: 1; background: #475569; border-radius: 2px; transition: background 0.1s;
  }}
  .clip-card.playing .wave-bars .bar {{ background: #60a5fa; }}
  .wave-prog {{
    position: absolute; left: 0; top: 0; bottom: 0; width: 0%;
    background: rgba(56, 189, 248, 0.22); pointer-events: none; z-index: 1;
  }}
  .meta-row {{
    display: flex; flex-wrap: wrap; gap: 10px; font-size: 0.75rem; color: var(--muted);
    font-variant-numeric: tabular-nums;
  }}
  .clip-note {{ margin: 0; font-size: 0.82rem; color: var(--muted); min-height: 2.2em; }}
  .card-actions {{ display: flex; flex-wrap: wrap; gap: 7px; align-items: center; margin-top: auto; padding-top: 4px; }}
  .btn {{
    background: var(--panel2); color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 6px 11px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
  }}
  .btn:hover {{ border-color: #64748b; }}
  .btn-play {{ background: #0284c7; border-color: #0ea5e9; color: #fff; }}
  .btn-play:hover {{ background: #0369a1; }}
  .btn-loop.active {{ background: rgba(245, 158, 11, 0.22); border-color: var(--accent2); color: #fde68a; }}
  .btn-ab.raw {{ background: rgba(244, 63, 94, 0.18); border-color: #fb7185; color: #fecdd3; }}
  .pick-chk {{
    margin-left: auto; display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.82rem; color: var(--muted); cursor: pointer; user-select: none;
  }}
  .pick-chk input {{ accent-color: var(--ok); width: 15px; height: 15px; }}
  @media (max-width: 640px) {{
    header.hero {{ grid-template-columns: 1fr; text-align: center; }}
    .sprite-stage {{ margin: 0 auto; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="sprite-stage" onclick="toggleSpriteAnim()" title="Click to toggle Kyle's snip-run animation">
      <img id="kyle-sprite" alt="Kyle Tillet sprite">
    </div>
    <div>
      <h1>Kyle Tillet (Scissors) &mdash; Cleaned Sound Pack</h1>
      <p class="hero-sub">
        15 clean individual takes + 3 edited variants sliced from the uploaded 31.4s recording
        (the cut-off 1.36s <code>&ldquo;...and&rdquo;</code> fragment at the start was discarded).
        Each card lets you toggle <b>Cleaned vs Raw</b> and <b>Loop</b>, plus check <b>Keep</b> to shortlist clips.
      </p>
      <div class="stats-row">
        <span class="pill">Format: <b>22050 Hz &middot; 16-bit Mono WAV</b></span>
        <span class="pill">Noise floor: <b>{noise_raw_db:.1f} dBFS &rarr; {noise_cln_db:.1f} dBFS</b></span>
        <span class="pill">Target level: <b>-15.5 dBFS RMS / &le;-1.1 dBFS peak</b></span>
        <span class="pill">Embedded payload: <b>{total_kb:.0f} KB</b></span>
      </div>
    </div>
  </header>

  <div class="toolbar">
    <div class="toolbar-left">
      <button class="btn btn-play" id="btn-play-all" onclick="playAll()">&#9654; Play All Sequentially</button>
      <button class="btn" onclick="stopAudio()">&#9632; Stop</button>
      <button class="btn" id="btn-global-mode" onclick="toggleGlobalMode()">Mode: Cleaned (Switch All to Raw)</button>
    </div>
    <div class="toolbar-right">
      <span id="pick-count" style="font-size:0.84rem;color:var(--muted);">0 selected</span>
      <button class="btn" onclick="selectAll(true)">Check All</button>
      <button class="btn" onclick="selectAll(false)">Clear</button>
      <button class="btn" style="border-color:var(--ok);color:#6ee7b7;" onclick="copyPicks()">Copy Selected List</button>
    </div>
  </div>

  {''.join(sections_html)}
</div>

<audio id="player"></audio>
<script>
const SPRITES = {sprite_js};
const CLIPS = {clips_js};
const clipMap = Object.fromEntries(CLIPS.map(c => [c.id, c]));
const player = document.getElementById("player");

let currentId = null;
let loopState = {{}};
let rawState = {{}};
let globalRaw = false;
let queue = [];
let spriteAnim = true;
let spriteIdx = 1;

// Sprite animation
const spriteImg = document.getElementById("kyle-sprite");
if (SPRITES.length > 0) {{
  spriteImg.src = SPRITES[0];
  setInterval(() => {{
    if (!spriteAnim || SPRITES.length <= 1) return;
    spriteIdx = 1 + ((spriteIdx) % (SPRITES.length - 1));
    spriteImg.src = SPRITES[spriteIdx];
  }}, 110);
}}
function toggleSpriteAnim() {{
  spriteAnim = !spriteAnim;
  if (!spriteAnim && SPRITES.length > 0) spriteImg.src = SPRITES[0];
}}

function cardEl(id) {{
  return document.querySelector(`.clip-card[data-id="${{id}}"]`);
}}

function playClip(id) {{
  const c = clipMap[id];
  if (!c) return;
  const useRaw = !!(rawState[id] && c.raw_uri);
  currentId = id;
  player.src = useRaw ? c.raw_uri : c.uri;
  player.loop = !!loopState[id];
  player.play().catch(() => {{}});
  refreshUI();
}}

function togglePlay(id) {{
  if (currentId === id && !player.paused) {{
    stopAudio();
    return;
  }}
  queue = [];
  playClip(id);
}}

function stopAudio() {{
  queue = [];
  player.pause();
  player.currentTime = 0;
  currentId = null;
  refreshUI();
}}

function seekCard(ev, id) {{
  const rect = ev.currentTarget.getBoundingClientRect();
  const frac = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
  if (currentId !== id) {{
    queue = [];
    playClip(id);
    player.addEventListener("loadedmetadata", () => {{
      if (player.duration) player.currentTime = frac * player.duration;
    }}, {{ once: true }});
  }} else if (player.duration) {{
    player.currentTime = frac * player.duration;
  }}
}}

function toggleLoop(id) {{
  loopState[id] = !loopState[id];
  if (currentId === id) player.loop = !!loopState[id];
  const btn = cardEl(id).querySelector(".btn-loop");
  btn.classList.toggle("active", !!loopState[id]);
}}

function toggleRaw(id) {{
  rawState[id] = !rawState[id];
  const btn = cardEl(id).querySelector(".btn-ab");
  if (btn) {{
    btn.textContent = rawState[id] ? "Raw" : "Cleaned";
    btn.classList.toggle("raw", !!rawState[id]);
  }}
  if (currentId === id && !player.paused) {{
    playClip(id);
  }}
}}

function toggleGlobalMode() {{
  globalRaw = !globalRaw;
  CLIPS.forEach(c => {{
    if (!c.raw_uri) return;
    rawState[c.id] = globalRaw;
    const btn = cardEl(c.id).querySelector(".btn-ab");
    if (btn) {{
      btn.textContent = globalRaw ? "Raw" : "Cleaned";
      btn.classList.toggle("raw", globalRaw);
    }}
  }});
  document.getElementById("btn-global-mode").textContent = globalRaw
    ? "Mode: Raw (Switch All to Cleaned)"
    : "Mode: Cleaned (Switch All to Raw)";
}}

function playAll() {{
  queue = CLIPS.map(c => c.id);
  if (queue.length) playClip(queue.shift());
}}

player.addEventListener("ended", () => {{
  if (player.loop) return;
  if (queue.length > 0) {{
    setTimeout(() => {{
      if (queue.length > 0) playClip(queue.shift());
    }}, 220);
  }} else {{
    currentId = null;
    refreshUI();
  }}
}});

player.addEventListener("timeupdate", () => {{
  if (!currentId || !player.duration) return;
  const pct = (player.currentTime / player.duration) * 100;
  const prog = cardEl(currentId)?.querySelector(".wave-prog");
  if (prog) prog.style.width = pct.toFixed(1) + "%";
}});

function refreshUI() {{
  document.querySelectorAll(".clip-card").forEach(el => {{
    const isThis = el.dataset.id === currentId && !player.paused;
    el.classList.toggle("playing", isThis);
    const playBtn = el.querySelector(".btn-play");
    if (playBtn) playBtn.innerHTML = isThis ? "&#9646;&#9646; Pause" : "&#9654; Play";
    if (!isThis) {{
      const prog = el.querySelector(".wave-prog");
      if (prog) prog.style.width = "0%";
    }}
  }});
}}

function updatePicks() {{
  const checked = [...document.querySelectorAll(".pick-chk input:checked")];
  document.getElementById("pick-count").textContent = `${{checked.length}} selected`;
  document.querySelectorAll(".clip-card").forEach(el => {{
    const chk = el.querySelector(".pick-chk input");
    el.classList.toggle("picked", !!(chk && chk.checked));
  }});
}}

function selectAll(flag) {{
  document.querySelectorAll(".pick-chk input").forEach(el => el.checked = flag);
  updatePicks();
}}

function copyPicks() {{
  const lines = [...document.querySelectorAll(".pick-chk input:checked")].map(el => {{
    const c = clipMap[el.value];
    return `${{c.filename}}  # "${{c.transcript}}" (${{c.role}})`;
  }});
  const txt = lines.length ? lines.join("\\n") : "No clips selected yet.";
  navigator.clipboard?.writeText(txt).then(() => {{
    const btn = event.target;
    const old = btn.textContent;
    btn.textContent = `Copied ${{lines.length}}!`;
    setTimeout(() => btn.textContent = old, 1400);
  }}).catch(() => alert(txt));
}}
</script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    with open(out_html, "w", encoding="utf-8") as fh:
        fh.write(page)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", default=DEFAULT_SRC)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--html", default=DEFAULT_HTML)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # 1. Decode raw and EQ-filtered continuous 48 kHz audio
    raw_full = decode_audio(args.src, sr=WORK_SR)
    af_eq = "highpass=f=85:p=2,equalizer=f=240:t=q:w=1.2:g=-1.8,equalizer=f=3400:t=q:w=1.0:g=2.0,equalizer=f=6500:t=q:w=1.1:g=-1.5"
    eq_full = decode_audio(args.src, af=af_eq, sr=WORK_SR)

    # 2. Spectral Wiener denoise + compression/gating
    denoised_full = wiener_denoise(eq_full, WORK_SR)
    cln_full = compress_and_gate(denoised_full, WORK_SR)

    n0, n1 = int(7.85 * WORK_SR), int(9.05 * WORK_SR)
    noise_raw_db = float(20.0 * np.log10(np.sqrt(np.mean(raw_full[n0:n1] ** 2)) + 1e-12))
    noise_cln_db = float(20.0 * np.log10(np.sqrt(np.mean(cln_full[n0:n1] ** 2)) + 1e-12))
    print(f"Measured room noise floor: {noise_raw_db:.1f} dBFS -> {noise_cln_db:.1f} dBFS")

    clips_meta = []
    cleaned_48k_by_id = {}

    # 3. Cut, trim, fade, level, and export all 15 individual takes
    for cid, cat, title, transcript, role, t0, t1, notes in TAKES:
        s0, s1 = int(t0 * WORK_SR), int(t1 * WORK_SR)
        seg_cln = trim_silence(cln_full[s0:s1], WORK_SR)
        seg_cln = apply_fades(seg_cln, WORK_SR)
        seg_cln = level_clip(seg_cln)
        cleaned_48k_by_id[cid] = seg_cln

        seg_22k = resample_to_game_sr(seg_cln, WORK_SR, GAME_SR)
        wav_cln = to_wav_bytes(seg_22k, GAME_SR)

        raw_slice = apply_fades(raw_full[s0:s1], WORK_SR, fade_in_s=0.005, fade_out_s=0.010)
        raw_22k = resample_to_game_sr(raw_slice, WORK_SR, GAME_SR)
        wav_raw = to_wav_bytes(raw_22k, GAME_SR)

        fname = f"{cid}.wav"
        with open(os.path.join(args.out_dir, fname), "wb") as fh:
            fh.write(wav_cln)

        rms_db = float(20.0 * np.log10(np.sqrt(np.mean(seg_22k ** 2)) + 1e-12))
        peak_db = float(20.0 * np.log10(np.max(np.abs(seg_22k)) + 1e-12))
        dur = len(seg_22k) / GAME_SR
        print(f"  {fname:32s} dur={dur:5.2f}s  rms={rms_db:5.1f}dB  peak={peak_db:5.1f}dB")

        clips_meta.append({
            "id": cid,
            "filename": fname,
            "category": cat,
            "title": title,
            "transcript": transcript,
            "role": role,
            "notes": notes,
            "src_range": f"{t0:.2f}s–{t1:.2f}s",
            "duration": dur,
            "rms_db": rms_db,
            "peak_db": peak_db,
            "wav_bytes": len(wav_cln),
            "peaks": waveform_peaks(seg_22k),
            "uri": "data:audio/wav;base64," + base64.b64encode(wav_cln).decode("ascii"),
            "raw_uri": "data:audio/wav;base64," + base64.b64encode(wav_raw).decode("ascii"),
        })

    # 4. Bonus edited variants
    # Edit 1: "Hey man, you gonna give me a cut?" (splices out the "uhhh" from 20.17s to 20.53s)
    part_a = trim_silence(cln_full[int(19.67 * WORK_SR):int(20.19 * WORK_SR)], WORK_SR, pad_in=0.012, pad_out=0.008)
    part_b = trim_silence(cln_full[int(20.52 * WORK_SR):int(21.36 * WORK_SR)], WORK_SR, pad_in=0.008, pad_out=0.028)
    edit1_48 = apply_fades(level_clip(crossfade_join(part_a, part_b, int(0.025 * WORK_SR))), WORK_SR)

    # Edit 2: "Whoa! Give me a cut!"
    gap80 = np.zeros(int(0.08 * WORK_SR))
    edit2_48 = level_clip(np.concatenate([cleaned_48k_by_id["whoa_04_punch"], gap80, cleaned_48k_by_id["cut_02_give_me_a_cut"]]))

    edits = [
        ("edit_01_hey_man_tight", "Hey man, you gonna give me a cut? (No 'uh')",
         "Hey man, you gonna give me a cut?", "Idle / Approach",
         "Spliced out the drawn-out 'uhhh' pause (20.19s–20.52s) with a 25ms crossfade.",
         "19.67s–21.36s (edited)", edit1_48),
        ("edit_02_whoa_give_cut", "Whoa! Give me a cut! (Combo)",
         "Whoa! Give me a cut!", "Aggro / Attack",
         "Combined loud 'Whoa!' + 80ms gap + 'Give me a cut!' for a punchy lunge cue.",
         "whoa_04 + cut_02", edit2_48),
    ]

    for eid, title, transcript, role, notes, src_rng, seg48 in edits:
        seg_22k = resample_to_game_sr(seg48, WORK_SR, GAME_SR)
        wav_cln = to_wav_bytes(seg_22k, GAME_SR)
        fname = f"{eid}.wav"
        with open(os.path.join(args.out_dir, fname), "wb") as fh:
            fh.write(wav_cln)
        rms_db = float(20.0 * np.log10(np.sqrt(np.mean(seg_22k ** 2)) + 1e-12))
        peak_db = float(20.0 * np.log10(np.max(np.abs(seg_22k)) + 1e-12))
        dur = len(seg_22k) / GAME_SR
        print(f"  {fname:32s} dur={dur:5.2f}s  rms={rms_db:5.1f}dB  peak={peak_db:5.1f}dB")

        clips_meta.append({
            "id": eid,
            "filename": fname,
            "category": "edits",
            "title": title,
            "transcript": transcript,
            "role": role,
            "notes": notes,
            "src_range": src_rng,
            "duration": dur,
            "rms_db": rms_db,
            "peak_db": peak_db,
            "wav_bytes": len(wav_cln),
            "peaks": waveform_peaks(seg_22k),
            "uri": "data:audio/wav;base64," + base64.b64encode(wav_cln).decode("ascii"),
            "raw_uri": None,
        })

    sprite_uris = extract_kyle_sprite_b64()
    build_html(clips_meta, sprite_uris, noise_raw_db, noise_cln_db, args.html)
    print(f"Wrote HTML preview: {args.html} ({os.path.getsize(args.html)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
