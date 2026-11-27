"""Builds zz_triple_wheeled.pk3: reproducible B. Triple Wheeled powerup model, shaders & sounds.

Usage:
  python -I source/mm_tools/triple_wheeled/build_triple_wheeled_pk3.py [q15.pk3] [output_pk3] [--verify-repro]

Generates deterministically into zz_triple_wheeled.pk3:
  - progs/triple_wheeled.md3 (+ _0.skin)  : 4 Rocket Launchers clustered together (2 upright, 2 upside down) + glow shell & rings
  - progs/triple_wheeled_rl.png           : Rocket launcher metallic/emissive texture (derived from q15 textures/p_rock2.png)
  - progs/triple_wheeled_glow.png         : Pulsing plasma glow texture for the energy core, rings & outer shell
  - scripts/triple_wheeled.shader         : Pulsing emissive + additive plasma glow shaders
  - sound/triple_wheeled/pickup.wav       : Celebratory 4-launcher rack + powerup chord
  - sound/triple_wheeled/wearoff.wav      : Powerup expiration descend
"""
from __future__ import annotations

import argparse
import hashlib
import io
import math
import os
import struct
import sys
import tempfile
import wave
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
REPO_ROOT = MM_TOOLS.parent.parent

if str(MM_TOOLS) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS))
import md3lib  # noqa: E402

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}
SR = 22050


def _rot_matrix(rx_deg: float, ry_deg: float, rz_deg: float) -> np.ndarray:
    rx, ry, rz = map(math.radians, (rx_deg, ry_deg, rz_deg))
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    mx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)
    my = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    mz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)
    return mz @ my @ mx


def _load_aligned_rocket_launcher(q15_pk3: Path):
    """Read progs/p_rock2.md3 from q15.pk3, align barrel along +X and grips down (-Z), centered at origin."""
    with zipfile.ZipFile(q15_pk3, "r") as z:
        md3_bytes = z.read("progs/p_rock2.md3")
        tex_bytes = z.read("textures/p_rock2.png")

    with tempfile.NamedTemporaryFile(suffix=".md3", delete=False) as tf:
        tf.write(md3_bytes)
        tmp_path = tf.name
    try:
        model = md3lib.read(tmp_path)
    finally:
        os.unlink(tmp_path)

    surf = model["surfaces"][0]
    vv = np.array(surf["frames"][0][0], dtype=np.float64)
    nn = np.array(surf["frames"][0][1], dtype=np.float64)
    st = list(surf["st"])
    tris = list(surf["tris"])

    # PCA on frame 0 vertices to align barrel along +X, pistol grips along -Z
    center = vv.mean(axis=0)
    _, _, vt = np.linalg.svd(vv - center)
    axis_fwd = vt[0]      # barrel axis (+ = muzzle)
    axis_down = vt[1]     # pistol grips stick out in +vt[1]
    axis_up = -axis_down
    axis_left = np.cross(axis_up, axis_fwd)
    axis_left /= np.linalg.norm(axis_left)
    axis_up = np.cross(axis_fwd, axis_left)
    axis_up /= np.linalg.norm(axis_up)

    # Basis matrix rows = target axes (X=fwd, Y=left, Z=up); ensure det = +1
    basis = np.vstack([axis_fwd, axis_left, axis_up])
    if np.linalg.det(basis) < 0:
        basis[1] = -basis[1]

    vv_aligned = (vv - center) @ basis.T
    nn_aligned = nn @ basis.T
    # Center bounding box cleanly
    bmin = vv_aligned.min(axis=0)
    bmax = vv_aligned.max(axis=0)
    vv_aligned -= 0.5 * (bmin + bmax)

    return vv_aligned, nn_aligned, st, tris, tex_bytes


def _add_torus_ring(
    verts: list,
    norms: list,
    st: list,
    tris: list,
    major_r: float,
    minor_r: float,
    n_maj: int,
    n_min: int,
    x_offset: float,
    tri_base: int = 0,
) -> None:
    """Add an emissive torus energy ring centered in the YZ plane at x = x_offset."""
    base = len(verts)
    for i in range(n_maj):
        u = i / n_maj
        theta = u * 2.0 * math.pi
        ct, st_a = math.cos(theta), math.sin(theta)
        for j in range(n_min):
            v = j / n_min
            phi = v * 2.0 * math.pi
            cp, sp = math.cos(phi), math.sin(phi)
            # Ring around X axis (in YZ plane)
            px = x_offset + minor_r * sp
            r = major_r + minor_r * cp
            py = r * ct
            pz = r * st_a
            nx = sp
            ny = cp * ct
            nz = cp * st_a
            verts.append((px, py, pz))
            norms.append((nx, ny, nz))
            st.append((u * 2.0, v))

    for i in range(n_maj):
        ni = (i + 1) % n_maj
        for j in range(n_min):
            nj = (j + 1) % n_min
            i0 = base + i * n_min + j
            i1 = base + ni * n_min + j
            i2 = base + ni * n_min + nj
            i3 = base + i * n_min + nj
            # Verify winding against outward normal
            p0 = np.array(verts[i0])
            p1 = np.array(verts[i1])
            p2 = np.array(verts[i2])
            n_avg = np.array(norms[i0]) + np.array(norms[i1]) + np.array(norms[i2])
            if np.dot(np.cross(p1 - p0, p2 - p0), n_avg) < 0:
                tris.append((tri_base + i0, tri_base + i1, tri_base + i2))
                tris.append((tri_base + i0, tri_base + i2, tri_base + i3))
            else:
                tris.append((tri_base + i0, tri_base + i2, tri_base + i1))
                tris.append((tri_base + i0, tri_base + i3, tri_base + i2))


def _add_glow_core(verts: list, norms: list, st: list, tris: list, rx: float, ry: float, rz: float, tri_base: int = 0) -> None:
    """Add a glowing octahedral energy core at the center of the 4 rocket launchers."""
    base = len(verts)
    pts = [
        (rx, 0.0, 0.0),
        (-rx, 0.0, 0.0),
        (0.0, ry, 0.0),
        (0.0, -ry, 0.0),
        (0.0, 0.0, rz),
        (0.0, 0.0, -rz),
    ]
    uvs = [
        (0.5, 0.0),
        (0.5, 1.0),
        (0.0, 0.5),
        (1.0, 0.5),
        (0.25, 0.25),
        (0.75, 0.75),
    ]
    for p, uv in zip(pts, uvs):
        l = math.sqrt(p[0] * p[0] + p[1] * p[1] + p[2] * p[2]) or 1.0
        verts.append(p)
        norms.append((p[0] / l, p[1] / l, p[2] / l))
        st.append(uv)

    faces = [
        (0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
        (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5),
    ]
    for a, b, c in faces:
        p0 = np.array(verts[base + a])
        p1 = np.array(verts[base + b])
        p2 = np.array(verts[base + c])
        outward = p0 + p1 + p2
        if np.dot(np.cross(p1 - p0, p2 - p0), outward) < 0:
            tris.append((tri_base + base + a, tri_base + base + b, tri_base + base + c))
        else:
            tris.append((tri_base + base + a, tri_base + base + c, tri_base + base + b))


def build_powerup_md3(q15_pk3: Path, out_dir: Path) -> None:
    """Build progs/triple_wheeled.md3 with 4 clustered rocket launchers + glowing shell/rings."""
    vv0, nn0, st0, tris0, tex_bytes = _load_aligned_rocket_launcher(q15_pk3)

    # Scale each RL so the 4-launcher cluster sits cleanly inside ~42x28x28u
    rl_scale = 0.88
    vv0 = vv0 * rl_scale

    # 4 rocket launcher placements all pointing forward (+X):
    # (rx_roll_deg, ry_pitch_deg, rz_yaw_deg)
    # Bottom-Right (upright), Bottom-Left (upright), Top-Right (upside down), Top-Left (upside down)
    placements = [
        ((0.0, -6.8, -5.8), (0.0, 0.0, -4.0)),      # Bottom-Right, upright
        ((0.0, +6.8, -5.8), (0.0, 0.0, +4.0)),      # Bottom-Left, upright
        ((0.0, -6.8, +5.8), (180.0, 0.0, -4.0)),    # Top-Right, upside down (180 roll around X)
        ((0.0, +6.8, +5.8), (180.0, 0.0, +4.0)),    # Top-Left, upside down (180 roll around X)
    ]

    # Build 12 animated pulse/bob frames? Or 1 static frame and QC spins/bobs the entity!
    # Actually 16 subtle internal breathing/ring-pulse frames make even static screenshots look alive,
    # while QC spins the entity rapidly on Y and bobs Z.
    n_frames = 16

    # Surface 1: the 4 rocket launchers
    s1_st = st0 * 4
    s1_tris = []
    nv_one = len(vv0)
    for k in range(4):
        off = k * nv_one
        for a, b, c in tris0:
            s1_tris.append((a + off, b + off, c + off))

    s1_frames = []
    for fi in range(n_frames):
        phase = (fi / n_frames) * 2.0 * math.pi
        breathe = 1.0 + 0.03 * math.sin(phase)
        f_verts = []
        f_norms = []
        for (pos, rot_deg) in placements:
            rmat = _rot_matrix(*rot_deg)
            tv = vv0 @ rmat.T + np.array(pos) * breathe
            tn = nn0 @ rmat.T
            f_verts.extend(map(tuple, tv))
            f_norms.extend(map(tuple, tn))
        s1_frames.append((f_verts, f_norms))

    # Surface 2: glowing additive outer shell around all 4 launchers + glowing core & twin halo rings
    s2_st = list(st0 * 4)
    s2_tris = []
    for k in range(4):
        off = k * nv_one
        for a, b, c in tris0:
            s2_tris.append((a + off, b + off, c + off))

    # Build template ring & core geometry once to capture topology
    ring_verts_0: list = []
    ring_norms_0: list = []
    tri_base = 4 * nv_one
    _add_torus_ring(ring_verts_0, ring_norms_0, s2_st, s2_tris, major_r=12.8, minor_r=1.05, n_maj=24, n_min=8, x_offset=-5.5, tri_base=tri_base)
    _add_torus_ring(ring_verts_0, ring_norms_0, s2_st, s2_tris, major_r=12.8, minor_r=1.05, n_maj=24, n_min=8, x_offset=+5.5, tri_base=tri_base)
    _add_glow_core(ring_verts_0, ring_norms_0, s2_st, s2_tris, rx=9.5, ry=4.6, rz=4.6, tri_base=tri_base)

    s2_frames = []
    for fi in range(n_frames):
        phase = (fi / n_frames) * 2.0 * math.pi
        breathe = 1.0 + 0.03 * math.sin(phase)
        shell_inflate = 0.55 + 0.25 * math.sin(phase)
        f_verts = []
        f_norms = []
        for (pos, rot_deg) in placements:
            rmat = _rot_matrix(*rot_deg)
            tv = (vv0 + nn0 * shell_inflate) @ rmat.T + np.array(pos) * breathe
            tn = nn0 @ rmat.T
            f_verts.extend(map(tuple, tv))
            f_norms.extend(map(tuple, tn))
        # Rotate core + rings slightly per frame for extra electric spin inside the cluster
        ring_rot = _rot_matrix(fi * (360.0 / n_frames), 0.0, 0.0)
        rv_np = np.array(ring_verts_0, dtype=np.float64) @ ring_rot.T
        rn_np = np.array(ring_norms_0, dtype=np.float64) @ ring_rot.T
        f_verts.extend(map(tuple, rv_np))
        f_norms.extend(map(tuple, rn_np))
        s2_frames.append((f_verts, f_norms))

    model = {
        "name": "triple_wheeled",
        "frame_names": [f"spin_{i:02d}" for i in range(n_frames)],
        "surfaces": [
            {
                "name": "launchers",
                "shader": "progs/triple_wheeled_rl",
                "tris": s1_tris,
                "st": s1_st,
                "frames": s1_frames,
            },
            {
                "name": "glow_shell",
                "shader": "progs/triple_wheeled_glow",
                "tris": s2_tris,
                "st": s2_st,
                "frames": s2_frames,
            },
        ],
    }

    progs_dir = out_dir / "progs"
    progs_dir.mkdir(parents=True, exist_ok=True)
    md3lib.write(str(progs_dir / "triple_wheeled.md3"), model)
    (progs_dir / "triple_wheeled.md3_0.skin").write_text(
        "launchers,progs/triple_wheeled_rl\nglow_shell,progs/triple_wheeled_glow\n",
        encoding="ascii",
        newline="\n",
    )

    # Build bright warm-metallic RL texture (progs/triple_wheeled_rl.png)
    rl_img = Image.open(io.BytesIO(tex_bytes)).convert("RGB")
    rl_img = ImageEnhance.Color(rl_img).enhance(1.30)
    rl_img = ImageEnhance.Brightness(rl_img).enhance(1.35)
    rl_img.save(progs_dir / "triple_wheeled_rl.png", optimize=True)

    # Build procedural neon-gold/cyan plasma glow texture (progs/triple_wheeled_glow.png)
    w, h = 128, 128
    yy, xx = np.mgrid[0:h, 0:w]
    u = xx / w * 2.0 * math.pi
    v = yy / h * 2.0 * math.pi
    wave1 = 0.5 + 0.5 * np.sin(u * 2.0 + np.sin(v * 3.0) * 1.4)
    wave2 = 0.5 + 0.5 * np.cos(v * 2.0 - u * 1.0)
    streak = np.clip(wave1 * 0.6 + wave2 * 0.4, 0.0, 1.0) ** 1.4
    r = np.clip(90 + 165 * streak, 0, 255).astype(np.uint8)
    g = np.clip(60 + 160 * (streak ** 0.85), 0, 255).astype(np.uint8)
    b = np.clip(25 + 190 * ((1.0 - wave1) * 0.55 + streak * 0.45), 0, 255).astype(np.uint8)
    glow_arr = np.stack([r, g, b], axis=-1)
    Image.fromarray(glow_arr, "RGB").save(progs_dir / "triple_wheeled_glow.png", optimize=True)


def build_shader(out_dir: Path) -> None:
    scripts_dir = out_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    shader_text = """\
progs/triple_wheeled_rl
{
\tcull none
\t{
\t\tmap progs/triple_wheeled_rl
\t\trgbGen lightingDiffuse
\t}
\t{
\t\tmap progs/triple_wheeled_rl
\t\tblendfunc add
\t\trgbGen wave sin 0.42 0.28 0 2.6
\t}
}

progs/triple_wheeled_glow
{
\tcull none
\tsurfaceparm nomarks
\tsurfaceparm trans
\tsurfaceparm nolightmap
\t{
\t\tmap progs/triple_wheeled_glow
\t\tblendfunc add
\t\ttcMod scroll 0.55 0.35
\t\trgbGen wave sin 0.62 0.35 0 2.8
\t}
}
"""
    (scripts_dir / "triple_wheeled.shader").write_text(shader_text, encoding="ascii", newline="\n")


def _write_wav(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def build_sounds(out_dir: Path) -> None:
    snd_dir = out_dir / "sound" / "triple_wheeled"
    snd_dir.mkdir(parents=True, exist_ok=True)

    # 1. pickup.wav: 4 rapid mechanical launcher racks + rising hype fanfare chord
    dur = 1.25
    t = np.arange(int(SR * dur), dtype=np.float64) / SR
    sig = np.zeros_like(t)
    # 4 rapid metallic clacks at 0.00, 0.09, 0.18, 0.27s
    for idx, t0 in enumerate((0.0, 0.09, 0.18, 0.27)):
        dt = t - t0
        mask = (dt >= 0) & (dt < 0.10)
        f0 = 320 + idx * 75
        env = np.exp(-dt[mask] * 38.0)
        sig[mask] += 0.38 * env * (
            np.sin(2 * math.pi * f0 * dt[mask])
            + 0.5 * np.sin(2 * math.pi * (f0 * 2.4) * dt[mask])
        )
    # Rising brassy/synth hype powerup chord at 0.25..1.25s
    dt_c = np.maximum(0.0, t - 0.22)
    mask_c = t >= 0.22
    env_c = np.minimum(1.0, dt_c[mask_c] / 0.05) * np.exp(-dt_c[mask_c] * 2.4)
    chord = np.zeros_like(dt_c[mask_c])
    for freq in (261.63, 329.63, 392.00, 523.25, 659.25):
        chord += np.sin(2 * math.pi * freq * dt_c[mask_c])
    # Subtle vibrato whoosh
    sweep = np.sin(2 * math.pi * (220.0 + 440.0 * (1.0 - np.exp(-dt_c[mask_c] * 3.0))) * dt_c[mask_c])
    sig[mask_c] += (0.14 * chord + 0.18 * sweep) * env_c
    _write_wav(snd_dir / "pickup.wav", sig * 0.85)

    # 2. wearoff.wav: descending power-down whoosh
    dur2 = 0.65
    t2 = np.arange(int(SR * dur2), dtype=np.float64) / SR
    f_dn = 540.0 * np.exp(-t2 * 2.8) + 95.0
    phase = 2.0 * math.pi * np.cumsum(f_dn) / SR
    env2 = np.minimum(1.0, t2 / 0.03) * np.exp(-t2 * 4.2)
    sig2 = 0.6 * env2 * (np.sin(phase) + 0.35 * np.sin(phase * 0.5))
    _write_wav(snd_dir / "wearoff.wav", sig2)


def pack_pk3(src_dir: Path, out_pk3: Path) -> None:
    out_pk3.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_pk3.with_suffix(".pk3.tmp")
    files = sorted(
        (p for p in src_dir.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(src_dir).as_posix(),
    )
    with zipfile.ZipFile(tmp, "w") as z:
        for p in files:
            arc = p.relative_to(src_dir).as_posix()
            zi = zipfile.ZipInfo(arc, date_time=FIXED_DATE)
            zi.external_attr = FILE_ATTR
            ext = p.suffix.lower()
            if ext in STORE_EXTS:
                zi.compress_type = zipfile.ZIP_STORED
                z.writestr(zi, p.read_bytes())
            else:
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    os.replace(tmp, out_pk3)


def build_once(q15_pk3: Path, out_pk3: Path) -> str:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        build_powerup_md3(q15_pk3, root)
        build_shader(root)
        build_sounds(root)
        pack_pk3(root, out_pk3)
    return hashlib.sha256(out_pk3.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("q15_pk3", nargs="?", default=str(REPO_ROOT.parent / "quake15" / "q15.pk3"))
    ap.add_argument("out_pk3", nargs="?", default=str(REPO_ROOT / "zz_triple_wheeled.pk3"))
    ap.add_argument("--verify-repro", action="store_true")
    args = ap.parse_args()

    q15 = Path(args.q15_pk3)
    out = Path(args.out_pk3)
    if not q15.is_file():
        sys.exit(f"missing q15.pk3: {q15}")

    h1 = build_once(q15, out)
    if args.verify_repro:
        with tempfile.TemporaryDirectory() as td2:
            out2 = Path(td2) / "check.pk3"
            h2 = build_once(q15, out2)
        if h1 != h2:
            sys.exit(f"repro check failed: {h1} != {h2}")
        print(f"repro ok: {out.name} sha256={h1} ({out.stat().st_size} bytes)")
    else:
        print(f"built {out} sha256={h1} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
