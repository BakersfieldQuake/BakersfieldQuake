"""Builds zz_foreloco.pk3: reproducible ForeLoco powerup models, textures, shaders & sounds.

Usage:
  python -I source/mm_tools/foreloco/build_foreloco_pk3.py [bakersfield.pk3] [output_pk3]

Generates into a clean temporary directory and packs deterministically into zz_foreloco.pk3:
  - progs/foreloco_can.md3 (+ _0.skin)        : Floating 3D Watermelon Four Loko tallboy pickup
  - progs/v_foreloco.md3 (+ _0.skin)          : 40-frame 1st-person hands pick-up / open / drink viewmodel
  - progs/foreloco_proj_can.md3 (+ _0.skin)   : Tossed spinning Four Loko can projectile
  - progs/foreloco_bedpan.md3 (+ _0.skin)     : Flying stainless hospital bedpan projectile
  - progs/foreloco/*.png                      : Can artwork (from assets/four_loko_watermelon.jpg), metal, hands, bedpan
  - gfx/foreloco/vm_01.png .. vm_36.png       : 36-frame 640x480 realistic 2D viewmodel chug sequence + smear overlays
  - scripts/foreloco.shader                   : Diffuse + pulsing party glow shaders
  - sound/foreloco/*.wav                      : Tab crack, glug-glug/burp, VEGAS BABY!, 140 BPM party loop, boing, horn, jump, boost
"""
from __future__ import annotations

import argparse
import math
import os
import random
import struct
import sys
import tempfile
import wave
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
REPO_ROOT = MM_TOOLS.parent.parent
ASSETS_DIR = HERE / "assets"

if str(MM_TOOLS) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import md3lib  # noqa: E402
from build_foreloco_sprites import build_smear_overlays, build_viewmodel_sprites  # noqa: E402

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}
SR = 22050


# ---------------------------------------------------------------------------
# Vector / Mesh Helpers
# ---------------------------------------------------------------------------
def _vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vnorm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


def rot_x(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def rot_z(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


class MeshSurf:
    """Builds a single MD3 surface with Quake CW front-face winding."""

    def __init__(self, name: str, shader: str):
        self.name = name
        self.shader = shader
        self.verts: list[tuple[float, float, float]] = []
        self.norms: list[tuple[float, float, float]] = []
        self.st: list[tuple[float, float]] = []
        self.tris: list[tuple[int, int, int]] = []

    def add_v(self, p, n, uv):
        self.verts.append(p)
        self.norms.append(_vnorm(n))
        self.st.append(uv)
        return len(self.verts) - 1

    def add_tri(self, i0: int, i1: int, i2: int, outward):
        p0, p1, p2 = self.verts[i0], self.verts[i1], self.verts[i2]
        if _vdot(_vcross(_vsub(p1, p0), _vsub(p2, p0)), outward) < 0:
            self.tris.append((i0, i1, i2))
        else:
            self.tris.append((i0, i2, i1))

    def quad(self, p0, p1, p2, p3, uv_box=(0.0, 0.0, 1.0, 1.0), outward=None):
        if outward is None:
            outward = _vcross(_vsub(p2, p0), _vsub(p1, p0))
        u0, v0, u1, v1 = uv_box
        n = _vnorm(outward)
        i0 = self.add_v(p0, n, (u0, v0))
        i1 = self.add_v(p1, n, (u1, v0))
        i2 = self.add_v(p2, n, (u1, v1))
        i3 = self.add_v(p3, n, (u0, v1))
        self.add_tri(i0, i1, i2, n)
        self.add_tri(i0, i2, i3, n)

    def box(self, x0, y0, z0, x1, y1, z1, uv_box=(0.0, 0.0, 1.0, 1.0)):
        self.quad((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), uv_box, (1, 0, 0))
        self.quad((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), uv_box, (-1, 0, 0))
        self.quad((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), uv_box, (0, 1, 0))
        self.quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), uv_box, (0, -1, 0))
        self.quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), uv_box, (0, 0, 1))
        self.quad((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0), uv_box, (0, 0, -1))

    def to_surface(self, frames=None):
        if frames is None:
            frames = [(list(self.verts), list(self.norms))]
        return dict(
            name=self.name,
            shader=self.shader,
            tris=self.tris,
            st=self.st,
            frames=frames,
        )


def write_md3_and_skin(out_dir: Path, stem: str, surfs: list[MeshSurf], frames_per_surf=None):
    md3_surfs = []
    skin_lines = []
    for idx, s in enumerate(surfs):
        fr = frames_per_surf[idx] if frames_per_surf is not None else None
        md3_surfs.append(s.to_surface(fr))
        skin_lines.append(f"{s.name},{s.shader}")
    model = dict(name=stem, surfaces=md3_surfs)
    md3_path = out_dir / f"{stem}.md3"
    md3lib.write(str(md3_path), model)
    skin_path = out_dir / f"{stem}.md3_0.skin"
    skin_path.write_text("\n".join(skin_lines) + "\n", encoding="ascii", newline="\n")


def transform_verts_norms(verts, norms, pos=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), scale=1.0):
    rx, ry, rz = rot
    ov = []
    on = []
    for p, n in zip(verts, norms):
        q = (p[0] * scale, p[1] * scale, p[2] * scale)
        q = rot_z(rot_y(rot_x(q, rx), ry), rz)
        ov.append((q[0] + pos[0], q[1] + pos[1], q[2] + pos[2]))
        nq = rot_z(rot_y(rot_x(n, rx), ry), rz)
        on.append(_vnorm(nq))
    return ov, on


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------
def build_textures(tex_dir: Path) -> None:
    tex_dir.mkdir(parents=True, exist_ok=True)

    # 1. Watermelon Four Loko wrap texture (512x512) from uploaded product photo
    src_img = Image.open(ASSETS_DIR / "four_loko_watermelon.jpg").convert("RGB")
    w_src, h_src = src_img.size  # 500x500
    # Crop just the printed cylindrical body (exclude top/bottom silver rims & white background)
    # In the 500x500 photo, the can spans roughly x=[178..322], y=[45..452].
    body_crop = src_img.crop((188, 52, 312, 444))
    body_crop = ImageEnhance.Color(body_crop).enhance(1.18)
    body_crop = ImageEnhance.Contrast(body_crop).enhance(1.10)
    # Resize one front/back wrap panel to 256x512 and tile twice around 360 deg (512x512)
    # Mirror-stitch slightly at the seam edge for seamless cylindrical wrap
    panel = body_crop.resize((256, 512), Image.Resampling.LANCZOS)
    label = Image.new("RGB", (512, 512))
    label.paste(panel, (0, 0))
    label.paste(panel, (256, 0))
    # Subtle cylindrical shading blend along seam columns
    arr = np.asarray(label, dtype=np.float32)
    # Darken slightly for Zircon HDR/overbright (0.82x) while keeping neon watermelon punch
    arr = np.clip(arr * 0.86, 0, 255).astype(np.uint8)
    Image.fromarray(arr, "RGB").save(tex_dir / "can_label.png", optimize=True)

    # 2. Brushed aluminum + dark open mouth + pull tab atlas (256x256)
    # Left half (u=0..0.5): brushed silver lid & rims; top-right (u=0.5..1, v=0..0.5): dark scored opening;
    # bottom-right (u=0.5..1, v=0.5..1): bright anodized green/silver pull tab
    rng = np.random.default_rng(4242)
    m_arr = np.zeros((256, 256, 3), dtype=np.float32)
    # brushed horizontal streaks (0.55x overbright safe)
    streaks = rng.normal(0.0, 10.0, (256, 1))
    base_silver = 122.0 + streaks + rng.normal(0.0, 4.0, (256, 256))
    m_arr[:, :128, :] = base_silver[:, :128, None]
    # subtle radial highlight band on silver
    yy, xx = np.mgrid[0:256, 0:128]
    dist = np.sqrt((xx - 64) ** 2 + (yy - 128) ** 2) / 64.0
    m_arr[:, :128, :] += (1.0 - np.clip(dist, 0, 1))[:, :, None] * 18.0
    # dark opening mouth
    m_arr[:128, 128:, :] = 22.0 + rng.normal(0.0, 2.0, (128, 128, 1))
    # bright silver/lime pull tab
    m_arr[128:, 128:, 0] = 170.0
    m_arr[128:, 128:, 1] = 205.0
    m_arr[128:, 128:, 2] = 175.0
    m_arr = np.clip(m_arr, 0, 255).astype(np.uint8)
    Image.fromarray(m_arr, "RGB").save(tex_dir / "can_metal.png", optimize=True)

    # 3. First-person hands/sleeves atlas (256x256):
    # u=0..0.5: tactical olive/charcoal Quake sleeve; u=0.5..1, v=0..0.5: fingerless dark glove;
    # u=0.5..1, v=0.5..1: warm skin tone for fingers/knuckles
    h_arr = np.zeros((256, 256, 3), dtype=np.float32)
    noise = rng.normal(0.0, 6.0, (256, 256))
    # olive-brown sleeve
    h_arr[:, :128, 0] = 58 + noise[:, :128]
    h_arr[:, :128, 1] = 64 + noise[:, :128]
    h_arr[:, :128, 2] = 46 + noise[:, :128]
    # dark leather glove
    h_arr[:128, 128:, 0] = 36 + noise[:128, 128:]
    h_arr[:128, 128:, 1] = 34 + noise[:128, 128:]
    h_arr[:128, 128:, 2] = 36 + noise[:128, 128:]
    # warm skin fingers
    h_arr[128:, 128:, 0] = 188 + noise[128:, 128:] * 0.6
    h_arr[128:, 128:, 1] = 138 + noise[128:, 128:] * 0.5
    h_arr[128:, 128:, 2] = 108 + noise[128:, 128:] * 0.4
    h_arr = np.clip(h_arr, 0, 255).astype(np.uint8)
    Image.fromarray(h_arr, "RGB").save(tex_dir / "hands.png", optimize=True)

    # 4. Hospital bedpan brushed stainless steel texture (256x256)
    bp = Image.new("RGB", (256, 256), (176, 186, 194))
    bp_arr = np.asarray(bp, dtype=np.float32) + rng.normal(0.0, 5.0, (256, 1, 1))
    bp = Image.fromarray(np.clip(bp_arr, 0, 255).astype(np.uint8), "RGB")
    drw = ImageDraw.Draw(bp)
    # Red hospital cross badge on bottom/side
    drw.rectangle((188, 188, 236, 236), fill=(228, 234, 240), outline=(80, 95, 110), width=2)
    drw.rectangle((206, 196, 218, 228), fill=(195, 28, 36))
    drw.rectangle((196, 206, 228, 218), fill=(195, 28, 36))
    bp.save(tex_dir / "bedpan.png", optimize=True)


# ---------------------------------------------------------------------------
# Geometry Builders
# ---------------------------------------------------------------------------
def build_can_surfaces(
    radius: float = 5.4,
    height: float = 25.0,
    z_base: float = -12.5,
    segs: int = 24,
    crush: float = 0.0,
    tab_open_deg: float = 0.0,
) -> tuple[MeshSurf, MeshSurf]:
    """Builds a 24oz Four Loko tallboy can (label surface + aluminum/tab surface)."""
    s_lbl = MeshSurf("can_body", "progs/foreloco/can_label")
    s_mtl = MeshSurf("can_metal", "progs/foreloco/can_metal")

    # Profile stations along Z: (frac_z, radius_mult, is_label)
    z0 = z_base
    z_bot_chime = z0 + height * 0.05
    z_top_sh = z0 + height * 0.89
    z_rim = z0 + height * 0.98
    z_lid = z0 + height * 0.945

    def cyl_ring(z, r_base, ang_fn=None):
        pts = []
        for i in range(segs + 1):
            a = 2.0 * math.pi * i / segs
            r = r_base
            if crush > 0.0:
                # Subtle diagonal dent on crushed thrown cans
                dent = math.exp(-((z - (z0 + height * 0.5)) / (height * 0.25)) ** 2)
                r *= 1.0 - crush * 0.28 * dent * max(0.0, math.cos(2 * a + 0.6))
            pts.append((r * math.cos(a), r * math.sin(a), z, a))
        return pts

    def loft_band(surf: MeshSurf, ring_a, ring_b, v_a: float, v_b: float, u_scale: float = 1.0, u_off: float = 0.0):
        for i in range(segs):
            ax0, ay0, az0, aa0 = ring_a[i]
            ax1, ay1, az1, aa1 = ring_a[i + 1]
            bx0, by0, bz0, _ = ring_b[i]
            bx1, by1, bz1, _ = ring_b[i + 1]
            u0 = u_off + (i / segs) * u_scale
            u1 = u_off + ((i + 1) / segs) * u_scale
            am = 0.5 * (aa0 + aa1)
            out = (math.cos(am), math.sin(am), 0.0)
            surf.quad((ax0, ay0, az0), (ax1, ay1, az1), (bx1, by1, bz1), (bx0, by0, bz0), (u0, v_a, u1, v_b), out)

    r_bot_in = radius * 0.78
    r_top_in = radius * 0.84
    ring_bot_in = cyl_ring(z0, r_bot_in)
    ring_bot_out = cyl_ring(z_bot_chime, radius)
    ring_mid = cyl_ring(z0 + height * 0.50, radius)
    ring_sh = cyl_ring(z_top_sh, radius)
    ring_rim_out = cyl_ring(z_rim, r_top_in * 1.03)
    ring_rim_in = cyl_ring(z_rim, r_top_in * 0.94)
    ring_lid = cyl_ring(z_lid, r_top_in * 0.90)

    # Label wraps around the main cylindrical wall (v=1 at bottom, v=0 at top in Quake/MD3 st)
    loft_band(s_lbl, ring_bot_out, ring_mid, 1.0, 0.5, u_scale=1.0)
    loft_band(s_lbl, ring_mid, ring_sh, 0.5, 0.0, u_scale=1.0)

    # Aluminum bottom chime, tapered shoulder, top rim, recessed lid
    loft_band(s_mtl, ring_bot_in, ring_bot_out, 0.9, 0.7, u_scale=0.45)
    loft_band(s_mtl, ring_sh, ring_rim_out, 0.6, 0.3, u_scale=0.45)
    loft_band(s_mtl, ring_rim_out, ring_rim_in, 0.3, 0.2, u_scale=0.45)
    loft_band(s_mtl, ring_rim_in, ring_lid, 0.2, 0.1, u_scale=0.45)

    # Flat top lid disk & bottom disk
    uv_silver = (0.05, 0.1, 0.45, 0.9)
    for i in range(segs):
        a0 = 2.0 * math.pi * i / segs
        a1 = 2.0 * math.pi * (i + 1) / segs
        # Top lid
        p0 = (0.0, 0.0, z_lid)
        p1 = (r_top_in * 0.90 * math.cos(a0), r_top_in * 0.90 * math.sin(a0), z_lid)
        p2 = (r_top_in * 0.90 * math.cos(a1), r_top_in * 0.90 * math.sin(a1), z_lid)
        i0 = s_mtl.add_v(p0, (0, 0, 1), (0.25, 0.5))
        i1 = s_mtl.add_v(p1, (0, 0, 1), (0.25 + 0.18 * math.cos(a0), 0.5 + 0.35 * math.sin(a0)))
        i2 = s_mtl.add_v(p2, (0, 0, 1), (0.25 + 0.18 * math.cos(a1), 0.5 + 0.35 * math.sin(a1)))
        s_mtl.add_tri(i0, i1, i2, (0, 0, 1))
        # Bottom cap
        q0 = (0.0, 0.0, z0)
        q1 = (r_bot_in * math.cos(a0), r_bot_in * math.sin(a0), z0)
        q2 = (r_bot_in * math.cos(a1), r_bot_in * math.sin(a1), z0)
        j0 = s_mtl.add_v(q0, (0, 0, -1), (0.25, 0.5))
        j1 = s_mtl.add_v(q1, (0, 0, -1), (0.25 + 0.18 * math.cos(a0), 0.5 + 0.35 * math.sin(a0)))
        j2 = s_mtl.add_v(q2, (0, 0, -1), (0.25 + 0.18 * math.cos(a1), 0.5 + 0.35 * math.sin(a1)))
        s_mtl.add_tri(j0, j1, j2, (0, 0, -1))

    # Dark drink opening (recessed beneath lid when closed, flush on top when opened)
    z_op = z_lid + 0.01 if tab_open_deg > 5.0 else z_lid - 0.18
    s_mtl.box(1.0, -1.1, z_op, 2.8, 1.1, z_op + 0.04, (0.55, 0.05, 0.95, 0.45))

    # Pull-tab hinged near center (0, 0, z_lid + 0.35), extending toward -X (rear) or +X when flipped
    tab_pts_local = [
        (-2.2, -0.85, 0.0),
        (0.9, -0.85, 0.0),
        (0.9, 0.85, 0.0),
        (-2.2, 0.85, 0.0),
        (-2.2, -0.85, 0.25),
        (0.9, -0.85, 0.25),
        (0.9, 0.85, 0.25),
        (-2.2, 0.85, 0.25),
    ]
    # Rotate around Y at hinge (0,0) so positive tab_open_deg lifts the rear of the tab upward
    tp = [rot_y(p, -tab_open_deg) for p in tab_pts_local]
    tp = [(p[0] + 0.4, p[1], p[2] + z_lid + 0.28) for p in tp]
    uv_tab = (0.55, 0.55, 0.95, 0.95)
    # Top & bottom faces of tab
    s_mtl.quad(tp[4], tp[5], tp[6], tp[7], uv_tab, rot_y((0, 0, 1), -tab_open_deg))
    s_mtl.quad(tp[3], tp[2], tp[1], tp[0], uv_tab, rot_y((0, 0, -1), -tab_open_deg))
    s_mtl.quad(tp[0], tp[1], tp[5], tp[4], uv_tab, (0, -1, 0))
    s_mtl.quad(tp[2], tp[3], tp[7], tp[6], uv_tab, (0, 1, 0))
    s_mtl.quad(tp[1], tp[2], tp[6], tp[5], uv_tab, rot_y((1, 0, 0), -tab_open_deg))
    s_mtl.quad(tp[3], tp[0], tp[4], tp[7], uv_tab, rot_y((-1, 0, 0), -tab_open_deg))

    return s_lbl, s_mtl


def build_arm_mesh(is_left: bool) -> MeshSurf:
    """Builds an articulated forearm + fingerless glove + thumb + fingers in local hand origin (palm at 0,0,0)."""
    s = MeshSurf("left_hand" if is_left else "right_hand", "progs/foreloco/hands")
    uv_sleeve = (0.05, 0.05, 0.45, 0.95)
    uv_glove = (0.55, 0.05, 0.95, 0.45)
    uv_skin = (0.55, 0.55, 0.95, 0.95)
    sgn = 1.0 if is_left else -1.0

    # Forearm running back along -X from wrist (-2.6) to elbow (-14.5)
    s.box(-14.5, -2.1, -2.0, -2.6, 2.1, 2.0, uv_sleeve)
    # Palm / fingerless glove
    s.box(-2.8, -1.7, -1.7, 1.4, 1.7, 1.7, uv_glove)
    # Curled fingers wrapping forward/inward toward the can
    for fi, fy in enumerate((-1.2, -0.4, 0.4, 1.2)):
        # Proximal finger segment
        s.box(1.2, fy - 0.34, -1.1, 3.0, fy + 0.34, 0.1, uv_skin)
        # Curled tip inward toward palm center
        s.box(2.5, fy - 0.32, 0.0, 3.3, fy + 0.32, 1.35, uv_skin)
    # Thumb protruding on inner side
    s.box(0.2, sgn * -1.4 - 0.45, 0.6, 2.2, sgn * -1.4 + 0.45, 1.65, uv_skin)
    return s


def build_viewmodel_foreloco(progs_dir: Path) -> None:
    """Builds 40-frame first-person viewmodel: pick up -> crack tab -> chug -> party finish."""
    # Base meshes in local coords
    can_closed_lbl, can_closed_mtl = build_can_surfaces(radius=2.2, height=10.0, z_base=-5.0, segs=20, tab_open_deg=0.0)
    can_open_lbl, can_open_mtl = build_can_surfaces(radius=2.2, height=10.0, z_base=-5.0, segs=20, tab_open_deg=72.0)
    rh_base = build_arm_mesh(is_left=False)
    lh_base = build_arm_mesh(is_left=True)

    # Sanity check vertex/tri topology matches between closed & open can
    assert len(can_closed_lbl.verts) == len(can_open_lbl.verts)
    assert len(can_closed_mtl.verts) == len(can_open_mtl.verts)

    nframes = 40
    frames_lbl = []
    frames_mtl = []
    frames_rh = []
    frames_lh = []

    def lerp(a, b, t):
        return a + (b - a) * t

    def smooth(t):
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    for f in range(nframes):
        # 0..9: pickup rise into view
        # 10..19: left hand reaches across, snaps pull tab open at f=14
        # 20..35: tilt can up to mouth & 4 chug pulses
        # 36..39: drop/pump ready for Vegas blackout
        if f <= 9:
            t = smooth(f / 9.0)
            can_pos = (lerp(13.5, 15.8, t), lerp(-9.0, -3.2, t), lerp(-16.0, -4.2, t))
            can_rot = (lerp(18.0, 6.0, t), lerp(15.0, -8.0, t), lerp(120.0, 175.0, t))
            lh_pos = (lerp(9.0, 14.5, t), lerp(12.0, 5.5, t), lerp(-18.0, -5.5, t))
            lh_rot = (10.0, -12.0, lerp(-35.0, -25.0, t))
            opened = False
        elif f <= 19:
            t = smooth((f - 10) / 9.0)
            can_pos = (15.8, -3.2, -4.2 + 0.35 * math.sin(t * math.pi))
            can_rot = (6.0, -8.0, 175.0)
            # Left hand swoops over top of can to pop the tab at f=14..15
            if f <= 14:
                u = smooth((f - 10) / 4.0)
                lh_pos = (lerp(14.5, 15.4, u), lerp(5.5, -1.6, u), lerp(-5.5, 1.4, u))
                lh_rot = (lerp(10.0, -25.0, u), lerp(-12.0, 22.0, u), lerp(-25.0, -68.0, u))
            else:
                u = smooth((f - 14) / 5.0)
                kick = math.sin(u * math.pi) * 1.4
                lh_pos = (lerp(15.4, 13.5, u), lerp(-1.6, 7.5, u), lerp(1.4 + kick, -6.5, u))
                lh_rot = (lerp(-25.0, 15.0, u), lerp(22.0, -10.0, u), lerp(-68.0, -20.0, u))
            opened = f >= 14
        elif f <= 35:
            opened = True
            u = (f - 20) / 15.0
            if f <= 23:
                up = smooth((f - 20) / 3.0)
            elif f >= 33:
                up = 1.0 - smooth((f - 33) / 2.0) * 0.45
            else:
                up = 1.0
            gulp_wave = math.sin((f - 22) * 1.55) if 22 <= f <= 33 else 0.0
            can_pos = (
                lerp(15.8, 12.6, up) + gulp_wave * 0.35,
                lerp(-3.2, -1.6, up),
                lerp(-4.2, -0.4, up) + gulp_wave * 0.65,
            )
            # Tilt back toward player's face while keeping the Watermelon label & lid clearly visible
            can_rot = (
                lerp(6.0, 12.0, up),
                lerp(-8.0, -44.0, up) - gulp_wave * 7.5,
                lerp(175.0, 198.0, up),
            )
            lh_pos = (13.5, 7.5, -6.5 + gulp_wave * 0.6)
            lh_rot = (15.0, -10.0, -20.0)
        else:
            opened = True
            t = smooth((f - 36) / 3.0)
            can_pos = (lerp(12.5, 16.5, t), lerp(-2.0, -7.5, t), lerp(-1.8, -14.0, t))
            can_rot = (0.0, lerp(-35.0, 22.0, t), 185.0)
            lh_pos = (lerp(13.5, 15.5, t), lerp(7.5, 4.0, t), lerp(-6.5, -2.0, t))
            lh_rot = (-10.0, -25.0, -15.0)

        # Right hand always grips around lower-mid body of the can
        # Compute right hand offset relative to can's tilted center
        grip_local = (-1.6, 0.4, -1.2)
        grip_rot = rot_z(rot_y(rot_x(grip_local, can_rot[0]), can_rot[1]), can_rot[2])
        rh_pos = _vadd(can_pos, grip_rot)
        rh_rot = (can_rot[0] * 0.5, can_rot[1] * 0.65, 55.0)

        src_lbl = can_open_lbl if opened else can_closed_lbl
        src_mtl = can_open_mtl if opened else can_closed_mtl
        frames_lbl.append(transform_verts_norms(src_lbl.verts, src_lbl.norms, can_pos, can_rot))
        frames_mtl.append(transform_verts_norms(src_mtl.verts, src_mtl.norms, can_pos, can_rot))
        frames_rh.append(transform_verts_norms(rh_base.verts, rh_base.norms, rh_pos, rh_rot))
        frames_lh.append(transform_verts_norms(lh_base.verts, lh_base.norms, lh_pos, lh_rot))

    write_md3_and_skin(
        progs_dir,
        "v_foreloco",
        [can_closed_lbl, can_closed_mtl, rh_base, lh_base],
        [frames_lbl, frames_mtl, frames_rh, frames_lh],
    )


def build_bedpan_model(progs_dir: Path) -> None:
    """Builds a shiny stainless-steel hospital bedpan projectile (~18u x 14u x 6u)."""
    s = MeshSurf("bedpan", "progs/foreloco/bedpan")
    uv_steel = (0.05, 0.05, 0.65, 0.95)
    uv_badge = (0.70, 0.70, 0.95, 0.95)

    segs = 20
    # Outer elliptical bowl wall + flat lip + inner concave basin + rear handle
    outer_bot, outer_top, lip_in, inner_bot = [], [], [], []
    for i in range(segs + 1):
        a = 2.0 * math.pi * i / segs
        ca, sa = math.cos(a), math.sin(a)
        outer_bot.append((ca * 6.8, sa * 5.2, -2.5, a))
        outer_top.append((ca * 8.4, sa * 6.4, 2.2, a))
        lip_in.append((ca * 6.6, sa * 5.0, 2.3, a))
        inner_bot.append((ca * 5.2, sa * 3.8, -1.6, a))

    def loft(ra, rb, inward=False):
        for i in range(segs):
            ax0, ay0, az0, aa0 = ra[i]
            ax1, ay1, az1, aa1 = ra[i + 1]
            bx0, by0, bz0, _ = rb[i]
            bx1, by1, bz1, _ = rb[i + 1]
            am = 0.5 * (aa0 + aa1)
            out = (-math.cos(am), -math.sin(am), 0.3) if inward else (math.cos(am), math.sin(am), 0.0)
            u0, u1 = 0.05 + 0.55 * (i / segs), 0.05 + 0.55 * ((i + 1) / segs)
            s.quad((ax0, ay0, az0), (ax1, ay1, az1), (bx1, by1, bz1), (bx0, by0, bz0), (u0, 0.1, u1, 0.9), out)

    loft(outer_bot, outer_top, inward=False)
    loft(outer_top, lip_in, inward=False)
    loft(lip_in, inner_bot, inward=True)

    # Bottom and inner floor disks
    for i in range(segs):
        a0 = 2.0 * math.pi * i / segs
        a1 = 2.0 * math.pi * (i + 1) / segs
        # Outer underside
        p0 = (0.0, 0.0, -2.5)
        p1 = outer_bot[i][:3]
        p2 = outer_bot[i + 1][:3]
        j0, j1, j2 = s.add_v(p0, (0, 0, -1), (0.82, 0.82)), s.add_v(p1, (0, 0, -1), (0.72, 0.72)), s.add_v(p2, (0, 0, -1), (0.92, 0.72))
        s.add_tri(j0, j1, j2, (0, 0, -1))
        # Inner floor
        q0 = (0.0, 0.0, -1.6)
        q1 = inner_bot[i][:3]
        q2 = inner_bot[i + 1][:3]
        k0, k1, k2 = s.add_v(q0, (0, 0, 1), (0.3, 0.5)), s.add_v(q1, (0, 0, 1), (0.2, 0.4)), s.add_v(q2, (0, 0, 1), (0.4, 0.6))
        s.add_tri(k0, k1, k2, (0, 0, 1))

    # Rear handle sticking out -X
    s.box(-12.8, -1.6, 1.3, -7.8, 1.6, 2.3, uv_steel)
    # Red cross badge plate on front lip
    s.box(7.4, -1.6, -0.8, 8.6, 1.6, 1.6, uv_badge)

    write_md3_and_skin(progs_dir, "foreloco_bedpan", [s])


# ---------------------------------------------------------------------------
# Shader
# ---------------------------------------------------------------------------
SHADER_TEXT = """// Generated by source/mm_tools/foreloco/build_foreloco_pk3.py

progs/foreloco/can_label
{
\t{
\t\tmap progs/foreloco/can_label
\t\trgbGen lightingDiffuse
\t}
\t{
\t\tmap progs/foreloco/can_label
\t\tblendfunc add
\t\trgbGen wave sin 0.14 0.14 0 1.4
\t}
}

progs/foreloco/can_metal
{
\t{
\t\tmap progs/foreloco/can_metal
\t\trgbGen lightingDiffuse
\t}
}

progs/foreloco/hands
{
\t{
\t\tmap progs/foreloco/hands
\t\trgbGen lightingDiffuse
\t}
}

progs/foreloco/bedpan
{
\t{
\t\tmap progs/foreloco/bedpan
\t\trgbGen lightingDiffuse
\t}
}
"""


# ---------------------------------------------------------------------------
# Audio Synthesis
# ---------------------------------------------------------------------------
def _write_wav(path: Path, samples: np.ndarray, sr: int = SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = float(np.max(np.abs(samples))) if len(samples) else 1.0
    if peak > 0.96:
        samples = samples * (0.94 / peak)
    pcm = np.clip(samples * 32767.0, -32767.0, 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def build_sounds(snd_dir: Path) -> None:
    snd_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(1337)

    # 1. can_open.wav: crisp aluminum pull-tab snap + pressurized fizz
    dur = 0.78
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n, dtype=np.float32)
    # Tab lift click at 0.05s + seal pop at 0.14s
    for tc, f0, f1, amp in [(0.05, 1900, 3200, 0.55), (0.14, 1100, 4200, 0.85)]:
        i0 = int(tc * SR)
        m = min(n - i0, int(0.055 * SR))
        tt = np.arange(m) / SR
        env = np.exp(-tt * 75.0)
        sig[i0:i0 + m] += amp * env * (
            0.6 * np.sin(2 * math.pi * f0 * tt) + 0.4 * np.sin(2 * math.pi * f1 * tt)
        )
    # Pressurized CO2 fizz from 0.14s .. 0.72s (high-passed white noise)
    noise = rng.normal(0.0, 1.0, n).astype(np.float32)
    hp = np.concatenate([[0.0], np.diff(noise)])
    fizz_env = np.where(t >= 0.14, np.exp(-(t - 0.14) * 5.2), 0.0)
    sig += 0.38 * hp * fizz_env
    _write_wav(snd_dir / "can_open.wav", sig)

    # 2. drink_gulp.wav: 4 juicy glug-glug swallows + comical satisfied burp
    dur = 1.90
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n, dtype=np.float32)
    for k, tg in enumerate([0.08, 0.40, 0.72, 1.04]):
        i0 = int(tg * SR)
        m = min(n - i0, int(0.24 * SR))
        tt = np.arange(m) / SR
        # Liquid glug: rising pitch sweep 150 -> 460 Hz + bubbly harmonic
        freq = 155.0 + 310.0 * (tt / 0.24) ** 0.7 + k * 14.0
        phase = 2 * math.pi * np.cumsum(freq) / SR
        env = np.sin(math.pi * tt / 0.24) ** 0.8 * np.exp(-tt * 5.0)
        sig[i0:i0 + m] += 0.75 * env * (np.sin(phase) + 0.45 * np.sin(2.1 * phase))
    # Satisfied burp at 1.38s
    i0 = int(1.38 * SR)
    m = n - i0
    tt = np.arange(m) / SR
    f_burp = 92.0 - 24.0 * (tt / (m / SR)) + 12.0 * np.sin(2 * math.pi * 22.0 * tt)
    ph = 2 * math.pi * np.cumsum(f_burp) / SR
    b_env = np.sin(math.pi * np.minimum(1.0, tt / 0.45)) * np.exp(-tt * 3.8)
    raw_burp = np.tanh(2.4 * (np.sin(ph) + 0.6 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph)))
    sig[i0:] += 0.65 * b_env * raw_burp
    _write_wav(snd_dir / "drink_gulp.wav", sig)

    # 3. vegas_baby.wav from pre-generated speech asset
    vb_src = ASSETS_DIR / "vegas_baby.wav"
    assert vb_src.is_file(), f"Missing {vb_src}"
    (snd_dir / "vegas_baby.wav").write_bytes(vb_src.read_bytes())

    # 4. party_loop.wav: 140 BPM 4-bar seamless Vegas Eurodance/Rave loop (~6.857s)
    bpm = 140.0
    beat = 60.0 / bpm
    total_beats = 16
    dur = total_beats * beat
    n = int(round(dur * SR))
    t = np.arange(n) / SR
    mix = np.zeros(n, dtype=np.float32)

    # Kick drum on every beat (0..15) + offbeat pumping bassline
    bass_notes = [110.0, 110.0, 130.81, 146.83, 110.0, 110.0, 164.81, 146.83] * 2
    for b in range(total_beats):
        tb = b * beat
        i0 = int(round(tb * SR))
        # Punchy club kick
        km = min(n - i0, int(0.18 * SR))
        kt = np.arange(km) / SR
        kf = 52.0 + 130.0 * np.exp(-kt * 32.0)
        kph = 2 * math.pi * np.cumsum(kf) / SR
        kick = np.tanh(1.6 * np.sin(kph)) * np.exp(-kt * 13.0)
        mix[i0:i0 + km] += 0.68 * kick

        # Offbeat pumping acid/euro bass at b + 0.5 beat
        ib = int(round((tb + 0.5 * beat) * SR))
        bm = min(n - ib, int(0.20 * SR))
        bt = np.arange(bm) / SR
        bf = bass_notes[b]
        bph = 2 * math.pi * bf * bt
        saw = 2.0 * ((bf * bt) % 1.0) - 1.0
        bass = 0.65 * np.sin(bph) + 0.35 * saw
        benv = np.sin(math.pi * np.minimum(1.0, bt / 0.18)) * np.exp(-bt * 6.0)
        mix[ib:ib + bm] += 0.42 * bass * benv

        # Snare/Clap on beats 1, 3, 5, 7...
        if b % 2 == 1:
            cm = min(n - i0, int(0.14 * SR))
            ct = np.arange(cm) / SR
            cnoise = rng.normal(0.0, 1.0, cm).astype(np.float32)
            mix[i0:i0 + cm] += 0.32 * cnoise * np.exp(-ct * 22.0)

        # Crisp offbeat hi-hat
        hm = min(n - ib, int(0.06 * SR))
        ht = np.arange(hm) / SR
        hnoise = np.diff(rng.normal(0.0, 1.0, hm + 1).astype(np.float32))
        mix[ib:ib + hm] += 0.22 * hnoise * np.exp(-ht * 55.0)

    # Euphoric rave supersaw arpeggio on 16th notes
    arp_hz = [
        440.0, 523.25, 659.25, 880.0, 659.25, 523.25, 440.0, 659.25,
        392.0, 493.88, 587.33, 783.99, 587.33, 493.88, 440.0, 523.25,
    ]
    step = beat * 0.25
    steps = total_beats * 4
    for s_idx in range(steps):
        i0 = int(round(s_idx * step * SR))
        sm = min(n - i0, int(step * 0.92 * SR))
        st = np.arange(sm) / SR
        f = arp_hz[s_idx % len(arp_hz)]
        # Detuned dual-saw lead
        s1 = 2.0 * ((f * 0.996 * st) % 1.0) - 1.0
        s2 = 2.0 * ((f * 1.004 * st) % 1.0) - 1.0
        senv = np.minimum(1.0, st / 0.008) * np.exp(-st * 9.0)
        mix[i0:i0 + sm] += 0.16 * (s1 + s2) * senv

    # Party airhorn stabs on beat 0 and beat 8
    for b_horn in (0, 8):
        i0 = int(round(b_horn * beat * SR))
        hm = min(n - i0, int(0.45 * SR))
        ht = np.arange(hm) / SR
        # Brass/airhorn chord (A4 + C#5 + E5)
        horn = np.zeros(hm, dtype=np.float32)
        for fh in (440.0, 554.37, 659.25):
            horn += np.tanh(2.2 * (2.0 * ((fh * ht) % 1.0) - 1.0))
        henv = np.minimum(1.0, ht / 0.015) * np.exp(-ht * 4.5)
        mix[i0:i0 + hm] += 0.14 * horn * henv

    # Soft master limiter + short edge crossfade for clickless loop
    mix = np.tanh(mix * 1.25)
    fade = int(0.015 * SR)
    mix[:fade] *= np.linspace(0.0, 1.0, fade, dtype=np.float32)
    mix[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
    _write_wav(snd_dir / "party_loop.wav", mix)

    # 5. bed_horn.wav: Hospital ECG triple-beep + cheeky airhorn blast
    dur = 0.72
    n = int(dur * SR)
    sig = np.zeros(n, dtype=np.float32)
    for ts, fb, d_b in [(0.02, 1046.5, 0.10), (0.16, 1046.5, 0.10), (0.30, 1567.98, 0.34)]:
        i0 = int(ts * SR)
        m = min(n - i0, int(d_b * SR))
        tt = np.arange(m) / SR
        env = np.minimum(1.0, tt / 0.006) * np.exp(-tt * (4.0 if d_b > 0.2 else 8.0))
        sig[i0:i0 + m] += 0.55 * env * np.sin(2 * math.pi * fb * tt)
        if d_b > 0.2:
            # Layer goofy party horn chord on the long beep
            h = sum(np.tanh(2.0 * np.sin(2 * math.pi * f * tt)) for f in (392.0, 493.88, 587.33))
            sig[i0:i0 + m] += 0.18 * env * h
    _write_wav(snd_dir / "bed_horn.wav", sig)

    # 6. boing_hit.wav: Cartoon spring-boing + metallic gurney crash
    dur = 0.65
    n = int(dur * SR)
    tt = np.arange(n) / SR
    # Wobbling spring sweep 170 -> 580 Hz
    f_boing = 170.0 + 410.0 * (1.0 - np.exp(-tt * 7.5)) + 65.0 * np.sin(2 * math.pi * 19.0 * tt) * np.exp(-tt * 3.0)
    ph = 2 * math.pi * np.cumsum(f_boing) / SR
    boing = np.sin(ph) + 0.35 * np.sin(2.0 * ph)
    # Initial metallic gurney clatter
    clang_env = np.exp(-tt * 22.0)
    clang = sum(np.sin(2 * math.pi * fc * tt) for fc in (320.0, 512.0, 885.0, 1340.0)) * 0.25
    sig = 0.72 * boing * np.exp(-tt * 4.2) + clang * clang_env
    _write_wav(snd_dir / "boing_hit.wav", sig)

    # 7. bed_jump.wav: Springy mattress bounce + upward whoosh
    dur = 0.44
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f_j = 190.0 + 480.0 * (tt / dur) ** 0.75
    ph = 2 * math.pi * np.cumsum(f_j) / SR
    whoosh = rng.normal(0.0, 1.0, n).astype(np.float32) * 0.18 * np.sin(math.pi * tt / dur)
    sig = 0.75 * np.sin(ph) * np.exp(-tt * 6.5) + whoosh
    _write_wav(snd_dir / "bed_jump.wav", sig)

    # 8. bed_boost.wav: Screaming turbo whine + caster rattle
    dur = 0.65
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f_w = 240.0 + 520.0 * (1.0 - np.exp(-tt * 6.0))
    ph = 2 * math.pi * np.cumsum(f_w) / SR
    rattle = np.sin(2 * math.pi * 38.0 * tt) * rng.normal(0.0, 0.25, n).astype(np.float32)
    sig = (0.55 * np.tanh(1.8 * np.sin(ph)) + rattle) * np.sin(math.pi * tt / dur) ** 0.4
    _write_wav(snd_dir / "bed_boost.wav", sig)


# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------
def build_pk3(out_pk3: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        progs_dir = stage / "progs"
        tex_dir = progs_dir / "foreloco"
        scripts_dir = stage / "scripts"
        snd_dir = stage / "sound" / "foreloco"
        progs_dir.mkdir(parents=True, exist_ok=True)
        scripts_dir.mkdir(parents=True, exist_ok=True)

        build_textures(tex_dir)

        # World pickup can (~26u tall, floating centered at z=0)
        can_lbl, can_mtl = build_can_surfaces(radius=5.4, height=26.0, z_base=-13.0, segs=24, tab_open_deg=0.0)
        write_md3_and_skin(progs_dir, "foreloco_can", [can_lbl, can_mtl])

        # Thrown spinning empty can projectile (~14u tall, slightly dented, open tab)
        p_lbl, p_mtl = build_can_surfaces(radius=2.9, height=14.0, z_base=-7.0, segs=18, crush=0.55, tab_open_deg=70.0)
        write_md3_and_skin(progs_dir, "foreloco_proj_can", [p_lbl, p_mtl])

        # Flying bedpan projectile
        build_bedpan_model(progs_dir)

        # 1st-person 40-frame pickup/open/drink viewmodel (kept for precache fallback)
        build_viewmodel_foreloco(progs_dir)

        # 2D funny viewmodel sprites + liquid pour / vision smear overlays (CSQC)
        gfx_dir = stage / "gfx" / "foreloco"
        build_viewmodel_sprites(gfx_dir, ASSETS_DIR)
        build_smear_overlays(gfx_dir)

        # Shader
        (scripts_dir / "foreloco.shader").write_text(SHADER_TEXT, encoding="ascii", newline="\n")

        # Sounds
        build_sounds(snd_dir)

        # Pack deterministically
        out_pk3.parent.mkdir(parents=True, exist_ok=True)
        tmp_pk3 = out_pk3.with_suffix(".pk3.tmp")
        files = sorted(p for p in stage.rglob("*") if p.is_file())
        with zipfile.ZipFile(tmp_pk3, "w", compresslevel=6) as zf:
            for p in files:
                rel = p.relative_to(stage).as_posix()
                zi = zipfile.ZipInfo(rel, date_time=FIXED_DATE)
                zi.external_attr = FILE_ATTR
                ctype = zipfile.ZIP_STORED if p.suffix.lower() in STORE_EXTS else zipfile.ZIP_DEFLATED
                zi.compress_type = ctype
                zf.writestr(zi, p.read_bytes())
        os.replace(tmp_pk3, out_pk3)
        print(f"Wrote {out_pk3} ({out_pk3.stat().st_size:,} bytes, {len(files)} entries)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("base_pk3", nargs="?", default=str(REPO_ROOT / "bakersfield.pk3"))
    ap.add_argument("out_pk3", nargs="?", default=str(REPO_ROOT / "zz_foreloco.pk3"))
    args = ap.parse_args()
    build_pk3(Path(args.out_pk3))


if __name__ == "__main__":
    main()
