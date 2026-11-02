"""Build the Mystery Box sound-vote page.

Run (numpy + scipy live in the user site, so NOT with -I):
  python make_mbox_sound_vote.py

Writes
  source/mbox_sound_vote/clips/<id>.wav   16-bit mono 22050 Hz, one per candidate
  source/mbox_sound_vote/clips.json       id, file, job, name, description, source, origin, duration, peak, rms ...
  mystery_box_sound_vote.html             single self-contained page (clips embedded as base64 WAV), built from
                                          mbox_sound_vote_template.html; one sound pair per monster (7 monsters)

Candidates come from three places:
  "in the game now"  existing sounds under BakersfieldQuake/sound/
  "stock Quake"      id1/pak0.pak and quake15/q15.pk3
  "made here"        synthesised below with numpy/scipy (drive loops are periodic by construction, so they loop
                     with no click; loops taken from recordings are made seamless with an equal-power crossfade
                     of the tail into the head)
Everything is peak-normalised to at most 0.85 (and RMS-capped so the vote is not decided by loudness).
"""
import base64
import json
import os
import struct
import subprocess
import sys
import wave
import zipfile

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
MM = os.path.dirname(HERE)
MOD = os.path.dirname(os.path.dirname(MM))          # .../BakersfieldQuake
COMBAT = os.path.dirname(MOD)                       # .../Combat
SND = os.path.join(MOD, "sound")
OUTDIR = os.path.join(MOD, "source", "mbox_sound_vote")
CLIPS = os.path.join(OUTDIR, "clips")
PAGE = os.path.join(MOD, "mystery_box_sound_vote.html")
THUMBS = os.path.join(MM, "out", "mystery_box", "vote_thumbs")     # tone-matched by make_vote_thumbs.py / normalise_vote_thumbs.py
TEMPLATE_FILE = os.path.join(HERE, "mbox_sound_vote_template.html")
PAK = os.path.join(COMBAT, "id1", "pak0.pak")
PK3 = os.path.join(COMBAT, "quake15", "q15.pk3")

SR = 22050
PEAK = 0.85
rng = np.random.default_rng(20261031)


# ----------------------------------------------------------------------------- source readers
_pak = None
_pk3 = None


def stock_bytes(name):
    """Raw bytes of sound/<name> from pak0.pak, else q15.pk3."""
    global _pak, _pk3
    if _pak is None:
        f = open(PAK, "rb")
        _, off, ln = struct.unpack("<4sii", f.read(12))
        f.seek(off)
        ents = {}
        for _i in range(ln // 64):
            nm, o, l = struct.unpack("<56sii", f.read(64))
            ents[nm.split(b"\0")[0].decode()] = (o, l)
        _pak = (f, ents)
        _pk3 = zipfile.ZipFile(PK3)
    f, ents = _pak
    key = "sound/" + name
    if key in ents:
        o, l = ents[key]
        f.seek(o)
        return f.read(l), "id1/pak0.pak"
    return _pk3.read(key), "quake15/q15.pk3"


def decode(b):
    """Any audio bytes -> float32 mono at SR via ffmpeg."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                       input=b, capture_output=True, check=True)
    return np.frombuffer(p.stdout, "<f4").astype(np.float64)


def mod_wav(rel):
    with open(os.path.join(SND, rel), "rb") as fh:
        return decode(fh.read())


def stock_wav(name):
    return decode(stock_bytes(name)[0])


# ----------------------------------------------------------------------------- dsp helpers
def tt(d):
    return np.arange(int(round(d * SR))) / SR


def sos(kind, fc, order=2):
    return signal.butter(order, fc, btype=kind, fs=SR, output="sos")


def lp(x, fc, order=2):
    return signal.sosfilt(sos("lowpass", min(fc, SR * 0.49), order), x)


def hp(x, fc, order=2):
    return signal.sosfilt(sos("highpass", fc, order), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(sos("bandpass", [lo, min(hi, SR * 0.49)], order), x)


def white(n):
    return rng.standard_normal(n)


def pnoise(D, lo, hi, tilt=0.0):
    """Exactly periodic band noise (random phases on bins that are multiples of 1/D), unit RMS."""
    N = int(round(D * SR))
    f = np.fft.rfftfreq(N, 1 / SR)
    amp = np.zeros(len(f))
    band = (f >= lo) & (f <= hi)
    amp[band] = (np.maximum(f[band], 1.0) / max(lo, 1.0)) ** tilt
    amp *= np.clip((f - lo) / (0.2 * lo + 20), 0, 1) * np.clip((hi - f) / (0.1 * hi + 20), 0, 1)
    spec = amp * np.exp(1j * rng.uniform(0, 2 * np.pi, len(f)))
    spec[0] = 0
    x = np.fft.irfft(spec, N)
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-12)


def pphase(freq):
    """Phase (radians) of a periodic frequency curve, nudged so the total is a whole number of cycles."""
    ph = np.concatenate([[0.0], np.cumsum(freq) / SR])
    total = ph[-1]
    k = max(1.0, round(total))
    return 2 * np.pi * ph[:-1] * (k / total)


def phase(freq):
    return 2 * np.pi * np.cumsum(freq) / SR


def edec(n, tau, t0=0.0, attack=0.001):
    t = np.arange(n) / SR - t0
    e = np.exp(-np.maximum(t, 0) / tau) * (t >= 0)
    if attack:
        e *= np.minimum(1, np.maximum(t, 0) / attack)
    return e


def place(buf, sig, t0, circ=False, gain=1.0):
    i = int(round(t0 * SR))
    n = len(buf)
    if circ:
        np.add.at(buf, (np.arange(len(sig)) + i) % n, sig * gain)
    else:
        m = min(len(sig), n - i)
        if m > 0:
            buf[i:i + m] += sig[:m] * gain


def ping(freqs, amps, tau, dur=None, taus=None):
    dur = dur or min(0.6, tau * 7)
    t = tt(dur)
    y = np.zeros(len(t))
    for k, (f, a) in enumerate(zip(freqs, amps)):
        tk = taus[k] if taus else tau
        y += a * np.sin(2 * np.pi * f * t) * np.exp(-t / tk)
    return y * np.minimum(1, t / 0.0008)


def nburst(dur, tau, lo=None, hi=None, order=2):
    n = int(dur * SR)
    x = white(n)
    if lo and hi:
        x = bp(x, lo, hi, order)
    elif hi:
        x = lp(x, hi, order)
    elif lo:
        x = hp(x, lo, order)
    return x * edec(n, tau, attack=0.0004)


def thump(f0=120, f1=50, tau=0.08, dur=0.4, drop=0.03):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t / drop)
    return np.sin(phase(f)) * np.exp(-t / tau) * np.minimum(1, t / 0.001)


def boom(dur, sub0, sub1, tau_sub, noise_tau, gain_noise=1.0, rumble=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = sub1 + (sub0 - sub1) * np.exp(-t / 0.12)
    sub = np.sin(phase(f)) * np.exp(-t / tau_sub) * np.minimum(1, t / 0.002)
    # noise whose low-pass cutoff sweeps down (bright crack -> dull rumble)
    nz = white(n)
    out = np.zeros(n)
    blocks = 10
    seg = n // blocks
    cuts = np.geomspace(7000, 220, blocks)
    for b in range(blocks):
        s = slice(b * seg, n if b == blocks - 1 else (b + 1) * seg)
        out[s] = lp(nz, cuts[b], 2)[s]
    out = out * np.exp(-t / noise_tau) * np.minimum(1, t / 0.0006) * gain_noise
    rum = lp(white(n), 140, 2) * np.exp(-t / (tau_sub * 1.3)) * rumble * 3
    return sub * 1.4 + out * 0.8 + rum


def bell(f, dur=1.0, tau=0.4, partials=((1, 1.0, 1.0), (2.0, 0.45, 0.55), (3.0, 0.25, 0.35), (4.2, 0.12, 0.2), (5.4, 0.07, 0.12))):
    t = tt(dur)
    y = np.zeros(len(t))
    for ratio, a, dk in partials:
        y += a * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / (tau * dk))
    return y * np.minimum(1, t / 0.001)


def mix(*sigs):
    n = max(len(s) for s in sigs)
    out = np.zeros(n)
    for s in sigs:
        out[:len(s)] += s
    return out


def softclip(x, k=1.0):
    return np.tanh(k * x) / np.tanh(k)


# ----------------------------------------------------------------------------- seamless loops from recordings
def make_seamless(x, xf):
    """x has len = loop + xf. The tail (the xf after the loop point) is blended into the head so out[0] continues out[-1]."""
    n = int(xf * SR)
    dur = len(x) - n
    w = np.linspace(0, 1, n, endpoint=False)
    out = x[:dur].copy()
    out[:n] = x[:n] * np.sin(w * np.pi / 2) + x[dur:dur + n] * np.cos(w * np.pi / 2)
    return out


def loop_from(a, start, dur, xf):
    s = int(start * SR)
    seg = a[s:s + int((dur + xf) * SR)]
    return make_seamless(seg, xf)


def tile_loop(a, reps, xf):
    n = int(xf * SR)
    w = np.linspace(0, 1, n, endpoint=False)
    out = a
    for _ in range(reps - 1):
        out = np.concatenate([out[:-n], out[-n:] * np.cos(w * np.pi / 2) + a[:n] * np.sin(w * np.pi / 2), a[n:]])
    return make_seamless(out, xf)


# ----------------------------------------------------------------------------- DRIVE: synthesised (all exactly periodic, D seconds)
D = 2.0


def drv_trike_squeak():
    t = tt(D)
    rev = 3.0
    ph = 2 * np.pi * rev * t
    g1 = np.clip(np.sin(ph + 0.3), 0, None) ** 0.6
    f1 = 2250 + 260 * np.sin(ph + 0.3) + 90 * np.sin(2 * np.pi * 7 * t)
    p1 = pphase(f1)
    sq1 = (np.sin(p1) + 0.5 * np.sin(2 * p1 + 0.5) + 0.22 * np.sin(3 * p1)) * g1
    g2 = np.clip(-np.sin(ph + 0.3), 0, None) ** 1.5
    f2 = 1620 + 160 * np.sin(2 * ph) + 40 * np.sin(2 * np.pi * 11 * t)
    sq2 = np.sin(pphase(f2)) * g2
    rub = lp(pnoise(D, 60, 900), 500) * (0.5 + 0.5 * np.cos(ph)) ** 2
    ticks = np.zeros(len(t))
    for k in range(int(rev * D)):
        place(ticks, thump(150, 70, 0.04, 0.2, 0.02), k / rev + 0.02, circ=True)
    return 0.5 * sq1 + 0.3 * sq2 + 0.55 * rub + 0.3 * ticks


def drv_tile_skate():
    t = tt(D)
    rum = pnoise(D, 120, 2800, tilt=-0.5) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.5 * t))
    low = pnoise(D, 40, 220) * 0.7
    joints = np.zeros(len(t))
    for k in range(8):
        g = 1.0 if k % 2 == 0 else 0.75
        place(joints, mix(thump(110, 55, 0.035, 0.25, 0.02), 0.5 * nburst(0.04, 0.006, lo=1200)), k * 0.25, circ=True, gain=g)
        place(joints, 0.45 * nburst(0.06, 0.012, lo=300, hi=1500), k * 0.25 + 0.05, circ=True)
    return 0.55 * rum + 0.35 * low + 0.9 * joints


def drv_cart_rattle():
    t = tt(D)
    base = pnoise(D, 700, 5500)
    am = 0.55 + 0.25 * np.sin(2 * np.pi * 6 * t) + 0.2 * np.sin(2 * np.pi * 9.5 * t + 1)
    low = pnoise(D, 80, 450) * (0.6 + 0.4 * np.sin(2 * np.pi * 6 * t + 0.7))
    cl = np.zeros(len(t))
    for _ in range(18):
        place(cl, ping([2100, 3300, 5200], [1, 0.6, 0.4], 0.012, 0.1), rng.uniform(0, D), circ=True, gain=rng.uniform(0.3, 1.0))
    return 0.35 * base * am + 0.4 * low + 0.6 * cl


def cyc(f, Dd):
    """Nearest modulation frequency that fits a whole number of cycles in Dd seconds."""
    return max(1, round(f * Dd)) / Dd


def drv_kart_buzz(D=D, base=135):
    t = tt(D)
    f0 = base * (1 + 0.12 * np.sin(2 * np.pi * cyc(2, D) * t) + 0.04 * np.sin(2 * np.pi * cyc(5, D) * t + 1) + 0.02 * np.sin(2 * np.pi * cyc(13, D) * t))
    ph = pphase(f0)
    x = np.zeros(len(t))
    for k in range(1, 36):
        fk = k * f0
        mask = np.clip((5200 - fk) / 900, 0, 1)
        form = 1 + 2.2 * np.exp(-((fk - 900) / 330) ** 2) + 1.2 * np.exp(-((fk - 2300) / 600) ** 2)
        x += np.sin(k * ph + 0.3 * k) / k ** 0.9 * mask * form
    am = 0.78 + 0.22 * np.cos(ph)
    exhaust = pnoise(D, 300, 3200) * 0.12
    return softclip((x * 0.9 + exhaust) * am, 1.6)


def snip(g=1.0):
    a = nburst(0.03, 0.007, lo=3500) * 0.9
    b = nburst(0.03, 0.006, lo=4500) * 0.8
    ring = ping([4300, 6100, 7800], [1, 0.7, 0.5], 0.012, 0.08) * 0.7
    out = np.zeros(int(0.12 * SR))
    place(out, mix(a, ring), 0.0)
    place(out, mix(b, 0.7 * ring), 0.032)           # blades open, then close
    return out * g


def drv_scissor_snip():
    n = int(D * SR)
    buf = np.zeros(n)
    for g in range(4):
        for j, off in enumerate((0.0, 0.11, 0.22)):
            place(buf, snip(1.0 if j < 2 else 0.85), g * 0.5 + off, circ=True)
    for k in range(8):
        place(buf, mix(0.5 * nburst(0.12, 0.035, lo=60, hi=320), 0.25 * thump(140, 70, 0.04, 0.2)), k * 0.25, circ=True)
    return buf


def drv_boing_hop():
    n = int(D * SR)
    buf = np.zeros(n)
    for k in range(4):
        t = tt(0.46)
        base = 240 if k % 2 == 0 else 285
        f = base * (1 + 1.2 * np.exp(-t / 0.06)) * (1 + 0.07 * np.sin(2 * np.pi * 30 * t) * np.exp(-t / 0.2))
        p = phase(f)
        env = np.exp(-t / 0.17) * np.minimum(1, t / 0.002)
        b = (np.sin(p) + 0.35 * np.sin(2 * p) + 0.12 * np.sin(3 * p)) * env
        place(buf, b, k * 0.5, circ=True, gain=0.75)
        place(buf, thump(130, 60, 0.05, 0.2, 0.02), k * 0.5, circ=True, gain=0.55)
    return buf


def drv_tippy_tap():
    n = int(D * SR)
    buf = np.zeros(n)
    pat = [1.0, 0.55, 0.9, 0.5]
    for k in range(16):
        tm = k * 0.125 + rng.uniform(-0.006, 0.006)
        fr = 2400 if k % 2 == 0 else 1800
        g = pat[k % 4]
        tk = mix(nburst(0.03, 0.006, lo=1500) * 0.7, ping([fr, fr * 1.6], [0.7, 0.35], 0.01, 0.06))
        place(buf, tk, tm, circ=True, gain=g)
        place(buf, ping([320, 560], [0.5, 0.2], 0.02, 0.1), tm, circ=True, gain=g * 0.5)
    return buf


def drv_unicycle_whir():
    t = tt(D)
    f = 210 * (1 + 0.18 * np.sin(2 * np.pi * 1.0 * t) + 0.05 * np.sin(2 * np.pi * 3 * t + 2))
    ph = pphase(f)
    x = (np.sin(ph) + 0.4 * np.sin(2 * ph + 1) + 0.2 * np.sin(3 * ph)) * (0.65 + 0.35 * np.sin(2 * np.pi * 1.0 * t + 1.1))
    whir = pnoise(D, 900, 3200) * (0.4 + 0.4 * np.sin(2 * np.pi * 5 * t)) * 0.35
    ticks = np.zeros(len(t))
    for k in range(10):
        place(ticks, ping([1500, 2700], [1, 0.4], 0.008, 0.05), k * 0.2, circ=True, gain=0.35)
    return 0.55 * x + whir + ticks


def drv_icecream():
    n = int(D * SR)
    notes = [784.0, 659.3, 880.0, 784.0, 1046.5, 880.0, 784.0, 659.3]     # original little tune, 8 x 0.25 s
    jingle = np.zeros(n)
    for i, fnote in enumerate(notes):
        t = tt(0.9)
        f = fnote * (1 + 0.012 * np.sin(2 * np.pi * 6 * t))               # warbly tape
        p = phase(f)
        b = (np.sin(p) + 0.5 * np.sin(2.0 * p) * np.exp(-t / 0.2) + 0.3 * np.sin(3.01 * p) * np.exp(-t / 0.12) + 0.12 * np.sin(5.4 * p) * np.exp(-t / 0.06))
        b *= np.exp(-t / 0.3) * np.minimum(1, t / 0.002)
        place(jingle, b, i * 0.25, circ=True)
    jingle = softclip(bp(jingle, 380, 4200) * 1.4, 1.3)                  # cheap truck speaker
    t = tt(D)
    f = 70 + 4 * np.sin(2 * np.pi * 2 * t)
    ph = pphase(f)
    eng = lp(sum(np.sin(k * ph + k) / k for k in range(1, 9)) * (0.7 + 0.3 * np.sin(2 * np.pi * 8 * t)), 600)
    return 0.8 * jingle + 0.28 * eng


def drv_kazoo_engine():
    t = tt(D)
    f0 = 150 * (1 + 0.15 * np.sin(2 * np.pi * 1 * t) + 0.05 * np.sin(2 * np.pi * 3 * t + 1))
    ph = pphase(f0)
    x = np.zeros(len(t))
    for k in range(1, 28):
        fk = k * f0
        mask = np.clip((5500 - fk) / 900, 0, 1)
        res = 1 + 4 * np.exp(-((fk - 1200) / 450) ** 2) + 2.5 * np.exp(-((fk - 2800) / 600) ** 2)
        x += np.sin(k * ph + 0.5 * k) / k ** 0.8 * mask * res
    x = softclip(x * 0.35, 2.2)                                             # membrane buzz
    putt = 0.62 + 0.38 * np.sqrt(0.5 + 0.5 * np.sin(2 * np.pi * 12 * t))
    nasal = pnoise(D, 1500, 4500) * 0.12
    return (x + nasal) * putt


# ----------------------------------------------------------------------------- EXPLODE: synthesised one-shots
def exp_confetti_horn():
    buf = np.zeros(int(1.9 * SR))
    place(buf, mix(nburst(0.1, 0.014, hi=3500) * 1.0, thump(150, 60, 0.05, 0.3, 0.03) * 0.9), 0.0)
    for _ in range(110):
        tm = 0.03 + min(rng.exponential(0.32), 1.0)
        a = 0.4 * np.exp(-tm / 0.5) * rng.uniform(0.3, 1)
        place(buf, mix(ping([rng.uniform(3000, 9500)], [1], rng.uniform(0.004, 0.012), 0.06), 0.3 * nburst(0.01, 0.003, lo=3000)), tm, gain=a)
    # party horn: short "pah" then long unfurling "paaaaah"
    def horn(f0, f1, dur):
        t = tt(dur)
        f = f0 + (f1 - f0) * (1 - np.exp(-t / 0.12)) + 6 * np.sin(2 * np.pi * 9 * t)
        p = phase(f)
        x = sum(np.sin(k * p) / k for k in range(1, 16, 2)) + 0.35 * np.sin(2 * p)
        x = lp(softclip(x * 0.8, 1.5), 3400)
        env = np.minimum(1, t / 0.012) * np.minimum(1, (dur - t) / 0.06)
        return (x + 0.25 * white(len(t)) * np.exp(-t / 0.03)) * env
    place(buf, horn(430, 470, 0.16), 0.5, gain=0.5)
    place(buf, horn(470, 560, 0.85), 0.7, gain=0.55)
    return buf


def exp_balloon_pop():
    buf = np.zeros(int(0.8 * SR))
    place(buf, white(int(0.012 * SR)) * edec(int(0.012 * SR), 0.0025, attack=0.0002) * 1.2, 0.0)
    place(buf, ping([220, 430], [0.9, 0.3], 0.035, 0.3), 0.0, gain=0.8)
    place(buf, ping([900, 1450, 2300], [0.6, 0.45, 0.3], 0.04, 0.3), 0.0, gain=0.45)
    place(buf, nburst(0.04, 0.012, lo=600, hi=3000) * 0.4, 0.015)
    for tm in (0.07, 0.11, 0.17, 0.26):
        place(buf, nburst(0.05, 0.01, lo=500, hi=2600), tm, gain=0.18 * np.exp(-tm / 0.2))
    t = tt(0.45)
    flap = lp(white(len(t)), 2400) * edec(len(t), 0.07) * (0.6 + 0.4 * np.sin(2 * np.pi * 34 * t))
    place(buf, flap, 0.05, gain=0.22)
    return buf


def exp_boing_bang():
    buf = np.zeros(int(2.1 * SR))
    t = tt(0.95)
    f = 140 * (1 + 1.8 * (1 - np.exp(-t / 0.35))) * (1 + 0.1 * np.sin(2 * np.pi * 16 * t))
    p = phase(f)
    env = np.minimum(1, t / 0.02) * (0.5 + 0.5 * t / 0.95) * np.minimum(1, (0.95 - t) / 0.03)
    place(buf, (np.sin(p) + 0.4 * np.sin(2 * p) + 0.15 * np.sin(3 * p)) * env, 0.0, gain=0.55)
    place(buf, boom(1.1, 110, 42, 0.28, 0.17), 0.98, gain=0.8)
    return buf


def brass(f, gate, fc):
    p = phase(f)
    x = np.zeros(len(f))
    for k in range(1, 22):
        w = np.exp(-((k * f) / fc) ** 2)
        x += np.sin(k * p) / k ** 0.8 * w
    return x * gate


def exp_sad_trombone():
    buf = np.zeros(int(3.0 * SR))
    place(buf, mix(nburst(0.08, 0.012, hi=2500) * 0.9, thump(140, 70, 0.05, 0.3, 0.03) * 0.8), 0.0, gain=0.8)
    notes = [(233.1, 0.40, 0.0), (220.0, 0.40, 0.0), (207.7, 0.40, 0.0), (196.0, 1.25, -10.0)]
    tm = 0.3
    for fn, dur, slide in notes:
        t = tt(dur)
        f = fn + slide * (t / dur) ** 2 * 1.0
        if dur > 1:
            f = f * (1 + 0.018 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.5))
        fc = 500 + 1400 * np.sin(np.pi * np.minimum(1, t / (0.34 if dur < 1 else 0.7))) ** 1.2   # the wah
        g = np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / (0.05 if dur < 1 else 0.25)) * (1 if dur < 1 else (0.85 + 0.15 * np.exp(-t / 0.3)))
        place(buf, brass(f, g, fc), tm, gain=0.35)
        tm += dur + 0.02
    return buf


def exp_glass_springs():
    buf = np.zeros(int(2.0 * SR))
    place(buf, mix(nburst(0.15, 0.03, lo=1800) * 1.0, thump(180, 80, 0.04, 0.2, 0.02) * 0.4), 0.0)
    for _ in range(80):
        tm = 0.01 + min(rng.exponential(0.26), 1.45)
        f0 = rng.uniform(2500, 10000)
        place(buf, ping([f0, f0 * 2.3], [1, 0.4], rng.uniform(0.01, 0.05), 0.2), tm, gain=0.4 * np.exp(-tm / 0.55) * rng.uniform(0.3, 1))
    for i, tm in enumerate((0.12, 0.34, 0.6)):
        t = tt(0.7)
        f = 700 + 2500 * np.exp(-t / 0.12) + 400 * np.sin(2 * np.pi * 45 * t) * np.exp(-t / 0.15)
        p = phase(f)
        sp = (np.sin(p) + 0.3 * np.sin(2 * p)) * np.exp(-t / 0.2) * np.minimum(1, t / 0.002)
        place(buf, sp, tm, gain=0.34 * (0.8 ** i))
    for _ in range(14):
        place(buf, ping([rng.uniform(1500, 4000)], [1], 0.01, 0.05), rng.uniform(0.9, 1.8), gain=rng.uniform(0.04, 0.1))
    return buf


def exp_tada_chime():
    buf = np.zeros(int(2.4 * SR))
    place(buf, mix(thump(150, 45, 0.13, 0.6, 0.05) * 1.2, nburst(0.1, 0.02, hi=700) * 0.8), 0.0)
    arp = [523.3, 659.3, 784.0, 1046.5, 1318.5, 1568.0]
    for i, fa in enumerate(arp):
        tm = 0.12 + i * 0.07
        g = 0.28 + 0.05 * i
        place(buf, bell(fa, 1.2, 0.5), tm, gain=g)
        place(buf, bell(fa * 1.004, 1.2, 0.5), tm, gain=g * 0.6)
    for fa, g in ((1046.5, 0.3), (1318.5, 0.25), (1568.0, 0.25), (2093.0, 0.18)):
        place(buf, bell(fa, 1.7, 0.8), 0.58, gain=g)
    for _ in range(36):
        tm = rng.uniform(0.1, 1.6)
        place(buf, ping([rng.uniform(4000, 10000)], [1], 0.02, 0.08), tm, gain=0.12 * np.exp(-tm / 1.0))
    return buf


def exp_fart_pop():
    n = int(1.05 * SR)
    t = np.arange(n) / SR
    wob = lp(white(n), 28)
    wob = wob / (np.abs(wob).max() + 1e-9)
    f = 115 * np.exp(-1.1 * t) * (1 + 0.4 * wob)
    p = phase(f)
    saw = signal.sawtooth(p) + 0.4 * np.sign(np.sin(0.5 * p))
    x = lp(saw, 900, 3)
    x *= 0.65 + 0.35 * np.sin(2 * np.pi * 17 * t)
    x += 0.3 * bp(white(n), 200, 1500)
    env = np.minimum(1, t / 0.03) * np.where(t < 0.78, 1.0, np.exp(-(t - 0.78) / 0.05)) * np.where(t < 0.5, 1.0, 0.75)
    buf = np.zeros(int(1.1 * SR))
    place(buf, x * env, 0.06, gain=0.7)
    place(buf, mix(nburst(0.1, 0.014, hi=3000) * 0.9, thump(160, 60, 0.05, 0.3, 0.03) * 0.8), 0.0, gain=0.6)
    place(buf, mix(nburst(0.1, 0.014, hi=3500) * 0.9, thump(200, 70, 0.04, 0.3, 0.03) * 0.8), 0.9, gain=0.9)
    return buf


def exp_slide_boom():
    buf = np.zeros(int(2.7 * SR))
    t = tt(0.95)
    u = t / 0.95
    f = 250 + 2200 * (1 - u) ** 1.8
    f = f * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))
    p = phase(f)
    env = np.minimum(1, t / 0.01) * np.minimum(1, (0.95 - t) / 0.04)
    w = (np.sin(p) + 0.06 * np.sin(2 * p)) * env + 0.05 * bp(white(len(t)), 1500, 4000) * env
    place(buf, w, 0.0, gain=0.5)
    place(buf, boom(1.6, 85, 36, 0.5, 0.2), 1.12, gain=1.0)
    return buf


def exp_chicken_pop():
    buf = np.zeros(int(1.45 * SR))

    t1 = tt(0.28)
    f1 = 500 * (1500 / 500) ** (t1 / 0.28)
    p = phase(f1)
    sq1 = np.zeros(len(t1))
    for k in range(1, 14):
        fk = k * f1
        sq1 += np.sin(k * p) / k ** 0.7 * (0.3 + 2.0 * np.exp(-((fk - 1800) / 700) ** 2)) * np.clip((6000 - fk) / 800, 0, 1)
    sq1 *= np.minimum(1, t1 / 0.01) * np.minimum(1, (0.28 - t1) / 0.03)
    place(buf, sq1, 0.0, gain=0.4)
    t2 = tt(0.5)
    f2 = 1300 - 600 * (t2 / 0.5) ** 0.8
    p2 = phase(f2 * (1 + 0.06 * np.sin(2 * np.pi * 25 * t2)))
    sq2 = np.zeros(len(t2))
    for k in range(1, 14):
        fk = k * f2
        sq2 += np.sin(k * p2) / k ** 0.7 * (0.3 + 2.0 * np.exp(-((fk - 1700) / 700) ** 2)) * np.clip((6000 - fk) / 800, 0, 1)
    sq2 *= np.minimum(1, t2 / 0.02) * np.minimum(1, (0.5 - t2) / 0.05)
    place(buf, sq2, 0.34, gain=0.4)
    place(buf, mix(nburst(0.1, 0.012, hi=3500) * 1.0, thump(170, 65, 0.05, 0.3, 0.03) * 0.9), 0.95, gain=0.9)
    for tm in (1.0, 1.04, 1.1):
        place(buf, nburst(0.05, 0.01, lo=800, hi=3000), tm, gain=0.15)
    return buf


def exp_sub_boom():
    b = boom(2.7, 78, 30, 0.7, 0.28, rumble=0.5)
    b[:int(0.01 * SR)] += white(int(0.01 * SR)) * 0.8
    return softclip(b * 0.7, 1.4)


# ----------------------------------------------------------------------------- shared little helpers for the monster clips
def pshift(a, r):
    """Resample by ratio r (r>1 = higher + shorter)."""
    n = int(len(a) / r)
    return np.interp(np.arange(n) * r, np.arange(len(a)), a)


def nrm(x):
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-12)


def fit(x, n):
    out = np.zeros(n)
    m = min(n, len(x))
    out[:m] = x[:m]
    return out


def chirp(f0, f1, dur):
    t = tt(dur)
    p = phase(f0 + (f1 - f0) * (t / dur))
    return (np.sin(p) + 0.3 * np.sin(2 * p)) * np.minimum(1, t / 0.006) * np.minimum(1, (dur - t) / 0.012)


def clank(base=1.0):
    return ping([310 * base, 760 * base, 1210 * base, 1900 * base], [1, 0.7, 0.5, 0.3], 0.07, 0.5, taus=[0.18, 0.12, 0.08, 0.05])


def pop():
    return mix(nburst(0.1, 0.014, hi=3500) * 1.0, thump(150, 60, 0.05, 0.3, 0.03) * 0.9)


def funny(name):
    return mod_wav("funny/" + name)


def stepthump(buf, times, g=0.5, f0=140, f1=70):
    for tm in times:
        place(buf, mix(0.6 * nburst(0.1, 0.03, lo=100, hi=900), thump(f0, f1, 0.04, 0.2)), tm, circ=True, gain=g)


# ----------------------------------------------------------------------------- monster-specific DRIVE loops (exactly periodic)
def drv_rig_clank():
    t = tt(D)
    buf = np.zeros(len(t))
    for k in range(8):
        base = [1.0, 1.06, 0.94, 1.1][k % 4]
        place(buf, clank(base), k * 0.25, circ=True, gain=[1, 0.6, 0.8, 0.5][k % 4])
        for _ in range(4):
            place(buf, ping([rng.uniform(2000, 5200)], [1], 0.01, 0.05), k * 0.25 + rng.uniform(0.02, 0.2), circ=True, gain=rng.uniform(0.1, 0.3))
    hum = pnoise(D, 100, 700) * (0.5 + 0.5 * np.cos(2 * np.pi * 4 * t)) ** 1.5
    return 0.8 * buf + 0.35 * hum


def drv_rig_chain():
    t = tt(D)
    buf = np.zeros(len(t))
    for k in range(48):
        place(buf, mix(nburst(0.012, 0.003, lo=1200, hi=4500), ping([2400], [0.6], 0.004, 0.03)), k / 24.0, circ=True, gain=1.0 if k % 2 == 0 else 0.7)
    spokes = pnoise(D, 2000, 6000) * (0.4 + 0.4 * np.sin(2 * np.pi * 8 * t)) * 0.3
    f = 120 * (1 + 0.03 * np.sin(2 * np.pi * 3 * t))
    ph = pphase(f)
    hum = (np.sin(ph) + 0.4 * np.sin(2 * ph)) * 0.3
    return 0.7 * buf + spokes + hum


def drv_suit_tie():
    t = tt(D)
    flap = pnoise(D, 300, 2800, tilt=-0.3) * np.abs(np.sin(np.pi * 14 * t)) ** 3
    f = 90 * (1 + 0.04 * np.sin(2 * np.pi * 2 * t))
    ph = pphase(f)
    wheels = sum(np.sin(k * ph) / k for k in range(1, 7))
    clunk = np.zeros(len(t))
    for k in range(4):
        place(clunk, mix(thump(200, 90, 0.05, 0.25, 0.02), ping([700, 1500], [0.5, 0.3], 0.03, 0.15)), k * 0.5, circ=True)
    return 0.5 * flap + 0.35 * wheels + 0.5 * clunk


def drv_squat_stomp():
    t = tt(D)
    buf = np.zeros(len(t))
    for k in range(6):
        place(buf, mix(thump(75, 40, 0.09, 0.4, 0.04), nburst(0.15, 0.05, hi=700) * 0.6), k / 3.0, circ=True)
    for k in range(24):
        place(buf, nburst(0.01, 0.003, lo=1500, hi=4000), k / 12.0, circ=True, gain=0.25)
    wheeze = pnoise(D, 300, 1000) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)) ** 2
    return buf + 0.3 * wheeze


def drv_wheelman_wobble():
    t = tt(D)
    rum = pnoise(D, 40, 300, tilt=-0.3) * (0.6 + 0.4 * np.cos(2 * np.pi * 2.5 * t))
    f = 58 * (1 + 0.15 * np.sin(2 * np.pi * 1 * t) + 0.05 * np.sin(2 * np.pi * 2.5 * t + 1))
    ph = pphase(f)
    tone = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)) * (0.6 + 0.4 * np.sin(2 * np.pi * t + 0.5))
    slap = np.zeros(len(t))
    for k in range(5):
        place(slap, mix(thump(85, 45, 0.1, 0.4, 0.04), nburst(0.12, 0.04, lo=100, hi=900) * 0.5), k / 2.5, circ=True)
    flutter = pnoise(D, 300, 1200) * (0.3 + 0.3 * np.sin(2 * np.pi * 5 * t))
    return 0.6 * rum + 0.5 * tone + 0.7 * slap + 0.25 * flutter


def drv_wheelman_slap():
    t = tt(D)
    buf = np.zeros(len(t))
    for k in range(10):
        place(buf, mix(nburst(0.16, 0.05, lo=120, hi=1400), thump(70, 40, 0.08, 0.3, 0.03) * 0.8), k * 0.2, circ=True, gain=1.0 if k % 2 == 0 else 0.7)
    tread = pnoise(D, 1500, 5500) * (0.35 + 0.25 * np.sin(2 * np.pi * 5 * t))
    return buf + 0.4 * tread


def drv_wheelman_creak():
    t = tt(D)
    f = 900 + 300 * np.sin(2 * np.pi * 1.25 * t) + 80 * np.sin(2 * np.pi * 4 * t)
    ph = pphase(f)
    gate = np.clip(np.sin(2 * np.pi * 1.25 * t + 1), 0, None) ** 0.8
    sq = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph)) * gate
    rub = pnoise(D, 200, 1800) * 0.4 * (0.5 + 0.5 * gate)
    th = np.zeros(len(t))
    for k in range(5):
        place(th, thump(90, 50, 0.08, 0.3, 0.03), k / 2.5, circ=True, gain=0.8)
    return 0.45 * sq + rub + th


def drv_roll_whirr():
    t = tt(D)
    f = 520 * (1 + 0.08 * np.sin(2 * np.pi * 3 * t) + 0.03 * np.sin(2 * np.pi * 7 * t))
    ph = pphase(f)
    w = sum(np.sin(k * ph) / k for k in range(1, 5))
    nz = pnoise(D, 1000, 4000) * (0.4 + 0.3 * np.sin(2 * np.pi * 10 * t))
    ch = np.zeros(len(t))
    for tm in (0.2, 0.65, 1.1, 1.6):
        place(ch, chirp(2000, 3300, 0.07), tm, circ=True, gain=0.5)
    return 0.45 * w + 0.4 * nz + ch


def drv_roll_gravel():
    t = tt(D)
    base = pnoise(D, 500, 6000, tilt=-0.3) * (0.6 + 0.3 * np.sin(2 * np.pi * 7 * t))
    low = pnoise(D, 60, 300) * 0.6
    cr = np.zeros(len(t))
    for _ in range(80):
        place(cr, nburst(0.006, 0.002, lo=1500), rng.uniform(0, D), circ=True, gain=rng.uniform(0.2, 1.0))
    return 0.5 * base + 0.4 * low + 0.35 * cr


def drv_roll_swoop():
    t = tt(D)
    u = (t * 1.0) % 1.0
    f = 760 - 380 * u
    ph = pphase(f)
    amp = np.sin(np.pi * u) ** 2
    x = sum(np.sin(k * ph) / k for k in range(1, 6)) * amp
    return 0.6 * x + 0.25 * pnoise(D, 800, 3000) * amp


def drv_kart_giggle():
    Dg = 1.69
    n = int(round(Dg * SR))
    kart = nrm(drv_kart_buzz(Dg, 150))
    g = fit(loop_from(funny("giggles.wav"), 0, Dg, 0.15), n)
    return 0.5 * kart + nrm(g) * 1.0


def drv_kart_drift():
    t = tt(D)
    base = nrm(drv_kart_buzz(D, 120))
    f = 2200 + 300 * np.sin(2 * np.pi * 1.5 * t) + 120 * np.sin(2 * np.pi * 9 * t)
    ph = pphase(f)
    gate = np.clip(np.sin(2 * np.pi * 1 * t + 0.5), 0, None) ** 0.5
    sq = (np.sin(ph) + 0.4 * np.sin(2 * ph)) * gate
    hiss = pnoise(D, 2500, 6500) * gate * 0.3
    return 0.6 * base + 0.8 * nrm(sq) * 0.5 + 0.25 * hiss


def drv_kart_bell():
    trike = nrm(drv_trike_squeak())
    kart = nrm(drv_kart_buzz())
    bells = np.zeros(len(trike))
    for tm in (0.0, 0.67, 1.33):
        place(bells, bell(2400, 0.5, 0.15, partials=((1, 1, 1), (2.4, 0.5, 0.6), (3.7, 0.3, 0.3))), tm, circ=True, gain=0.5)
    return 0.55 * trike + 0.4 * kart + 1.2 * bells


def drv_kyle_snip():
    buf = np.zeros(int(D * SR))
    for g in range(5):
        for off in (0.0, 0.08, 0.16, 0.24):
            place(buf, snip(0.9), g * 0.4 + off, circ=True)
    stepthump(buf, [k * 0.2 for k in range(10)], g=0.7)
    return buf


def drv_kyle_pant():
    t = tt(D)
    env = (0.5 - 0.5 * np.cos(2 * np.pi * 3 * t)) ** 1.5
    breath = pnoise(D, 400, 3500, tilt=-0.4) * env
    buf = np.zeros(len(t))
    stepthump(buf, [k * 0.2 for k in range(10)], g=0.5)
    for tm in (0.5, 1.3):
        tv = tt(0.14)
        p = phase(420 + 140 * (tv / 0.14))
        eep = lp(signal.sawtooth(p), 2500) * np.minimum(1, tv / 0.01) * np.minimum(1, (0.14 - tv) / 0.03)
        place(buf, eep, tm, circ=True, gain=0.5)
    return 0.5 * breath + buf


def drv_kyle_shing():
    t = tt(D)
    scrape = pnoise(D, 2000, 7000) * (0.3 + 0.5 * np.abs(np.sin(2 * np.pi * 2.5 * t)) ** 2)
    buf = np.zeros(len(t))
    for k in range(5):
        place(buf, ping([5200, 6600, 3900], [1, 0.6, 0.5], 0.08, 0.4), k * 0.4, circ=True, gain=0.5)
    stepthump(buf, [k * 0.4 + 0.2 for k in range(5)], g=0.6, f0=120, f1=60)
    return 0.35 * scrape + buf


def drv_rob_wewe():
    return tile_loop(funny("wewe.wav"), 2, 0.1)


def drv_rob_gg():
    gg = funny("gg.wav")
    buf = np.zeros(int(D * SR))
    for k in range(3):
        place(buf, gg, k * 0.667, circ=True, gain=1 - 0.1 * k)
    stepthump(buf, [k / 3.0 for k in range(6)], g=0.3)
    return buf


def drv_rob_heh():
    heh = funny("heh.wav")
    buf = np.zeros(int(D * SR))
    for k in range(8):
        place(buf, pshift(heh, [1.0, 1.15, 0.9, 1.05][k % 4]), k * 0.25, circ=True, gain=1.0 if k % 2 == 0 else 0.8)
    stepthump(buf, [k * 0.25 for k in range(8)], g=0.35)
    return buf


# ----------------------------------------------------------------------------- monster-specific EXPLODE one-shots
def exp_rig_crash():
    buf = np.zeros(int(1.7 * SR))
    place(buf, boom(0.8, 120, 50, 0.15, 0.08), 0, gain=0.6)
    place(buf, mod_wav("vehicles/clang1.wav"), 0.02, gain=0.7)
    for i, (tm, b) in enumerate([(0.18, 1.06), (0.33, 0.93), (0.47, 1.12), (0.58, 1.0), (0.66, 0.97)]):
        place(buf, clank(b), tm, gain=0.55 * 0.75 ** i)
    for _ in range(25):
        tm = rng.uniform(0.1, 1.2)
        place(buf, ping([rng.uniform(1500, 5000)], [1], 0.01, 0.05), tm, gain=0.12 * np.exp(-tm / 0.6))
    return buf


def exp_rig_sproing():
    buf = np.zeros(int(1.8 * SR))
    for i, tm in enumerate((0.0, 0.2, 0.42, 0.7)):
        t = tt(0.6)
        f = 600 + 2200 * np.exp(-t / 0.1) + 350 * np.sin(2 * np.pi * 40 * t) * np.exp(-t / 0.12)
        p = phase(f)
        place(buf, (np.sin(p) + 0.3 * np.sin(2 * p)) * np.exp(-t / 0.18) * np.minimum(1, t / 0.002), tm, gain=0.4 * 0.85 ** i)
    place(buf, clank(1.0), 0.9, gain=0.7)
    place(buf, pop(), 1.05, gain=0.9)
    return buf


def exp_suit_papers():
    buf = np.zeros(int(1.6 * SR))
    place(buf, pop(), 0.0)
    t = tt(1.0)
    fl = bp(white(len(t)), 2000, 6500) * edec(len(t), 0.3, attack=0.01) * (0.5 + 0.5 * np.sin(2 * np.pi * 25 * t))
    place(buf, fl, 0.05, gain=0.5)
    for tm in (0.12, 0.2, 0.33):
        place(buf, nburst(0.06, 0.015, lo=1200, hi=5000), tm, gain=0.4)
    place(buf, bell(1760, 0.9, 0.4), 0.5, gain=0.35)
    return buf


def exp_squat_thud():
    buf = np.zeros(int(1.7 * SR))
    place(buf, boom(1.0, 90, 38, 0.25, 0.12), 0.0, gain=0.8)
    place(buf, nburst(0.1, 0.03, lo=200, hi=1500), 0.02, gain=0.6)
    place(buf, mod_wav("vehicles/clang2.wav"), 0.3, gain=0.5)
    place(buf, thump(100, 50, 0.08, 0.3, 0.03), 0.5, gain=0.5)
    place(buf, chirp(900, 1400, 0.12), 0.75, gain=0.3)
    return buf


def exp_wheel_blowout():
    buf = np.zeros(int(2.0 * SR))
    place(buf, mix(nburst(0.15, 0.02, hi=5000), thump(120, 55, 0.06, 0.4, 0.03)), 0.0)
    t = tt(1.4)
    hiss = hp(white(len(t)), 1800) * edec(len(t), 0.4, attack=0.01) * (0.7 + 0.3 * np.sin(2 * np.pi * 18 * t))
    place(buf, hiss, 0.03, gain=0.35)
    tm, gap, g = 0.2, 0.12, 0.6
    while tm < 1.7:
        place(buf, thump(90, 50, 0.06, 0.3, 0.03), tm, gain=g)
        tm += gap
        gap *= 1.18
        g *= 0.85
    return buf


def exp_wheel_wobble():
    buf = np.zeros(int(2.0 * SR))
    place(buf, pop(), 0.0)
    tm, gap, g = 0.18, 0.13, 0.4
    while gap > 0.006:
        place(buf, ping([900, 1700, 2700], [1, 0.5, 0.3], 0.015, 0.08), tm, gain=g)
        tm += gap
        gap *= 0.89
        g = min(0.9, g * 1.04)
    place(buf, bp(white(int(0.3 * SR)), 800, 2500) * edec(int(0.3 * SR), 0.1), tm, gain=0.4)
    place(buf, thump(110, 60, 0.06, 0.3, 0.03), tm + 0.1, gain=0.7)
    return buf


def exp_wheel_squeal_boom():
    buf = np.zeros(int(2.0 * SR))
    t = tt(0.6)
    sq = chirp(2600, 1500, 0.6) * 0.6 + 0.3 * bp(white(len(t)), 1800, 4500)
    place(buf, sq * np.minimum(1, t / 0.02) * np.minimum(1, (0.6 - t) / 0.05), 0.0, gain=0.5)
    place(buf, boom(1.4, 95, 38, 0.4, 0.17), 0.62)
    return buf


def exp_roll_skid():
    buf = np.zeros(int(1.9 * SR))
    t = tt(0.6)
    sk = bp(white(len(t)), 1800, 4500) * np.minimum(1, t / 0.03) * np.minimum(1, (0.6 - t) / 0.05)
    tone = np.sin(phase(2000 + 200 * np.sin(2 * np.pi * 14 * t))) * np.minimum(1, t / 0.03) * np.minimum(1, (0.6 - t) / 0.05)
    place(buf, 0.5 * sk + 0.25 * tone, 0.0)
    place(buf, boom(1.3, 100, 40, 0.3, 0.15), 0.55)
    return buf


def exp_roll_spinout():
    buf = np.zeros(int(1.5 * SR))
    t = tt(0.85)
    f = 150 + 1500 * (t / 0.85) ** 2
    p = phase(f)
    w = sum(np.sin(k * p) / k for k in range(1, 6)) * np.minimum(1, t / 0.02) * np.minimum(1, (0.85 - t) / 0.02)
    place(buf, w, 0.0, gain=0.4)
    place(buf, pop(), 0.87)
    for tm in (1.0, 1.06, 1.15):
        place(buf, ping([900, 1700], [1, 0.5], 0.015, 0.08), tm, gain=0.3)
    return buf


def exp_roll_chirp():
    buf = np.zeros(int(1.5 * SR))
    for tm in (0.0, 0.22, 0.42):
        place(buf, chirp(1800, 3000, 0.12), tm, gain=0.5)
    place(buf, pop(), 0.65)
    place(buf, nburst(0.2, 0.05, lo=1000, hi=4000), 0.7, gain=0.3)
    return buf


def exp_kart_giggle():
    buf = np.zeros(int(2.0 * SR))
    place(buf, mix(pop(), boom(0.5, 110, 50, 0.1, 0.06) * 0.7), 0.0)
    g = funny("giggles.wav")[:int(1.65 * SR)].copy()
    fo = int(0.1 * SR)
    g[-fo:] *= np.linspace(1, 0, fo)
    place(buf, g, 0.18, gain=0.8)
    return buf


def exp_kart_honk():
    buf = np.zeros(int(1.8 * SR))
    h = mod_wav("vehicles/horn.wav")
    place(buf, h, 0.0, gain=0.8)
    place(buf, pshift(h, 1.12), 0.55, gain=0.8)
    place(buf, pop(), 1.15)
    place(buf, nburst(0.3, 0.08, lo=2500, hi=8000), 1.17, gain=0.3)
    return buf


def exp_kart_bell():
    buf = np.zeros(int(1.9 * SR))
    for tm in (0.0, 0.3, 0.5, 0.65, 0.75, 0.82):
        place(buf, bell(2400, 0.5, 0.12, partials=((1, 1, 1), (2.4, 0.5, 0.6), (3.7, 0.3, 0.3))), tm, gain=0.5)
    place(buf, pop(), 0.92)
    for _ in range(50):
        tm = 0.95 + min(rng.exponential(0.25), 0.9)
        place(buf, ping([rng.uniform(3000, 9500)], [1], 0.008, 0.05), tm, gain=0.2 * rng.uniform(0.3, 1))
    return buf


def exp_kyle_snip_pop():
    buf = np.zeros(int(1.5 * SR))
    for tm in (0.0, 0.14, 0.28):
        place(buf, snip(1.0), tm)
    place(buf, pop(), 0.55)
    place(buf, nburst(0.2, 0.05, lo=1500, hi=6000), 0.58, gain=0.3)
    return buf


def exp_kyle_scream():
    buf = np.zeros(int(1.6 * SR))
    place(buf, mod_wav("grenade/boom_03_scream_launch.wav"), 0.0, gain=0.9)
    place(buf, snip(1.0), 0.9, gain=0.8)
    place(buf, snip(1.0), 1.04, gain=0.8)
    return buf


def exp_kyle_clash():
    buf = np.zeros(int(1.8 * SR))
    place(buf, ping([3800, 5100, 6900, 8800], [1, 0.8, 0.6, 0.4], 0.35, 1.2), 0.0, gain=0.45)
    place(buf, boom(1.2, 100, 45, 0.3, 0.15), 0.1, gain=0.9)
    return buf


def exp_rob_wewe():
    buf = np.zeros(int(2.1 * SR))
    place(buf, funny("wewe.wav"), 0.0, gain=0.8)
    place(buf, boom(0.95, 100, 42, 0.25, 0.12), 1.12)
    return buf


def exp_rob_gg():
    buf = np.zeros(int(2.3 * SR))
    place(buf, funny("gg.wav"), 0.0, gain=0.8)
    place(buf, boom(1.5, 80, 34, 0.5, 0.2, rumble=0.5), 0.8)
    return buf


def exp_rob_heh_fart():
    buf = np.zeros(int(1.9 * SR))
    place(buf, funny("heh.wav"), 0.0, gain=0.8)
    place(buf, funny("fart1.wav"), 0.35, gain=0.9)
    place(buf, pop(), 1.25)
    return buf


# ----------------------------------------------------------------------------- candidate tables
TAG_NOW, TAG_Q, TAG_MADE = "in the game now", "stock Quake", "made here"
SYN = "synth"


def D_mod(rel, start=None, dur=None, xf=0.1, reps=None):
    def f():
        a = mod_wav(rel)
        if reps:
            return tile_loop(a, reps, xf)
        return loop_from(a, start, dur, xf)
    return f


def D_stock(name, start, dur, xf=0.12):
    return lambda: loop_from(stock_wav(name), start, dur, xf)


def drive_hop():
    a = stock_wav("player/land.wav")
    buf = np.zeros(int(1.8 * SR))
    for k, g in enumerate((1.0, 0.8, 1.0, 0.8)):
        place(buf, a, k * 0.45, circ=True, gain=g)
    return buf


def M(rel):
    return lambda: mod_wav(rel)


def S(name):
    return lambda: stock_wav(name)


SUIT, SQUAT, WHEEL, JESS, KYLE, ROB, ROLL = "suit_rider", "squat_rider", "wheelman", "jesskart", "kyle_scissor", "friend_rob", "rolling_wheelman"
RIDERS = [SUIT, SQUAT]

# (id, name, description, source tag, origin, builder[, [monsters it was made for]])
DRIVE = [
    ("drv_trike_squeak", "Squeaky Trike Wheel", "One dry axle, three turns a second, begging for oil.", TAG_MADE, SYN, drv_trike_squeak),
    ("drv_tile_skate", "Skateboard on Tile", "Low rumble with a clack at every grout line.", TAG_MADE, SYN, drv_tile_skate),
    ("drv_cart_rattle", "Shopping Cart Special", "The one wobbly wheel in the whole parking lot: rattle and clatter.", TAG_MADE, SYN, drv_cart_rattle),
    ("drv_kart_buzz", "Go-Kart Two-Stroke", "Angry lawnmower buzz, pitch wobbling like a nervous driver.", TAG_MADE, SYN, drv_kart_buzz),
    ("drv_scissor_snip", "Running With Scissors", "Snip-snip-snip on every stride. Safety first.", TAG_MADE, SYN, drv_scissor_snip),
    ("drv_boing_hop", "Boing Boing", "Spring-legged hop rhythm, four boings per loop.", TAG_MADE, SYN, drv_boing_hop),
    ("drv_tippy_tap", "Tippy-Tap Feet", "Tiny quick feet on a hard floor.", TAG_MADE, SYN, drv_tippy_tap),
    ("drv_unicycle_whir", "Wobbly Unicycle", "Bearing whir that sways up and down, spokes ticking.", TAG_MADE, SYN, drv_unicycle_whir),
    ("drv_icecream", "Ice-Cream Truck", "Warbly music-box jingle (original tune) over a rumbly idle.", TAG_MADE, SYN, drv_icecream),
    ("drv_kazoo_engine", "Kazoo Engine", "Somebody is doing the engine noise with a kazoo.", TAG_MADE, SYN, drv_kazoo_engine),
    ("drv_idle_coupe", "Coupe Idle", "The coupe's idle loop from the car map, made seamless.", TAG_NOW, "sound/vehicles/idle_coupe.wav", D_mod("vehicles/idle_coupe.wav", reps=2, xf=0.08)),
    ("drv_mm_drive", "Mega Man Drive", "The Mega Man contraption's driving rumble (2 s slice).", TAG_NOW, "sound/megaman/mm_drive.wav", D_mod("megaman/mm_drive.wav", start=0.4, dur=2.0, xf=0.15)),
    ("drv_engine_grain", "Engine Grain Buzz", "The car engine grain, repeated into a fast buzz.", TAG_NOW, "sound/vehicles/engine_grain.wav", D_mod("vehicles/engine_grain.wav", reps=6, xf=0.04)),
    ("drv_megamotor", "Mega Motor", "The Mega Man motor revved in a loop.", TAG_NOW, "sound/weapons/megamotor.wav", D_mod("weapons/megamotor.wav", reps=4, xf=0.05)),
    ("drv_q_train", "Quake Platform Rumble", "The moving-platform rumble from stock Quake.", TAG_Q, "plats/train1.wav", D_stock("plats/train1.wav", 0.05, 1.75, 0.12)),
    ("drv_q_buzz", "Quake Buzz", "Buzzy electric drone from the Quake 1.5 sounds.", TAG_Q, "buzz/buzz1.wav", D_stock("buzz/buzz1.wav", 0.05, 1.5, 0.12)),
    ("drv_q_drag", "Ogre Drag", "Something heavy being dragged along, from an Ogre.", TAG_Q, "ogre/ogdrag.wav", lambda: tile_loop(stock_wav("ogre/ogdrag.wav"), 2, 0.15)),
    ("drv_q_hop", "Thud-Thud Hop", "The player landing thump, repeated into a hop rhythm.", TAG_Q, "player/land.wav", drive_hop),
    # --- made for specific monsters
    ("drv_rig_clank", "Rig Clank-and-Rattle", "Loose tubes clanking on every wheel turn, bolts rattling.", TAG_MADE, SYN, drv_rig_clank, RIDERS),
    ("drv_rig_chain", "Chain and Spokes", "Ticking chain, whirring spokes, low rig hum.", TAG_MADE, SYN, drv_rig_chain, RIDERS),
    ("drv_suit_tie", "Flapping Tie", "Necktie flapping in the wind over a wheel hum, briefcase clunking.", TAG_MADE, SYN, drv_suit_tie, [SUIT]),
    ("drv_squat_stomp", "Squat Pedal Chug", "Heavy pedal strokes, wheezing, chain ticking.", TAG_MADE, SYN, drv_squat_stomp, [SQUAT]),
    ("drv_wheelman_wobble", "Big Wheel Wobble", "Heavy single-wheel wobble-rumble, one slap per turn.", TAG_MADE, SYN, drv_wheelman_wobble, [WHEEL]),
    ("drv_wheelman_slap", "Tire Slap Whump", "A fat tire whumping the road five times a second.", TAG_MADE, SYN, drv_wheelman_slap, [WHEEL]),
    ("drv_wheelman_creak", "Creaky Big Wheel", "Axle creak gliding up and down with deep thumps.", TAG_MADE, SYN, drv_wheelman_creak, [WHEEL]),
    ("drv_roll_whirr", "Rolling Whirr + Chirps", "Fast rolling whirr with little tire squeal chirps.", TAG_MADE, SYN, drv_roll_whirr, [ROLL]),
    ("drv_roll_gravel", "Gravel Roller", "Rolling over a gravel parking lot, crunchy.", TAG_MADE, SYN, drv_roll_gravel, [ROLL]),
    ("drv_roll_swoop", "Doppler Roller", "Zooms past and away, twice a loop.", TAG_MADE, SYN, drv_roll_swoop, [ROLL]),
    ("drv_kart_giggle", "Giggly Kart", "Kart buzz with the giggling from the game laid over it.", TAG_MADE, "synth + sound/funny/giggles.wav", drv_kart_giggle, [JESS]),
    ("drv_kart_drift", "Drifting Kart", "Kart buzz with a tire squeal on every drift.", TAG_MADE, SYN, drv_kart_drift, [JESS]),
    ("drv_kart_bell", "Trike Bell Kart", "Squeaky trike, kart buzz and a ding-ding bell.", TAG_MADE, SYN, drv_kart_bell, [JESS]),
    ("drv_kyle_snip", "Kyle's Sprint Snips", "Fast scissor snips, panicked footsteps.", TAG_MADE, SYN, drv_kyle_snip, [KYLE]),
    ("drv_kyle_pant", "Panting Sprint", "Out-of-breath panting, footsteps and a couple of squeaky eeps.", TAG_MADE, SYN, drv_kyle_pant, [KYLE]),
    ("drv_kyle_shing", "Blade Shing Run", "Metallic scrape and ring on each stride.", TAG_MADE, SYN, drv_kyle_shing, [KYLE]),
    ("drv_rob_wewe", "Rob's Wewe Loop", "The game's wewe voice clip, looped.", TAG_NOW, "sound/funny/wewe.wav (looped)", drv_rob_wewe, [ROB]),
    ("drv_rob_gg", "GG GG GG Run", "The game's gg voice clip chanted in time with footsteps.", TAG_NOW, "sound/funny/gg.wav (rhythm)", drv_rob_gg, [ROB]),
    ("drv_rob_heh", "Heh-Heh-Heh Jog", "The game's heh clip at running tempo, pitch bouncing.", TAG_NOW, "sound/funny/heh.wav (rhythm)", drv_rob_heh, [ROB]),
]

EXPLODE = [
    ("exp_confetti_horn", "Confetti Pop + Party Horn", "Pop, a rain of tiny sparkles, then a pah-paaaah blower.", TAG_MADE, SYN, exp_confetti_horn),
    ("exp_balloon_pop", "Balloon Pop", "Sharp latex crack and a floppy rubber flap.", TAG_MADE, SYN, exp_balloon_pop),
    ("exp_boing_bang", "Boing... BANG", "Cartoon spring winds up, then a big bang.", TAG_MADE, SYN, exp_boing_bang),
    ("exp_sad_trombone", "Sad Trombone", "Tiny pop, then wah-wah-wah-waaaah downhill.", TAG_MADE, SYN, exp_sad_trombone),
    ("exp_glass_springs", "Glass and Springs", "Shattering glass with sproingy springs flying out.", TAG_MADE, SYN, exp_glass_springs),
    ("exp_tada_chime", "Ta-Da Sparkle", "Thump, then a rising magic chime arpeggio and glitter.", TAG_MADE, SYN, exp_tada_chime),
    ("exp_fart_pop", "Fart-Pop", "Pop, long wet raspberry, one last pop.", TAG_MADE, SYN, exp_fart_pop),
    ("exp_slide_boom", "Slide Whistle Drop", "Slide whistle plunges... then boom.", TAG_MADE, SYN, exp_slide_boom),
    ("exp_chicken_pop", "Rubber Chicken", "Two squeaks, a pause for dread, then pop.", TAG_MADE, SYN, exp_chicken_pop),
    ("exp_sub_boom", "Big Sub-Bass Boom", "Floor-shaking boom with a noise burst on top.", TAG_MADE, SYN, exp_sub_boom),
    ("exp_car_boom", "Car Boom", "The car explosion from the car map.", TAG_NOW, "sound/vehicles/car_boom1.wav", M("vehicles/car_boom1.wav")),
    ("exp_mega_fart", "Mega Fart", "The grenade's mega-fart boom.", TAG_NOW, "sound/grenade/boom_04_mega_fart.wav", M("grenade/boom_04_mega_fart.wav")),
    ("exp_scream_launch", "Scream Launch", "The grenade boom with a scream in it.", TAG_NOW, "sound/grenade/boom_03_scream_launch.wav", M("grenade/boom_03_scream_launch.wav")),
    ("exp_goo_pop", "Goo Pop", "Squishy pop from the goo gun.", TAG_NOW, "sound/weapons/goopop.wav", M("weapons/goopop.wav")),
    ("exp_mm_boom09", "Mega Man Boom 9", "One of the 27 Mega Man contraption booms.", TAG_NOW, "sound/megaman/boom09.wav", M("megaman/boom09.wav")),
    ("exp_bonk_hit", "Bonk!", "The Bonk gun's hit sound.", TAG_NOW, "sound/fungun/fg_bonk_hit.wav", M("fungun/fg_bonk_hit.wav")),
    ("exp_q_rocket", "Quake Rocket Boom", "The classic rocket explosion.", TAG_Q, "weapons/r_exp3.wav", S("weapons/r_exp3.wav")),
    ("exp_q_zombie_gib", "Zombie Gib Splat", "Stock Quake zombie bursting.", TAG_Q, "zombie/z_gib.wav", S("zombie/z_gib.wav")),
    ("exp_q_pot_smash", "Clay Pot Smash", "A pot shattering, from the Quake 1.5 break sounds.", TAG_Q, "break/potbrk2.wav", S("break/potbrk2.wav")),
    ("exp_q_coaled", "Burning Monster Burst", "A monster going up, from the Quake 1.5 ambience.", TAG_Q, "ambience/coaled_monster_explode.wav", S("ambience/coaled_monster_explode.wav")),
    # --- made for specific monsters
    ("exp_rig_crash", "Rig Crash-Clatter", "Metal tubes crash and bounce, bolts scatter.", TAG_MADE, "synth + sound/vehicles/clang1.wav", exp_rig_crash, RIDERS),
    ("exp_rig_sproing", "Handlebar Sproing-Clang", "Springs sproing out of the rig, a clank, then pop.", TAG_MADE, SYN, exp_rig_sproing, RIDERS),
    ("exp_suit_papers", "Paperwork Pop", "Pop, loose papers fluttering, an office bell ding.", TAG_MADE, SYN, exp_suit_papers, [SUIT]),
    ("exp_squat_thud", "Squat Belly-Flop", "Heavy thud, a wet slap, metal clang and a squeak.", TAG_MADE, "synth + sound/vehicles/clang2.wav", exp_squat_thud, [SQUAT]),
    ("exp_wheel_blowout", "Tire Blowout", "Bang, a long pssshhh, flap-flap-flap slowing down.", TAG_MADE, SYN, exp_wheel_blowout, [WHEEL]),
    ("exp_wheel_wobble", "Wheel Spin-Down", "Pop, then the wheel clatters faster and faster to a buzz.", TAG_MADE, SYN, exp_wheel_wobble, [WHEEL]),
    ("exp_wheel_squeal_boom", "Squeal and Boom", "Long tire squeal sliding down into a big boom.", TAG_MADE, SYN, exp_wheel_squeal_boom, [WHEEL]),
    ("exp_roll_skid", "Skid Into Boom", "Tire skid screech, then a boom.", TAG_MADE, SYN, exp_roll_skid, [ROLL]),
    ("exp_roll_spinout", "Spin-Out Whirr-Pop", "A whirr climbing higher and higher, then pop and rattle.", TAG_MADE, SYN, exp_roll_spinout, [ROLL]),
    ("exp_roll_chirp", "Chirp-Chirp-Pop", "Three tire chirps and a pop.", TAG_MADE, SYN, exp_roll_chirp, [ROLL]),
    ("exp_kart_giggle", "Giggle Boom", "Pop and boom, then the game's giggling carries on.", TAG_MADE, "synth + sound/funny/giggles.wav", exp_kart_giggle, [JESS]),
    ("exp_kart_honk", "Honk-Honk-Pop", "Two kart horn honks, then pop.", TAG_MADE, "synth + sound/vehicles/horn.wav", exp_kart_honk, [JESS]),
    ("exp_kart_bell", "Bell Dings and Pop", "Bell dings speeding up, then a sparkly pop.", TAG_MADE, SYN, exp_kart_bell, [JESS]),
    ("exp_kyle_snip_pop", "Snip-Snip-Pop", "Three scissor snips then pop.", TAG_MADE, SYN, exp_kyle_snip_pop, [KYLE]),
    ("exp_kyle_scream", "Scream and Snip", "The game's scream-boom, then two last snips.", TAG_MADE, "synth + sound/grenade/boom_03_scream_launch.wav", exp_kyle_scream, [KYLE]),
    ("exp_kyle_clash", "Scissors Clash Boom", "Long metal ring of blades clashing, then boom.", TAG_MADE, SYN, exp_kyle_clash, [KYLE]),
    ("exp_rob_wewe", "Wewe-BOOM", "The game's wewe voice, then a boom.", TAG_NOW, "sound/funny/wewe.wav + synth boom", exp_rob_wewe, [ROB]),
    ("exp_rob_gg", "GG... Boom", "The game's gg voice, a pause, then a deep boom.", TAG_NOW, "sound/funny/gg.wav + synth boom", exp_rob_gg, [ROB]),
    ("exp_rob_heh_fart", "Heh... Fart-Pop", "A heh, the game's fart, then a pop.", TAG_NOW, "sound/funny/heh.wav, fart1.wav + synth pop", exp_rob_heh_fart, [ROB]),
]

# curated clips that are one unmodified game sound (only the level differs): the exact game-relative path
DIRECT_GAME_PATH = {
    "exp_car_boom": "vehicles/car_boom1.wav", "exp_mega_fart": "grenade/boom_04_mega_fart.wav",
    "exp_scream_launch": "grenade/boom_03_scream_launch.wav", "exp_goo_pop": "weapons/goopop.wav",
    "exp_mm_boom09": "megaman/boom09.wav", "exp_bonk_hit": "fungun/fg_bonk_hit.wav", "exp_q_rocket": "weapons/r_exp3.wav",
    "exp_q_zombie_gib": "zombie/z_gib.wav", "exp_q_pot_smash": "break/potbrk2.wav", "exp_q_coaled": "ambience/coaled_monster_explode.wav",
}

# (key, name, short name, note, game id (mb_pool), thumbnail file)
MONSTERS = [
    (SUIT, "Suit Rider on Bar & Wheels", "Suit Rider", "A suit riding a handlebar-and-wheels rig", 2, "02_suit_rider.png"),
    (SQUAT, "Squat Rider on Bar & Wheels", "Squat Rider", "A squat guy on the same kind of rig", 4, "04_squat_rider.png"),
    (WHEEL, "Wheelman", "Wheelman", "A guy on a single big wheel", 9, "09_wheelman.png"),
    (JESS, "JessKart Racer", "JessKart", "Two women on a go-kart/trike", 10, "10_jesskart.png"),
    (KYLE, "Kyle the Scissor Man", "Kyle", "Running with scissors", 11, "11_kyle_scissors.png"),
    (ROB, "Friend Rob", "Friend Rob", "Rob", 14, "14_friend_rob.png"),
    (ROLL, "Rolling Wheelman", "Rolling Wheelman", "Wheelman, rolling", 16, "16_wheelman_rolling.png"),
]

# optional extra fields per monster key, passed straight to the page (make_mbox_vote_page.py uses it)
MONSTER_EXTRA = {}

# Existing clips that suit each monster (listed after the clips made for it); order = suggested order.
SUGGEST_BASE = {
    SUIT: {"drive": ["drv_trike_squeak", "drv_cart_rattle", "drv_tile_skate", "drv_idle_coupe", "drv_megamotor"],
           "explode": ["exp_car_boom", "exp_glass_springs", "exp_boing_bang", "exp_sad_trombone"]},
    SQUAT: {"drive": ["drv_cart_rattle", "drv_trike_squeak", "drv_q_drag", "drv_q_train", "drv_mm_drive"],
            "explode": ["exp_sub_boom", "exp_car_boom", "exp_q_rocket", "exp_glass_springs"]},
    WHEEL: {"drive": ["drv_unicycle_whir", "drv_tile_skate", "drv_q_train", "drv_q_drag", "drv_engine_grain"],
            "explode": ["exp_slide_boom", "exp_balloon_pop", "exp_boing_bang", "exp_sad_trombone"]},
    JESS: {"drive": ["drv_kart_buzz", "drv_trike_squeak", "drv_icecream", "drv_engine_grain"],
           "explode": ["exp_confetti_horn", "exp_tada_chime", "exp_balloon_pop", "exp_goo_pop"]},
    KYLE: {"drive": ["drv_scissor_snip", "drv_tippy_tap", "drv_boing_hop"],
           "explode": ["exp_scream_launch", "exp_glass_springs", "exp_chicken_pop", "exp_q_zombie_gib"]},
    ROB: {"drive": ["drv_kazoo_engine", "drv_boing_hop", "drv_icecream"],
          "explode": ["exp_mega_fart", "exp_fart_pop", "exp_bonk_hit", "exp_chicken_pop", "exp_sad_trombone"]},
    ROLL: {"drive": ["drv_unicycle_whir", "drv_tile_skate", "drv_engine_grain", "drv_q_hop", "drv_kart_buzz"],
           "explode": ["exp_slide_boom", "exp_balloon_pop", "exp_boing_bang", "exp_confetti_horn"]},
}


# ----------------------------------------------------------------------------- finishing, QA
def finalize(x, loop, rms_cap):
    x = np.asarray(x, dtype=np.float64)
    x = np.nan_to_num(x)
    x = x - np.mean(x)                                   # DC
    if not loop:
        x = hp(x, 22, 1)                                 # kill sub-audible drift on one-shots
        fi, fo = int(0.002 * SR), int(0.03 * SR)
        x[:fi] *= np.linspace(0, 1, fi)
        x[-fo:] *= np.linspace(1, 0, fo)
    peak = np.abs(x).max()
    rms = np.sqrt(np.mean(x ** 2))
    g = min(PEAK / (peak + 1e-12), rms_cap / (rms + 1e-12))
    return x * g


def write_wav(path, x):
    pcm = np.round(np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def check_wav(path):
    with wave.open(path, "rb") as w:
        n, sr = w.getnframes(), w.getframerate()
        a = np.frombuffer(w.readframes(n), "<i2").astype(np.float64) / 32768
    dur = n / sr
    peak = float(np.abs(a).max())
    rms = float(np.sqrt(np.mean(a ** 2)))
    clipped = int(np.sum(np.abs(a) >= 0.9995))
    dc = float(np.mean(a))
    seam = abs(a[0] - a[-1]) / (np.median(np.abs(np.diff(a))) * 3 + 1e-6)
    return dict(dur=round(dur, 3), peak=round(peak, 3), rms=round(rms, 3), dc=round(dc, 5), clipped=clipped, seam=round(float(seam), 2))


def thumb_uri(fn):
    """Small WebP data URI of a vote thumbnail (needs PIL; falls back to the full PNG)."""
    path = os.path.join(THUMBS, fn)
    try:
        import io
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        im.thumbnail((260, 260))
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=82, method=6)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:                      # pragma: no cover
        print("thumb fallback", fn, e)
        with open(path, "rb") as fh:
            return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")


# ----------------------------------------------------------------------------- the "browse every sound" library
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor

LIB_CACHE = os.path.join(OUTDIR, "lib_cache")
PREVIEW_CAP = {"mod": 10.0, "stock": 6.0}      # seconds of preview kept for long sources (the true length is still shown)
MP3_KBPS = {"mod": 40, "stock": 24}            # stock sounds are only for auditioning: smaller
LIB_VER = "v2"
# nice titles; the folders the user added come first ("The fun ones")
FUN_FOLDERS = [("funny", "Funny voices & noises"), ("john", "John"), ("larry", "Larry"), ("friends", "Friends"), ("hackmon", "Hackmon"),
               ("calc", "Calculator"), ("floathead", "Floathead"), ("grenade", "Grenade booms"), ("pickle", "Pickle Surprise"),
               ("fungun", "Fun guns (pong, bonk, fork)"), ("hammer", "Hammer"), ("megaman", "Mega Man"), ("ltgun", "Laptop gun"),
               ("milky", "Pink Lady / Milky Gun"), ("netsend", "NetSend gun"), ("jetpack", "Jetpack")]
OTHER_FOLDERS = [("vehicles", "Vehicles"), ("weapons", "Weapons"), ("misc", "Misc"), ("ccc", "CCC"), ("bklan", "B-LAN warehouse")]
AUDIO_EXT = (".wav", ".ogg", ".mp3")


def collect_library():
    """Every sound file of the mod's sound/ folder plus every stock Quake sound (pak0.pak, q15.pk3; music tracks left out)."""
    ents = []
    for root, _dirs, files in os.walk(SND):
        for fn in sorted(files):
            if not fn.lower().endswith(AUDIO_EXT):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, SND).replace("\\", "/")
            top = rel.split("/")[0] if "/" in rel else "(root)"
            with open(full, "rb") as fh:
                ents.append(dict(src="mod", path=rel, folder="mod:" + top, top=top, pk="", data=fh.read()))
    stock = {}
    stock_bytes("weapons/r_exp3.wav")            # opens the archives
    f, ents_pak = _pak
    for key, (o, l) in ents_pak.items():
        if key.startswith("sound/") and key.lower().endswith(AUDIO_EXT) and l > 0:
            f.seek(o)
            stock[key[6:]] = ("pak0.pak", f.read(l))
    for zi in _pk3.infolist():
        n = zi.filename
        if n.startswith("sound/") and n.lower().endswith(AUDIO_EXT) and zi.file_size > 0 and not n.startswith("sound/cdtracks/"):
            stock[n[6:]] = ("q15.pk3", _pk3.read(n))      # q15.pk3 overrides pak0
    for path, (pk, data) in stock.items():
        top = path.split("/")[0] if "/" in path else "(root)"
        ents.append(dict(src="stock", path=path, folder="stock:" + top, top=top, pk=pk, data=data))
    # folder table + ordering
    fun = [k for k, _ in FUN_FOLDERS]
    other = [k for k, _ in OTHER_FOLDERS]
    titles = dict(FUN_FOLDERS + OTHER_FOLDERS)
    mod_tops = sorted({e["top"] for e in ents if e["src"] == "mod"})
    order = [("mod:" + k, titles[k], "fun") for k in fun if k in mod_tops]
    order += [("mod:" + k, titles[k], "other") for k in other if k in mod_tops]
    order += [("mod:" + k, k, "other") for k in mod_tops if k not in titles]
    st_tops = sorted({e["top"] for e in ents if e["src"] == "stock"})
    order += [("stock:" + k, ("Stock: " + (k if k != "(root)" else "sound root")), "stock") for k in st_tops]
    rank = {k: i for i, (k, _t, _g) in enumerate(order)}
    ents.sort(key=lambda e: (rank[e["folder"]], [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", e["path"])]))
    return ents, order


def _run(cmd, data):
    return subprocess.run(cmd, input=data, capture_output=True)


def make_preview(e):
    """-> (mp3 bytes, true duration s, capped?, silent?). Level-matched like the curated clips; cached on disk."""
    key = hashlib.sha1(e["data"] + ("|%s|%s|%s" % (LIB_VER, PREVIEW_CAP[e["src"]], MP3_KBPS[e["src"]])).encode()).hexdigest()[:24]
    cp = os.path.join(LIB_CACHE, key + ".mp3")
    mp = os.path.join(LIB_CACHE, key + ".json")
    if os.path.exists(cp) and os.path.exists(mp):
        with open(mp) as fh:
            m = json.load(fh)
        with open(cp, "rb") as fh:
            return fh.read(), m["dur"], m["capped"], m["silent"]
    p = _run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"], e["data"])
    a = np.frombuffer(p.stdout, "<f4").astype(np.float64)
    if len(a) < 10:
        return None
    dur = len(a) / SR
    cap = PREVIEW_CAP[e["src"]]
    capped = dur > cap
    if capped:
        a = a[:int(cap * SR)]
        fo = int(0.05 * SR)
        a[-fo:] *= np.linspace(1, 0, fo)
    a = a - np.mean(a)
    peak = float(np.abs(a).max())
    rms = float(np.sqrt(np.mean(a ** 2)))
    silent = peak < 1e-4
    if not silent:
        a = a * min(PEAK / peak, 0.18 / max(rms, 1e-9))
    q = _run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0", "-c:a", "libmp3lame",
              "-b:a", "%dk" % MP3_KBPS[e["src"]], "-f", "mp3", "pipe:1"], np.clip(a, -1, 1).astype("<f4").tobytes())
    mp3 = q.stdout
    if not mp3:
        return None
    os.makedirs(LIB_CACHE, exist_ok=True)
    with open(cp, "wb") as fh:
        fh.write(mp3)
    with open(mp, "w") as fh:
        json.dump(dict(dur=round(dur, 3), capped=capped, silent=silent), fh)
    return mp3, round(dur, 3), capped, silent


def build_library():
    ents, order = collect_library()
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(make_preview, ents))
    lib, audio, skipped = [], [], []
    counts = {}
    for e, r in zip(ents, res):
        if r is None:
            skipped.append(e["src"] + ":" + e["path"])
            continue
        mp3, dur, capped, silent = r
        lib.append(dict(p=e["path"], g=e["folder"], d=dur, pd=round(min(dur, PREVIEW_CAP[e["src"]]), 2), c=1 if capped else 0, s=e["src"], k=e["pk"], z=1 if silent else 0))
        audio.append(base64.b64encode(mp3).decode("ascii"))
        counts[e["folder"]] = counts.get(e["folder"], 0) + 1
    folders = [dict(key=k, title=t, group=g, count=counts.get(k, 0)) for k, t, g in order if counts.get(k, 0)]
    return lib, audio, folders, skipped



def main():
    os.makedirs(CLIPS, exist_ok=True)
    meta = []
    problems = []
    for job, table, loop, cap in (("drive", DRIVE, True, 0.16), ("explode", EXPLODE, False, 0.20)):
        for row in table:
            cid, name, desc, tag, origin, fn = row[:6]
            fors = list(row[6]) if len(row) > 6 else []
            x = finalize(fn(), loop, cap)
            path = os.path.join(CLIPS, cid + ".wav")
            write_wav(path, x)
            q = check_wav(path)
            if q["clipped"] or q["rms"] < 0.01 or abs(q["dc"]) > 0.005:
                problems.append((cid, q))
            if loop and not (1.0 <= q["dur"] <= 2.3):
                problems.append((cid, "loop length", q["dur"]))
            if (not loop) and not (0.4 <= q["dur"] <= 3.1):
                problems.append((cid, "one-shot length", q["dur"]))
            meta.append(dict(id=cid, file=cid + ".wav", job=job, loop=loop, name=name, desc=desc, source=tag, made_for=fors,
                             origin=("synthesised by make_mbox_sound_vote.py" if origin == SYN else origin), **q))
    for m in meta:
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,sample_rate,channels:format=duration",
                            "-of", "json", os.path.join(CLIPS, m["file"])], capture_output=True, text=True)
        info = json.loads(p.stdout)
        m["ffprobe_ok"] = bool(info.get("streams")) and float(info["format"]["duration"]) > 0.3
        if not m["ffprobe_ok"]:
            problems.append((m["id"], "ffprobe failed"))
    with open(os.path.join(OUTDIR, "clips.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)

    ids = {m["id"] for m in meta}
    suggest = {}
    for key, *_ in MONSTERS:
        suggest[key] = {}
        for job in ("drive", "explode"):
            own = [m["id"] for m in meta if m["job"] == job and key in m["made_for"]]
            base = [i for i in SUGGEST_BASE[key][job] if i in ids]
            suggest[key][job] = own + [i for i in base if i not in own]

    payload = []
    for m in meta:
        with open(os.path.join(CLIPS, m["file"]), "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        gp = DIRECT_GAME_PATH.get(m["id"])
        dm = re.match(r"^(?:sound/)?([\w/]+\.wav)", m["origin"])
        payload.append(dict(id=m["id"], file=m["file"], job=m["job"], loop=m["loop"], name=m["name"], desc=m["desc"],
                            source=m["source"], origin=m["origin"], dur=m["dur"], b64=b64, game_path=gp,
                            derived_from=(dm.group(1) if dm and not gp else None)))
    mons = [dict(key=k, name=n, short=s, note=d, game_id=g, thumb=thumb_uri(th), **MONSTER_EXTRA.get(k, {})) for k, n, s, d, g, th in MONSTERS]
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as fh:
        html = fh.read()
    lib, libaudio, libfolders, skipped = build_library()
    for ph, val in (("__CLIPS_JSON__", payload), ("__MONSTERS_JSON__", mons), ("__SUGGEST_JSON__", suggest),
                    ("__LIB_JSON__", lib), ("__LIBFOLDERS_JSON__", libfolders), ("__LIBAUDIO_JSON__", libaudio)):
        html = html.replace(ph, json.dumps(val, ensure_ascii=True).replace("</", "<\\/"))
    with open(PAGE, "w", encoding="utf-8") as fh:
        fh.write(html)

    print("%-22s %-7s %-17s %6s %6s %6s %8s %5s %6s" % ("id", "job", "source", "dur", "peak", "rms", "dc", "clip", "seam"))
    for m in meta:
        print("%-22s %-7s %-17s %6.2f %6.3f %6.3f %8.5f %5d %6.2f" % (m["id"], m["job"], m["source"], m["dur"], m["peak"], m["rms"], m["dc"], m["clipped"], m["seam"]))
    print("library: %d sounds in %d folders, %d skipped %s" % (len(lib), len(libfolders), len(skipped), skipped))
    for fo in libfolders:
        print("  %-28s %-6s %4d" % (fo["title"], fo["group"], fo["count"]))
    print("preview audio total %.2f MB (base64 %.2f MB)" % (sum(len(a) * 3 / 4 for a in libaudio) / 1e6, sum(len(a) for a in libaudio) / 1e6))
    print("page: %s  (%.2f MB)  clips: %d" % (PAGE, os.path.getsize(PAGE) / 1e6, len(meta)))
    print("PROBLEMS:", problems if problems else "none")


if __name__ == "__main__":
    main()
