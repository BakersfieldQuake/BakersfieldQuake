#!/usr/bin/env python3
"""Build zz_robdrone.pk3: the Raspberry Pi 4B board picture for the Rob Drone HUD (gfx/rh_rpi.png).

The HUD used to draw the board from ~50 drawfill rectangles every frame, with little detail (playtest 1.76).
This draws a detailed board once, at 4x and scaled down: SoC under a heat spreader, RAM, wireless shield, 2x20 GPIO
header, PoE pins, stacked USB 2/3 and Ethernet, USB-C, two micro-HDMI, audio jack, CSI/DSI connectors, SMD parts,
copper traces, silkscreen and mounting holes. The HUD (csqc/robhead_xray.qc, RH_DrawRaspberryPi) draws the live
PWR/ACT LEDs over the two pads at (24,150) and (24,168).

Reproducible: no clock, seeded RNG, fixed zip dates/attributes, pinned Pillow/numpy in CI.

Usage:
  python -I build_robdrone_pk3.py <out zz_robdrone.pk3> [--png <preview.png>] [--verify-repro]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
W, H = 320, 212          # must match RH_RPI_W / RH_RPI_H in robhead_xray.qc
SS = 4                   # supersampling
MM = W / 85.0            # board is 85 x 56 mm

PCB = (18, 112, 52)
PCB_DARK = (12, 82, 38)
TRACE = (52, 150, 78)
SILK = (236, 240, 232)
GOLD = (222, 184, 86)
METAL = (196, 202, 210)
METAL_DARK = (128, 134, 142)
BLACK = (22, 22, 26)
CHIP = (34, 34, 40)


def mm(v: float) -> int:
    return int(round(v * MM * SS))


def box(d: ImageDraw.ImageDraw, x0, y0, x1, y1, fill, outline=None, r=0.0, width=1):
    d.rounded_rectangle((mm(x0), mm(y0), mm(x1), mm(y1)), radius=mm(r), fill=fill, outline=outline,
                        width=max(1, width * SS // 2) if outline else 0)


def font(size_mm: float) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=max(6, mm(size_mm)))


def text(d: ImageDraw.ImageDraw, x, y, s, size_mm, fill=SILK, anchor="la"):
    d.text((mm(x), mm(y)), s, font=font(size_mm), fill=fill, anchor=anchor)


def render() -> Image.Image:
    rng = np.random.default_rng(20261125)
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # board + edge
    box(d, 0, 0, 85, 56, PCB, outline=PCB_DARK, r=3, width=2)

    # copper traces: bundles of thin lines between the parts (seeded, so the same every build)
    for _ in range(46):
        x = float(rng.uniform(8, 64))
        y = float(rng.uniform(9, 50))
        pts = [(x, y)]
        for _ in range(int(rng.integers(2, 5))):
            if rng.random() < 0.5:
                x = float(np.clip(x + rng.uniform(-14, 14), 4, 66))
            else:
                y = float(np.clip(y + rng.uniform(-10, 10), 8, 52))
            pts.append((x, y))
        d.line([(mm(px), mm(py)) for px, py in pts], fill=TRACE, width=max(1, SS // 2), joint="curve")
        d.ellipse((mm(pts[-1][0]) - SS, mm(pts[-1][1]) - SS, mm(pts[-1][0]) + SS, mm(pts[-1][1]) + SS), fill=GOLD)

    # mounting holes
    for hx, hy in ((3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)):
        d.ellipse((mm(hx - 3), mm(hy - 3), mm(hx + 3), mm(hy + 3)), fill=GOLD)
        d.ellipse((mm(hx - 1.4), mm(hy - 1.4), mm(hx + 1.4), mm(hy + 1.4)), fill=(10, 10, 12))

    # 2x20 GPIO header
    box(d, 7.0, 0.9, 58.0, 6.1, BLACK, r=0.4)
    for i in range(20):
        for row in (0, 1):
            cx = 8.27 + i * 2.54
            cy = 2.2 + row * 2.54
            d.rectangle((mm(cx - 0.55), mm(cy - 0.55), mm(cx + 0.55), mm(cy + 0.55)), fill=GOLD)
    text(d, 7.2, 6.6, "GPIO", 1.6)
    # PoE header
    box(d, 59.5, 6.8, 64.6, 11.9, BLACK, r=0.3)
    for i in range(2):
        for row in range(2):
            cx, cy = 60.8 + i * 2.54, 8.1 + row * 2.54
            d.rectangle((mm(cx - 0.5), mm(cy - 0.5), mm(cx + 0.5), mm(cy + 0.5)), fill=GOLD)

    # wireless module shield + antenna
    box(d, 6.0, 9.0, 19.5, 19.5, METAL, outline=METAL_DARK, r=0.6)
    for i in range(5):
        d.line((mm(7.0), mm(10.5 + i * 1.9), mm(18.5), mm(10.5 + i * 1.9)), fill=(176, 182, 190), width=SS // 2)
    text(d, 12.75, 14.2, "WiFi BT5", 1.5, fill=(70, 74, 80), anchor="mm")
    for i in range(5):
        d.line((mm(2.0 + i * 0.6), mm(10 + i * 1.6), mm(5.2), mm(10 + i * 1.6)), fill=GOLD, width=SS // 2)

    # SoC with heat spreader
    box(d, 21.0, 17.0, 36.0, 32.0, (150, 156, 164), r=1.0)
    box(d, 21.8, 17.8, 35.2, 31.2, METAL, outline=(230, 234, 238), r=0.8)
    text(d, 28.5, 22.0, "BROADCOM", 1.6, fill=(60, 64, 70), anchor="mm")
    text(d, 28.5, 25.0, "BCM2711", 2.2, fill=(40, 44, 50), anchor="mm")
    text(d, 28.5, 28.2, "ARM 1.5GHz", 1.3, fill=(80, 84, 90), anchor="mm")
    # RAM
    box(d, 39.0, 19.5, 50.5, 31.0, CHIP, outline=(60, 60, 70), r=0.4)
    text(d, 44.75, 23.5, "LPDDR4", 1.6, fill=(200, 200, 205), anchor="mm")
    text(d, 44.75, 26.8, "4GB", 1.8, fill=(200, 200, 205), anchor="mm")
    # USB / Ethernet controllers
    box(d, 54.0, 21.0, 61.0, 28.0, CHIP, r=0.3)
    text(d, 57.5, 24.5, "VL805", 1.2, fill=(190, 190, 196), anchor="mm")
    box(d, 47.0, 37.0, 53.0, 43.0, CHIP, r=0.3)
    text(d, 50.0, 40.0, "PHY", 1.2, fill=(190, 190, 196), anchor="mm")
    # PMIC
    box(d, 9.0, 36.0, 15.0, 42.0, CHIP, r=0.3)

    # SMD capacitors / resistors scattered in the gaps (avoid the big parts)
    taken = [(6, 9, 19.5, 19.5), (21, 17, 36, 32), (39, 19.5, 50.5, 31), (54, 21, 61, 28), (47, 37, 53, 43),
             (9, 36, 15, 42), (66, 2, 85, 56), (0, 47, 66, 56), (7, 0.9, 58, 6.1), (59.5, 6.8, 64.6, 11.9),
             (21, 33, 46, 39.5), (6, 38, 13, 47)]
    placed = 0
    while placed < 70:
        x = float(rng.uniform(4, 64))
        y = float(rng.uniform(8, 46))
        if any(a - 0.6 <= x <= c + 0.6 and b - 0.6 <= y <= e + 0.6 for a, b, c, e in taken):
            continue
        horiz = rng.random() < 0.5
        lw, lh = (1.4, 0.7) if horiz else (0.7, 1.4)
        body = (150, 110, 60) if rng.random() < 0.55 else (28, 28, 30)
        d.rectangle((mm(x), mm(y), mm(x + lw), mm(y + lh)), fill=body)
        if horiz:
            d.rectangle((mm(x), mm(y), mm(x + 0.3), mm(y + lh)), fill=METAL)
            d.rectangle((mm(x + lw - 0.3), mm(y), mm(x + lw), mm(y + lh)), fill=METAL)
        else:
            d.rectangle((mm(x), mm(y), mm(x + lw), mm(y + 0.3)), fill=METAL)
            d.rectangle((mm(x), mm(y + lh - 0.3), mm(x + lw), mm(y + lh)), fill=METAL)
        placed += 1

    # right edge: USB 2.0, USB 3.0 (blue tongues), Ethernet
    for y0, tongue in ((2.0, BLACK), (20.5, (30, 90, 200))):
        box(d, 67.5, y0, 85.0, y0 + 15.0, METAL, outline=METAL_DARK, r=0.5)
        for k in range(2):
            ty = y0 + 2.2 + k * 6.4
            box(d, 69.0, ty, 84.2, ty + 4.6, (40, 42, 46), r=0.3)
            box(d, 69.5, ty + 1.5, 83.5, ty + 3.1, tongue)
    box(d, 65.5, 39.0, 85.0, 55.0, METAL, outline=METAL_DARK, r=0.5)
    box(d, 67.5, 41.5, 84.2, 52.5, (30, 32, 36), r=0.4)
    d.rectangle((mm(73.0), mm(50.0), mm(79.0), mm(52.5)), fill=(30, 32, 36))
    d.rectangle((mm(68.2), mm(41.8), mm(70.6), mm(43.4)), fill=(255, 170, 40))
    d.rectangle((mm(81.0), mm(41.8), mm(83.4), mm(43.4)), fill=(80, 220, 90))

    # bottom edge: USB-C, 2x micro-HDMI, CSI, audio jack
    box(d, 3.4, 49.0, 12.4, 56.0, METAL, outline=METAL_DARK, r=1.2)
    box(d, 5.0, 51.6, 10.8, 53.8, (40, 42, 46), r=0.8)
    for hx in (22.0, 35.5):
        box(d, hx, 49.5, hx + 7.0, 56.0, METAL, outline=METAL_DARK, r=0.6)
        box(d, hx + 1.0, 51.5, hx + 6.0, 54.0, (40, 42, 46), r=0.4)
    box(d, 44.0, 41.0, 46.8, 54.5, (230, 226, 210), outline=(150, 146, 130), r=0.2)   # CSI camera
    d.rectangle((mm(44.4), mm(41.4), mm(46.4), mm(54.1)), fill=(40, 36, 30))
    box(d, 50.0, 47.0, 57.0, 56.0, BLACK, r=0.8)                                       # audio
    d.ellipse((mm(51.6), mm(50.6), mm(55.4), mm(54.4)), fill=(60, 60, 66))
    d.ellipse((mm(52.6), mm(51.6), mm(54.4), mm(53.4)), fill=(10, 10, 12))
    box(d, 1.0, 16.5, 3.8, 34.0, (230, 226, 210), outline=(150, 146, 130), r=0.2)     # DSI display
    d.rectangle((mm(1.4), mm(16.9), mm(3.4), mm(33.6)), fill=(40, 36, 30))

    # LED pads (lit by the HUD): image pixels (24,150) and (24,168), 8x8 -> mm
    for py in (150, 168):
        x0, y0 = 24 * SS, py * SS
        d.rectangle((x0 - SS, y0 - SS, x0 + 9 * SS, y0 + 9 * SS), fill=(230, 230, 220))
        d.rectangle((x0, y0, x0 + 8 * SS - 1, y0 + 8 * SS - 1), fill=(60, 30, 30) if py == 150 else (30, 60, 34))
    text(d, 9.5, 39.95, "PWR", 1.4)
    text(d, 9.5, 44.7, "ACT", 1.4)

    # silkscreen
    text(d, 22.0, 34.0, "Raspberry Pi 4 Model B", 2.0)
    text(d, 22.0, 37.0, "(c) Raspberry Pi 2018  ROB-DRONE", 1.3)
    text(d, 22.0, 11.0, "J8", 1.5)
    # raspberry logo: leaves + berry
    lx, ly = 16.5, 26.0
    d.polygon([(mm(lx - 1.6), mm(ly - 2.8)), (mm(lx), mm(ly - 1.4)), (mm(lx - 0.4), mm(ly - 3.6))], fill=(70, 200, 90))
    d.polygon([(mm(lx + 1.6), mm(ly - 2.8)), (mm(lx), mm(ly - 1.4)), (mm(lx + 0.4), mm(ly - 3.6))], fill=(70, 200, 90))
    for bx, by in ((-0.9, -0.6), (0.9, -0.6), (0, 0.4), (-0.9, 1.2), (0.9, 1.2), (0, 2.1)):
        d.ellipse((mm(lx + bx - 0.75), mm(ly + by - 0.75), mm(lx + bx + 0.75), mm(ly + by + 0.75)),
                  fill=(200, 30, 70), outline=(240, 90, 120), width=max(1, SS // 3))

    return im.resize((W, H), Image.Resampling.LANCZOS)


def png_bytes() -> bytes:
    out = io.BytesIO()
    render().save(out, format="PNG", optimize=True)
    return out.getvalue()


def build(out: Path, png_preview: Path | None) -> str:
    data = png_bytes()
    if png_preview:
        png_preview.parent.mkdir(parents=True, exist_ok=True)
        png_preview.write_bytes(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        info = zipfile.ZipInfo("gfx/rh_rpi.png", date_time=FIXED_DATE)
        info.external_attr = FILE_ATTR
        info.compress_type = zipfile.ZIP_STORED
        z.writestr(info, data)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{out}: gfx/rh_rpi.png {W}x{H} ({len(data)} bytes) sha256 {digest}")
    return digest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--png", type=Path, help="also write the picture here for a look")
    ap.add_argument("--verify-repro", action="store_true")
    a = ap.parse_args()
    first = build(a.out, a.png)
    if a.verify_repro:
        tmp = a.out.with_suffix(".repro.pk3")
        second = build(tmp, None)
        tmp.unlink()
        if first != second:
            sys.exit("NOT REPRODUCIBLE: two builds differ")
        print("reproducible: OK")


if __name__ == "__main__":
    main()
