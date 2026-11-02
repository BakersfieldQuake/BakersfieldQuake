"""Procedural 3D MD3 models + 256x256 UV textures + .skin files for BakersfieldQuake LAN party rooms:
  - 4 unique CRT Monitors:  progs/bklan/lan_mon1..4.md3   (+ skins 0..6 for Q3A, CS 1.5, Win98, Dead CRT)
  - 4 unique PC Towers:     progs/bklan/lan_pc1..4.md3    (Beige ATX, Modded UV Chieftec w/ handle+neon, Bondi 2-tone, Silver Alu)
  - 4 unique LAN Chairs:    progs/bklan/lan_chair1..4.md3 (Burgundy Banquet, Black Exec Swivel, Padded Folding, Cobalt Task)
  - 4 unique LAN Tables:    progs/bklan/lan_table1..4.md3 (+ lan_table4s.md3 compact desk)
  - 6 custom Debris chunks: progs/bklan/lan_deb_{glass,yoke,panel,fan,wheel,plank}.md3

Coordinate convention (matches DarkPlaces + make_bklan.py):
  - Origin (0, 0, 0) at bottom center (z = 0 rests flush on floor or z = 30u tabletop).
  - Monitors, PC towers, and chairs face +X at angles = '0 0 0' (sitter looks +X, monitor screen faces +X, PC front bezel faces +X).
  - Tables have long axis (96u = 8 ft) along X and depth (30u = 2.5 ft) along Y at angles = '0 0 0'.
"""
import math
import os
import random

import md3lib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

DIFFUSE_GAIN = float(os.environ.get("LAN_DIFFUSE_GAIN", "0.48"))
GLOW_GAIN = float(os.environ.get("LAN_GLOW_GAIN", "0.56"))


def _font(size, bold=True):
    for n in (("arialbd.ttf", "tahomabd.ttf", "consolab.ttf") if bold else ("tahoma.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", n), size)
        except OSError:
            pass
    return ImageFont.load_default()


def _norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


def _cross(u, w):
    return (
        u[1] * w[2] - u[2] * w[1],
        u[2] * w[0] - u[0] * w[2],
        u[0] * w[1] - u[1] * w[0],
    )


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vnormals(verts, tris):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        n = _cross(_sub(p1, p0), _sub(p2, p0))
        for i in (a, b, c):
            acc[i][0] += n[0]
            acc[i][1] += n[1]
            acc[i][2] += n[2]
    return [_norm(a) for a in acc]


def _save_tex(im: Image.Image, path: str, gain: float = DIFFUSE_GAIN):
    arr = np.asarray(im.convert("RGB"), dtype=np.float32) * gain
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(path)


def _uv_rect(px0, py0, px1, py1, size=256, pad=2.0):
    """Return (u0, v0, u1, v1) inset by pad pixels inside a size x size texture."""
    return (
        (px0 + pad) / size,
        (py0 + pad) / size,
        (px1 - pad) / size,
        (py1 - pad) / size,
    )


class SurfBuilder:
    """Collects triangles + UVs with guaranteed outward CCW winding."""

    def __init__(self, name: str, shader: str):
        self.name = name
        self.shader = shader
        self.verts = []
        self.st = []
        self.tris = []

    def quad(self, p0, p1, p2, p3, uv_box=(0.0, 0.0, 1.0, 1.0), outward=None, flip_uv_y=False):
        """Add quad (p0=BL, p1=BR, p2=TR, p3=TL when viewed from outside).
        Verifies/fixes winding against `outward` vector if given!"""
        u0, v0, u1, v1 = uv_box
        if flip_uv_y:
            v0, v1 = v1, v0
        q_pts = [p0, p1, p2, p3]
        q_st = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        n = _cross(_sub(p1, p0), _sub(p2, p0))
        b = len(self.verts)
        self.verts.extend(q_pts)
        self.st.extend(q_st)
        if outward is not None and _dot(n, outward) < 0:
            self.tris.extend([(b, b + 2, b + 1), (b, b + 3, b + 2)])
        else:
            self.tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])

    def tri(self, p0, p1, p2, st0, st1, st2, outward=None):
        n = _cross(_sub(p1, p0), _sub(p2, p0))
        b = len(self.verts)
        self.verts.extend([p0, p1, p2])
        self.st.extend([st0, st1, st2])
        if outward is not None and _dot(n, outward) < 0:
            self.tris.append((b, b + 2, b + 1))
        else:
            self.tris.append((b, b + 1, b + 2))

    def box(self, x0, y0, z0, x1, y1, z1, uvs: dict, skip=()):
        """Axis-aligned box with per-face UV rects: keys 'px','nx','py','ny','pz','nz' (fallback 'all')."""
        def guv(k):
            return uvs[k] if k in uvs else uvs["all"]

        if "px" not in skip:
            # Viewer at +X looking -X: left is -Y, right is +Y, bottom is z0, top is z1
            self.quad((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), guv("px"), outward=(1, 0, 0))
        if "nx" not in skip:
            # Viewer at -X looking +X: left is +Y, right is -Y
            self.quad((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), guv("nx"), outward=(-1, 0, 0))
        if "py" not in skip:
            # Viewer at +Y looking -Y: left is +X, right is -X
            self.quad((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), guv("py"), outward=(0, 1, 0))
        if "ny" not in skip:
            # Viewer at -Y looking +Y: left is -X, right is +X
            self.quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), guv("ny"), outward=(0, -1, 0))
        if "pz" not in skip:
            # Viewer above +Z looking -Z: +X forward/up, -Y left..+Y right
            self.quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), guv("pz"), outward=(0, 0, 1))
        if "nz" not in skip:
            self.quad((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0), guv("nz"), outward=(0, 0, -1))

    def frustum_x(self, x0, y0a, z0a, y1a, z1a, x1, y0b, z0b, y1b, z1b, uvs: dict, cap0=True, cap1=True):
        """Lofted rectangular section from x=x0 (back) to x=x1 (front)."""
        def guv(k):
            return uvs[k] if k in uvs else uvs["all"]

        # Top (+Z)
        self.quad((x0, y0a, z1a), (x1, y0b, z1b), (x1, y1b, z1b), (x0, y1a, z1a), guv("pz"), outward=(0, 0, 1))
        # Bottom (-Z)
        self.quad((x0, y1a, z0a), (x1, y1b, z0b), (x1, y0b, z0b), (x0, y0a, z0a), guv("nz"), outward=(0, 0, -1))
        # Right (+Y)
        self.quad((x1, y1b, z0b), (x0, y1a, z0a), (x0, y1a, z1a), (x1, y1b, z1b), guv("py"), outward=(0, 1, 0))
        # Left (-Y)
        self.quad((x0, y0a, z0a), (x1, y0b, z0b), (x1, y0b, z1b), (x0, y0a, z1a), guv("ny"), outward=(0, -1, 0))
        if cap0:
            self.quad((x0, y1a, z0a), (x0, y0a, z0a), (x0, y0a, z1a), (x0, y1a, z1a), guv("nx"), outward=(-1, 0, 0))
        if cap1:
            self.quad((x1, y0b, z0b), (x1, y1b, z0b), (x1, y1b, z1b), (x1, y0b, z1b), guv("px"), outward=(1, 0, 0))

    def cyl_z(self, cx, cy, z0, z1, r0, r1, uv_box, segs=12, cap_top=True, cap_bot=False):
        u0, v0, u1, v1 = uv_box
        um, vm = (u0 + u1) * 0.5, (v0 + v1) * 0.5
        for i in range(segs):
            a0 = 2.0 * math.pi * i / segs
            a1 = 2.0 * math.pi * (i + 1) / segs
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            p00 = (cx + r0 * c0, cy + r0 * s0, z0)
            p10 = (cx + r0 * c1, cy + r0 * s1, z0)
            p11 = (cx + r1 * c1, cy + r1 * s1, z1)
            p01 = (cx + r1 * c0, cy + r1 * s0, z1)
            su0 = u0 + (u1 - u0) * (i / segs)
            su1 = u0 + (u1 - u0) * ((i + 1) / segs)
            self.quad(p00, p10, p11, p01, (su0, v0, su1, v1), outward=(c0 + c1, s0 + s1, 0))
            if cap_top and r1 > 0.01:
                self.tri((cx, cy, z1), p01, p11, (um, vm), (u0, v0), (u1, v0), outward=(0, 0, 1))
            if cap_bot and r0 > 0.01:
                self.tri((cx, cy, z0), p10, p00, (um, vm), (u1, v1), (u0, v1), outward=(0, 0, -1))

    def strut(self, p_a, p_b, rad, uv_box, segs=6):
        """3D tubular steel strut between any two 3D points p_a -> p_b."""
        axis = _sub(p_b, p_a)
        ln = math.sqrt(_dot(axis, axis))
        if ln < 1e-4:
            return
        ax = _norm(axis)
        ref = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
        t1 = _norm(_cross(ax, ref))
        t2 = _norm(_cross(ax, t1))
        for i in range(segs):
            a0 = 2.0 * math.pi * i / segs
            a1 = 2.0 * math.pi * (i + 1) / segs
            d0 = tuple(t1[k] * math.cos(a0) + t2[k] * math.sin(a0) for k in range(3))
            d1 = tuple(t1[k] * math.cos(a1) + t2[k] * math.sin(a1) for k in range(3))
            q0 = tuple(p_a[k] + rad * d0[k] for k in range(3))
            q1 = tuple(p_a[k] + rad * d1[k] for k in range(3))
            q2 = tuple(p_b[k] + rad * d1[k] for k in range(3))
            q3 = tuple(p_b[k] + rad * d0[k] for k in range(3))
            mid_n = tuple(d0[k] + d1[k] for k in range(3))
            self.quad(q0, q1, q2, q3, uv_box, outward=mid_n)

    def to_surface(self):
        return dict(
            name=self.name,
            shader=self.shader,
            tris=self.tris,
            st=self.st,
            frames=[(self.verts, _vnormals(self.verts, self.tris))],
        )


def _write_md3(path: str, name: str, builders):
    surfs = [b.to_surface() for b in builders if b.tris]
    md3lib.write(path, dict(name=name, surfaces=surfs, nframes=1))


# ==============================================================================
# 1. FOUR UNIQUE 3D CRT MONITORS (lan_mon1..4.md3)
# ==============================================================================
SCREEN_SHADERS = [
    "progs/bklan/scr_q3a1",     # skin 0: Quake 3 Arena (q3dm17)
    "progs/bklan/scr_cs1",      # skin 1: Counter-Strike 1.5 (de_dust2 M4A1)
    "progs/bklan/scr_win98a",   # skin 2: Windows 98 Desktop + Explorer + Winamp + NET SEND
    "progs/bklan/scr_q3a2",     # skin 3: Quake 3 Arena (q3dm6 Railgun)
    "progs/bklan/scr_cs2",      # skin 4: Counter-Strike 1.5 (de_dust AK/AWP Scope)
    "progs/bklan/scr_win98b",   # skin 5: Windows 98 GameSpy LAN + BSOD
    "progs/bklan/scr_dead",     # skin 6: Shattered / imploded CRT
]


def _make_monitor_atlas(kind: int) -> Image.Image:
    """256x256 texture atlas per CRT monitor:
      [0,0..128,128]   = Front bezel face (with sculpted opening frame, brand logo, OSD buttons, LED, stickers)
      [128,0..256,128] = Side / top housing with cooling vent slots (+ BAWLS/Q3 stickers on gamer black CRT!)
      [0,128..128,256] = Rear cathode shell with vent louvers, FCC/serial plate, VGA/power ports
      [128,128..256,256] = Pedestal base / dark inner bezel / cord trim
    """
    palettes = {
        1: ((214, 206, 188), (186, 178, 160), (150, 142, 126), "PROVIEW", True),    # 17" Beige ViewSonic/ProView
        2: ((196, 202, 210), (76, 80, 88), (54, 58, 64), "TRINITRON", False),       # 19" Silver/Charcoal Sony Flat CRT
        3: ((54, 56, 62), (44, 46, 52), (32, 34, 38), "SYNCMASTER", False),         # 17" Matte-Black Gamer CRT
        4: ((206, 190, 152), (182, 166, 130), (146, 132, 102), "MAG 15\"", False),  # 15" Vintage Yellowed Fishbowl CRT
    }
    front_c, side_c, dark_c, brand, has_birds = palettes[kind]
    im = Image.new("RGB", (256, 256), side_c)
    d = ImageDraw.Draw(im)
    rng = random.Random(100 + kind)

    # Subtle plastic grain across entire sheet
    arr = np.asarray(im, dtype=np.int16)
    noise = np.random.default_rng(100 + kind).integers(-5, 6, size=(256, 256, 1))
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)

    # Quadrant TL (0..128, 0..128): Front Bezel
    d.rectangle([0, 0, 127, 127], fill=front_c, outline=dark_c)
    d.rectangle([12, 13, 115, 96], fill=dark_c)  # inner bezel shadow
    d.text((14, 101), brand, font=_font(8, bold=True), fill=(55, 55, 60) if kind != 3 else (195, 200, 210))
    # OSD buttons + glowing power LED along bottom bezel
    if kind == 1:
        # Diamond 4-button cluster + green LED + "14" sharpie & 3-bird ViewSonic/TCO sticker (from 00894.jpg!)
        for bx, by in ((58, 112), (68, 112), (63, 107), (63, 117)):
            d.ellipse([bx - 2, by - 2, bx + 2, by + 2], fill=dark_c)
        d.ellipse([86, 110, 91, 115], fill=(80, 245, 90))
        d.ellipse([93, 109, 100, 116], fill=side_c, outline=dark_c)
        d.text((58, 2), "14", font=_font(9, bold=True), fill=(48, 42, 38))
        d.ellipse([104, 2, 116, 11], fill=(235, 230, 215), outline=(160, 45, 35))
        d.ellipse([107, 4, 110, 8], fill=(220, 50, 40))
        d.ellipse([111, 4, 114, 8], fill=(45, 130, 215))
    elif kind == 2:
        # Sony Trinitron silver top label + 5 silver buttons + cyan/green LED
        d.text((14, 3), "SONY", font=_font(8, bold=True), fill=(45, 48, 55))
        for bi in range(5):
            d.rectangle([48 + bi * 9, 110, 54 + bi * 9, 115], fill=(140, 145, 155), outline=(70, 74, 82))
        d.rectangle([102, 110, 108, 115], fill=(65, 240, 165))
    elif kind == 3:
        # Gamer black bezel: silver metallic OSD strip + amber/green LED
        d.rectangle([36, 106, 92, 118], fill=(155, 162, 172), outline=(30, 32, 36))
        for bi in range(4):
            d.ellipse([42 + bi * 11, 109, 47 + bi * 11, 114], fill=(55, 58, 65))
        d.ellipse([102, 110, 107, 115], fill=(70, 250, 95))
    else:
        # Vintage 15" fishbowl: analog thumbwheels + yellow sticky note on lower-right corner!
        for bi in range(3):
            d.rectangle([44 + bi * 12, 110, 52 + bi * 12, 116], fill=(115, 105, 82), outline=(70, 62, 48))
        d.ellipse([90, 110, 95, 115], fill=(185, 245, 65))
        d.polygon([(98, 96), (122, 98), (120, 122), (96, 120)], fill=(248, 232, 92), outline=(175, 155, 45))
        d.line([(100, 104), (117, 105)], fill=(50, 50, 120), width=1)
        d.line([(100, 110), (115, 111)], fill=(50, 50, 120), width=1)

    # Quadrant TR (128..256, 0..128): Side & Top Housing + cooling louver vents
    d.rectangle([128, 0, 255, 127], fill=side_c)
    for vy in range(18, 72, 6):
        d.line([(146, vy), (236, vy)], fill=dark_c, width=2)
    d.line([(138, 8), (138, 120)], fill=dark_c, width=2)  # mold seam
    if kind == 3:
        # Gamer stickers on side of black CRT: Quake III red badge + blue BAWLS sticker!
        d.rectangle([156, 80, 192, 108], fill=(165, 28, 24), outline=(235, 190, 120))
        d.text((162, 87), "Q3A", font=_font(11, bold=True), fill=(255, 225, 160))
        d.ellipse([202, 82, 238, 106], fill=(28, 88, 205), outline=(220, 235, 255))
        d.text((207, 89), "BAWLS", font=_font(8, bold=True), fill=(255, 255, 255))

    # Quadrant BL (0..128, 128..256): Rear CRT shell with vent slots + FCC label + VGA socket
    d.rectangle([0, 128, 127, 255], fill=side_c)
    for vy in range(140, 186, 6):
        d.line([(18, vy), (108, vy)], fill=dark_c, width=2)
    d.rectangle([28, 194, 98, 226], fill=(215, 215, 210), outline=(90, 90, 90))  # white spec sticker
    for ly in range(199, 222, 5):
        d.line([(33, ly), (92, ly)], fill=(95, 95, 100), width=1)
    d.rectangle([42, 232, 64, 244], fill=(35, 55, 135), outline=(25, 25, 30))    # blue VGA connector
    d.rectangle([70, 232, 88, 244], fill=(28, 28, 32))                           # IEC power socket

    # Quadrant BR (128..256, 128..256):
    #   [128..192, 128..192] = Swivel pedestal
    #   [192..256, 128..192] = Dark inner bezel trim
    #   [128..232, 192..256] = Detailed 104-key Keyboard top (beige mechanical for 1,4; dark/silver gamer for 2,3!)
    #   [232..256, 192..256] = Mouse + cloth LAN mousepad
    d.rectangle([128, 128, 191, 191], fill=tuple(max(18, c - 18) for c in side_c))
    d.rectangle([192, 128, 255, 191], fill=tuple(max(14, c - 36) for c in dark_c))

    kbd_body = (210, 202, 184) if kind in (1, 4) else (46, 48, 56)
    key_cap = (232, 226, 212) if kind in (1, 4) else (78, 82, 92)
    d.rectangle([128, 192, 231, 255], fill=kbd_body, outline=(60, 60, 66))
    # Function row + main alphanumeric keycap blocks + spacebar + numpad
    for ry in range(198, 248, 8):
        for rx in range(133, 206, 6):
            if ry == 246 and 148 <= rx <= 186:
                d.rectangle([148, 245, 190, 251], fill=key_cap)
            else:
                d.rectangle([rx, ry, rx + 4, ry + 5], fill=key_cap)
        for rx in range(211, 227, 5):
            d.rectangle([rx, ry, rx + 3, ry + 5], fill=key_cap)
    # 3 tiny green Num/Caps/Scroll lock LEDs top-right of keyboard!
    for lx_i in range(3):
        d.point((214 + lx_i * 4, 195), fill=(75, 250, 85))

    pad_col = (28, 74, 142) if kind in (1, 4) else (138, 26, 28)
    d.rectangle([232, 192, 255, 255], fill=pad_col, outline=(22, 24, 28))
    ms_col = (214, 208, 192) if kind in (1, 4) else (168, 174, 184)
    d.ellipse([237, 206, 250, 238], fill=ms_col, outline=(45, 48, 54))
    d.line([(243, 207), (243, 218)], fill=(55, 58, 64), width=1)
    if kind in (2, 3):
        # Glowing red IntelliMouse optical tail LED!
        d.rectangle([241, 236, 246, 240], fill=(255, 50, 45))
    return im


def _build_crt_monitor(progs_bklan_dir: str, kind: int):
    """Build lan_mon<kind>.md3 with 2 surfaces: 'body' and 'screen' (+ _0.._6.skin files)."""
    atlas = _make_monitor_atlas(kind)
    tex_rel = f"progs/bklan/t_mon{kind}"
    _save_tex(atlas, os.path.join(progs_bklan_dir, f"t_mon{kind}.png"), DIFFUSE_GAIN)

    uv_front = _uv_rect(0, 0, 128, 128)
    uv_side = _uv_rect(128, 0, 256, 128)
    uv_back = _uv_rect(0, 128, 128, 256)
    uv_base = _uv_rect(128, 128, 192, 192)
    uv_dark = _uv_rect(192, 128, 256, 192)
    uv_kbd = _uv_rect(128, 192, 232, 256)
    uv_mpad = _uv_rect(232, 192, 256, 256)

    body = SurfBuilder("body", tex_rel)
    scr = SurfBuilder("screen", SCREEN_SHADERS[0])

    # Dimensions per monitor variant (units; 12u = 1 ft)
    if kind == 1:      # 17" Beige ProView / ViewSonic
        hw, z_bot, z_top, x_fr, x_bk, bulge = 8.5, 2.8, 16.8, 7.6, -8.8, 0.55
        base_round = True
    elif kind == 2:    # 19" Sony Trinitron Flat-Screen Pro
        hw, z_bot, z_top, x_fr, x_bk, bulge = 9.5, 2.8, 18.4, 7.8, -9.8, 0.16
        base_round = False
    elif kind == 3:    # 17" Matte-Black Gamer SyncMaster
        hw, z_bot, z_top, x_fr, x_bk, bulge = 8.4, 2.7, 16.6, 7.5, -8.6, 0.45
        base_round = True
    else:              # 15" Vintage Boxy Fishbowl CRT
        hw, z_bot, z_top, x_fr, x_bk, bulge = 7.6, 2.9, 15.6, 7.2, -8.4, 0.85
        base_round = False

    # 1. Pedestal base + swivel tilt neck (z = 0 .. z_bot + 0.6)
    if base_round:
        body.cyl_z(-0.5, 0.0, 0.0, 1.1, hw * 0.66, hw * 0.58, uv_base, segs=14, cap_top=True, cap_bot=True)
    else:
        body.frustum_x(-5.4, -hw * 0.66, 0.0, hw * 0.66, 1.1, 4.4, -hw * 0.66, 0.0, hw * 0.66, 1.1, {"all": uv_base})
    body.cyl_z(-0.6, 0.0, 0.9, z_bot + 0.8, 2.9, 2.4, uv_dark, segs=10, cap_top=False, cap_bot=False)

    # 2. Main front bezel housing (x_mid .. x_fr) with 4-frame border around recessed screen opening!
    x_mid = 2.0
    body.frustum_x(
        x_mid, -hw * 0.96, z_bot + 0.2, hw * 0.96, z_top - 0.2,
        x_fr, -hw, z_bot, hw, z_top,
        {"pz": uv_side, "nz": uv_base, "py": uv_side, "ny": uv_side},
        cap0=False, cap1=False,
    )
    # Screen opening margins inside front face (x = x_fr)
    pad_y = hw * 0.16
    pad_top = 1.45
    pad_bot = 2.45 if kind != 4 else 2.75
    sy0, sy1 = -hw + pad_y, hw - pad_y
    sz0, sz1 = z_bot + pad_bot, z_top - pad_top

    # Map front UV helper from (-hw..hw, z_bot..z_top) into uv_front
    def fuv(ya, za, yb, zb):
        u0, v0, u1, v1 = uv_front
        su0 = u0 + (u1 - u0) * ((ya + hw) / (2 * hw))
        su1 = u0 + (u1 - u0) * ((yb + hw) / (2 * hw))
        sv0 = v1 - (v1 - v0) * ((zb - z_bot) / (z_top - z_bot))
        sv1 = v1 - (v1 - v0) * ((za - z_bot) / (z_top - z_bot))
        return (su0, sv0, su1, sv1)

    # 4 front bezel frame quads surrounding screen opening
    body.quad((x_fr, -hw, z_bot), (x_fr, hw, z_bot), (x_fr, hw, sz0), (x_fr, -hw, sz0),
              fuv(-hw, z_bot, hw, sz0), outward=(1, 0, 0))
    body.quad((x_fr, -hw, sz1), (x_fr, hw, sz1), (x_fr, hw, z_top), (x_fr, -hw, z_top),
              fuv(-hw, sz1, hw, z_top), outward=(1, 0, 0))
    body.quad((x_fr, -hw, sz0), (x_fr, sy0, sz0), (x_fr, sy0, sz1), (x_fr, -hw, sz1),
              fuv(-hw, sz0, sy0, sz1), outward=(1, 0, 0))
    body.quad((x_fr, sy1, sz0), (x_fr, hw, sz0), (x_fr, hw, sz1), (x_fr, sy1, sz1),
              fuv(sy1, sz0, hw, sz1), outward=(1, 0, 0))

    # Recessed chamfered inner bezel lip from x_fr back to x_scr (creates authentic deep CRT shadow rim!)
    x_scr = x_fr - 0.75
    iy0, iy1 = sy0 + 0.35, sy1 - 0.35
    iz0, iz1 = sz0 + 0.30, sz1 - 0.30
    body.quad((x_scr, iy0, iz0), (x_scr, iy1, iz0), (x_fr, sy1, sz0), (x_fr, sy0, sz0), uv_dark, outward=(0.4, 0, 1))
    body.quad((x_fr, sy0, sz1), (x_fr, sy1, sz1), (x_scr, iy1, iz1), (x_scr, iy0, iz1), uv_dark, outward=(0.4, 0, -1))
    body.quad((x_fr, sy0, sz0), (x_scr, iy0, iz0), (x_scr, iy0, iz1), (x_fr, sy0, sz1), uv_dark, outward=(0.4, 1, 0))
    body.quad((x_scr, iy1, iz0), (x_fr, sy1, sz0), (x_fr, sy1, sz1), (x_scr, iy1, iz1), uv_dark, outward=(0.4, -1, 0))

    # Optional protruding OSD control bar on Gamer Black CRT (kind == 3)
    if kind == 3:
        body.box(x_fr - 0.1, -3.8, z_bot + 0.45, x_fr + 0.45, 3.8, z_bot + 1.55, {"all": uv_base, "px": fuv(-3.8, z_bot + 0.45, 3.8, z_bot + 1.55)})

    # 3. Stepped tapered rear CRT cathode housing (x_bk .. x_mid) + electron-gun rear cap + VGA cord stub
    x_step = -3.8
    body.frustum_x(
        x_step, -hw * 0.72, z_bot + 1.6, hw * 0.72, z_top - 1.5,
        x_mid, -hw * 0.96, z_bot + 0.2, hw * 0.96, z_top - 0.2,
        {"pz": uv_side, "nz": uv_base, "py": uv_side, "ny": uv_side},
        cap0=False, cap1=False,
    )
    body.frustum_x(
        x_bk, -hw * 0.40, z_bot + 3.8, hw * 0.40, z_top - 3.8,
        x_step, -hw * 0.72, z_bot + 1.6, hw * 0.72, z_top - 1.5,
        {"pz": uv_back, "nz": uv_back, "py": uv_back, "ny": uv_back, "nx": uv_back},
        cap0=True, cap1=False,
    )
    # Molded rear VGA/power cable strain relief stub
    body.strut((x_bk + 0.2, -1.2, z_bot + 4.4), (x_bk - 1.6, -1.8, 1.2), 0.38, uv_dark, segs=6)

    # 3b. 3D Keyboard + Mousepad + Mouse in front of CRT (+X = +8.0..+11.8, sitting flush on z=0 tabletop!)
    # Viewer sits at +X looking -X: left hand is -Y (keyboard), right hand is +Y (mousepad + mouse)!
    body.frustum_x(8.0, -7.8, 0.0, 3.6, 0.85, 11.7, -7.8, 0.0, 3.6, 0.48,
                   {"pz": uv_kbd, "all": uv_base})
    body.box(8.3, 4.1, 0.0, 11.7, 7.9, 0.16, {"pz": uv_mpad, "all": uv_dark})
    body.frustum_x(9.0, 5.2, 0.16, 6.8, 0.88, 11.0, 5.3, 0.16, 6.7, 0.62, {"all": uv_base})

    # 4. Curved 4x3 subdivided 3D CRT glass screen surface (4 cols x 3 rows = 24 tris!)
    #    Viewer at +X looking -X: left (u=0) is iy0 (-Y), right (u=1) is iy1 (+Y), top (v=0) is iz1 (+Z), bottom (v=1) is iz0 (-Z).
    nx_g, nz_g = 4, 3
    grid_pts = {}
    for gi in range(nx_g + 1):
        u = gi / nx_g
        yn = 2.0 * u - 1.0
        yv = iy0 + (iy1 - iy0) * u
        for gj in range(nz_g + 1):
            w = gj / nz_g  # 0 at bottom (iz0), 1 at top (iz1)
            zn = 2.0 * w - 1.0
            zv = iz0 + (iz1 - iz0) * w
            if kind == 2:
                # Sony Trinitron: vertically flat, subtle horizontal cylindrical curve!
                curve = bulge * (1.0 - yn * yn)
            else:
                # Classic spherical/ellipsoidal CRT glass dome!
                curve = bulge * max(0.0, 1.0 - 0.52 * yn * yn - 0.48 * zn * zn)
            grid_pts[(gi, gj)] = (x_scr + curve, yv, zv)

    for gi in range(nx_g):
        u0, u1 = gi / nx_g, (gi + 1) / nx_g
        for gj in range(nz_g):
            w0, w1 = gj / nz_g, (gj + 1) / nz_g
            # Image top is v=0 (at w=1 / top Z), image bottom is v=1 (at w=0 / bottom Z)
            scr.quad(
                grid_pts[(gi, gj)],
                grid_pts[(gi + 1, gj)],
                grid_pts[(gi + 1, gj + 1)],
                grid_pts[(gi, gj + 1)],
                (u0, 1.0 - w1, u1, 1.0 - w0),
                outward=(1, 0, 0),
            )

    md3_name = f"lan_mon{kind}"
    md3_path = os.path.join(progs_bklan_dir, f"{md3_name}.md3")
    _write_md3(md3_path, md3_name, [body, scr])

    # Write .skin files _0.skin .. _6.skin so ANY monitor can play Q3A, CS 1.5, Win98, or Dead CRT!
    for sk_i, sh_name in enumerate(SCREEN_SHADERS):
        skin_path = os.path.join(progs_bklan_dir, f"{md3_name}.md3_{sk_i}.skin")
        with open(skin_path, "w", encoding="utf-8", newline="\n") as sf:
            sf.write(f"body,{tex_rel}\nscreen,{sh_name}\n")


# ==============================================================================
# 2. FOUR UNIQUE 3D COMPUTER TOWERS (lan_pc1..4.md3)
# ==============================================================================
def _make_pc_atlas(kind: int) -> Image.Image:
    """256x256 texture per PC tower:
      [0..96,   0..224]  = Detailed Front Bezel (5.25" CD/DVD bays, 3.5" floppy, buttons, LEDs, grilles, badges)
      [96..192, 0..224]  = Rear ATX panel (PSU fan grille, I/O shield, PCI slots, exhaust fan)
      [192..256, 0..128] = Left/Right Side panel metal + vent perforations
      [192..256, 128..256] = Top panel / feet / accent metal
    """
    base_cols = {
        1: ((212, 204, 186), (196, 188, 170), (148, 140, 124)),   # Classic Beige ATX Mid-Tower
        2: ((44, 46, 52), (38, 40, 46), (26, 28, 32)),            # Black Chieftec Dragon Modded Case
        3: ((212, 206, 192), (72, 118, 168), (54, 88, 132)),      # Two-Tone Beige & Translucent Bondi-Blue Case
        4: ((192, 198, 206), (174, 180, 188), (118, 124, 132)),   # Brushed Silver Aluminium Full-Tower
    }
    front_c, side_c, dark_c = base_cols[kind]
    im = Image.new("RGB", (256, 256), side_c)

    # Brushed metal / plastic micro-grain
    arr = np.asarray(im, dtype=np.int16)
    rng_np = np.random.default_rng(200 + kind)
    if kind == 4:
        # Horizontal brushed aluminium streaks!
        streak = rng_np.integers(-8, 9, size=(256, 1, 1))
        arr = np.clip(arr + streak + rng_np.integers(-3, 4, size=(256, 256, 1)), 0, 255).astype(np.uint8)
    else:
        arr = np.clip(arr + rng_np.integers(-5, 6, size=(256, 256, 1)), 0, 255).astype(np.uint8)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)

    # --- Front Bezel (0..96, 0..224) ---
    d.rectangle([0, 0, 95, 223], fill=front_c, outline=dark_c)
    if kind == 1:
        # Classic Beige ATX: 2x CD-ROM/CD-RW + 1x empty bay + 2x 3.5" floppy + concave vent scoop
        for bi in range(3):
            by = 14 + bi * 24
            d.rectangle([10, by, 85, by + 20], fill=(202, 194, 176), outline=(130, 122, 108))
            if bi < 2:
                d.rectangle([14, by + 4, 72, by + 11], fill=(168, 160, 144))  # CD tray lip
                d.rectangle([74, by + 13, 81, by + 17], fill=(120, 125, 118)) # eject button
                d.ellipse([18, by + 14, 21, by + 17], fill=(75, 235, 85) if bi == 0 else (235, 165, 45))
        # 3.5" Floppy drive
        d.rectangle([18, 92, 77, 108], fill=(196, 188, 170), outline=(125, 118, 104))
        d.rectangle([24, 97, 71, 101], fill=(72, 68, 60))
        d.rectangle([62, 102, 70, 106], fill=(140, 134, 120))
        # Power + Reset + Green/Amber LEDs + Intel/AMD sticker + lower louver holes
        d.ellipse([38, 124, 57, 143], fill=(180, 172, 156), outline=(105, 98, 86))
        d.ellipse([43, 148, 52, 157], fill=(165, 158, 142), outline=(105, 98, 86))
        d.ellipse([30, 132, 34, 136], fill=(65, 250, 80))
        d.ellipse([30, 140, 34, 144], fill=(255, 170, 35))
        d.rectangle([14, 122, 25, 134], fill=(35, 95, 195))  # Intel Inside blue badge!
        for vy in range(170, 214, 7):
            for vx in range(20, 76, 9):
                d.rectangle([vx, vy, vx + 5, vy + 3], fill=(95, 90, 80))

    elif kind == 2:
        # Modded Black Chieftec Dragon / Antec SX1030: upper stealth optical bays + iconic slotted curved grille!
        for bi in range(3):
            by = 14 + bi * 22
            d.rectangle([10, by, 85, by + 18], fill=(52, 54, 62), outline=(24, 26, 30))
            if bi < 2:
                d.rectangle([15, by + 5, 70, by + 10], fill=(34, 36, 42))
                d.ellipse([75, by + 7, 79, by + 11], fill=(65, 235, 255))
        # Chieftec latch + arched horizontal louvers with faint blue UV inner glow peeking through!
        d.rectangle([40, 86, 55, 98], fill=(75, 78, 88), outline=(22, 22, 26))
        for vy in range(106, 212, 7):
            d.rectangle([14, vy, 81, vy + 4], fill=(22, 36, 62))
            d.line([(20, vy + 2), (75, vy + 2)], fill=(45, 110, 215), width=1)

    elif kind == 3:
        # Two-Tone Beige & Translucent Bondi-Blue Curved Case (from orcom 01:04!)
        # Translucent blue side cheeks on front bezel!
        d.rectangle([0, 0, 16, 223], fill=(62, 112, 168))
        d.rectangle([79, 0, 95, 223], fill=(62, 112, 168))
        d.pieslice([8, 126, 87, 232], 180, 360, fill=(58, 106, 162), outline=(38, 72, 118))
        for bi in range(2):
            by = 18 + bi * 25
            d.rectangle([18, by, 77, by + 20], fill=(216, 210, 196), outline=(140, 134, 122))
            d.rectangle([22, by + 5, 66, by + 11], fill=(176, 170, 156))
            d.rectangle([68, by + 12, 74, by + 16], fill=(90, 130, 180))
        d.rectangle([22, 76, 73, 92], fill=(210, 204, 190), outline=(140, 134, 122))
        d.rectangle([28, 82, 66, 85], fill=(65, 65, 70))
        # Big silver power button + glowing blue ring
        d.ellipse([36, 112, 59, 135], fill=(195, 202, 212), outline=(65, 195, 255), width=2)
        for vy in range(154, 208, 8):
            d.line([(22, vy), (73, vy)], fill=(34, 66, 108), width=3)

    else:
        # Brushed Silver Aluminium Full-Tower: black mesh 5.25" bays + cyan temp LCD + 4 silver fanbus knobs!
        for bi in range(3):
            by = 12 + bi * 21
            d.rectangle([10, by, 85, by + 17], fill=(42, 46, 52), outline=(95, 100, 108))
            d.rectangle([68, by + 6, 78, by + 12], fill=(175, 182, 190))
        # Bay 4: Glowing Cyan LCD Temperature & Fan Bus Controller!
        d.rectangle([10, 76, 85, 96], fill=(34, 38, 44), outline=(95, 100, 108))
        d.rectangle([14, 80, 48, 92], fill=(28, 175, 215))
        d.text((17, 81), "38.5C", font=_font(8, bold=True), fill=(10, 30, 40))
        for ki in range(4):
            kx = 53 + ki * 8
            d.ellipse([kx, 82, kx + 6, 88], fill=(210, 215, 222), outline=(60, 65, 72))
        # Lower anodized mesh intake grille + brushed silver bezel
        d.rectangle([14, 128, 81, 208], fill=(46, 50, 56), outline=(115, 122, 130))
        for gy in range(132, 206, 6):
            d.line([(16, gy), (79, gy)], fill=(28, 30, 34), width=2)
        d.ellipse([42, 106, 53, 117], fill=(220, 225, 232), outline=(55, 185, 255))

    # --- Rear ATX Panel (96..192, 0..224) ---
    d.rectangle([96, 0, 191, 223], fill=(148, 152, 158) if kind != 2 else (48, 50, 56), outline=(70, 72, 78))
    # Top PSU exhaust fan grille + black IEC socket
    d.rectangle([104, 10, 183, 56], fill=(128, 132, 138) if kind != 2 else (38, 40, 46), outline=(60, 62, 68))
    d.ellipse([110, 14, 150, 52], fill=(32, 34, 38), outline=(85, 88, 94))
    d.ellipse([122, 26, 138, 40], fill=(55, 58, 64))
    d.rectangle([156, 20, 178, 38], fill=(22, 22, 26))
    # ATX I/O shield (PS/2 purple+green, serial teal, LPT magenta, VGA blue, 10/100 RJ45!)
    d.rectangle([106, 66, 144, 132], fill=(168, 172, 178), outline=(75, 78, 84))
    d.ellipse([110, 70, 119, 79], fill=(135, 65, 185))   # PS/2 kbd purple
    d.ellipse([122, 70, 131, 79], fill=(65, 185, 85))    # PS/2 mouse green
    d.rectangle([110, 84, 136, 94], fill=(185, 55, 125)) # LPT parallel port
    d.rectangle([110, 98, 128, 108], fill=(45, 75, 185)) # VGA port
    d.rectangle([110, 114, 124, 126], fill=(215, 210, 195)) # RJ45 LAN jack w/ link LED!
    d.ellipse([126, 118, 130, 122], fill=(75, 250, 85))
    # Rear 80mm case fan
    d.ellipse([148, 72, 182, 106], fill=(30, 32, 36), outline=(80, 84, 90))
    # 6 horizontal PCI expansion slot brackets
    for si in range(6):
        sy = 142 + si * 11
        d.rectangle([108, sy, 176, sy + 7], fill=(112, 116, 122), outline=(55, 58, 64))

    # --- Side Panel & Top Metal (192..256, 0..256) ---
    side_fill = front_c if kind != 3 else (208, 202, 188)
    d.rectangle([192, 0, 255, 127], fill=side_fill, outline=dark_c)
    for vy in range(76, 116, 6):
        for vx in range(204, 244, 6):
            d.rectangle([vx, vy, vx + 3, vy + 3], fill=dark_c)
    if kind == 2:
        # Black latch handle on Chieftec panel
        d.rectangle([196, 48, 212, 74], fill=(24, 26, 30), outline=(120, 125, 135))
        d.ellipse([204, 58, 209, 63], fill=(195, 200, 210))
    # Brushed silver / dark accent swatch at bottom-right (192..256, 128..256)
    d.rectangle([192, 128, 255, 191], fill=side_fill)
    d.rectangle([192, 192, 255, 255], fill=(185, 192, 202) if kind == 2 else dark_c)
    return im


def _make_pc2_glow_tex() -> Image.Image:
    """Self-lit 256x256 texture for lan_pc2.md3 'glow' surface (modeled straight after Orcom 2.mpg 00860.jpg!):
      [0..192, 0..192] = Clear acrylic side window showing silver PSU w/ label, galvanized drive cages,
                         twisted yellow IDE cables, orange Thermaltake CPU cooler ring, and glowing blue UV cathodes!
      [192..256, 0..128] = Bright red neon cold-cathode bar mounted on top of the case!
      [0..192, 192..256] = Glowing blue UV front intake grille strips!
    """
    im = Image.new("RGB", (256, 256), (18, 28, 58))
    d = ImageDraw.Draw(im)

    # Window interior (0..192, 0..192): deep UV blue motherboard cavity
    d.rectangle([0, 0, 191, 191], fill=(22, 42, 96))
    # Top-left silver ATX PSU box + white spec sticker (just like 00860.jpg!)
    d.rectangle([6, 6, 74, 48], fill=(155, 160, 168), outline=(90, 95, 105))
    d.rectangle([12, 12, 66, 40], fill=(232, 232, 228))
    for ly in range(16, 38, 5):
        d.line([(16, ly), (60, ly)], fill=(95, 95, 105), width=1)
    # Horizontal steel chassis crossbeam
    d.rectangle([4, 49, 188, 58], fill=(145, 152, 162))
    # Right-side galvanized steel 5.25" & 3.5" drive bays with stamped holes
    d.rectangle([126, 8, 186, 172], fill=(148, 154, 160), outline=(85, 90, 98))
    for hy in (24, 44, 82, 118, 148):
        d.ellipse([146, hy, 160, hy + 12], fill=(28, 38, 68))
    # Dark green/brown motherboard PCB + PCI cards + glowing blue reflection
    d.rectangle([14, 62, 122, 174], fill=(26, 56, 54), outline=(45, 95, 120))
    # Orange Thermaltake Volcano CPU cooler shroud w/ black 80mm fan (exact match to 00860.jpg!)
    d.rectangle([28, 116, 74, 162], fill=(230, 102, 42), outline=(140, 55, 20))
    d.ellipse([32, 120, 70, 158], fill=(24, 26, 32), outline=(210, 215, 225), width=2)
    # Rear silver wire fan grille top-left of mobo
    d.ellipse([38, 68, 68, 98], outline=(185, 198, 225), width=1)
    d.ellipse([44, 74, 62, 92], outline=(165, 185, 220), width=1)
    # Twisted bright-yellow rounded IDE ribbon cables snaking from mobo to optical/HDD bays!
    d.line([(92, 156), (84, 112), (104, 62)], fill=(245, 220, 68), width=6)
    d.line([(106, 148), (94, 96), (126, 74)], fill=(235, 205, 58), width=5)
    # Twin ultra-bright cyan/blue UV cold-cathode tubes glowing along bottom of window!
    d.rectangle([24, 174, 168, 186], fill=(85, 195, 255))
    d.rectangle([38, 177, 154, 183], fill=(225, 250, 255))
    # Acrylic window edge reflection highlight
    d.line([(10, 16), (48, 12), (20, 54)], fill=(120, 185, 255), width=1)

    # Red neon cold-cathode bar on top of case (192..256, 0..128)
    d.rectangle([192, 0, 255, 127], fill=(235, 38, 38))
    d.rectangle([206, 8, 241, 119], fill=(255, 145, 135))

    # Glowing blue intake strip (0..192, 192..256)
    d.rectangle([0, 192, 191, 255], fill=(45, 145, 255))
    d.rectangle([12, 212, 179, 235], fill=(175, 235, 255))
    return im


def _build_pc_tower(progs_bklan_dir: str, kind: int):
    atlas = _make_pc_atlas(kind)
    tex_rel = f"progs/bklan/t_pc{kind}"
    _save_tex(atlas, os.path.join(progs_bklan_dir, f"t_pc{kind}.png"), DIFFUSE_GAIN)

    uv_front = _uv_rect(0, 0, 96, 224)
    uv_rear = _uv_rect(96, 0, 192, 224)
    uv_side = _uv_rect(192, 0, 256, 128)
    uv_top = _uv_rect(192, 128, 256, 192)
    uv_acc = _uv_rect(192, 192, 256, 256)

    body = SurfBuilder("body", tex_rel)
    builders = [body]

    if kind == 1:      # Beige ATX Mid-Tower
        hx, hy, ht = 8.4, 4.1, 17.8
    elif kind == 2:    # Modded Black Chieftec Dragon
        hx, hy, ht = 9.0, 4.4, 20.0
    elif kind == 3:    # Two-Tone Beige/Bondi Curved Tower
        hx, hy, ht = 8.5, 4.2, 18.2
    else:              # Brushed Silver Full-Tower
        hx, hy, ht = 9.2, 4.5, 21.6

    z0 = 0.7 if kind in (2, 4) else 0.35

    # Case feet (swing-out stabilizer feet on Chieftec & Full-Tower; rubber pads on 1 & 3)
    if kind in (2, 4):
        for fx in (-hx * 0.68, hx * 0.68):
            body.box(fx - 1.1, -hy - 0.85, 0.0, fx + 1.1, hy + 0.85, z0, {"all": uv_acc})
    else:
        for fx in (-hx * 0.75, hx * 0.75):
            for fy in (-hy * 0.72, hy * 0.72):
                body.box(fx - 0.8, fy - 0.7, 0.0, fx + 0.8, fy + 0.7, z0, {"all": uv_acc})

    # Main steel/aluminium chassis box (back to x_bezel)
    x_bez = hx - 1.35
    if kind == 2:
        # Chieftec left side (-Y) has a real recessed acrylic UV window frame!
        body.box(-hx, -hy, z0, x_bez, hy, ht,
                 {"nx": uv_rear, "py": uv_side, "pz": uv_top, "nz": uv_acc, "all": uv_side},
                 skip=("px", "ny"))
        # Frame around -Y window opening (wx0..wx1, wz0..wz1)
        wx0, wx1 = -hx + 1.8, x_bez - 1.4
        wz0, wz1 = z0 + 2.0, ht - 1.8
        body.quad((-hx, -hy, z0), (x_bez, -hy, z0), (x_bez, -hy, wz0), (-hx, -hy, wz0), uv_side, outward=(0, -1, 0))
        body.quad((-hx, -hy, wz1), (x_bez, -hy, wz1), (x_bez, -hy, ht), (-hx, -hy, ht), uv_side, outward=(0, -1, 0))
        body.quad((-hx, -hy, wz0), (wx0, -hy, wz0), (wx0, -hy, wz1), (-hx, -hy, wz1), uv_side, outward=(0, -1, 0))
        body.quad((wx1, -hy, wz0), (x_bez, -hy, wz0), (x_bez, -hy, wz1), (wx1, -hy, wz1), uv_side, outward=(0, -1, 0))

        # Self-lit UV acrylic window + red top neon bar + silver LAN carry handle!
        # Named scr_pc2uv (NOT t_pc2_glow, because DarkPlaces auto-applies <tex>_glow.png over the entire <tex> surface!)
        glow_im = _make_pc2_glow_tex()
        _save_tex(glow_im, os.path.join(progs_bklan_dir, "scr_pc2uv.png"), GLOW_GAIN)
        glow = SurfBuilder("glow", "progs/bklan/scr_pc2uv")
        uv_win = _uv_rect(0, 0, 192, 192)
        uv_neon = _uv_rect(192, 0, 256, 128)
        uv_fstrip = _uv_rect(0, 192, 192, 256)
        # Left (-Y) full acrylic window + subtle right (+Y) UV vent slit so it glows from either side of a desk!
        glow.quad((wx0, -hy + 0.18, wz0), (wx1, -hy + 0.18, wz0), (wx1, -hy + 0.18, wz1), (wx0, -hy + 0.18, wz1),
                  uv_win, outward=(0, -1, 0))
        glow.quad((wx1 * 0.6, hy + 0.04, wz0 + 1.5), (wx0 * 0.6, hy + 0.04, wz0 + 1.5),
                  (wx0 * 0.6, hy + 0.04, wz0 + 4.0), (wx1 * 0.6, hy + 0.04, wz0 + 4.0),
                  uv_fstrip, outward=(0, 1, 0))
        # Red neon cold-cathode bar mounted on top of the tower (just like Orcom 14:26!)
        glow.box(-4.8, 1.4, ht, 3.8, 2.5, ht + 0.75, {"all": uv_neon})
        # Brushed-silver tubular LAN party carry handle on top center!
        body.box(-4.6, -1.2, ht, -3.5, 0.2, ht + 1.6, {"all": uv_acc})
        body.box(3.5, -1.2, ht, 4.6, 0.2, ht + 1.6, {"all": uv_acc})
        body.box(-4.6, -1.2, ht + 1.2, 4.6, 0.2, ht + 1.85, {"all": uv_acc})
        builders.append(glow)
    else:
        body.box(-hx, -hy, z0, x_bez, hy, ht,
                 {"nx": uv_rear, "py": uv_side, "ny": uv_side, "pz": uv_top, "nz": uv_acc, "all": uv_side},
                 skip=("px",))

    # Sculpted Front Faceplate (x_bez .. hx): chamfered/curved plastic or aluminium bezel
    taper = 0.25 if kind in (1, 4) else 0.55
    body.frustum_x(
        x_bez, -hy, z0, hy, ht,
        hx, -hy + taper, z0 + 0.15, hy - taper, ht - 0.15,
        {"px": uv_front, "py": uv_side, "ny": uv_side, "pz": uv_top, "nz": uv_acc, "all": uv_front},
        cap0=False, cap1=True,
    )

    md3_name = f"lan_pc{kind}"
    _write_md3(os.path.join(progs_bklan_dir, f"{md3_name}.md3"), md3_name, builders)


# ==============================================================================
# 3. FOUR UNIQUE 3D CHAIRS (lan_chair1..4.md3)
# ==============================================================================
def _make_chair_atlas(kind: int) -> Image.Image:
    """256x256 texture per chair:
      [0..128, 0..128]   = Woven fabric / tufted leather seat & backrest cushion (with subtle edge welt shading)
      [128..256, 0..128] = Cushion side / back shell plastic
      [0..128, 128..256] = Tubular steel / bronze / chrome frame metal
      [128..256, 128..256] = Black nylon 5-star base / caster wheels / armrests
    """
    styles = {
        1: ((142, 34, 48), (112, 26, 38), (92, 78, 56), (36, 36, 40)),      # Burgundy Banquet Stacking Chair
        2: ((48, 50, 56), (38, 40, 46), (165, 172, 180), (28, 30, 34)),     # Black Executive Swivel Office Chair
        3: ((54, 78, 118), (96, 102, 112), (118, 124, 134), (34, 36, 40)),  # Padded Blue/Steel Folding Chair
        4: ((46, 98, 168), (42, 46, 54), (140, 146, 154), (30, 32, 36)),    # Cobalt & Charcoal LAN Task Chair
    }
    fab_c, back_c, metal_c, blk_c = styles[kind]
    im = Image.new("RGB", (256, 256), fab_c)

    # Woven fabric / leather grain
    arr = np.asarray(im, dtype=np.int16)
    rng_np = np.random.default_rng(300 + kind)
    weave = ((np.arange(256)[:, None] % 3 == 0).astype(np.int16) - (np.arange(256)[None, :] % 3 == 0).astype(np.int16)) * 5
    arr = np.clip(arr + weave[:, :, None] + rng_np.integers(-6, 7, size=(256, 256, 1)), 0, 255).astype(np.uint8)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)

    # TL: Cushion face with soft border seam / tufting
    d.rectangle([4, 4, 123, 123], outline=tuple(max(12, c - 28) for c in fab_c), width=3)
    if kind == 2:
        # Executive leather horizontal stitch lines
        for sy in (42, 84):
            d.line([(10, sy), (118, sy)], fill=(24, 26, 30), width=3)
            d.line([(10, sy + 2), (118, sy + 2)], fill=(72, 76, 84), width=1)
    elif kind == 1:
        # Subtle gold/burgundy banquet fleck pattern
        rng = random.Random(301)
        for _ in range(110):
            fx, fy = rng.randint(10, 116), rng.randint(10, 116)
            d.point((fx, fy), fill=(186, 132, 72))

    # TR: Back shell / cushion edge
    d.rectangle([128, 0, 255, 127], fill=back_c)
    d.rectangle([134, 6, 249, 121], outline=tuple(max(10, c - 18) for c in back_c), width=2)

    # BL: Steel / bronze tubular frame
    d.rectangle([0, 128, 127, 255], fill=metal_c)
    for sx in range(8, 120, 16):
        d.line([(sx, 128), (sx, 255)], fill=tuple(min(255, c + 24) for c in metal_c), width=2)

    # BR: Black nylon base / casters / armrests
    d.rectangle([128, 128, 255, 255], fill=blk_c)
    return im


def _build_chair(progs_bklan_dir: str, kind: int):
    """Build lan_chair<kind>.md3 facing +X (backrest at -X, sitter looks +X)."""
    atlas = _make_chair_atlas(kind)
    tex_rel = f"progs/bklan/t_chair{kind}"
    _save_tex(atlas, os.path.join(progs_bklan_dir, f"t_chair{kind}.png"), DIFFUSE_GAIN)

    uv_fab = _uv_rect(0, 0, 128, 128)
    uv_back = _uv_rect(128, 0, 256, 128)
    uv_metal = _uv_rect(0, 128, 128, 256)
    uv_blk = _uv_rect(128, 128, 256, 256)

    b = SurfBuilder("body", tex_rel)

    if kind == 1:
        # 1. Burgundy Padded Banquet Stacking Chair (Orcom 2.mpg 00516.jpg!)
        # 4 angled tubular legs + side/front stretchers + crowned burgundy seat + arched hoop backrest!
        for sy in (-7.6, 7.6):
            # Front leg (slants slightly forward to +X at floor)
            b.strut((6.8, sy, 16.8), (8.2, sy * 1.04, 0.0), 0.55, uv_metal, segs=6)
            # Rear continuous frame leg rising from floor all the way up to backrest hoop!
            b.strut((-9.2, sy * 1.05, 0.0), (-7.0, sy, 17.0), 0.55, uv_metal, segs=6)
            b.strut((-7.0, sy, 17.0), (-8.8, sy * 0.92, 32.5), 0.52, uv_metal, segs=6)
            # Side stacking stretcher bar
            b.strut((-7.8, sy * 1.02, 7.5), (7.5, sy * 1.02, 7.5), 0.38, uv_metal, segs=6)
        # Arched crown bar across top of backrest + under-seat crossbars
        b.strut((-8.8, -7.0, 32.5), (-9.1, -3.2, 35.0), 0.52, uv_metal, segs=6)
        b.strut((-9.1, -3.2, 35.0), (-9.1, 3.2, 35.0), 0.52, uv_metal, segs=6)
        b.strut((-9.1, 3.2, 35.0), (-8.8, 7.0, 32.5), 0.52, uv_metal, segs=6)
        b.strut((7.4, -7.6, 8.5), (7.4, 7.6, 8.5), 0.38, uv_metal, segs=6)
        # Thick crowned burgundy seat cushion
        b.frustum_x(-7.2, -8.2, 16.5, 8.2, 18.8, 7.8, -8.0, 16.5, 8.0, 18.6,
                    {"pz": uv_fab, "px": uv_fab, "py": uv_back, "ny": uv_back, "all": uv_back})
        # Curved trapezoidal burgundy backrest cushion
        b.frustum_x(-8.9, -6.6, 20.0, 6.6, 33.6, -7.3, -6.4, 20.0, 6.4, 33.4,
                    {"px": uv_fab, "nx": uv_back, "all": uv_fab})

    elif kind == 2:
        # 2. Black Executive 5-Star Rolling Office Chair with Loop Armrests!
        # 5-star caster base + 5 twin-wheel casters + pneumatic cylinder
        b.cyl_z(0.0, 0.0, 2.2, 5.2, 1.8, 1.5, uv_blk, segs=10, cap_top=True, cap_bot=True)
        b.cyl_z(0.0, 0.0, 5.0, 16.5, 1.15, 1.05, uv_metal, segs=10, cap_top=False, cap_bot=False)
        for k in range(5):
            ang = 2.0 * math.pi * k / 5.0 + 0.3
            ex, ey = 9.8 * math.cos(ang), 9.8 * math.sin(ang)
            b.strut((0.0, 0.0, 3.8), (ex, ey, 2.2), 0.72, uv_blk, segs=6)
            b.cyl_z(ex, ey, 0.0, 2.1, 1.15, 1.15, uv_blk, segs=8, cap_top=True, cap_bot=True)
        # Contoured plush seat cushion
        b.frustum_x(-8.4, -9.2, 16.4, 9.2, 19.4, 8.6, -9.0, 16.2, 9.0, 19.1,
                    {"pz": uv_fab, "px": uv_fab, "all": uv_back})
        # High segmented executive backrest + headrest pillow (tilted back toward -X)
        b.frustum_x(-9.8, -8.5, 18.8, 8.5, 32.0, -7.4, -8.2, 18.8, 8.2, 31.8,
                    {"px": uv_fab, "nx": uv_back, "all": uv_fab})
        b.frustum_x(-10.8, -7.8, 31.8, 7.8, 40.2, -8.4, -7.5, 31.8, 7.5, 39.8,
                    {"px": uv_fab, "nx": uv_back, "all": uv_fab})
        # Sculpted loop armrests on -Y and +Y sides!
        for sy in (-9.6, 9.6):
            b.strut((-5.5, sy, 18.0), (-5.8, sy, 25.2), 0.62, uv_blk, segs=6)
            b.strut((4.8, sy, 18.0), (4.2, sy, 24.8), 0.62, uv_blk, segs=6)
            b.box(-6.4, sy - 0.9, 24.6, 5.0, sy + 0.9, 25.9, {"all": uv_blk, "pz": uv_fab})

    elif kind == 3:
        # 3. Classic LAN Party Padded Steel Folding Chair!
        for sy in (-7.4, 7.4):
            # Continuous front-foot-to-backrest slanted main tubular rail!
            b.strut((7.8, sy, 0.0), (-8.6, sy, 32.2), 0.48, uv_metal, segs=6)
            # Crossing rear-foot-to-front-seat X-leg!
            b.strut((-8.2, sy, 0.0), (5.8, sy, 16.6), 0.46, uv_metal, segs=6)
        # Front & rear horizontal foot crossbars + curved top steel backrest pan!
        b.strut((6.2, -7.4, 5.2), (6.2, 7.4, 5.2), 0.36, uv_metal, segs=6)
        b.strut((-6.6, -7.4, 5.2), (-6.6, 7.4, 5.2), 0.36, uv_metal, segs=6)
        b.strut((-8.6, -7.4, 32.2), (-8.6, 7.4, 32.6), 0.50, uv_metal, segs=6)
        # Stamped metal backrest + navy padded insert
        b.frustum_x(-8.8, -7.2, 24.0, 7.2, 32.4, -7.7, -7.0, 24.0, 7.0, 32.2,
                    {"px": uv_fab, "nx": uv_back, "all": uv_metal})
        # Padded vinyl folding seat pan
        b.frustum_x(-5.8, -7.0, 15.8, 7.0, 17.5, 6.8, -6.8, 15.6, 6.8, 17.3,
                    {"pz": uv_fab, "px": uv_fab, "all": uv_metal})

    else:
        # 4. Cobalt-Blue & Charcoal Armless Ergonomic LAN Task Chair (slides tight under LAN rows!)
        b.cyl_z(0.0, 0.0, 2.0, 4.8, 1.6, 1.4, uv_blk, segs=10, cap_top=True, cap_bot=True)
        b.cyl_z(0.0, 0.0, 4.6, 16.2, 1.05, 0.95, uv_blk, segs=10)
        for k in range(5):
            ang = 2.0 * math.pi * k / 5.0
            ex, ey = 9.0 * math.cos(ang), 9.0 * math.sin(ang)
            b.strut((0.0, 0.0, 3.6), (ex, ey, 2.0), 0.65, uv_blk, segs=6)
            b.cyl_z(ex, ey, 0.0, 2.0, 1.05, 1.05, uv_blk, segs=8, cap_top=True, cap_bot=True)
        # Contoured cobalt task seat
        b.frustum_x(-7.6, -8.5, 16.0, 8.5, 18.8, 8.0, -8.2, 15.8, 8.2, 18.5,
                    {"pz": uv_fab, "px": uv_fab, "all": uv_back})
        # Curved black J-spine bar behind seat up to lumbar pad
        b.box(-8.8, -1.5, 16.5, -7.4, 1.5, 27.5, {"all": uv_blk})
        b.strut((-3.0, 0.0, 16.2), (-8.1, 0.0, 17.2), 1.1, uv_blk, segs=6)
        # Sculpted cobalt mid-back lumbar cushion with black plastic rear shell
        b.frustum_x(-9.2, -7.8, 22.0, 7.8, 35.2, -7.5, -7.4, 22.2, 7.4, 34.8,
                    {"px": uv_fab, "nx": uv_back, "all": uv_back})

    md3_name = f"lan_chair{kind}"
    _write_md3(os.path.join(progs_bklan_dir, f"{md3_name}.md3"), md3_name, [b])


# ==============================================================================
# 4. FOUR UNIQUE 3D LAN TABLES (lan_table1..4.md3 + lan_table4s.md3)
# ==============================================================================
def _make_table_atlas(kind: int) -> Image.Image:
    """256x256 texture per LAN table:
      [0..256, 0..128]   = Tabletop surface (woodgrain / speckled blow-molded granite / shop Formica / honey oak)
      [0..128, 128..192] = Table edge trim (rubber T-molding / polyethylene lip / angle-iron steel / oak edge)
      [128..256, 128..192] = Leg metal (black powder-coat / grey steel / brushed silver)
      [0..256, 192..256] = Under-table hardware / power strip / bright orange LAN extension cord!
    """
    im = Image.new("RGB", (256, 256), (90, 90, 90))
    rng_np = np.random.default_rng(400 + kind)
    arr = np.zeros((256, 256, 3), dtype=np.float32)

    if kind == 1:
        # Rich dark walnut woodgrain laminate!
        base = np.array([138.0, 92.0, 56.0])
        yy = np.arange(128)[:, None]
        xx = np.arange(256)[None, :]
        grain = np.sin(yy * 0.42 + np.sin(xx * 0.05) * 2.2) * 14.0 + rng_np.normal(0, 5, (128, 256))
        arr[:128, :, :] = base[None, None, :] + grain[:, :, None] * np.array([1.0, 0.72, 0.45])
        edge_c, leg_c = (38, 38, 42), (46, 48, 54)
    elif kind == 2:
        # Speckled cream/granite white blow-molded Lifetime folding table (Orcom 01:26!)
        base = np.array([216.0, 212.0, 202.0])
        speck = rng_np.normal(0, 11, (128, 256, 1))
        pepper = (rng_np.random((128, 256, 1)) < 0.045) * -55.0
        arr[:128, :, :] = base + speck + pepper
        edge_c, leg_c = (196, 192, 182), (108, 112, 118)
    elif kind == 3:
        # Heavy-duty industrial shop/LAN table: grey-tan speckled worktop + dark steel angle-iron edge
        base = np.array([148.0, 146.0, 138.0])
        arr[:128, :, :] = base + rng_np.normal(0, 9, (128, 256, 1))
        edge_c, leg_c = (58, 64, 70), (64, 70, 78)
    else:
        # Warm honey-oak computer lab desk with cable grommets!
        base = np.array([188.0, 142.0, 84.0])
        yy = np.arange(128)[:, None]
        xx = np.arange(256)[None, :]
        grain = np.sin(yy * 0.35 + np.cos(xx * 0.04) * 1.8) * 12.0 + rng_np.normal(0, 4, (128, 256))
        arr[:128, :, :] = base[None, None, :] + grain[:, :, None] * np.array([1.0, 0.8, 0.5])
        edge_c, leg_c = (152, 112, 62), (168, 174, 182)

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)

    if kind == 2:
        # Molded seam lines on blow-molded plastic top
        d.rectangle([8, 8, 247, 119], outline=(186, 182, 172), width=2)
    elif kind == 4:
        # Two black circular plastic cable grommets inset near rear of honey-oak desk!
        for gx in (56, 200):
            d.ellipse([gx - 9, 18, gx + 9, 36], fill=(32, 34, 38), outline=(18, 18, 20), width=2)
            d.pieslice([gx - 5, 22, gx + 5, 32], 0, 220, fill=(14, 14, 16))

    # Edge trim & leg metal swatches
    d.rectangle([0, 128, 127, 191], fill=edge_c)
    d.rectangle([128, 128, 255, 191], fill=leg_c)
    for sx in range(136, 248, 16):
        d.line([(sx, 128), (sx, 191)], fill=tuple(min(255, c + 20) for c in leg_c), width=2)

    # Bottom strip: Beige 6-outlet surge protector + glowing red rocker switch + bright orange extension cord!
    d.rectangle([0, 192, 159, 255], fill=(208, 200, 182), outline=(120, 114, 102))
    d.rectangle([10, 212, 26, 234], fill=(225, 48, 38), outline=(90, 20, 18))  # illuminated red surge switch
    for oi in range(6):
        ox = 36 + oi * 19
        d.rectangle([ox, 210, ox + 13, 236], fill=(175, 168, 152), outline=(95, 90, 80))
        d.line([(ox + 4, 215), (ox + 4, 224)], fill=(35, 35, 35), width=2)
        d.line([(ox + 9, 215), (ox + 9, 224)], fill=(35, 35, 35), width=2)
        d.ellipse([ox + 5, 228, ox + 8, 231], fill=(35, 35, 35))
    # Bright orange LAN power cord swatch (160..256, 192..256)
    d.rectangle([160, 192, 255, 255], fill=(235, 108, 28))
    return im


def _build_table(progs_bklan_dir: str, kind: int, custom_hx: float = 48.0, suffix: str = ""):
    """Build lan_table<kind>.md3: long axis along X (-hx..+hx), depth along Y (-15..+15), top at Z = 30.0."""
    tex_path = os.path.join(progs_bklan_dir, f"t_table{kind}.png")
    tex_rel = f"progs/bklan/t_table{kind}"
    if not os.path.exists(tex_path):
        _save_tex(_make_table_atlas(kind), tex_path, DIFFUSE_GAIN)

    uv_top = _uv_rect(0, 0, 256, 128)
    uv_edge = _uv_rect(0, 128, 128, 192)
    uv_leg = _uv_rect(128, 128, 256, 192)
    uv_strip = _uv_rect(0, 192, 160, 256)
    uv_cord = _uv_rect(160, 192, 256, 256)

    b = SurfBuilder("body", tex_rel)
    hx, hy, zt = custom_hx, 15.0, 30.0

    if kind == 1:
        # 1. Walnut Woodgrain Folding Banquet Table + tubular black wishbone legs + diagonal braces
        b.box(-hx, -hy, 28.4, hx, hy, zt, {"pz": uv_top, "nz": uv_edge, "all": uv_edge})
        # Recessed underside steel perimeter apron
        b.box(-hx + 2.5, -hy + 2.2, 27.1, hx - 2.5, -hy + 3.0, 28.4, {"all": uv_leg})
        b.box(-hx + 2.5, hy - 3.0, 27.1, hx - 2.5, hy - 2.2, 28.4, {"all": uv_leg})
        for lx in (-hx + 9.0, hx - 9.0):
            sgn = -1.0 if lx < 0 else 1.0
            for ly in (-hy + 3.4, hy - 3.4):
                b.strut((lx, ly, 28.4), (lx, ly * 1.04, 0.0), 0.68, uv_leg, segs=6)
            b.strut((lx, -hy + 3.4, 7.5), (lx, hy - 3.4, 7.5), 0.52, uv_leg, segs=6)
            b.strut((lx, -hy + 3.4, 24.0), (lx, hy - 3.4, 24.0), 0.52, uv_leg, segs=6)
            # Diagonal folding locking V-braces up to tabletop center!
            b.strut((lx, 0.0, 14.5), (lx - sgn * 14.0, -5.5, 28.3), 0.44, uv_leg, segs=6)
            b.strut((lx, 0.0, 14.5), (lx - sgn * 14.0, 5.5, 28.3), 0.44, uv_leg, segs=6)

    elif kind == 2:
        # 2. Speckled Granite-White Blow-Molded Folding Table (chamfered molded top + grey H-legs)
        b.frustum_x(-hx + 0.5, -hy + 0.4, 27.9, hy - 0.4, 29.8,
                    hx - 0.5, -hy + 0.4, 27.9, hy - 0.4, 29.8, {"all": uv_edge}, cap0=True, cap1=True)
        b.box(-hx, -hy, 28.1, hx, hy, zt, {"pz": uv_top, "nz": uv_edge, "all": uv_edge})
        for lx in (-hx + 9.5, hx - 9.5):
            sgn = -1.0 if lx < 0 else 1.0
            for ly in (-hy + 3.5, hy - 3.5):
                b.strut((lx, ly, 28.0), (lx - sgn * 0.8, ly * 1.05, 0.0), 0.72, uv_leg, segs=6)
            b.strut((lx - sgn * 0.4, -hy + 3.6, 8.5), (lx - sgn * 0.4, hy - 3.6, 8.5), 0.55, uv_leg, segs=6)
            b.strut((lx, 0.0, 15.0), (lx - sgn * 13.5, 0.0, 28.0), 0.48, uv_leg, segs=6)

    elif kind == 3:
        # 3. Heavy-Duty Industrial Shop / LAN Table w/ square steel legs + surge strip + orange LAN power cord!
        b.box(-hx, -hy, 28.2, hx, hy, zt, {"pz": uv_top, "nz": uv_edge, "all": uv_edge})
        # Deep angle-iron steel apron under top
        b.box(-hx + 0.8, -hy + 0.8, 26.2, hx - 0.8, hy - 0.8, 28.2, {"all": uv_leg}, skip=("pz",))
        for lx in (-hx + 3.2, hx - 3.2):
            for ly in (-hy + 2.8, hy - 2.8):
                b.box(lx - 0.9, ly - 0.9, 0.0, lx + 0.9, ly + 0.9, 26.4, {"all": uv_leg})
            b.box(lx - 0.7, -hy + 2.8, 6.5, lx + 0.7, hy - 2.8, 7.8, {"all": uv_leg})
        # Full-length lower steel cable/footrest stretcher + 6-outlet surge strip & orange power cord!
        b.box(-hx + 3.2, -1.8, 6.8, hx - 3.2, -0.4, 8.0, {"all": uv_leg})
        b.box(-14.0, -1.9, 8.0, 4.0, 1.3, 9.4, {"pz": uv_strip, "all": uv_edge})
        b.strut((4.0, -0.3, 8.6), (hx - 4.0, -1.2, 7.8), 0.42, uv_cord, segs=6)
        b.strut((hx - 4.0, -1.2, 7.8), (hx - 2.0, -3.5, 0.4), 0.42, uv_cord, segs=6)

    else:
        # 4. Honey-Oak LAN Computer Desk w/ Grommets, Silver Cantilever C-Legs, Modesty Panel & Wire Basket!
        b.box(-hx, -hy, 28.3, hx, hy, zt, {"pz": uv_top, "nz": uv_edge, "all": uv_edge})
        # Modesty crossbar panel along back (-Y or center)
        b.box(-hx + 4.0, -1.2, 19.0, hx - 4.0, 0.0, 28.3, {"all": uv_edge})
        # Under-desk wire cable basket + surge protector!
        b.box(-hx + 10.0, 0.5, 22.8, hx - 10.0, 4.5, 23.6, {"all": uv_leg})
        b.box(-8.0, 1.0, 23.6, 8.0, 4.0, 24.9, {"pz": uv_strip, "all": uv_edge})
        # Silver C-frame cantilever steel legs + wide floor skids!
        for lx in (-hx + 4.5, hx - 4.5):
            b.box(lx - 1.1, -hy + 1.5, 0.0, lx + 1.1, hy - 1.5, 1.4, {"all": uv_leg})        # floor skid
            b.box(lx - 1.0, -3.5, 1.4, lx + 1.0, 0.5, 28.3, {"all": uv_leg})                 # vertical C-column
            b.box(lx - 1.0, -hy + 2.2, 26.8, lx + 1.0, hy - 2.2, 28.3, {"all": uv_leg})      # top support arm

    md3_name = f"lan_table{kind}{suffix}"
    _write_md3(os.path.join(progs_bklan_dir, f"{md3_name}.md3"), md3_name, [b])


# ==============================================================================
# 5. SIX CUSTOM EXPLOSION DEBRIS MODELS (lan_deb_*.md3)
# ==============================================================================
def _build_debris_models(progs_bklan_dir: str):
    """Shared 256x256 debris atlas + 6 chunky 3D shrapnel models for monitors, towers, chairs, and tables."""
    im = Image.new("RGB", (256, 256), (80, 80, 80))
    d = ImageDraw.Draw(im)
    # [0..128, 0..128] Smoked phosphor CRT glass w/ bright fracture glint
    d.rectangle([0, 0, 127, 127], fill=(72, 92, 96), outline=(195, 225, 232), width=3)
    d.line([(8, 12), (112, 98)], fill=(210, 235, 240), width=2)
    d.line([(24, 110), (96, 22)], fill=(155, 185, 192), width=1)
    # [128..256, 0..128] Copper CRT deflection yoke windings + dark ferrite core
    d.rectangle([128, 0, 255, 127], fill=(186, 104, 48))
    for cy in range(6, 122, 6):
        d.line([(132, cy), (252, cy)], fill=(224, 138, 68), width=2)
    d.rectangle([128, 92, 255, 127], fill=(44, 46, 52))
    # [0..128, 128..256] Scorched beige/charcoal sheet-metal panel w/ blast soot
    d.rectangle([0, 128, 127, 255], fill=(168, 158, 140), outline=(48, 44, 40), width=3)
    d.ellipse([28, 152, 98, 224], fill=(54, 48, 44))
    for vx in range(22, 104, 10):
        d.rectangle([vx, 232, vx + 6, 242], fill=(35, 35, 38))
    # [128..256, 128..192] Black 80mm PC fan + hub sticker
    d.rectangle([128, 128, 255, 191], fill=(36, 38, 44))
    d.ellipse([160, 132, 224, 188], fill=(24, 26, 30), outline=(95, 100, 110), width=2)
    d.ellipse([182, 150, 202, 170], fill=(215, 75, 45))
    # [128..256, 192..256] Splintered walnut/oak woodgrain plank
    d.rectangle([128, 192, 255, 255], fill=(152, 104, 62))
    for wy in range(196, 252, 7):
        d.line([(130, wy), (253, wy)], fill=(112, 74, 42), width=2)

    tex_rel = "progs/bklan/t_lan_deb"
    _save_tex(im, os.path.join(progs_bklan_dir, "t_lan_deb.png"), DIFFUSE_GAIN)

    uv_glass = _uv_rect(0, 0, 128, 128)
    uv_copper = _uv_rect(128, 0, 256, 90)
    uv_dark = _uv_rect(128, 92, 256, 128)
    uv_panel = _uv_rect(0, 128, 128, 256)
    uv_fan = _uv_rect(128, 128, 256, 192)
    uv_wood = _uv_rect(128, 192, 256, 256)

    # 1. lan_deb_glass.md3 — Thick curved smoked CRT glass shard
    g = SurfBuilder("glass", tex_rel)
    g.frustum_x(-0.6, -4.2, -3.2, 3.8, 2.8, 0.7, -3.5, -2.6, 3.2, 3.4, {"all": uv_glass})
    _write_md3(os.path.join(progs_bklan_dir, "lan_deb_glass.md3"), "lan_deb_glass", [g])

    # 2. lan_deb_yoke.md3 — Copper-wound CRT deflection coil + glass electron-gun neck!
    y = SurfBuilder("yoke", tex_rel)
    y.cyl_z(0.0, 0.0, -3.5, 1.5, 1.3, 3.6, uv_copper, segs=10, cap_top=True, cap_bot=True)
    y.cyl_z(0.0, 0.0, -6.2, -3.4, 1.1, 1.25, uv_glass, segs=8, cap_top=False, cap_bot=True)
    _write_md3(os.path.join(progs_bklan_dir, "lan_deb_yoke.md3"), "lan_deb_yoke", [y])

    # 3. lan_deb_panel.md3 — Bent scorched PC case side panel
    p = SurfBuilder("panel", tex_rel)
    p.quad((-6.5, -0.4, -5.0), (0.5, 0.8, -5.0), (0.5, 0.8, 5.0), (-6.5, -0.4, 5.0), uv_panel, outward=(0, -1, 0))
    p.quad((0.5, 0.8, -5.0), (6.5, -0.6, -4.6), (6.5, -0.6, 4.6), (0.5, 0.8, 5.0), uv_panel, outward=(0, -1, 0))
    p.quad((-6.5, -0.1, -5.0), (-6.5, -0.1, 5.0), (0.5, 1.1, 5.0), (0.5, 1.1, -5.0), uv_panel, outward=(0, 1, 0))
    p.quad((0.5, 1.1, -5.0), (0.5, 1.1, 5.0), (6.5, -0.3, 4.6), (6.5, -0.3, -4.6), uv_panel, outward=(0, 1, 0))
    _write_md3(os.path.join(progs_bklan_dir, "lan_deb_panel.md3"), "lan_deb_panel", [p])

    # 4. lan_deb_fan.md3 — 80mm PC cooling fan
    fn = SurfBuilder("fan", tex_rel)
    fn.box(-3.2, -3.2, -0.9, 3.2, 3.2, 0.9, {"pz": uv_fan, "nz": uv_fan, "all": uv_dark})
    _write_md3(os.path.join(progs_bklan_dir, "lan_deb_fan.md3"), "lan_deb_fan", [fn])

    # 5. lan_deb_wheel.md3 — Broken chair caster spoke + twin wheel
    wh = SurfBuilder("wheel", tex_rel)
    wh.strut((-5.0, 0.0, 1.2), (3.5, 0.0, 0.0), 0.72, uv_dark, segs=6)
    wh.cyl_z(3.6, 0.0, -1.6, 0.4, 1.45, 1.45, uv_dark, segs=8, cap_top=True, cap_bot=True)
    _write_md3(os.path.join(progs_bklan_dir, "lan_deb_wheel.md3"), "lan_deb_wheel", [wh])

    # 6. lan_deb_plank.md3 — Jagged splintered wood/laminate table plank + bent leg stub
    pl = SurfBuilder("plank", tex_rel)
    pl.frustum_x(-9.5, -3.6, -0.8, 3.6, 0.8, 9.5, -2.2, -0.8, 3.2, 0.8, {"pz": uv_wood, "nz": uv_wood, "all": uv_panel})
    pl.strut((-4.0, 0.0, -0.8), (-6.5, 1.5, -7.5), 0.55, uv_dark, segs=6)
    _write_md3(os.path.join(progs_bklan_dir, "lan_deb_plank.md3"), "lan_deb_plank", [pl])


def build_all_models(progs_bklan_dir: str):
    os.makedirs(progs_bklan_dir, exist_ok=True)
    for k in (1, 2, 3, 4):
        _build_crt_monitor(progs_bklan_dir, k)
        _build_pc_tower(progs_bklan_dir, k)
        _build_chair(progs_bklan_dir, k)
        _build_table(progs_bklan_dir, k)
    # Compact 5.8-ft (70u) desk variant sharing t_table4.png for tight office/back-room corners
    _build_table(progs_bklan_dir, 4, custom_hx=35.0, suffix="s")
    _build_debris_models(progs_bklan_dir)
    print("Built 4 CRT monitors, 4 PC towers, 4 chairs, 4 (+1 compact) tables, and 6 debris MD3s.")
