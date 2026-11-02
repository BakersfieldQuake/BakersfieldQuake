"""Builds cleaned, presence-boosted 22050 Hz mono 16-bit Quake `.wav` voice clips for Larry
(the WEW CANNON / Wheelman projectile) from `G:\\Downloads\\Telegram Desktop\\ChatExport_2026-11-02\\files`:

  1. Explosion shouts (`sound/wcannon/wc_lboom1.wav` .. `wc_lboom8.wav`):
     Played in `WC_Boom` when Larry crashes and explodes into flying wheels, bars, and gibs.
  2. Post-crash crazed runner lines (`sound/wcannon/wc_lrun01.wav` .. `wc_lrun12.wav`):
     Played in `WC_DancerThink` while crazed Larry (`progs/wheelman_dance.spr32`) sprints,
     bounces off walls, and cycles through all 8 wild 360-degree animations.
"""
import os
import sys
import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import build_wcannon_sounds as B

SRC_DIR = r"G:\Downloads\Telegram Desktop\ChatExport_2026-11-02\files"
OUT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "sound", "wcannon"))
SR = B.SR
n_of = B.n_of

# (out_name, source_mp3, max_speech_sec, add_slapback_echo)
BOOM_SPECS = [
    ("wc_lboom1", "it won't boot.mp3",                  1.6, False),
    ("wc_lboom2", "oh windows me.mp3",                  1.9, False),
    ("wc_lboom3", "should i reformat.mp3",              2.1, False),
    ("wc_lboom4", "it feels so good wew.mp3",           2.6, False),
    ("wc_lboom5", "ilovethatecho.mp3",                  1.9, True),
    ("wc_lboom6", "who are youuuuuuu.mp3",              2.6, True),
    ("wc_lboom7", "Larry_Oh wow.mp3",                   2.2, False),
    ("wc_lboom8", "you're so good quad good.mp3",       2.8, False),
]

RUN_SPECS = [
    ("wc_lrun01", "wewwewwew.mp3",                              2.3),
    ("wc_lrun02", "Larry_I can bounce around for you.mp3",      2.6),
    ("wc_lrun03", "Larry_I can wobble for you.mp3",             2.5),
    ("wc_lrun04", "i don't use windows 97.mp3",                 2.1),
    ("wc_lrun05", "i'm having a problem with my computer.mp3",  2.3),
    ("wc_lrun06", "thats double good.mp3",                      1.8),
    ("wc_lrun07", "youredoublegood.mp3",                        2.5),
    ("wc_lrun08", "are you my daddy.mp3",                       2.2),
    ("wc_lrun09", "gowewd.mp3",                                 2.1),
    ("wc_lrun10", "howdoyoukeythat.mp3",                       1.5),
    ("wc_lrun11", "johnnnny.mp3",                               1.4),
    ("wc_lrun12", "oh i love it.mp3",                           1.7),
]


def trim_both_ends(x, thr=0.055):
    """Strips leading AND trailing dead air / phone-line hum so every clip starts & ends tight."""
    a = np.abs(x)
    peak = a.max()
    if peak < 1e-6:
        return x
    idx = np.nonzero(a > thr * peak)[0]
    if not len(idx):
        return x
    i0 = max(0, int(idx[0]) - n_of(0.018))
    i1 = min(len(x), int(idx[-1]) + n_of(0.045))
    return x[i0:i1]


def clean_larry_voice(x, max_sec):
    """Band-limits phone hum, boosts 1.8-4.0 kHz vocal articulation so Larry cuts cleanly over Quake explosions."""
    x = x - np.mean(x)
    x = B.hp(x, 150)
    x = B.lp(x, 7800)
    x = trim_both_ends(x, thr=0.06)
    x = x[:n_of(max_sec)]
    # Presence lift + soft saturation compressor so quiet syllables stay loud in 3D spatial audio
    x = x + 0.65 * B.bp(x, 1750, 4100)
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    k = 2.4 * rms
    x = np.tanh(x / k) * k
    x = B.fade(x, 0.004, 0.030)
    return B.norm(x, 0.92)


def build_boom_clip(voice, use_echo=False):
    """Layers shouted Larry line right on top of a punchy low-end detonation thump + optional canyon slapback."""
    tail = 0.42 if use_echo else 0.22
    dur = len(voice) / SR + tail
    out = np.zeros(n_of(dur), dtype=np.float64)
    # Tight sub-bass impact punch (`weapons/r_exp3.wav` already provides the wide noise explosion on CHAN_WEAPON!)
    B.place(out, B.thump(145, 34, 0.48, 0.13, 0.28), 0.0, 0.55)
    B.place(out, voice, 0.015, 1.05)
    if use_echo:
        B.place(out, B.bp(voice, 350, 3400), 0.165, 0.38)
        B.place(out, B.bp(voice, 350, 2800), 0.320, 0.18)
    else:
        B.place(out, B.bp(voice, 380, 3200), 0.115, 0.22)
    out = B.fade(out, 0.003, 0.055)
    return B.norm(out, 0.94)


def save_wav(path, y):
    pcm = np.clip(np.round(y * 32767.0), -32768, 32767).astype("<i2")
    wavfile.write(path, SR, pcm)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Building Larry explosion & crazed-runner sounds into {OUT_DIR} ...")

    for out_nm, mp3_nm, max_s, echo in BOOM_SPECS:
        src_p = os.path.join(SRC_DIR, mp3_nm)
        raw = B.ff_load(src_p)
        v = clean_larry_voice(raw, max_s)
        y = build_boom_clip(v, use_echo=echo)
        dst_p = os.path.join(OUT_DIR, out_nm + ".wav")
        save_wav(dst_p, y)
        print(f"  [BOOM] {out_nm}.wav  ({len(y)/SR:4.2f}s) <- {mp3_nm}")

    for out_nm, mp3_nm, max_s in RUN_SPECS:
        src_p = os.path.join(SRC_DIR, mp3_nm)
        raw = B.ff_load(src_p)
        y = clean_larry_voice(raw, max_s)
        dst_p = os.path.join(OUT_DIR, out_nm + ".wav")
        save_wav(dst_p, y)
        print(f"  [RUN ] {out_nm}.wav  ({len(y)/SR:4.2f}s) <- {mp3_nm}")

    print("ALL 20 LARRY PROJECTILE SOUNDS BUILT SUCCESSFULLY!")


if __name__ == "__main__":
    main()
