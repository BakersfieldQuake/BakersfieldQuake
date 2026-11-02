"""Wheelman Cannon sound vote, Larry edition: every funny line from D:\\Local\\Audio\\Larry Clips\\johny_clips_pack, cleaned up and
processed into the four cannon sounds (charge, shoot, scream, boom), then a fresh vote page.

  charge  the line pitches up through the 1.5 s charge, tremolo speeding up, a rising turbine underneath
  shoot   a cannon thump with the line punched out of it (a bit lower, saturated)
  scream  the line as a fast fly-by: pitch glides up and back down (doppler), vibrato, grit
  boom    the line shouted, then a big explosion

Cleanup of every line: phone-line band (140 Hz-7.5 kHz), leading silence cut, presence lift, soft compression, normalised.
Left out on purpose: the slur clips, explicit sex clips and the "cut them off / make them bleed" series (name filter below).

Writes clips to source/wcannon_sound_vote/clips/<slot>_L<nn>.wav (the ids start with the slot, so apply_wcannon_votes.py works),
merges clips.json (the old synth clips stay on disk) and rebuilds wheelman_cannon_sound_vote.html with only the Larry set.
Does not touch sound/wcannon (the game keeps the sounds you already picked).
python3.13 build_wcannon_larry.py        (needs numpy, scipy, ffmpeg; run it without -I)"""
import glob
import json
import os
import re
import sys

import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_wcannon_sounds as B

PACK = r"D:\Local\Audio\Larry Clips\johny_clips_pack"
SR = B.SR
n_of = B.n_of

# a filename containing any of these is left out
SKIP = ("nigg", "n_word", "condom", "butt_sex", "squirt", "peepee", "ass", "bitch", "balls", "fuck", "shit", "nuts", "bleed",
        "scissors", "bleach", "address", "pop_", "until_they", "smash", "pound", "penis", "cock", "dick", "pussy", "table_up")


def clean(x):
    """phone-line audio -> a voice that sits in the game: band-limit, lift the presence, squash, normalise"""
    x = x - np.mean(x)
    x = B.hp(x, 140)
    x = B.lp(x, 7500)
    x = x + 0.5 * B.bp(x, 1800, 3800)
    k = 3.0 * np.sqrt(np.mean(x ** 2)) + 1e-9
    x = np.tanh(x / k) * k
    return B.norm(x, 0.85)


def lead_trim(x, thr=0.07):
    a = np.abs(x)
    idx = np.nonzero(a > thr * a.max())[0]
    if not len(idx):
        return x
    return x[max(0, idx[0] - n_of(0.02)):]


def seg(x, dur):
    """the first dur seconds of speech (padded with silence if the line is shorter)"""
    x = lead_trim(x)[:n_of(dur)]
    if len(x) < n_of(dur):
        x = np.concatenate([x, np.zeros(n_of(dur) - len(x))])
    return x


def warp(x, rates, d):
    """read x with a time-varying playback rate (so pitch follows it) for d seconds; silence once x runs out"""
    n = n_of(d)
    pos = np.cumsum(np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(rates)), rates))
    out = np.interp(pos, np.arange(len(x)), x, right=0.0)
    return out


def charge(x):
    d = 1.5
    src = seg(x, 2.4)
    v = warp(src, [0.92, 1.0, 1.15, 1.4], d)
    t = np.arange(n_of(d)) / SR
    trem_f = 5 + 17 * (t / d)                       # tremolo speeds up as the charge builds
    v = v * (0.65 + 0.35 * np.sin(2 * np.pi * np.cumsum(trem_f) / SR))
    under = B.charge_turbine()[:n_of(d)]
    out = np.zeros(n_of(d))
    out[:len(v)] += v
    out[:len(under)] += 0.5 * under
    out *= np.minimum(1, t / 0.04)
    return out


def shoot(x):
    d = 1.15
    v = warp(seg(x, 1.4), [0.88, 0.88], d)
    k = 2.0 * np.sqrt(np.mean(v ** 2)) + 1e-9
    v = np.tanh(v / k) * k
    out = np.zeros(n_of(d))
    B.place(out, B.thump(150, 38, 0.7, 0.14, 0.4), 0.0, 1.15)
    B.place(out, v, 0.04, 0.9)
    return out


def scream(x):
    d = 1.6
    src = seg(x, 2.2)
    t = np.arange(n_of(d)) / SR
    glide = 1.0 + 0.4 * np.sin(np.pi * np.clip(t / d, 0, 1))          # up and back down: a fast fly-by
    vib = 0.05 * np.sin(2 * np.pi * 7.0 * t)
    rate = glide + vib
    pos = np.cumsum(rate)
    v = np.interp(pos, np.arange(len(src)), src, right=0.0)
    k = 1.6 * np.sqrt(np.mean(v ** 2)) + 1e-9
    v = np.tanh(v / k) * k                                            # grit
    amp = 0.45 + 0.55 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6   # louder as he passes
    return v * amp


def boom(x):
    d = 3.0
    out = np.zeros(n_of(d))
    v = warp(seg(x, 1.4), [0.9, 0.9], 1.2)
    B.place(out, v, 0.0, 0.85)
    B.place(out, B.boom_core(2.2, 1.0), 0.55, 1.0)
    return out


RECIPES = {"charge": charge, "shoot": shoot, "scream": scream, "boom": boom}


def label_of(stem, manifest):
    t = manifest.get(stem)
    if t:
        t = re.sub(r"\s+", " ", t).strip()
        return t if len(t) <= 70 else t[:67] + "..."
    return stem.replace("johny_", "").replace("_", " ")


def main():
    manifest = {}
    mf = os.path.join(PACK, "johny_clips_manifest.tsv")
    for line in open(mf, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 4:
            manifest[os.path.splitext(os.path.basename(p[2]))[0]] = p[3]
    files = sorted(glob.glob(os.path.join(PACK, "*.mp3")))
    keep, left_out = [], []
    for f in files:
        stem = os.path.splitext(os.path.basename(f))[0]
        (left_out if any(s in stem for s in SKIP) else keep).append((stem, f))
    print("keeping %d lines, leaving out %d" % (len(keep), len(left_out)))
    for s, _ in left_out:
        print("   out:", s)

    os.makedirs(B.CLIP_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(B.CLIP_DIR, "*_L*.wav")):
        os.remove(old)
    old_meta = [m for m in json.load(open(os.path.join(B.VOTE_DIR, "clips.json"))) if "_L" not in m["id"]]
    meta = []
    n = 0
    for stem, f in keep:
        n += 1
        voice = clean(B.ff_load(f))
        lab = label_of(stem, manifest)
        for slot, fn in RECIPES.items():
            y = fn(voice)
            y = B.norm(y)
            idx = np.nonzero(np.abs(y) > 0.004)[0]
            if len(idx):
                y = y[:min(len(y), idx[-1] + n_of(0.05))]
            y = B.fade(y, 0.002, 0.03 if slot != "boom" else 0.08)[:n_of(B.LIMIT[slot])]
            cid = "%s_L%02d" % (slot, n)
            wavfile.write(os.path.join(B.CLIP_DIR, cid + ".wav"), SR, np.clip(np.round(y * 32767), -32768, 32767).astype("<i2"))
            meta.append({"id": cid, "slot": slot, "label": lab, "source": "larry", "dur": round(len(y) / SR, 2), "default": False})
    with open(os.path.join(B.VOTE_DIR, "clips.json"), "w") as fh:
        json.dump(old_meta + meta, fh, indent=1)
    B.build_page(meta)
    print("%d Larry clips (%d lines x 4 sounds)" % (len(meta), len(keep)))


if __name__ == "__main__":
    main()
