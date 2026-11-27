#!/usr/bin/env python3
"""Build the reproducible BakersfieldQuake overlay package: zz_dn3chaingun.pk3.

Never touches bakersfield.pk3 or quake15/q15.pk3, and writes ZERO loose files
into repo `gfx/` or `sound/`.

Packages the DN3DooM Chaingun Cannon (Regular Gloves / CGGN*) 2D sprites,
HUD icons, and sounds:
  - gfx/dn3cg/cggn_<letter>.png  (18 frames A..R, 4x nearest-neighbor for crisp pixel art)
  - gfx/dn3cg/hud_icon.png       (2x CGUPA0 pickup silhouette for modern HUD styles)
  - gfx/inv_nailgun.png          (24x16 classic sbar weapon bar icon)
  - gfx/inv2_nailgun.png         (24x16 classic sbar selected weapon bar icon)
  - sound/dn3cg/fire.wav         (CHAINGUN.wav)
  - sound/dn3cg/select.wav       (WPNSEL21.wav)
  - sound/dn3cg/dryfire.wav      (DRYFIRE.wav)

Usage:
  python -I source/mm_tools/dn3_chaingun/build_dn3chaingun_pk3.py [--out <path>] [--check-repro]
  python -I source/mm_tools/dn3_chaingun/build_dn3chaingun_pk3.py <base_bakersfield.pk3> <out_zz_dn3chaingun.pk3>
"""
from __future__ import annotations

import argparse
import hashlib
import io
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageEnhance

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
ASSETS_DIR = HERE / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
SOUND_DIR = ASSETS_DIR / "sound"
DEFAULT_OUT_PK3 = REPO_ROOT / "zz_dn3chaingun.pk3"

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16

CGGN_LETTERS = tuple("abcdefghijklmnopqr")

SOUND_MAP = {
    "sound/dn3cg/fire.wav": "CHAINGUN.wav",
    "sound/dn3cg/select.wav": "WPNSEL21.wav",
    "sound/dn3cg/dryfire.wav": "DRYFIRE.wav",
}


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, format="PNG", compress_level=9, optimize=False)
    return buf.getvalue()


def _make_inv_icon(src_img: Image.Image, selected: bool) -> bytes:
    """Fit CGUPA0 cleanly into Quake's 24x16 classic weapon-bar slot."""
    canvas = Image.new("RGBA", (24, 16), (0, 0, 0, 0))
    w, h = src_img.size
    target_w = 24
    target_h = max(1, round(h * target_w / w))
    if target_h > 14:
        target_h = 14
        target_w = max(1, round(w * target_h / h))
    resized = src_img.convert("RGBA").resize((target_w, target_h), Image.Resampling.BILINEAR)
    r, g, b, a = resized.split()
    if selected:
        r = r.point(lambda v: min(255, int(v * 1.15 + 35)))
        g = g.point(lambda v: min(255, int(v * 0.95 + 15)))
        b = b.point(lambda v: min(255, int(v * 0.45)))
    else:
        r = r.point(lambda v: min(255, int(v * 0.85)))
        g = g.point(lambda v: min(255, int(v * 0.72)))
        b = b.point(lambda v: min(255, int(v * 0.52)))
    tinted = Image.merge("RGBA", (r, g, b, a))
    if not selected:
        tinted = ImageEnhance.Brightness(tinted).enhance(0.88)
    ox = (24 - target_w) // 2
    oy = (16 - target_h) // 2
    canvas.paste(tinted, (ox, oy), tinted)
    return _png_bytes(canvas)


def _collect_entries() -> dict[str, bytes]:
    entries: dict[str, bytes] = {}

    for lt in CGGN_LETTERS:
        src = SPRITES_DIR / f"CGGN{lt.upper()}0.png"
        if not src.is_file():
            raise FileNotFoundError(f"Missing CGGN sprite: {src}")
        with Image.open(src) as im:
            up = im.convert("RGBA").resize((im.width * 4, im.height * 4), Image.Resampling.NEAREST)
            entries[f"gfx/dn3cg/cggn_{lt}.png"] = _png_bytes(up)

    pickup_src = SPRITES_DIR / "CGUPA0.png"
    if not pickup_src.is_file():
        raise FileNotFoundError(f"Missing pickup sprite: {pickup_src}")
    with Image.open(pickup_src) as im:
        up = im.convert("RGBA").resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST)
        entries["gfx/dn3cg/hud_icon.png"] = _png_bytes(up)
        entries["gfx/inv_nailgun.png"] = _make_inv_icon(im, selected=False)
        entries["gfx/inv2_nailgun.png"] = _make_inv_icon(im, selected=True)

    for pk3_path, fname in SOUND_MAP.items():
        src = SOUND_DIR / fname
        if not src.is_file():
            raise FileNotFoundError(f"Missing sound: {src}")
        entries[pk3_path] = src.read_bytes()

    return entries


def write_pk3(out_path: Path, entries: dict[str, bytes]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".pk3.tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w") as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            info.create_system = 3
            if name.lower().endswith((".png", ".jpg", ".jpeg", ".ogg")):
                info.compress_type = zipfile.ZIP_STORED
                zf.writestr(info, entries[name])
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, entries[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    tmp.replace(out_path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pos", nargs="*", help="Optional <base_bakersfield.pk3> <out_pk3> positional args")
    ap.add_argument("--out", type=Path, default=None, help=f"Output pk3 path (default: {DEFAULT_OUT_PK3})")
    ap.add_argument("--check-repro", action="store_true", help="Build twice and verify identical SHA-256")
    args = ap.parse_args(argv)

    out_pk3 = args.out
    if out_pk3 is None:
        if len(args.pos) >= 2:
            out_pk3 = Path(args.pos[1])
        elif len(args.pos) == 1:
            out_pk3 = Path(args.pos[0])
        else:
            out_pk3 = DEFAULT_OUT_PK3

    entries = _collect_entries()
    write_pk3(out_pk3, entries)
    digest = sha256_file(out_pk3)
    print(f"wrote {out_pk3} ({out_pk3.stat().st_size} bytes, {len(entries)} entries, sha256={digest})")

    if args.check_repro:
        with tempfile.TemporaryDirectory() as td:
            p2 = Path(td) / "repro_check.pk3"
            write_pk3(p2, _collect_entries())
            d2 = sha256_file(p2)
            if d2 != digest:
                print(f"ERROR: reproducibility mismatch: {digest} vs {d2}", file=sys.stderr)
                return 1
            print(f"repro check passed: identical sha256 ({d2})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
