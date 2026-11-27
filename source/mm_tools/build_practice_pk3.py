#!/usr/bin/env python3
"""Build zz_practice.pk3: dark starry space skybox + dark metallic space-deck textures.

Generates:
  - gfx/env/pracspace_{bk,dn,ft,lf,rt,up}.png (1024x1024 seamless 3D cubemap)
  - textures/prac_deck.png  (256x256 dark steel deck plating)
  - textures/prac_pit.png   (256x256 dark industrial shaft plating)
  - textures/prac_trim.png  (256x256 dark charcoal steel trim)

Uses DarkPlaces' exact skybox face mapping (matching source/mm_tools/build_bklan_sky.py)
so nebula clouds and stars cross cube edges seamlessly.

Reproducible: fixed seed, fixed 1980-01-01 zip timestamps, sorted entry order,
ZIP_STORED PNGs, deterministic NumPy/Pillow output (--verify-repro).

Usage:
  python -I source/mm_tools/build_practice_pk3.py <out_pk3> [--verify-repro]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16

SKY_SIZE = 1024
TEX_SIZE = 256

# DarkPlaces skybox filename mapping (see source/mm_tools/build_bklan_sky.py):
# facing +x shows "rt", turning right (-y) shows "ft", -x shows "lf", +y shows "bk";
# "up" is stored vertically flipped.
FILE_MAP = {"ft": "rt", "rt": "ft", "bk": "lf", "lf": "bk", "up": "up", "dn": "dn"}

# (fwd, right, down) basis vectors per logical look direction (matches build_bklan_sky.faces)
FACE_BASIS: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]] = {
    "ft": ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)),
    "bk": ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)),
    "lf": ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    "rt": ((0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    "up": ((0.0, 0.0, 1.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0)),
    "dn": ((0.0, 0.0, -1.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),
}


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _face_dirs(face: str, n: int) -> np.ndarray:
    """Return unit 3D direction vectors (n, n, 3) for every pixel on a cubemap face."""
    fwd, rgt, dwn = FACE_BASIS[face]
    t = np.linspace(-1.0, 1.0, n, dtype=np.float32)
    u, v = np.meshgrid(t, t)
    dx = fwd[0] + u * rgt[0] + v * dwn[0]
    dy = fwd[1] + u * rgt[1] + v * dwn[1]
    dz = fwd[2] + u * rgt[2] + v * dwn[2]
    inv_len = 1.0 / np.sqrt(dx * dx + dy * dy + dz * dz)
    return np.stack((dx * inv_len, dy * inv_len, dz * inv_len), axis=-1)


def _fbm_3d(dirs: np.ndarray, planes: list[tuple[np.ndarray, float, float]]) -> np.ndarray:
    """Evaluate smooth seamless 3D trigonometric nebula waves over unit direction vectors."""
    acc = np.zeros(dirs.shape[:2], dtype=np.float32)
    for kvec, phase, amp in planes:
        proj = dirs[..., 0] * kvec[0] + dirs[..., 1] * kvec[1] + dirs[..., 2] * kvec[2] + phase
        acc += amp * (0.5 + 0.5 * np.sin(proj))
    return acc


def build_skybox_faces() -> dict[str, bytes]:
    rng = np.random.default_rng(19991202)

    # Subtle 3D purple/indigo nebula clouds (tuned low so Zircon HDR/gamma keeps space pitch black)
    neb_planes_a = []
    for octv in range(5):
        freq = 1.6 * (1.75 ** octv)
        amp = 0.52 ** (octv + 1)
        for _ in range(3):
            v = rng.normal(size=3).astype(np.float32)
            v = v / np.linalg.norm(v) * freq
            neb_planes_a.append((v, float(rng.uniform(0, 6.283)), amp))

    neb_planes_b = []
    for octv in range(4):
        freq = 2.2 * (1.8 ** octv)
        amp = 0.50 ** (octv + 1)
        for _ in range(3):
            v = rng.normal(size=3).astype(np.float32)
            v = v / np.linalg.norm(v) * freq
            neb_planes_b.append((v, float(rng.uniform(0, 6.283)), amp))

    # Uniform 3D star catalog on the unit sphere (~4,600 crisp stars)
    n_stars = 4600
    star_xyz = rng.normal(size=(n_stars, 3)).astype(np.float32)
    star_xyz /= np.linalg.norm(star_xyz, axis=1, keepdims=True)
    star_bright = (rng.random(n_stars) ** 4.2).astype(np.float32) * 0.92 + 0.08
    tint_roll = rng.random(n_stars)
    star_rgb = np.ones((n_stars, 3), dtype=np.float32)
    cool = tint_roll < 0.32
    warm = tint_roll > 0.86
    star_rgb[cool] = np.array([0.75, 0.85, 1.0], dtype=np.float32)
    star_rgb[warm] = np.array([1.0, 0.90, 0.75], dtype=np.float32)
    star_sigma = np.where(star_bright > 0.65, 0.72, 0.44).astype(np.float32)

    out: dict[str, bytes] = {}
    for face in sorted(FACE_BASIS):
        dirs = _face_dirs(face, SKY_SIZE)
        n_a = _fbm_3d(dirs, neb_planes_a)
        n_b = _fbm_3d(dirs, neb_planes_b)
        mask_a = np.clip((n_a - 1.40) * 1.65, 0.0, 1.0) ** 2.4
        mask_b = np.clip((n_b - 1.32) * 1.55, 0.0, 1.0) ** 2.6

        # Pitch-black deep space with faint purple/indigo nebula glow
        img = np.zeros((SKY_SIZE, SKY_SIZE, 3), dtype=np.float32)
        img[..., 0] = 1.0 + mask_a * 11.0 + mask_b * 5.0
        img[..., 1] = 1.0 + mask_a * 3.5 + mask_b * 5.0
        img[..., 2] = 2.0 + mask_a * 15.0 + mask_b * 13.0

        fwd, rgt, dwn = FACE_BASIS[face]
        f_v = np.array(fwd, dtype=np.float32)
        r_v = np.array(rgt, dtype=np.float32)
        d_v = np.array(dwn, dtype=np.float32)
        z_dot = star_xyz @ f_v
        in_front = z_dot > 0.35
        sx = (star_xyz[in_front] @ r_v) / z_dot[in_front]
        sy = (star_xyz[in_front] @ d_v) / z_dot[in_front]
        sb = star_bright[in_front]
        sc = star_rgb[in_front]
        ss = star_sigma[in_front]

        px_f = (sx + 1.0) * 0.5 * (SKY_SIZE - 1)
        py_f = (sy + 1.0) * 0.5 * (SKY_SIZE - 1)
        keep = (px_f >= -3) & (px_f <= SKY_SIZE + 2) & (py_f >= -3) & (py_f <= SKY_SIZE + 2)
        for cx, cy, br, col, sigma in zip(px_f[keep], py_f[keep], sb[keep], sc[keep], ss[keep]):
            sig = float(sigma)
            r_box = int(np.ceil(sig * 3.0))
            x0 = max(0, int(np.floor(cx)) - r_box)
            x1 = min(SKY_SIZE, int(np.ceil(cx)) + r_box + 1)
            y0 = max(0, int(np.floor(cy)) - r_box)
            y1 = min(SKY_SIZE, int(np.ceil(cy)) + r_box + 1)
            if x0 >= x1 or y0 >= y1:
                continue
            gx = np.arange(x0, x1, dtype=np.float32)[None, :] - cx
            gy = np.arange(y0, y1, dtype=np.float32)[:, None] - cy
            w = np.exp(-0.5 * (gx * gx + gy * gy) / (sig * sig)) * (br * 245.0)
            img[y0:y1, x0:x1] += w[..., None] * col[None, None, :]

        u8 = np.clip(img, 0, 255).astype(np.uint8)
        pil_im = Image.fromarray(u8, mode="RGB")
        if face == "up":
            pil_im = pil_im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        out_name = FILE_MAP[face]
        out[f"gfx/env/pracspace_{out_name}.png"] = _png_bytes(pil_im)
    return out


def build_deck_textures() -> dict[str, bytes]:
    rng = np.random.default_rng(20261127)
    n = TEX_SIZE
    grain = rng.normal(0.0, 2.2, size=(n, n)).astype(np.float32)

    # 1. prac_deck: dark slate/gunmetal 2x2 riveted plate floor
    deck = np.zeros((n, n, 3), dtype=np.float32)
    deck[..., 0] = 30.0 + grain
    deck[..., 1] = 33.0 + grain
    deck[..., 2] = 40.0 + grain
    for seam in (0, 1, 128, 129):
        deck[seam, :] *= 0.42
        deck[:, seam] *= 0.42
    for hi in (2, 130):
        deck[hi, :] += 5.0
        deck[:, hi] += 5.0
    for ty in (0, 128):
        for tx in (0, 128):
            for ry in (10, 118):
                for rx in (10, 118):
                    deck[ty + ry - 1 : ty + ry + 2, tx + rx - 1 : tx + rx + 2] += 10.0

    # 2. prac_pit: darker shaft metal with subtle horizontal rib seams
    pit = np.zeros((n, n, 3), dtype=np.float32)
    pit[..., 0] = 20.0 + grain * 0.8
    pit[..., 1] = 22.0 + grain * 0.8
    pit[..., 2] = 28.0 + grain * 0.8
    for y in range(0, n, 32):
        pit[y : y + 2, :] *= 0.45
        if y + 2 < n:
            pit[y + 2, :] += 4.0

    # 3. prac_trim: dark charcoal steel edge trim
    trim = np.zeros((n, n, 3), dtype=np.float32)
    trim[..., 0] = 38.0 + grain * 0.7
    trim[..., 1] = 41.0 + grain * 0.7
    trim[..., 2] = 49.0 + grain * 0.7
    trim[0:3, :] += 8.0
    trim[n - 3 : n, :] *= 0.55

    return {
        "textures/prac_deck.png": _png_bytes(Image.fromarray(np.clip(deck, 0, 255).astype(np.uint8), mode="RGB")),
        "textures/prac_pit.png": _png_bytes(Image.fromarray(np.clip(pit, 0, 255).astype(np.uint8), mode="RGB")),
        "textures/prac_trim.png": _png_bytes(Image.fromarray(np.clip(trim, 0, 255).astype(np.uint8), mode="RGB")),
    }


def build_pk3(out_path: Path) -> str:
    entries: dict[str, bytes] = {}
    entries.update(build_skybox_faces())
    entries.update(build_deck_textures())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w") as z:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, entries[name])
    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"Built {out_path} ({out_path.stat().st_size:,} B, {len(entries)} entries, sha256={digest})")
    return digest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path, help="Output zz_practice.pk3 path")
    ap.add_argument("--verify-repro", action="store_true", help="Build twice and assert identical SHA-256")
    args = ap.parse_args(argv)

    first = build_pk3(args.out)
    if args.verify_repro:
        tmp = args.out.with_suffix(".repro.pk3")
        second = build_pk3(tmp)
        tmp.unlink()
        if first != second:
            raise RuntimeError(f"NOT REPRODUCIBLE: {first} != {second}")
        print("reproducible: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
