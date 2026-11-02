"""Bounce-sound candidates for the CCC gun, built from the "I can't see!" clip (ccc.mp3, 0.95 s), for the preview page
source/ccc_sound_preview/index.html. Every file is 22050 Hz mono 16-bit, so whichever one wins can go straight into
BakersfieldQuake/sound/ccc/.

  fire.wav        the gun's own fire sound (hipweap/laserg.wav from quake15/q15.pk3), so the page shoots like the game
  oldric.wav      the old red-laser ricochet (hipweap/laserric.wav), for comparison
  die.wav         enforcer/enfstop.wav: a bolt plays it on the same channel when it dies, which cuts its bounce sound off
  synth.wav       the current CCC bounce (sound/ccc/bounce.wav, from make_ccc_sounds.py)
  v0_native.wav   the clip as it is
  v0_native2.wav  "native 2.0": the clip cut where "see!" ends, without the little laugh at the very end
  v1_fast.wav     sped up 1.8x, chipmunk pitch: the whole line in half a second
  v2_laser.wav    a laser ricochet zap with the line faint underneath, sped up and quiet
  v3_see.wav      only the "see!", pitched up: a tiny blip
  v4_radio.wav    the line squeezed through a walkie-talkie: thin, quicker, a little echo
  v5_zap.wav      a clean laser zap with no voice: the rationed version plays this on most bounces...
  v5_voice.wav    ...and the line (slightly sped up) at most once every so often (the rule is in the page)
  f2_laserghost.wav  a SHOOT candidate: the gun's laser fire with the line faint underneath. The other shoot candidates
                  reuse the files above (v0, v1, v3, v4, and v5_voice once per trigger pull); the page says which.

It also puts all of them (base64) into <outdir>/../index.html, between its <!--AUDIO--> markers, together with every
custom sound of the mod (BakersfieldQuake/sound, minus the calc song slices) for the page's "any mod sound" menu.
python make_ccc_preview_sounds.py <ccc.mp3> <outdir>      (needs ffmpeg on PATH and numpy)"""
import base64
import os
import subprocess
import sys
import tempfile
import wave
import zipfile

import numpy as np

RATE = 22050
PK3 = r"G:\Quake\Combat\quake15\q15.pk3"
SYNTH = r"G:\Quake\Combat\BakersfieldQuake\sound\ccc\bounce.wav"
GAME_SOUND = r"G:\Quake\Combat\BakersfieldQuake\sound"
NATIVE2_END = 0.80          # "see!" ends here; the laugh starts at about 0.81 s


def ff(src, dst, af=None):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16", dst]
    subprocess.run(cmd, check=True)


def load(path):
    with wave.open(path) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0


def save(path, x, peak=0.85):
    m = np.abs(x).max() or 1.0
    x = x / m * peak
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    print("wrote %-16s %.2fs" % (os.path.basename(path), len(x) / RATE))


def fade(x, a=0.003, b=0.02):
    x = x.copy()
    na, nb = int(RATE * a), int(RATE * b)
    if na:
        x[:na] *= np.linspace(0, 1, na)
    if nb:
        x[-nb:] *= np.linspace(1, 0, nb)
    return x


def zap(dur=0.16, f0=2600.0, f1=420.0, seed=3):
    """a laser ricochet: a fast falling sweep with a buzz on it and a tick of noise at the start"""
    n = int(RATE * dur)
    t = np.arange(n) / RATE
    f = f1 + (f0 - f1) * np.exp(-t / (dur * 0.28))
    ph = 2 * np.pi * np.cumsum(f) / RATE
    tone = np.sin(ph) + 0.3 * np.sign(np.sin(ph)) * 0.5 + 0.2 * np.sin(2 * ph + 0.4)
    env = np.exp(-t / (dur * 0.35)) * np.minimum(1, t / 0.002)
    noise = np.random.default_rng(seed).uniform(-1, 1, n) * np.exp(-t / 0.006)
    return fade(env * tone + 0.6 * noise, 0.0, 0.01)


def main(src, out):
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp()
    w = lambda name: os.path.join(out, name)
    t = lambda name: os.path.join(tmp, name)

    z = zipfile.ZipFile(PK3)
    for inner, name in (("sound/hipweap/laserg.wav", "fire.wav"), ("sound/hipweap/laserric.wav", "oldric.wav"),
                        ("sound/enforcer/enfstop.wav", "die.wav")):
        open(t(name), "wb").write(z.read(inner))
        ff(t(name), w(name))
    ff(SYNTH, w("synth.wav"))

    # v0: as it is (the end is still loud, so a short fade keeps it from clicking)
    ff(src, t("native.wav"))
    native = load(t("native.wav"))
    save(w("v0_native.wav"), fade(native, 0.0, 0.03), peak=0.9)
    # native 2.0: the same, cut where "see!" ends (0.80 s), before the little laugh that starts at 0.81 s
    save(w("v0_native2.wav"), fade(native[:int(RATE * NATIVE2_END)], 0.0, 0.025), peak=0.9)

    # v1: 1.8x faster and higher, like a tape sped up
    ff(src, t("fast.wav"), "asetrate=44100*1.8,aresample=44100")
    save(w("v1_fast.wav"), fade(load(t("fast.wav")), 0.0, 0.03))

    # v2: the zap, with the line underneath at about a fifth of the level (1.6x faster, a bit higher, dulled)
    ff(src, t("ghost.wav"), "asetrate=44100*1.25,aresample=44100,atempo=1.3,lowpass=f=2500,highpass=f=250")
    ghost = fade(load(t("ghost.wav")), 0.0, 0.08)
    z2 = zap(0.18)
    n = max(len(z2), len(ghost))
    mix = np.zeros(n)
    mix[:len(z2)] += z2
    mix[:len(ghost)] += 0.22 * ghost / (np.abs(ghost).max() or 1)
    save(w("v2_laser.wav"), mix)

    # v3: only "see!" (0.62 - 0.82 s), up a few semitones: a short bright blip
    ff(src, t("see.wav"), "atrim=0.62:0.82,asetrate=44100*1.3,aresample=44100")
    save(w("v3_see.wav"), fade(load(t("see.wav")), 0.004, 0.04))

    # v4: walkie-talkie: quicker, telephone band, a little crunch and a short slap echo
    ff(src, t("radio.wav"), "atempo=1.45,highpass=f=600,lowpass=f=2600,acrusher=bits=7:mix=0.6:mode=log,aecho=0.7:0.4:45:0.25")
    save(w("v4_radio.wav"), fade(load(t("radio.wav")), 0.0, 0.03), peak=0.7)

    # v5: a clean zap for most bounces, and the line itself (1.2x) now and then
    save(w("v5_zap.wav"), zap(0.12, 3000.0, 700.0, seed=5), peak=0.6)
    ff(src, t("voice.wav"), "asetrate=44100*1.2,aresample=44100")
    save(w("v5_voice.wav"), fade(load(t("voice.wav")), 0.0, 0.03))

    # f2 (a SHOOT sound): the gun's own laser fire with the line faint underneath, sped up so it is over with the laser
    fire = load(w("fire.wav"))
    n = max(len(fire), len(ghost))
    mix = np.zeros(n)
    mix[:len(fire)] += fire / (np.abs(fire).max() or 1)
    mix[:len(ghost)] += 0.3 * ghost / (np.abs(ghost).max() or 1)
    save(w("f2_laserghost.wav"), fade(mix, 0.0, 0.03))

    # the page opens straight from disk (file://), where fetch() of a .wav is blocked: put the sounds inside it, between
    # its <!--AUDIO--> markers, so it is one file that works anywhere
    lines = ["<script>", "window.CCC_AUDIO = {"]
    for name in sorted(os.listdir(out)):
        if name.endswith(".wav"):
            lines.append('"%s": "%s",' % (name[:-4], base64.b64encode(open(w(name), "rb").read()).decode("ascii")))
    lines += ["};"]
    # every custom sound of the mod (BakersfieldQuake/sound, except the calc song slices) as it is, to try as a bounce
    lines.append("window.CCC_GAME = {")
    for root, dirs, files in os.walk(GAME_SOUND):
        dirs.sort()
        if os.path.basename(root) == "calc":
            continue
        for f in sorted(files):
            if f.lower().endswith(".wav"):
                rel = os.path.relpath(os.path.join(root, f), GAME_SOUND).replace("\\", "/")
                lines.append('"%s": "%s",' % (rel, base64.b64encode(open(os.path.join(root, f), "rb").read()).decode("ascii")))
    lines += ["};", "</script>"]
    page = os.path.join(os.path.dirname(os.path.abspath(out)), "index.html")
    html = open(page, encoding="utf-8").read()
    a, b = html.index("<!--AUDIO-->") + len("<!--AUDIO-->"), html.index("<!--/AUDIO-->")
    open(page, "w", encoding="utf-8").write(html[:a] + "\n" + "\n".join(lines) + "\n" + html[b:])
    print("put the sounds into", page)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
