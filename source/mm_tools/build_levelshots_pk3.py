#!/usr/bin/env python3
"""Build zz_levelshots.pk3: PNG copies of every map levelshot.

Zircon only decodes JPEG through an external jpeg62 library that the Linux and Windows packages don't ship, so
`levelshots/*.jpg` fail to load ("file loaded but decode failed") and the Host Game map cards came up empty
(playtest 1.76). PNG decoding is built into the engine, so the menu now prefers `levelshots/<map>.png`.

Inputs: the loose `levelshots/*.jpg` of a package's BakersfieldQuake folder, plus any `levelshots/*.jpg` inside
`--pk3` overlays (for example zz_bakersfieldish.pk3). Later inputs win on a name clash.

Reproducible: fixed zip dates and attributes, sorted entries, deterministic PNG encoding (pinned Pillow).

Usage:
  python -I build_levelshots_pk3.py <BakersfieldQuake dir> <out zz_levelshots.pk3> [--pk3 extra.pk3 ...] [--verify-repro]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import sys
import zipfile
from pathlib import Path

from PIL import Image

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
MAX_W, MAX_H = 512, 320  # the shots are 512x320 already; anything bigger is scaled down to the card size


def collect(game_dir: Path, extra_pk3s: list[Path]) -> dict[str, bytes]:
    shots: dict[str, bytes] = {}
    loose = game_dir / "levelshots"
    if loose.is_dir():
        for p in sorted(loose.iterdir()):
            if p.suffix.lower() == ".jpg" and p.is_file():
                shots[p.stem.lower()] = p.read_bytes()
    for pk3 in extra_pk3s:
        if not pk3.is_file():
            print(f"note: {pk3} not found, skipped")
            continue
        with zipfile.ZipFile(pk3) as z:
            for n in sorted(z.namelist()):
                low = n.lower()
                if low.startswith("levelshots/") and low.endswith(".jpg") and "/" not in low[len("levelshots/"):]:
                    shots[Path(low).stem] = z.read(n)
    return shots


def to_png(data: bytes) -> bytes:
    im = Image.open(io.BytesIO(data))
    im.load()
    im = im.convert("RGB")
    if im.width > MAX_W or im.height > MAX_H:
        im.thumbnail((MAX_W, MAX_H), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    im.save(out, format="PNG", optimize=True)
    return out.getvalue()


def build(game_dir: Path, out: Path, extra_pk3s: list[Path]) -> str:
    shots = collect(game_dir, extra_pk3s)
    if "_unknown" not in shots:
        sys.exit("levelshots/_unknown.jpg not found: the menu needs it as the fallback card")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        for stem in sorted(shots):
            info = zipfile.ZipInfo(f"levelshots/{stem}.png", date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, to_png(shots[stem]))
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{out}: {len(shots)} levelshots ({', '.join(sorted(shots))}) sha256 {digest}")
    return digest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("game_dir", type=Path, help="package BakersfieldQuake folder (holds levelshots/*.jpg)")
    ap.add_argument("out", type=Path, help="output zz_levelshots.pk3")
    ap.add_argument("--pk3", type=Path, action="append", default=[], help="overlay pk3 with more levelshots")
    ap.add_argument("--verify-repro", action="store_true", help="build twice and require identical bytes")
    a = ap.parse_args()
    first = build(a.game_dir, a.out, a.pk3)
    if a.verify_repro:
        tmp = a.out.with_suffix(".repro.pk3")
        second = build(a.game_dir, tmp, a.pk3)
        tmp.unlink()
        if first != second:
            sys.exit("NOT REPRODUCIBLE: two builds differ")
        print("reproducible: OK")


if __name__ == "__main__":
    main()
