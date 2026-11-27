#!/usr/bin/env python3
"""Build the reproducible BakersfieldQuake overlay package: zz_dn3fx.pk3.

Never touches bakersfield.pk3 or quake15/q15.pk3, and writes ZERO loose files
into repo `progs/`, `scripts/`, or `sound/`.

Packages DN3DooM blood, gore, fire, smoke, explosion sprites, decal MD3s,
3D flesh gibs, shaders, and FX sounds:
  - progs/dn3fx_bloodpuff.spr32   (4 frames: BLUDA0..D0)
  - progs/dn3fx_blooddrop.spr32   (8 frames: GIB6A0..H0)
  - progs/dn3fx_gore2d.spr32      (25 frames: GIB1A0..E0 .. GIB5A0..E0)
  - progs/dn3fx_explode.spr32     (21 frames: RPGBB0..V0)
  - progs/dn3fx_fireball.spr32    (14 frames: FRB1A0..N0)
  - progs/dn3fx_flame.spr32       (32 frames: FIR3A0..P0 + FIR6A0..P0)
  - progs/dn3fx_smoke.spr32       (16 frames: SMOKA0..P0)
  - progs/dn3fx_shockwave.spr32   (9 frames: SHW2A0..I0)
  - progs/dn3fx_wallsplat.md3     (4-frame wall splatter quad + DNBLUD1..4)
  - progs/dn3fx_pool.md3          (5-frame floor blood pool quad + bloodpool2/CBL1..4)
  - progs/dn3fx_flesh1.md3        (3D gore chunk from Models/Gore/flesh1.md3)
  - scripts/dn3fx.shader          (polygonoffset + blend shaders)
  - sound/dn3fx/*                 (flesh hits, gib squish, explosion, fire, ricochets)

Usage:
  python -I source/mm_tools/dn3_fx/build_dn3fx_pk3.py [--out <path>] [--check-repro]
  python -I source/mm_tools/dn3_fx/build_dn3fx_pk3.py <base_bakersfield.pk3> <out_zz_dn3fx.pk3>
"""
from __future__ import annotations

import argparse
import hashlib
import io
import math
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
ASSETS_DIR = HERE / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
MODELS_DIR = ASSETS_DIR / "models"
SOUND_DIR = ASSETS_DIR / "sound"
DEFAULT_OUT_PK3 = REPO_ROOT / "zz_dn3fx.pk3"

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16

SPR_VP_PARALLEL_UPRIGHT = 0
SPR_VP_PARALLEL = 2

SOUND_FILES = (
    "hflesh.ogg",
    "organic1.ogg",
    "organic2.ogg",
    "dsslop.wav",
    "fire09.ogg",
    "bulithit.ogg",
    "ricoche1.wav",
    "ricoche2.wav",
    "ricoche3.wav",
    "ricoche4.wav",
)


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, format="PNG", compress_level=9, optimize=False)
    return buf.getvalue()


def _bleed_transparent_rgb(img: Image.Image, passes: int = 3) -> Image.Image:
    """Copy nearest opaque neighbor RGB into alpha==0 pixels to prevent white bilinear halos."""
    arr = np.array(img.convert("RGBA"), dtype=np.uint8)
    alpha = arr[:, :, 3]
    filled = alpha > 0
    rgb = arr[:, :, :3].copy()
    rgb[~filled] = 0
    for _ in range(passes):
        if filled.all():
            break
        acc = np.zeros((arr.shape[0], arr.shape[1], 3), dtype=np.int32)
        cnt = np.zeros((arr.shape[0], arr.shape[1], 1), dtype=np.int32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            s_y0, s_y1 = max(0, -dy), arr.shape[0] - max(0, dy)
            d_y0, d_y1 = max(0, dy), arr.shape[0] - max(0, -dy)
            s_x0, s_x1 = max(0, -dx), arr.shape[1] - max(0, dx)
            d_x0, d_x1 = max(0, dx), arr.shape[1] - max(0, -dx)
            m = filled[s_y0:s_y1, s_x0:s_x1]
            acc[d_y0:d_y1, d_x0:d_x1][m] += rgb[s_y0:s_y1, s_x0:s_x1][m]
            cnt[d_y0:d_y1, d_x0:d_x1, 0][m] += 1
        grow = (~filled) & (cnt[:, :, 0] > 0)
        rgb[grow] = (acc[grow] // cnt[grow]).astype(np.uint8)
        filled |= grow
    arr[:, :, :3] = rgb
    return Image.fromarray(arr, mode="RGBA")


def _load_rgba_frames(
    filenames: list[str],
    scale: int = 2,
    pivot_y_ratio: float = 0.5,
) -> list[tuple[np.ndarray, int, int]]:
    frames: list[tuple[np.ndarray, int, int]] = []
    for fname in filenames:
        src = SPRITES_DIR / fname
        if not src.is_file():
            raise FileNotFoundError(f"Missing sprite: {src}")
        with Image.open(src) as im:
            rgba = im.convert("RGBA")
            if scale != 1:
                rgba = rgba.resize((rgba.width * scale, rgba.height * scale), Image.Resampling.NEAREST)
            arr = np.asarray(rgba, dtype=np.uint8)
            h, w = arr.shape[:2]
            ox = -(w // 2)
            oy = int(round(h * pivot_y_ratio))
            frames.append((arr, ox, oy))
    return frames


def _build_spr32_bytes(frames: list[tuple[np.ndarray, int, int]], spr_type: int) -> bytes:
    max_w = max(fr.shape[1] for fr, _, _ in frames)
    max_h = max(fr.shape[0] for fr, _, _ in frames)
    max_r = 0.0
    for fr, ox, oy in frames:
        h, w = fr.shape[:2]
        for cx in (ox, ox + w):
            for cy in (oy, oy - h):
                max_r = max(max_r, math.hypot(cx, cy))

    buf = io.BytesIO()
    # dsprite_t: ident(4), version(32), type, radius, w, h, nframes, beam, synctype
    buf.write(
        struct.pack(
            "<4siifiiifi",
            b"IDSP",
            32,
            int(spr_type),
            float(max_r),
            int(max_w),
            int(max_h),
            len(frames),
            0.0,
            0,
        )
    )
    for fr, ox, oy in frames:
        h, w = fr.shape[:2]
        buf.write(struct.pack("<iiiii", 0, int(ox), int(oy), int(w), int(h)))
        buf.write(np.ascontiguousarray(fr, dtype=np.uint8).tobytes())
    return buf.getvalue()


def _encode_normal(nx: float, ny: float, nz: float) -> int:
    # MD3 spherical normal encoding (lat, lng in 0..255)
    if abs(nx) < 1e-6 and abs(ny) < 1e-6:
        return (0 << 8) | (0 if nz >= 0 else 128)
    lng = int(round(math.atan2(ny, nx) * 255.0 / (2.0 * math.pi))) & 0xFF
    lat = int(round(math.acos(max(-1.0, min(1.0, nz))) * 255.0 / (2.0 * math.pi))) & 0xFF
    return (lng << 8) | lat


def _build_multiframe_quad_md3(
    model_name: str,
    surf_prefix: str,
    shader_prefix: str,
    quads: list[tuple[tuple[float, float, float], ...]],
    normal: tuple[float, float, float],
) -> bytes:
    """Build a multi-frame MD3 where frame i shows surface i and collapses others."""
    num_frames = len(quads)
    num_surfs = len(quads)
    uvs = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    tris = ((0, 1, 2), (0, 2, 3))
    enc_norm = _encode_normal(*normal)

    ofs_frames = 108
    ofs_tags = ofs_frames + num_frames * 56
    ofs_surfs = ofs_tags

    surf_blobs: list[bytes] = []
    for s_idx in range(num_surfs):
        s_name = f"{surf_prefix}{s_idx}".encode("ascii")[:63].ljust(64, b"\x00")
        sh_name = f"{shader_prefix}{s_idx}".encode("ascii")[:63].ljust(64, b"\x00")

        # MD3 surface header is 108 bytes
        ofs_tris = 108
        ofs_shaders = ofs_tris + len(tris) * 12
        ofs_st = ofs_shaders + 68
        ofs_xyz = ofs_st + 4 * 8
        ofs_end = ofs_xyz + num_frames * 4 * 8

        sb = io.BytesIO()
        sb.write(
            struct.pack(
                "<4s64s10i",
                b"IDP3",
                s_name,
                0,
                num_frames,
                1,
                4,
                len(tris),
                ofs_tris,
                ofs_shaders,
                ofs_st,
                ofs_xyz,
                ofs_end,
            )
        )
        for a, b, c in tris:
            sb.write(struct.pack("<3i", a, b, c))
        sb.write(struct.pack("<64si", sh_name, 0))
        for u, v in uvs:
            sb.write(struct.pack("<2f", u, v))
        for f_idx in range(num_frames):
            verts = quads[s_idx] if f_idx == s_idx else ((0.0, 0.0, 0.0),) * 4
            for vx, vy, vz in verts:
                sb.write(
                    struct.pack(
                        "<hhhH",
                        int(round(vx * 64.0)),
                        int(round(vy * 64.0)),
                        int(round(vz * 64.0)),
                        enc_norm,
                    )
                )
        surf_blobs.append(sb.getvalue())

    ofs_eof = ofs_surfs + sum(len(b) for b in surf_blobs)

    buf = io.BytesIO()
    buf.write(
        struct.pack(
            "<4si64s9i",
            b"IDP3",
            15,
            model_name.encode("ascii")[:63].ljust(64, b"\x00"),
            0,
            num_frames,
            0,
            num_surfs,
            0,
            ofs_frames,
            ofs_tags,
            ofs_surfs,
            ofs_eof,
        )
    )
    for f_idx in range(num_frames):
        verts = quads[f_idx]
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        zs = [v[2] for v in verts]
        radius = max(math.sqrt(vx * vx + vy * vy + vz * vz) for vx, vy, vz in verts)
        fname = f"f{f_idx}".encode("ascii").ljust(16, b"\x00")
        buf.write(
            struct.pack(
                "<3f3f3ff16s",
                min(xs), min(ys), min(zs),
                max(xs), max(ys), max(zs),
                0.0, 0.0, 0.0,
                float(radius),
                fname,
            )
        )
    for b in surf_blobs:
        buf.write(b)
    return buf.getvalue()


def _patch_flesh_md3(src_bytes: bytes, shader_name: str) -> bytes:
    data = bytearray(src_bytes)
    num_surfs = struct.unpack_from("<i", data, 84)[0]
    ofs_surfs = struct.unpack_from("<i", data, 100)[0]
    if num_surfs < 1:
        return bytes(data)
    ofs_shaders = struct.unpack_from("<i", data, ofs_surfs + 92)[0]
    sh_pos = ofs_surfs + ofs_shaders
    data[sh_pos : sh_pos + 64] = shader_name.encode("ascii")[:63].ljust(64, b"\x00")
    return bytes(data)


def _build_shader_text() -> str:
    lines = ["// Generated by source/mm_tools/dn3_fx/build_dn3fx_pk3.py"]
    for i in range(4):
        lines.append(
            f"""progs/dn3fx_wall_v{i}
{{
\tcull none
\tnopicmip
\tpolygonoffset
\t{{
\t\tmap progs/dn3fx_wall_{i}
\t\tblendfunc blend
\t\trgbGen lightingDiffuse
\t}}
}}"""
        )
    for i in range(5):
        lines.append(
            f"""progs/dn3fx_pool_v{i}
{{
\tcull none
\tnopicmip
\tpolygonoffset
\t{{
\t\tmap progs/dn3fx_pool_{i}
\t\tblendfunc blend
\t\trgbGen lightingDiffuse
\t}}
}}"""
        )
    lines.append(
        """progs/dn3fx_flesh1
{
\tcull none
\t{
\t\tmap progs/dn3fx_flesh1
\t\trgbGen lightingDiffuse
\t}
}"""
    )
    return "\n".join(lines) + "\n"


def _collect_entries() -> dict[str, bytes]:
    entries: dict[str, bytes] = {}

    # 1. Animated .spr32 billboards
    entries["progs/dn3fx_bloodpuff.spr32"] = _build_spr32_bytes(
        _load_rgba_frames([f"BLUD{c}0.png" for c in "ABCD"], scale=2, pivot_y_ratio=0.5),
        SPR_VP_PARALLEL,
    )
    entries["progs/dn3fx_blooddrop.spr32"] = _build_spr32_bytes(
        _load_rgba_frames([f"GIB6{c}0.png" for c in "ABCDEFGH"], scale=2, pivot_y_ratio=0.5),
        SPR_VP_PARALLEL,
    )
    gore_names = [f"GIB{g}{c}0.png" for g in range(1, 6) for c in "ABCDE"]
    entries["progs/dn3fx_gore2d.spr32"] = _build_spr32_bytes(
        _load_rgba_frames(gore_names, scale=2, pivot_y_ratio=0.5),
        SPR_VP_PARALLEL,
    )
    flame_names = [f"FIR3{c}0.png" for c in "ABCDEFGHIJKLMNOP"] + [
        f"FIR6{c}0.png" for c in "ABCDEFGHIJKLMNOP"
    ]
    entries["progs/dn3fx_flame.spr32"] = _build_spr32_bytes(
        _load_rgba_frames(flame_names, scale=2, pivot_y_ratio=0.85),
        SPR_VP_PARALLEL_UPRIGHT,
    )
    entries["progs/dn3fx_smoke.spr32"] = _build_spr32_bytes(
        _load_rgba_frames([f"SMOK{c}0.png" for c in "ABCDEFGHIJKLMNOP"], scale=2, pivot_y_ratio=0.5),
        SPR_VP_PARALLEL,
    )

    # 2. Wall blood splatters (YZ plane facing +X so vectoangles(normal) aligns flush)
    wall_quads = [
        (
            (0.0, 7.5, 15.0),
            (0.0, -7.5, 15.0),
            (0.0, -7.5, -15.0),
            (0.0, 7.5, -15.0),
        )
        for _ in range(4)
    ]
    entries["progs/dn3fx_wallsplat.md3"] = _build_multiframe_quad_md3(
        "progs/dn3fx_wallsplat.md3",
        "wall",
        "progs/dn3fx_wall_v",
        wall_quads,
        (1.0, 0.0, 0.0),
    )
    for i in range(4):
        src = SPRITES_DIR / f"DNBLUD{i + 1}.png"
        with Image.open(src) as im:
            clean = _bleed_transparent_rgb(im)
            up = clean.resize((clean.width * 2, clean.height * 2), Image.Resampling.NEAREST)
            entries[f"progs/dn3fx_wall_{i}.png"] = _png_bytes(up)

    # 3. Floor blood pools (XY plane facing +Z)
    pool_quads = [
        (
            (16.0, 16.0, 0.0),
            (16.0, -16.0, 0.0),
            (-16.0, -16.0, 0.0),
            (-16.0, 16.0, 0.0),
        )
        for _ in range(5)
    ]
    entries["progs/dn3fx_pool.md3"] = _build_multiframe_quad_md3(
        "progs/dn3fx_pool.md3",
        "pool",
        "progs/dn3fx_pool_v",
        pool_quads,
        (0.0, 0.0, 1.0),
    )
    pool_srcs = ["bloodpool2.png", "CBL1E0.png", "CBL2E0.png", "CBL3E0.png", "CBL4E0.png"]
    for i, fname in enumerate(pool_srcs):
        src = SPRITES_DIR / fname
        with Image.open(src) as im:
            entries[f"progs/dn3fx_pool_{i}.png"] = _png_bytes(_bleed_transparent_rgb(im))

    # 4. 3D flesh chunk MD3
    flesh_src = MODELS_DIR / "flesh1.md3"
    entries["progs/dn3fx_flesh1.md3"] = _patch_flesh_md3(flesh_src.read_bytes(), "progs/dn3fx_flesh1")
    with Image.open(SPRITES_DIR / "flesh1.png") as im:
        entries["progs/dn3fx_flesh1.png"] = _png_bytes(im)

    # 5. Shaders
    entries["scripts/dn3fx.shader"] = _build_shader_text().encode("utf-8")

    # 6. Sounds
    for fname in SOUND_FILES:
        src = SOUND_DIR / fname
        if not src.is_file():
            raise FileNotFoundError(f"Missing sound: {src}")
        entries[f"sound/dn3fx/{fname}"] = src.read_bytes()

    return entries


def build_pk3(out_path: Path) -> Path:
    entries = _collect_entries()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w") as zf:
        for name in sorted(entries):
            data = entries[name]
            zi = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            zi.external_attr = FILE_ATTR
            ext = Path(name).suffix.lower()
            if ext in (".png", ".jpg", ".ogg"):
                zf.writestr(zi, data, compress_type=zipfile.ZIP_STORED)
            else:
                zf.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return out_path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positional", nargs="*", help="Optional <base_bakersfield.pk3> <out_pk3>")
    parser.add_argument("--out", type=Path, default=None, help="Output pk3 path")
    parser.add_argument("--check-repro", action="store_true", help="Build twice and assert identical sha256")
    args = parser.parse_args(argv)

    if len(args.positional) == 2:
        out_path = Path(args.positional[1])
    elif len(args.positional) == 1:
        out_path = Path(args.positional[0])
    elif args.out is not None:
        out_path = args.out
    else:
        out_path = DEFAULT_OUT_PK3

    if args.check_repro:
        with tempfile.TemporaryDirectory() as td:
            p1 = build_pk3(Path(td) / "a.pk3")
            p2 = build_pk3(Path(td) / "b.pk3")
            h1, h2 = _sha256(p1), _sha256(p2)
            if h1 != h2:
                print(f"ERROR: non-reproducible build! {h1} != {h2}", file=sys.stderr)
                return 1
            print(f"Reproducible OK: sha256={h1} size={p1.stat().st_size}")

    built = build_pk3(out_path)
    print(f"Wrote {built} ({built.stat().st_size:,} bytes, sha256={_sha256(built)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
