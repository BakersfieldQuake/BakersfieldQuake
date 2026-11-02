"""Builds the Wheelman Cannon candidate sounds, the default in-game sounds and the vote page.

    python3.13 build_wcannon_sounds.py

Writes
  source/wcannon_sound_vote/clips/<slot>_<nn>.wav   candidates (22050 Hz mono s16)
  source/wcannon_sound_vote/clips.json              id, slot, label, source, dur, default
  sound/wcannon/wc_{charge,shoot,scream,boom}.wav   the default pick of each slot
  wheelman_cannon_sound_vote.html                   self-contained vote page (audio as base64 mp3)

Re-runnable: everything is deterministic (fixed random seed).  Apply the votes with apply_wcannon_votes.py.
Needs numpy + scipy + ffmpeg on PATH.
"""
import base64, json, os, shutil, struct, subprocess, sys, tempfile
import numpy as np
from scipy import signal as sg
from scipy.io import wavfile

SR = 22050
HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))                 # .../BakersfieldQuake
VOTE_DIR = os.path.join(MOD, "source", "wcannon_sound_vote")
CLIP_DIR = os.path.join(VOTE_DIR, "clips")
GAME_DIR = os.path.join(MOD, "sound", "wcannon")
PAGE = os.path.join(MOD, "wheelman_cannon_sound_vote.html")
PAK = os.path.join(os.path.dirname(MOD), "id1", "pak0.pak")
RAND = os.path.join(MOD, "source", "sound_bank", "random_sounds")

rng = np.random.default_rng(1234)
LIMIT = {"charge": 1.6, "shoot": 1.2, "scream": 1.6, "boom": 3.0}

# default pick of each slot, matched by label
DEFAULTS = {
    "charge": "Turbine spool-up",
    "shoot": "Mortar thump + whistle",
    "scream": "Flaming shriek",
    "boom": "Big boom, sub-bass tail",
}

# ------------------------------------------------------------------ dsp helpers
def nz(d):            return rng.standard_normal(int(d * SR))
def tt(d):            return np.arange(int(d * SR)) / SR
def n_of(d):          return int(d * SR)

def _sos(kind, f, o):
    return sg.butter(o, f, kind, fs=SR, output="sos")

def lp(x, f, o=2):    return sg.sosfilt(_sos("lowpass", min(f, 10500), o), x)
def hp(x, f, o=2):    return sg.sosfilt(_sos("highpass", f, o), x)
def bp(x, lo, hi, o=2): return sg.sosfilt(_sos("bandpass", [lo, min(hi, 10500)], o), x)

def env(d, pts):
    """Piecewise-linear envelope over d seconds from [(time, value), ...]."""
    t = tt(d)
    return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])

def expd(d, tau):     return np.exp(-tt(d) / tau)

def glide(f0, f1, d, power=1.0):
    """Exponential frequency glide f0 -> f1; power>1 delays the change."""
    u = (tt(d) / d) ** power
    return f0 * (f1 / f0) ** u

def osc(f, shape="sine"):
    ph = np.cumsum(2 * np.pi * f / SR)
    if shape == "sine":   return np.sin(ph)
    if shape == "saw":    return sg.sawtooth(ph)
    if shape == "square": return sg.square(ph)
    raise ValueError(shape)

def sweep_noise(f_of_t, d, q=3.0, amp=None):
    """Noise through a band-pass whose centre follows f_of_t (array), in 256-sample blocks."""
    n = n_of(d); x = nz(d); y = np.zeros(n); zi = None; B = 256
    for i in range(0, n, B):
        fc = float(np.clip(f_of_t[min(i, len(f_of_t) - 1)], 80, 9500))
        sos = sg.butter(2, [fc * (1 - 0.5 / q), fc * (1 + 0.5 / q)], "bandpass", fs=SR, output="sos")
        if zi is None: zi = np.zeros((sos.shape[0], 2))
        y[i:i + B], zi = sg.sosfilt(sos, x[i:i + B], zi=zi)
    return y * (amp if amp is not None else 1.0)

def crackle(d, dens0, dens1, amp=1.0, tail=0.0009, hpf=0):
    """Random fire/spark crackle; density in clicks per second ramping dens0 -> dens1."""
    n = n_of(d)
    dens = np.linspace(dens0, dens1, n) / SR
    hit = rng.random(n) < dens
    imp = hit * (rng.random(n) ** 2) * rng.choice([-1, 1], n)
    k = nz(0.006) * np.exp(-tt(0.006) / tail)
    y = sg.fftconvolve(imp, k)[:n] * amp
    return hp(y, hpf) if hpf else y

def place(out, x, at=0.0, gain=1.0):
    i = n_of(at)
    if i >= len(out): return
    m = min(len(x), len(out) - i)
    out[i:i + m] += x[:m] * gain

def pad(x, d):
    n = n_of(d)
    return np.pad(x, (0, max(0, n - len(x))))[:n]

def clang(base, d=1.0, tau=0.35, ratios=(1, 2.76, 5.4, 8.93, 11.3), amps=(1, .7, .5, .35, .2)):
    t = tt(d); y = np.zeros(len(t))
    for r, a in zip(ratios, amps):
        y += a * np.sin(2 * np.pi * base * r * t + rng.random() * 6) * np.exp(-t / (tau / (0.6 + 0.4 * r ** .5)))
    y *= np.minimum(1, t / 0.002)
    return y

def thump(f0=160, f1=45, d=0.5, tau=0.12, click=0.3):
    t = tt(d)
    y = osc(glide(f0, f1, d, 0.5)) * np.exp(-t / tau)
    y += click * lp(nz(d), 700) * np.exp(-t / 0.02)
    return y

def boom_core(d, size=1.0, sub=True):
    """Layered explosion: band-passed noise bursts with longer decay for the lows, plus a sub-bass drop."""
    out = np.zeros(n_of(d))
    for lo, hi, tau, g in [(40, 160, 0.55, 1.0), (160, 600, 0.32, 0.9), (600, 2500, 0.16, 0.6), (2500, 9000, 0.07, 0.35)]:
        b = bp(nz(d), lo, hi) * np.exp(-tt(d) / (tau * size))
        out += g * b / (np.std(b) + 1e-9) * 0.3
    out *= np.minimum(1, tt(d) / 0.003)
    if sub:
        out += 1.1 * osc(glide(75, 26, d, 0.6)) * np.exp(-tt(d) / (0.55 * size)) * np.minimum(1, tt(d) / 0.01)
    return np.tanh(out * 1.2)

def speed(x, r):
    idx = np.arange(0, len(x) - 1, r)
    return np.interp(idx, np.arange(len(x)), x)

def loop_ramp(x, r0, r1, d):
    """Loop x while its playback rate ramps r0 -> r1 over d seconds."""
    n = n_of(d)
    rate = np.linspace(r0, r1, n)
    pos = np.cumsum(rate) % (len(x) - 1)
    return np.interp(pos, np.arange(len(x)), x)

def fade(x, a=0.003, r=0.02):
    x = x.copy()
    na, nr = max(1, n_of(a)), max(1, n_of(r))
    na, nr = min(na, len(x)), min(nr, len(x))
    x[:na] *= np.linspace(0, 1, na)
    x[-nr:] *= np.linspace(1, 0, nr)
    return x

def norm(x, peak=0.708):                       # about -3 dBFS
    x = x - np.mean(x)
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 1e-6 else x

# ------------------------------------------------------------------ voice
VOW = {"a": (800, 1200, 2600), "o": (500, 900, 2500), "e": (450, 1900, 2600),
       "i": (300, 2300, 3000), "u": (330, 800, 2400), "ae": (700, 1700, 2500)}

def voice(f0, vow, vib=(6.0, 0.03), breath=0.12, jitter=0.0, growl=(0, 0.0), drive=0.0, fscale=1.0, tilt=1.0):
    """Additive formant voice.  f0: Hz array.  vow: vowel name or [(frac, vowel), ...] across the clip."""
    n = len(f0); t = np.arange(n) / SR; d = n / SR
    f = f0 * (1 + vib[1] * np.sin(2 * np.pi * vib[0] * t))
    if jitter:
        j = lp(rng.standard_normal(n), 40, 1); j /= np.std(j) + 1e-9
        f = f * (1 + jitter * j)
    if isinstance(vow, str): vow = [(0, vow), (1, vow)]
    fr = [p[0] for p in vow]
    F = [np.interp(t / d, fr, [VOW[p[1]][i] for p in vow]) * fscale for i in range(3)]
    ph = np.cumsum(2 * np.pi * f / SR)
    K = int(min(9500 / max(f.min(), 60), 110))
    bw = (90, 120, 170); g = (1.0, 0.65, 0.35)
    out = np.zeros(n)
    for k in range(1, K + 1):
        fk = k * f
        a = sum(g[i] / (1 + ((fk - F[i]) / bw[i]) ** 2) for i in range(3)) + 0.01
        a = a / k ** (tilt - 0.4)
        a = a * (fk < 10000)
        out += a * np.sin(k * ph)
    out /= np.max(np.abs(out)) + 1e-9
    if breath:
        out += breath * bp(rng.standard_normal(n), 900, 4500)
    if growl[0]:
        out *= 1 - growl[1] + growl[1] * (0.5 + 0.5 * np.sin(2 * np.pi * growl[0] * t))
    if drive:
        out = np.tanh(out * drive)
    return out

# ------------------------------------------------------------------ source audio
def ff_load(path, trim=None, extra=()):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR)]
    if trim: cmd += ["-t", str(trim)]
    cmd += list(extra) + ["-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0

_pak = None
def pak_clip(name):
    global _pak
    if _pak is None:
        with open(PAK, "rb") as f:
            h, o, l = struct.unpack("<4sii", f.read(12))
            f.seek(o); d = f.read(l)
            ents = {d[i:i + 56].split(b"\0")[0].decode(): struct.unpack("<ii", d[i + 56:i + 64]) for i in range(0, l, 64)}
        _pak = (ents,)
    ents = _pak[0]
    off, size = ents["sound/" + name]
    with open(PAK, "rb") as f:
        f.seek(off); data = f.read(size)
    tmp = os.path.join(tempfile.gettempdir(), "wc_" + name.replace("/", "_"))
    with open(tmp, "wb") as f: f.write(data)
    try:    return ff_load(tmp)
    finally: os.remove(tmp)

def rand_clip(name, maxd, loud=False):
    x = ff_load(os.path.join(RAND, name))
    a = np.abs(x); idx = np.nonzero(a > 0.03 * a.max())[0]     # skip leading silence
    if len(idx): x = x[max(0, idx[0] - n_of(0.01)):]
    if loud and len(x) > n_of(maxd):                           # earliest window with nearly the most energy
        w = n_of(maxd); e = np.concatenate([[0], np.cumsum(x ** 2)]); win = e[w:] - e[:-w]
        st = int(np.nonzero(win >= 0.9 * win.max())[0][0])
        x = x[st:]
        x[:n_of(0.02)] *= np.linspace(0, 1, n_of(0.02))
    return x[:n_of(maxd)]

# ------------------------------------------------------------------ candidates
CLIPS = []                                  # (slot, label, source, samples)
def add(slot, label, source, x):
    x = x - np.mean(x)
    k = 4.0 * np.sqrt(np.mean(x ** 2)) + 1e-9          # soft-clip lone spikes (crackle) so the body is not squashed by normalising
    x = np.tanh(x / k) * k
    x = norm(x)
    idx = np.nonzero(np.abs(x) > 0.004)[0]               # drop a silent tail
    if len(idx): x = x[:min(len(x), idx[-1] + n_of(0.05))]
    x = fade(x, 0.002, 0.03 if slot != "boom" else 0.08)
    x = x[:n_of(LIMIT[slot])]
    CLIPS.append((slot, label, source, x))

# ---- charge: builds up for 1.5 s, rising
def charge_turbine():
    d = 1.5; t = tt(d); u = t / d
    f = glide(70, 1200, d, 1.3)
    y = lp(osc(f, "saw"), 3500) * 0.7 + 0.25 * osc(f * 2)
    y += hp(nz(d), 2500) * (u ** 2) * 0.25
    y += 0.3 * lp(nz(d), 300)
    return y * (0.12 + 0.88 * u ** 1.3)

def charge_tesla():
    d = 1.5; t = tt(d); u = t / d
    f = glide(90, 330, d, 1.2)
    y = sum(a * osc(f * k) for k, a in [(1, 1), (2, .6), (3, .5), (5, .3), (7, .2)])
    y *= 0.6 + 0.4 * np.sin(2 * np.pi * 100 * t)
    y += crackle(d, 15, 450, 4.0, 0.0006, 1500)
    y += 0.12 * osc(glide(1800, 5200, d)) * u
    return y * (0.2 + 0.8 * u ** 1.1)

def charge_bike():
    d = 1.5; n = n_of(d)
    rate = env(d, [(0, 12), (0.38, 42), (0.5, 18), (0.65, 24), (1.5, 78)])
    frac = (np.cumsum(rate) / SR) % 1
    y = np.exp(-9 * frac) - 0.12
    y = lp(hp(y, 45), 2000, 2)
    y += 0.22 * lp(nz(d), 2500) * env(d, [(0, .1), (1.5, .5)])
    return y * env(d, [(0, .35), (.4, .7), (.5, .5), (1.5, 1)])

def charge_windup():
    d = 1.5; t = tt(d); u = t / d
    f = glide(250, 2300, d, 1.1) * (1 + 0.03 * np.sin(2 * np.pi * 9 * t))
    y = 0.6 * osc(f)
    rate = np.linspace(7, 48, len(t))
    frac = (np.cumsum(rate) / SR) % 1
    y += 1.2 * bp(nz(d), 900, 4500) * np.exp(-55 * frac)
    return y * (0.3 + 0.7 * u)

def charge_capacitor():
    d = 1.5; t = tt(d); u = t / d
    fc = glide(180, 3300, d, 1.0)
    y = np.sin(np.cumsum(2 * np.pi * fc / SR) + (0.5 + 4 * u) * np.sin(np.cumsum(2 * np.pi * fc * 2.01 / SR)))
    y = y * (0.15 + 0.85 * u ** 1.2)
    y[n_of(1.42):] *= 0.0
    y = pad(y, d)
    place(y, np.sin(2 * np.pi * 2000 * tt(0.16)) * np.exp(-tt(0.16) / 0.05), 1.34, 0.9)   # ready ping
    return y

def charge_voice():
    d = 1.5
    f0 = glide(120, 560, d, 1.2)
    y = voice(f0, [(0, "u"), (0.5, "o"), (1, "a")], vib=(6, 0.025), breath=0.15, jitter=0.01, growl=(45, 0.5), drive=2.0)
    return y * env(d, [(0, .15), (1.1, .7), (1.5, 1)])

def charge_tire():
    d = 1.5; t = tt(d); u = t / d
    y = sweep_noise(np.interp(t, [0, d], [700, 3800]), d, 2.5)
    y *= 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(np.linspace(5, 38, len(t))) / SR)
    y += 0.5 * osc(glide(500, 1700, d) * (1 + 0.04 * np.sin(2 * np.pi * 14 * t))) * u ** 1.5
    y += 0.6 * lp(nz(d), 200)
    return y * (0.15 + 0.85 * u ** 1.2)

def charge_siren():
    d = 1.5; t = tt(d); u = t / d
    f = 330 + 450 * 0.5 * (1 - np.cos(2 * np.pi * 1.4 * t)) + 450 * u
    y = osc(f, "saw") * 0.5 + osc(f) * 0.5
    return lp(y, 3000) * (0.2 + 0.8 * u)

def charge_game_lightning():
    return loop_ramp(pak_clip("weapons/lstart.wav"), 0.7, 1.8, 1.5) * env(1.5, [(0, .3), (1.3, 1), (1.5, 1)])

def charge_game_fire():
    x = pak_clip("ambience/fire1.wav")
    y = loop_ramp(x, 0.8, 2.4, 1.5)
    return y * env(1.5, [(0, .3), (1.5, 1)]) + 0.6 * crackle(1.5, 20, 300, 3, 0.0008, 1200)

def charge_chicken():
    c = rand_clip("chicken.wav", 0.4)
    d = 1.5; y = np.zeros(n_of(d)); t = 0.0; r = 0.75
    while t < d - 0.1:
        place(y, speed(c, r), t, 0.4 + 0.6 * t / d)
        t += 0.34 * (1 - 0.82 * t / d) ** 1.0 + 0.04
        r *= 1.06
    return y

# ---- shoot: the cannon fires the Wheelman, <= 1.2 s
def shoot_mortar():
    d = 1.1; y = np.zeros(n_of(d))
    place(y, thump(150, 38, 0.6, 0.14, 0.5) * 1.3)
    place(y, sweep_noise(glide(1800, 300, 1.0, 0.7), 1.0, 1.5) * expd(1.0, 0.35) * 1.5, 0.03)
    place(y, osc(glide(2600, 450, 0.9, 0.6) * (1 + 0.02 * np.sin(2 * np.pi * 8 * tt(0.9)))) * expd(0.9, 0.3) * 0.3, 0.06)
    return np.tanh(y)

def shoot_popwhistle():
    d = 1.1; y = np.zeros(n_of(d))
    place(y, osc(glide(900, 140, 0.08, 0.4)) * expd(0.08, 0.025) * 1.2)
    place(y, bp(nz(0.05), 800, 4000) * expd(0.05, 0.01) * 0.9)
    place(y, osc(glide(3400, 520, 1.0, 0.8) * (1 + 0.03 * np.sin(2 * np.pi * 10 * tt(1.0)))) * expd(1.0, 0.45) * 0.5, 0.04)
    return y

def shoot_rocket():
    d = 1.2; t = tt(d)
    f = np.interp(t, [0, .2, d], [250, 2400, 600])
    y = sweep_noise(f, d, 1.2) * 1.2 * env(d, [(0, 0), (.02, 1), (.5, .7), (1.2, 0)])
    y += 0.6 * lp(nz(d), 220) * env(d, [(0, 1), (1.2, 0)])
    place(y, bp(nz(0.05), 1500, 7000) * expd(0.05, 0.015) * 2.0)
    return y

def shoot_cannon_ring():
    d = 1.2; y = np.zeros(n_of(d))
    place(y, boom_core(1.0, 0.45) * 1.2)
    place(y, clang(520, 1.1, 0.5) * 0.35, 0.005)
    return y

def shoot_laser():
    d = 0.8; t = tt(d)
    f = glide(3200, 110, 0.35, 0.7)
    y = np.zeros(n_of(d))
    place(y, osc(f, "square") * 0.35 + osc(f * 1.5) * 0.4 + osc(f * 0.5) * 0.4)
    y *= env(d, [(0, 1), (0.35, 0.9), (0.36, 0.0), (0.8, 0)]) * 1.0
    echo = np.zeros_like(y); place(echo, y, 0.12, 0.45); place(echo, y, 0.25, 0.25)
    place(y, bp(nz(0.06), 2000, 8000) * expd(0.06, 0.02) * 0.6)
    return y + echo

def shoot_sonic():
    d = 1.2; y = np.zeros(n_of(d))
    place(y, np.r_[1.0, -0.8, 0.6, -0.3, np.zeros(60)] * 2)
    place(y, bp(nz(0.07), 3000, 9500) * expd(0.07, 0.02) * 2.0)
    f = glide(4500, 380, 1.1, 0.8)
    place(y, sweep_noise(f, 1.1, 1.8) * env(1.1, [(0, 0), (0.12, 1), (1.1, 0)]) * 1.4, 0.03)
    place(y, thump(110, 50, 0.3, 0.07) * 0.6)
    return y

def shoot_cork():
    d = 1.0; y = np.zeros(n_of(d))
    place(y, bp(nz(0.04), 400, 5000) * expd(0.04, 0.008) * 1.5)
    place(y, osc(glide(700, 250, 0.05)) * expd(0.05, 0.015) * 1.2)
    place(y, hp(nz(0.9), 3000) * expd(0.9, 0.3) * 0.5, 0.01)
    place(y, sweep_noise(glide(700, 3500, 0.5, 0.5), 0.5, 1.5) * expd(0.5, 0.3) * 0.8, 0.02)
    return y

def shoot_boing():
    d = 1.2; t = tt(d)
    f = 280 * (1 + 0.9 * np.exp(-t / 0.28) * np.sin(2 * np.pi * 11 * t * (1 + 1.5 * t)))
    y = osc(f) * expd(d, 0.4) * 0.8 + 0.3 * osc(f * 2) * expd(d, 0.25)
    place(y, thump(130, 50, 0.3, 0.07) * 0.9)
    place(y, sweep_noise(glide(2200, 500, 0.8), 0.8, 1.3) * expd(0.8, 0.3) * 0.8, 0.02)
    return y

def shoot_game_rocket():  return pak_clip("weapons/rocket1i.wav")
def shoot_game_grenade(): return pak_clip("weapons/grenade.wav")

def shoot_game_deep():
    d = 1.2; y = np.zeros(n_of(d))
    place(y, speed(pak_clip("weapons/sgun1.wav"), 0.55))
    place(y, pak_clip("weapons/rocket1i.wav"), 0.05, 0.8)
    return y

def shoot_rand_yay():
    d = 1.2; y = np.zeros(n_of(d))
    place(y, thump(150, 38, 0.5, 0.12, 0.5) * 1.2)
    place(y, bp(nz(0.05), 800, 4000) * expd(0.05, 0.012))
    place(y, rand_clip("YaY.wav", 0.4), 0.06, 0.9)
    place(y, sweep_noise(glide(1500, 300, 0.9), 0.9, 1.5) * expd(0.9, 0.3), 0.04)
    return np.tanh(y)

# ---- scream: Wheelman flying fast, on fire, <= 1.6 s
def scream_falling():
    d = 1.5
    f0 = np.interp(tt(d), [0, .12, .6, d], [330, 520, 400, 230])
    y = voice(f0, "a", vib=(6, 0.035), jitter=0.01, drive=1.5)
    return y * env(d, [(0, 0), (.04, 1), (1.1, .9), (1.5, 0)])

def scream_doppler():
    d = 1.6; t = tt(d)
    f0 = 400 - 150 / (1 + np.exp(-(t - 0.75) * 9))
    y = voice(f0, "a", vib=(6.5, 0.03), jitter=0.008, drive=1.4)
    y = y * np.exp(-0.5 * ((t - 0.72) / 0.35) ** 2) + 0.2 * sweep_noise(f0 * 4, d, 1) * np.exp(-0.5 * ((t - 0.72) / 0.4) ** 2)
    return y

def scream_flaming():
    d = 1.5
    f0 = np.interp(tt(d), [0, .1, .5, 1.0, d], [300, 480, 620, 420, 360])
    y = voice(f0, [(0, "a"), (0.4, "ae"), (1, "a")], vib=(7, 0.04), breath=0.3, jitter=0.03, growl=(58, 0.55), drive=3.5)
    y += 0.8 * crackle(d, 80, 420, 5, 0.0007, 1500)
    y += 0.12 * hp(nz(d), 2500)
    return y * env(d, [(0, 0), (.03, 1), (1.2, .9), (1.5, 0)])

def scream_wail():
    d = 1.5
    f0 = glide(950, 190, d, 0.9)
    y = voice(f0, [(0, "e"), (0.3, "a"), (1, "u")], vib=(9, 0.07), breath=0.08, drive=1.2)
    return y * env(d, [(0, 0), (.03, 1), (1.2, .8), (1.5, 0)])

def scream_whee():
    d = 1.4
    f0 = np.interp(tt(d), [0, 1.0, d], [260, 760, 600])
    y = voice(f0, [(0, "o"), (0.2, "e"), (1, "i")], vib=(7, 0.04), breath=0.05, drive=1.2)
    return y * env(d, [(0, 0), (.05, 1), (1.1, .9), (1.4, 0)])

def scream_panic():
    d = 1.6; t = tt(d)
    f0 = np.interp(t, [0, 0.8, d], [280, 420, 330])
    y = voice(f0, "a", vib=(7, 0.04), jitter=0.015, growl=(0, 0), drive=1.8)
    gate = np.where(t < 0.85, 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 6.5 * t)), 1.0)
    gate = lp(gate, 60, 1)
    return y * gate * env(d, [(0, 0), (.03, 1), (1.3, .9), (1.6, 0)])

def scream_deep():
    d = 1.5
    f0 = np.interp(tt(d), [0, .25, .7, d], [120, 190, 210, 110])
    y = voice(f0, [(0, "o"), (0.25, "a"), (1, "ae")], vib=(5.5, 0.03), breath=0.2, jitter=0.02, growl=(40, 0.4), drive=3.0)
    return y * env(d, [(0, 0), (.05, 1), (1.1, .9), (1.5, 0)])

def scream_game(name, r=1.0):
    return lambda: speed(pak_clip(name), r)[:n_of(1.6)]

def scream_rand(name, maxd=1.55):
    return lambda: rand_clip(name, maxd, True)

# ---- boom: crash and explosion, <= 3 s
def boom_big():
    d = 2.8
    y = boom_core(d, 1.4)
    place(y, thump(90, 30, 1.0, 0.3) * 0.5)
    return y

def boom_metal():
    d = 2.6; y = np.zeros(n_of(d))
    place(y, boom_core(1.4, 0.7) * 0.9)
    for at, base, g in [(0.0, 380, .5), (0.05, 610, .4), (0.14, 270, .5), (0.3, 840, .3), (0.5, 450, .25), (0.8, 1100, .15)]:
        place(y, clang(base, 1.6, 0.6) * g, at)
    place(y, sweep_noise(glide(3500, 800, 1.5), 1.5, 3) * env(1.5, [(0, 0), (.1, .5), (1.5, 0)]) * 0.6, 0.1)
    place(y, crackle(1.5, 120, 10, 3, 0.0008, 2000), 0.2)
    return y

def boom_nuke():
    d = 3.0; t = tt(d)
    r = lp(nz(d), 180, 2) * env(d, [(0, 0), (.08, 1), (.6, .9), (3, 0)]) * 3
    r += lp(nz(d), 900) * env(d, [(0, 1), (.6, .15), (1.2, 0), (3, 0)]) * 0.8
    r += osc(glide(60, 24, d, 0.5)) * env(d, [(0, 0), (.04, 1), (2.0, .5), (3, 0)]) * 1.1
    r *= 0.7 + 0.3 * np.sin(2 * np.pi * 9 * t)
    r += crackle(d, 40, 5, 3, 0.002, 400) * env(d, [(0, 0), (0.5, 1), (3, 0)])
    return np.tanh(r)

def boom_gibs():
    d = 2.2; y = np.zeros(n_of(d))
    place(y, boom_core(1.5, 0.6) * 1.0)
    for _ in range(9):
        at = 0.08 + rng.random() * 1.2
        place(y, thump(rng.uniform(120, 220), 55, 0.25, 0.04, 0.6) * rng.uniform(.3, .7), at)
    place(y, crackle(1.8, 400, 15, 4, 0.0006, 2500), 0.05)
    for _ in range(7):
        place(y, clang(rng.uniform(900, 2400), 0.5, 0.15, (1, 2.76, 5.4), (1, .5, .3)) * rng.uniform(.1, .3), 0.1 + rng.random() * 1.3)
    return y

def boom_cartoon():
    d = 2.2; y = np.zeros(n_of(d))
    place(y, boom_core(0.8, 0.35, False) * 1.0)
    f = np.interp(tt(1.0), [0, .25, 1.0], [180, 1800, 120])
    place(y, osc(f) * env(1.0, [(0, 0), (0.02, .7), (0.25, .5), (1.0, 0)]) * 0.6, 0.05)
    for _ in range(14):
        place(y, np.sin(2 * np.pi * rng.uniform(1800, 5200) * tt(0.12)) * expd(0.12, 0.03) * rng.uniform(.1, .3), 0.35 + rng.random() * 1.5)
    place(y, thump(180, 60, 0.3, 0.06) * 0.5, 1.6)
    return y

def boom_wheels():
    d = 3.0; y = np.zeros(n_of(d))
    place(y, boom_core(1.2, 0.8) * 1.0)
    t = 0.45; gap = 0.38; g = 0.9
    while t < 2.8 and gap > 0.035:
        place(y, thump(240, 90, 0.2, 0.05, 0.5) * g, t)
        place(y, clang(330 + rng.uniform(-60, 60), 0.5, 0.2, (1, 2.4, 4.9), (1, .5, .3)) * g * 0.25, t)
        t += gap; gap *= 0.78; g *= 0.8
    place(y, bp(nz(2.3), 1500, 5000) * np.abs(np.sin(2 * np.pi * np.cumsum(np.linspace(6, 20, n_of(2.3))) / SR)) * env(2.3, [(0, .3), (2.3, 0)]) * 0.5, 0.5)
    return y

def boom_firework():
    d = 2.6; y = np.zeros(n_of(d))
    place(y, boom_core(0.9, 0.5, False))
    place(y, thump(130, 40, 0.8, 0.2) * 0.9)
    place(y, crackle(2.2, 500, 0, 5, 0.0005, 3500), 0.1)
    for _ in range(25):
        place(y, np.sin(2 * np.pi * rng.uniform(2500, 7000) * tt(0.1)) * expd(0.1, 0.02) * rng.uniform(.05, .2), 0.1 + rng.random() * 2.0)
    place(y, hp(nz(1.0), 2500) * expd(1.0, 0.4) * 0.35, 0.05)
    return y

def boom_chain():
    d = 2.9; y = np.zeros(n_of(d))
    for at, s, g in [(0.0, 0.4, .7), (0.22, 0.55, .8), (0.5, 0.8, .9), (0.85, 1.6, 1.2)]:
        place(y, boom_core(2.0, s) * g, at)
    return np.tanh(y * 0.9)

def boom_game_raw():  return pak_clip("weapons/r_exp3.wav")

def boom_game_deep():
    d = 3.0; y = np.zeros(n_of(d))
    place(y, speed(pak_clip("weapons/r_exp3.wav"), 0.7))
    place(y, osc(glide(60, 28, 1.6, 0.6)) * expd(1.6, 0.5) * 0.8)
    return y

def boom_game_gibs():
    d = 3.0; y = np.zeros(n_of(d))
    place(y, pak_clip("weapons/r_exp3.wav"))
    place(y, pak_clip("player/gib.wav"), 0.2, 0.9)
    place(y, pak_clip("zombie/z_gib.wav"), 0.4, 0.8)
    place(y, pak_clip("player/tornoff2.wav")[:n_of(1.0)], 0.7, 0.6)
    for at, nm in [(0.9, "weapons/tink1.wav"), (1.25, "weapons/ric1.wav"), (1.6, "weapons/ric3.wav"), (2.0, "weapons/tink1.wav"), (2.3, "weapons/ric2.wav")]:
        place(y, pak_clip(nm), at, 0.6)
    return y

def boom_rand_yay():
    d = 3.0; y = np.zeros(n_of(d))
    place(y, boom_core(1.8, 0.9))
    place(y, rand_clip("YaY.wav", 0.4), 1.3, 0.8)
    return y

def boom_rand_bump():
    d = 2.6; y = np.zeros(n_of(d))
    place(y, boom_core(1.6, 0.8))
    place(y, rand_clip("bump1.wav", 0.7), 0.9, 0.9)
    place(y, rand_clip("bump1.wav", 0.7), 1.5, 0.6)
    return y

SPEC = [
    ("charge", "Turbine spool-up", "synth", charge_turbine),
    ("charge", "Tesla hum + crackle", "synth", charge_tesla),
    ("charge", "Motorbike rev-up", "synth", charge_bike),
    ("charge", "Cartoon wind-up whistle", "synth", charge_windup),
    ("charge", "Capacitor whine + ping", "synth", charge_capacitor),
    ("charge", "Wheelman winds up (voice)", "synth", charge_voice),
    ("charge", "Tire squeal spin-up", "synth", charge_tire),
    ("charge", "Air-raid siren climb", "synth", charge_siren),
    ("charge", "Quake lightning hum, rising", "game", charge_game_lightning),
    ("charge", "Quake fire roar, rising", "game", charge_game_fire),
    ("charge", "Clucking chicken speeds up", "random-sounds", charge_chicken),

    ("shoot", "Mortar thump + whistle", "synth", shoot_mortar),
    ("shoot", "Cartoon pop + whistle", "synth", shoot_popwhistle),
    ("shoot", "Rocket whoosh", "synth", shoot_rocket),
    ("shoot", "Cannon boom + metal ring", "synth", shoot_cannon_ring),
    ("shoot", "Laser pew", "synth", shoot_laser),
    ("shoot", "Sonic crack + fly-by", "synth", shoot_sonic),
    ("shoot", "Champagne cork + fizz", "synth", shoot_cork),
    ("shoot", "Spring BOING launch", "synth", shoot_boing),
    ("shoot", "Quake rocket launch", "game", shoot_game_rocket),
    ("shoot", "Quake grenade launcher", "game", shoot_game_grenade),
    ("shoot", "Deep shotgun + rocket", "game", shoot_game_deep),
    ("shoot", "Thump + YaY!", "random-sounds", shoot_rand_yay),

    ("scream", "AAAAH falling", "synth", scream_falling),
    ("scream", "Doppler fly-by AAAH", "synth", scream_doppler),
    ("scream", "Flaming shriek", "synth", scream_flaming),
    ("scream", "Cartoon falling wail", "synth", scream_wail),
    ("scream", "WHEEEE!", "synth", scream_whee),
    ("scream", "Panic a-a-a-AAAH", "synth", scream_panic),
    ("scream", "Deep manly WOAAAH", "synth", scream_deep),
    ("scream", "Quake gib scream", "game", scream_game("player/udeath.wav")),
    ("scream", "Quake death yell, sped up", "game", scream_game("player/death3.wav", 1.25)),
    ("scream", "uuaaahh", "random-sounds", scream_rand("uuaaahh.wav")),
    ("scream", "quakeahh", "random-sounds", scream_rand("quakeahh.wav")),
    ("scream", "wewe", "random-sounds", scream_rand("wewe.wav")),
    ("scream", "yipikiya", "random-sounds", scream_rand("yipikiya.wav")),
    ("scream", "dumbhowl", "random-sounds", scream_rand("dumbhowl.wav")),

    ("boom", "Big boom, sub-bass tail", "synth", boom_big),
    ("boom", "Metal crash + clangs", "synth", boom_metal),
    ("boom", "Nuke rumble", "synth", boom_nuke),
    ("boom", "Gibs, thuds + sparks", "synth", boom_gibs),
    ("boom", "Cartoon BOOM + debris tinkle", "synth", boom_cartoon),
    ("boom", "Wheels bounce away", "synth", boom_wheels),
    ("boom", "Firework burst", "synth", boom_firework),
    ("boom", "Chain of explosions", "synth", boom_chain),
    ("boom", "Quake rocket explosion", "game", boom_game_raw),
    ("boom", "Quake explosion, deep", "game", boom_game_deep),
    ("boom", "Quake blast + gibs + ricochets", "game", boom_game_gibs),
    ("boom", "Boom, then YaY!", "random-sounds", boom_rand_yay),
    ("boom", "Boom + bump thuds", "random-sounds", boom_rand_bump),
]

# ------------------------------------------------------------------ output
def write_wav(path, x):
    wavfile.write(path, SR, np.clip(np.round(x * 32767), -32768, 32767).astype("<i2"))

def build_clips():
    shutil.rmtree(CLIP_DIR, ignore_errors=True)
    os.makedirs(CLIP_DIR); os.makedirs(GAME_DIR, exist_ok=True)
    counts = {}; meta = []
    for slot, label, source, fn in SPEC:
        try:
            x = fn()
        except Exception as e:
            print("SKIPPED", slot, label, "->", e); continue
        add(slot, label, source, x)
        _, _, _, x = CLIPS[-1]
        counts[slot] = counts.get(slot, 0) + 1
        cid = "%s_%02d" % (slot, counts[slot])
        write_wav(os.path.join(CLIP_DIR, cid + ".wav"), x)
        meta.append({"id": cid, "slot": slot, "label": label, "source": source, "dur": round(len(x) / SR, 2),
                     "default": DEFAULTS[slot] == label})
    for slot, label in DEFAULTS.items():
        if not any(m["slot"] == slot and m["default"] for m in meta):
            sys.exit("default %r not found for slot %s" % (label, slot))
    for m in meta:
        if m["default"]:
            shutil.copyfile(os.path.join(CLIP_DIR, m["id"] + ".wav"), os.path.join(GAME_DIR, "wc_%s.wav" % m["slot"]))
    with open(os.path.join(VOTE_DIR, "clips.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return meta

def mp3_b64(wav):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", "22050", "-codec:a", "libmp3lame",
                          "-b:a", "56k", "-f", "mp3", "-"], capture_output=True, check=True).stdout
    return "data:audio/mpeg;base64," + base64.b64encode(out).decode()

def build_page(meta):
    audio = {m["id"]: mp3_b64(os.path.join(CLIP_DIR, m["id"] + ".wav")) for m in meta}
    html = PAGE_TEMPLATE.replace("/*CLIPS*/[]", json.dumps(meta)).replace("/*AUDIO*/{}", json.dumps(audio))
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(html)
    print("page %.1f MB" % (os.path.getsize(PAGE) / 1e6))

PAGE_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wheelman Cannon Sounds</title>
<style>
:root{--bg:#f6f1e6;--card:#fffdf7;--ink:#2a2118;--mute:#6f6556;--line:#dcd2bd;--acc:#d9531e;--acc-ink:#fff;--pick:#fdeccb;--star:#d99a00;--chip:#efe6d2;--good:#2f8a3d;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root{--bg:#1a1613;--card:#241e19;--ink:#f0e8dc;--mute:#a39786;--line:#3a3128;--acc:#ff7a3d;--acc-ink:#1c0e05;--pick:#4a3515;--star:#ffc233;--chip:#2e261f;--good:#5cc86b;--bad:#ff7a70}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.4 system-ui,Segoe UI,sans-serif}
header{padding:20px 16px 8px;max-width:1100px;margin:0 auto}
h1{margin:0 0 4px;font-size:26px}
header p{margin:0;color:var(--mute);max-width:72ch}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:8px 16px}
.bar-in{max-width:1100px;margin:0 auto}
.sum{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px}
.sl{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:5px 9px;min-width:0}
.sl b{display:block;font-size:12px;color:var(--mute);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.sl .pk{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;cursor:pointer}
.sl .pk.none{color:var(--mute);font-weight:400;font-style:italic;cursor:default}
.sl small{color:var(--mute)}
.acts{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
button{font:inherit;color:inherit;cursor:pointer}
.act{border:1px solid var(--line);background:var(--card);border-radius:8px;padding:6px 12px}
.act.primary{background:var(--acc);color:var(--acc-ink);border-color:var(--acc)}
.hint{color:var(--mute);font-size:13px;margin-left:auto}
main{max-width:1100px;margin:0 auto;padding:6px 16px 60px}
section.slot{padding-top:14px}
section.slot h2{margin:0;font-size:21px}
section.slot p{margin:2px 0 10px;color:var(--mute)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}
.clip{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:grid;grid-template-columns:44px 1fr;gap:4px 10px;align-items:center}
.clip.picked{background:var(--pick);border-color:var(--star)}
.clip.playing{outline:2px solid var(--acc)}
.play{width:44px;height:44px;border-radius:50%;border:none;background:var(--acc);color:var(--acc-ink);font-size:18px;grid-row:1/3}
.lab{font-weight:600;word-break:break-word}
.meta{color:var(--mute);font-size:12.5px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.tag{border:1px solid var(--line);background:var(--chip);border-radius:999px;padding:0 8px;font-size:12px}
.tag.def{border-color:var(--acc);color:var(--acc)}
.prog{grid-column:2;height:4px;background:var(--line);border-radius:2px;overflow:hidden}
.prog i{display:block;height:100%;width:0;background:var(--acc)}
.bt{grid-column:1/3;display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.bt button{border:1px solid var(--line);background:var(--chip);border-radius:8px;padding:5px 10px;font-size:14px;min-height:34px}
.bt button[data-k=like][aria-pressed=true]{background:var(--good);color:#fff;border-color:var(--good)}
.bt button[data-k=dislike][aria-pressed=true]{background:var(--bad);color:#fff;border-color:var(--bad)}
.bt button[data-k=pick]{margin-left:auto}
.bt button[data-k=pick][aria-pressed=true]{background:var(--star);color:#241a00;border-color:var(--star);font-weight:600}
.toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:8px 14px;border-radius:8px;opacity:0;transition:opacity .2s;pointer-events:none}
.toast.on{opacity:1}
@media (max-width:640px){
 .sum{grid-template-columns:repeat(2,1fr);gap:6px;margin-bottom:6px}
 .sl{padding:3px 8px}.sl .pk{font-size:13px}
 h1{font-size:22px}.hint{display:none}
 .grid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<header>
  <h1>Wheelman Cannon: pick the sounds</h1>
  <p>Hold fire to charge, release, and a flaming screaming Wheelman rockets along the floor until he crashes and blows up. Four sounds to choose. Play the candidates, give a thumbs up or down, and press "Use this one" on your favourite in each section (only one per section). Votes save in your browser as you go; press Download votes or Copy votes when you are done. Esc stops the sound.</p>
</header>

<div class="bar"><div class="bar-in">
  <div class="sum" id="sum"></div>
  <div class="acts">
    <button class="act primary" id="dl">Download votes</button>
    <button class="act" id="cp">Copy votes</button>
    <button class="act" id="rs">Reset</button>
    <span class="hint">Esc = stop</span>
  </div>
</div></div>

<main id="main"></main>
<div class="toast" id="toast"></div>

<script>
const CLIPS = /*CLIPS*/[];
const AUDIO = /*AUDIO*/{};
const SLOTS = [
  {k:"charge", name:"Charge-up",        hint:"Heard while you hold fire. The gun builds up for 1.5 seconds, so something that rises in pitch and intensity fits best."},
  {k:"shoot",  name:"Blast-off",        hint:"The cannon firing the Wheelman."},
  {k:"scream", name:"Wheelman scream",  hint:"He screams while flying super fast and on fire. It re-triggers while he flies."},
  {k:"boom",   name:"Crash explosion",  hint:"He hits a wall and blows up in wheels, bars, gibs and sparks."}
];
const SRC = {"synth":"synth", "game":"from the game", "random-sounds":"your Random Sounds"};
const STORE = "wcannon_sound_votes_v1";
let votes = {pick:{}, like:{}, dislike:{}};
try { const v = JSON.parse(localStorage.getItem(STORE) || "null"); if (v && v.pick) votes = {pick:v.pick||{}, like:v.like||{}, dislike:v.dislike||{}}; } catch (e) {}
let playing = null;
const audio = new Audio();
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const save = () => { try { localStorage.setItem(STORE, JSON.stringify(votes)); } catch (e) {} };
const byId = id => CLIPS.find(c => c.id === id);
const inSlot = k => CLIPS.filter(c => c.slot === k);

function act(id, kind) {
  const c = byId(id), k = c.slot;
  if (kind === "pick") {
    if (votes.pick[k] === id) delete votes.pick[k]; else votes.pick[k] = id;
  } else {
    const other = kind === "like" ? "dislike" : "like";
    if (votes[kind][id]) delete votes[kind][id]; else { votes[kind][id] = 1; delete votes[other][id]; }
  }
  save(); render();
}

function play(id) {
  if (playing === id && !audio.paused) { audio.pause(); return; }
  playing = id;
  audio.src = AUDIO[id];
  audio.play().catch(() => toast("Could not play that one"));
  paint();
}
audio.addEventListener("ended", () => { playing = null; paint(); });
audio.addEventListener("pause", paint);
audio.addEventListener("play", paint);
audio.addEventListener("timeupdate", () => {
  const bar = document.querySelector(".clip.playing .prog i");
  if (bar && audio.duration) bar.style.width = (100 * audio.currentTime / audio.duration) + "%";
});

function paint() {
  document.querySelectorAll(".clip").forEach(el => {
    const on = el.dataset.id === playing && !audio.paused;
    el.classList.toggle("playing", on);
    el.querySelector(".play").innerHTML = on ? "&#10074;&#10074;" : "&#9654;";
    if (!on) el.querySelector(".prog i").style.width = "0";
  });
}

function render() {
  $("#sum").innerHTML = SLOTS.map(s => {
    const id = votes.pick[s.k], c = id && byId(id);
    const likes = inSlot(s.k).filter(x => votes.like[x.id]).length;
    return `<div class="sl"><b>${esc(s.name)}</b>` +
      (c ? `<span class="pk" data-play="${c.id}" title="${esc(c.label)}">&#9733; ${esc(c.label)}</span>` : `<span class="pk none">no pick yet</span>`) +
      `<small>&#128077; ${likes}</small></div>`;
  }).join("");
  $("#main").innerHTML = SLOTS.map(s => `<section class="slot" id="s-${s.k}"><h2>${esc(s.name)}</h2><p>${esc(s.hint)}</p><div class="grid">` +
    inSlot(s.k).map(c => {
      const picked = votes.pick[c.id.split("_")[0]] === c.id, on = c.id === playing && !audio.paused;
      return `<div class="clip${picked ? " picked" : ""}${on ? " playing" : ""}" data-id="${c.id}">
        <button class="play" data-play="${c.id}" aria-label="Play ${esc(c.label)}">${on ? "&#10074;&#10074;" : "&#9654;"}</button>
        <div><div class="lab">${esc(c.label)}</div>
          <div class="meta"><span class="tag">${SRC[c.source] || esc(c.source)}</span><span>${c.dur.toFixed(1)} s</span>${c.default ? '<span class="tag def">game default</span>' : ""}</div></div>
        <div class="prog"><i></i></div>
        <div class="bt">
          <button data-act="${c.id}:like" data-k="like" aria-pressed="${!!votes.like[c.id]}" aria-label="Like">&#128077;</button>
          <button data-act="${c.id}:dislike" data-k="dislike" aria-pressed="${!!votes.dislike[c.id]}" aria-label="Dislike">&#128078;</button>
          <button data-act="${c.id}:pick" data-k="pick" aria-pressed="${picked}">&#9733; ${picked ? "Your pick" : "Use this one"}</button>
        </div></div>`;
    }).join("") + `</div></section>`).join("");
}

function result() {
  const out = {};
  SLOTS.forEach(s => {
    const ids = inSlot(s.k).map(c => c.id);
    out[s.k] = {pick: votes.pick[s.k] || null, likes: ids.filter(i => votes.like[i]), dislikes: ids.filter(i => votes.dislike[i])};
  });
  return out;
}

function toast(t) { const el = $("#toast"); el.textContent = t; el.classList.add("on"); setTimeout(() => el.classList.remove("on"), 1800); }

document.addEventListener("click", e => {
  const p = e.target.closest("[data-play]");
  if (p) { play(p.dataset.play); return; }
  const a = e.target.closest("[data-act]");
  if (a) { const [id, kind] = a.dataset.act.split(":"); act(id, kind); }
});
document.addEventListener("keydown", e => { if (e.key === "Escape") { audio.pause(); audio.currentTime = 0; } });
$("#dl").onclick = () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(result(), null, 1)], {type: "application/json"}));
  a.download = "votes.json"; a.click(); toast("votes.json downloaded");
};
$("#cp").onclick = async () => {
  const text = JSON.stringify(result(), null, 1);
  try { await navigator.clipboard.writeText(text); toast("Votes copied"); }
  catch (e) { const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); toast("Votes copied"); }
};
$("#rs").onclick = () => { if (confirm("Clear every vote?")) { votes = {pick:{}, like:{}, dislike:{}}; save(); render(); } };
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    meta = build_clips()
    for slot in LIMIT:
        print("--", slot)
        for m in meta:
            if m["slot"] == slot:
                print("  %-10s %-34s %-14s %.2fs%s" % (m["id"], m["label"], m["source"], m["dur"], "  [default]" if m["default"] else ""))
    build_page(meta)
