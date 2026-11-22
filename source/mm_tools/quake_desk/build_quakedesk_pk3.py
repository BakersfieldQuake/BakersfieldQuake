#!/usr/bin/env python3
"""Build the reproducible BakersfieldQuake overlay package: zz_quakedesk.pk3.

Never touches bakersfield.pk3 or quake15/q15.pk3, and writes ZERO loose files
into repo `progs/` or `scripts/`. Uses only the Python standard library (no
Blender, NumPy, or Pillow required in CI).

Packages the audited Model B ("1996 LAN-Party Battlestation") MD3 with 3
distinct fullbright Quake 1 CRT skins (`qdesk_b.md3_0/1/2.skin`):
  - progs/qdesk_b.md3
  - progs/qdesk_b.md3_0.skin  (E2M1 Super Shotgun CRT)
  - progs/qdesk_b.md3_1.skin  (Start Hall Shotgun CRT)
  - progs/qdesk_b.md3_2.skin  (DM3 Rocket Launcher CRT)
  - progs/qdb_*.png           (11 textures: 9 Model B + 2 extra CRT screens)
  - scripts/qdesk_b.shader    (lightingDiffuse + rgbGen identity CRTs & LEDs)

Usage:
  python -I source/mm_tools/quake_desk/build_quakedesk_pk3.py [--out <path>] [--check-repro]
  python -I source/mm_tools/quake_desk/build_quakedesk_pk3.py <base_bakersfield.pk3> <out_zz_quakedesk.pk3>
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
ASSETS_DIR = HERE / "assets"
TEX_DIR = ASSETS_DIR / "tex"
DEFAULT_OUT_PK3 = REPO_ROOT / "zz_quakedesk.pk3"

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}

EXPECTED_SKINS = (
    "qdesk_b.md3_0.skin",
    "qdesk_b.md3_1.skin",
    "qdesk_b.md3_2.skin",
)

FULLBRIGHT_SHADERS = (
    "progs/qdb_crt_screen",
    "progs/qdb_crt_screen_a",
    "progs/qdb_crt_screen_c",
    "progs/qdb_leds",
)


def _read_md3_surface_names(md3_bytes: bytes) -> list[str]:
    """Parse MD3 binary header and surface names using stdlib struct only."""
    if len(md3_bytes) < 108:
        raise ValueError(f"MD3 too small: {len(md3_bytes)} bytes")
    ident, ver = struct.unpack_from("<4si", md3_bytes, 0)
    if ident != b"IDP3" or ver != 15:
        raise ValueError(f"Unexpected MD3 header: ident={ident!r}, ver={ver}")
    nframes, ntags, nsurfs, nskins, ofs_frames, ofs_tags, ofs_surfs, ofs_eof = struct.unpack_from(
        "<8i", md3_bytes, 76
    )
    if nframes < 1 or nsurfs < 1 or ofs_eof != len(md3_bytes):
        raise ValueError(
            f"Invalid MD3 counts/size: nframes={nframes}, nsurfs={nsurfs}, ofs_eof={ofs_eof}, len={len(md3_bytes)}"
        )
    names: list[str] = []
    cur = ofs_surfs
    for idx in range(nsurfs):
        s_ident = md3_bytes[cur : cur + 4]
        if s_ident != b"IDP3":
            raise ValueError(f"Bad surface {idx} magic {s_ident!r} at {cur}")
        s_name = md3_bytes[cur + 4 : cur + 68].split(b"\x00", 1)[0].decode("ascii")
        ofs_end = struct.unpack_from("<i", md3_bytes, cur + 104)[0]
        names.append(s_name)
        cur += ofs_end
    return names


def _collect_and_validate_entries() -> dict[str, bytes]:
    entries: dict[str, bytes] = {}

    md3_path = ASSETS_DIR / "qdesk_b.md3"
    if not md3_path.is_file():
        raise FileNotFoundError(f"Missing MD3 asset: {md3_path}")
    md3_bytes = md3_path.read_bytes()
    md3_surfs = _read_md3_surface_names(md3_bytes)
    entries["progs/qdesk_b.md3"] = md3_bytes

    shader_path = ASSETS_DIR / "qdesk_b.shader"
    if not shader_path.is_file():
        raise FileNotFoundError(f"Missing shader asset: {shader_path}")
    shader_bytes = shader_path.read_bytes()
    if b"\r" in shader_bytes:
        raise ValueError("qdesk_b.shader must use LF-only newlines")
    shader_text = shader_bytes.decode("ascii")
    entries["scripts/qdesk_b.shader"] = shader_bytes

    if not TEX_DIR.is_dir():
        raise FileNotFoundError(f"Missing texture directory: {TEX_DIR}")
    pngs = sorted(p for p in TEX_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".png")
    if not pngs:
        raise FileNotFoundError(f"No PNG textures found in {TEX_DIR}")
    for p in pngs:
        entries[f"progs/{p.name}"] = p.read_bytes()

    # Parse shader blocks & verify every map target + fullbright CRT/LED rgbGen identity
    defined_shaders: dict[str, str] = {}
    for m in re.finditer(r"^(progs/\S+)\s*\n(\{.*?\n\})", shader_text, re.MULTILINE | re.DOTALL):
        defined_shaders[m.group(1)] = m.group(2)

    for fb in FULLBRIGHT_SHADERS:
        if fb not in defined_shaders:
            raise ValueError(f"Missing fullbright shader block: {fb}")
        if "rgbGen identity" not in defined_shaders[fb]:
            raise ValueError(f"Shader {fb} must specify 'rgbGen identity'")

    map_refs = re.findall(r"^\s*map\s+(progs/\S+)\s*$", shader_text, re.MULTILINE)
    if not map_refs:
        raise ValueError("No map directives found in qdesk_b.shader")
    for mref in map_refs:
        png_key = mref if mref.endswith(".png") else f"{mref}.png"
        if png_key not in entries:
            raise ValueError(f"Shader references missing texture: {png_key}")

    # Load and cross-check all 3 skin files against MD3 surfaces & defined shaders
    for skin_fn in EXPECTED_SKINS:
        sp = ASSETS_DIR / skin_fn
        if not sp.is_file():
            raise FileNotFoundError(f"Missing skin file: {sp}")
        sb = sp.read_bytes()
        if b"\r" in sb:
            raise ValueError(f"{skin_fn} must use LF-only newlines")
        skin_lines = [ln.strip() for ln in sb.decode("ascii").splitlines() if ln.strip()]
        skin_surfs = []
        for ln in skin_lines:
            sname, sh_name = [tok.strip() for tok in ln.split(",", 1)]
            skin_surfs.append(sname)
            if sh_name not in defined_shaders:
                raise ValueError(f"{skin_fn} references undefined shader '{sh_name}'")
        if skin_surfs != md3_surfs:
            raise ValueError(f"{skin_fn} surfaces {skin_surfs} != MD3 surfaces {md3_surfs}")
        entries[f"progs/{skin_fn}"] = sb

    return entries


def _write_reproducible_pk3(out_pk3: Path, entries: dict[str, bytes]) -> str:
    out_pk3.parent.mkdir(parents=True, exist_ok=True)
    tmp_pk3 = out_pk3.with_suffix(out_pk3.suffix + ".tmp")
    if tmp_pk3.exists():
        tmp_pk3.unlink()

    with zipfile.ZipFile(tmp_pk3, "w") as zf:
        for arcname in sorted(entries.keys()):
            data = entries[arcname]
            ext = Path(arcname).suffix.lower()
            zi = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
            zi.create_system = 3
            zi.external_attr = FILE_ATTR
            if ext in STORE_EXTS:
                zi.compress_type = zipfile.ZIP_STORED
                zf.writestr(zi, data, compress_type=zipfile.ZIP_STORED)
            else:
                zi.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    os.replace(tmp_pk3, out_pk3)
    return hashlib.sha256(out_pk3.read_bytes()).hexdigest()


def build_pk3(out_pk3: Path) -> tuple[str, int, int]:
    entries = _collect_and_validate_entries()
    sha = _write_reproducible_pk3(out_pk3, entries)
    size = out_pk3.stat().st_size
    print(f"Built {out_pk3} ({len(entries)} entries, {size:,} bytes, sha256={sha})")
    return sha, size, len(entries)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build reproducible zz_quakedesk.pk3 overlay.")
    ap.add_argument("--out", type=Path, default=None, help="Output pk3 path (default: <repo>/zz_quakedesk.pk3)")
    ap.add_argument(
        "--check-repro",
        action="store_true",
        help="Build twice to temp paths and assert byte-identical SHA-256.",
    )
    ap.add_argument(
        "positional",
        nargs="*",
        help="Optional CI positional form: [<base_bakersfield.pk3>] <out_zz_quakedesk.pk3>",
    )
    args = ap.parse_args(argv)

    if args.out is not None:
        out_pk3 = args.out
    elif len(args.positional) >= 2:
        out_pk3 = Path(args.positional[1])
    elif len(args.positional) == 1:
        out_pk3 = Path(args.positional[0])
    else:
        out_pk3 = DEFAULT_OUT_PK3

    if args.check_repro:
        with tempfile.TemporaryDirectory(prefix="zz_quakedesk_repro_") as td:
            p1 = Path(td) / "run1.pk3"
            p2 = Path(td) / "run2.pk3"
            s1, sz1, n1 = build_pk3(p1)
            s2, sz2, n2 = build_pk3(p2)
            if s1 != s2 or sz1 != sz2 or n1 != n2:
                raise RuntimeError(f"Reproducibility check FAILED: {s1} != {s2}")
            print(f"Reproducibility PASSED: byte-identical sha256={s1} ({sz1:,} bytes)")

    build_pk3(out_pk3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
