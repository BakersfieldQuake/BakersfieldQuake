"""Builds a self-contained HTML review page for /home/computer/Downloads/Telegram Desktop/selected_sounds.

Deduplicates exact byte-identical WAVs, groups them into clean categories, assigns
canonical Sound 1..N numbers, precomputes waveform peaks, embeds base64 WAV audio,
and writes docs/selected_sounds.html.

Usage:
    python3 source/mm_tools/build_selected_sounds_page.py [sounds_dir] [out_html]
"""
import array
import base64
import datetime
import hashlib
import json
import os
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEFAULT_SRC = Path("/home/computer/Downloads/Telegram Desktop/selected_sounds")
DEFAULT_OUT = ROOT / "docs" / "selected_sounds.html"
TEMPLATE = HERE / "selected_sounds.template.html"

GROUPS = [
    ("greetings", "Greetings & Hellos", "Openers, goodbyes, good morning, hello clips"),
    ("characters", "Rob / Calc / Canis Lupus", "Named voices, Rob, Calc, Canis Lupus, Paul, eweewew"),
    ("reactions", "Reactions & Exclamations", "Good, gg, hell yeah, BUH2, durr, damnit"),
    ("sfx_laughs", "Laughs, Giggles & SFX", "Giggles, heh, chicken, farts"),
    ("misc", "Phrases & Wildcards", "Longer lines, weird quotes, dotdot, dude I'm so lead"),
]

# Explicit group assignment for every unique canonical filename so Sound 1..N order is deterministic.
GROUP_OF = {
    # greetings
    "good-morning.wav": "greetings",
    "hello-2.wav": "greetings",
    "hello-i-am-good.wav": "greetings",
    "hello-hello-hello-hello-hello-hello-hello.wav": "greetings",
    "hello-i-live-in-the-jedo-you-know-what-i-mean.wav": "greetings",
    "goodbye-2.wav": "greetings",
    # characters
    "CanisLupusFantasy.wav": "characters",
    "canislupusfantasy2.wav": "characters",
    "hello-this-is-rob-i-am-talking-to-gainus-lubus.wav": "characters",
    "calc.wav": "characters",
    "calc1.wav": "characters",
    "big-long-strand-of-wires-that-s-paul.wav": "characters",
    "eweewew.wav": "characters",
    # reactions
    "good.wav": "reactions",
    "good-2.wav": "reactions",
    "goooooood.wav": "reactions",
    "gg.wav": "reactions",
    "hell-yeah.wav": "reactions",
    "BUH2.WAV": "reactions",
    "durrR.wav": "reactions",
    "damnit-my-wave.wav": "reactions",
    "damn-nazi.wav": "reactions",
    "are-defrauding-stalls.wav": "reactions",
    # sfx_laughs
    "giggles.wav": "sfx_laughs",
    "giggleh4x.wav": "sfx_laughs",
    "heh.wav": "sfx_laughs",
    "chicken.wav": "sfx_laughs",
    "fart.wav": "sfx_laughs",
    "fart2.wav": "sfx_laughs",
    "fart23.wav": "sfx_laughs",
    "fart3.wav": "sfx_laughs",
    # misc
    "900hour.wav": "misc",
    "awimist.wav": "misc",
    "bigmetaldildos.wav": "misc",
    "can-t-eat-your-best-money-see-make-it-out-to-the-world-in-a-mad-change.wav": "misc",
    "cit-e.wav": "misc",
    "day.wav": "misc",
    "firstday.wav": "misc",
    "dotdot.wav": "misc",
    "dude-i-m-so-lead.wav": "misc",
    "hearh.wav": "misc",
    "hey-there-s-never-been-one-that-freeble-at-all.wav": "misc",
}

# Preferred canonical representative when two or more files have identical bytes.
PREFERRED_NAME = {
    "can-you-see-the-little-open-span-to-see.wav": "CanisLupusFantasy.wav",
    "FTH.WAV": "hell-yeah.wav",
    "day-2.wav": "day.wav",
    "giggle-hacks-clicking.wav": "giggleh4x.wav",
    "giggle-hacks-clicking-2.wav": "giggleh4x.wav",
    "hel-helhel-helooooooooooooo.wav": "hello-hello-hello-hello-hello-hello-hello.wav",
    "helloiamgood.wav": "hello-i-am-good.wav",
}


def wav_info_and_peaks(path: Path, bars: int = 72):
    raw_bytes = path.read_bytes()
    with wave.open(str(path), "rb") as w:
        ch = w.getnchannels()
        sr = w.getframerate()
        sw = w.getsampwidth()
        nframes = w.getnframes()
        frames = w.readframes(nframes)
    dur = round(nframes / float(sr), 2) if sr else 0.0
    if sw == 1:
        samples = [b - 128 for b in frames]
        max_amp = 128.0
    elif sw == 2:
        arr = array.array("h")
        arr.frombytes(frames)
        if sys.byteorder != "little":
            arr.byteswap()
        samples = arr
        max_amp = 32768.0
    else:
        samples = [0]
        max_amp = 1.0

    total = len(samples)
    peaks = []
    if total == 0:
        peaks = [0.05] * bars
    else:
        step = max(1, total // bars)
        for i in range(bars):
            start = (i * total) // bars
            end = min(total, ((i + 1) * total) // bars)
            if start >= end:
                peaks.append(0.05)
                continue
            stride = max(1, (end - start) // 256)
            pk = max(abs(samples[j]) for j in range(start, end, stride)) / max_amp
            peaks.append(round(min(1.0, pk), 3))
        top = max(peaks) or 1.0
        if top < 0.85:
            scale = 0.92 / top
            peaks = [round(min(1.0, p * scale), 3) for p in peaks]

    ch_label = "Mono" if ch == 1 else "Stereo"
    spec = f"{sr / 1000:.1f} kHz · {ch_label} · {sw * 8}-bit"
    mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    return dur, spec, mtime, peaks, b64


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    if not src.is_dir():
        sys.exit(f"Source directory not found: {src}")

    by_hash = {}
    for p in sorted(src.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_file() or p.suffix.lower() != ".wav":
            continue
        h = hashlib.md5(p.read_bytes()).hexdigest()
        by_hash.setdefault(h, []).append(p)

    # Collapse exact byte duplicates and attach dude-i-m-so-lead-2.wav as alt encoding.
    entries = {}
    alt_lead = None
    for h, paths in by_hash.items():
        names = [p.name for p in paths]
        canon = next((n for n in names if n not in PREFERRED_NAME), names[0])
        if len(names) > 1:
            for n in names:
                if n not in PREFERRED_NAME and n in GROUP_OF:
                    canon = n
                    break
        canon_path = next(p for p in paths if p.name == canon)
        aliases = [n for n in names if n != canon]
        if canon == "dude-i-m-so-lead-2.wav":
            dur, spec, mtime, peaks, b64 = wav_info_and_peaks(canon_path)
            alt_lead = {"file": canon, "spec": spec, "b64": b64}
            continue
        entries[canon] = (canon_path, aliases)

    group_meta = {gid: {"id": gid, "name": name, "desc": desc} for gid, name, desc in GROUPS}
    ordered_keys = []
    for gid, _, _ in GROUPS:
        for k, g in GROUP_OF.items():
            if g == gid and k in entries:
                ordered_keys.append(k)
    for k in sorted(entries):
        if k not in ordered_keys:
            ordered_keys.append(k)

    sounds = []
    for idx, fname in enumerate(ordered_keys, start=1):
        p, aliases = entries[fname]
        gid = GROUP_OF.get(fname, "misc")
        dur, spec, mtime, peaks, b64 = wav_info_and_peaks(p)
        item = {
            "id": f"s{idx}",
            "num": idx,
            "group": gid,
            "groupName": group_meta[gid]["name"],
            "file": fname,
            "aliases": aliases,
            "dur": dur,
            "spec": spec,
            "mtime": mtime,
            "peaks": peaks,
            "b64": b64,
        }
        if fname == "dude-i-m-so-lead.wav" and alt_lead:
            item["alt"] = alt_lead
        sounds.append(item)

    tpl = TEMPLATE.read_text(encoding="utf-8")
    html = (
        tpl.replace("/*SOUNDS*/[]", json.dumps(sounds))
        .replace("/*GROUPS*/[]", json.dumps([group_meta[g[0]] for g in GROUPS]))
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({len(sounds)} unique sounds from {sum(len(v) for v in by_hash.values())} files, {out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
