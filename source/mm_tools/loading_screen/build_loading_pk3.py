#!/usr/bin/env python3
"""Build the reproducible BakersfieldQuake overlay package: zz_loading.pk3.

Never touches bakersfield.pk3 or quake15/q15.pk3, and writes ZERO loose files
into repo `gfx/`.

Packages the 6 borderless Bakersfield Quake loading screen backdrops and
animated MenuQC sprite assets:
  - gfx/loading/bg_1.png .. bg_6.png  (1280x720 borderless hero illustrations)
  - gfx/loading/rob_drone.png         (128x128 Rob Drone sprite extracted from bakersfield.pk3)
  - gfx/loading/rocket_r.png          (96x40 right-facing cartoon/Quake rocket)
  - gfx/loading/rocket_l.png          (96x40 left-facing cartoon/Quake rocket)
  - gfx/loading/flame.png             (256x64 4-frame animated exhaust flame sheet)
  - gfx/loading/boom.png              (512x128 4-frame animated comic explosion sheet)

Usage:
  python -I source/mm_tools/loading_screen/build_loading_pk3.py [--out <path>] [--check-repro]
  python -I source/mm_tools/loading_screen/build_loading_pk3.py <base_bakersfield.pk3> <out_zz_loading.pk3>
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

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
ASSETS_DIR = HERE / "assets"
DEFAULT_BASE_PK3 = REPO_ROOT / "bakersfield.pk3"
DEFAULT_OUT_PK3 = REPO_ROOT / "zz_loading.pk3"

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", compress_level=9, optimize=False)
    return buf.getvalue()


def _extract_rob_drone(base_pk3: Path) -> Image.Image:
    """Extract frame 0 of progs/robhead_proj.spr32 centered in a 128x128 RGBA canvas."""
    with zipfile.ZipFile(base_pk3, "r") as zf:
        raw = zf.read("progs/robhead_proj.spr32")
    ident, ver, _st, _rad, _mw, _mh, nframes, _b, _sy = struct.unpack_from("<4siiifiiii", raw, 0)
    if ident != b"IDSP" or ver != 32 or nframes < 1:
        raise ValueError(f"Unexpected spr32 header for robhead_proj: {ident!r} v{ver}")
    pos = 36
    ft = struct.unpack_from("<i", raw, pos)[0]
    pos += 4
    if ft != 0:
        raise ValueError(f"Unexpected frame group {ft} in robhead_proj.spr32")
    _ox, _oy, w, h = struct.unpack_from("<4i", raw, pos)
    pos += 16
    src = Image.frombytes("RGBA", (w, h), raw[pos : pos + w * h * 4])
    bbox = src.getbbox()
    if bbox:
        src = src.crop(bbox)
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    pad = 8
    avail = 128 - pad * 2
    scale = min(avail / src.width, avail / src.height)
    nw = max(1, round(src.width * scale))
    nh = max(1, round(src.height * scale))
    rs = src.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas.paste(rs, ((128 - nw) // 2, (128 - nh) // 2), rs)
    return canvas


def _make_rocket_right() -> Image.Image:
    """Render a crisp 96x40 retro comic/Quake rocket facing right (at 2x SSAA)."""
    s = 2
    w, h = 96 * s, 40 * s
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = h // 2

    ink = (22, 18, 22, 255)
    red = (224, 42, 34, 255)
    red_hi = (255, 118, 92, 255)
    silver = (204, 214, 226, 255)
    silver_hi = (242, 248, 255, 255)
    silver_dk = (118, 130, 148, 255)
    nozzle = (64, 68, 78, 255)

    # Top and bottom fins
    top_fin = [(18 * s, cy - 8 * s), (6 * s, cy - 17 * s), (26 * s, cy - 17 * s), (36 * s, cy - 8 * s)]
    bot_fin = [(18 * s, cy + 8 * s), (6 * s, cy + 17 * s), (26 * s, cy + 17 * s), (36 * s, cy + 8 * s)]
    d.polygon(top_fin, fill=red, outline=ink, width=2 * s)
    d.polygon(bot_fin, fill=red, outline=ink, width=2 * s)

    # Rear nozzle collar
    d.rounded_rectangle([8 * s, cy - 7 * s, 20 * s, cy + 7 * s], radius=2 * s, fill=nozzle, outline=ink, width=2 * s)

    # Main cylindrical silver fuselage
    d.rounded_rectangle([16 * s, cy - 9 * s, 68 * s, cy + 9 * s], radius=3 * s, fill=silver, outline=ink, width=2 * s)
    # Shading & specular highlight along fuselage
    d.rectangle([18 * s, cy + 2 * s, 66 * s, cy + 7 * s], fill=silver_dk)
    d.rectangle([18 * s, cy - 7 * s, 66 * s, cy - 3 * s], fill=silver_hi)
    # Red hazard band
    d.rectangle([30 * s, cy - 8 * s, 38 * s, cy + 8 * s], fill=red)
    # Center stabilizer fin
    d.rectangle([14 * s, cy - 2 * s, 38 * s, cy + 2 * s], fill=red_hi, outline=ink, width=s)

    # Pointed red nose cone
    cone = [(66 * s, cy - 9 * s), (92 * s, cy), (66 * s, cy + 9 * s)]
    d.polygon(cone, fill=red, outline=ink, width=2 * s)
    cone_hi = [(68 * s, cy - 7 * s), (88 * s, cy - 1 * s), (68 * s, cy - 2 * s)]
    d.polygon(cone_hi, fill=red_hi)

    return im.resize((96, 40), Image.Resampling.LANCZOS)


def _make_flame_sheet() -> Image.Image:
    """Render a 256x64 4-frame animated rocket exhaust flame strip."""
    sheet = Image.new("RGBA", (256, 64), (0, 0, 0, 0))
    for frame in range(4):
        s = 2
        cell = Image.new("RGBA", (64 * s, 64 * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(cell)
        cx, cy = 48 * s, 32 * s
        stretch = [1.0, 1.25, 0.90, 1.15][frame]
        wobble = [0, -3, 2, -1][frame] * s

        # Outer orange-red tongue
        outer = [
            (cx + 8 * s, cy - 12 * s),
            (cx - int(36 * stretch) * s, cy + wobble),
            (cx + 8 * s, cy + 12 * s),
            (cx + 12 * s, cy),
        ]
        d.polygon(outer, fill=(255, 112, 24, 235))
        # Mid bright gold tongue
        mid = [
            (cx + 8 * s, cy - 8 * s),
            (cx - int(25 * stretch) * s, cy + wobble // 2),
            (cx + 8 * s, cy + 8 * s),
            (cx + 10 * s, cy),
        ]
        d.polygon(mid, fill=(255, 206, 48, 245))
        # White-hot core
        core = [
            (cx + 8 * s, cy - 4 * s),
            (cx - int(13 * stretch) * s, cy),
            (cx + 8 * s, cy + 4 * s),
        ]
        d.polygon(core, fill=(255, 252, 224, 255))
        # Trailing smoke puff
        px = cx - int((30 + frame * 4) * s)
        py = cy + wobble
        r = (5 + (frame % 2) * 2) * s
        d.ellipse([px - r, py - r, px + r, py + r], fill=(235, 235, 240, 175))

        cell_sm = cell.resize((64, 64), Image.Resampling.LANCZOS)
        sheet.paste(cell_sm, (frame * 64, 0), cell_sm)
    return sheet


def _make_boom_sheet() -> Image.Image:
    """Render a 512x128 4-frame retro comic starburst explosion strip."""
    sheet = Image.new("RGBA", (512, 128), (0, 0, 0, 0))
    for frame in range(4):
        s = 2
        cell = Image.new("RGBA", (128 * s, 128 * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(cell)
        cx, cy = 64 * s, 64 * s
        scale = [0.55, 0.92, 1.0, 0.72][frame]
        alpha = [255, 255, 235, 150][frame]
        rot = frame * 0.24

        spikes = 14
        pts_outer = []
        pts_mid = []
        pts_inner = []
        for i in range(spikes * 2):
            ang = rot + (math.pi * i) / spikes
            if i % 2 == 0:
                ro = (54 + (i % 4) * 2) * scale * s
                rm = (40 + (i % 4) * 2) * scale * s
                ri = 24 * scale * s
            else:
                ro = 26 * scale * s
                rm = 19 * scale * s
                ri = 12 * scale * s
            pts_outer.append((cx + math.cos(ang) * ro, cy + math.sin(ang) * ro))
            pts_mid.append((cx + math.cos(ang) * rm, cy + math.sin(ang) * rm))
            pts_inner.append((cx + math.cos(ang) * ri, cy + math.sin(ang) * ri))

        d.polygon(pts_outer, fill=(242, 78, 22, alpha), outline=(24, 14, 12, alpha), width=2 * s)
        d.polygon(pts_mid, fill=(255, 186, 36, alpha))
        d.polygon(pts_inner, fill=(255, 248, 200, alpha))

        cell_sm = cell.resize((128, 128), Image.Resampling.LANCZOS)
        sheet.paste(cell_sm, (frame * 128, 0), cell_sm)
    return sheet


def _collect_entries(base_pk3: Path) -> dict[str, bytes]:
    if not base_pk3.is_file():
        raise FileNotFoundError(f"Missing base bakersfield.pk3: {base_pk3}")

    entries: dict[str, bytes] = {}
    for idx in range(1, 7):
        bg_path = ASSETS_DIR / f"loading_bg_{idx}.png"
        if not bg_path.is_file():
            raise FileNotFoundError(f"Missing loading backdrop: {bg_path}")
        with Image.open(bg_path) as im:
            entries[f"gfx/loading/bg_{idx}.png"] = _png_bytes(im.convert("RGB"))

    menu_bg = ASSETS_DIR / "main_menu_bg.png"
    if not menu_bg.is_file():
        raise FileNotFoundError(f"Missing main menu backdrop: {menu_bg}")
    with Image.open(menu_bg) as im:
        entries["gfx/loading/main_menu_bg.png"] = _png_bytes(im.convert("RGB"))

    entries["gfx/loading/rob_drone.png"] = _png_bytes(_extract_rob_drone(base_pk3))

    rocket_r = _make_rocket_right()
    rocket_l = rocket_r.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    entries["gfx/loading/rocket_r.png"] = _png_bytes(rocket_r)
    entries["gfx/loading/rocket_l.png"] = _png_bytes(rocket_l)
    entries["gfx/loading/flame.png"] = _png_bytes(_make_flame_sheet())
    entries["gfx/loading/boom.png"] = _png_bytes(_make_boom_sheet())
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
    ap.add_argument("--base-pk3", type=Path, default=None, help=f"Base bakersfield.pk3 path (default: {DEFAULT_BASE_PK3})")
    ap.add_argument("--check-repro", action="store_true", help="Build twice and verify identical SHA-256")
    args = ap.parse_args(argv)

    base_pk3 = args.base_pk3
    out_pk3 = args.out
    if len(args.pos) >= 2:
        base_pk3 = base_pk3 or Path(args.pos[0])
        out_pk3 = out_pk3 or Path(args.pos[1])
    elif len(args.pos) == 1:
        out_pk3 = out_pk3 or Path(args.pos[0])

    base_pk3 = base_pk3 or DEFAULT_BASE_PK3
    out_pk3 = out_pk3 or DEFAULT_OUT_PK3

    entries = _collect_entries(base_pk3)
    write_pk3(out_pk3, entries)
    digest = sha256_file(out_pk3)
    print(f"wrote {out_pk3} ({out_pk3.stat().st_size} bytes, {len(entries)} entries, sha256={digest})")

    if args.check_repro:
        with tempfile.TemporaryDirectory() as td:
            p2 = Path(td) / "repro_check.pk3"
            write_pk3(p2, _collect_entries(base_pk3))
            d2 = sha256_file(p2)
            if d2 != digest:
                print(f"ERROR: reproducibility mismatch: {digest} vs {d2}", file=sys.stderr)
                return 1
            print(f"repro check passed: identical sha256 ({d2})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
