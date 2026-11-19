"""Build the 3D bouncing chrome barber scissors model (progs/kyle_scissors.md3),
its brushed-chrome metallic texture (progs/kyle_scissors.png), and 3 realistic
metallic scissor-clang bounce WAVs (scissor_clang1..3.wav) for Kyle's death explosion!

Run:
    python -I source/mm_tools/kyle_scissors/build_scissors_md3.py
"""

import math
import os
import sys
import wave
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
TOOLS_DIR = HERE.parent
sys.path.insert(0, str(TOOLS_DIR))
import md3lib

ARTIFACT_ROOT = Path(r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671")
OUT_MODEL_DIR = ARTIFACT_ROOT / "scratch" / "kyle_stage" / "models"
OUT_SFX_DIR = ARTIFACT_ROOT / "scratch" / "kyle_stage" / "sfx"


def add_extruded_poly(verts, tris, st, pts_2d: List[Tuple[float, float]],
                      z0: float, z1: float, uv_box: Tuple[float, float, float, float]):
    """Extrude a 2D closed polygon (CCW) along Z from z0 to z1 with clean side walls & caps."""
    n = len(pts_2d)
    u0, v0, u1, v1 = uv_box
    xs = [p[0] for p in pts_2d]
    ys = [p[1] for p in pts_2d]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    dx = max(1e-4, maxx - minx)
    dy = max(1e-4, maxy - miny)

    # Top face (+Z)
    b_top = len(verts)
    cx = sum(xs) / n
    cy = sum(ys) / n
    verts.append((cx, cy, z1))
    st.append((u0 + 0.5 * (u1 - u0), v0 + 0.5 * (v1 - v0)))
    for x, y in pts_2d:
        verts.append((x, y, z1))
        st.append((u0 + ((x - minx) / dx) * (u1 - u0), v0 + ((y - miny) / dy) * (v1 - v0)))
    for i in range(n):
        j = (i + 1) % n
        tris.append((b_top, b_top + 1 + i, b_top + 1 + j))

    # Bottom face (-Z)
    b_bot = len(verts)
    verts.append((cx, cy, z0))
    st.append((u0 + 0.5 * (u1 - u0), v0 + 0.5 * (v1 - v0)))
    for x, y in pts_2d:
        verts.append((x, y, z0))
        st.append((u0 + ((x - minx) / dx) * (u1 - u0), v0 + ((y - miny) / dy) * (v1 - v0)))
    for i in range(n):
        j = (i + 1) % n
        tris.append((b_bot, b_bot + 1 + j, b_bot + 1 + i))

    # Side walls
    for i in range(n):
        j = (i + 1) % n
        x0, y0 = pts_2d[i]
        x1, y1 = pts_2d[j]
        bi = len(verts)
        verts.extend([
            (x0, y0, z0),
            (x1, y1, z0),
            (x1, y1, z1),
            (x0, y0, z1),
        ])
        st.extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        tris.extend([(bi, bi + 1, bi + 2), (bi, bi + 2, bi + 3)])


def add_torus_ring(verts, tris, st, cx: float, cy: float, cz: float,
                   R_major: float, R_minor: float, n_seg: int = 16, n_tube: int = 8,
                   uv_box=(0.05, 0.55, 0.45, 0.95)):
    """Build a smooth 3D finger ring (torus in XY plane centered at cx, cy, cz)."""
    u0, v0, u1, v1 = uv_box
    base = len(verts)
    for i in range(n_seg):
        a = 2.0 * math.pi * i / n_seg
        ca, sa = math.cos(a), math.sin(a)
        for j in range(n_tube):
            b = 2.0 * math.pi * j / n_tube
            cb, sb = math.cos(b), math.sin(b)
            r = R_major + R_minor * cb
            x = cx + r * ca
            y = cy + r * sa
            z = cz + R_minor * sb
            verts.append((x, y, z))
            st.append((u0 + (i / n_seg) * (u1 - u0), v0 + (j / n_tube) * (v1 - v0)))
    for i in range(n_seg):
        ni = (i + 1) % n_seg
        for j in range(n_tube):
            nj = (j + 1) % n_tube
            v00 = base + i * n_tube + j
            v10 = base + ni * n_tube + j
            v11 = base + ni * n_tube + nj
            v01 = base + i * n_tube + nj
            tris.append((v00, v10, v11))
            tris.append((v00, v11, v01))


def add_cylinder_z(verts, tris, st, cx: float, cy: float, z0: float, z1: float,
                   radius: float, n_seg: int = 12, uv_box=(0.55, 0.55, 0.95, 0.95)):
    pts = [
        (cx + radius * math.cos(2.0 * math.pi * i / n_seg),
         cy + radius * math.sin(2.0 * math.pi * i / n_seg))
        for i in range(n_seg)
    ]
    add_extruded_poly(verts, tris, st, pts, z0, z1, uv_box)


def build_one_half(verts, tris, st, angle_deg: float, z_off: float, flip_y: float):
    """Build one complete chrome barber scissor half (beveled blade + sculpted shank + 3D finger ring + tang)."""
    rad = math.radians(angle_deg)
    ca, sa = math.cos(rad), math.sin(rad)

    def xform(x, y):
        y = y * flip_y
        return (x * ca - y * sa, x * sa + y * ca)

    # 1. Sleek tapered stainless steel blade (pivot at x=0 -> tip at x=+16)
    blade_local = [
        (-1.4, -0.95),
        (16.2, -0.18),
        (17.4, 0.15),
        (14.5, 1.35),
        (6.5, 1.75),
        (-1.4, 1.35),
    ]
    blade_pts = [xform(x, y) for x, y in blade_local]
    if flip_y < 0:
        blade_pts = list(reversed(blade_pts))
    add_extruded_poly(verts, tris, st, blade_pts, z_off - 0.32, z_off + 0.32, (0.04, 0.04, 0.96, 0.44))

    # 2. Ergonomic chrome shank connecting pivot (x=-1) to ring (x=-10)
    shank_local = [
        (-1.0, -0.75),
        (-1.0, 0.95),
        (-6.2, 1.85),
        (-10.2, 2.25),
        (-10.6, 1.15),
        (-6.0, 0.55),
    ]
    shank_pts = [xform(x, y) for x, y in shank_local]
    if flip_y < 0:
        shank_pts = list(reversed(shank_pts))
    add_extruded_poly(verts, tris, st, shank_pts, z_off - 0.42, z_off + 0.42, (0.06, 0.52, 0.48, 0.94))

    # 3. 3D Finger Ring (torus)
    rcx, rcy = xform(-12.6, 2.55)
    add_torus_ring(verts, tris, st, rcx, rcy, z_off, R_major=2.75, R_minor=0.58, n_seg=18, n_tube=8,
                   uv_box=(0.06, 0.52, 0.48, 0.94))

    # 4. Barber pinky tang on one half
    if flip_y > 0:
        tang_local = [
            (-14.6, 3.8),
            (-17.8, 5.2),
            (-18.6, 4.6),
            (-15.6, 2.9),
        ]
        tang_pts = [xform(x, y) for x, y in tang_local]
        add_extruded_poly(verts, tris, st, tang_pts, z_off - 0.35, z_off + 0.35, (0.06, 0.52, 0.48, 0.94))


def compute_vertex_normals(verts, tris):
    acc = np.zeros((len(verts), 3), dtype=np.float64)
    v_arr = np.asarray(verts, dtype=np.float64)
    for i0, i1, i2 in tris:
        e1 = v_arr[i1] - v_arr[i0]
        e2 = v_arr[i2] - v_arr[i0]
        n = np.cross(e1, e2)
        acc[i0] += n
        acc[i1] += n
        acc[i2] += n
    lens = np.linalg.norm(acc, axis=1, keepdims=True)
    acc = np.where(lens > 1e-8, acc / np.maximum(lens, 1e-8), np.array([[0.0, 0.0, 1.0]]))
    return [tuple(row) for row in acc]


def build_scissors_texture(out_png: Path):
    """Crisp brushed-chrome metallic texture (256x256):
      Top half (v=0..0.48): bright mirror-steel blade with bevel sheen
      Bottom-left (u=0..0.5, v=0.5..1): polished chrome handles/rings
      Bottom-right (u=0.5..1, v=0.5..1): warm brass-steel pivot screw
    """
    w, h = 256, 256
    arr = np.zeros((h, w, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # Brushed steel horizontal grain + specular gradient
    rng = np.random.default_rng(2026)
    grain = rng.normal(0.0, 6.0, (h, 1)).repeat(w, axis=1)
    sheen = 178.0 + 58.0 * np.sin((yy / 128.0) * math.pi) + 22.0 * np.cos((xx / 256.0) * math.pi * 2.0)
    # Top half: razor-sharp cool mirror stainless steel
    arr[:128, :, 0] = sheen[:128] + grain[:128] - 4.0
    arr[:128, :, 1] = sheen[:128] + grain[:128]
    arr[:128, :, 2] = sheen[:128] + grain[:128] + 10.0
    # Crisp bright blade bevel edge highlight
    arr[4:14, :, :] += 34.0
    arr[114:124, :, :] -= 28.0

    # Bottom-left: polished chrome rings/shanks
    chrome = 162.0 + 62.0 * np.sin(((yy - 128.0) / 128.0) * math.pi * 1.6) + 18.0 * np.sin((xx / 128.0) * math.pi * 2.0)
    arr[128:, :128, 0] = chrome[128:, :128] - 2.0
    arr[128:, :128, 1] = chrome[128:, :128] + 2.0
    arr[128:, :128, 2] = chrome[128:, :128] + 12.0

    # Bottom-right: machined brass/gold-chrome pivot screw with slot
    arr[128:, 128:, 0] = 225.0 + grain[128:, 128:] * 0.5
    arr[128:, 128:, 1] = 192.0 + grain[128:, 128:] * 0.5
    arr[128:, 128:, 2] = 115.0 + grain[128:, 128:] * 0.5
    # Screw slot stripe
    arr[186:198, 140:244, :] *= 0.35

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    im.save(out_png, format="PNG", compress_level=6, optimize=False)
    print(f"Wrote {out_png}")


def build_scissors_md3(out_md3: Path):
    """Build 8-frame animated 3D chrome barber scissors MD3 (snapping open & shut while bouncing!)."""
    open_angles = [28.0, 20.0, 10.0, 3.0, 10.0, 22.0, 32.0, 28.0]
    frames = []
    tris_ref = None
    st_ref = None

    for ang in open_angles:
        verts: List[Tuple[float, float, float]] = []
        tris: List[Tuple[int, int, int]] = []
        st: List[Tuple[float, float]] = []
        build_one_half(verts, tris, st, +ang, +0.34, +1.0)
        build_one_half(verts, tris, st, -ang, -0.34, -1.0)
        # Central pivot screw pin
        add_cylinder_z(verts, tris, st, 0.0, 0.0, -0.92, +0.92, radius=1.15, n_seg=12)
        normals = compute_vertex_normals(verts, tris)
        frames.append((verts, normals))
        if tris_ref is None:
            tris_ref = tris
            st_ref = st
        else:
            assert len(verts) == len(frames[0][0]) and len(tris) == len(tris_ref)

    surf = dict(
        name="scissors",
        shader="progs/kyle_scissors",
        tris=tris_ref,
        st=st_ref,
        frames=frames,
    )
    md3lib.write(str(out_md3), dict(name="kyle_scissors", surfaces=[surf], nframes=len(frames)))
    print(f"Wrote {out_md3} ({len(frames)} frames, {len(frames[0][0])} verts, {len(tris_ref)} tris)")


def synth_clang_wav(out_wav: Path, seed: int, pitch_mult: float):
    """Synthesize crisp realistic bouncing steel barber-scissors clang on concrete (22050 Hz mono 16-bit PCM)."""
    sr = 22050
    dur = 0.62
    t = np.linspace(0.0, dur, int(sr * dur), endpoint=False, dtype=np.float64)
    rng = np.random.default_rng(seed)

    sig = np.zeros_like(t)
    # Inharmonic stainless steel shears partials + subtle double-blade rattle 28ms later
    partials = [
        (1680.0, 0.34, 8.5),
        (2540.0, 0.42, 7.2),
        (3710.0, 0.36, 9.8),
        (4890.0, 0.28, 12.0),
        (6420.0, 0.22, 16.0),
        (8150.0, 0.14, 22.0),
    ]
    for f0, amp, dec in partials:
        f = f0 * pitch_mult * (1.0 + rng.uniform(-0.025, 0.025))
        ph = rng.uniform(0.0, 2.0 * math.pi)
        sig += amp * np.sin(2.0 * math.pi * f * t + ph) * np.exp(-t * dec)

    # Sharp metallic impact transient + secondary scissor-blade clatter 32ms later
    imp1 = rng.normal(0.0, 1.0, len(t)) * np.exp(-t * 140.0) * 0.55
    t2 = np.maximum(0.0, t - 0.032)
    mask2 = (t >= 0.032).astype(np.float64)
    imp2 = mask2 * (
        0.26 * np.sin(2.0 * math.pi * (3120.0 * pitch_mult) * t2) * np.exp(-t2 * 11.0)
        + 0.20 * np.sin(2.0 * math.pi * (5340.0 * pitch_mult) * t2) * np.exp(-t2 * 16.0)
        + rng.normal(0.0, 1.0, len(t)) * np.exp(-t2 * 160.0) * 0.30
    )
    sig = sig + imp1 + imp2

    # Subtle 1-pole high-pass to keep it crisp & metallic (no muddy low end)
    sig = np.diff(sig, prepend=0.0) * 0.55 + sig * 0.65
    peak = np.max(np.abs(sig)) + 1e-8
    sig = (sig / peak) * 0.88
    # Smooth 15ms tail fade
    fade = min(len(sig), int(sr * 0.025))
    sig[-fade:] *= np.linspace(1.0, 0.0, fade)

    pcm = np.clip(np.round(sig * 32767.0), -32767, 32767).astype("<i2")
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    print(f"Wrote {out_wav} ({out_wav.stat().st_size} bytes)")


def main():
    OUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SFX_DIR.mkdir(parents=True, exist_ok=True)
    build_scissors_texture(OUT_MODEL_DIR / "kyle_scissors.png")
    build_scissors_md3(OUT_MODEL_DIR / "kyle_scissors.md3")
    synth_clang_wav(OUT_SFX_DIR / "scissor_clang1.wav", seed=101, pitch_mult=1.00)
    synth_clang_wav(OUT_SFX_DIR / "scissor_clang2.wav", seed=202, pitch_mult=1.14)
    synth_clang_wav(OUT_SFX_DIR / "scissor_clang3.wav", seed=303, pitch_mult=0.89)


if __name__ == "__main__":
    main()
