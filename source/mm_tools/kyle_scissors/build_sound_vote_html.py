"""Generate extended "WHOAAA WHOAAAA!" voice remixes from Kyle's real denoised takes
and build the interactive Kyle Sound Voting & Audition Lab HTML
(docs/kyle_sound_vote.html).

Never touches bakersfield.pk3 or q15.pk3; ZERO 'Will stole my clients' clips.

Run:
    python -I source/mm_tools/kyle_scissors/build_sound_vote_html.py
"""

import base64
import html as html_mod
import io
import json
import os
import subprocess
import sys
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
ARTIFACT_ROOT = Path(r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671")
CLIPS_DIR = ARTIFACT_ROOT / "scratch" / "kyle_clips"
SFX_DIR = ARTIFACT_ROOT / "scratch" / "kyle_stage" / "sfx"
VM_DIR = ARTIFACT_ROOT / "scratch" / "pocket_kyle_hd"
OUT_HTML = REPO / "docs" / "kyle_sound_vote.html"

WORK_SR = 44100
GAME_SR = 22050


def read_wav_f64(path: Path) -> Tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        nch = wf.getnchannels()
        samp = np.frombuffer(wf.readframes(wf.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
        if nch > 1:
            samp = samp.reshape(-1, nch).mean(axis=1)
        return samp, sr


def resample_f64(x: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    raw = x.astype("<f4").tobytes()
    cmd = [
        "ffmpeg", "-v", "error",
        "-f", "f32le", "-ac", "1", "-ar", str(src_sr), "-i", "pipe:0",
        "-af", f"aresample={dst_sr}",
        "-f", "f32le", "-ac", "1", "-ar", str(dst_sr), "pipe:1",
    ]
    proc = subprocess.run(cmd, input=raw, capture_output=True, check=True)
    return np.frombuffer(proc.stdout, "<f4").astype(np.float64)


def pitch_shift_keep_formant(x: np.ndarray, sr: int, rate: float) -> np.ndarray:
    """Clean variable-rate / subtle pitch contour helper via linear interpolation."""
    n = len(x)
    idx = np.arange(0, n - 1, rate, dtype=np.float64)
    i0 = np.floor(idx).astype(np.int64)
    frac = idx - i0
    return x[i0] * (1.0 - frac) + x[i0 + 1] * frac


def pitch_contour(x: np.ndarray, sr: int, rates: np.ndarray) -> np.ndarray:
    """Resample along a smooth time-varying pitch/speed contour (e.g. Superman Doppler Whoaaa!)."""
    pos = np.cumsum(rates)
    pos = pos[pos < len(x) - 1]
    i0 = np.floor(pos).astype(np.int64)
    frac = pos - i0
    return x[i0] * (1.0 - frac) + x[i0 + 1] * frac


def add_canyon_echo(x: np.ndarray, sr: int, taps=((0.19, 0.42), (0.39, 0.24), (0.62, 0.12))) -> np.ndarray:
    extra = int((taps[-1][0] + 0.15) * sr)
    out = np.zeros(len(x) + extra, dtype=np.float64)
    out[:len(x)] += x
    for delay_s, gain in taps:
        d = int(delay_s * sr)
        out[d:d + len(x)] += x * gain
    return out


def crossfade_join(a: np.ndarray, b: np.ndarray, fade_n: int) -> np.ndarray:
    f = min(fade_n, len(a) // 3, len(b) // 3)
    if f <= 0:
        return np.concatenate([a, b])
    t = np.linspace(0.0, np.pi * 0.5, f)
    return np.concatenate([a[:-f], a[-f:] * np.cos(t) + b[:f] * np.sin(t), b[f:]])


def apply_fades_and_level(seg: np.ndarray, sr: int, target_db: float = -15.0, max_peak: float = 0.88) -> np.ndarray:
    out = seg.copy()
    fi = min(int(0.008 * sr), len(out) // 6)
    fo = min(int(0.032 * sr), len(out) // 6)
    if fi > 0:
        out[:fi] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(fi) / fi))
    if fo > 0:
        out[-fo:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(fo) / fo))
    rms = np.sqrt(np.mean(out ** 2))
    if rms > 1e-8:
        gain = (10.0 ** (target_db / 20.0)) / rms
        pk = np.max(np.abs(out))
        if pk * gain > max_peak:
            gain = max_peak / pk
        out *= gain
    return np.clip(out, -0.95, 0.95)


def write_wav_22k(path: Path, seg_22k: np.ndarray) -> bytes:
    pcm = np.clip(np.round(seg_22k * 32767.0), -32768, 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(GAME_SR)
        wf.writeframes(pcm.tobytes())
    data = buf.getvalue()
    path.write_bytes(data)
    return data


def generate_more_whoaas() -> None:
    """Synthesize 7 brand-new clean 'WHOAAA WHOAAAA!' voice variations from Kyle's real voice takes."""
    w1, _ = read_wav_f64(CLIPS_DIR / "whoa_01_short.wav")
    w2, _ = read_wav_f64(CLIPS_DIR / "whoa_02_wobble.wav")
    w3, _ = read_wav_f64(CLIPS_DIR / "whoa_03_rise.wav")
    w4, _ = read_wav_f64(CLIPS_DIR / "whoa_04_punch.wav")
    w5, _ = read_wav_f64(CLIPS_DIR / "whoa_05_long.wav")
    cut2, _ = read_wav_f64(CLIPS_DIR / "cut_02_give_me_a_cut.wav")

    fade_n = int(0.035 * GAME_SR)
    gap90 = np.zeros(int(0.09 * GAME_SR))
    gap55 = np.zeros(int(0.055 * GAME_SR))

    # 1. whoa_06_double_warble.wav: "Whoa-oh-oh... WHOA-OH-OH-OH!"
    s6 = crossfade_join(np.concatenate([w2, gap55]), w3, fade_n)
    write_wav_22k(CLIPS_DIR / "whoa_06_double_warble.wav", apply_fades_and_level(s6, GAME_SR))

    # 2. whoa_07_triple_rapid.wav: "Whoa! Whoa! WHOAAA-OOOH!"
    w1_hi = pitch_shift_keep_formant(w1, GAME_SR, 1.07)
    w4_lo = pitch_shift_keep_formant(w4, GAME_SR, 0.96)
    s7 = np.concatenate([w1_hi, gap55, w4_lo, gap55, w5[:int(1.25 * GAME_SR)]])
    write_wav_22k(CLIPS_DIR / "whoa_07_triple_rapid.wav", apply_fades_and_level(s7, GAME_SR))

    # 3. whoa_08_superman_doppler.wav: Flying Superman Doppler "WHOAAAAAooouu!"
    t_norm = np.linspace(0.0, 1.0, len(w5))
    # Pitch starts bright (+6%), then glides down smoothly (-13%) as Torpedo rockets past toward the bird!
    contour = 1.06 - 0.19 * (t_norm ** 1.35)
    s8 = pitch_contour(w5, GAME_SR, contour)
    s8 = add_canyon_echo(s8, GAME_SR, taps=((0.14, 0.28), (0.30, 0.14)))
    write_wav_22k(CLIPS_DIR / "whoa_08_superman_doppler.wav", apply_fades_and_level(s8, GAME_SR))

    # 4. whoa_09_canyon_yell.wav: Sky-throw echoing "WHOAAAA-OOOH... oooh..."
    s9 = add_canyon_echo(w5, GAME_SR, taps=((0.22, 0.44), (0.46, 0.25), (0.72, 0.12)))
    write_wav_22k(CLIPS_DIR / "whoa_09_canyon_yell.wav", apply_fades_and_level(s9, GAME_SR))

    # 5. whoa_10_whoa_whoaaa_long.wav: "WHOA! ... WHOAAA-OOOH!!"
    s10 = crossfade_join(np.concatenate([w4, gap90]), w5, fade_n)
    write_wav_22k(CLIPS_DIR / "whoa_10_whoa_whoaaa_long.wav", apply_fades_and_level(s10, GAME_SR))

    # 6. whoa_11_pocket_excited.wav: Crisp energetic Pocket-Kyle pitched warble!
    s11 = pitch_shift_keep_formant(w3, GAME_SR, 1.11)
    s11_b = pitch_shift_keep_formant(w2, GAME_SR, 1.06)
    s11_full = crossfade_join(np.concatenate([s11_b, gap55]), s11, fade_n)
    write_wav_22k(CLIPS_DIR / "whoa_11_pocket_excited.wav", apply_fades_and_level(s11_full, GAME_SR))

    # 7. whoa_12_torpedo_cut_cry.wav: "WHOAAA-OOOH... Give me a cut!!"
    s12 = crossfade_join(np.concatenate([w5[:int(1.65 * GAME_SR)], gap55]), cut2, fade_n)
    write_wav_22k(CLIPS_DIR / "whoa_12_torpedo_cut_cry.wav", apply_fades_and_level(s12, GAME_SR))

    print("Generated 7 new 'WHOAAA!' 22050 Hz Quake WAVs in", CLIPS_DIR)


# Complete catalog of sounds for the interactive voting page (ZERO 'clients' clips!)
SOUND_CATALOG = [
    # ---- CATEGORY 1: MORE WHOAAA! ----
    ("whoa_05_long", CLIPS_DIR / "whoa_05_long.wav", "whoa", "Whoa-oooh! (Long Yell)", "WHOAAA-OOOH!",
     "Original untouched 2.4s sustained yell! Huge comedy value for sky throws & flying torpedo.", ["Draw", "Throw / Torpedo"], True),
    ("whoa_06_double_warble", CLIPS_DIR / "whoa_06_double_warble.wav", "whoa", "Whoa-oh-oh... WHOA-OH-OH!", "Whoa-oh-oh... WHOA-OH-OH-OH!",
     "Chains Kyle's descending wobble straight into his rising warble!", ["Draw", "Throw / Torpedo"], True),
    ("whoa_08_superman_doppler", CLIPS_DIR / "whoa_08_superman_doppler.wav", "whoa", "Superman Doppler WHOAAA!", "WHOAAAAooouuu...",
     "Built specifically for the spinning Superman Torpedo launching off your hand toward a bird!", ["Throw / Torpedo", "Bird Lock"], True),
    ("whoa_09_canyon_yell", CLIPS_DIR / "whoa_09_canyon_yell.wav", "whoa", "Sky Canyon Echo WHOAAA!", "WHOAAA-OOOH... ooh... ooh...",
     "Sustained sky yell with slapback stadium echoes when he soars across the map!", ["Throw / Torpedo"], True),
    ("whoa_10_whoa_whoaaa_long", CLIPS_DIR / "whoa_10_whoa_whoaaa_long.wav", "whoa", "WHOA! + WHOAAA-OOOH!", "WHOA! ... WHOAAA-OOOH!!",
     "Loud punch exclamation immediately followed by the big sustained scream!", ["Draw", "Throw / Torpedo"], True),
    ("whoa_07_triple_rapid", CLIPS_DIR / "whoa_07_triple_rapid.wav", "whoa", "Triple Panic Whoa-Whoa-WHOAAA!", "Whoa! Whoa! WHOAAA!",
     "Rapid 3-stage panic triple-take!", ["Throw / Torpedo", "Death"], True),
    ("whoa_11_pocket_excited", CLIPS_DIR / "whoa_11_pocket_excited.wav", "whoa", "Hyper Warble Whoaaa! (+Pitch)", "Whoa-oh-oh WHOA-OH!",
     "Pocket-sized slightly pitched-up double warble!", ["Throw / Torpedo", "Roam"], False),
    ("whoa_12_torpedo_cut_cry", CLIPS_DIR / "whoa_12_torpedo_cut_cry.wav", "whoa", "WHOAAA... Give Me a Cut!", "WHOAAA-OOOH... Give me a cut!!",
     "Full flying battle cry into scissor demand!", ["Throw / Torpedo", "Latch / Chop"], True),
    ("whoa_02_wobble", CLIPS_DIR / "whoa_02_wobble.wav", "whoa", "Whoa-oh-oh! (Wobble)", "Whoa-oh-oh!",
     "Classic warbly descending whoa take.", ["Draw", "Throw / Torpedo"], True),
    ("whoa_03_rise", CLIPS_DIR / "whoa_03_rise.wav", "whoa", "Whoa-oh-oh-oh! (Rising)", "Whoa-oh-oh-oh!",
     "Excited rising warble!", ["Draw", "Throw / Torpedo"], True),
    ("whoa_04_punch", CLIPS_DIR / "whoa_04_punch.wav", "whoa", "Whoa! (Loud Punch)", "Whoa!",
     "Punchy exclamation currently also used on Kyle death pop.", ["Draw", "Death"], True),
    ("whoa_01_short", CLIPS_DIR / "whoa_01_short.wav", "whoa", "Whoa! (Quick Snappy)", "Whoa!",
     "Ultra-quick startled pull-out reaction.", ["Draw"], True),

    # ---- CATEGORY 2: KYLE INTROS & CUT LINES ----
    ("cut_01_wheres_my_cut", CLIPS_DIR / "cut_01_wheres_my_cut.wav", "voice", "Whoa man, where's my cut?!", "Whoa man, where's my cut?!",
     "Iconic panicked draw & pursuit line.", ["Draw", "Latch / Chop"], True),
    ("cut_02_give_me_a_cut", CLIPS_DIR / "cut_02_give_me_a_cut.wav", "voice", "Give me a cut!", "Give me a cut!",
     "Aggressive demand while chasing or latching onto an enemy.", ["Latch / Chop", "Roam"], True),
    ("edit_02_whoa_give_cut", CLIPS_DIR / "edit_02_whoa_give_cut.wav", "voice", "Whoa! Give me a cut! (Combo)", "Whoa! Give me a cut!",
     "Loud 'Whoa!' right into 'Give me a cut!' combo.", ["Latch / Chop", "Throw / Torpedo"], True),
    ("kyle_02_hey_bright", CLIPS_DIR / "kyle_02_hey_bright.wav", "voice", "Hey, it's Kyle! (Bright)", "Hey, it's Kyle!",
     "Upbeat bright greeting while roaming.", ["Roam", "Latch / Chop"], True),
    ("kyle_03_its_kyle", CLIPS_DIR / "kyle_03_its_kyle.wav", "voice", "It's Kyle.", "It's Kyle.",
     "Deadpan 0.6s quick ID tag.", ["Roam"], True),
    ("edit_01_hey_man_tight", CLIPS_DIR / "edit_01_hey_man_tight.wav", "voice", "Hey man, gonna give me a cut?", "Hey man, you gonna give me a cut?",
     "Tightened creepy barber approach line.", ["Roam", "Latch / Chop"], True),
    ("kyle_01_hey_high", CLIPS_DIR / "kyle_01_hey_high.wav", "voice", "Hey, it's Kyle! (High)", "Hey, it's Kyle!",
     "High-inflection greeting (candidate for roam/draw).", ["Roam"], False),
    ("kyle_04_hey_fast", CLIPS_DIR / "kyle_04_hey_fast.wav", "voice", "Hey, it's Kyle. (Snappy)", "Hey, it's Kyle.",
     "Fast casual intro (candidate).", ["Roam"], False),
    ("kyle_05_this_is_kyle", CLIPS_DIR / "kyle_05_this_is_kyle.wav", "voice", "This is Kyle.", "This is Kyle.",
     "Direct deadpan intro (candidate).", ["Roam"], False),
    ("cut_03_hey_man_cut", CLIPS_DIR / "cut_03_hey_man_cut.wav", "voice", "Hey man, uh, give me a cut?", "Hey man, uh, you gonna give me a cut?",
     "Original awkward 'uhhh' pause version.", ["Roam"], False),

    # ---- CATEGORY 3: SCISSORS, CLANGS, LOCK & CASH SFX ----
    ("scissor_clang1", SFX_DIR / "scissor_clang1.wav", "sfx", "3D Scissor Bounce Clang #1", "*SHING-CLANK!*",
     "Bright crisp barber steel ring when 3D scissors bounce on the ground on Kyle's death!", ["Death"], True),
    ("scissor_clang2", SFX_DIR / "scissor_clang2.wav", "sfx", "3D Scissor Bounce Clang #2", "*PING-CLATTER!*",
     "Harmonic metallic clatter bounce #2.", ["Death"], True),
    ("scissor_clang3", SFX_DIR / "scissor_clang3.wav", "sfx", "3D Scissor Bounce Clang #3", "*TING-CLANG!*",
     "Warm metallic steel ring bounce #3.", ["Death"], True),
    ("snip_fast", SFX_DIR / "snip_fast.wav", "sfx", "Fast Chrome Scissor Snip", "*SNIP!*",
     "Sharp razor-steel shear snip during windup, flight & chops.", ["Throw / Torpedo", "Latch / Chop"], True),
    ("snip_heavy", SFX_DIR / "snip_heavy.wav", "sfx", "Heavy Shear Crunch", "*CHOMP-SNIP!*",
     "Heavy double-blade crunch on latch & death pop.", ["Latch / Chop", "Death"], True),
    ("lock_tick", SFX_DIR / "lock_tick.wav", "sfx", "Bird Lock-On Bracket Tick", "*BEEP-TICK*",
     "Escalating radar chirp while locking onto a Winged John Bird.", ["Bird Lock"], True),
    ("lock_ready", SFX_DIR / "lock_ready.wav", "sfx", "TORPEDO LOCKED! Chime", "*DING-DING!*",
     "Green/red full lock-on confirmation chord.", ["Bird Lock"], True),
    ("plane_whoosh", SFX_DIR / "plane_whoosh.wav", "sfx", "Kyle Launch / Sky Whoosh", "*WHOOOSH!*",
     "Airborne launch wind gust.", ["Throw / Torpedo"], True),
    ("cash_register", SFX_DIR / "cash_register.wav", "sfx", "Cha-Ching! Cash Explosion", "*CHA-CHING!*",
     "Classic register bell when Kyle explodes into US $100 bills & coins!", ["Death"], True),
    ("cash_flutter", SFX_DIR / "cash_flutter.wav", "sfx", "Paper Bills Flutter Burst", "*FFFT-FLUTTER*",
     "Crisp banknote paper rustle on hits & cash burst.", ["Latch / Chop", "Death"], True),
]


def wav_peaks(path: Path, n_bars: int = 44) -> Tuple[List[float], float]:
    x, sr = read_wav_f64(path)
    dur = len(x) / float(sr)
    if len(x) < n_bars:
        return [0.1] * n_bars, dur
    chunks = np.array_split(np.abs(x), n_bars)
    vals = [float(np.max(c)) for c in chunks]
    mx = max(max(vals), 1e-6)
    return [round(v / mx, 3) for v in vals], round(dur, 2)


def main() -> None:
    generate_more_whoaas()

    items = []
    for cid, wav_p, cat, title, quote, desc, roles, in_game in SOUND_CATALOG:
        assert wav_p.exists(), f"Missing WAV: {wav_p}"
        assert "client" not in cid.lower() and "client" not in wav_p.name.lower()
        peaks, dur = wav_peaks(wav_p)
        b64 = "data:audio/wav;base64," + base64.b64encode(wav_p.read_bytes()).decode("ascii")
        items.append({
            "id": cid,
            "file": wav_p.name,
            "cat": cat,
            "title": title,
            "quote": quote,
            "desc": desc,
            "roles": roles,
            "in_game": in_game,
            "dur": dur,
            "peaks": peaks,
            "url": b64,
        })

    # Embed miniature Kyle icon from fire_22 / birdlock_0
    hero_png = VM_DIR / "birdlock_12.png"
    hero_b64 = ""
    if hero_png.exists():
        im = Image.open(hero_png).convert("RGBA").resize((150, 200), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="WEBP", quality=88)
        hero_b64 = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    page = HTML_TEMPLATE.replace("__SOUNDS_JSON__", json.dumps(items, separators=(",", ":")))
    page = page.replace("__HERO_IMG__", hero_b64)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page, encoding="utf-8")
    mb = OUT_HTML.stat().st_size / (1024 * 1024)
    print(f"Wrote {OUT_HTML} ({len(items)} sounds, {mb:.2f} MB self-contained)")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Kyle Sound Vote Lab — MORE WHOAAA WHOAAAA!</title>
<style>
  :root {
    --bg: #0b0f17;
    --panel: #131a26;
    --panel2: #1b2434;
    --border: #2a364d;
    --text: #eef2f8;
    --muted: #93a3bd;
    --blue: #38bdf8;
    --green: #22c55e;
    --amber: #f59e0b;
    --red: #ef4444;
    --gold: #facc15;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: radial-gradient(circle at top center, #16233a 0%, var(--bg) 60%);
    color: var(--text);
    line-height: 1.45;
  }
  .wrap { max-width: 1240px; margin: 0 auto; padding: 20px 16px 80px; }

  .hero {
    display: grid; grid-template-columns: 128px 1fr auto; gap: 18px; align-items: center;
    background: linear-gradient(135deg, rgba(25,38,60,0.95), rgba(16,22,34,0.95));
    border: 1px solid var(--border); border-radius: 16px; padding: 18px 22px; margin-bottom: 18px;
  }
  .hero img {
    width: 120px; height: 156px; object-fit: contain;
    background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.3);
    border-radius: 12px; cursor: pointer;
  }
  .hero h1 { margin: 0 0 6px; font-size: 1.55rem; letter-spacing: -0.02em; }
  .hero p { margin: 0; color: var(--muted); font-size: 0.94rem; }
  .hero-actions { display: flex; flex-direction: column; gap: 8px; min-width: 230px; }

  .btn {
    border: 1px solid var(--border); background: var(--panel2); color: var(--text);
    border-radius: 10px; padding: 9px 14px; font-weight: 700; font-size: 0.88rem;
    cursor: pointer; transition: transform 0.08s, border-color 0.15s, background 0.15s;
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  }
  .btn:hover { border-color: #64748b; }
  .btn:active { transform: scale(0.97); }
  .btn-whoa {
    background: linear-gradient(135deg, #22c55e, #16a34a); border-color: #4ade80;
    color: #052e16; font-size: 1rem; padding: 12px 16px;
    box-shadow: 0 6px 20px rgba(34,197,94,0.28);
  }
  .btn-play { background: #0284c7; border-color: #38bdf8; color: #fff; }
  .btn-amber { background: #d97706; border-color: #fbbf24; color: #fff; }
  .btn-battle { background: #7c3aed; border-color: #a78bfa; color: #fff; }

  .sticky-bar {
    position: sticky; top: 8px; z-index: 30;
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between;
    background: rgba(16, 22, 34, 0.94); backdrop-filter: blur(10px);
    border: 1px solid var(--border); border-radius: 12px; padding: 10px 14px; margin-bottom: 18px;
  }
  .filter-pills, .bar-right { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .tab-pill {
    background: var(--panel2); border: 1px solid var(--border); color: var(--muted);
    padding: 6px 12px; border-radius: 999px; font-size: 0.82rem; font-weight: 700; cursor: pointer;
  }
  .tab-pill.active { background: #0284c7; border-color: #38bdf8; color: #fff; }

  /* Head-to-head Battle Arena */
  .arena {
    display: none; background: linear-gradient(180deg, rgba(88,28,135,0.28), rgba(19,26,38,0.96));
    border: 1px solid rgba(167,139,250,0.45); border-radius: 14px; padding: 18px; margin-bottom: 22px;
  }
  .arena.open { display: block; }
  .arena-grid { display: grid; grid-template-columns: 1fr auto 1fr; gap: 14px; align-items: center; margin-top: 12px; }
  .arena-card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px;
    text-align: center;
  }
  .arena-vs { font-size: 1.3rem; font-weight: 900; color: var(--amber); }

  /* Summary Leaderboard */
  .summary-box {
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
    padding: 16px 18px; margin-bottom: 22px;
  }
  .summary-head { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; align-items: center; }
  .winners-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
  .win-chip {
    background: rgba(34,197,94,0.14); border: 1px solid rgba(34,197,94,0.4);
    color: #bbf7d0; border-radius: 8px; padding: 5px 10px; font-size: 0.8rem; font-weight: 600;
    cursor: pointer;
  }

  .sec-head {
    display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
    border-bottom: 1px solid var(--border); padding-bottom: 6px; margin: 24px 0 14px;
  }
  .sec-head h2 { margin: 0; font-size: 1.25rem; color: var(--blue); }
  .sec-head .sub { color: var(--muted); font-size: 0.88rem; }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(355px, 1fr)); gap: 14px; }
  .card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
    padding: 14px 16px; display: flex; flex-direction: column; gap: 9px;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  .card.playing { border-color: var(--blue); box-shadow: 0 0 0 1px var(--blue), 0 8px 24px rgba(56,189,248,0.18); }
  .card.voted-up { border-color: var(--green); background: linear-gradient(180deg, rgba(20,45,32,0.45), var(--panel)); }
  .card.voted-down { opacity: 0.62; border-color: var(--red); }

  .card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
  .title { font-weight: 800; font-size: 1rem; }
  .fname { font-size: 0.74rem; color: var(--muted); font-family: ui-monospace, monospace; }
  .badges { display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-end; }
  .tag {
    font-size: 0.7rem; font-weight: 800; padding: 2px 7px; border-radius: 6px; text-transform: uppercase;
  }
  .tag-live { background: rgba(34,197,94,0.18); color: #86efac; border: 1px solid rgba(34,197,94,0.4); }
  .tag-new { background: rgba(245,158,11,0.2); color: #fde68a; border: 1px solid rgba(245,158,11,0.45); }

  .quote {
    background: var(--panel2); border-left: 3px solid var(--blue); border-radius: 7px;
    padding: 6px 10px; font-style: italic; font-size: 0.92rem;
  }
  .desc { margin: 0; font-size: 0.82rem; color: var(--muted); }

  .wave {
    position: relative; height: 40px; background: #0d121b; border: 1px solid var(--border);
    border-radius: 8px; padding: 4px 6px; cursor: pointer; overflow: hidden;
  }
  .bars { display: flex; align-items: center; gap: 2px; height: 100%; position: relative; z-index: 2; }
  .bars span { flex: 1; background: #475569; border-radius: 2px; }
  .card.playing .bars span { background: #38bdf8; }
  .prog { position: absolute; left: 0; top: 0; bottom: 0; width: 0%; background: rgba(56,189,248,0.22); z-index: 1; }

  .pitch-row { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: var(--muted); }
  .pitch-row input { flex: 1; accent-color: var(--blue); }

  .vote-row {
    display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
    padding-top: 4px; border-top: 1px solid rgba(42,54,77,0.65);
  }
  .vbtn {
    border: 1px solid var(--border); background: var(--panel2); color: var(--text);
    border-radius: 8px; padding: 5px 10px; font-weight: 700; font-size: 0.82rem; cursor: pointer;
  }
  .vbtn.up.on { background: #16a34a; border-color: #4ade80; color: #fff; }
  .vbtn.dn.on { background: #dc2626; border-color: #f87171; color: #fff; }

  .stars { display: inline-flex; gap: 2px; margin-left: auto; }
  .star { background: none; border: none; color: #475569; font-size: 1.15rem; cursor: pointer; padding: 0 2px; }
  .star.on { color: var(--gold); }

  .roles-row { display: flex; flex-wrap: wrap; gap: 5px; }
  .role-chip {
    font-size: 0.72rem; padding: 3px 7px; border-radius: 6px;
    background: #101622; border: 1px solid var(--border); color: var(--muted); cursor: pointer;
  }
  .role-chip.on { background: rgba(56,189,248,0.2); border-color: var(--blue); color: #e0f2fe; font-weight: 700; }

  .note-in {
    width: 100%; background: #0e141f; border: 1px solid var(--border); color: var(--text);
    border-radius: 7px; padding: 5px 9px; font-size: 0.8rem;
  }

  @media (max-width: 740px) {
    .hero { grid-template-columns: 1fr; text-align: center; }
    .hero img { margin: 0 auto; }
    .arena-grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <img id="heroImg" alt="Pocket Kyle" onclick="playRandomWhoa()" title="Click Kyle for a random WHOAAA!" />
    <div>
      <h1>Kyle Sound Vote Lab — MORE WHOAAA WHOAAAA!</h1>
      <p>
        Audition every <strong>WHOAAA!</strong> take, warble remix, Superman Doppler scream, Kyle voice line,
        and 3D chrome scissor clang! Cast your <strong>&#128077; / &#128078; + 5&#9733; votes</strong>, test custom pitch sliders,
        run <strong>Head-to-Head Battle</strong> mode, and hit <strong>Copy My Votes</strong> to send me your exact picks for <code>zz_kyle.pk3</code>!
      </p>
    </div>
    <div class="hero-actions">
      <button class="btn btn-whoa" onclick="playRandomWhoa()">&#128266; PLAY RANDOM WHOAAA!</button>
      <button class="btn btn-battle" onclick="toggleArena()">&#9876;&#65039; Whoaaa! Head-to-Head Battle</button>
      <button class="btn" onclick="stopAll()">&#9632; Stop Sound</button>
    </div>
  </header>

  <div class="sticky-bar">
    <div class="filter-pills">
      <button class="tab-pill active" data-filter="all" onclick="setFilter('all')">All Sounds (32)</button>
      <button class="tab-pill" data-filter="whoa" onclick="setFilter('whoa')">More WHOAAA! (12)</button>
      <button class="tab-pill" data-filter="voice" onclick="setFilter('voice')">Kyle / Cut Lines (10)</button>
      <button class="tab-pill" data-filter="sfx" onclick="setFilter('sfx')">Scissors / Clangs / SFX (10)</button>
      <button class="tab-pill" data-filter="voted" onclick="setFilter('voted')">My Upvoted</button>
    </div>
    <div class="bar-right">
      <button class="btn btn-play" onclick="playSeq('whoa')">&#9654; Play All Whoaaas</button>
      <button class="btn btn-amber" id="copyBtn" onclick="copyVotes()">&#128203; Copy Vote Results</button>
      <button class="btn" onclick="resetVotes()">Reset</button>
    </div>
  </div>

  <div class="arena" id="arenaBox">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
      <strong>&#9876;&#65039; WHOAAA! TOURNAMENT BATTLE — Pick your favorite sound head-to-head!</strong>
      <button class="btn" onclick="nextBattle()">Skip / New Pair</button>
    </div>
    <div class="arena-grid" id="arenaGrid"></div>
  </div>

  <div class="summary-box">
    <div class="summary-head">
      <div>
        <strong id="voteStatsText">0 voted so far</strong>
        <span style="color:var(--muted); font-size:0.85rem;"> &mdash; saved automatically in this browser</span>
      </div>
      <div style="display:flex; gap:8px;">
        <button class="btn" onclick="playWinners()">&#9654; Play Top Voted</button>
      </div>
    </div>
    <div class="winners-row" id="winnersRow"></div>
  </div>

  <div id="sectionsMount"></div>
</div>

<script>
const HERO_SRC = "__HERO_IMG__";
if (HERO_SRC) document.getElementById("heroImg").src = HERO_SRC;

const SOUNDS = __SOUNDS_JSON__;
const soundMap = Object.fromEntries(SOUNDS.map(s => [s.id, s]));
const ALL_ROLES = ["Draw", "Throw / Torpedo", "Bird Lock", "Latch / Chop", "Roam", "Death"];
const STORE_KEY = "kyle_sound_votes_v1";

let votes = {};
try { votes = JSON.parse(localStorage.getItem(STORE_KEY) || "{}"); } catch {}

function saveVotes() {
  localStorage.setItem(STORE_KEY, JSON.stringify(votes));
  renderSummary();
}

function getVote(id) {
  if (!votes[id]) {
    const s = soundMap[id];
    votes[id] = { thumb: 0, stars: 0, pitch: 1.0, roles: [...s.roles], note: "" };
  }
  return votes[id];
}

let curFilter = "all";
let curAudio = null;
let curPlayingId = null;
let seqQueue = [];
let loopId = null;
let battlePair = null;

function stopAll() {
  seqQueue = [];
  if (curAudio) { curAudio.pause(); curAudio.currentTime = 0; curAudio = null; }
  if (curPlayingId) {
    document.querySelector(`.card[data-id="${curPlayingId}"]`)?.classList.remove("playing");
    const prog = document.querySelector(`.card[data-id="${curPlayingId}"] .prog`);
    if (prog) prog.style.width = "0%";
    curPlayingId = null;
  }
}

function playSound(id, onDone = null) {
  const wasSame = (curPlayingId === id);
  stopAll();
  if (wasSame && !onDone) return;
  const s = soundMap[id];
  const v = getVote(id);
  const a = new Audio(s.url);
  a.playbackRate = v.pitch || 1.0;
  try { a.preservesPitch = false; } catch {}
  curAudio = a;
  curPlayingId = id;
  const card = document.querySelector(`.card[data-id="${id}"]`);
  card?.classList.add("playing");

  a.ontimeupdate = () => {
    const p = card?.querySelector(".prog");
    if (p && a.duration) p.style.width = ((a.currentTime / a.duration) * 100) + "%";
  };
  a.onended = () => {
    if (loopId === id) { playSound(id, onDone); return; }
    card?.classList.remove("playing");
    const p = card?.querySelector(".prog");
    if (p) p.style.width = "0%";
    curPlayingId = null;
    curAudio = null;
    if (onDone) onDone();
    else if (seqQueue.length) playSound(seqQueue.shift());
  };
  a.play().catch(() => {});
}

function playRandomWhoa() {
  const pool = SOUNDS.filter(s => s.cat === "whoa");
  const pick = pool[Math.floor(Math.random() * pool.length)];
  loopId = null;
  playSound(pick.id);
}

function playSeq(cat) {
  stopAll();
  loopId = null;
  seqQueue = SOUNDS.filter(s => s.cat === cat).map(s => s.id);
  if (seqQueue.length) playSound(seqQueue.shift());
}

function toggleLoop(id) {
  loopId = (loopId === id) ? null : id;
  document.querySelectorAll(".btn-loop").forEach(b => b.textContent = (b.dataset.id === loopId ? "🔁 Looping" : "🔁 Loop"));
  if (loopId === id) playSound(id);
}

function setThumb(id, val) {
  const v = getVote(id);
  v.thumb = (v.thumb === val) ? 0 : val;
  if (v.thumb === 1 && v.stars === 0) v.stars = 5;
  if (v.thumb === -1) v.stars = 1;
  saveVotes();
  syncCardUI(id);
}

function setStars(id, st) {
  const v = getVote(id);
  v.stars = st;
  if (st >= 4 && v.thumb === 0) v.thumb = 1;
  else if (st <= 1 && v.thumb === 0) v.thumb = -1;
  saveVotes();
  syncCardUI(id);
}

function setPitch(id, val) {
  const v = getVote(id);
  v.pitch = parseFloat(val);
  saveVotes();
  const lbl = document.getElementById("pitchVal_" + id);
  if (lbl) lbl.textContent = v.pitch.toFixed(2) + "x";
}

function toggleRole(id, role) {
  const v = getVote(id);
  const idx = v.roles.indexOf(role);
  if (idx >= 0) v.roles.splice(idx, 1);
  else v.roles.push(role);
  saveVotes();
  syncCardUI(id);
}

function setNote(id, txt) {
  getVote(id).note = txt;
  saveVotes();
}

function syncCardUI(id) {
  const card = document.querySelector(`.card[data-id="${id}"]`);
  if (!card) return;
  const v = getVote(id);
  card.classList.toggle("voted-up", v.thumb === 1 || v.stars >= 4);
  card.classList.toggle("voted-down", v.thumb === -1);
  card.querySelector(".vbtn.up").classList.toggle("on", v.thumb === 1);
  card.querySelector(".vbtn.dn").classList.toggle("on", v.thumb === -1);
  card.querySelectorAll(".star").forEach(st => st.classList.toggle("on", Number(st.dataset.s) <= v.stars));
  card.querySelectorAll(".role-chip").forEach(rc => rc.classList.toggle("on", v.roles.includes(rc.dataset.r)));
}

function setFilter(f) {
  curFilter = f;
  document.querySelectorAll(".tab-pill").forEach(b => b.classList.toggle("active", b.dataset.filter === f));
  renderAll();
}

function toggleArena() {
  const box = document.getElementById("arenaBox");
  box.classList.toggle("open");
  if (box.classList.contains("open") && !battlePair) nextBattle();
}

function nextBattle() {
  const pool = SOUNDS.filter(s => s.cat === "whoa");
  const a = pool[Math.floor(Math.random() * pool.length)];
  let b = pool[Math.floor(Math.random() * pool.length)];
  while (b.id === a.id) b = pool[Math.floor(Math.random() * pool.length)];
  battlePair = [a, b];
  const g = document.getElementById("arenaGrid");
  g.innerHTML = [a, b].map((s, idx) => `
    <div class="arena-card">
      <div class="title">${s.title}</div>
      <div class="quote" style="margin:8px 0;">&ldquo;${s.quote}&rdquo;</div>
      <div style="display:flex; gap:8px; justify-content:center;">
        <button class="btn btn-play" onclick="playSound('${s.id}')">&#9654; Play</button>
        <button class="btn btn-whoa" style="padding:8px 12px; font-size:0.86rem;" onclick="pickWinner('${s.id}', '${idx === 0 ? b.id : a.id}')">&#127942; Vote Winner</button>
      </div>
    </div>
  `).join('<div class="arena-vs">VS</div>');
}

function pickWinner(winId, loseId) {
  const vw = getVote(winId);
  vw.thumb = 1;
  vw.stars = Math.min(5, Math.max(4, vw.stars + 1));
  saveVotes();
  syncCardUI(winId);
  nextBattle();
  playSound(battlePair[0].id);
}

function rankedWinners() {
  return SOUNDS.filter(s => {
    const v = votes[s.id];
    return v && (v.thumb > 0 || v.stars >= 3);
  }).sort((a, b) => {
    const va = votes[a.id], vb = votes[b.id];
    return ((vb.thumb * 3 + vb.stars) - (va.thumb * 3 + va.stars));
  });
}

function playWinners() {
  stopAll();
  const w = rankedWinners();
  if (!w.length) { playRandomWhoa(); return; }
  seqQueue = w.map(s => s.id);
  playSound(seqQueue.shift());
}

function renderSummary() {
  let up = 0, dn = 0, rated = 0;
  for (const s of SOUNDS) {
    const v = votes[s.id];
    if (!v) continue;
    if (v.thumb > 0) up++;
    if (v.thumb < 0) dn++;
    if (v.stars > 0) rated++;
  }
  document.getElementById("voteStatsText").textContent = `${up} Upvoted 👍 • ${dn} Skipped 👎 • ${rated} Star-Rated`;
  const winners = rankedWinners();
  document.getElementById("winnersRow").innerHTML = winners.length
    ? winners.map((s, i) => `<span class="win-chip" onclick="playSound('${s.id}')">#${i + 1} ${s.title} (${votes[s.id].stars}&#9733;)</span>`).join("")
    : `<span style="color:var(--muted); font-size:0.84rem;">Tap 👍 or &#9733; stars on your favorite sounds below to build your custom Kyle soundboard!</span>`;
}

function copyVotes() {
  const lines = ["KYLE SOUND VOTES:"];
  const winners = rankedWinners();
  if (winners.length) {
    lines.push("\n[TOP PICKED / KEEP]");
    for (const s of winners) {
      const v = votes[s.id];
      const pTxt = Math.abs(v.pitch - 1.0) > 0.02 ? ` @ pitch ${v.pitch.toFixed(2)}x` : "";
      const nTxt = v.note ? ` // note: ${v.note}` : "";
      lines.push(`- ${s.file}${pTxt} | ${v.stars}★ | roles=[${v.roles.join(", ")}]${nTxt}`);
    }
  }
  const downs = SOUNDS.filter(s => votes[s.id] && votes[s.id].thumb < 0);
  if (downs.length) {
    lines.push("\n[CUT / REMOVE]");
    for (const s of downs) lines.push(`- ${s.file}`);
  }
  const txt = lines.length > 1 ? lines.join("\n") : "No votes cast yet — upvote sounds first!";
  navigator.clipboard?.writeText(txt).then(() => {
    const b = document.getElementById("copyBtn");
    const old = b.textContent;
    b.textContent = "✅ Copied Votes!";
    setTimeout(() => b.textContent = old, 1600);
  }).catch(() => alert(txt));
}

function resetVotes() {
  if (!confirm("Reset all your local sound votes?")) return;
  votes = {};
  localStorage.removeItem(STORE_KEY);
  renderSummary();
  renderAll();
}

function renderAll() {
  const GROUPS = [
    ["whoa", "1. More WHOAAA WHOAAAA! Yells & Warbles", "Click to binge every whoa take & remix — upvote your favorites for throws & Superman Torpedo!"],
    ["voice", "2. Kyle Intros & Barber Cut Lines", "Voice lines played on pull-out, roaming, and wing/player latch"],
    ["sfx", "3. 3D Chrome Scissors, Metal Clangs, Lock & Cash", "Bouncing scissor steel clangs, snapping blades, lock radar & US bills"],
  ];

  const mount = document.getElementById("sectionsMount");
  mount.innerHTML = GROUPS.map(([gKey, gTitle, gSub]) => {
    const list = SOUNDS.filter(s => {
      if (s.cat !== gKey) return false;
      if (curFilter === "all") return true;
      if (curFilter === "voted") return votes[s.id] && (votes[s.id].thumb > 0 || votes[s.id].stars >= 4);
      return s.cat === curFilter;
    });
    if (!list.length) return "";
    return `
      <section>
        <div class="sec-head">
          <h2>${gTitle} (${list.length})</h2>
          <span class="sub">${gSub}</span>
        </div>
        <div class="grid">
          ${list.map(s => {
            const v = getVote(s.id);
            const bars = s.peaks.map(pk => `<span style="height:${Math.max(12, Math.round(pk * 100))}%"></span>`).join("");
            const badge = s.in_game
              ? `<span class="tag tag-live">In Game</span>`
              : `<span class="tag tag-new">New Option</span>`;
            const stars = [1,2,3,4,5].map(n => `<button class="star ${v.stars >= n ? "on" : ""}" data-s="${n}" onclick="setStars('${s.id}', ${n})">&#9733;</button>`).join("");
            const roles = ALL_ROLES.map(r => `<span class="role-chip ${v.roles.includes(r) ? "on" : ""}" data-r="${r}" onclick="toggleRole('${s.id}', '${r}')">${r}</span>`).join("");
            const cls = (v.thumb === 1 || v.stars >= 4) ? "voted-up" : (v.thumb === -1 ? "voted-down" : "");
            return `
              <article class="card ${cls}" data-id="${s.id}">
                <div class="card-top">
                  <div>
                    <div class="title">${s.title}</div>
                    <div class="fname">${s.file} &bull; ${s.dur.toFixed(2)}s</div>
                  </div>
                  <div class="badges">${badge}</div>
                </div>
                <div class="quote">&ldquo;${s.quote}&rdquo;</div>
                <p class="desc">${s.desc}</p>
                <div class="wave" onclick="playSound('${s.id}')">
                  <div class="bars">${bars}</div>
                  <div class="prog"></div>
                </div>
                <div class="pitch-row">
                  <span>Speed/Pitch:</span>
                  <input type="range" min="0.75" max="1.35" step="0.02" value="${v.pitch}" oninput="setPitch('${s.id}', this.value)" />
                  <strong id="pitchVal_${s.id}">${v.pitch.toFixed(2)}x</strong>
                </div>
                <div style="display:flex; gap:6px; align-items:center;">
                  <button class="btn btn-play" style="padding:6px 12px;" onclick="playSound('${s.id}')">&#9654; Play</button>
                  <button class="btn btn-loop" style="padding:6px 10px;" data-id="${s.id}" onclick="toggleLoop('${s.id}')">🔁 Loop</button>
                </div>
                <div class="vote-row">
                  <button class="vbtn up ${v.thumb === 1 ? "on" : ""}" onclick="setThumb('${s.id}', 1)">&#128077; Keep</button>
                  <button class="vbtn dn ${v.thumb === -1 ? "on" : ""}" onclick="setThumb('${s.id}', -1)">&#128078; Cut</button>
                  <div class="stars">${stars}</div>
                </div>
                <div class="roles-row">${roles}</div>
                <input class="note-in" placeholder="Optional note (e.g. 'play on bird throw!')" value="${v.note.replace(/"/g, '&quot;')}" oninput="setNote('${s.id}', this.value)" />
              </article>
            `;
          }).join("")}
        </div>
      </section>
    `;
  }).join("");
}

renderSummary();
renderAll();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
