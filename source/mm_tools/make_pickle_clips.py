"""Cut the Pickle Surprise mp3 into short clips for picking the weapon's sounds, and write the voting page.
  source/pickle_sound_vote/clips/NNN.mp3   one clip each
  source/pickle_sound_vote/clips.json      id, start, end, duration, what was said (faster-whisper; blank for noises and music)
  source/pickle_sound_vote/index.html      open it in a browser: play, vote, download votes.json
python make_pickle_clips.py <audio.mp3> [out_dir]
Needs ffmpeg on PATH, numpy and faster-whisper (run it without -I so they are found)."""
import json
import os
import subprocess
import sys

import numpy as np

AUDIO = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pickle_sound_vote")
OUT = os.path.abspath(OUT)
HERE = os.path.dirname(os.path.abspath(__file__))

SR = 22050
HOP = SR // 100         # 10 ms frames
QUIET_DB = -37          # smoothed level below this counts as a dip
DIP = 0.09              # seconds of dip that make a boundary
MIN_LEN = 0.5           # shorter clips are merged into a neighbour
MAX_LEN = 3.0           # longer ones are cut at their quietest point
PINNED = [("P1", 93.20, 94.80, "Pickle surprise. (the one in the game now)"),
          ("P2", 78.05, 79.30, "Pickle surprise. (the other take)")]      # whole lines the splitter would cut in two
SKIP_DB = -52          # clips quieter than this on average are dropped (silence)
PAD = 0.05


def envelope():
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
    n = len(x) // HOP
    rms = np.sqrt((x[:n * HOP].reshape(n, HOP) ** 2).mean(1))
    sm = np.convolve(rms, np.ones(6) / 6, mode="same")           # 60 ms
    return 20 * np.log10(sm + 1e-9), len(x) / SR


def boundaries(db, words):
    """the middle of every stretch of at least DIP seconds below QUIET_DB, and between sentences"""
    cuts, i, n = [0], 0, len(db)
    for (s, e, w), nxt in zip(words, words[1:]):
        if w[-1:] in ".?!" and nxt[0] - e > 0.0:
            cuts.append(int((e + nxt[0]) / 2 * 100))
    need = int(DIP * 100)
    while i < n:
        if db[i] < QUIET_DB:
            j = i
            while j < n and db[j] < QUIET_DB:
                j += 1
            if j - i >= need:
                cuts.append((i + j) // 2)
            i = j
        else:
            i += 1
    cuts.append(n)
    return sorted(set(c for c in cuts if 0 <= c <= n))


def split_long(db, a, b):
    if (b - a) / 100.0 <= MAX_LEN:
        return [(a, b)]
    lo, hi = a + int((b - a) * 0.3), b - int((b - a) * 0.3)
    m = lo + int(np.argmin(db[lo:hi]))
    return split_long(db, a, m) + split_long(db, m, b)


def clips_from(db, words):
    cuts = boundaries(db, words)
    spans = []
    for a, b in zip(cuts, cuts[1:]):
        spans += split_long(db, a, b)
    merged = []
    for a, b in spans:                       # too-short spans join the previous one
        if merged and (b - a) / 100.0 < MIN_LEN and (b - merged[-1][0]) / 100.0 <= MAX_LEN:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    if len(merged) > 1 and (merged[0][1] - merged[0][0]) / 100.0 < MIN_LEN:
        merged[1] = (merged[0][0], merged[1][1])
        merged.pop(0)
    return [(a, b) for a, b in merged if db[a:b].mean() > SKIP_DB and (b - a) / 100.0 >= 0.25]


def transcribe():
    from faster_whisper import WhisperModel
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(AUDIO, word_timestamps=True)
    return [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or [])]


def main():
    os.makedirs(os.path.join(OUT, "clips"), exist_ok=True)
    for old in os.listdir(os.path.join(OUT, "clips")):
        os.remove(os.path.join(OUT, "clips", old))
    db, total = envelope()
    words = transcribe()
    spans = clips_from(db, words)
    clips = []

    def cut(cid, start, end, text):
        dur = end - start
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.3f" % start, "-t", "%.3f" % dur,
                        "-i", AUDIO, "-af", "afade=t=in:d=0.008,afade=t=out:st=%.3f:d=0.02" % max(0.0, dur - 0.02),
                        "-ac", "1", "-b:a", "64k", os.path.join(OUT, "clips", cid + ".mp3")], check=True)
        clips.append(dict(id=cid, start=round(start, 2), end=round(end, 2), dur=round(dur, 2), text=text))

    for cid, start, end, text in PINNED:
        cut(cid, start, end, text)
    for k, (a, b) in enumerate(spans, 1):
        start, end = max(0.0, a / 100.0 - PAD), min(total, b / 100.0 + PAD)
        cut("%03d" % k, start, end, " ".join(w for s, e, w in words if start <= (s + e) / 2 <= end))
    with open(os.path.join(OUT, "clips.json"), "w") as f:
        json.dump(clips, f, indent=1)
    page = open(os.path.join(HERE, "pickle_sound_vote.template.html"), encoding="utf-8").read()
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page.replace("/*CLIPS*/[]", json.dumps(clips)))
    print("%d clips (%.1f s of %.1f s) in %s" % (len(clips), sum(c["dur"] for c in clips), total, OUT))


main()
