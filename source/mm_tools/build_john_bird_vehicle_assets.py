"""Build all audio, skin, shader, and 3D feather-debris assets for the
Flyable Winged Breezy-Hair John Vehicle ('misc_vehicle_johnbird'):

  1. sound/john_bird/flap1..4.wav, takeoff.wav, swoop.wav, feather_hit.wav, shootdown.wav
     (22050 Hz, 16-bit mono PCM WAV)
  2. sound/john_bird/jv_fly00..13.wav + jv_hurt.wav
     (14 curated "John" voice clips downmixed & loudness-leveled to 22050 Hz 16-bit mono WAV)
  3. progs/john_bird_wings_white.png, progs/john_bird_wings_hurt.png, progs/john_bird_wings_hurt_glow.png
  4. progs/john_bird_head.md3_0.skin, _1.skin, _2.skin & scripts/john_bird.shader
  5. progs/john_bird_feather.md3 (curved 3D feather debris mesh for rocket hits & 5-rocket shootdown)
"""
import json
import math
import os
import sys
import wave

import numpy as np
from PIL import Image
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS_DIR = os.path.join(ROOT, "progs")
SCRIPTS_DIR = os.path.join(ROOT, "scripts")
SND_DIR = os.path.join(ROOT, "sound", "john_bird")
CELEB_DIR = os.path.join(ROOT, "source", "grenade_sound_vote", "audio", "celeb")
OUT_DIR = os.path.join(HERE, "out", "john_bird")

SR = 22050


def save_wav_mono16(path, samples, sr=SR):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = np.asarray(samples, dtype=np.float64)
    # Remove DC offset
    if len(x) > 0:
        x = x - np.mean(x)
    # Short 4ms fade-in/out to prevent clicks
    fade = min(int(0.004 * sr), len(x) // 4)
    if fade > 1:
        ramp = np.linspace(0.0, 1.0, fade)
        x[:fade] *= ramp
        x[-fade:] *= ramp[::-1]
    x = np.clip(x, -0.98, 0.98)
    pcm = np.round(x * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def load_wav_mono_resampled(path, target_sr=SR):
    with wave.open(path, "rb") as w:
        sr, ch, sw, nf = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(nf)
    if sw == 1:
        arr = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    elif sw == 2:
        arr = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    else:
        raise ValueError(f"Unsupported sample width {sw} in {path}")
    if ch > 1:
        arr = arr.reshape(-1, ch).mean(axis=1)
    if sr != target_sr:
        g = math.gcd(sr, target_sr)
        arr = signal.resample_poly(arr, target_sr // g, sr // g)
    return arr


def master_voice_clip(arr, target_rms=0.25):
    # Trim leading/trailing dead air below -46 dB with 18ms pad
    thr = 0.005
    idx = np.where(np.abs(arr) > thr)[0]
    if len(idx) > 16:
        pad = int(0.018 * SR)
        i0 = max(0, int(idx[0]) - pad)
        i1 = min(len(arr), int(idx[-1]) + pad)
        arr = arr[i0:i1]
    # Gentle 75 Hz high-pass so voice never muddies wing-flap bass
    b, a = signal.butter(2, 75.0 / (0.5 * SR), btype="highpass")
    arr = signal.filtfilt(b, a, arr)
    rms = math.sqrt(float(np.mean(arr * arr)) + 1e-12)
    gain = min(3.2, target_rms / rms)
    y = arr * gain
    # Smooth soft-knee limiter around +/-0.94
    y = 0.94 * np.tanh(y / 0.94)
    return y


def synth_wing_flap(seed, dur=0.29, pitch_mul=1.0, heavy=1.0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR

    # 1. Deep chesty downstroke air displacement thump (sweeps 125 -> 46 Hz)
    f0 = 128.0 * pitch_mul
    f1 = 44.0 * pitch_mul
    phase = 2.0 * math.pi * (f1 * t + (f0 - f1) * 0.065 * (1.0 - np.exp(-t / 0.065)))
    env_thump = (t / 0.024) * np.exp(1.0 - t / 0.024)
    env_thump = np.clip(env_thump, 0.0, 1.5) * np.exp(-np.maximum(0.0, t - 0.03) / 0.085)
    thump = 0.48 * heavy * np.sin(phase) * env_thump

    # 2. Aerodynamic broad wing-whoosh (time-varying bandpass 170..680 Hz)
    wn = rng.standard_normal(n)
    b_lo, a_lo = signal.butter(3, [140.0 * pitch_mul / (0.5 * SR), min(0.92, 760.0 * pitch_mul / (0.5 * SR))], btype="band")
    whoosh_raw = signal.lfilter(b_lo, a_lo, wn)
    t_pk = 0.068 / pitch_mul
    env_whoosh = np.exp(-0.5 * ((t - t_pk) / (0.048 + 0.015 * heavy)) ** 2)
    # Subtle recovery upstroke air puff
    env_up = 0.28 * np.exp(-0.5 * ((t - (t_pk + 0.105)) / 0.036) ** 2)
    whoosh = 0.85 * whoosh_raw * (env_whoosh + env_up)

    # 3. Slotted primary feather quill rustle & snap (crisp staggered micro-transients)
    b_hi, a_hi = signal.butter(2, [950.0 / (0.5 * SR), 4600.0 / (0.5 * SR)], btype="band")
    rustle_src = signal.lfilter(b_hi, a_hi, rng.standard_normal(n))
    env_rustle = np.zeros(n, dtype=np.float64)
    for k in range(6):
        tk = 0.026 + k * 0.014 + rng.uniform(-0.003, 0.003)
        wk = 0.008 + 0.003 * (k % 2)
        ak = (0.85 - 0.09 * k) * rng.uniform(0.8, 1.15)
        env_rustle += ak * np.exp(-0.5 * ((t - tk) / wk) ** 2)
    # Upstroke feather tip flick
    env_rustle += 0.35 * np.exp(-0.5 * ((t - (t_pk + 0.098)) / 0.014) ** 2)
    rustle = 0.56 * rustle_src * env_rustle

    mix = thump + whoosh + rustle
    pk = float(np.max(np.abs(mix))) + 1e-9
    return 0.88 * (mix / pk)


def synth_takeoff():
    # Two rapid powerful wing-claps + breezy upward gust
    n = int(0.56 * SR)
    out = np.zeros(n, dtype=np.float64)
    f1 = synth_wing_flap(101, dur=0.28, pitch_mul=1.08, heavy=1.25)
    f2 = synth_wing_flap(202, dur=0.30, pitch_mul=1.18, heavy=1.10)
    out[:len(f1)] += f1
    off2 = int(0.18 * SR)
    out[off2:off2 + len(f2)] += 0.92 * f2

    rng = np.random.default_rng(303)
    t = np.arange(n, dtype=np.float64) / SR
    b, a = signal.butter(2, [320.0 / (0.5 * SR), 2200.0 / (0.5 * SR)], btype="band")
    gust = signal.lfilter(b, a, rng.standard_normal(n)) * np.sin(math.pi * np.clip(t / 0.54, 0, 1)) ** 1.3
    out += 0.28 * gust
    return 0.92 * np.tanh(out / (float(np.max(np.abs(out))) + 1e-9) * 1.15)


def synth_swoop():
    # High-speed peregrine falcon dive wind-shear + aerodynamic whistle
    dur = 0.78
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    rng = np.random.default_rng(404)

    snap = synth_wing_flap(405, dur=0.24, pitch_mul=1.28, heavy=1.15)
    out = np.zeros(n, dtype=np.float64)
    out[:len(snap)] += 0.75 * snap

    # Sweeping wind-rush
    wn = rng.standard_normal(n)
    b1, a1 = signal.butter(2, [260.0 / (0.5 * SR), 1850.0 / (0.5 * SR)], btype="band")
    b2, a2 = signal.butter(2, [1400.0 / (0.5 * SR), 4800.0 / (0.5 * SR)], btype="band")
    env = np.sin(math.pi * np.clip(t / dur, 0.0, 1.0)) ** 0.85 * np.exp(-t * 1.15) * 1.8
    shear = 0.55 * signal.lfilter(b1, a1, wn) * env + 0.32 * signal.lfilter(b2, a2, wn) * (env ** 1.3)

    # Subtle falcon air-whistle harmonic sweeping down slightly as he streaks past
    f_wh = 1180.0 - 420.0 * (t / dur) + 28.0 * np.sin(2.0 * math.pi * 14.0 * t)
    ph = 2.0 * math.pi * np.cumsum(f_wh) / SR
    whistle = 0.11 * np.sin(ph) * np.exp(-0.5 * ((t - 0.22) / 0.16) ** 2)

    out += shear + whistle
    return 0.90 * (out / (float(np.max(np.abs(out))) + 1e-9))


def synth_feather_hit():
    # Punchy rocket-on-plumage thud + frantic flurry of scattering feathers
    dur = 0.48
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    rng = np.random.default_rng(505)

    # Impact punch
    ph = 2.0 * math.pi * (55.0 * t + 110.0 * 0.035 * (1.0 - np.exp(-t / 0.035)))
    punch = 0.85 * np.sin(ph) * np.exp(-t / 0.075)

    # Frantic feather scatter
    b, a = signal.butter(2, [850.0 / (0.5 * SR), 5200.0 / (0.5 * SR)], btype="band")
    noise = signal.lfilter(b, a, rng.standard_normal(n))
    flurry = np.zeros(n, dtype=np.float64)
    for k in range(11):
        tk = 0.015 + k * 0.034 + rng.uniform(-0.006, 0.006)
        flurry += (0.95 - 0.06 * k) * np.exp(-0.5 * ((t - tk) / 0.011) ** 2)
    out = punch + 0.72 * noise * flurry
    return 0.92 * np.tanh(out / (float(np.max(np.abs(out))) + 1e-9) * 1.25)


def synth_shootdown(reooow_arr, bye_arr):
    # Dramatic 5th-rocket shootdown: explosive avian screech/John cry + cascading feathers!
    dur = 1.32
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    rng = np.random.default_rng(606)

    out = np.zeros(n, dtype=np.float64)
    # Layer John's "Reooow!" pitched slightly downward in comedic defeat + "Goodbye!"
    r_len = min(n, len(reooow_arr))
    out[:r_len] += 0.85 * reooow_arr[:r_len] * np.exp(-np.maximum(0.0, t[:r_len] - 0.55) / 0.35)
    b_off = int(0.58 * SR)
    b_len = min(n - b_off, len(bye_arr))
    if b_len > 0:
        out[b_off:b_off + b_len] += 0.88 * bye_arr[:b_len]

    # Cascading blast + feather explosion
    ph = 2.0 * math.pi * (38.0 * t + 135.0 * 0.06 * (1.0 - np.exp(-t / 0.06)))
    boom = 0.75 * np.sin(ph) * np.exp(-t / 0.16)
    b_lo, a_lo = signal.butter(2, [90.0 / (0.5 * SR), 900.0 / (0.5 * SR)], btype="band")
    blast = 0.65 * signal.lfilter(b_lo, a_lo, rng.standard_normal(n)) * np.exp(-t / 0.28)

    b_hi, a_hi = signal.butter(2, [1100.0 / (0.5 * SR), 5000.0 / (0.5 * SR)], btype="band")
    f_noise = signal.lfilter(b_hi, a_hi, rng.standard_normal(n))
    cascade = np.zeros(n, dtype=np.float64)
    for k in range(18):
        tk = 0.04 + k * 0.058 + rng.uniform(-0.01, 0.01)
        cascade += max(0.18, 0.85 - 0.04 * k) * np.exp(-0.5 * ((t - tk) / 0.015) ** 2)

    out += boom + blast + 0.48 * f_noise * cascade
    return 0.94 * np.tanh(out / (float(np.max(np.abs(out))) + 1e-9) * 1.35)


def build_hurt_wing_textures():
    src = np.asarray(Image.open(os.path.join(PROGS_DIR, "john_bird_wings.png")).convert("RGB"), dtype=np.float32)
    h, w, _ = src.shape
    yy, xx = np.meshgrid(np.linspace(0.0, 1.0, h), np.linspace(0.0, 1.0, w), indexing="ij")

    # Procedural soot & singed feather-tip mask (stronger near primary tips & trailing edge)
    rng = np.random.default_rng(707)
    coarse = rng.uniform(0.0, 1.0, (32, 32))
    noise = np.asarray(
        Image.fromarray((coarse * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BILINEAR),
        dtype=np.float32,
    ) / 255.0
    streaks = 0.5 + 0.5 * np.sin(xx * 58.0 + noise * 5.0)
    scorch = np.clip((0.35 + 0.55 * yy) * (0.45 + 0.75 * noise) * (0.65 + 0.35 * streaks), 0.0, 1.0)
    scorch = scorch ** 1.35

    char_rgb = np.array([28.0, 21.0, 18.0], dtype=np.float32)
    ash_rgb = np.array([72.0, 62.0, 56.0], dtype=np.float32)
    hurt = src * (1.0 - 0.74 * scorch[..., None]) + char_rgb * (0.58 * scorch[..., None]) + ash_rgb * (0.16 * scorch[..., None])

    # Subtle glowing orange-amber ember cracks on the most singed tips (after 3-4 rockets!)
    ember_mask = np.clip((scorch - 0.62) / 0.32, 0.0, 1.0) ** 1.8
    ember_col = np.array([255.0, 112.0, 24.0], dtype=np.float32)
    hurt = np.clip(hurt + ember_col * (0.42 * ember_mask[..., None]), 0.0, 255.0)
    glow = np.clip(ember_col * (0.85 * ember_mask[..., None]), 0.0, 255.0)

    Image.fromarray(hurt.astype(np.uint8)).save(os.path.join(PROGS_DIR, "john_bird_wings_hurt.png"), optimize=True)
    Image.fromarray(glow.astype(np.uint8)).save(os.path.join(PROGS_DIR, "john_bird_wings_hurt_glow.png"), optimize=True)

    white_src = os.path.join(OUT_DIR, "john_bird_wings_white.png")
    if os.path.isfile(white_src):
        Image.open(white_src).convert("RGB").save(os.path.join(PROGS_DIR, "john_bird_wings_white.png"), optimize=True)


def build_feather_md3():
    """Create a lightweight curved 3D primary feather MD3 ('progs/john_bird_feather.md3')
    mapped onto 'progs/john_bird_wings' so rocket impacts & 5-rocket shootdowns burst
    real 3D tumbling feathers in DarkPlaces!
    """
    # 6 span stations along X (-8..+10), 3 chord stations across Y (left vane, central rachis, right vane)
    xs = [-8.0, -4.8, -1.2, 2.6, 6.4, 9.8]
    half_w = [0.45, 2.05, 2.55, 2.25, 1.45, 0.25]
    arch_z = [-0.35, 0.25, 0.65, 0.55, 0.05, -0.65]

    verts = []
    norms = []
    uvs = []
    for i, (x, hw, zc) in enumerate(zip(xs, half_w, arch_z)):
        t = i / float(len(xs) - 1)
        # Sample rich golden-brown primary feather region in john_bird_wings.png
        v_uv = 0.18 + 0.72 * t
        for side, u_uv, dz in ((-1.0, 0.18, -0.22), (0.0, 0.25, 0.22), (1.0, 0.32, -0.22)):
            verts.append((x, side * hw, zc + dz))
            nx = -0.10 * (t - 0.5)
            ny = 0.24 * side
            nz = 0.96
            nl = math.hypot(nx, ny, nz)
            norms.append((nx / nl, ny / nl, nz / nl))
            uvs.append((u_uv, v_uv))

    tris = []
    for i in range(len(xs) - 1):
        r0 = i * 3
        r1 = (i + 1) * 3
        # Left vane quad & Right vane quad (cull none in john_bird.shader handles underside!)
        tris.append((r0 + 0, r1 + 0, r1 + 1))
        tris.append((r0 + 0, r1 + 1, r0 + 1))
        tris.append((r0 + 1, r1 + 1, r1 + 2))
        tris.append((r0 + 1, r1 + 2, r0 + 2))
        # Also include back-facing triangles with inverted normals? No need when john_bird.shader uses cull none,
        # OR duplicate underside verts so hardware lighting is accurate on both faces even without shader!
    n_top = len(verts)
    for i in range(n_top):
        vx, vy, vz = verts[i]
        nx, ny, nz = norms[i]
        verts.append((vx, vy, vz - 0.08))
        norms.append((-nx, -ny, -nz))
        uvs.append(uvs[i])
    top_tris = list(tris)
    for a, b, c in top_tris:
        tris.append((n_top + a, n_top + c, n_top + b))

    surf = dict(
        name="feather",
        shader="progs/john_bird_wings",
        tris=tris,
        st=uvs,
        frames=[(verts, norms)],
    )
    out_md3 = os.path.join(PROGS_DIR, "john_bird_feather.md3")
    md3lib.write(out_md3, dict(name="progs/john_bird_feather.md3", surfaces=[surf]))
    print(f"Wrote 3D feather debris model: {out_md3} ({len(verts)} verts, {len(tris)} tris)")


def write_skins_and_shader():
    skins = {
        "john_bird_head.md3_0.skin": (
            "head,progs/john_bird_head\n"
            "hair_breezy,progs/john_bird_hair\n"
            "wings_bird,progs/john_bird_wings\n"
        ),
        "john_bird_head.md3_1.skin": (
            "head,progs/john_bird_head\n"
            "hair_breezy,progs/john_bird_hair\n"
            "wings_bird,progs/john_bird_wings_hurt\n"
        ),
        "john_bird_head.md3_2.skin": (
            "head,progs/john_bird_head\n"
            "hair_breezy,progs/john_bird_hair\n"
            "wings_bird,progs/john_bird_wings_white\n"
        ),
    }
    for fn, content in skins.items():
        with open(os.path.join(PROGS_DIR, fn), "w", encoding="ascii", newline="\n") as f:
            f.write(content)

    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    shader_txt = """// Winged Breezy-Hair John flyable vehicle double-sided materials (build_john_bird_vehicle_assets.py)

progs/john_bird_head
{
\tcull none
\t{
\t\tmap progs/john_bird_head
\t\trgbGen lightingDiffuse
\t}
}

progs/john_bird_hair
{
\tcull none
\t{
\t\tmap progs/john_bird_hair
\t\trgbGen lightingDiffuse
\t}
}

progs/john_bird_wings
{
\tcull none
\t{
\t\tmap progs/john_bird_wings
\t\trgbGen lightingDiffuse
\t}
}

progs/john_bird_wings_white
{
\tcull none
\t{
\t\tmap progs/john_bird_wings_white
\t\trgbGen lightingDiffuse
\t}
}

progs/john_bird_wings_hurt
{
\tcull none
\t{
\t\tmap progs/john_bird_wings_hurt
\t\trgbGen lightingDiffuse
\t}
\t{
\t\tmap progs/john_bird_wings_hurt_glow
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""
    with open(os.path.join(SCRIPTS_DIR, "john_bird.shader"), "w", encoding="ascii", newline="\n") as f:
        f.write(shader_txt)
    print("Wrote DarkPlaces .md3_0..2.skin files and scripts/john_bird.shader")


def main():
    os.makedirs(SND_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Wing-flapping & flight SFX
    flap_specs = [
        ("flap1.wav", 11, 0.28, 0.98, 1.05),
        ("flap2.wav", 22, 0.27, 1.05, 0.96),
        ("flap3.wav", 33, 0.30, 0.93, 1.12),
        ("flap4.wav", 44, 0.26, 1.11, 0.94),
    ]
    for fn, seed, dur, pm, hv in flap_specs:
        save_wav_mono16(os.path.join(SND_DIR, fn), synth_wing_flap(seed, dur, pm, hv))
    save_wav_mono16(os.path.join(SND_DIR, "takeoff.wav"), synth_takeoff())
    save_wav_mono16(os.path.join(SND_DIR, "swoop.wav"), synth_swoop())
    save_wav_mono16(os.path.join(SND_DIR, "feather_hit.wav"), synth_feather_hit())

    # 2. Curated random "John" voice clips while flying
    voice_specs = [
        ("jv_fly00.wav", "hmfloating.wav",         "Hmm... I'm floating!"),
        ("jv_fly01.wav", "doyouhavehairspray.wav", "Do you have hairspray?"),
        ("jv_fly02.wav", "mynameisjohn.wav",       "My name is John."),
        ("jv_fly03.wav", "thisisjohn.wav",         "This is John."),
        ("jv_fly04.wav", "ridethewave.wav",        "Ride the wave of the future, baby!"),
        ("jv_fly05.wav", "johnwave99.wav",         "John Wave '99!"),
        ("jv_fly06.wav", "fixwave.wav",            "Fix the wave!"),
        ("jv_fly07.wav", "isntsalon.wav",          "Isn't this a salon?!"),
        ("jv_fly08.wav", "damnitmyhave.wav",       "Damn it, my hair!"),
        ("jv_fly09.wav", "john.wav",               "John!"),
        ("jv_fly10.wav", "thatiselite.wav",        "That is elite."),
        ("jv_fly11.wav", "imusingwin97.wav",       "I'm using Windows 97."),
        ("jv_fly12.wav", "whyhello.wav",           "Why, hello!"),
        ("jv_fly13.wav", "reooow.wav",             "Reooow!!"),
    ]
    manifest = []
    reooow_m = None
    for out_fn, src_fn, quote in voice_specs:
        src_p = os.path.join(CELEB_DIR, src_fn)
        raw = load_wav_mono_resampled(src_p, SR)
        m = master_voice_clip(raw, target_rms=0.25)
        if src_fn == "reooow.wav":
            reooow_m = m
        out_p = os.path.join(SND_DIR, out_fn)
        save_wav_mono16(out_p, m)
        dur = round(len(m) / float(SR), 2)
        manifest.append(dict(file=out_fn, src=src_fn, quote=quote, duration=dur))
        print(f"  Mastered John voice: {out_fn:14s} ({dur:4.2f}s) <- {src_fn:24s} \"{quote}\"")

    hurt_m = master_voice_clip(load_wav_mono_resampled(os.path.join(CELEB_DIR, "imsorry.wav"), SR), 0.26)
    bye_m = master_voice_clip(load_wav_mono_resampled(os.path.join(CELEB_DIR, "goodbye.wav"), SR), 0.27)
    save_wav_mono16(os.path.join(SND_DIR, "jv_hurt.wav"), hurt_m)
    save_wav_mono16(os.path.join(SND_DIR, "shootdown.wav"), synth_shootdown(reooow_m, bye_m))

    with open(os.path.join(OUT_DIR, "voice_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 3. Battle-singed wing textures, .skin files, .shader, and 3D feather debris MD3
    build_hurt_wing_textures()
    build_feather_md3()
    write_skins_and_shader()
    print("All Winged Breezy-Hair John vehicle assets built successfully!")


if __name__ == "__main__":
    main()
