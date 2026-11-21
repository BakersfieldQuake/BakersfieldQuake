r"""Imports all unique Larry audio clips from G:\Downloads\Telegram Desktop\larry sounds\files
into:
  - source/sound_bank/larry_telegram/raw/<clean_stem>.mp3   (original MP3s, deduplicated by SHA-256)
  - sound/larry_telegram/<clean_stem>.wav                   (22050 Hz mono s16le Quake-ready WAVs)
  - source/sound_bank/larry_telegram/manifest.json          (metadata, durations, tags)

Also builds:
  - docs/woo_cannon_sound_vote.html                         (self-contained sound menu & voting studio)
"""
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import wave
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
MOD_ROOT = MM_TOOLS.parent.parent
TG_FILES = Path(r"G:\Downloads\Telegram Desktop\larry sounds\files")

BANK_DIR = MOD_ROOT / "source" / "sound_bank" / "larry_telegram"
BANK_RAW_DIR = BANK_DIR / "raw"
GAME_LARRY_DIR = MOD_ROOT / "sound" / "larry_telegram"
REMIX_META = MOD_ROOT / "source" / "sound_bank" / "larry_remixes" / "manifest.json"
LARRY_MCCART_DIR = MOD_ROOT / "source" / "sound_bank" / "larry_mccart_clips"
RANDOM_DIR = MOD_ROOT / "source" / "sound_bank" / "random_sounds"
PK3_PATH = MOD_ROOT / "bakersfield.pk3"
OUT_HTML = MOD_ROOT / "docs" / "woo_cannon_sound_vote.html"

EXPLICIT_HINTS = (
    "n-i-gg", "negro", "masturbate", "boob", "titties", "nipple", "panties",
    "sexual", "under", "turn 18", "youre 18", "not 17", "heroin", "recreational drugs",
    "hormone balls", "dress", "lay on top", "feel my", "hangs down", "bra", "rub on you",
    "legs_wrapped", "physical stuff", "confidential", "address", "woman tonight",
    "sexy woman", "be your woman",
)

WEW_PATTERNS = ("wew", "gowewd")
DOUBLE_GOOD_PATTERNS = ("double good", "doublegood", "double_good", "quad good", "quadgood", "quadruple", "octogood", "thats good", "thats_good", "goooood", "omgdouble")

NEW_REMIX_STEMS = {
    "rmx_chg_slow_to_chipmunk_dbl",
    "rmx_chg_dj_scratch_wew",
    "rmx_chg_tape_slowdown_gowewd",
    "rmx_chg_2x_speedrun_panic",
    "rmx_sht_slomo_monster_gowewd",
    "rmx_sht_hyper_wew_dbl",
    "rmx_sht_dj_scratch_wew",
    "rmx_sht_stutter_gowewd",
    "rmx_scr_2x_speedrun_everything",
    "rmx_scr_slomo_demon_feels_wew",
    "rmx_scr_yoyo_rollercoaster",
    "rmx_scr_drunk_to_chipmunk",
    "rmx_scr_3speed_polyrhythm",
    "rmx_scr_ufo_alien_warble",
    "rmx_boom_slomo_banana",
    "rmx_boom_hyper_good_combo",
    "rmx_boom_tape_die_gowewd",
    "rmx_boom_choir_who_are_you",
    "rmx_run_2x_windows_me",
    "rmx_run_yoyo_dollar",
    "rmx_run_dj_larry_johnny",
    "rmx_run_slomo_drunk_feels",
    "rmx_run_stutter_dbl_wew",
    "rmx_run_hyper_giggle_chaos",
}

RANDOM_HIGHLIGHTS = [
    ("wewe.wav", "WEW! (short clip)"),
    ("wewe2.wav", "WEW WEW! (long clip)"),
    ("eweewew.wav", "Eweewew!"),
    ("eweweweIamawoman.wav", "Ewewewe I am a woman!"),
    ("oooooooewewewewew.wav", "Ooooooo ewewewewew!"),
    ("quakeahhwewew.wav", "Quake ahh wewew!"),
    ("quadgood.wav", "Quad good! (full)"),
    ("omgdouble.wav", "OMG double!"),
    ("that'sGOOOOOD.wav", "That's GOOOOOD!"),
    ("good.wav", "Good!"),
]

# Pre-existing curated labels for larry_mccart_clips
MCCART_LABELS = {
    "double_good": 'Double good!',
    "triple_ripple_quadruple_good": 'Triple good, ripple good, quadruple good!',
    "octogood": 'Octogood!',
    "banana_cannon": 'Banana cannon!',
    "love_to_play_quake": "I'd love to play Quake!",
    "giggle_hacks": 'Giggle hacks!',
    "love_that_echo": 'I love that echo!',
    "it_wont_boot": "It won't boot!",
    "interesting": 'Hmm, interesting.',
    "windows_me_you_ha": 'Windows me / Windows you / Windows heh',
    "windows_professional_2000": 'Windows Professional 2000',
    "i_believe_windows_2000": 'I believe I use Windows 2000',
    "should_i_double_click": 'Should I double click?',
    "another_menu": 'Is there supposed to be another menu?',
    "my_c_folder": 'Should I go to my C folder?',
    "yesterday_i_made_a_dollar": 'Yesterday I made a dollar',
    "play_with_knives": 'We get to play with knives',
    "joey_sewed_his_hands": 'My friend Joey sewed his hands together',
    "cant_say_that_feel_so_bad": "Oh I can't say that... feel so bad",
    "love_to_giggle": 'I love to giggle',
    "computer_commutes": 'My computer commutes with another computer',
    "dont_know_how_internet_works": "Truthfully speaking I don't know how it works",
    "listening_to_kelly_studios": "You're listening to Kelly Studios",
    "i_have_a_policy": "I have a policy",
    "dont_say_negative": "I don't say negative about anything",
    "cant_say_not_true": "I can't say something that's not true",
    "cigarettes": 'Cigarettes.',
    "kern_county_golf_champion": 'Kern County Junior Golf Champion',
    "womanly_man": "I'm a womanly man",
    "electricity": "It's like electricity",
    "how_can_i_say_no": 'How can I say no to Johnny?',
    "how_can_i_say_goodbye": 'How can I say goodbye to Johnny?',
    "i_dare_you": 'I dare you',
    "damn_nazis": 'Damn Nazis!',
    "im_not_sure": "I'm not sure",
}


def sanitize_stem(name: str) -> str:
    s = Path(name).stem.lower()
    s = re.sub(r"\(\d+\)$", "", s).strip()
    s = s.replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "clip"


def pretty_label(filename: str) -> str:
    s = Path(filename).stem
    s = re.sub(r"\s*\(\d+\)$", "", s).strip()
    s = re.sub(r"^Larry_", "", s, flags=re.I)
    s = s.replace("_", " ").strip()
    return s


def wav_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def convert_to_quake_wav(src: Path, dst_wav: Path) -> float:
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    # Trim silent edges lightly, normalize loudness to -14 LUFS / -1.5 dBTP, 22050 Hz mono s16le
    af = "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-42dB,areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-42dB,areverse,loudnorm=I=-14:TP=-1.5:LRA=11"
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", af, "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", str(dst_wav)],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not dst_wav.exists() or wav_duration(dst_wav) < 0.08:
        # Fallback without silenceremove if a very short/quiet clip got trimmed too aggressively
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", str(dst_wav)],
            check=True,
        )
    return wav_duration(dst_wav)


def encode_mp3_b64(src: Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
        tmp = Path(tf.name)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "22050", "-b:a", "64k", str(tmp)],
            check=True,
        )
        return "data:audio/mpeg;base64," + base64.b64encode(tmp.read_bytes()).decode("ascii")
    finally:
        if tmp.exists():
            tmp.unlink()


def classify_tags(text: str) -> list[str]:
    tl = text.lower()
    tags = []
    if any(k in tl for k in WEW_PATTERNS):
        tags.append("wew")
    if any(k in tl for k in DOUBLE_GOOD_PATTERNS):
        tags.append("double_good")
    if any(k in tl for k in EXPLICIT_HINTS):
        tags.append("explicit")
    return tags


def import_telegram_sounds():
    BANK_RAW_DIR.mkdir(parents=True, exist_ok=True)
    GAME_LARRY_DIR.mkdir(parents=True, exist_ok=True)

    seen_hashes = {}
    used_stems = set()
    entries = []

    for p in sorted(TG_FILES.iterdir()):
        if not p.is_file() or p.suffix.lower() not in (".mp3", ".wav", ".ogg"):
            continue
        raw_bytes = p.read_bytes()
        h = hashlib.sha256(raw_bytes).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes[h] = p.name

        stem = sanitize_stem(p.name)
        base_stem = stem
        n = 2
        while stem in used_stems:
            stem = f"{base_stem}_{n}"
            n += 1
        used_stems.add(stem)

        raw_dst = BANK_RAW_DIR / f"{stem}{p.suffix.lower()}"
        shutil.copy2(p, raw_dst)

        wav_dst = GAME_LARRY_DIR / f"{stem}.wav"
        dur = wav_duration(wav_dst) if wav_dst.is_file() else convert_to_quake_wav(raw_dst, wav_dst)

        label = pretty_label(p.name)
        tags = classify_tags(p.name + " " + label)
        entries.append({
            "stem": stem,
            "orig_file": p.name,
            "label": label,
            "dur": round(dur, 2),
            "tags": tags,
            "game_path": f"sound/larry_telegram/{stem}.wav",
            "raw_path": f"source/sound_bank/larry_telegram/raw/{raw_dst.name}",
            "sha256": h[:16],
        })

    (BANK_DIR / "manifest.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"[IMPORT] Copied {len(entries)} unique Telegram Larry sounds -> {BANK_RAW_DIR} & {GAME_LARRY_DIR}")
    return entries


def build_vote_html(tg_entries):
    clips = []
    audio_map = {}

    def add_clip(cid, label, source, wav_path: Path, dur: float, tags: list[str], game_path: str, suggested_slots=None, default_slot=None):
        clips.append({
            "id": cid,
            "label": label,
            "source": source,
            "dur": round(dur, 2),
            "tags": tags,
            "game_path": game_path,
            "suggested": suggested_slots or [],
            "default_slot": default_slot,
        })
        audio_map[cid] = encode_mp3_b64(wav_path)

    # 0. Custom Hilarious Gun Remixes (Wind-Ups, Echoes & Flying Screams — NEW ones first!)
    if REMIX_META.is_file():
        remix_rows = json.loads(REMIX_META.read_text(encoding="utf-8"))
        remix_rows.sort(key=lambda r: (0 if r["stem"] in NEW_REMIX_STEMS else 1))
        for r in remix_rows:
            rp = MOD_ROOT / r["game_path"]
            if not rp.is_file():
                continue
            tags = list(dict.fromkeys(r["tags"] + ["remix", f"slot_{r['slot']}"] + (["new"] if r["stem"] in NEW_REMIX_STEMS else [])))
            add_clip(
                cid=r["stem"],
                label=r["label"],
                source="Custom Gun Remix",
                wav_path=rp,
                dur=r["dur"],
                tags=tags,
                game_path=r["game_path"],
                suggested_slots=[r["slot"]],
            )

    # 1. All Telegram Larry clips (using the cleaned 22050Hz game WAV so preview matches in-game!)
    for i, e in enumerate(tg_entries):
        wav_p = MOD_ROOT / e["game_path"]
        tags = list(e["tags"])
        if "wew" in tags or "double_good" in tags:
            tags.append("spotlight")
        # Suggest good gun slots based on duration & vibe
        sugg = []
        if e["dur"] <= 1.8:
            sugg.append("shoot")
        if e["dur"] <= 2.9:
            sugg.append("lboom")
        sugg.append("lrun")
        if "wew" in tags or "scream" in e["stem"] or e["dur"] >= 2.0:
            sugg.append("scream")
        if "wew" in tags or "echo" in e["stem"]:
            sugg.append("charge")
        add_clip(
            cid=f"tg_{e['stem']}",
            label=e["label"],
            source="Telegram Larry",
            wav_path=wav_p,
            dur=e["dur"],
            tags=tags,
            game_path=e["game_path"],
            suggested_slots=sugg,
        )

    # 2. Best clean cuts from larry_mccart_clips
    for p in sorted(LARRY_MCCART_DIR.glob("*.wav")):
        stem = p.stem
        dur = wav_duration(p)
        label = MCCART_LABELS.get(stem, stem.replace("_", " "))
        tags = classify_tags(stem + " " + label)
        if stem in ("double_good", "triple_ripple_quadruple_good", "octogood", "banana_cannon", "love_that_echo", "giggle_hacks", "love_to_play_quake", "it_wont_boot", "interesting"):
            tags.append("spotlight")
        sugg = ["lrun"]
        if dur <= 2.4:
            sugg.append("lboom")
        if dur <= 1.6:
            sugg.append("shoot")
        add_clip(
            cid=f"mc_{stem}",
            label=label,
            source="Larry Prank Cuts",
            wav_path=p,
            dur=dur,
            tags=tags,
            game_path=f"source/sound_bank/larry_mccart_clips/{p.name}",
            suggested_slots=sugg,
        )

    # 3. WEW / Good classics from random_sounds
    for fname, label in RANDOM_HIGHLIGHTS:
        p = RANDOM_DIR / fname
        if not p.is_file():
            continue
        dur = wav_duration(p)
        tags = classify_tags(fname + " " + label)
        tags.append("spotlight")
        add_clip(
            cid=f"rs_{sanitize_stem(fname)}",
            label=label,
            source="Random Sounds (WEW/Good)",
            wav_path=p,
            dur=dur,
            tags=list(dict.fromkeys(tags)),
            game_path=f"source/sound_bank/random_sounds/{fname}",
            suggested_slots=["charge", "shoot", "scream", "lboom", "lrun"],
        )

    # 4. Current In-Game wcannon sounds from bakersfield.pk3 for reference
    with zipfile.ZipFile(PK3_PATH) as z, tempfile.TemporaryDirectory() as td:
        for slot_name, fname, lbl in [
            ("charge", "sound/wcannon/wc_charge.wav", "Current Game Charge (wc_charge)"),
            ("shoot",  "sound/wcannon/wc_shoot.wav",  "Current Game Shoot (wc_shoot)"),
            ("scream", "sound/wcannon/wc_scream.wav", "Current Game Scream (wc_scream)"),
            ("boom",   "sound/wcannon/wc_boom.wav",   "Current Game Boom (wc_boom)"),
        ]:
            if fname in z.namelist():
                tp = Path(td) / Path(fname).name
                tp.write_bytes(z.read(fname))
                dur = wav_duration(tp)
                add_clip(
                    cid=f"cur_{slot_name}",
                    label=lbl,
                    source="Current In-Game",
                    wav_path=tp,
                    dur=dur,
                    tags=["in_game"],
                    game_path=fname,
                    suggested_slots=[slot_name],
                    default_slot=slot_name,
                )

    html = VOTE_TEMPLATE.replace("/*__CLIPS__*/[]", json.dumps(clips, separators=(",", ":")))
    html = html.replace("/*__AUDIO__*/{}", json.dumps(audio_map, separators=(",", ":")))
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"[HTML OK] Wrote {OUT_HTML} ({OUT_HTML.stat().st_size / 1e6:.2f} MB, {len(clips)} clips)")


VOTE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Woo Cannon · Larry Sound Menu &amp; Vote</title>
<style>
  :root {
    --bg:#0b0f17; --panel:#121826; --panel2:#1a2234; --line:#28354e; --fg:#f1f5f9; --dim:#94a3b8;
    --acc:#38bdf8; --gold:#fbbf24; --hot:#fb923c; --ok:#4ade80; --bad:#f87171;
    --mono:Consolas,"IBM Plex Mono",monospace; --sans:"Segoe UI",system-ui,sans-serif;
  }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--fg); font:13.5px/1.45 var(--sans); padding-bottom:48px; }
  header { position:sticky; top:0; z-index:20; background:rgba(11,15,23,0.95); backdrop-filter:blur(8px); border-bottom:1px solid var(--line); padding:12px 18px; display:flex; flex-direction:column; gap:10px; }
  .top-row { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px; }
  h1 { font-size:19px; font-weight:900; letter-spacing:0.02em; }
  h1 small { font:400 12px var(--mono); color:var(--dim); margin-left:8px; }
  .actions { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
  button { background:var(--panel2); color:var(--fg); border:1px solid var(--line); border-radius:6px; padding:6px 11px; font:600 12px var(--sans); cursor:pointer; transition:0.12s; }
  button:hover { border-color:var(--acc); }
  button.primary { background:var(--gold); color:#1a1000; border-color:var(--gold); font-weight:800; }
  button.test-seq { background:linear-gradient(135deg,#f97316,#ef4444); color:#fff; border-color:#fdba74; font-weight:800; }
  button.on { background:var(--acc); color:#06101e; border-color:var(--acc); font-weight:800; }
  button.on-ok { background:#143d26; color:#86efac; border-color:var(--ok); }
  button.on-bad { background:#3f1519; color:#fca5a5; border-color:var(--bad); }
  button.on-gold { background:#3b2908; color:#fde68a; border-color:var(--gold); }

  .loadout { display:grid; grid-template-columns:repeat(auto-fit,minmax(195px,1fr)); gap:8px; }
  .slot-box { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:8px 10px; display:flex; flex-direction:column; gap:4px; }
  .slot-box b { font:700 11px var(--mono); text-transform:uppercase; letter-spacing:0.06em; color:var(--acc); display:flex; justify-content:space-between; }
  .slot-val { font-size:12px; color:var(--fg); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; cursor:pointer; }
  .slot-val.empty { color:var(--dim); font-style:italic; }
  .pool-chips { display:flex; flex-wrap:wrap; gap:4px; max-height:46px; overflow:auto; }
  .pool-chip { background:#1e293b; border:1px solid #334155; border-radius:4px; padding:1px 6px; font-size:11px; cursor:pointer; }
  .pool-chip:hover { border-color:var(--gold); }

  .toolbar { max-width:1360px; margin:14px auto 0; padding:0 18px; display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:space-between; }
  .filters { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
  .search-wrap { display:flex; gap:8px; align-items:center; }
  input[type=search] { background:var(--panel); border:1px solid var(--line); color:var(--fg); border-radius:6px; padding:7px 11px; width:260px; font:13px var(--sans); }
  label.chk { display:flex; align-items:center; gap:6px; color:var(--dim); font-size:12px; cursor:pointer; }
  label.chk input { accent-color:var(--gold); }

  .section { max-width:1360px; margin:16px auto 0; padding:0 18px; }
  .sec-head { display:flex; align-items:baseline; gap:10px; margin-bottom:9px; }
  .sec-head h2 { font-size:16px; font-weight:800; color:#f8fafc; }
  .sec-head span { font:12px var(--mono); color:var(--dim); }

  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:9px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:9px; padding:10px 11px; display:flex; flex-direction:column; gap:7px; position:relative; transition:0.12s; }
  .card.playing { border-color:var(--acc); box-shadow:0 0 0 1px var(--acc); }
  .card.spotlight { border-color:#523c14; background:linear-gradient(180deg,#18171c 0%,#121826 100%); }
  .card-top { display:grid; grid-template-columns:36px 1fr auto; gap:9px; align-items:center; }
  .play-btn { width:36px; height:36px; border-radius:50%; padding:0; font-size:14px; display:flex; align-items:center; justify-content:center; background:#1e293b; border:1px solid #334155; }
  .card.playing .play-btn { background:var(--acc); color:#06101e; border-color:var(--acc); }
  .title { font-weight:700; font-size:13.5px; color:#f8fafc; word-break:break-word; }
  .meta { display:flex; flex-wrap:wrap; gap:5px; align-items:center; margin-top:2px; font:11px var(--mono); color:var(--dim); }
  .tag { padding:1px 6px; border-radius:4px; background:#1e293b; color:#cbd5e1; font:700 10px var(--mono); }
  .tag.new { background:#064e3b; color:#6ee7b7; border:1px solid #10b981; }
  .tag.wew { background:#451a03; color:#fdba74; border:1px solid #9a3412; }
  .tag.dg { background:#143829; color:#86efac; border:1px solid #166534; }
  .tag.rmx { background:#3b0764; color:#e9d5ff; border:1px solid #7e22ce; }
  .tag.cur { background:#172554; color:#93c5fd; border:1px solid #1d4ed8; }
  .tag.exp { background:#3f1519; color:#fca5a5; }
  .prog { height:3px; background:#1e293b; border-radius:2px; overflow:hidden; }
  .prog i { display:block; height:100%; width:0%; background:var(--acc); }

  .card-btns { display:flex; flex-wrap:wrap; gap:5px; align-items:center; }
  .card-btns button { padding:4px 7px; font-size:11.5px; }
  .sep { flex:1; }
  .toast { position:fixed; bottom:18px; left:50%; transform:translateX(-50%); background:#1e293b; border:1px solid var(--gold); color:#fde68a; padding:8px 16px; border-radius:8px; font-weight:700; opacity:0; pointer-events:none; transition:0.18s; z-index:50; }
  .toast.on { opacity:1; }
</style>
</head>
<body>
<header>
  <div class="top-row">
    <h1>WOO CANNON · LARRY SOUND MENU &amp; VOTE <small id="count-lbl"></small></h1>
    <div class="actions">
      <button class="test-seq" id="btn-test-seq">▶ Test Full Gun Sequence</button>
      <button id="btn-stop">■ Stop</button>
      <button class="primary" id="btn-dl">Download votes JSON</button>
      <button id="btn-cp">Copy JSON</button>
      <button id="btn-rs">Reset votes</button>
    </div>
  </div>
  <div class="loadout" id="loadout"></div>
</header>

<div class="toolbar">
  <div class="filters" id="filters">
    <button class="on" data-f="best">🔥 Best Gun Menu + Remixes</button>
    <button data-f="new">🆕 NEW Remixes</button>
    <button data-f="remix">🎛️ All Remixes</button>
    <button data-f="slot_charge">⚡ Wind-Ups</button>
    <button data-f="slot_shoot">💥 Gun Shots</button>
    <button data-f="slot_scream">🚀 Fly Screams</button>
    <button data-f="slot_lboom">💣 Boom Shouts</button>
    <button data-f="slot_lrun">🕺 Dance Lines</button>
    <button data-f="wew">WEW!!! Only</button>
    <button data-f="double_good">Double / Quad Good</button>
    <button data-f="liked">👍 Liked / Picked</button>
    <button data-f="all">📦 All Clips</button>
  </div>
  <div class="search-wrap">
    <label class="chk"><input type="checkbox" id="chk-explicit"> include NSFW/explicit raw clips</label>
    <input type="search" id="search" placeholder="Search clips (wew, double, windows...)">
  </div>
</div>

<div id="content"></div>
<div class="toast" id="toast"></div>

<script>
const CLIPS = /*__CLIPS__*/[];
const AUDIO = /*__AUDIO__*/{};

const SLOTS = [
  { k:"charge", name:"1 · Charge-Up",    multi:false, hint:"Held fire wind-up (~1.5s)" },
  { k:"shoot",  name:"2 · Blast-Off",    multi:false, hint:"Cannon launch shot" },
  { k:"scream", name:"3 · Fly Screams",  multi:true,  hint:"Screaming a bunch of Larry stuff in flight (multi-pick!)" },
  { k:"lboom",  name:"4 · Boom Shouts",  multi:true,  hint:"Random explosion shouts (up to 8)" },
  { k:"lrun",   name:"5 · Dance Lines",  multi:true,  hint:"Post-crash crazed runner lines (up to 12)" },
];

const STORE = "woo_larry_sound_vote_v4";
let state = {
  picks: {
    charge:"rmx_chg_gowewd_ratchet",
    shoot:"tg_gowewd",
    scream:["rmx_scr_wew_who_are_you"],
    lboom:[],
    lrun:["rmx_scr_wew_who_are_you"],
  },
  like: {},
  dislike: {},
};
try {
  const s = JSON.parse(localStorage.getItem(STORE) || "null");
  if (s && s.picks) {
    const scr = Array.isArray(s.picks.scream) ? s.picks.scream : (s.picks.scream ? [s.picks.scream] : []);
    state = { picks:{ charge:s.picks.charge||null, shoot:s.picks.shoot||null, scream:scr, lboom:s.picks.lboom||[], lrun:s.picks.lrun||[] }, like:s.like||{}, dislike:s.dislike||{} };
  }
} catch (e) {}

let filter = "best";
let playingId = null;
let seqAbort = false;
const audio = new Audio();
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const byId = id => CLIPS.find(c => c.id === id);
const save = () => { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) {} };

function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("on");
  clearTimeout(t._tm); t._tm = setTimeout(() => t.classList.remove("on"), 2000);
}

function play(id) {
  seqAbort = true;
  if (playingId === id && !audio.paused) { audio.pause(); return; }
  playingId = id;
  audio.src = AUDIO[id];
  audio.play().catch(() => toast("Could not play clip"));
  paintPlaying();
}

function stopAudio() {
  seqAbort = true;
  audio.pause();
  audio.currentTime = 0;
  playingId = null;
  paintPlaying();
}

async function testSequence() {
  seqAbort = false;
  const scrId = state.picks.scream.length ? state.picks.scream[Math.floor(Math.random() * state.picks.scream.length)] : "cur_scream";
  const boomId = state.picks.lboom.length ? state.picks.lboom[Math.floor(Math.random() * state.picks.lboom.length)] : "cur_boom";
  const runId = state.picks.lrun.length ? state.picks.lrun[Math.floor(Math.random() * state.picks.lrun.length)] : null;
  const seq = [
    ["Charge", state.picks.charge || "rmx_chg_wew_turbine"],
    ["Shoot",  state.picks.shoot  || "rmx_sht_wew_cannon"],
    ["Scream", scrId],
    ["Boom",   boomId],
    ["Run",    runId],
  ].filter(x => x[1] && AUDIO[x[1]]);
  if (!seq.length) { toast("Pick some sounds first!"); return; }
  for (const [nm, id] of seq) {
    if (seqAbort) break;
    toast(`Playing ${nm}: ${byId(id).label}`);
    playingId = id;
    audio.src = AUDIO[id];
    paintPlaying();
    await new Promise(res => {
      const done = () => { audio.removeEventListener("ended", done); audio.removeEventListener("pause", done); res(); };
      audio.addEventListener("ended", done);
      audio.addEventListener("pause", done);
      audio.play().catch(done);
    });
    if (seqAbort) break;
    await new Promise(r => setTimeout(r, 150));
  }
}

audio.addEventListener("ended", () => { playingId = null; paintPlaying(); });
audio.addEventListener("pause", paintPlaying);
audio.addEventListener("play", paintPlaying);
audio.addEventListener("timeupdate", () => {
  const bar = document.querySelector(".card.playing .prog i");
  if (bar && audio.duration) bar.style.width = (100 * audio.currentTime / audio.duration) + "%";
});

function paintPlaying() {
  document.querySelectorAll(".card").forEach(el => {
    const on = el.dataset.id === playingId && !audio.paused;
    el.classList.toggle("playing", on);
    el.querySelector(".play-btn").innerHTML = on ? "&#10074;&#10074;" : "&#9654;";
    if (!on) el.querySelector(".prog i").style.width = "0";
  });
}

function toggleSlot(id, slotKey) {
  const sl = SLOTS.find(s => s.k === slotKey);
  if (sl.multi) {
    const arr = state.picks[slotKey];
    const idx = arr.indexOf(id);
    if (idx >= 0) arr.splice(idx, 1);
    else arr.push(id);
  } else {
    state.picks[slotKey] = (state.picks[slotKey] === id) ? null : id;
  }
  save(); render();
}

function toggleVote(id, kind) {
  const other = kind === "like" ? "dislike" : "like";
  if (state[kind][id]) delete state[kind][id];
  else { state[kind][id] = 1; delete state[other][id]; }
  save(); render();
}

function isPickedAny(id) {
  return SLOTS.some(s => s.multi ? state.picks[s.k].includes(id) : state.picks[s.k] === id);
}

function visibleClips() {
  const q = $("#search").value.trim().toLowerCase();
  const incExp = $("#chk-explicit").checked;
  return CLIPS.filter(c => {
    if (!incExp && c.tags.includes("explicit") && filter !== "all") return false;
    if (q && !(c.label.toLowerCase().includes(q) || c.game_path.toLowerCase().includes(q) || c.source.toLowerCase().includes(q))) return false;
    if (filter === "new") return c.tags.includes("new");
    if (filter === "remix") return c.tags.includes("remix");
    if (filter.startsWith("slot_")) return c.tags.includes("remix") && c.tags.includes(filter);
    if (filter === "wew") return c.tags.includes("wew");
    if (filter === "double_good") return c.tags.includes("double_good");
    if (filter === "liked") return !!state.like[c.id] || isPickedAny(c.id);
    if (filter === "best") return !c.tags.includes("explicit");
    return true;
  });
}

function renderCard(c) {
  const on = c.id === playingId && !audio.paused;
  const spot = c.tags.includes("remix") || c.tags.includes("wew") || c.tags.includes("double_good");
  const tagsHtml = [
    c.tags.includes("new") ? `<span class="tag new">🆕 NEW</span>` : "",
    c.tags.includes("remix") ? `<span class="tag rmx">CUSTOM REMIX</span>` : "",
    c.tags.includes("wew") ? `<span class="tag wew">WEW!!!</span>` : "",
    c.tags.includes("double_good") ? `<span class="tag dg">DOUBLE / QUAD GOOD!</span>` : "",
    c.tags.includes("in_game") ? `<span class="tag cur">CURRENT IN-GAME</span>` : "",
    c.tags.includes("explicit") ? `<span class="tag exp">NSFW</span>` : "",
    `<span class="tag">${esc(c.source)}</span>`,
    `<span>${c.dur.toFixed(2)}s</span>`,
  ].join("");

  const slotBtns = SLOTS.map(s => {
    const active = s.multi ? state.picks[s.k].includes(c.id) : state.picks[s.k] === c.id;
    const short = s.k === "charge" ? "Charge" : s.k === "shoot" ? "Shoot" : s.k === "scream" ? "+Scream" : s.k === "lboom" ? "+Boom" : "+Run";
    return `<button class="${active ? "on-gold" : ""}" data-slot="${c.id}:${s.k}" title="${esc(s.hint)}">${active ? "★ " : ""}${short}</button>`;
  }).join("");

  return `<div class="card${spot ? " spotlight" : ""}${on ? " playing" : ""}" data-id="${c.id}">
    <div class="card-top">
      <button class="play-btn" data-play="${c.id}" aria-label="Play ${esc(c.label)}">${on ? "&#10074;&#10074;" : "&#9654;"}</button>
      <div>
        <div class="title">${esc(c.label)}</div>
        <div class="meta">${tagsHtml}</div>
      </div>
      <div style="display:flex;gap:4px;">
        <button class="${state.like[c.id] ? "on-ok" : ""}" data-vote="${c.id}:like" title="Like">👍</button>
        <button class="${state.dislike[c.id] ? "on-bad" : ""}" data-vote="${c.id}:dislike" title="Dislike">👎</button>
      </div>
    </div>
    <div class="prog"><i></i></div>
    <div class="card-btns">${slotBtns}</div>
  </div>`;
}

function render() {
  $("#loadout").innerHTML = SLOTS.map(s => {
    if (s.multi) {
      const ids = state.picks[s.k];
      const chips = ids.length
        ? ids.map(id => { const c = byId(id); return c ? `<span class="pool-chip" data-play="${id}" title="Click to play">${esc(c.label)}</span>` : ""; }).join("")
        : `<span class="slot-val empty">none selected yet</span>`;
      return `<div class="slot-box"><b><span>${esc(s.name)}</span><span>${ids.length} picked</span></b><div class="pool-chips">${chips}</div></div>`;
    } else {
      const id = state.picks[s.k], c = id && byId(id);
      return `<div class="slot-box"><b><span>${esc(s.name)}</span><span>${c ? c.dur.toFixed(1)+"s" : "—"}</span></b>
        <div class="slot-val${c ? "" : " empty"}" ${c ? `data-play="${c.id}"` : ""}>${c ? "★ " + esc(c.label) : "click ★ on a clip below"}</div></div>`;
    }
  }).join("");

  const list = visibleClips();
  $("#count-lbl").textContent = `${list.length} shown · ${CLIPS.length} total`;

  const newRemixes = list.filter(c => c.tags.includes("new"));
  const remixes = list.filter(c => c.tags.includes("remix") && !c.tags.includes("new"));
  const wewAndGood = list.filter(c => !c.tags.includes("remix") && (c.tags.includes("wew") || c.tags.includes("double_good")));
  const rest = list.filter(c => !c.tags.includes("remix") && !c.tags.includes("wew") && !c.tags.includes("double_good"));

  let html = "";
  if (filter === "best" || filter === "all" || filter === "liked") {
    if (newRemixes.length) html += `<section class="section"><div class="sec-head"><h2>🆕 NEW Speed-Up, Slow-Down &amp; Funny Remixes</h2><span>${newRemixes.length} clips</span></div><div class="grid">${newRemixes.map(renderCard).join("")}</div></section>`;
    if (remixes.length) html += `<section class="section"><div class="sec-head"><h2>🎛️ Earlier Custom Gun Remixes (Wind-Ups, Echoes &amp; Flying Screams)</h2><span>${remixes.length} clips</span></div><div class="grid">${remixes.map(renderCard).join("")}</div></section>`;
    if (wewAndGood.length) html += `<section class="section"><div class="sec-head"><h2>⚡ "WEW!!!" &amp; "Double / Quad Good!" Spotlight</h2><span>${wewAndGood.length} clips</span></div><div class="grid">${wewAndGood.map(renderCard).join("")}</div></section>`;
    if (rest.length) html += `<section class="section"><div class="sec-head"><h2>🎙️ Best Larry Voice Clips &amp; Game Reference</h2><span>${rest.length} clips</span></div><div class="grid">${rest.map(renderCard).join("")}</div></section>`;
  } else {
    html += `<section class="section"><div class="sec-head"><h2>Clips</h2><span>${list.length} clips</span></div><div class="grid">${list.map(renderCard).join("")}</div></section>`;
  }
  $("#content").innerHTML = html;
}

function buildResult() {
  const expand = id => { const c = byId(id); return c ? { id:c.id, label:c.label, game_path:c.game_path, dur:c.dur } : null; };
  return {
    picks: {
      charge: expand(state.picks.charge),
      shoot:  expand(state.picks.shoot),
      scream: state.picks.scream.map(expand).filter(Boolean),
      lboom:  state.picks.lboom.map(expand).filter(Boolean),
      lrun:   state.picks.lrun.map(expand).filter(Boolean),
    },
    likes: Object.keys(state.like).map(expand).filter(Boolean),
    dislikes: Object.keys(state.dislike).map(expand).filter(Boolean),
  };
}

document.addEventListener("click", e => {
  const p = e.target.closest("[data-play]");
  if (p) { play(p.dataset.play); return; }
  const s = e.target.closest("[data-slot]");
  if (s) { const [id, k] = s.dataset.slot.split(":"); toggleSlot(id, k); return; }
  const v = e.target.closest("[data-vote]");
  if (v) { const [id, kind] = v.dataset.vote.split(":"); toggleVote(id, kind); return; }
  const f = e.target.closest("#filters button");
  if (f) {
    filter = f.dataset.f;
    document.querySelectorAll("#filters button").forEach(b => b.classList.toggle("on", b === f));
    render();
  }
});

$("#search").addEventListener("input", render);
$("#chk-explicit").addEventListener("change", render);
$("#btn-test-seq").addEventListener("click", testSequence);
$("#btn-stop").addEventListener("click", stopAudio);
$("#btn-dl").addEventListener("click", () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(buildResult(), null, 2)], {type:"application/json"}));
  a.download = "woo_cannon_sound_votes.json"; a.click();
  toast("Downloaded woo_cannon_sound_votes.json");
});
$("#btn-cp").addEventListener("click", async () => {
  const txt = JSON.stringify(buildResult(), null, 2);
  try { await navigator.clipboard.writeText(txt); toast("Copied votes JSON!"); }
  catch (e) { const t = document.createElement("textarea"); t.value = txt; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); toast("Copied votes JSON!"); }
});
$("#btn-rs").addEventListener("click", () => {
  if (!confirm("Reset all Woo Cannon sound votes?")) return;
  state = { picks:{ charge:null, shoot:null, scream:[], lboom:[], lrun:[] }, like:{}, dislike:{} };
  save(); render();
});
document.addEventListener("keydown", e => { if (e.key === "Escape") stopAudio(); });

document.querySelectorAll("#filters button").forEach(b => {
  const f = b.dataset.f;
  if (f === "new") b.textContent += ` (${CLIPS.filter(c => c.tags.includes("new")).length})`;
  else if (f === "remix") b.textContent += ` (${CLIPS.filter(c => c.tags.includes("remix")).length})`;
  else if (f.startsWith("slot_")) b.textContent += ` (${CLIPS.filter(c => c.tags.includes("remix") && c.tags.includes(f)).length})`;
});
render();
</script>
</body>
</html>
"""


def main():
    tg_entries = import_telegram_sounds()
    build_vote_html(tg_entries)


if __name__ == "__main__":
    main()
