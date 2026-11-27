"""Build reproducible zz_selected_sounds.pk3 from committed WAV assets.

Packs all WAVs under source/mm_tools/selected_sounds/assets/sound/ into
zz_selected_sounds.pk3 with deterministic timestamps (1980-01-01 00:00:00),
fixed file permissions, sorted entry paths, and ZIP_DEFLATED level 6.

Standard library only.

Usage:
  python3 -I source/mm_tools/selected_sounds/build_selected_sounds_pk3.py <out.pk3> [--verify-repro]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o644 << 16


def build_pk3(out_path: Path) -> str:
    files = sorted(p for p in ASSETS.rglob("*.wav") if p.is_file())
    if not files:
        sys.exit(f"No .wav assets found under {ASSETS}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".pk3.tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    with zipfile.ZipFile(tmp_path, "w") as zf:
        for p in files:
            arcname = p.relative_to(ASSETS).as_posix()
            zi = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
            zi.create_system = 3
            zi.external_attr = FILE_ATTR
            zf.writestr(zi, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    os.replace(tmp_path, out_path)
    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"Built {out_path} ({len(files)} wavs, {out_path.stat().st_size:,} bytes) sha256={digest}")
    return digest


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Build reproducible zz_selected_sounds.pk3.")
    parser.add_argument("out_pk3", help="Output path for zz_selected_sounds.pk3")
    parser.add_argument("--verify-repro", action="store_true", help="Build twice and assert identical SHA-256")
    args = parser.parse_args(argv)

    out_path = Path(args.out_pk3).resolve()
    sha1 = build_pk3(out_path)
    if args.verify_repro:
        with tempfile.TemporaryDirectory() as td:
            sha2 = build_pk3(Path(td) / "repro.pk3")
        if sha1 != sha2:
            sys.exit(f"Reproducibility check failed: {sha1} != {sha2}")
        print(f"Reproducibility OK: {sha1}")


if __name__ == "__main__":
    main()
