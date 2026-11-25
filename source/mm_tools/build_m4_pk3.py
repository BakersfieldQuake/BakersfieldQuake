#!/usr/bin/env python3
"""Build zz_m4.pk3: a silencer for the M4 (playtest: "needs a silencer ... sound properly suppressed").

  progs/v_m4.md3, progs/p_m4.md3    the base package's models plus a "silencer" surface on the muzzle, moved with the
                                     barrel in every animation frame
  sound/cs16/m4a1_unsil-1/2.wav      suppressed shots, synthesised here (same names, so m4.qc plays them unchanged)
  models/cs16/m4_silencer.png + scripts/m4_silencer.shader

Reproducible: seeded noise, no clock, fixed zip dates/attributes, pinned numpy/Pillow in CI.

Usage:
  python -I build_m4_pk3.py <base bakersfield.pk3> <out zz_m4.pk3> [--wav-dir <dir>] [--verify-repro]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import math
import sys
import tempfile
import wave
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md3lib  # noqa: E402

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
RATE = 22050
SIDES = 14

SHADER = """// written by source/mm_tools/build_m4_pk3.py
models/cs16/m4_silencer
{
	cull none
	{
		map models/cs16/m4_silencer.png
		rgbGen lightingDiffuse
	}
}
"""

# model: barrel surface, a point on the barrel behind the muzzle, radius, how far it sleeves back over the barrel,
# how far it sticks out past the muzzle
MODELS = {
    "progs/v_m4.md3": ("barrel", (25.68, -14.70, -6.50), 0.92, 1.6, 7.6),
    "progs/p_m4.md3": ("m4a1_skin", (14.95, -0.10, 1.22), 1.05, 1.6, 6.5),
}


def muzzle(barrel: np.ndarray) -> np.ndarray:
    return barrel[barrel[:, 0] > barrel[:, 0].max() - 0.3].mean(0)


def cylinder(tip, axis, radius, back, out):
    """Frame-0 silencer: a tube with a closed front cap (with a dark bore) and a collar at the rear."""
    side = np.cross(axis, (0.0, 0.0, 1.0))
    side /= np.linalg.norm(side)
    up = np.cross(side, axis)
    # (distance along the axis from the muzzle, radius, texture v)
    rings = [(-back, radius * 0.55, 0.00), (-back, radius * 1.08, 0.04), (-back + 0.7, radius * 1.08, 0.12),
             (-back + 0.7, radius, 0.14), (out - 0.35, radius, 0.86), (out, radius * 0.84, 0.90),
             (out, radius * 0.34, 0.96), (out - 0.8, radius * 0.30, 1.00)]
    verts, norms, st, tris = [], [], [], []
    for ri, (d, r, v) in enumerate(rings):
        for i in range(SIDES + 1):
            a = 2 * math.pi * i / SIDES
            radial = side * math.cos(a) + up * math.sin(a)
            verts.append(tip + axis * d + radial * r)
            if ri in (0, 1):
                n = -axis + radial * 0.4
            elif ri in (5, 6, 7):
                n = axis + radial * 0.4
            else:
                n = radial
            norms.append(n / np.linalg.norm(n))
            st.append((i / SIDES, v))
    w = SIDES + 1
    for ri in range(len(rings) - 1):
        for i in range(SIDES):
            a, b, c, d = ri * w + i, ri * w + i + 1, (ri + 1) * w + i, (ri + 1) * w + i + 1
            tris += [(a, c, b), (b, c, d)]
    return np.array(verts), np.array(norms), st, tris


def kabsch(a: np.ndarray, b: np.ndarray):
    """Rigid transform taking point set a onto b: returns (R, ca, cb) with b ~ (a - ca) @ R + cb."""
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    d = np.sign(np.linalg.det(u @ vt))
    return u @ np.diag([1.0, 1.0, d]) @ vt, ca, cb


def silenced_model(raw: bytes, name: str) -> bytes:
    barrel_name, behind, radius, back, out = MODELS[name]
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.md3"
        src.write_bytes(raw)
        model = md3lib.read(str(src))
        barrel = next(s for s in model["surfaces"] if s["name"] == barrel_name)
        rest = np.array(barrel["frames"][0][0])
        tip = muzzle(rest)
        axis = tip - np.array(behind)
        axis /= np.linalg.norm(axis)
        verts, norms, st, tris = cylinder(tip, axis, radius, back, out)
        frames = []
        for vv, _ in barrel["frames"]:
            rot, ca, cb = kabsch(rest, np.array(vv))
            fv = (verts - ca) @ rot + cb
            fn = norms @ rot
            frames.append(([tuple(map(float, p)) for p in fv], [tuple(map(float, p)) for p in fn]))
        model["surfaces"].append({"name": "silencer", "shader": "models/cs16/m4_silencer", "tris": tris, "st": st,
                                  "frames": frames})
        dst = Path(td) / "out.md3"
        md3lib.write(str(dst), model)
        end = tip + axis * out
        print(f"{name}: muzzle {np.round(tip, 2)} -> silencer end {np.round(end, 2)}")
        return dst.read_bytes()


def silencer_texture() -> bytes:
    w, h = 128, 128
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    v = y / (h - 1)
    grain = np.sin(x * 12.9 + y * 78.2) * 43758.5453
    grain = grain - np.floor(grain)
    shade = 34 + 8 * grain + 26 * np.exp(-(((x / (w - 1)) - 0.30) / 0.10) ** 2)
    img = np.stack([shade, shade + 1, shade + 4], axis=-1)
    for edge in (0.13, 0.20, 0.80, 0.87):
        img[np.abs(v - edge) < 0.012] *= 0.45
    img[v > 0.955] = [6, 6, 7]                 # the bore
    out = io.BytesIO()
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()


def suppressed_shot(seed: int, pitch: float) -> bytes:
    """A suppressed rifle: a soft low thump, a short muffled gas 'pfft' and the quiet clack of the bolt."""
    rng = np.random.default_rng(seed)
    n = int(RATE * 0.26)
    t = np.arange(n) / RATE

    def lowpass(x, cut):
        a = 1 - math.exp(-2 * math.pi * cut / RATE)
        y = np.empty_like(x)
        acc = 0.0
        for i, s in enumerate(x):
            acc += a * (s - acc)
            y[i] = acc
        return y

    noise = rng.uniform(-1, 1, n)
    gas = lowpass(lowpass(noise, 2300 * pitch), 2300 * pitch) - lowpass(noise, 320)
    gas *= np.minimum(1, t / 0.0025) * (0.85 * np.exp(-t / 0.022) + 0.15 * np.exp(-t / 0.085))
    thump = np.sin(2 * math.pi * (150 * pitch * t - 260 * t * t)) * np.exp(-t / 0.030) * np.minimum(1, t / 0.002)
    clack = np.zeros(n)
    for at, f, g in ((0.034, 2600, 0.30), (0.071, 1900, 0.18)):
        k = t >= at
        dt = t[k] - at
        clack[k] += g * np.sin(2 * math.pi * f * pitch * dt) * np.exp(-dt / 0.006) + g * noise[k] * np.exp(-dt / 0.003) * 0.5
    s = gas * 2.2 + thump * 0.75 + clack * 0.45
    s *= np.minimum(1, (t[-1] - t) / 0.02)
    s = s / np.abs(s).max() * 0.55             # well under full scale: it is meant to be quiet
    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(np.round(s * 32767).astype("<i2").tobytes())
    return out.getvalue()


def sounds() -> dict[str, bytes]:
    return {"sound/cs16/m4a1_unsil-1.wav": suppressed_shot(67, 1.00),
            "sound/cs16/m4a1_unsil-2.wav": suppressed_shot(68, 0.93)}


def entries(base: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(base) as z:
        models = {name: silenced_model(z.read(name), name) for name in MODELS}
    return {**models, **sounds(),
            "models/cs16/m4_silencer.png": silencer_texture(),
            "scripts/m4_silencer.shader": SHADER.encode("ascii")}


def build(base: Path, out: Path) -> str:
    ent = entries(base)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        for name in sorted(ent):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            if name.endswith(".png"):
                info.compress_type = zipfile.ZIP_STORED
                z.writestr(info, ent[name])
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, ent[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{out}: {len(ent)} files sha256 {digest}")
    return digest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--wav-dir", type=Path, help="also write the shot sounds here (to listen to them)")
    ap.add_argument("--verify-repro", action="store_true")
    a = ap.parse_args()
    first = build(a.base, a.out)
    if a.wav_dir:
        a.wav_dir.mkdir(parents=True, exist_ok=True)
        for name, data in sounds().items():
            (a.wav_dir / Path(name).name).write_bytes(data)
    if a.verify_repro:
        tmp = a.out.with_suffix(".repro.pk3")
        second = build(a.base, tmp)
        tmp.unlink()
        if first != second:
            sys.exit("NOT REPRODUCIBLE: two builds differ")
        print("reproducible: OK")


if __name__ == "__main__":
    main()
