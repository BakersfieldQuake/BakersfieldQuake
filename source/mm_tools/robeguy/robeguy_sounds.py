"""Synthesizes 5 hilarious custom WAV sound effects for the Pink Flamingo Bathrobe Monster
(used in the self-contained interactive HTML showcase & Quake monster audio)."""

from __future__ import annotations

from pathlib import Path
import wave

import numpy as np

SR = 22050


def _write_wav(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = max(1e-4, float(np.max(np.abs(samples))))
    normed = np.clip(samples / peak * 0.90, -1.0, 1.0)
    pcm = (normed * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def _flamingo_honk(dur: float, f0: float = 540.0, f1: float = 780.0, rng: np.random.Generator | None = None) -> np.ndarray:
    """Nasal rubbery plastic-lawn-flamingo squeak-honk!"""
    n = int(SR * dur)
    t = np.linspace(0.0, dur, n, endpoint=False)
    freq = f0 + (f1 - f0) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    freq += 22.0 * np.sin(2.0 * np.pi * 28.0 * t)
    ph = 2.0 * np.pi * np.cumsum(freq) / SR
    # Nasal reed harmonic stack
    sig = (
        0.55 * np.sin(ph)
        + 0.42 * np.sin(2.0 * ph + 0.4)
        + 0.35 * np.sin(3.0 * ph + 1.1)
        + 0.22 * np.sin(5.0 * ph)
    )
    if rng is not None:
        sig += 0.06 * rng.standard_normal(n)
    env = np.sin(np.pi * (t / dur)) ** 0.35 * np.exp(-1.6 * t / dur)
    return sig * env


def _monster_roar(dur: float, f_start: float = 155.0, f_end: float = 92.0, rng: np.random.Generator | None = None) -> np.ndarray:
    """Guttural gravelly Sunday-morning dad-monster vocal roar."""
    if rng is None:
        rng = np.random.default_rng(42)
    n = int(SR * dur)
    t = np.linspace(0.0, dur, n, endpoint=False)
    f = f_start + (f_end - f_start) * (t / dur) + 9.0 * np.sin(2.0 * np.pi * 17.0 * t)
    ph = 2.0 * np.pi * np.cumsum(f) / SR
    glottal = np.tanh(2.6 * (np.sin(ph) + 0.65 * np.sin(2.0 * ph) + 0.40 * np.sin(3.0 * ph) + 0.25 * np.sin(0.5 * ph)))
    rasp = rng.standard_normal(n)
    # Simple 1-pole lowpass on rasp
    rasp_lp = np.zeros_like(rasp)
    a = 0.18
    for i in range(1, n):
        rasp_lp[i] = (1.0 - a) * rasp_lp[i - 1] + a * rasp[i]
    env = np.minimum(1.0, t / 0.05) * np.minimum(1.0, (dur - t) / 0.12)
    return (0.72 * glottal + 0.48 * rasp_lp * (0.5 + 0.5 * np.sin(ph))) * env


def build_all_robeguy_sounds(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261101)
    paths: dict[str, Path] = {}

    # 1. Idle Menace: deep breathing monster growl + 2 sneaky pocket-flamingo honks
    n1 = int(SR * 1.45)
    s1 = np.zeros(n1, dtype=np.float64)
    g1 = _monster_roar(0.75, 118.0, 82.0, rng) * 0.65
    s1[:len(g1)] += g1
    h_a = _flamingo_honk(0.18, 590.0, 860.0, rng) * 0.85
    h_b = _flamingo_honk(0.22, 640.0, 510.0, rng) * 0.90
    i_a, i_b = int(0.72 * SR), int(0.96 * SR)
    s1[i_a:i_a + len(h_a)] += h_a
    s1[i_b:i_b + len(h_b)] += h_b
    p1 = out_dir / "idle_honk_growl.wav"
    _write_wav(p1, s1)
    paths["monster_idle"] = p1

    # 2. Berserker Charge: rapid barefoot floor slaps + unhinged charging war-cry + frantic honks
    n2 = int(SR * 1.35)
    s2 = np.zeros(n2, dtype=np.float64)
    roar2 = _monster_roar(1.15, 195.0, 132.0, rng) * 0.85
    s2[int(0.06 * SR):int(0.06 * SR) + len(roar2)] += roar2
    for step_t in np.arange(0.02, 1.28, 0.155):
        idx = int(step_t * SR)
        slap_n = int(0.055 * SR)
        if idx + slap_n < n2:
            ts = np.linspace(0, 0.055, slap_n, endpoint=False)
            slap = (rng.standard_normal(slap_n) * 0.55 + np.sin(2 * np.pi * (210 - 1100 * ts) * ts) * 0.8) * np.exp(-52.0 * ts)
            s2[idx:idx + slap_n] += slap * 0.85
    hk = _flamingo_honk(0.16, 700.0, 960.0, rng) * 0.65
    s2[int(0.45 * SR):int(0.45 * SR) + len(hk)] += hk
    p2 = out_dir / "berserker_yell.wav"
    _write_wav(p2, s2)
    paths["berserker_charge"] = p2

    # 3. Robe-Flash Chest-Laser: dramatic fabric whip-open + "AAAH!" shock chord + sci-fi mega chest laser!
    n3 = int(SR * 1.65)
    t3 = np.linspace(0.0, 1.65, n3, endpoint=False)
    s3 = np.zeros(n3, dtype=np.float64)
    # Robe whip whoosh at t=0.08..0.30
    w_mask = (t3 >= 0.06) & (t3 < 0.32)
    tw = t3[w_mask] - 0.06
    s3[w_mask] += rng.standard_normal(np.sum(w_mask)) * np.sin(np.pi * tw / 0.26) * 0.55
    # Blinding chest-hair laser beam t=0.32..1.38
    b_mask = (t3 >= 0.30) & (t3 < 1.42)
    tb = t3[b_mask] - 0.30
    f_beam = 880.0 * np.exp(-1.1 * tb) + 220.0 + 45.0 * np.sin(2.0 * np.pi * 34.0 * tb)
    ph_b = 2.0 * np.pi * np.cumsum(f_beam) / SR
    choir = 0.45 * np.sin(2 * np.pi * 293.66 * tb) + 0.40 * np.sin(2 * np.pi * 369.99 * tb) + 0.38 * np.sin(2 * np.pi * 440.0 * tb)
    beam = (0.65 * np.tanh(2.2 * np.sin(ph_b)) + 0.45 * choir) * np.minimum(1.0, tb / 0.04) * np.exp(-1.25 * tb)
    s3[b_mask] += beam
    r3 = _monster_roar(0.85, 210.0, 145.0, rng) * 0.55
    s3[int(0.32 * SR):int(0.32 * SR) + len(r3)] += r3
    p3 = out_dir / "chest_laser_flash.wav"
    _write_wav(p3, s3)
    paths["robe_flash_laser"] = p3

    # 4. Flamingo Weapon & Coffee Rampage: rapid whoosh swings + rabid flamingo honk barrage + ceramic bonk
    n4 = int(SR * 1.45)
    t4 = np.linspace(0.0, 1.45, n4, endpoint=False)
    s4 = np.zeros(n4, dtype=np.float64)
    for wt in (0.08, 0.38, 0.72):
        wm = (t4 >= wt) & (t4 < wt + 0.20)
        tw = t4[wm] - wt
        s4[wm] += rng.standard_normal(np.sum(wm)) * np.sin(np.pi * tw / 0.20) ** 1.5 * 0.65
    for ht, f_lo, f_hi in ((0.18, 620.0, 940.0), (0.50, 740.0, 1080.0), (0.82, 820.0, 520.0)):
        hk = _flamingo_honk(0.21, f_lo, f_hi, rng) * 0.90
        i0 = int(ht * SR)
        s4[i0:min(n4, i0 + len(hk))] += hk[:max(0, n4 - i0)]
    p4 = out_dir / "flamingo_whack.wav"
    _write_wav(p4, s4)
    paths["flamingo_attack"] = p4

    # 5. Catastrophic Feather & Gib Explosion: rising overload whine -> massive boom -> wet gib splats -> sad dying flamingo squeak!
    n5 = int(SR * 2.10)
    t5 = np.linspace(0.0, 2.10, n5, endpoint=False)
    s5 = np.zeros(n5, dtype=np.float64)
    # Overload swell 0..0.38s
    m_ov = t5 < 0.38
    t_ov = t5[m_ov]
    ph_ov = 2 * np.pi * np.cumsum(260.0 + 950.0 * (t_ov / 0.38) ** 1.8) / SR
    s5[m_ov] += 0.60 * np.sin(ph_ov) * (t_ov / 0.38)
    # Quake explosion boom at 0.38s
    m_bm = (t5 >= 0.38) & (t5 < 1.55)
    tb = t5[m_bm] - 0.38
    noise = rng.standard_normal(np.sum(m_bm))
    lp = np.zeros_like(noise)
    alpha = 0.08
    for i in range(1, len(noise)):
        lp[i] = (1.0 - alpha) * lp[i - 1] + alpha * noise[i]
    sub_boom = np.sin(2 * np.pi * (95.0 * np.exp(-3.2 * tb) + 32.0) * tb) * np.exp(-3.4 * tb)
    s5[m_bm] += (1.35 * lp * np.exp(-2.8 * tb) + 0.95 * sub_boom)
    # Sad deflating flamingo squeak at the end (1.42..1.95s)
    sq = _flamingo_honk(0.48, 780.0, 240.0, rng) * 0.72
    i_sq = int(1.42 * SR)
    s5[i_sq:i_sq + len(sq)] += sq
    p5 = out_dir / "feather_gib_boom.wav"
    _write_wav(p5, s5)
    paths["flamingo_gib_death"] = p5

    return paths
