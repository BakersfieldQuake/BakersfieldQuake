"""Builds zz_console.pk3: crisp outlined classic Quake font (gfx/conchars.png) and bundled Roboto-Medium.ttf.

    python -I source/mm_tools/console/build_console_pk3.py [output_pk3] [--verify-repro]

Packs:
  - gfx/conchars.png: 512x512 Scale2x high-contrast black-outlined classic Quake font
  - engine/fonts/Roboto-Medium.ttf: bundled menu/UI font for cross-platform parity

Reproducible: fixed 1980-01-01 zip timestamps, sorted entry order, fixed permissions, ZIP_STORED.
"""
import argparse
import hashlib
import zipfile
from pathlib import Path

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16

HERE = Path(__file__).resolve().parent
DEFAULT_CONCHARS = HERE / "assets" / "conchars.png"
DEFAULT_FONT = HERE / "assets" / "Roboto-Medium.ttf"


def build_pk3(out_path: Path, conchars_path: Path = DEFAULT_CONCHARS, font_path: Path = DEFAULT_FONT) -> bytes:
    if not conchars_path.is_file():
        raise FileNotFoundError(f"missing conchars asset: {conchars_path}")
    if not font_path.is_file():
        raise FileNotFoundError(f"missing font asset: {font_path}")

    entries = {
        "engine/fonts/Roboto-Medium.ttf": font_path.read_bytes(),
        "gfx/conchars.png": conchars_path.read_bytes(),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".pk3.tmp")
    with zipfile.ZipFile(tmp, "w") as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, entries[name])
    tmp.replace(out_path)
    return out_path.read_bytes()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out_pk3", type=Path, nargs="?", default=Path("zz_console.pk3"), help="Output zz_console.pk3 path")
    ap.add_argument("--conchars", type=Path, default=DEFAULT_CONCHARS, help="Path to conchars.png")
    ap.add_argument("--font", type=Path, default=DEFAULT_FONT, help="Path to Roboto-Medium.ttf")
    ap.add_argument("--verify-repro", action="store_true", help="Build twice and assert identical SHA-256")
    args = ap.parse_args()

    b1 = build_pk3(args.out_pk3, args.conchars, args.font)
    h1 = hashlib.sha256(b1).hexdigest()
    if args.verify_repro:
        b2 = build_pk3(args.out_pk3, args.conchars, args.font)
        h2 = hashlib.sha256(b2).hexdigest()
        if h1 != h2:
            raise SystemExit(f"Reproducibility check failed: {h1} != {h2}")
    print(f"wrote {args.out_pk3} ({len(b1)} bytes, sha256={h1})")


if __name__ == "__main__":
    main()
