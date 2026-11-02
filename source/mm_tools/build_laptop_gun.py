"""Builds the Black AOL Hacker Laptop Gun first-person viewmodel:
  - progs/v_laptop.md3          (34 animated frames: 12 idle + 22 rapid-typing & electric discharge shoot frames)
  - progs/v_laptop_body.png     (512x512 matte-black laptop chassis, touchpad, vents, LEDs, 56k modem jack, lid badge)
  - progs/v_laptop_keys.png     (512x512 sculpted dark keycaps with crisp legends & red TrackPoint)
  - progs/v_laptop_hand.png     (256x256 shaded skin + matte-black fingerless hacker glove & cuff)
  - progs/v_laptop_scr.png      (1024x1024 4-panel Win98 AOL Dial-Up + AOL Download + 'Hacking internet lag' screen)
  - progs/v_laptop_zap.png      (128x128 electric cyan-white plasma bolt & corona texture)
  - scripts/laptop_gun.shader   (unlit screen + additive unlit electric lightning shader for DarkPlaces)

Player perspective (Quake eye at (0,0,0) looking +X, +Y left, -Y right, +Z up):
  - Held in the player's RIGHT hand (thumb clamped over the right palm-rest, fingers curled underneath the base).
  - Screen displays 'Hacking internet lag' alongside classic AOL Dial-Up & AOL File Download windows.
  - On shoot (frames 12..33): the player's LEFT hand whips up over the keyboard and furiously hammers the keys,
    switching the screen into 'HACKING INTERNET LAG' overdrive and unleashing 3D electric lightning bolts forward!

Usage:
    python3.13 source/mm_tools/build_laptop_gun.py
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")

sys.path.insert(0, HERE)
import md3lib


# --------------------------------------------------------------------------- 3D Math Helpers
def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vlen(a):
    return math.sqrt(max(0.0, vdot(a, a)))


def vnorm(a):
    l = vlen(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-9 else (0.0, 0.0, 1.0)


def vlerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def rot_x(p, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y(p, deg):
    # +deg pitches +X up toward +Z
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[2] * s, p[1], p[0] * s + p[2] * c)


def rot_z(p, deg):
    # +deg yaws +X toward +Y (screen left)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# --------------------------------------------------------------------------- Mesh Builder Container
class MeshPart:
    """Static-topology part with UV coordinates, triangle list, and per-frame transform/deformation hook."""
    def __init__(self, surf_key):
        self.surf_key = surf_key
        self.verts = []
        self.norms = []
        self.st = []
        self.tris = []

    def add_quad(self, p0, p1, p2, p3, uv0, uv1, uv2, uv3, nrm=None, two_sided=False):
        if nrm is None:
            nrm = vnorm(vcross(vsub(p1, p0), vsub(p2, p0)))
        b = len(self.verts)
        self.verts += [p0, p1, p2, p3]
        self.norms += [nrm, nrm, nrm, nrm]
        self.st += [uv0, uv1, uv2, uv3]
        self.tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        if two_sided:
            b2 = len(self.verts)
            n_rev = vmul(nrm, -1.0)
            self.verts += [p0, p1, p2, p3]
            self.norms += [n_rev, n_rev, n_rev, n_rev]
            self.st += [uv0, uv1, uv2, uv3]
            self.tris += [(b2, b2 + 2, b2 + 1), (b2, b2 + 3, b2 + 2)]

    def add_box(self, x0, x1, y0, y1, z0, z1, uv_rect=(0.02, 0.02, 0.22, 0.22), top_uv=None, front_uv=None, back_uv=None, skip_bottom=False):
        u0, v0, u1, v1 = uv_rect
        tuv = top_uv if top_uv else uv_rect
        fuv = front_uv if front_uv else uv_rect
        buv = back_uv if back_uv else uv_rect

        # +Z top (viewed from above: +X is rear/away, +Y is left, -Y is right)
        self.add_quad(
            (x1, y1, z1), (x1, y0, z1), (x0, y0, z1), (x0, y1, z1),
            (tuv[0], tuv[1]), (tuv[2], tuv[1]), (tuv[2], tuv[3]), (tuv[0], tuv[3]),
            nrm=(0.0, 0.0, 1.0),
        )
        if not skip_bottom:
            # -Z bottom
            self.add_quad(
                (x0, y1, z0), (x0, y0, z0), (x1, y0, z0), (x1, y1, z0),
                (u0, v0), (u1, v0), (u1, v1), (u0, v1),
                nrm=(0.0, 0.0, -1.0),
            )
        # -X front face (facing player!)
        self.add_quad(
            (x0, y1, z1), (x0, y0, z1), (x0, y0, z0), (x0, y1, z0),
            (fuv[0], fuv[1]), (fuv[2], fuv[1]), (fuv[2], fuv[3]), (fuv[0], fuv[3]),
            nrm=(-1.0, 0.0, 0.0),
        )
        # +X rear face (away from player)
        self.add_quad(
            (x1, y0, z1), (x1, y1, z1), (x1, y1, z0), (x1, y0, z0),
            (buv[0], buv[1]), (buv[2], buv[1]), (buv[2], buv[3]), (buv[0], buv[3]),
            nrm=(1.0, 0.0, 0.0),
        )
        # +Y left side
        self.add_quad(
            (x1, y1, z1), (x0, y1, z1), (x0, y1, z0), (x1, y1, z0),
            (u0, v0), (u1, v0), (u1, v1), (u0, v1),
            nrm=(0.0, 1.0, 0.0),
        )
        # -Y right side
        self.add_quad(
            (x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0),
            (u0, v0), (u1, v0), (u1, v1), (u0, v1),
            nrm=(0.0, -1.0, 0.0),
        )

    def add_keycap(self, x0, x1, y0, y1, z0, z1, uv_top, uv_side):
        """Trapezoidal sculpted 3D laptop keycap (5 faces, no underside)."""
        inset_x = (x1 - x0) * 0.13
        inset_y = (y1 - y0) * 0.13
        tx0, tx1 = x0 + inset_x, x1 - inset_x
        ty0, ty1 = y0 + inset_y, y1 - inset_y
        u0, v0, u1, v1 = uv_top
        su0, sv0, su1, sv1 = uv_side

        # Top legend face (+Y is left -> u0, -Y is right -> u1; +X is rear -> v0, -X is front -> v1)
        self.add_quad(
            (tx1, ty1, z1), (tx1, ty0, z1), (tx0, ty0, z1), (tx0, ty1, z1),
            (u0, v0), (u1, v0), (u1, v1), (u0, v1),
            nrm=(0.0, 0.0, 1.0),
        )
        # Front slope (-X)
        self.add_quad((tx0, ty1, z1), (tx0, ty0, z1), (x0, y0, z0), (x0, y1, z0), (su0, sv0), (su1, sv0), (su1, sv1), (su0, sv1))
        # Rear slope (+X)
        self.add_quad((tx1, ty0, z1), (tx1, ty1, z1), (x1, y1, z0), (x1, y0, z0), (su0, sv0), (su1, sv0), (su1, sv1), (su0, sv1))
        # Left slope (+Y)
        self.add_quad((tx1, ty1, z1), (tx0, ty1, z1), (x0, y1, z0), (x1, y1, z0), (su0, sv0), (su1, sv0), (su1, sv1), (su0, sv1))
        # Right slope (-Y)
        self.add_quad((tx0, ty0, z1), (tx1, ty0, z1), (x1, y0, z0), (x0, y0, z0), (su0, sv0), (su1, sv0), (su1, sv1), (su0, sv1))


def frame_basis(t):
    t = vnorm(t)
    ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.88 else (1.0, 0.0, 0.0)
    u = vnorm(vcross(t, ref))
    v = vcross(t, u)
    return t, u, v


def build_tube_into(mesh, points, radii, uv_rect, sides=8, cap_start=True, cap_end=True):
    """Sweeps a smooth shaded tube along `points` with elliptical/circular radii into `mesh`."""
    n = len(points)
    tans = []
    for i in range(n):
        p_prev = points[max(0, i - 1)]
        p_next = points[min(n - 1, i + 1)]
        tans.append(vnorm(vsub(p_next, p_prev)))

    u0, v0, u1, v1 = uv_rect
    rings = []
    # Parallel-transport frame so fingers/arms never twist!
    t0, bu, bv = frame_basis(tans[0])
    for i in range(n):
        ti = tans[i]
        # Project previous bu onto plane perpendicular to ti
        bu_proj = vsub(bu, vmul(ti, vdot(bu, ti)))
        if vlen(bu_proj) < 1e-5:
            _, bu, bv = frame_basis(ti)
        else:
            bu = vnorm(bu_proj)
            bv = vcross(ti, bu)

        r_val = radii[i]
        rx, ry = r_val if isinstance(r_val, tuple) else (r_val, r_val)
        ring_start = len(mesh.verts)
        rings.append(ring_start)
        v_coord = v0 + (v1 - v0) * (i / max(1, n - 1))
        for k in range(sides):
            ang = 2.0 * math.pi * k / sides
            ca, sa = math.cos(ang), math.sin(ang)
            off = vadd(vmul(bu, ca * rx), vmul(bv, sa * ry))
            nrm = vnorm(vadd(vmul(bu, ca / max(rx, 1e-4)), vmul(bv, sa / max(ry, 1e-4))))
            mesh.verts.append(vadd(points[i], off))
            mesh.norms.append(nrm)
            u_coord = u0 + (u1 - u0) * (k / float(sides))
            mesh.st.append((u_coord, v_coord))

    for i in range(n - 1):
        rA, rB = rings[i], rings[i + 1]
        for k in range(sides):
            k2 = (k + 1) % sides
            a, b, c, d = rA + k, rA + k2, rB + k2, rB + k
            mesh.tris += [(a, b, c), (a, c, d)]

    if cap_start:
        r0 = radii[0][0] if isinstance(radii[0], tuple) else radii[0]
        idx_c0 = len(mesh.verts)
        mesh.verts.append(vsub(points[0], vmul(tans[0], r0 * 0.55)))
        mesh.norms.append(vmul(tans[0], -1.0))
        mesh.st.append((0.5 * (u0 + u1), v0))
        for k in range(sides):
            k2 = (k + 1) % sides
            mesh.tris.append((idx_c0, rings[0] + k2, rings[0] + k))

    if cap_end:
        rn = radii[-1][0] if isinstance(radii[-1], tuple) else radii[-1]
        idx_c1 = len(mesh.verts)
        mesh.verts.append(vadd(points[-1], vmul(tans[-1], rn * 0.65)))
        mesh.norms.append(tans[-1])
        mesh.st.append((0.5 * (u0 + u1), v1))
        for k in range(sides):
            k2 = (k + 1) % sides
            mesh.tris.append((idx_c1, rings[-1] + k, rings[-1] + k2))


def build_ellipsoid_into(mesh, center, ax, ay, az, rx, ry, rz, uv_rect, segs=10, rings=6):
    u0, v0, u1, v1 = uv_rect
    base = len(mesh.verts)
    for r in range(rings + 1):
        th = math.pi * r / rings
        sth, cth = math.sin(th), math.cos(th)
        vv = v0 + (v1 - v0) * (r / float(rings))
        for s in range(segs):
            ph = 2.0 * math.pi * s / segs
            x, y, z = sth * math.cos(ph), sth * math.sin(ph), cth
            p = vadd(center, vadd(vadd(vmul(ax, x * rx), vmul(ay, y * ry)), vmul(az, z * rz)))
            nn = vnorm(vadd(vadd(vmul(ax, x / rx), vmul(ay, y / ry)), vmul(az, z / rz)))
            mesh.verts.append(p)
            mesh.norms.append(nn)
            mesh.st.append((u0 + (u1 - u0) * (s / float(segs)), vv))
    for r in range(rings):
        for s in range(segs):
            s2 = (s + 1) % segs
            a = base + r * segs + s
            b = base + r * segs + s2
            c = base + (r + 1) * segs + s2
            d = base + (r + 1) * segs + s
            mesh.tris += [(a, c, b), (a, d, c)]


# --------------------------------------------------------------------------- Font Helpers & Procedural Textures
def load_font(names, size):
    for nm in names:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def build_body_texture():
    """512x512 matte-black ThinkPad-style laptop texture atlas:
      - [0..256, 0..256]: dark anodized magnesium/ABS matte-black grain
      - [256..512, 0..256]: palm-rest deck with touchpad, click buttons, & status LEDs
      - [0..256, 256..512]: side ports (cooling louvers, yellow 56k RJ-11 modem jack, serial port)
      - [256..512, 256..512]: outer black lid backplate with cyber 'THINK-LAG 56K' & AOL triangle badge
    """
    W = H = 512
    im = Image.new("RGB", (W, H), (24, 26, 30))
    dr = ImageDraw.Draw(im)
    rng = random.Random(1999)

    # Subtle matte-black ThinkPad rubberized texture speckle across entire sheet
    px = im.load()
    for y in range(H):
        for x in range(W):
            n = rng.randint(-4, 4)
            px[x, y] = (24 + n, 26 + n, 31 + n)

    # Quadrant (256..512, 0..256): Top palm-rest & keyboard recess deck
    dr.rectangle([256, 0, 511, 255], fill=(27, 29, 34))
    # Dark recessed keyboard tray well (top 62% of deck)
    dr.rectangle([268, 12, 500, 156], fill=(14, 15, 18), outline=(42, 45, 52), width=2)
    # Power button & 3 glowing status LEDs above keyboard right
    dr.ellipse([282, 16, 294, 28], fill=(38, 42, 48), outline=(78, 84, 96))
    dr.rectangle([448, 18, 456, 24], fill=(45, 235, 95))    # Power LED (green)
    dr.rectangle([462, 18, 470, 24], fill=(255, 185, 35))   # HDD LED (amber)
    dr.rectangle([476, 18, 484, 24], fill=(55, 210, 255))   # 56k Modem LED (cyan)

    # Trackpad + dual ThinkPad-style red-accent buttons on lower palm rest
    dr.rounded_rectangle([346, 170, 422, 238], radius=5, fill=(36, 39, 46), outline=(58, 63, 74), width=2)
    dr.rectangle([348, 172, 420, 183], fill=(30, 32, 38))
    dr.line([384, 172, 384, 183], fill=(200, 42, 48), width=2)
    dr.line([350, 182, 418, 182], fill=(205, 42, 48), width=2)
    dr.rectangle([348, 226, 420, 237], fill=(28, 30, 36), outline=(54, 58, 68))
    dr.line([384, 226, 384, 237], fill=(54, 58, 68), width=2)

    # Retro 'AOL 5.0 READY / 56K V.90' palm-rest sticker on right side!
    dr.rounded_rectangle([438, 186, 492, 232], radius=4, fill=(14, 40, 96), outline=(90, 128, 175), width=1)
    f_tiny = load_font(["tahomabd.ttf", "arialbd.ttf"], 10)
    dr.text((444, 192), "AOL 5.0", fill=(185, 192, 205), font=f_tiny)
    dr.text((443, 206), "56K V.90", fill=(185, 160, 48), font=f_tiny)
    dr.text((445, 218), "TURBO", fill=(78, 175, 190), font=f_tiny)

    # Quadrant (0..256, 256..512): Side cooling vents + yellow 56k RJ-11 modem jack + serial port
    dr.rectangle([0, 256, 255, 511], fill=(20, 22, 26))
    for i in range(9):
        vx = 18 + i * 11
        dr.rectangle([vx, 286, vx + 6, 344], fill=(8, 9, 11), outline=(34, 37, 42))
    # Yellow 56k Modem RJ-11 port
    dr.rectangle([132, 286, 174, 340], fill=(210, 175, 32), outline=(45, 45, 50), width=2)
    dr.rectangle([140, 296, 166, 330], fill=(12, 14, 18))
    for p_i in range(4):
        dr.line([145 + p_i * 5, 298, 145 + p_i * 5, 312], fill=(235, 195, 65), width=2)
    # Teal DB-9 serial hacker port
    dr.rounded_rectangle([186, 294, 242, 334], radius=5, fill=(45, 115, 125), outline=(140, 150, 160), width=2)

    # Front LCD bezel strip (0..256, 380..450) with silver 'THINK-LAG 56K' label
    dr.rectangle([0, 380, 255, 450], fill=(19, 21, 25))
    f_badge = load_font(["tahomabd.ttf", "arialbd.ttf"], 14)
    dr.text((16, 396), "THINK-LAG  56K", fill=(185, 195, 210), font=f_badge)
    dr.ellipse([215, 398, 225, 408], fill=(40, 225, 95))

    # Quadrant (256..512, 256..512): Outer matte-black lid backplate with cyber AOL emblem
    dr.rectangle([256, 256, 511, 511], fill=(22, 24, 29))
    dr.rounded_rectangle([270, 270, 497, 497], radius=10, outline=(38, 42, 50), width=3)
    # Glowing blue/cyan triangle emblem on outer lid
    tri = [(384, 316), (326, 420), (442, 420)]
    dr.polygon(tri, fill=(22, 78, 168), outline=(95, 205, 255))
    f_lid = load_font(["consolab.ttf", "tahomabd.ttf"], 18)
    dr.text((314, 434), "LAG-CASTER 98", fill=(180, 215, 255), font=f_lid)

    out_p = os.path.join(PROGS, "v_laptop_body.png")
    im.save(out_p, "PNG", optimize=True)
    return out_p


def build_keys_texture():
    """512x512 crisp dark-charcoal laptop keyboard atlas + bright red TrackPoint swatch."""
    W = H = 512
    im = Image.new("RGB", (W, H), (16, 18, 22))
    dr = ImageDraw.Draw(im)

    rows_spec = [
        [("Esc", 1.1), ("F1", 1), ("F2", 1), ("F3", 1), ("F4", 1), ("F5", 1), ("F6", 1), ("F7", 1), ("F8", 1), ("F9", 1), ("F10", 1), ("F11", 1), ("Del", 1.2)],
        [("~", 0.9), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("Bksp", 1.8)],
        [("Tab", 1.4), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1), ("\\", 1.3)],
        [("Caps", 1.65), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("Enter", 2.05)],
        [("Shift", 2.1), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("Shift", 2.1)],
        [("Ctrl", 1.3), ("Fn", 1.1), ("AOL", 1.3), ("Alt", 1.1), ("SPACE", 5.2), ("Alt", 1.1), ("<", 1.0), ("v", 1.0), (">", 1.0)],
    ]

    f_key = load_font(["tahomabd.ttf", "arialbd.ttf"], 15)
    f_sm = load_font(["tahomabd.ttf", "arialbd.ttf"], 11)

    pad_x = 12
    usable_w = W - 2 * pad_x
    row_h = 62
    for ri, rkeys in enumerate(rows_spec):
        y0 = 14 + ri * (row_h + 6)
        y1 = y0 + row_h
        tot_u = sum(w for _, w in rkeys)
        cx = float(pad_x)
        for lbl, kw in rkeys:
            w_px = usable_w * (kw / tot_u)
            kx0, kx1 = int(round(cx)) + 2, int(round(cx + w_px)) - 2
            cx += w_px
            is_aol = lbl == "AOL"
            fill_c = (26, 68, 148) if is_aol else ((34, 37, 45) if len(lbl) == 1 else (28, 31, 38))
            rim_c = (95, 165, 245) if is_aol else (64, 70, 84)
            dr.rounded_rectangle([kx0, y0, kx1, y1], radius=5, fill=fill_c, outline=rim_c, width=2)
            # Subtle top keycap highlight bevel
            dr.line([kx0 + 3, y0 + 2, kx1 - 3, y0 + 2], fill=(82, 88, 104), width=1)
            if lbl != "SPACE":
                use_f = f_key if len(lbl) <= 2 else f_sm
                txt_c = (255, 235, 110) if is_aol else (228, 234, 245)
                dr.text((kx0 + 6, y0 + 8), lbl, fill=txt_c, font=use_f)
            else:
                dr.line([kx0 + 48, y1 - 12, kx1 - 48, y1 - 12], fill=(120, 132, 155), width=2)

    # Bottom strip (y = 430..511): [0..128] dark keycap side skirt, [128..256] bright red TrackPoint nib!
    dr.rectangle([0, 430, 127, 511], fill=(20, 22, 27))
    dr.rectangle([128, 430, 255, 511], fill=(215, 34, 42))
    # Knurled TrackPoint dots
    for yy in range(436, 506, 8):
        for xx in range(134, 250, 8):
            dr.ellipse([xx, yy, xx + 3, yy + 3], fill=(165, 18, 26))

    out_p = os.path.join(PROGS, "v_laptop_keys.png")
    im.save(out_p, "PNG", optimize=True)
    return out_p


def build_hand_texture():
    """256x256 texture for the right holding hand & left rapid-typing hand:
      - [0..128, 0..128]: warm natural skin tone (darkened ~0.62x for Game Brightness / DarkPlaces diffuse)
      - [128..256, 0..128]: slightly lighter fingernail / knuckle highlight skin
      - [0..128, 128..256]: matte-black fingerless tactical hacker glove leather
      - [128..256, 128..256]: dark charcoal jacket sleeve & ribbed wrist cuff
    """
    W = H = 256
    im = Image.new("RGB", (W, H), (30, 30, 34))
    dr = ImageDraw.Draw(im)
    rng = random.Random(42)

    # Skin quadrant (0..128, 0..128) - authored at ~0.62x brightness so 1.65x game overbright renders natural flesh!
    for y in range(128):
        shade = 0.92 + 0.14 * math.sin(math.pi * y / 127.0)
        for x in range(128):
            n = rng.randint(-3, 3)
            r = int(min(255, max(0, 146 * shade + n)))
            g = int(min(255, max(0, 108 * shade + n)))
            b = int(min(255, max(0, 88 * shade + n)))
            im.putpixel((x, y), (r, g, b))

    # Knuckle/fingertip warm skin (128..256, 0..128)
    for y in range(128):
        shade = 0.95 + 0.12 * math.sin(math.pi * y / 127.0)
        for x in range(128, 256):
            n = rng.randint(-3, 3)
            r = int(min(255, max(0, 158 * shade + n)))
            g = int(min(255, max(0, 118 * shade + n)))
            b = int(min(255, max(0, 98 * shade + n)))
            im.putpixel((x, y), (r, g, b))

    # Matte-black fingerless hacker glove leather (0..128, 128..256)
    for y in range(128, 256):
        for x in range(128):
            n = rng.randint(-4, 4)
            im.putpixel((x, y), (26 + n, 28 + n, 33 + n))
    dr.rectangle([6, 134, 121, 249], outline=(46, 50, 58), width=2)
    # Glove knuckle vent perforations
    for k in range(4):
        dr.ellipse([22 + k * 24, 175, 34 + k * 24, 187], fill=(16, 17, 20), outline=(48, 52, 62))

    # Ribbed dark navy-charcoal hoodie/jacket cuff (128..256, 128..256)
    for y in range(128, 256):
        rib = int(5 * math.sin(y * 0.55))
        for x in range(128, 256):
            im.putpixel((x, y), (20 + rib, 24 + rib, 32 + rib))

    out_p = os.path.join(PROGS, "v_laptop_hand.png")
    im.save(out_p, "PNG", optimize=True)
    return out_p


def draw_aol_logo(dr, cx, cy, r, color_tri=(28, 92, 188), color_man=(255, 224, 72)):
    """Draws an iconic retro AOL triangle + stylised Running Man icon centered at (cx, cy)."""
    pts = [(cx, cy - r), (cx - int(r * 0.94), cy + int(r * 0.78)), (cx + int(r * 0.94), cy + int(r * 0.78))]
    dr.polygon(pts, fill=color_tri, outline=(255, 255, 255))
    # Running man head & limbs inside triangle
    dr.ellipse([cx - 5, cy - int(r * 0.34), cx + 5, cy - int(r * 0.34) + 10], fill=color_man)
    dr.line([cx, cy - int(r * 0.34) + 10, cx - 3, cy + 8], fill=color_man, width=4)
    dr.line([cx - 11, cy - 2, cx + 10, cy - 5], fill=color_man, width=3)
    dr.line([cx - 3, cy + 8, cx - 12, cy + 19], fill=color_man, width=3)
    dr.line([cx - 3, cy + 8, cx + 10, cy + 18], fill=color_man, width=3)


def draw_win98_window(dr, x0, y0, x1, y1, title, active=True, body_fill=(198, 200, 206)):
    """Classic beveled Windows 98 / AOL 5.0 window frame with navy-blue title bar."""
    dr.rectangle([x0, y0, x1, y1], fill=body_fill)
    # 3D Win98 outer bevel
    dr.line([x0, y0, x1, y0], fill=(250, 250, 252), width=2)
    dr.line([x0, y0, x0, y1], fill=(250, 250, 252), width=2)
    dr.line([x0, y1, x1, y1], fill=(70, 72, 78), width=2)
    dr.line([x1, y0, x1, y1], fill=(70, 72, 78), width=2)
    # Gradient navy->royal blue title bar
    tb_h = 24
    for i in range(tb_h):
        t = i / float(tb_h)
        c = (int(12 + 24 * t), int(38 + 68 * t), int(128 + 75 * t)) if active else (110, 115, 125)
        dr.line([x0 + 3, y0 + 3 + i, x1 - 3, y0 + 3 + i], fill=c)
    f_tb = load_font(["tahomabd.ttf", "arialbd.ttf"], 14)
    dr.text((x0 + 9, y0 + 6), title, fill=(255, 255, 255), font=f_tb)
    # [X] close button
    bx0, by0 = x1 - 22, y0 + 6
    dr.rectangle([bx0, by0, bx0 + 16, by0 + 15], fill=(198, 200, 206), outline=(60, 60, 66))
    dr.text((bx0 + 4, by0 - 1), "x", fill=(20, 20, 24), font=f_tb)


def build_screen_texture():
    """1024x1024 lossless 4-panel LCD screen atlas (gain-calibrated for 1.65x Game Brightness):
      - Panel 0 (top-left  0..512,   0..512): Idle - 'Hacking internet lag' + AOL Dial-Up + AOL Download (48%)
      - Panel 1 (top-right 512..1024,0..512): Shoot Rapid Typing - Typing macro + AOL Dial-Up & AOL Download racing to 96%!
      - Panel 2 (bot-left  0..512, 512..1024): Shoot Alert - Giant 'Hacking internet lag' takeover banner + AOL 100%!
      - Panel 3 (bot-right 512..1024,512..1024): Shoot Electric Blast - Electrified cyan/white 'Hacking internet lag' Surge!
    """
    S = 512
    atlas = Image.new("RGB", (S * 2, S * 2), (0, 108, 114))

    f_hero = load_font(["consolab.ttf", "tahomabd.ttf", "arialbd.ttf"], 32)
    f_huge = load_font(["tahomabd.ttf", "arialbd.ttf"], 54)
    f_bolt = load_font(["tahomabd.ttf", "arialbd.ttf"], 46)
    f_aol = load_font(["tahomabd.ttf", "arialbd.ttf"], 27)
    f_med = load_font(["tahomabd.ttf", "arialbd.ttf"], 18)
    f_ui = load_font(["tahomabd.ttf", "arialbd.ttf"], 15)
    f_mono = load_font(["consolab.ttf", "courbd.ttf"], 16)
    f_sm = load_font(["tahomabd.ttf", "arialbd.ttf"], 13)

    # ---- Panel 0 (0, 0) [IDLE] & Panel 1 (512, 0) [RAPID TYPING]: Win98 AOL Dial-Up + AOL Download + Hacking internet lag ----
    for idx, (ox, oy, pct, step_no) in enumerate([
        (0, 0, 0.48, 2),
        (S, 0, 0.94, 3),
    ]):
        pan = Image.new("RGB", (S, S), (0, 112, 118))  # Classic Windows 98 teal desktop!
        dr = ImageDraw.Draw(pan)

        # 1. Top High-Contrast Hacker Console Window: "Hacking internet lag"
        draw_win98_window(dr, 10, 8, 502, 128, "C:\\AOL98\\lag_hack.exe", body_fill=(8, 14, 12))
        dr.rectangle([16, 36, 496, 122], fill=(6, 12, 10), outline=(36, 110, 52), width=1)
        if idx == 0:
            dr.text((24, 42), "Hacking internet lag", fill=(80, 255, 118), font=f_hero)
            dr.text((24, 88), "> AOL 56k v.90 hooked... ping=999ms", fill=(165, 255, 185), font=f_mono)
        else:
            dr.text((24, 42), "Hacking internet lag_", fill=(255, 245, 90), font=f_hero)
            dr.text((24, 88), "> FAST TYPING 900 WPM!! FLOODING AOL!", fill=(95, 255, 140), font=f_mono)

        # 2. Middle Classic "America Online — Dial-Up" Window
        draw_win98_window(dr, 10, 134, 502, 316, "America Online 5.0 - Dial-Up", body_fill=(206, 210, 218))
        # Crisp white inner AOL banner with bold dark navy border & AOL Running Man triangle
        dr.rectangle([20, 164, 492, 248], fill=(246, 248, 252), outline=(75, 90, 120), width=2)
        draw_aol_logo(dr, 66, 206, 32, color_tri=(18, 72, 172), color_man=(255, 220, 55))
        dr.text((112, 168), "AOL Dial-Up", fill=(10, 38, 122), font=f_aol)
        dr.text((114, 202), "Modem: 56K v.90  |  1-800-AOL-LAG", fill=(14, 18, 28), font=f_ui)
        status_line = "Step 2 of 3: Dialing America Online..." if idx == 0 else "Step 3 of 3: SCREEEECH!! OVERCLOCKING!"
        dr.text((114, 224), status_line, fill=(175, 20, 24) if idx == 1 else (16, 68, 148), font=f_ui)

        # Classic 3 AOL dial-up step boxes at bottom of AOL window
        for s_i, s_lbl in enumerate(["1. Modem Init", "2. AOL Dial", "3. Lag Armed"]):
            bx0 = 20 + s_i * 159
            bx1 = bx0 + 152
            lit = (s_i + 1) <= step_no
            dr.rectangle(
                [bx0, 255, bx1, 306],
                fill=(178, 212, 252) if lit else (192, 196, 204),
                outline=(20, 62, 148) if lit else (95, 100, 112),
                width=2,
            )
            dr.text((bx0 + 10, 271), s_lbl, fill=(8, 28, 92) if lit else (58, 62, 72), font=f_ui)

        # 3. Bottom Classic "AOL Download" Progress Window
        draw_win98_window(dr, 10, 322, 502, 476, "AOL Download - [internet_lag.exe]", body_fill=(202, 206, 214))
        dr.text((24, 352), f"AOL Download: internet_lag.exe ({int(pct * 100)}%)", fill=(10, 14, 24), font=f_med)
        rate_txt = "Speed: 2.8 KB/sec   Time left: 39 min" if idx == 0 else "Speed: 999 KB/sec!!  CHARGING COILS!!"
        dr.text((24, 378), rate_txt, fill=(165, 22, 26) if idx == 1 else (28, 34, 48), font=f_sm)
        # Sunken Win98 chunky royal-blue segmented progress bar!
        dr.rectangle([22, 402, 490, 438], fill=(246, 248, 252), outline=(52, 58, 72), width=2)
        n_blocks = int(round(pct * 22))
        for b_i in range(n_blocks):
            bx = 27 + b_i * 20
            dr.rectangle([bx, 407, bx + 16, 433], fill=(14, 48, 158))
        dr.rectangle([366, 444, 490, 469], fill=(192, 196, 204), outline=(48, 52, 62), width=2)
        dr.text((386, 448), "Sign Off", fill=(12, 14, 20), font=f_sm)

        # Win98 Start Taskbar at very bottom
        dr.rectangle([0, 482, S, S], fill=(188, 192, 200))
        dr.line([0, 482, S, 482], fill=(245, 246, 250), width=2)
        dr.rectangle([6, 486, 76, 508], fill=(188, 192, 200), outline=(45, 48, 56), width=2)
        dr.text((16, 488), "Start", fill=(10, 12, 18), font=f_ui)
        dr.text((90, 489), "AOL 5.0  |  Hacking internet lag", fill=(14, 20, 36), font=f_sm)

        atlas.paste(pan, (ox, oy))

    # ---- Panel 2 (0, 512): POST-TYPING GIANT SCREEN ALERT ("Hacking internet lag"!) ----
    pan2 = Image.new("RGB", (S, S), (6, 16, 24))
    dr2 = ImageDraw.Draw(pan2)
    for i in range(17):
        yy = 8 + i * 29
        dr2.text((10, yy), f"64 bytes from aol-dialup.net: seq={i+10} ping=9999ms LAG!", fill=(18, 92, 46), font=f_mono)

    # Compact AOL Dial-Up + AOL 100% Download bar at bottom
    draw_win98_window(dr2, 12, 336, 500, 500, "AOL Dial-Up & AOL Download - 100% COMPLETE!", body_fill=(206, 214, 228))
    draw_aol_logo(dr2, 54, 396, 27, color_tri=(18, 72, 172), color_man=(255, 220, 55))
    dr2.text((94, 368), "AOL Dial-Up:  CONNECTED @ 99,999ms LAG", fill=(168, 18, 24), font=f_ui)
    dr2.text((94, 392), "AOL Download: internet_lag.exe [100%!]", fill=(12, 38, 128), font=f_ui)
    dr2.rectangle([24, 428, 488, 462], fill=(246, 248, 252), outline=(36, 44, 62), width=2)
    for b_i in range(22):
        bx = 29 + b_i * 20
        dr2.rectangle([bx, 432, bx + 17, 458], fill=(18, 138, 225) if b_i > 15 else (14, 48, 158))
    dr2.text((28, 470), ">> KEYBOARD HACK COMPLETE -> DISCHARGING! <<", fill=(165, 18, 28), font=f_ui)

    # Giant High-Contrast Center Banner: "Hacking internet lag"
    dr2.rounded_rectangle([12, 18, 500, 320], radius=10, fill=(6, 18, 12), outline=(80, 255, 125), width=6)
    dr2.rectangle([20, 26, 492, 66], fill=(24, 138, 58))
    dr2.text((32, 34), ">>>  AOL 56K TERMINAL OVERRIDE  <<<", fill=(255, 255, 255), font=f_med)
    dr2.text((32, 82), "Hacking", fill=(92, 255, 132), font=f_huge)
    dr2.text((32, 148), "internet lag", fill=(255, 240, 75), font=f_bolt)
    dr2.text((32, 222), "> KEYBOARD TURBO: 999 WPM COMPLETE!", fill=(120, 250, 245), font=f_mono)
    dr2.text((32, 252), "> PING: 9999ms  |  VOLTAGE: CRITICAL!", fill=(255, 140, 90), font=f_mono)
    dr2.text((32, 282), "> FIRING ELECTRIC LAG BOLT [||||||||||]", fill=(115, 255, 145), font=f_mono)
    atlas.paste(pan2, (0, S))

    # ---- Panel 3 (512, 512): ELECTRIC DISCHARGE PHASE! ----
    pan3 = Image.new("RGB", (S, S), (10, 36, 108))
    dr3 = ImageDraw.Draw(pan3)
    for r_c in range(340, 20, -18):
        t = 1.0 - r_c / 340.0
        col = (int(16 + 190 * t), int(72 + 165 * t), 255)
        dr3.ellipse([256 - r_c, 245 - r_c, 256 + r_c, 245 + r_c], fill=col)

    rng_z = random.Random(777)
    for _ in range(12):
        lx, ly = 256, 245
        for _s in range(6):
            nx = lx + rng_z.randint(-90, 90)
            ny = ly + rng_z.randint(-90, 90)
            dr3.line([lx, ly, nx, ny], fill=(230, 252, 255), width=4)
            lx, ly = nx, ny

    dr3.rounded_rectangle([20, 42, 492, 468], radius=12, fill=(6, 18, 48), outline=(145, 245, 255), width=6)
    draw_aol_logo(dr3, 72, 108, 34, color_tri=(28, 128, 245), color_man=(255, 245, 110))
    dr3.text((122, 78), "AOL 56K OVERLOAD!", fill=(140, 242, 255), font=load_font(["tahomabd.ttf", "arialbd.ttf"], 28))
    dr3.text((124, 114), "AOL DOWNLOAD 100% -> ELECTRIC!", fill=(255, 232, 85), font=f_ui)

    dr3.line([38, 158, 474, 158], fill=(105, 228, 255), width=3)
    dr3.text((44, 174), "Hacking", fill=(255, 255, 255), font=f_huge)
    dr3.text((44, 242), "internet lag", fill=(115, 245, 255), font=load_font(["tahomabd.ttf", "arialbd.ttf"], 50))
    dr3.line([38, 322, 474, 322], fill=(105, 228, 255), width=3)

    dr3.rectangle([40, 344, 472, 390], fill=(215, 248, 255), outline=(75, 215, 255), width=3)
    dr3.text((60, 354), ">>>  56,000 VOLTS // YOU'VE GOT LAG!  <<<", fill=(8, 26, 82), font=f_med)
    dr3.text((74, 412), "PING: 99,999 ms   [ELECTRIC DISCHARGE]", fill=(255, 235, 95), font=f_ui)
    atlas.paste(pan3, (S, S))

    # Calibrate exposure by 0.63x + subtle 4% LCD scanline so 1.65x Game Brightness renders crisp unclipped colors!
    px = atlas.load()
    for y in range(S * 2):
        scan = 0.61 if (y % 2 == 0) else 0.64
        for x in range(S * 2):
            r, g, b = px[x, y]
            px[x, y] = (int(r * scan), int(g * scan), int(b * scan))

    out_p = os.path.join(PROGS, "v_laptop_scr.png")
    atlas.save(out_p, "PNG", optimize=True)
    return out_p


def build_zap_texture():
    """128x128 electric cyan-blue-white lightning ribbon & corona texture (rendered additive unlit)."""
    W = H = 128
    im = Image.new("RGB", (W, H), (0, 0, 0))
    px = im.load()
    for y in range(H):
        # Upper half (v in 0..0.5): jagged glowing lightning bolt cross-section (v=0.25 core)
        if y < 64:
            d = abs(y - 31.5) / 31.5
            core = max(0.0, 1.0 - d * 2.6) ** 1.4
            halo = max(0.0, 1.0 - d) ** 2.2
            for x in range(W):
                flick = 0.85 + 0.15 * math.sin(x * 0.35 + y * 0.2)
                r = int(min(255, (255 * core + 45 * halo) * flick))
                g = int(min(255, (255 * core + 185 * halo) * flick))
                b = int(min(255, (255 * core + 255 * halo) * flick))
                px[x, y] = (r, g, b)
        else:
            # Lower half (v in 0.5..1.0): radial electric plasma corona burst centered at (64, 96)
            for x in range(W):
                rr = math.hypot(x - 63.5, y - 95.5) / 31.0
                if rr < 1.0:
                    ang = math.atan2(y - 95.5, x - 63.5)
                    rays = 0.72 + 0.28 * math.sin(ang * 9.0) * math.cos(ang * 5.0)
                    s = ((1.0 - rr) ** 1.8) * rays
                    r = int(min(255, 220 * (s ** 2.0)))
                    g = int(min(255, 240 * (s ** 1.25)))
                    b = int(min(255, 255 * s))
                    px[x, y] = (r, g, b)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    out_p = os.path.join(PROGS, "v_laptop_zap.png")
    im.save(out_p, "PNG", optimize=True)
    return out_p


def write_laptop_shader():
    os.makedirs(SCRIPTS, exist_ok=True)
    sh_path = os.path.join(SCRIPTS, "laptop_gun.shader")
    txt = """// written by mm_tools/build_laptop_gun.py
progs/v_laptop_scr
{
\tcull none
\t{
\t\tmap progs/v_laptop_scr
\t\trgbGen identity
\t}
}

progs/v_laptop_zap
{
\tcull none
\t{
\t\tmap progs/v_laptop_zap
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""
    for sname in ("body", "keys", "hand"):
        txt += f"\nprogs/v_laptop_{sname}\n{{\n\tcull none\n\t{{\n\t\tmap progs/v_laptop_{sname}\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"Wrote {sh_path}", flush=True)


# --------------------------------------------------------------------------- Laptop Local Geometry (Deck Origin = Center of Base Top)
# Laptop local space before eye-space placement:
#   x in [-3.9, +3.9]  (-x = front wrist-rest lip facing player, +x = rear hinge away from player)
#   y in [-5.8, +5.8]  (+y = left side of laptop, -y = right side of laptop)
#   z = 0.0            top surface of base palm-rest deck; base bottom at z = -0.82
DECK_X0, DECK_X1 = -3.9, 3.9
DECK_Y0, DECK_Y1 = -5.8, 5.8
DECK_Z0, DECK_Z1 = -0.82, 0.0
HINGE_X, HINGE_Z = 3.72, 0.08
LID_OPEN_DEG = 104.0    # Angle between keyboard deck and open screen (>90 deg tilts slightly back)
LID_H = 8.15
LID_THICK = 0.48


def lid_point(u_y, h_along, d_normal):
    """Maps lid-local coordinates to laptop-local 3D coordinates:
      u_y      : lateral [-5.8 .. +5.8] (+ left, - right)
      h_along  : distance from hinge up along lid [0 .. LID_H]
      d_normal : offset toward viewer along screen normal (+ in front of LCD backing, - inside lid)
    """
    # At LID_OPEN_DEG = 104 deg from front deck (-X):
    # Lid upward vector goes slightly +X (rearward) by (LID_OPEN_DEG - 90) = 14 deg!
    tilt_back = math.radians(LID_OPEN_DEG - 90.0)
    up_dir = (math.sin(tilt_back), 0.0, math.cos(tilt_back))          # along screen bottom -> top
    nrm_dir = (-math.cos(tilt_back), 0.0, math.sin(tilt_back))        # pointing toward player's eyes!
    base = (HINGE_X, u_y, HINGE_Z)
    return vadd(base, vadd(vmul(up_dir, h_along), vmul(nrm_dir, d_normal)))


def lid_normal(d_normal=1.0):
    tilt_back = math.radians(LID_OPEN_DEG - 90.0)
    n = (-math.cos(tilt_back), 0.0, math.sin(tilt_back))
    return n if d_normal >= 0 else vmul(n, -1.0)


def build_laptop_static_and_keys():
    """Returns:
      body_mesh  : rigid laptop base + open lid + ports + phone cord stub
      fixed_keys : outer non-animated keys + red TrackPoint
      anim_keys  : list of 4 MeshParts (key clusters that physically depress during fast typing!)
      scr_quads  : list of 4 tuple(verts_active, verts_parked, nrm, uvs) for the 4 LCD quadrants
    """
    body = MeshPart("body")

    # 1. Beveled Base Chassis (2-tier chamfered ThinkPad slab)
    body.add_box(
        DECK_X0, DECK_X1, DECK_Y0, DECK_Y1, -0.66, 0.0,
        uv_rect=(0.02, 0.02, 0.46, 0.46),
        top_uv=(0.50, 0.0, 1.0, 0.50),
        front_uv=(0.02, 0.75, 0.48, 0.87),
        back_uv=(0.02, 0.52, 0.48, 0.70),
    )
    # Tapered lower belly pan + 4 rubber feet
    body.add_box(DECK_X0 + 0.28, DECK_X1 - 0.22, DECK_Y0 + 0.28, DECK_Y1 - 0.28, -0.84, -0.66, uv_rect=(0.04, 0.04, 0.42, 0.42))
    for fx in (DECK_X0 + 0.75, DECK_X1 - 0.75):
        for fy in (DECK_Y0 + 0.85, DECK_Y1 - 0.85):
            body.add_box(fx - 0.32, fx + 0.32, fy - 0.32, fy + 0.32, -0.92, -0.84, uv_rect=(0.02, 0.40, 0.12, 0.48))

    # Left-side (+Y) 56k RJ-11 modular phone plug & coiled grey modem line stub!
    plug_x, plug_y, plug_z = 1.45, DECK_Y1, -0.34
    body.add_box(plug_x - 0.36, plug_x + 0.36, plug_y, plug_y + 0.55, plug_z - 0.22, plug_z + 0.22, uv_rect=(0.26, 0.56, 0.34, 0.66))
    cord_pts = [
        (plug_x, plug_y + 0.50, plug_z),
        (plug_x + 0.15, plug_y + 1.15, plug_z - 0.25),
        (plug_x + 0.45, plug_y + 1.65, plug_z - 0.85),
        (plug_x + 0.65, plug_y + 1.95, plug_z - 1.75),
        (plug_x + 0.75, plug_y + 2.05, plug_z - 2.85),
    ]
    build_tube_into(body, cord_pts, [0.11, 0.11, 0.10, 0.10, 0.09], (0.37, 0.58, 0.46, 0.65), sides=6)

    # Twin metallic/dark barrel hinges along rear edge
    for hy0, hy1 in ((-4.85, -3.55), (3.55, 4.85)):
        pts_h = [(HINGE_X, hy0, HINGE_Z), (HINGE_X, hy1, HINGE_Z)]
        build_tube_into(body, pts_h, [0.28, 0.28], (0.04, 0.10, 0.24, 0.24), sides=8)

    # 2. Clamshell Black LCD Lid (framed bezel around recessed LCD panel!)
    # Outer lid shell behind the LCD backing (-0.48 .. -0.04 in d_normal)
    def add_lid_slab(y0, y1, h0, h1, d0, d1, uv_front=(0.04, 0.04, 0.44, 0.44), uv_back=(0.50, 0.50, 1.0, 1.0)):
        # 8 corners in lid space
        p_ftl = lid_point(y1, h1, d1)
        p_ftr = lid_point(y0, h1, d1)
        p_fbr = lid_point(y0, h0, d1)
        p_fbl = lid_point(y1, h0, d1)

        p_btl = lid_point(y1, h1, d0)
        p_btr = lid_point(y0, h1, d0)
        p_bbr = lid_point(y0, h0, d0)
        p_bbl = lid_point(y1, h0, d0)

        # Front face (toward player)
        body.add_quad(p_ftl, p_ftr, p_fbr, p_fbl, (uv_front[0], uv_front[1]), (uv_front[2], uv_front[1]), (uv_front[2], uv_front[3]), (uv_front[0], uv_front[3]))
        # Back face (away from player)
        body.add_quad(p_btr, p_btl, p_bbl, p_bbr, (uv_back[0], uv_back[1]), (uv_back[2], uv_back[1]), (uv_back[2], uv_back[3]), (uv_back[0], uv_back[3]))
        # Top edge
        body.add_quad(p_btl, p_btr, p_ftr, p_ftl, (0.04, 0.04), (0.44, 0.04), (0.44, 0.16), (0.04, 0.16))
        # Bottom edge
        body.add_quad(p_fbl, p_fbr, p_bbr, p_bbl, (0.04, 0.04), (0.44, 0.04), (0.44, 0.16), (0.04, 0.16))
        # Left edge (+Y)
        body.add_quad(p_btl, p_ftl, p_fbl, p_bbl, (0.04, 0.04), (0.44, 0.04), (0.44, 0.16), (0.04, 0.16))
        # Right edge (-Y)
        body.add_quad(p_ftr, p_btr, p_bbr, p_fbr, (0.04, 0.04), (0.44, 0.04), (0.44, 0.16), (0.04, 0.16))

    # Rear lid housing + opaque LCD backing plate at d = -0.04 (screen quads switch across d = -0.04!)
    add_lid_slab(DECK_Y0, DECK_Y1, 0.12, LID_H, -LID_THICK, -0.04, uv_front=(0.04, 0.04, 0.20, 0.20), uv_back=(0.50, 0.50, 1.0, 1.0))

    # Raised 4-side black LCD bezel frame (d = -0.04 .. +0.16) surrounding screen aperture (y in [-5.12..+5.12], h in [0.78..7.56])
    SCR_Y0, SCR_Y1 = -5.12, 5.12
    SCR_H0, SCR_H1 = 0.78, 7.56
    # Bottom bezel bar (with 'THINK-LAG 56K' label!)
    add_lid_slab(DECK_Y0, DECK_Y1, 0.12, SCR_H0, -0.04, 0.16, uv_front=(0.01, 0.75, 0.49, 0.87), uv_back=(0.04, 0.04, 0.24, 0.24))
    # Top bezel bar + twin ThinkPad latch hooks
    add_lid_slab(DECK_Y0, DECK_Y1, SCR_H1, LID_H, -0.04, 0.16, uv_front=(0.04, 0.04, 0.44, 0.16), uv_back=(0.04, 0.04, 0.24, 0.24))
    add_lid_slab(-3.6, -3.25, LID_H - 0.05, LID_H + 0.12, 0.08, 0.28)
    add_lid_slab(3.25, 3.6, LID_H - 0.05, LID_H + 0.12, 0.08, 0.28)
    # Left & Right side bezel bars
    add_lid_slab(SCR_Y1, DECK_Y1, SCR_H0, SCR_H1, -0.04, 0.16)
    add_lid_slab(DECK_Y0, SCR_Y0, SCR_H0, SCR_H1, -0.04, 0.16)

    # 3. Four LCD Screen Quadrants (active at d = +0.055 in front of -0.04 black plate; parked at d = -0.145 inside lid!)
    scr_quads = []
    quad_uvs = [
        (0.002, 0.002, 0.498, 0.498),   # 0: Idle A
        (0.502, 0.002, 0.998, 0.498),   # 1: Idle B
        (0.002, 0.502, 0.498, 0.998),   # 2: Shoot Typing ('Hacking internet lag' + AOL 99%)
        (0.502, 0.502, 0.998, 0.998),   # 3: Shoot Electric Blast ('Hacking internet lag' 56K Surge!)
    ]
    n_scr = lid_normal(+1.0)
    for qi, (u0, v0, u1, v1) in enumerate(quad_uvs):
        # Active screen corners (+Y is viewer's LEFT -> u0, -Y is viewer's RIGHT -> u1; top h1 -> v0, bottom h0 -> v1)
        v_act = [
            lid_point(SCR_Y1, SCR_H1, +0.060),
            lid_point(SCR_Y0, SCR_H1, +0.060),
            lid_point(SCR_Y0, SCR_H0, +0.060),
            lid_point(SCR_Y1, SCR_H0, +0.060),
        ]
        v_prk = [
            lid_point(SCR_Y1, SCR_H1, -0.140),
            lid_point(SCR_Y0, SCR_H1, -0.140),
            lid_point(SCR_Y0, SCR_H0, -0.140),
            lid_point(SCR_Y1, SCR_H0, -0.140),
        ]
        uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        scr_quads.append((v_act, v_prk, n_scr, uvs))

    # 4. Sculpted 3D Keyboard (6 rows of keys + red TrackPoint; left/center home keys grouped into 4 animated clusters!)
    fixed_keys = MeshPart("keys")
    anim_keys = [MeshPart("keys") for _ in range(4)]

    rows_widths = [
        [1.1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1.2],
        [0.9, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1.8],
        [1.4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1.3],
        [1.65, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2.05],
        [2.1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2.1],
        [1.3, 1.1, 1.3, 1.1, 5.2, 1.1, 1.0, 1.0, 1.0],
    ]
    kb_y_left, kb_y_right = 5.18, -5.18     # +Y is left, -Y is right
    kb_x_rear, kb_x_front = 3.15, -0.95     # +X is rear (row 0), -X is front (row 5)
    uv_side = (0.04, 0.86, 0.22, 0.98)

    n_rows = len(rows_widths)
    row_pitch_x = (kb_x_rear - kb_x_front) / float(n_rows)

    for ri, rws in enumerate(rows_widths):
        kx1 = kb_x_rear - ri * row_pitch_x - 0.04
        kx0 = kx1 - (row_pitch_x - 0.08)
        # Matching UV vertical band in build_keys_texture() (512x512: y0 = 14 + ri * 68, h = 62)
        v_top0 = (14.0 + ri * 68.0) / 512.0
        v_top1 = (14.0 + ri * 68.0 + 62.0) / 512.0

        tot_w = float(sum(rws))
        cur_u = 0.0
        for ci, kw in enumerate(rws):
            f0 = cur_u / tot_w
            f1 = (cur_u + kw) / tot_w
            cur_u += kw
            ky_l = kb_y_left - f0 * (kb_y_left - kb_y_right) - 0.03
            ky_r = kb_y_left - f1 * (kb_y_left - kb_y_right) + 0.03
            u_top0 = (12.0 + f0 * 488.0 + 2.0) / 512.0
            u_top1 = (12.0 + f1 * 488.0 - 2.0) / 512.0

            # Assign left-half & spacebar typing keys (rows 1..5, left/middle columns) to animated clusters 0..3!
            y_mid = 0.5 * (ky_l + ky_r)
            if 1 <= ri <= 4 and y_mid > -1.2 and 1 <= ci <= 8:
                cluster_id = (ri + ci) % 3
                target_mesh = anim_keys[cluster_id]
            elif ri == 5 and kw > 4.0:
                # Spacebar -> cluster 3 (thumb strikes!)
                target_mesh = anim_keys[3]
            else:
                target_mesh = fixed_keys

            target_mesh.add_keycap(kx0, kx1, ky_r, ky_l, 0.01, 0.21, (u_top0, v_top0, u_top1, v_top1), uv_side)

    # Iconic bright red ThinkPad TrackPoint nub right in the middle of G-H-B!
    build_ellipsoid_into(
        fixed_keys,
        center=(0.68, -0.05, 0.22),
        ax=(1.0, 0.0, 0.0), ay=(0.0, 1.0, 0.0), az=(0.0, 0.0, 1.0),
        rx=0.22, ry=0.22, rz=0.14,
        uv_rect=(0.27, 0.85, 0.48, 0.98),
        segs=8, rings=5,
    )

    return body, fixed_keys, anim_keys, scr_quads


# --------------------------------------------------------------------------- Right Holding Hand & Left Rapid-Typing Hand
UV_SKIN = (0.04, 0.04, 0.46, 0.46)
UV_TIP = (0.54, 0.04, 0.96, 0.46)
UV_GLOVE = (0.04, 0.54, 0.46, 0.96)
UV_CUFF = (0.54, 0.54, 0.96, 0.96)


def build_right_holding_hand():
    """Builds the player's RIGHT hand in laptop-local space, gripping the right (-Y) palm-rest corner & base!
    Thumb clamps firmly over top of the right palm-rest deck; 4 fingers curl underneath the bottom plate."""
    m = MeshPart("hand_r")

    # Forearm + ribbed cuff coming from lower-right-front (-X, -Y, -Z) up to wrist at (-3.2, -6.25, -0.55)
    fore_pts = [
        (-9.6, -9.8, -5.8),
        (-7.2, -8.4, -3.9),
        (-5.1, -7.2, -2.1),
        (-3.8, -6.5, -1.05),
    ]
    build_tube_into(m, fore_pts, [(1.45, 1.25), (1.30, 1.12), (1.15, 0.98), (1.02, 0.88)], UV_CUFF, sides=8, cap_end=False)

    # Fingerless tactical hacker glove palm hugging the right edge (-Y = -5.8) of the laptop deck
    palm_pts = [
        (-3.95, -6.45, -1.02),
        (-3.15, -6.18, -0.68),
        (-2.15, -6.02, -0.52),
        (-1.25, -5.92, -0.50),
    ]
    build_tube_into(m, palm_pts, [(1.02, 0.72), (1.16, 0.76), (1.14, 0.72), (0.92, 0.62)], UV_GLOVE, sides=8)

    # Right Thumb: wraps UP and OVER the top of the right palm-rest bezel (clearly visible in 1st-person POV!)
    thumb_glove = [
        (-3.25, -6.05, -0.42),
        (-2.85, -5.75, 0.24),
        (-2.45, -5.22, 0.44),
    ]
    build_tube_into(m, thumb_glove, [0.46, 0.43, 0.39], UV_GLOVE, sides=7, cap_end=False)
    thumb_skin = [
        (-2.50, -5.28, 0.43),
        (-2.05, -4.68, 0.36),
        (-1.62, -4.22, 0.24),
    ]
    build_tube_into(m, thumb_skin, [0.38, 0.35, 0.29], UV_TIP, sides=7)

    # Four Right Fingers (index -> pinky): curled securely underneath the laptop base plate (z = -0.84)
    # Index is furthest forward (+X = -0.85), pinky is closest to front corner (-X = -3.15)
    for fi, fx in enumerate([-0.95, -1.68, -2.40, -3.08]):
        reach = 1.95 if fi in (1, 2) else (1.78 if fi == 0 else 1.48)
        f_pts = [
            (fx, -6.02, -0.56),
            (fx + 0.05, -5.82, -1.04),
            (fx + 0.08, -5.10, -1.16),
            (fx + 0.08, -5.10 + reach * 0.55, -1.08),
        ]
        build_tube_into(m, f_pts[:2], [0.36, 0.34], UV_GLOVE, sides=6, cap_end=False)
        build_tube_into(m, f_pts[1:], [0.34, 0.31, 0.26], UV_SKIN, sides=6)

    return m


def build_left_typing_hand_frame(pose_cfg):
    """Builds the player's LEFT hand for a single frame in laptop-local space with identical vertex/triangle topology!
    Finger order from LEFT (+Y) to RIGHT (-Y) when palm-down over keyboard:
      pinky (+Y outermost) -> ring -> middle -> index -> thumb (-Y innermost, over spacebar)!
    pose_cfg = dict(
        wrist=(wx, wy, wz),       # wrist center in laptop-local space
        pitch_deg=...,            # hand pitch (+deg tips fingers down toward keys)
        roll_deg=...,             # hand roll
        yaw_deg=...,              # hand yaw (-deg angles fingers slightly inward toward center of keyboard)
        curls=[c_pinky, c_ring, c_mid, c_idx],   # 0.0 = lifted high, 1.0 = slamming keycap!
        splay=[...],              # subtle lateral spread
        thumb_press=0.0..1.0,     # thumb striking spacebar
    )
    """
    m = MeshPart("hand_l")
    wx, wy, wz = pose_cfg["wrist"]
    hpitch = pose_cfg.get("pitch_deg", -8.0)
    hroll = pose_cfg.get("roll_deg", 8.0)
    hyaw = pose_cfg.get("yaw_deg", -18.0)
    curls = pose_cfg["curls"]         # [pinky, ring, middle, index]
    thumb_p = pose_cfg["thumb_press"]

    def xform_h(p):
        q = rot_x(p, hroll)
        q = rot_y(q, hpitch)
        q = rot_z(q, hyaw)
        return (q[0] + wx, q[1] + wy, q[2] + wz)

    # Forearm + dark cuff extending back-left-down from wrist (0, 0, 0) to elbow (-7.5, +4.4, -4.8)
    fore_local = [
        (-7.6, 4.4, -4.8),
        (-5.0, 2.9, -3.1),
        (-2.5, 1.4, -1.5),
        (-0.5, 0.25, -0.25),
    ]
    build_tube_into(
        m,
        [xform_h(p) for p in fore_local],
        [(1.42, 1.20), (1.28, 1.08), (1.12, 0.94), (0.98, 0.80)],
        UV_CUFF, sides=8, cap_end=False,
    )

    # Fingerless hacker-glove dorsal palm & metacarpals (from wrist x=0 forward to knuckles x=+2.18)
    palm_local = [
        (-0.55, 0.12, -0.14),
        (0.42, 0.04, 0.00),
        (1.38, 0.00, 0.06),
        (2.16, -0.02, 0.04),
    ]
    build_tube_into(
        m,
        [xform_h(p) for p in palm_local],
        [(0.94, 0.52), (1.26, 0.52), (1.40, 0.48), (1.34, 0.42)],
        UV_GLOVE, sides=10,
    )

    # 4 Articulated 3-segment typing fingers (from +Y left = Pinky to -Y right = Index!)
    # Every joint slopes naturally downward (+a1, +a2, +a3) so fingers arch like a real pianist/hacker!
    finger_specs = [
        # (y_knuckle, lengths (prox, mid, dist), base_radius, yaw_splay_deg)
        (+1.10, (0.94, 0.68, 0.50), 0.25, +6.0),    # 0: Left Pinky (+Y outer)
        (+0.37, (1.14, 0.82, 0.56), 0.28, +2.0),    # 1: Left Ring
        (-0.36, (1.22, 0.88, 0.60), 0.30, -2.0),    # 2: Left Middle
        (-1.08, (1.12, 0.80, 0.56), 0.29, -5.5),    # 3: Left Index (-Y inner)
    ]

    for fi, (yk, (l1, l2, l3), r0, splay_deg) in enumerate(finger_specs):
        c = curls[fi]   # 0.0 = arched cleanly above keycap, 1.0 = slamming keycap!
        a1 = math.radians(12.0 + 16.0 * c)
        a2 = a1 + math.radians(18.0 + 26.0 * c)
        a3 = a2 + math.radians(18.0 + 16.0 * c)

        sp = math.radians(splay_deg)
        dir_xy = (math.cos(sp), math.sin(sp))

        p0 = (2.06, yk, 0.05)
        p1 = (p0[0] + dir_xy[0] * l1 * math.cos(a1), p0[1] + dir_xy[1] * l1 * math.cos(a1), p0[2] - l1 * math.sin(a1))
        p2 = (p1[0] + dir_xy[0] * l2 * math.cos(a2), p1[1] + dir_xy[1] * l2 * math.cos(a2), p1[2] - l2 * math.sin(a2))
        p3 = (p2[0] + dir_xy[0] * l3 * math.cos(a3), p2[1] + dir_xy[1] * l3 * math.cos(a3), p2[2] - l3 * math.sin(a3))

        pts_w = [xform_h(p) for p in (p0, p1, p2, p3)]
        p_glove_end = vlerp(pts_w[0], pts_w[1], 0.45)
        build_tube_into(m, [pts_w[0], p_glove_end], [r0 * 1.06, r0 * 1.00], UV_GLOVE, sides=7, cap_end=False)
        build_tube_into(m, [p_glove_end, pts_w[1], pts_w[2], pts_w[3]], [r0 * 0.96, r0 * 0.88, r0 * 0.78, r0 * 0.66], UV_TIP, sides=7)

    # Left Thumb (-Y inner side of left hand, poised over the Spacebar!)
    tb0 = (0.72, -1.16, -0.10)
    drop_t = 0.65 * thumb_p
    tb1 = (1.48, -1.68, -0.42 - 0.26 * drop_t)
    tb2 = (2.22, -1.86, -0.78 - 0.48 * drop_t)
    tb3 = (2.82, -1.78, -1.04 - 0.66 * drop_t)
    t_pts = [xform_h(p) for p in (tb0, tb1, tb2, tb3)]
    build_tube_into(m, t_pts[:2], [0.40, 0.36], UV_GLOVE, sides=7, cap_end=False)
    build_tube_into(m, t_pts[1:], [0.35, 0.31, 0.25], UV_TIP, sides=7)

    return m


# --------------------------------------------------------------------------- Eye-Space Placement & Coordinate Helpers
BASE_EYE = (14.6, -2.35, -5.85)
BASE_PITCH = +11.5    # lifts rear hinge (+X) higher than front lip (-X) so entire 3D keyboard faces player's eye!
BASE_ROLL = -3.5      # subtle natural right-handed cant
BASE_YAW = +16.5      # angles laptop screen & keyboard comfortably toward the player's eyes


def laptop_to_eye(p, kick_dx=0.0, kick_dz=0.0, kick_pitch=0.0, kick_roll=0.0, kick_yaw=0.0):
    q = rot_x(p, BASE_ROLL + kick_roll)
    q = rot_y(q, BASE_PITCH + kick_pitch)
    q = rot_z(q, BASE_YAW + kick_yaw)
    return (q[0] + BASE_EYE[0] + kick_dx, q[1] + BASE_EYE[1], q[2] + BASE_EYE[2] + kick_dz)


def eye_to_laptop(p_eye):
    """Exact inverse of laptop_to_eye() at rest pose, used to aim 3D lightning bolts around the screen into the crosshair!"""
    d = vsub(p_eye, BASE_EYE)
    d = rot_z(d, -BASE_YAW)
    d = rot_y(d, -BASE_PITCH)
    d = rot_x(d, -BASE_ROLL)
    return d


def laptop_nrm_to_eye(n, kick_pitch=0.0, kick_roll=0.0, kick_yaw=0.0):
    q = rot_x(n, BASE_ROLL + kick_roll)
    q = rot_y(q, BASE_PITCH + kick_pitch)
    q = rot_z(q, BASE_YAW + kick_yaw)
    return vnorm(q)


# --------------------------------------------------------------------------- 3D Electric Lightning Arcs Builder
def build_electric_bolts_frame(active_level, frame_seed, corona_scale=0.0):
    """Builds fixed-topology 3D electric lightning bolts + screen plasma corona in laptop-local space!
    When active_level <= 0.0, all vertices collapse cleanly to a single point hidden inside the hinge (0 area, 0 wire edges!).
    Topology is 100% constant across all 34 frames:
      - 5 main forward bolts arcing AROUND & OVER the LCD screen and converging forward into the player's crosshair!
      - 4 chassis/keyboard/modem arcs crackling across bezel, 3D keys, screen glass, and 56k phone jack!
      - 1 screen plasma corona burst quad!
    """
    m = MeshPart("zap")
    rng = random.Random(1000 + frame_seed * 97)
    hide_pt = (HINGE_X - 0.2, 0.0, -0.35)   # safely inside opaque black laptop chassis

    N_SEGS = 10

    def add_crossed_bolt(pts, half_w):
        assert len(pts) == N_SEGS + 1
        # Compute perpendicular basis per vertex so crossed ribbons have full thickness from EVERY angle!
        tans = []
        for i in range(N_SEGS + 1):
            p_prev = pts[max(0, i - 1)]
            p_next = pts[min(N_SEGS, i + 1)]
            d = vsub(p_next, p_prev)
            tans.append(vnorm(d) if vlen(d) > 1e-6 else (1.0, 0.0, 0.0))

        _, bu0, bv0 = frame_basis(tans[0])
        frames_uv = []
        bu, bv = bu0, bv0
        for ti in tans:
            bu_p = vsub(bu, vmul(ti, vdot(bu, ti)))
            if vlen(bu_p) < 1e-5:
                _, bu, bv = frame_basis(ti)
            else:
                bu = vnorm(bu_p)
                bv = vcross(ti, bu)
            frames_uv.append((bu, bv))

        for plane_idx in (0, 1):
            b = len(m.verts)
            for i, p in enumerate(pts):
                u_c = i / float(N_SEGS)
                taper = math.sin(math.pi * min(0.96, max(0.08, u_c)))
                hw = half_w * (0.42 + 0.58 * taper)
                axis = frames_uv[i][plane_idx]
                p_lo = vadd(p, vmul(axis, -hw))
                p_hi = vadd(p, vmul(axis, +hw))
                m.verts += [p_lo, p_hi]
                m.norms += [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0)]
                m.st += [(u_c, 0.03), (u_c, 0.47)]
            for i in range(N_SEGS):
                a0, a1, a2, a3 = b + 2 * i, b + 2 * i + 1, b + 2 * i + 2, b + 2 * i + 3
                m.tris += [(a0, a1, a2), (a1, a3, a2)]

    def bezier2(p0, p1, p2, t):
        om = 1.0 - t
        return (
            om * om * p0[0] + 2.0 * om * t * p1[0] + t * t * p2[0],
            om * om * p0[1] + 2.0 * om * t * p1[1] + t * t * p2[1],
            om * om * p0[2] + 2.0 * om * t * p1[2] + t * t * p2[2],
        )

    # 5 Forward Muzzle Lightning Bolts (arc cleanly AROUND left/right & OVER top of LCD lid into the crosshair!)
    bolt_curves = [
        # 0: Left 56k RJ-11 Modem Jack -> sweeps outside left bezel -> converges into crosshair!
        ((1.45, DECK_Y1 + 0.35, -0.15), eye_to_laptop((20.5, +6.8, +0.4)), eye_to_laptop((33.5, +0.9, +0.3)), 0.50),
        # 1: Left Keyboard Keys -> arcs over top-left bezel -> converges into crosshair!
        ((1.85, +3.10, 0.32),           eye_to_laptop((18.5, +4.2, +5.0)), eye_to_laptop((34.5, +0.3, +0.7)), 0.48),
        # 2: Top Center Screen Bezel -> high overhead arc -> center crosshair!
        (lid_point(0.0, LID_H, +0.20),  eye_to_laptop((22.5, -0.8, +5.6)), eye_to_laptop((35.5, 0.0, +0.2)),  0.54),
        # 3: Upper-Right Screen Bezel -> sweeps outside right bezel -> converges into crosshair!
        (lid_point(-5.2, 6.6, +0.20),   eye_to_laptop((21.5, -8.2, +2.0)), eye_to_laptop((34.0, -0.7, +0.0)), 0.50),
        # 4: Right Keyboard Keys -> lower-right arc around screen -> converges into crosshair!
        ((1.10, -4.55, 0.30),           eye_to_laptop((20.5, -7.8, -1.6)), eye_to_laptop((33.0, -0.4, -0.5)), 0.46),
    ]
    for p_start, p_mid_full, p_end_full, hw_max in bolt_curves:
        if active_level <= 0.08:
            pts = [hide_pt] * (N_SEGS + 1)
            add_crossed_bolt(pts, 0.0)
        else:
            reach = min(1.0, active_level)
            pts = [p_start]
            for s in range(1, N_SEGS + 1):
                t = (s / float(N_SEGS)) * reach
                base_p = bezier2(p_start, p_mid_full, p_end_full, t)
                if s < N_SEGS:
                    j_amp = 1.35 * math.sin(math.pi * (s / float(N_SEGS))) * reach
                    jitter = (rng.uniform(-0.5, 0.5) * j_amp, rng.uniform(-1.0, 1.0) * j_amp, rng.uniform(-1.0, 1.0) * j_amp)
                    base_p = vadd(base_p, jitter)
                pts.append(base_p)
            add_crossed_bolt(pts, hw_max * min(1.0, active_level * 1.15))

    # 4 Local Laptop Arcs (crackling across top of black LCD bezel, keyboard keys, & 56k modem jack!)
    local_arcs = [
        (lid_point(+4.9, 7.65, +0.24), lid_point(-4.9, 7.65, +0.24), 0.28, 0.50),  # Across top LCD bezel!
        ((2.3, +4.7, 0.36),            (0.2, -4.5, 0.36),            0.28, 0.48),  # Across 3D keyboard!
        ((1.45, DECK_Y1 + 0.4, -0.2),  lid_point(+4.9, 4.4, +0.25),  0.25, 0.44),  # 56k Modem port -> Screen!
        (lid_point(-4.8, 1.3, +0.24),  lid_point(+4.2, 6.9, +0.24),  0.24, 0.46),  # Diagonal across LCD glass!
    ]
    for p_s, p_e, hw_l, jag in local_arcs:
        if active_level <= 0.005:
            pts = [hide_pt] * (N_SEGS + 1)
            add_crossed_bolt(pts, 0.0)
        else:
            pts = [p_s]
            for s in range(1, N_SEGS):
                t = s / float(N_SEGS)
                bp = vlerp(p_s, p_e, t)
                ja = jag * math.sin(math.pi * t)
                pts.append(vadd(bp, (rng.uniform(-ja, ja), rng.uniform(-ja, ja), rng.uniform(-ja, ja) + 0.22 * ja)))
            pts.append(p_e)
            add_crossed_bolt(pts, hw_l * min(1.0, active_level * 1.45))

    # Screen Plasma Corona Quad (uses lower half of v_laptop_zap.png: v in 0.52..0.98)
    if corona_scale <= 0.01:
        m.add_quad(hide_pt, hide_pt, hide_pt, hide_pt, (0.02, 0.52), (0.98, 0.52), (0.98, 0.98), (0.02, 0.98), nrm=(-1.0, 0.0, 0.0))
    else:
        r_y = 4.6 * corona_scale
        r_h = 3.5 * corona_scale
        hc = 4.2
        c0 = lid_point(+r_y, hc + r_h, +0.32)
        c1 = lid_point(-r_y, hc + r_h, +0.32)
        c2 = lid_point(-r_y, hc - r_h, +0.32)
        c3 = lid_point(+r_y, hc - r_h, +0.32)
        m.add_quad(c0, c1, c2, c3, (0.02, 0.52), (0.98, 0.52), (0.98, 0.98), (0.02, 0.98), nrm=lid_normal(+1.0))

    return m


def build_animation_schedule():
    """Returns 34 frame dicts:
      - Frames  0..11: idle1..idle12   (gentle breathing sway in right hand; Panel 0: 'Hacking internet lag' + AOL Dial-Up & Download)
      - Frames 12..33: shoot1..shoot22
          * 12..13 (shoot1..2):   Left hand whips up from lower-left onto the black laptop keyboard!
          * 14..20 (shoot3..9):   Left hand furiously types at hyper-speed across the keys (Panel 1: AOL racing to 94%)!
          * 21..23 (shoot10..12): Final power keystrokes -> Screen flashes GIANT 'Hacking internet lag' alert (Panel 2) + pre-sparks!
          * 24..30 (shoot13..19): ELECTRIC DISCHARGE! Screen blazes Panel 3 ('Hacking internet lag' 56K Surge) +
                                  5 forward 3D lightning bolts arc around/over the screen into the crosshair!
          * 31..33 (shoot20..22): Bolts snap out, left hand drops smoothly back to idle!
    """
    sched = []
    parked_wrist = (-5.2, +6.2, -5.8)   # Low off-deck resting position during idle

    # 12 Idle Frames (0..11)
    for i in range(12):
        ph = 2.0 * math.pi * i / 12.0
        sched.append(dict(
            name=f"idle{i + 1}",
            dx=0.12 * math.cos(ph),
            dz=0.24 * math.sin(ph),
            kp=0.8 * math.sin(ph + 0.5),
            kr=0.6 * math.cos(ph),
            ky=0.5 * math.sin(ph),
            scr=0,
            key_dep=[0.0, 0.0, 0.0, 0.0],
            zap=0.0,
            corona=0.0,
            lh=dict(
                wrist=(parked_wrist[0], parked_wrist[1], parked_wrist[2] + 0.18 * math.sin(ph)),
                pitch_deg=-18.0, roll_deg=16.0, yaw_deg=-24.0,
                curls=[0.35, 0.40, 0.42, 0.35],
                thumb_press=0.2,
            ),
        ))

    # 22 Shoot Frames (12..33)
    # Pre-choreographed furious typing finger patterns [pinky, ring, middle, index] + thumb + lateral wrist sweep!
    # Wrist sits on the left (+Y = 3.2..4.3) angled inward (-32 deg yaw, +16 deg roll) so all 4 fingers & keys shine in POV!
    typing_patterns = [
        # (wy_wrist, wx_wrist, [pinky, ring, mid, idx], thumb, depressed_key_cluster_weights)
        (+4.20, -0.75, [0.05, 1.00, 0.10, 1.00], 0.05, [1.0, 0.0, 0.8, 0.0]),
        (+3.65, -0.45, [1.00, 0.05, 1.00, 0.05], 1.00, [0.0, 1.0, 0.0, 1.0]),
        (+3.15, -0.35, [0.10, 1.00, 0.15, 0.95], 0.05, [0.9, 0.2, 1.0, 0.0]),
        (+3.85, -0.65, [0.95, 0.10, 0.95, 0.05], 1.00, [0.1, 1.0, 0.0, 1.0]),
        (+4.30, -0.40, [0.05, 0.95, 0.05, 1.00], 0.10, [1.0, 0.0, 0.9, 0.0]),
        (+3.40, -0.60, [1.00, 0.05, 1.00, 0.10], 0.95, [0.0, 0.9, 0.2, 1.0]),
        (+3.05, -0.35, [0.15, 1.00, 0.05, 1.00], 0.05, [0.9, 0.0, 1.0, 0.0]),
        (+3.95, -0.55, [0.95, 0.15, 1.00, 0.05], 1.00, [0.0, 1.0, 0.1, 1.0]),
        (+3.55, -0.45, [1.00, 0.95, 0.10, 1.00], 0.15, [1.0, 0.8, 0.0, 0.0]),
        (+3.35, -0.50, [0.95, 0.95, 1.00, 1.00], 1.00, [1.0, 1.0, 1.0, 1.0]),  # Final Enter/Space power chord!
    ]

    for s_idx in range(22):
        fn = f"shoot{s_idx + 1}"
        if s_idx < 2:
            # Frames 12..13: Left hand whips up from parked position onto keyboard!
            t = smoothstep((s_idx + 1) / 2.0)
            w_pos = vlerp(parked_wrist, (-0.75, +4.25, 1.88), t)
            sched.append(dict(
                name=fn,
                dx=-0.15 * t, dz=0.10 * t, kp=-1.0 * t, kr=0.8 * t, ky=0.0,
                scr=0 if s_idx == 0 else 1,
                key_dep=[0.0, 0.0, 0.0, 0.0],
                zap=0.0, corona=0.0,
                lh=dict(
                    wrist=w_pos,
                    pitch_deg=-18.0 * (1.0 - t),
                    roll_deg=16.0,
                    yaw_deg=-24.0 - 8.0 * t,
                    curls=[0.20, 0.25, 0.20, 0.25],
                    thumb_press=0.1,
                ),
            ))
        elif s_idx < 12:
            # Frames 14..23 (10 frames of FURIOUS HIGH-SPEED TYPING!)
            # tp_i 0..6: Panel 1 (typing macro + AOL racing to 94%); tp_i 7..9: Panel 2 (GIANT 'Hacking internet lag' alert!)
            tp_i = s_idx - 2
            wy, wx, curls, th_p, kdep = typing_patterns[tp_i]
            shudder_z = -0.14 if (tp_i % 2 == 0) else 0.08
            pre_zap = 0.05 * (tp_i - 6) if tp_i >= 7 else 0.0    # Local static sparks crackle across keys on tp_i 7..9!
            sched.append(dict(
                name=fn,
                dx=-0.20, dz=shudder_z, kp=-1.2 + 0.5 * (tp_i % 2), kr=1.0, ky=(-0.7 if tp_i % 2 else 0.7),
                scr=1 if tp_i < 7 else 2,
                key_dep=kdep,
                zap=pre_zap,
                corona=0.22 if tp_i == 9 else 0.0,
                lh=dict(
                    wrist=(wx, wy, 1.88 + (0.06 if tp_i % 2 else -0.06)),
                    pitch_deg=0.0,
                    roll_deg=16.0 + (2.5 if tp_i % 2 else -2.5),
                    yaw_deg=-32.0 + (wy - 3.6) * 4.0,
                    curls=curls,
                    thumb_press=th_p,
                ),
            ))
        elif s_idx < 19:
            # Frames 24..30 (7 frames of FULL ELECTRIC DISCHARGE + RECOIL!)
            e_i = s_idx - 12     # 0..6
            env = math.sin(math.pi * (e_i + 0.8) / 7.2)
            recoil_x = -2.15 * env
            recoil_p = -5.5 * env
            jit_y = (0.85 if e_i % 2 == 0 else -0.85) * env
            sched.append(dict(
                name=fn,
                dx=recoil_x, dz=0.38 * env, kp=recoil_p, kr=-2.0 * env, ky=jit_y,
                scr=3,
                key_dep=[0.0, 0.0, 0.0, 0.0],
                zap=0.88 + 0.12 * (e_i % 2),
                corona=0.65 + 0.25 * math.sin(e_i * 1.9),
                lh=dict(
                    # Left hand jolts back slightly with electrified fingers from the 56,000V blast!
                    wrist=(-1.55 - 0.55 * env, +4.45 + 0.40 * env, 2.15 + 0.45 * env),
                    pitch_deg=-6.0 * env,
                    roll_deg=18.0,
                    yaw_deg=-28.0,
                    curls=[0.10 + 0.15 * (e_i % 2), 0.15, 0.10, 0.15 * ((e_i + 1) % 2)],
                    thumb_press=0.10,
                ),
            ))
        else:
            # Frames 31..33 (3 recovery frames: arcs snap out, left hand lowers smoothly back to idle!)
            r_i = s_idx - 19     # 0..2
            t = smoothstep((r_i + 1) / 3.0)
            w_start = (-1.65, +4.55, 2.10)
            w_pos = vlerp(w_start, parked_wrist, t)
            sched.append(dict(
                name=fn,
                dx=-0.35 * (1.0 - t), dz=0.1 * (1.0 - t), kp=-1.0 * (1.0 - t), kr=0.0, ky=0.0,
                scr=2 if r_i == 0 else 0,
                key_dep=[0.0, 0.0, 0.0, 0.0],
                zap=0.06 if r_i == 0 else 0.0,
                corona=0.0,
                lh=dict(
                    wrist=w_pos,
                    pitch_deg=-18.0 * t,
                    roll_deg=17.0,
                    yaw_deg=-28.0 + 4.0 * t,
                    curls=[0.25, 0.30, 0.32, 0.28],
                    thumb_press=0.15,
                ),
            ))

    assert len(sched) == 34
    return sched


def main():
    os.makedirs(PROGS, exist_ok=True)
    build_body_texture()
    build_keys_texture()
    build_hand_texture()
    build_screen_texture()
    build_zap_texture()
    write_laptop_shader()

    body_part, fixed_keys_part, anim_key_parts, scr_quads = build_laptop_static_and_keys()
    rhand_part = build_right_holding_hand()
    sched = build_animation_schedule()

    # Assemble MD3 surfaces:
    #   1. body   (progs/v_laptop_body)
    #   2. keys   (progs/v_laptop_keys: fixed keys + 4 animated keycap clusters merged into 1 surface!)
    #   3. scr    (progs/v_laptop_scr:  4 LCD screen quadrants switching cleanly across the -0.04 backing plate!)
    #   4. hands  (progs/v_laptop_hand: right holding hand + left articulated typing hand!)
    #   5. zap    (progs/v_laptop_zap:  3D crossed-ribbon lightning bolts + screen plasma corona!)

    # --- Surface 1: body ---
    body_frames = []
    for fr in sched:
        vv = [laptop_to_eye(p, fr["dx"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]) for p in body_part.verts]
        nn = [laptop_nrm_to_eye(n, fr["kp"], fr["kr"], fr["ky"]) for n in body_part.norms]
        body_frames.append((vv, nn))
    surf_body = dict(name="laptop_body", shader="progs/v_laptop_body", tris=body_part.tris, st=body_part.st, frames=body_frames)

    # --- Surface 2: keys (fixed + 4 animated keycap clusters) ---
    keys_st = list(fixed_keys_part.st)
    keys_tris = list(fixed_keys_part.tris)
    cluster_offsets = []
    cur_v = len(fixed_keys_part.verts)
    for ak in anim_key_parts:
        cluster_offsets.append(cur_v)
        keys_st += ak.st
        keys_tris += [(a + cur_v, b + cur_v, c + cur_v) for (a, b, c) in ak.tris]
        cur_v += len(ak.verts)

    keys_frames = []
    for fr in sched:
        vv = [laptop_to_eye(p, fr["dx"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]) for p in fixed_keys_part.verts]
        nn = [laptop_nrm_to_eye(n, fr["kp"], fr["kr"], fr["ky"]) for n in fixed_keys_part.norms]
        for ci, ak in enumerate(anim_key_parts):
            dep = -0.15 * fr["key_dep"][ci]     # Depress keycap downward into keyboard well!
            for p, n in zip(ak.verts, ak.norms):
                vv.append(laptop_to_eye((p[0], p[1], p[2] + dep), fr["dx"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]))
                nn.append(laptop_nrm_to_eye(n, fr["kp"], fr["kr"], fr["ky"]))
        keys_frames.append((vv, nn))
    surf_keys = dict(name="laptop_keys", shader="progs/v_laptop_keys", tris=keys_tris, st=keys_st, frames=keys_frames)

    # --- Surface 3: scr (4 fullbright LCD quadrants) ---
    scr_st, scr_tris = [], []
    for qi, (_, _, _, uvs) in enumerate(scr_quads):
        b = qi * 4
        scr_st += uvs
        scr_tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]

    scr_frames = []
    for fr in sched:
        vv, nn = [], []
        active_qi = fr["scr"]
        n_eye = laptop_nrm_to_eye(scr_quads[0][2], fr["kp"], fr["kr"], fr["ky"])
        for qi, (v_act, v_prk, _, _) in enumerate(scr_quads):
            src_pts = v_act if qi == active_qi else v_prk
            for p in src_pts:
                vv.append(laptop_to_eye(p, fr["dx"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]))
                nn.append(n_eye)
        scr_frames.append((vv, nn))
    surf_scr = dict(name="laptop_scr", shader="progs/v_laptop_scr", tris=scr_tris, st=scr_st, frames=scr_frames)

    # --- Surface 4: hands (right holding hand + left articulated typing hand) ---
    lhand_meshes = [build_left_typing_hand_frame(fr["lh"]) for fr in sched]
    lh0 = lhand_meshes[0]
    off_lh = len(rhand_part.verts)
    hands_st = list(rhand_part.st) + list(lh0.st)
    hands_tris = list(rhand_part.tris) + [(a + off_lh, b + off_lh, c + off_lh) for (a, b, c) in lh0.tris]

    hands_frames = []
    for fi, fr in enumerate(sched):
        lhm = lhand_meshes[fi]
        assert len(lhm.verts) == len(lh0.verts), (len(lhm.verts), len(lh0.verts))
        vv = [laptop_to_eye(p, fr["dx"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]) for p in rhand_part.verts]
        nn = [laptop_nrm_to_eye(n, fr["kp"], fr["kr"], fr["ky"]) for n in rhand_part.norms]
        vv += [laptop_to_eye(p, fr["dx"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]) for p in lhm.verts]
        nn += [laptop_nrm_to_eye(n, fr["kp"], fr["kr"], fr["ky"]) for n in lhm.norms]
        hands_frames.append((vv, nn))
    surf_hands = dict(name="laptop_hands", shader="progs/v_laptop_hand", tris=hands_tris, st=hands_st, frames=hands_frames)

    # --- Surface 5: zap (3D electric lightning bolts + screen corona) ---
    zap_meshes = [build_electric_bolts_frame(fr["zap"], fi, fr["corona"]) for fi, fr in enumerate(sched)]
    z0 = zap_meshes[0]
    zap_frames = []
    for fi, fr in enumerate(sched):
        zm = zap_meshes[fi]
        assert len(zm.verts) == len(z0.verts), (len(zm.verts), len(z0.verts))
        vv = [laptop_to_eye(p, fr["dx"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]) for p in zm.verts]
        nn = [laptop_nrm_to_eye(n, fr["kp"], fr["kr"], fr["ky"]) for n in zm.norms]
        zap_frames.append((vv, nn))
    surf_zap = dict(name="laptop_zap", shader="progs/v_laptop_zap", tris=z0.tris, st=z0.st, frames=zap_frames)

    surfaces = [surf_body, surf_keys, surf_scr, surf_hands, surf_zap]
    for s in surfaces:
        assert len(s["st"]) <= 4096 and len(s["tris"]) <= 8192, (s["name"], len(s["st"]), len(s["tris"]))

    out_md3 = os.path.join(PROGS, "v_laptop.md3")
    md3lib.write(out_md3, dict(name="v_laptop", surfaces=surfaces, nframes=len(sched)))
    tot_v = sum(len(s["st"]) for s in surfaces)
    tot_t = sum(len(s["tris"]) for s in surfaces)
    print(f"Wrote {out_md3}: {len(surfaces)} surfaces, {tot_v} verts, {tot_t} tris, {len(sched)} frames", flush=True)


if __name__ == "__main__":
    main()
