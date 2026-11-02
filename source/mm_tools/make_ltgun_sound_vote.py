"""The laptop gun's sound-vote page: source/ltgun_sound_vote/index.html (+ clips/*.wav, clips.json).
Two kinds of clip: pieces of the "Canis Lupus" audio (D:\\Local\\Video\\canisdur.wmv, cut at its quiet dips; C0 is the whole thing, what
flies with the head now) and sounds made here for each job (typing, launch, shock zap, head lands), several takes each, the one in the
game now included. Open index.html in a browser, play, press the job a clip should do, then Download or Copy the votes.
python make_ltgun_sound_vote.py        (needs ffmpeg on PATH and numpy; run it without -I)"""
import json
import math
import os
import shutil
import subprocess
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.abspath(os.path.join(HERE, "..", "ltgun_sound_vote"))
CLIPS_DIR = os.path.join(OUT, "clips")
CANIS = r"D:\Local\Video\canisdur.wmv"
SR = 22050
HOP = SR // 100
QUIET_DB = -34
DIP = 0.07
MIN_LEN = 0.45
MAX_LEN = 2.6
rng = np.random.RandomState(11)


def write_wav(path, x):
    x = np.asarray(x, dtype=np.float64)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak * 0.85
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32000).astype("<i2").tobytes())


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(t / max(attack, 1e-4), 1) * np.exp(-t / decay)


def tone(freq, dur, decay=None, harmonics=(1.0,)):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = sum(h * np.sin(2 * math.pi * freq * (i + 1) * t) for i, h in enumerate(harmonics))
    return x * env(n, 0.003, decay or dur / 3)


def place(buf, x, at):
    i = int(at * SR)
    m = min(len(x), len(buf) - i)
    if m > 0:
        buf[i:i + m] += x[:m]


# ----------------------------------------------------------------------------- made sounds

def clicks(dur, gap, pitch, decay, thump=False, bell=False):
    out = np.zeros(int(SR * dur))
    t = 0.0
    while t < dur - 0.06:
        m = int(SR * 0.04)
        f = rng.uniform(*pitch)
        c = rng.randn(m) * env(m, 0.0005, decay) + 0.6 * np.sin(2 * math.pi * f * np.arange(m) / SR) * env(m, 0.0005, decay * 1.5)
        place(out, c * rng.uniform(0.5, 1.0), t)
        t += rng.uniform(*gap)
    if thump:
        place(out, tone(110, 0.12, 0.04) * 1.2, dur - 0.15)
    if bell:
        place(out, tone(2200, 0.5, 0.15, (1, 0.4, 0.2)) * 0.5, dur - 0.5)
    return out


def modem_screech():
    n = int(SR * 0.55)
    tt = np.arange(n) / SR
    f = 1200 + 1100 * np.sin(2 * math.pi * 6 * tt) + 900 * tt
    ph = 2 * math.pi * np.cumsum(f) / SR
    sig = np.sin(ph) * 0.5 + np.sign(np.sin(ph * 0.5)) * 0.15
    whoosh = rng.randn(n) * np.clip((tt - 0.3) / 0.25, 0, 1) * np.exp(-(tt - 0.3).clip(0) * 4) * 0.5
    return sig * np.minimum(tt / 0.02, 1) * np.exp(-tt * 1.5) + whoosh


def handshake():
    out = np.zeros(int(SR * 0.9))
    at = 0.0
    for f, d in ((1300, 0.09), (2100, 0.09), (1100, 0.11), (2400, 0.08), (1700, 0.12), (980, 0.1)):
        place(out, tone(f, d, d * 3), at)
        at += d
    n = int(SR * 0.3)
    place(out, rng.randn(n) * np.exp(-np.arange(n) / (SR * 0.08)) * 0.5, at)
    return out


def ping():
    out = np.zeros(int(SR * 0.9))
    base = tone(1250, 0.5, 0.12, (1, 0.3))
    for k, g in enumerate((1.0, 0.5, 0.25)):
        place(out, base * g, 0.12 * k)
    n = int(SR * 0.2)
    place(out, rng.randn(n) * np.exp(-np.arange(n) / (SR * 0.05)) * 0.3, 0.0)
    return out


def upload():
    n = int(SR * 0.6)
    tt = np.arange(n) / SR
    f = 400 + 2600 * (tt / 0.6) ** 1.6
    ph = 2 * math.pi * np.cumsum(f) / SR
    x = np.sin(ph) * (0.6 + 0.4 * np.sin(2 * math.pi * 30 * tt)) * np.minimum(tt / 0.01, 1) * np.minimum((0.6 - tt) / 0.05, 1)
    place(x, tone(3200, 0.04, 0.01), 0.56)
    return x


def crackle(dur, power):
    n = int(SR * dur)
    tt = np.arange(n) / SR
    sig = np.zeros(n)
    for _ in range(int(40 * dur * power)):
        i = rng.randint(0, n - 200)
        m = rng.randint(40, 200)
        sig[i:i + m] += rng.randn(m) * np.exp(-np.arange(m) / (m / 4.0)) * rng.uniform(0.3, 1.0)
    sig += np.sin(2 * math.pi * 120 * tt) * 0.25 * np.exp(-tt * 6) + np.sin(2 * math.pi * 3200 * tt) * 0.1 * np.exp(-tt * 12)
    return sig * np.minimum(tt / 0.003, 1) * np.exp(-tt * (3.0 / dur))


def arc_buzz():
    n = int(SR * 0.55)
    tt = np.arange(n) / SR
    saw = 2 * ((100 * tt) % 1) - 1
    x = (saw * 0.6 + rng.randn(n) * 0.35 * (0.5 + 0.5 * np.sin(2 * math.pi * 23 * tt))) * np.exp(-tt * 4.5)
    return x * np.minimum(tt / 0.004, 1)


def bug_zapper():
    n = int(SR * 0.25)
    tt = np.arange(n) / SR
    hp = np.diff(rng.randn(n + 1))
    return (hp * 0.8 + np.sin(2 * math.pi * 4200 * tt) * 0.5) * np.exp(-tt * 16) * np.minimum(tt / 0.001, 1)


def static_burst():
    n = int(SR * 0.5)
    tt = np.arange(n) / SR
    x = rng.randn(n) * np.sin(np.pi * tt / 0.5) ** 2 * 0.6
    for _ in range(25):
        i = rng.randint(0, n - 120)
        x[i:i + 80] += rng.randn(80) * 1.2 * np.exp(-np.arange(80) / 20.0)
    return x


def digital_crash():
    n = int(SR * 0.6)
    tt = np.arange(n) / SR
    x = np.repeat(rng.randn(n // 12 + 1), 12)[:n] * np.exp(-tt * 5)          # bit-crushed noise
    f = 900 * np.exp(-tt * 5)
    x += np.sin(2 * math.pi * np.cumsum(f) / SR) * 0.8 * np.exp(-tt * 4)
    return x * np.minimum(tt / 0.002, 1)


def power_surge():
    n = int(SR * 0.75)
    tt = np.arange(n) / SR
    boom = np.sin(2 * math.pi * (80 - 45 * tt) * tt) * np.exp(-tt * 6)
    whine = np.sin(2 * math.pi * np.cumsum(2400 * np.exp(-tt * 3)) / SR) * 0.3 * np.exp(-tt * 3.5)
    return boom * 1.2 + whine + crackle(0.75, 1.2)[:n] * 0.5


def error_ding():
    out = np.zeros(int(SR * 0.9))
    place(out, tone(880, 0.5, 0.12, (1, 0.5, 0.25)), 0.0)
    place(out, tone(660, 0.6, 0.15, (1, 0.5, 0.25)), 0.22)
    return out


def made_sounds():
    """(slot, label, samples or the path of the file in the game now)"""
    cur = os.path.join(MOD, "sound", "ltgun")
    return [
        ("type", "Mechanical keys (in the game now)", os.path.join(cur, "type.wav")),
        ("type", "Soft laptop keys, lower and quieter", clicks(0.8, (0.05, 0.1), (300, 700), 0.008)),
        ("type", "Rapid hacker typing, ends with a hard enter", clicks(0.8, (0.025, 0.05), (900, 2200), 0.004, thump=True)),
        ("type", "Old typewriter, ends with a bell", clicks(1.0, (0.07, 0.13), (600, 1400), 0.007, bell=True)),
        ("send", "Modem screech into a whoosh (in the game now)", os.path.join(cur, "send.wav")),
        ("send", "Dial-up handshake beeps", handshake()),
        ("send", "Network ping, with echoes", ping()),
        ("send", "Upload: a rising chirp", upload()),
        ("zap", "Electric crackle (in the game now)", os.path.join(cur, "zap.wav")),
        ("zap", "Arc buzz, a mains-hum sawtooth", arc_buzz()),
        ("zap", "Bug zapper: one sharp zzt", bug_zapper()),
        ("zap", "Static burst that swells", static_burst()),
        ("hit", "Crackle and boom (in the game now)", os.path.join(cur, "hit.wav")),
        ("hit", "Digital crash: crushed noise and a falling beep", digital_crash()),
        ("hit", "Power surge: deep boom, whine and sparks", power_surge()),
        ("hit", "Error ding-dong, two bell tones", error_ding()),
    ]


# ----------------------------------------------------------------------------- the Canis Lupus pieces

def canis_pieces(tmp):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", CANIS, "-vn", "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", tmp], check=True)
    with wave.open(tmp) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    n = len(x) // HOP
    rms = np.sqrt((x[:n * HOP].reshape(n, HOP) ** 2).mean(1))
    db = 20 * np.log10(np.convolve(rms, np.ones(5) / 5, mode="same") + 1e-9)
    cuts, i = [0], 0
    while i < n:
        if db[i] < QUIET_DB:
            j = i
            while j < n and db[j] < QUIET_DB:
                j += 1
            if j - i >= int(DIP * 100):
                cuts.append((i + j) // 2)
            i = j
        else:
            i += 1
    cuts.append(n)
    cuts = sorted(set(cuts))
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        if segs and (b - a) < MIN_LEN * 100:
            segs[-1] = (segs[-1][0], b)
        else:
            segs.append((a, b))
    if len(segs) > 1 and (segs[0][1] - segs[0][0]) < MIN_LEN * 100:
        segs[1] = (segs[0][0], segs[1][1])
        segs.pop(0)
    out = []
    for a, b in segs:
        while b - a > MAX_LEN * 100:                  # long ones are cut at their quietest point
            lo, hi = a + int(MIN_LEN * 100), a + int(MAX_LEN * 100)
            k = lo + int(np.argmin(db[lo:hi]))
            out.append((a, k))
            a = k
        out.append((a, b))
    return [(a / 100.0, b / 100.0) for a, b in out], len(x) / SR


def main():
    if os.path.isdir(CLIPS_DIR):
        shutil.rmtree(CLIPS_DIR)
    os.makedirs(CLIPS_DIR)
    clips = []
    tmp = os.path.join(OUT, "_canis.wav")
    pieces, total = canis_pieces(tmp)
    # C0: the whole clip, as it plays with the head now
    shutil.copyfile(tmp, os.path.join(CLIPS_DIR, "C0.wav"))      # the whole original: times on this page are times in the original clip
    clips.append(dict(id="C0", file="C0.wav", kind="canis", start=0.0, end=round(total, 2), dur=round(total, 2),
                      text="The whole Canis Lupus clip (the game plays it from 0.85 s, after the hiss at the start)"))
    for i, (a, b) in enumerate(pieces, 1):
        cid = "C%02d" % i
        a0, b0 = max(0.0, a - 0.03), min(total, b + 0.03)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.2f" % a0, "-t", "%.2f" % (b0 - a0), "-i", tmp, "-af",
                        "afade=t=in:st=0:d=0.02,afade=t=out:st=%.2f:d=0.04" % max(0, b0 - a0 - 0.04), "-ac", "1", "-ar", str(SR),
                        os.path.join(CLIPS_DIR, cid + ".wav")], check=True)
        clips.append(dict(id=cid, file=cid + ".wav", kind="canis", start=round(a, 2), end=round(b, 2), dur=round(b - a, 2),
                          text="Piece %d of the Canis Lupus clip" % i))
    os.remove(tmp)
    names = {"type": "Typing", "send": "Launch", "zap": "Shock zap", "hit": "Head lands"}
    count = {}
    for slot, label, src in made_sounds():
        count[slot] = count.get(slot, 0) + 1
        mid = "%s%d" % (slot[0].upper() + slot[1:].lower(), count[slot])
        dst = os.path.join(CLIPS_DIR, mid + ".wav")
        if isinstance(src, str):
            shutil.copyfile(src, dst)
        else:
            write_wav(dst, src)
        with wave.open(dst) as w:
            dur = w.getnframes() / float(w.getframerate())
        clips.append(dict(id=mid, file=mid + ".wav", kind="made", start=0, end=0, dur=round(dur, 2), text=label, forslot=names[slot]))
    json.dump(clips, open(os.path.join(OUT, "clips.json"), "w"), indent=1)
    # the waveform of the whole clip (C0), 50 bars a second, for the page's cutter
    with wave.open(os.path.join(CLIPS_DIR, "C0.wav")) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    bar = SR // 50
    nb = len(x) // bar
    peaks = np.abs(x[:nb * bar]).reshape(nb, bar).max(1)
    peaks = np.round((peaks / max(float(peaks.max()), 1e-6)) ** 0.7, 3).tolist()
    page = open(os.path.join(HERE, "ltgun_sound_vote.template.html"), encoding="utf-8").read()
    page = page.replace("/*CLIPS*/[]", json.dumps(clips)).replace("/*PEAKS*/[]", json.dumps(peaks)).replace("/*TOTAL*/0", repr(round(total, 2)))
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
    print("wrote %d clips (%d from Canis Lupus, %d made) to %s" % (len(clips), sum(c["kind"] == "canis" for c in clips),
                                                               sum(c["kind"] == "made" for c in clips), OUT))


if __name__ == "__main__":
    main()
