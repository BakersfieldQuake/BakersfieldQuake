"""3D MD3 geometry and multi-frame vertex animations for the "WHERE'S THE DISK?" gun:
  1. progs/v_netsend.md3    : First-person viewmodel (60 frames: 0-39 idle spin/flip/inspect,
                              40-47 wind-up & throw [leaves hand at 44], 48-53 empty follow-through,
                              54-59 shake-out & fresh LOL.BAT disk reload)
  2. progs/netsend_pc.md3   : Deployable early-90s beige CRT PC on school lab stand (50 frames:
                              0-9 materialize w/ squash & stretch, 10-19 boot w/ LEDs & degauss shake,
                              20-39 active ghost-typing & antenna-twitch loop, 40-49 shutdown slump)
  3. progs/netsend_arc.md3  : Additive blue-white 3D crackling lightning arcs (8 frames: 0-7)
  4. progs/netsend_disk.md3 : Lone 3.5" LOL.BAT floppy disk stuck at an angle in the floor (8 frames:
                              0 flying flat, 1 stuck in floor, 2-7 electric pre-materialize tremor)
"""
import math
import random


# ==============================================================================
# 3D VECTOR & ROTATION HELPERS (Quake: +X forward, +Y left, +Z up)
# ==============================================================================
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
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def rot_x(p, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y(p, deg):
    # +deg tips +X down toward -Z (right-handed around +Y)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def rot_z(p, deg):
    # +deg turns +X toward +Y (left)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def rot_axis(v, axis, deg):
    k = vnorm(axis)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    kv = vdot(k, v)
    kxv = vcross(k, v)
    return (
        v[0] * c + kxv[0] * s + k[0] * kv * (1.0 - c),
        v[1] * c + kxv[1] * s + k[1] * kv * (1.0 - c),
        v[2] * c + kxv[2] * s + k[2] * kv * (1.0 - c),
    )


def frame_basis(t):
    t = vnorm(t)
    ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.88 else (1.0, 0.0, 0.0)
    u = vnorm(vcross(t, ref))
    v = vcross(t, u)
    return t, u, v


class MeshPart:
    """Static-topology triangle mesh builder with outward normals & UVs."""

    def __init__(self, name="part"):
        self.name = name
        self.verts = []
        self.norms = []
        self.st = []
        self.tris = []

    def append(self, other, xform_pt=None, xform_nrm=None):
        b = len(self.verts)
        if xform_pt is None:
            self.verts += list(other.verts)
        else:
            self.verts += [xform_pt(p) for p in other.verts]
        if xform_nrm is None:
            self.norms += list(other.norms)
        else:
            self.norms += [vnorm(xform_nrm(n)) for n in other.norms]
        self.st += list(other.st)
        self.tris += [(i0 + b, i1 + b, i2 + b) for (i0, i1, i2) in other.tris]

    def add_quad(self, p0, p1, p2, p3, uv0, uv1, uv2, uv3, nrm=None):
        """Adds quad (p0, p1, p2, p3) with CCW outward winding (p1-p0) x (p2-p0)."""
        if nrm is None:
            nrm = vnorm(vcross(vsub(p1, p0), vsub(p2, p0)))
        b = len(self.verts)
        self.verts += [p0, p1, p2, p3]
        self.norms += [nrm, nrm, nrm, nrm]
        self.st += [uv0, uv1, uv2, uv3]
        self.tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]

    def add_box(self, x0, x1, y0, y1, z0, z1, uv_all, uv_px=None, uv_nx=None, uv_py=None, uv_ny=None, uv_pz=None, uv_nz=None, skip_bottom=False):
        """Axis-aligned box with correct outward CCW winding and non-mirrored UVs on every face."""
        upx = uv_px or uv_all
        unx = uv_nx or uv_all
        upy = uv_py or uv_all
        uny = uv_ny or uv_all
        upz = uv_pz or uv_all
        unz = uv_nz or uv_all

        # +X face (viewer stands at +X looking -X: viewer-left is -Y=y0 -> u0, viewer-right is +Y=y1 -> u1, top is +Z=z1 -> v0)
        # Check cross: ((x1,y0,z0)-(x1,y0,z1)) x ((x1,y1,z0)-(x1,y0,z1)) = (0,0,-dz) x (0,dy,0) = (+dz*dy, 0, 0) = +X!
        self.add_quad(
            (x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1),
            (upx[0], upx[1]), (upx[0], upx[3]), (upx[2], upx[3]), (upx[2], upx[1]),
            nrm=(1.0, 0.0, 0.0),
        )
        # -X face (viewer stands at -X looking +X: viewer-left is +Y=y1 -> u0, viewer-right is -Y=y0 -> u1, top is +Z=z1 -> v0)
        # Check cross: (0,0,-dz) x (0,-dy,0) = (-dz*dy, 0, 0) = -X!
        self.add_quad(
            (x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1),
            (unx[0], unx[1]), (unx[0], unx[3]), (unx[2], unx[3]), (unx[2], unx[1]),
            nrm=(-1.0, 0.0, 0.0),
        )
        # +Y face (left side: viewer at +Y looking -Y -> left is +X=x1, right is -X=x0)
        # Check cross: (0,0,-dz) x (-dx,0,0) = (0, +dz*dx, 0) = +Y!
        self.add_quad(
            (x1, y1, z1), (x1, y1, z0), (x0, y1, z0), (x0, y1, z1),
            (upy[0], upy[1]), (upy[0], upy[3]), (upy[2], upy[3]), (upy[2], upy[1]),
            nrm=(0.0, 1.0, 0.0),
        )
        # -Y face (right side: viewer at -Y looking +Y -> left is -X=x0, right is +X=x1)
        # Check cross: (0,0,-dz) x (+dx,0,0) = (0, -dz*dx, 0) = -Y!
        self.add_quad(
            (x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1),
            (uny[0], uny[1]), (uny[0], uny[3]), (uny[2], uny[3]), (uny[2], uny[1]),
            nrm=(0.0, -1.0, 0.0),
        )
        # +Z top face (viewed from above facing -X when standing in front at +X: top of UV at -X=x0, bottom at +X=x1, left at -Y=y0, right at +Y=y1)
        # Check cross: ((x1,y0,z1)-(x0,y0,z1)) x ((x1,y1,z1)-(x0,y0,z1)) = (+dx,0,0) x (+dx,+dy,0) = (0,0,+dx*dy) = +Z!
        self.add_quad(
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
            (upz[0], upz[1]), (upz[0], upz[3]), (upz[2], upz[3]), (upz[2], upz[1]),
            nrm=(0.0, 0.0, 1.0),
        )
        if not skip_bottom:
            # -Z bottom face
            self.add_quad(
                (x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0),
                (unz[0], unz[1]), (unz[0], unz[3]), (unz[2], unz[3]), (unz[2], unz[1]),
                nrm=(0.0, 0.0, -1.0),
            )

    def add_bevel_frustum(self, pts_bot, pts_top, uv_sides, uv_top=None, uv_bot=None, cap_top=True, cap_bot=True):
        """Lofts a 4-cornered frustum/wedge between pts_bot[0..3] and pts_top[0..3] (ordered CCW when viewed from +Z)."""
        for i in range(4):
            j = (i + 1) % 4
            b0, b1 = pts_bot[i], pts_bot[j]
            t0, t1 = pts_top[i], pts_top[j]
            u0, v0, u1, v1 = uv_sides[i] if isinstance(uv_sides[0], tuple) else uv_sides
            # Outward side quad: (t0, b0, b1, t1) -> (b0-t0) x (b1-t0) points outward!
            self.add_quad(t0, b0, b1, t1, (u0, v0), (u0, v1), (u1, v1), (u1, v0))
        if cap_top:
            ut = uv_top or (uv_sides[0] if isinstance(uv_sides[0], tuple) else uv_sides)
            self.add_quad(pts_top[0], pts_top[1], pts_top[2], pts_top[3], (ut[0], ut[1]), (ut[0], ut[3]), (ut[2], ut[3]), (ut[2], ut[1]))
        if cap_bot:
            ub = uv_bot or (uv_sides[0] if isinstance(uv_sides[0], tuple) else uv_sides)
            self.add_quad(pts_bot[1], pts_bot[0], pts_bot[3], pts_bot[2], (ub[0], ub[1]), (ub[0], ub[3]), (ub[2], ub[3]), (ub[2], ub[1]))

    def add_tube(self, points, radii, uv_rect, segs=8, cap_start=True, cap_end=True):
        """Parallel-transport swept tube along `points` with circular or (rx, ry) elliptical radii."""
        n = len(points)
        tans = []
        for i in range(n):
            p_prev = points[max(0, i - 1)]
            p_next = points[min(n - 1, i + 1)]
            d = vsub(p_next, p_prev)
            tans.append(vnorm(d) if vlen(d) > 1e-6 else (0.0, 0.0, 1.0))

        u0, v0, u1, v1 = uv_rect
        _, bu, bv = frame_basis(tans[0])
        rings = []
        for i in range(n):
            ti = tans[i]
            bu_p = vsub(bu, vmul(ti, vdot(bu, ti)))
            if vlen(bu_p) < 1e-5:
                _, bu, bv = frame_basis(ti)
            else:
                bu = vnorm(bu_p)
                bv = vcross(ti, bu)

            rv = radii[i]
            rx, ry = rv if isinstance(rv, tuple) else (rv, rv)
            r_start = len(self.verts)
            rings.append(r_start)
            vc = v0 + (v1 - v0) * (i / max(1, n - 1))
            for k in range(segs + 1):
                ang = 2.0 * math.pi * (k % segs) / segs
                ca, sa = math.cos(ang), math.sin(ang)
                off = vadd(vmul(bu, ca * rx), vmul(bv, sa * ry))
                nrm = vnorm(vadd(vmul(bu, ca / max(rx, 1e-4)), vmul(bv, sa / max(ry, 1e-4))))
                self.verts.append(vadd(points[i], off))
                self.norms.append(nrm)
                uc = u0 + (u1 - u0) * (k / float(segs))
                self.st.append((uc, vc))

        for i in range(n - 1):
            rA, rB = rings[i], rings[i + 1]
            for k in range(segs):
                a, b, c, d = rA + k, rA + k + 1, rB + k + 1, rB + k
                # Check outward winding: bu x bv = ti -> a->d is +ti, a->b is +tangent_theta (ti x nrm),
                # so (d - a) x (b - a) = ti x (ti x nrm) = -nrm -> (b - a) x (c - a) = +nrm!
                self.tris += [(a, b, c), (a, c, d)]

        if cap_start:
            r0 = radii[0][0] if isinstance(radii[0], tuple) else radii[0]
            ic = len(self.verts)
            self.verts.append(vsub(points[0], vmul(tans[0], r0 * 0.35)))
            self.norms.append(vmul(tans[0], -1.0))
            self.st.append(((u0 + u1) * 0.5, v0))
            rA = rings[0]
            for k in range(segs):
                self.tris.append((ic, rA + k + 1, rA + k))

        if cap_end:
            rn = radii[-1][0] if isinstance(radii[-1], tuple) else radii[-1]
            ic = len(self.verts)
            self.verts.append(vadd(points[-1], vmul(tans[-1], rn * 0.35)))
            self.norms.append(tans[-1])
            self.st.append(((u0 + u1) * 0.5, v1))
            rB = rings[-1]
            for k in range(segs):
                self.tris.append((ic, rB + k, rB + k + 1))


# ==============================================================================
# 1. SCULPTED 3.5" 'LOL.BAT' FLOPPY DISK MESH
# ==============================================================================
def build_floppy_disk_mesh(half_w=4.65, half_h=4.90, half_t=0.28):
    """Builds a watertight 3D 3.5" floppy disk in local space:
      - Front face ('LOL.BAT' white paper label) faces -X (toward player in 1st-person idle hold).
      - Back face (brushed steel circular drive spindle hub + rear shutter) faces +X.
      - Top metal shutter edge is +Z; bottom label edge is -Z.
      - Classic 45-degree notched upper-right corner at (-half_w, +half_h) when viewing front (-X).
    """
    m = MeshPart("netsend_disk")
    W, H, T = half_w, half_h, half_t
    cham = W * 0.20  # iconic 3.5" floppy top-right 45-deg orientation notch

    # 5-vertex perimeter polygon in (y, z), ordered clockwise when looking +X at front (-X normal):
    # Top-left (+W, +H) -> Top-notch-start (-W+cham, +H) -> Notch-end (-W, +H-cham) -> Bot-right (-W, -H) -> Bot-left (+W, -H)
    perim = [
        (+W, +H),
        (-W + cham, +H),
        (-W, +H - cham),
        (-W, -H),
        (+W, -H),
    ]

    def uv_front(y, z):
        # Q1 [0.0..0.5, 0.0..0.5]: u=0 at +W (left), u=0.5 at -W (right); v=0 at +H (top), v=0.5 at -H (bottom)
        u = 0.008 + 0.484 * ((W - y) / (2.0 * W))
        v = 0.008 + 0.484 * ((H - z) / (2.0 * H))
        return (u, v)

    def uv_back(y, z):
        # Q2 [0.5..1.0, 0.0..0.5]: when flipped to view +X face, viewer-left is -Y (-W), viewer-right is +Y (+W)
        u = 0.508 + 0.484 * ((y + W) / (2.0 * W))
        v = 0.008 + 0.484 * ((H - z) / (2.0 * H))
        return (u, v)

    # Front face (-X normal): fan from center (0, 0)
    b_f = len(m.verts)
    m.verts.append((-T, 0.0, 0.0))
    m.norms.append((-1.0, 0.0, 0.0))
    m.st.append(uv_front(0.0, 0.0))
    for y, z in perim:
        m.verts.append((-T, y, z))
        m.norms.append((-1.0, 0.0, 0.0))
        m.st.append(uv_front(y, z))
    for i in range(len(perim)):
        j = (i + 1) % len(perim)
        # Check cross: perim[0]=(+W,+H), perim[1]=(-W+c,+H) -> v1=(0,W,H), v2=(0,-W+c,H)
        # v1 x v2 = (W*H - H*(-W+c), 0, 0) = (+, 0, 0) -> so (center, j, i) gives (-X) outward normal!
        m.tris.append((b_f, b_f + 1 + j, b_f + 1 + i))

    # Back face (+X normal): fan from center (0, 0)
    b_b = len(m.verts)
    m.verts.append((+T, 0.0, 0.0))
    m.norms.append((+1.0, 0.0, 0.0))
    m.st.append(uv_back(0.0, 0.0))
    for y, z in perim:
        m.verts.append((+T, y, z))
        m.norms.append((+1.0, 0.0, 0.0))
        m.st.append(uv_back(y, z))
    for i in range(len(perim)):
        j = (i + 1) % len(perim)
        m.tris.append((b_b, b_b + 1 + i, b_b + 1 + j))

    # Perimeter plastic rim edges (Q4 [0.52..0.98, 0.52..0.98])
    for i in range(len(perim)):
        j = (i + 1) % len(perim)
        y0, z0 = perim[i]
        y1, z1 = perim[j]
        # Edge tangent = (0, y1-y0, z1-z0); outward normal in YZ plane:
        # Since perim goes (+W,+H)->(-W,+H)->(-W,-H)->(+W,-H), dy = -2W on top (+Z outward): (-dz, +dy)? Wait:
        # Top edge: dy < 0, dz = 0 -> outward is (0, 0, +1) = (0, dz, -dy)! Check right edge: dy=0, dz<0 -> (0, -1, 0) = (0, dz, -dy)!
        en = vnorm((0.0, z1 - z0, -(y1 - y0)))
        m.add_quad(
            (-T, y0, z0), (-T, y1, z1), (+T, y1, z1), (+T, y0, z0),
            (0.54, 0.54), (0.96, 0.54), (0.96, 0.96), (0.54, 0.96),
            nrm=en,
        )

    # Raised 3D U-shaped Brushed Stainless-Steel Sliding Shutter wrapping top edge (Q3 [0.01..0.49, 0.51..0.99])
    # Spans y in [-W*0.64 .. +W*0.68], z in [+H*0.36 .. +H*1.015], standing proud at x = +/- (T + 0.055)
    sy0, sy1 = -W * 0.64, +W * 0.68
    sz0, sz1 = +H * 0.36, +H * 1.012
    st_x = T + 0.055
    m.add_box(
        -st_x, +st_x, sy0, sy1, sz0, sz1,
        uv_all=(0.02, 0.52, 0.48, 0.98),
        uv_nx=(0.01, 0.51, 0.49, 0.99),  # Front metal shutter w/ media window
        uv_px=(0.01, 0.51, 0.49, 0.99),  # Back metal shutter w/ media window!
        uv_pz=(0.04, 0.52, 0.46, 0.60),  # Top folded metal bridge
    )

    # Raised 3D Circular Brushed-Metal Spindle Hub Disc on the BACK (+X) face (centered at z = -H*0.18)
    hub_z = -H * 0.21
    hub_r = W * 0.34
    hub_x0, hub_x1 = T, T + 0.065
    segs_h = 14
    b_hc = len(m.verts)
    m.verts.append((hub_x1, 0.0, hub_z))
    m.norms.append((1.0, 0.0, 0.0))
    m.st.append(uv_back(0.0, hub_z))
    for k in range(segs_h):
        ang = 2.0 * math.pi * k / segs_h
        hy = hub_r * math.cos(ang)
        hz = hub_z + hub_r * math.sin(ang)
        m.verts.append((hub_x1, hy, hz))
        m.norms.append((1.0, 0.0, 0.0))
        m.st.append(uv_back(hy, hz))
    for k in range(segs_h):
        k2 = (k + 1) % segs_h
        m.tris.append((b_hc, b_hc + 1 + k, b_hc + 1 + k2))
    # Subtle bevel rim around spindle hub
    for k in range(segs_h):
        k2 = (k + 1) % segs_h
        a0 = 2.0 * math.pi * k / segs_h
        a1 = 2.0 * math.pi * k2 / segs_h
        y0, z0 = hub_r * math.cos(a0), hub_z + hub_r * math.sin(a0)
        y1, z1 = hub_r * math.cos(a1), hub_z + hub_r * math.sin(a1)
        m.add_quad(
            (hub_x1, y0, z0), (hub_x0, y0, z0), (hub_x0, y1, z1), (hub_x1, y1, z1),
            (0.05, 0.55), (0.05, 0.65), (0.25, 0.65), (0.25, 0.55),
        )

    return m


# ==============================================================================
# 2. ARTICULATED QUAKE RANGER GLOVED HAND FOR FLOPPY HOLD, SPIN & THROW
# ==============================================================================
def build_ranger_hand_pose(
    palm_center,
    fwd_dir,
    up_dir,
    finger_curls=(0.55, 0.58, 0.82, 0.88),
    finger_splay=(-9.0, -2.5, +3.5, +9.0),
    thumb_curl=0.48,
    thumb_abd=34.0,
    hand_scale=1.08,
    wrist_target=(11.0, -30.5, -21.5),
):
    """Builds fixed-topology articulated Quake Ranger gloved right hand + bronze knuckle guard +
    buckled gauntlet cuff + forearm extending cleanly past the bottom-right corner of the screen."""
    hp = MeshPart("netsend_hand")
    F = vnorm(fwd_dir)
    U_raw = vsub(up_dir, vmul(F, vdot(up_dir, F)))
    U = vnorm(U_raw)
    # Right hand: dorsal U, forward F -> thumb side T_side = U x F
    T_side = vnorm(vcross(U, F))
    S = hand_scale

    def to_w(fc, tc, uc):
        return vadd(palm_center, vadd(vmul(F, fc * S), vadd(vmul(T_side, tc * S), vmul(U, uc * S))))

    UV_LEATHER = (0.04, 0.04, 0.46, 0.46)
    UV_PALM    = (0.54, 0.04, 0.96, 0.46)
    UV_CUFF    = (0.02, 0.53, 0.48, 0.97)
    UV_KNUCKLE = (0.53, 0.53, 0.97, 0.73)
    UV_SLEEVE  = (0.53, 0.77, 0.97, 0.98)

    # 1. Sculpted Palm
    palm_pts = [to_w(-1.82, 0.0, -0.05), to_w(-0.72, 0.04, 0.0), to_w(+0.55, 0.06, 0.02), to_w(+1.60, 0.04, -0.02)]
    palm_rads = [(1.30 * S, 0.70 * S), (1.56 * S, 0.76 * S), (1.72 * S, 0.72 * S), (1.64 * S, 0.64 * S)]
    hp.add_tube(palm_pts, palm_rads, UV_LEATHER, segs=12)

    # Bronze 4-stud knuckle armor bar across dorsal knuckles
    kn_pts = [to_w(+1.36, +1.32, +0.56), to_w(+1.44, +0.44, +0.64), to_w(+1.42, -0.44, +0.63), to_w(+1.30, -1.28, +0.54)]
    hp.add_tube(kn_pts, [0.34 * S] * 4, UV_KNUCKLE, segs=8)

    # 2. 3-Jointed Opposable Thumb
    th_base = to_w(-0.52, +1.28, -0.20)
    th_dir0 = vnorm(vadd(vmul(F, 0.70), vadd(vmul(T_side, 0.64), vmul(U, -0.26))))
    th_bend_ax = vnorm(vsub(F, vmul(T_side, 0.45)))
    th_d1 = rot_axis(th_dir0, U, +(thumb_abd - 30.0))
    th_d2 = rot_axis(th_d1, th_bend_ax, -42.0 * thumb_curl)
    th_d3 = rot_axis(th_d2, th_bend_ax, -52.0 * thumb_curl)
    tp0 = to_w(-1.08, +0.90, -0.24)
    tp1 = th_base
    tp2 = vadd(tp1, vmul(th_d1, 1.12 * S))
    tp3 = vadd(tp2, vmul(th_d2, 0.96 * S))
    tp4 = vadd(tp3, vmul(th_d3, 0.76 * S))
    hp.add_tube([tp0, tp1, tp2, tp3, tp4], [0.62 * S, 0.54 * S, 0.44 * S, 0.39 * S, 0.32 * S], UV_LEATHER, segs=8)

    # 3. Four Individually Articulated 3-Phalanx Fingers
    t_offs = (+1.20, +0.42, -0.38, -1.12)
    l_mults = (0.96, 1.05, 0.96, 0.80)
    r_mults = (0.98, 1.02, 0.94, 0.85)
    for fi in range(4):
        cv = finger_curls[fi]
        sp = finger_splay[fi]
        lm = l_mults[fi] * S
        rm = r_mults[fi] * S
        mcp = to_w(+1.56 - 0.13 * abs(fi - 1.2), t_offs[fi], -0.02)
        f_dir0 = rot_axis(F, U, +sp)
        lat_ax = vnorm(vcross(U, f_dir0))  # +angle curls palmar (-U)
        a1 = 74.0 * cv
        a2 = 86.0 * min(1.12, cv * 1.05)
        a3 = 62.0 * min(1.12, cv * 0.95)
        d1 = rot_axis(f_dir0, lat_ax, a1)
        d2 = rot_axis(f_dir0, lat_ax, a1 + a2)
        d3 = rot_axis(f_dir0, lat_ax, a1 + a2 + a3)
        p1 = vadd(mcp, vmul(d1, 1.20 * lm))
        p2 = vadd(p1, vmul(d2, 0.90 * lm))
        p3 = vadd(p2, vmul(d3, 0.66 * lm))
        hp.add_tube([mcp, p1, p2, p3], [0.42 * rm, 0.38 * rm, 0.33 * rm, 0.27 * rm], UV_PALM if cv > 0.5 else UV_LEATHER, segs=8)

    # 4. Riveted Gauntlet Cuff & Forearm anchored to bottom-right screen exit
    w0 = to_w(-1.72, 0.0, -0.06)
    arm_vec = vsub(wrist_target, w0)
    arm_len = max(6.0, vlen(arm_vec))
    arm_dir = vnorm(arm_vec)
    wrist_dir0 = vnorm(vadd(vmul(F, -0.94), vadd(vmul(T_side, -0.12), vmul(U, -0.18))))
    cuff_dir = vnorm(vlerp(wrist_dir0, arm_dir, 0.58))

    w1 = vadd(w0, vmul(cuff_dir, 1.25 * S))
    w2 = vadd(w1, vmul(arm_dir, 2.85 * S))
    hp.add_tube([w0, w1, w2], [(1.40 * S, 1.02 * S), (1.60 * S, 1.20 * S), (1.84 * S, 1.42 * S)], UV_CUFF, segs=12)

    w3 = vlerp(w2, wrist_target, 0.48)
    w4 = wrist_target
    hp.add_tube([w2, w3, w4], [(1.78 * S, 1.40 * S), (2.10 * S, 1.72 * S), (2.42 * S, 1.98 * S)], UV_SLEEVE, segs=12)
    return hp


# ==============================================================================
# 3. VIEWMODEL BUILDER: progs/v_netsend.md3 (60 FRAMES: 0..59)
# ==============================================================================
def build_v_netsend_md3():
    """Builds progs/v_netsend.md3 (60 frames):
      - Frames  0-39: Seamless smug idle loop (holds LOL.BAT disk in lower-right, spins it between
                      fingers, flips 180 deg to show metal shutter & rear hub, flips back, tilts to
                      inspect LOL.BAT label, gives a smug double-nod, returns seamlessly to 0).
      - Frames 40-47: Wind-up & hard downward-forward throw at floor. Disk leaves hand at frame 44
                      (collapses zero-area off-screen from frame 44 onward so hand is empty).
      - Frames 48-53: Empty-hand follow-through & recovery.
      - Frames 54-59: Empty hand shakes out, dips to pocket, and slides a fresh LOL.BAT disk into view.
    """
    disk_base = build_floppy_disk_mesh(half_w=3.55, half_h=3.75, half_t=0.26)

    # Base idle hold pose in 90-deg H-FOV eye space (at x=15.6, screen spans y in [-15.6..+15.6], z in [-8.78..+8.78]):
    # Centered at (15.6, -7.2, -1.75) -> well right of crosshair (0,0), inside right border, above bottom HUD!
    REST_POS = (15.6, -7.20, -1.75)
    REST_ROLL = -4.0
    REST_PITCH = -8.0
    REST_YAW = 18.0

    # Right-hand anatomy: dorsal +U points (+X, -Y, +Z) so bronze knuckles are on outer-back,
    # 4 fingers curl from behind (+X) onto rear of disk, and thumb (+T_side = U x F) pinches front (-X) corner!
    REST_PALM = (16.65, -10.70, -5.85)
    REST_HFWD = vnorm((+0.06, +0.56, +0.82))
    REST_HUP  = vnorm((+0.76, -0.56, +0.33))
    REST_CURL = (0.38, 0.42, 0.72, 0.82)
    REST_TCURL = 0.42
    REST_TABD = 34.0
    HAND_SCALE = 0.88
    WRIST_EXIT = (12.8, -17.6, -11.6)

    disk_frames = []
    hand_frames = []
    frame_names = []

    for f in range(60):
        # Defaults = rest pose
        d_pos = REST_POS
        d_roll, d_pitch, d_yaw = REST_ROLL, REST_PITCH, REST_YAW
        d_spin = 0.0   # in-plane spin around disk's face normal (-X)
        d_flip = 0.0   # 180-deg flip around disk's vertical (+Z) axis to show back metal shutter
        d_scale = 1.0

        p_pos = REST_PALM
        h_fwd = REST_HFWD
        h_up = REST_HUP
        curls = REST_CURL
        tcurl = REST_TCURL
        tabd = REST_TABD
        w_exit = WRIST_EXIT

        if f <= 39:
            # --- SEAMLESS 40-FRAME IDLE LOOP (0..39) ---
            ph = 2.0 * math.pi * (f / 40.0)
            bob_y = 0.18 * math.sin(ph)
            bob_z = 0.22 * math.sin(ph * 2.0)

            if f <= 7:
                # 0..7: Relaxed smug idle hold, label LOL.BAT facing player clearly
                frame_names.append(f"idle_{f:02d}")
                d_pos = (REST_POS[0], REST_POS[1] + bob_y, REST_POS[2] + bob_z)
                d_yaw = REST_YAW + 2.0 * math.sin(ph)
                p_pos = (REST_PALM[0], REST_PALM[1] + bob_y * 0.8, REST_PALM[2] + bob_z * 0.8)
                tcurl = REST_TCURL + 0.05 * math.sin(ph * 2.0)

            elif f <= 22:
                # 8..22 (15 frames): Finger twirl/spin + 180-deg flip showing back metal shutter (pause 14..16), then flip back!
                frame_names.append(f"spin_{f:02d}")
                u = (f - 8) / 14.0  # 0.0 at f=8 .. 1.0 at f=22
                lift = math.sin(math.pi * u)

                if u < 0.36:
                    k = smootherstep(u / 0.36)
                    d_flip = 180.0 * k
                    d_spin = 360.0 * k
                elif u <= 0.64:
                    mid_w = math.sin(math.pi * (u - 0.36) / 0.28)
                    d_flip = 180.0 + 12.0 * mid_w
                    d_spin = 360.0 + 8.0 * mid_w
                else:
                    k = smootherstep((u - 0.64) / 0.36)
                    d_flip = 180.0 + 180.0 * k
                    d_spin = 360.0

                d_pos = (
                    REST_POS[0] - 0.35 * lift,
                    REST_POS[1] + 0.65 * lift + bob_y,
                    REST_POS[2] + 1.15 * lift + bob_z,
                )
                d_pitch = REST_PITCH - 4.5 * lift
                flick = math.sin(math.pi * min(1.0, u * 2.5)) if u < 0.4 else (math.sin(math.pi * (u - 0.6) * 2.5) if u > 0.6 else 0.0)
                curls = (0.20 + 0.16 * (1.0 - flick), 0.24 + 0.16 * (1.0 - flick), 0.70, 0.80)
                tcurl = 0.22 + 0.12 * (1.0 - lift)
                p_pos = (REST_PALM[0] + 0.15 * lift, REST_PALM[1] + 0.35 * lift + bob_y * 0.8, REST_PALM[2] + 0.45 * lift + bob_z * 0.8)

            elif f <= 33:
                # 23..33 (11 frames): Tilts disk in to inspect "LOL.BAT" label & gives two smug nods!
                frame_names.append(f"inspect_{f:02d}")
                u = (f - 23) / 10.0
                env_in = math.sin(math.pi * u) ** 0.75
                nod = math.sin(max(0.0, min(1.0, (u - 0.18) / 0.68)) * 2.0 * math.pi * 2.0) * env_in
                d_pos = (
                    REST_POS[0] - 0.95 * env_in,
                    REST_POS[1] + 1.15 * env_in + bob_y,
                    REST_POS[2] + 0.85 * env_in + 0.36 * nod + bob_z,
                )
                d_yaw = REST_YAW + 6.5 * env_in
                d_pitch = REST_PITCH - 5.0 * env_in + 6.0 * nod
                d_roll = REST_ROLL + 3.5 * env_in
                p_pos = (
                    REST_PALM[0] - 0.85 * env_in,
                    REST_PALM[1] + 1.05 * env_in + bob_y * 0.8,
                    REST_PALM[2] + 0.75 * env_in + 0.28 * nod + bob_z * 0.8,
                )
                h_fwd = vnorm(rot_y(REST_HFWD, 4.0 * nod))
                h_up = vnorm(rot_y(REST_HUP, 4.0 * nod))

            else:
                # 34..39: Smooth settle back to exact frame-0 rest pose
                frame_names.append(f"idle_{f:02d}")
                d_pos = (REST_POS[0], REST_POS[1] + bob_y, REST_POS[2] + bob_z)
                d_yaw = REST_YAW + 2.0 * math.sin(ph)
                p_pos = (REST_PALM[0], REST_PALM[1] + bob_y * 0.8, REST_PALM[2] + bob_z * 0.8)

        elif f <= 47:
            # --- WIND-UP & HARD THROW AT FLOOR (40..47; disk leaves hand at 44!) ---
            frame_names.append(f"throw_{f:02d}")
            if f <= 42:
                # 40..42: Draw arm up, back & right, cocking wrist like hurling a floppy/card at the floor
                k = smootherstep((f - 39) / 3.0)
                d_pos = vlerp(REST_POS, (13.6, -9.1, +0.85), k)
                d_roll = REST_ROLL - 22.0 * k
                d_pitch = REST_PITCH + 32.0 * k
                d_yaw = REST_YAW - 12.0 * k
                p_pos = vlerp(REST_PALM, (14.6, -11.4, -2.1), k)
                h_fwd = vnorm(vlerp(REST_HFWD, (-0.14, +0.48, +0.86), k))
                h_up = vnorm(vlerp(REST_HUP, (+0.68, -0.64, +0.36), k))
                curls = (0.48, 0.52, 0.78, 0.86)
                tcurl = 0.48
            elif f == 43:
                # 43: Explosive forward-and-downward whip! Disk right at releasing fingertips!
                d_pos = (18.4, -5.0, -3.4)
                d_roll, d_pitch, d_yaw = -34.0, +40.0, +16.0
                p_pos = (17.0, -7.8, -4.1)
                h_fwd = vnorm((+0.74, +0.40, -0.54))
                h_up = vnorm((+0.42, -0.46, +0.78))
                curls = (0.24, 0.28, 0.48, 0.58)
                tcurl = 0.22
                tabd = 44.0
            else:
                # 44..47: Disk has LEFT the hand (collapses zero-area below screen along throw vector)!
                # Empty open hand whips forward-down in full view in lower-right!
                u = (f - 44) / 3.0
                d_pos = (24.0, -4.0, -16.5)  # off-screen below bottom along downward throw path
                d_scale = 0.0                # exact zero-area degenerate tris -> 100% invisible!
                p_pos = vlerp((17.6, -6.6, -4.4), (16.8, -8.0, -5.3), smoothstep(u))
                h_fwd = vnorm(vlerp((+0.78, +0.38, -0.49), (+0.66, +0.42, -0.62), u))
                h_up = vnorm(vlerp((+0.42, -0.46, +0.78), (+0.52, -0.52, +0.68), u))
                curls = (0.08 + 0.08 * u, 0.10 + 0.08 * u, 0.14 + 0.10 * u, 0.18 + 0.12 * u)
                tcurl = 0.10 + 0.08 * u
                tabd = 48.0

        elif f <= 53:
            # --- EMPTY-HAND FOLLOW-THROUGH (48..53) ---
            frame_names.append(f"follow_{f:02d}")
            u = smootherstep((f - 47) / 6.0)
            d_pos = (24.0, -4.0, -16.5)
            d_scale = 0.0
            p_pos = vlerp((16.8, -8.0, -5.3), (16.2, -9.4, -4.6), u)
            h_fwd = vnorm(vlerp((+0.66, +0.42, -0.62), (+0.14, +0.54, +0.83), u))
            h_up = vnorm(vlerp((+0.52, -0.52, +0.68), (+0.72, -0.58, +0.38), u))
            curls = (0.16 + 0.20 * u, 0.18 + 0.22 * u, 0.24 + 0.30 * u, 0.30 + 0.34 * u)
            tcurl = 0.18 + 0.18 * u
            tabd = 48.0 - 12.0 * u

        else:
            # --- SHAKE-OUT & NEW DISK RELOAD (54..59) ---
            frame_names.append(f"reload_{f:02d}")
            if f in (54, 55):
                # Empty hand loose wrist shake-out clearly visible in lower-right!
                shake = +1.0 if f == 54 else -1.0
                d_pos = (24.0, -4.0, -16.5) if f == 54 else (14.6, -11.5, -14.5)
                d_scale = 0.0
                p_pos = (16.0, -9.4 + 0.78 * shake, -4.8 - 0.3 * abs(shake))
                h_fwd = vnorm(rot_x((+0.12, +0.54, +0.83), 18.0 * shake))
                h_up = vnorm(rot_x((+0.72, -0.58, +0.38), 18.0 * shake))
                curls = (0.28, 0.32, 0.46, 0.54) if f == 54 else (0.42, 0.46, 0.62, 0.70)
                tcurl = 0.30
            elif f == 56:
                # Hand dips toward pocket/belt; fresh LOL.BAT disk begins sliding up into view!
                d_pos = (14.9, -9.8, -7.2)
                d_roll, d_pitch, d_yaw = -12.0, +6.0, 12.0
                d_scale = 0.95
                p_pos = (15.9, -12.8, -10.2)
                h_fwd = vnorm((+0.06, +0.56, +0.82))
                h_up = vnorm((+0.76, -0.56, +0.33))
                curls = (0.40, 0.44, 0.74, 0.82)
                tcurl = 0.42
            elif f == 57:
                # Slides rapidly upward into view
                d_pos = (15.35, -8.0, -3.6)
                d_roll, d_pitch, d_yaw = -6.5, -3.5, 16.0
                d_scale = 1.0
                p_pos = (16.4, -11.4, -7.5)
            elif f == 58:
                # Crisp upward settle overshoot!
                d_pos = (15.65, -7.02, -1.42)
                d_roll, d_pitch, d_yaw = -3.2, -9.5, 19.0
                d_scale = 1.0
                p_pos = (16.7, -10.52, -5.52)
            else:
                # 59: Clean settle right onto REST_POS -> frame 0 seamless!
                d_pos = (15.6, -7.18, -1.70)
                d_roll, d_pitch, d_yaw = -3.9, -8.1, 18.2
                d_scale = 1.0
                p_pos = (16.65, -10.66, -5.80)

        # Transform disk vertices & normals for frame f
        dv, dn = [], []
        for p, n in zip(disk_base.verts, disk_base.norms):
            if d_scale <= 1e-6:
                dv.append(d_pos)
                dn.append((-1.0, 0.0, 0.0))
            else:
                q = vmul(p, d_scale)
                qn = n
                if d_spin:
                    q = rot_x(q, d_spin)
                    qn = rot_x(qn, d_spin)
                if d_flip:
                    q = rot_z(q, d_flip)
                    qn = rot_z(qn, d_flip)
                q = rot_z(rot_y(rot_x(q, d_roll), d_pitch), d_yaw)
                qn = vnorm(rot_z(rot_y(rot_x(qn, d_roll), d_pitch), d_yaw))
                dv.append(vadd(q, d_pos))
                dn.append(qn)
        disk_frames.append((dv, dn))

        # Build articulated hand for frame f
        hm = build_ranger_hand_pose(
            palm_center=p_pos,
            fwd_dir=h_fwd,
            up_dir=h_up,
            finger_curls=curls,
            thumb_curl=tcurl,
            thumb_abd=tabd,
            hand_scale=HAND_SCALE,
            wrist_target=w_exit,
        )
        hand_frames.append((hm.verts, hm.norms))
        if f == 0:
            hand_tris = hm.tris
            hand_st = hm.st

    surfaces = [
        dict(name="netsend_disk", shader="progs/netsend_disk", tris=disk_base.tris, st=disk_base.st, frames=disk_frames),
        dict(name="netsend_hand", shader="progs/netsend_hand", tris=hand_tris, st=hand_st, frames=hand_frames),
    ]
    return dict(name="v_netsend", surfaces=surfaces, nframes=60), frame_names


# ==============================================================================
# 4. WORLD DEPLOYABLE PC: progs/netsend_pc.md3 (50 FRAMES: 0..49)
# ==============================================================================
# Exact antenna tip rest positions in PC world space (origin on floor at base center, +X forward):
ANTENNA_BASES_AND_TIPS = [
    # 0: Top-Left Rabbit Ear
    ((+1.2, +2.0, 55.0), (+2.6, +10.4, 62.8)),
    # 1: Top-Right Rabbit Ear
    ((+1.2, -2.0, 55.0), (+2.6, -10.4, 62.8)),
    # 2: Left Case Whip
    ((-1.0, +12.3, 28.2), (+0.6, +14.8, 50.2)),
    # 3: Right Case Whip
    ((-1.0, -12.3, 28.2), (+0.6, -14.8, 50.2)),
]


def _build_pc_static_parts():
    """Builds all component MeshParts of the early-90s Beige CRT PC & School Stand in rest pose:
      - Footprint: ~29 x 30 units centered squarely on (0, 0) on the floor (z = 0) so spinning yaw has zero wobble!
      - Total height: ~63.2 Quake units to bright antenna tips (55.2 to top of CRT bezel).
      - Front of CRT screen, keyboard, 3.5" floppy drive, and LEDs face +X.
    """
    UV_CASE_FRONT = (0.008, 0.008, 0.492, 0.242)
    UV_CASE_REAR  = (0.508, 0.008, 0.992, 0.120)
    UV_CASE_METAL = (0.508, 0.132, 0.992, 0.246)
    UV_CRT_FRONT  = (0.008, 0.258, 0.492, 0.618)
    UV_CRT_BACK   = (0.508, 0.258, 0.992, 0.618)
    UV_KEY_SHELL  = (0.318, 0.632, 0.494, 0.806)
    UV_STAND      = (0.508, 0.632, 0.774, 0.806)
    UV_SURGE      = (0.786, 0.632, 0.992, 0.712)
    UV_DARK_HW    = (0.786, 0.724, 0.992, 0.806)
    UV_CORD_BLK   = (0.010, 0.820, 0.240, 0.992)
    UV_CORD_GRY   = (0.260, 0.820, 0.490, 0.992)
    UV_CORD_BNC   = (0.510, 0.820, 0.740, 0.992)
    UV_CHROME     = (0.760, 0.820, 0.990, 0.992)

    # --- A. School Computer Stand / Pedestal Desk Base + Cables + Desktop Case ('stand_and_case') ---
    base_part = MeshPart("stand_case")

    # 4 sturdy rubberized floor feet + wide symmetrical H-frame floor skids (z = 0.0 .. 2.4)
    for sy in (-1.0, +1.0):
        # Left & right floor skids (x: -11.5..+11.5, y: sy*10.2..sy*13.0, z: 0..2.2)
        y_in, y_out = (sy * 10.2, sy * 13.0) if sy > 0 else (sy * 13.0, sy * 10.2)
        base_part.add_box(-11.5, +11.5, y_in, y_out, 0.4, 2.2, UV_STAND)
        for sx in (-9.6, +9.6):
            base_part.add_box(sx - 1.6, sx + 1.6, y_in - 0.2, y_out + 0.2, 0.0, 0.6, UV_DARK_HW)
        # Sturdy vertical steel side legs rising to desktop shelf (z = 2.2 .. 22.4)
        base_part.add_box(-9.2, +6.8, y_in + 0.3, y_out - 0.3, 2.2, 22.4, UV_STAND, skip_bottom=True)

    # Lower equipment shelf (z = 6.2 .. 7.6) + modesty rear cross-panel (z = 7.6 .. 21.8)
    base_part.add_box(-9.0, +6.6, -10.4, +10.4, 6.2, 7.6, UV_STAND)
    base_part.add_box(-9.2, -7.8, -10.4, +10.4, 7.6, 21.8, UV_STAND, skip_bottom=True)

    # Beige 6-outlet Surge Protector Power Strip sitting on lower shelf
    base_part.add_box(-2.5, +5.5, -8.6, -4.2, 7.6, 9.2, UV_SURGE, uv_pz=UV_SURGE, skip_bottom=True)

    # Top desk surface supporting Desktop Case (z = 21.8 .. 23.2) + cantilevered front Keyboard Tray (z = 20.4 .. 21.8)
    base_part.add_box(-11.8, +8.4, -13.2, +13.2, 21.8, 23.2, UV_STAND)
    # Side keyboard tray brackets + keyboard shelf
    for sy in (-1.0, +1.0):
        yb0, yb1 = (sy * 9.8, sy * 11.0) if sy > 0 else (sy * 11.0, sy * 9.8)
        base_part.add_box(+5.0, +14.0, yb0, yb1, 20.2, 21.8, UV_DARK_HW)
    base_part.add_box(+5.2, +14.2, -11.2, +11.2, 20.6, 21.8, UV_STAND)

    # Horizontal 486 Beige Desktop Pizza-Box Case (x: -11.2..+7.8, y: -12.0..+12.0, z: 23.2..32.2)
    base_part.add_box(
        -11.2, +7.0, -12.0, +12.0, 23.2, 32.2,
        uv_all=UV_CASE_METAL,
        uv_nx=UV_CASE_REAR,
        skip_bottom=True,
    )
    # Moulded plastic front faceplate on Desktop Case (x: +7.0..+7.9)
    base_part.add_box(
        +7.0, +7.9, -12.2, +12.2, 23.1, 32.3,
        uv_all=UV_CRT_BACK,
        uv_px=UV_CASE_FRONT,
    )
    # Side antenna mounting blocks on left & right of Desktop Case
    for sy in (-1.0, +1.0):
        yb0, yb1 = (sy * 12.0, sy * 12.8) if sy > 0 else (sy * 12.8, sy * 12.0)
        base_part.add_box(-2.2, +0.2, yb0, yb1, 26.8, 29.2, UV_DARK_HW)

    # Chunky Mechanical Keyboard Sloped Wedge Base on front tray (x: +6.0..+13.8, y: -10.2..+10.2, z: 21.8..23.8)
    kb_bot = [(+6.0, -10.2, 21.8), (+13.8, -10.2, 21.8), (+13.8, +10.2, 21.8), (+6.0, +10.2, 21.8)]
    kb_top = [(+6.2, -9.9,  24.1), (+13.5, -9.9,  22.9), (+13.5, +9.9,  22.9), (+6.2, +9.9,  24.1)]
    base_part.add_bevel_frustum(kb_bot, kb_top, UV_KEY_SHELL, uv_top=UV_KEY_SHELL, cap_bot=False)

    # Trailing Cables to Floor (kept strictly inside r <= 14.8 so yaw rotation stays inside 32x32 footprint!)
    # 1. Thick Black AC Power Cord from rear PSU (-11.2, -6.5, 27.5) down to surge strip & floor loop
    ac_pts = [
        (-11.0, -6.5, 27.5),
        (-12.8, -7.2, 21.0),
        (-12.4, -8.0, 12.5),
        (-9.8,  -8.4, 4.2),
        (-6.2,  -9.2, 0.55),
        (-1.0,  -9.0, 0.50),
        (+3.2,  -7.2, 3.8),
        (+3.5,  -6.4, 8.2),
    ]
    base_part.add_tube(ac_pts, [0.46] * len(ac_pts), UV_CORD_BLK, segs=6)

    # 2. BNC 10BASE2 Coax Network Cable trailing from rear NIC (-11.0, +5.2, 26.2) onto floor coil
    bnc_pts = [
        (-11.0, +5.2, 26.2),
        (-12.9, +6.6, 18.5),
        (-12.5, +9.2, 8.5),
        (-10.2, +11.4, 0.50),
        (-4.5,  +13.2, 0.48),
        (+2.5,  +12.8, 0.48),
        (+7.2,  +10.5, 0.48),
    ]
    base_part.add_tube(bnc_pts, [0.36] * len(bnc_pts), UV_CORD_BNC, segs=6)

    # 3. Coiled Putty-Grey PS/2 Keyboard Cable from front/side of keyboard around to rear of case
    ps2_pts = [
        (+6.2, +6.5, 23.3),
        (+4.8, +12.5, 23.6),
        (-1.5, +13.1, 24.0),
        (-8.2, +12.6, 24.8),
        (-11.2, +2.4, 26.0),
    ]
    base_part.add_tube(ps2_pts, [0.34] * len(ps2_pts), UV_CORD_GRY, segs=6)

    # --- B. 8 Individually Animated 3D Sculpted Keycap Clusters ('key_clusters') ---
    # Keyboard plane slopes from (x=6.5, z=24.05) down to (x=13.2, z=22.95), y in [-9.2 .. +9.2]
    # Note: viewer facing +X from front sees -Y on LEFT (ESC/QWER) and +Y on RIGHT (ENTER/NUMPAD)!
    key_specs = [
        # (x0, x1, y0, y1, u0, v0, u1, v1)
        (6.5,  8.0, -9.2, -1.0, 0.005, 0.635, 0.160, 0.662),  # 0: ESC + Function row left
        (6.5,  8.0, -0.4, +8.8, 0.160, 0.635, 0.308, 0.662),  # 1: Function row right
        (8.2,  9.7, -9.2, -0.6, 0.005, 0.665, 0.160, 0.715),  # 2: QWER / Number left
        (8.2,  9.7, -0.1, +9.0, 0.160, 0.665, 0.308, 0.715),  # 3: UIOP / Backspace right
        (9.9, 11.4, -9.2, -0.8, 0.005, 0.718, 0.155, 0.768),  # 4: ASDF / ZXCV home-left
        (9.9, 11.4, -0.3, +5.8, 0.155, 0.718, 0.245, 0.768),  # 5: JKL; home-right
        (9.9, 11.6, +6.2, +9.2, 0.248, 0.718, 0.308, 0.775),  # 6: Big L-shaped ENTER key!
        (11.6,13.1, -6.2, +5.6, 0.065, 0.778, 0.240, 0.806),  # 7: Long SPACEBAR!
    ]
    key_parts = []
    for (kx0, kx1, ky0, ky1, ku0, kv0, ku1, kv1) in key_specs:
        kp = MeshPart("key")
        # Base z on sloped keyboard top
        def kz(x):
            t = (x - 6.2) / (13.5 - 6.2)
            return 24.05 - 1.15 * t
        zb0, zb1 = kz(kx0) - 0.3, kz(kx1) - 0.3
        zt0, zt1 = kz(kx0) + 0.65, kz(kx1) + 0.65
        ins = 0.18
        pts_b = [(kx0, ky0, zb0), (kx1, ky0, zb1), (kx1, ky1, zb1), (kx0, ky1, zb0)]
        pts_t = [(kx0 + ins, ky0 + ins, zt0), (kx1 - ins, ky0 + ins, zt1), (kx1 - ins, ky1 - ins, zt1), (kx0 + ins, ky1 - ins, zt0)]
        kp.add_bevel_frustum(pts_b, pts_t, UV_KEY_SHELL, uv_top=(ku0, kv0, ku1, kv1), cap_bot=False)
        key_parts.append(kp)

    # --- C. Deep Rounded-Back Early-90s CRT Monitor (pivots around neck (x=-0.8, y=0, z=33.8)) ---
    crt_part = MeshPart("crt_monitor")
    # Swivel tilt pedestal base (z = 32.1 .. 34.8)
    crt_part.add_tube([(-0.8, 0.0, 32.0), (-0.8, 0.0, 33.6), (-0.4, 0.0, 34.8)], [(5.6, 6.2), (4.2, 4.6), (5.2, 5.8)], UV_CRT_BACK, segs=12)

    # Thick Front CRT Bezel Collar (x: +4.6..+8.4, y: -11.6..+11.6, z: 34.5..55.0)
    bz_back = [(+4.6, -11.6, 34.5), (+4.6, +11.6, 34.5), (+4.6, +11.6, 55.0), (+4.6, -11.6, 55.0)]
    bz_frnt = [(+8.4, -11.2, 34.8), (+8.4, +11.2, 34.8), (+8.4, +11.2, 54.7), (+8.4, -11.2, 54.7)]
    # Build main front bezel box + tapered deep CRT rear shell!
    crt_part.add_box(
        +4.4, +8.4, -11.5, +11.5, 34.6, 55.0,
        uv_all=UV_CRT_BACK,
        uv_px=UV_CRT_FRONT,
    )
    # Recessed inner bezel frame around screen glass (x: +8.4 -> +8.05 inset lip)
    # Multi-stage deep rounded CRT rear housing tapering from x=+4.4 back to x=-12.6!
    rear_rings = [
        (+4.4, 11.3, 34.8, 54.8, 0.26),
        (+0.5, 10.6, 35.4, 54.0, 0.36),
        (-4.5,  9.2, 36.6, 52.4, 0.46),
        (-9.2,  7.0, 38.6, 49.8, 0.54),
        (-12.4, 4.4, 41.0, 47.2, 0.60),
    ]
    for i in range(len(rear_rings) - 1):
        xa, ya, za0, za1, va = rear_rings[i]
        xb, yb, zb0, zb1, vb = rear_rings[i + 1]
        # Top slope (+Z)
        crt_part.add_quad(
            (xb, -yb, zb1), (xa, -ya, za1), (xa, +ya, za1), (xb, +yb, zb1),
            (0.52, va), (0.52, vb), (0.98, vb), (0.98, va),
        )
        # Bottom slope (-Z)
        crt_part.add_quad(
            (xa, -ya, za0), (xb, -yb, zb0), (xb, +yb, zb0), (xa, +ya, za0),
            (0.52, va), (0.52, vb), (0.98, vb), (0.98, va),
        )
        # Left slope (+Y)
        crt_part.add_quad(
            (xa, +ya, za1), (xa, +ya, za0), (xb, +yb, zb0), (xb, +yb, zb1),
            (0.52, va), (0.52, vb), (0.98, vb), (0.98, va),
        )
        # Right slope (-Y)
        crt_part.add_quad(
            (xb, -yb, zb1), (xb, -yb, zb0), (xa, -ya, za0), (xa, -ya, za1),
            (0.52, va), (0.52, vb), (0.98, vb), (0.98, va),
        )
    # Rear CRT electron-gun neck cap at x = -12.4
    xr, yr, zr0, zr1, _ = rear_rings[-1]
    crt_part.add_quad(
        (xr, +yr, zr1), (xr, +yr, zr0), (xr, -yr, zr0), (xr, -yr, zr1),
        (0.58, 0.44), (0.58, 0.58), (0.92, 0.58), (0.92, 0.44),
        nrm=(-1.0, 0.0, 0.0),
    )
    # Thick VGA signal cable looping from CRT back (-9.5, -2.5, 39.2) into Desktop Case rear (-11.2, +0.5, 27.2)
    crt_part.add_tube(
        [(-9.2, -2.2, 39.5), (-12.8, -1.5, 35.8), (-13.2, -0.4, 30.8), (-11.0, +0.4, 27.2)],
        [0.42, 0.42, 0.42, 0.46], UV_CORD_GRY, segs=6,
    )
    # Chrome rabbit-ear dipole base block atop CRT monitor (x: +0.2..+2.4, y: -2.8..+2.8, z: 54.9..55.8)
    crt_part.add_box(+0.2, +2.4, -2.8, +2.8, 54.9, 55.8, UV_DARK_HW)

    # --- D. Dedicated High-Res Curved CRT Screen Surface ('netsend_screen', 4x3 grid = 24 tris) ---
    # Spans y in [-9.6 .. +9.6] (19.2 units wide!) and z in [38.2 .. 52.6] (14.4 units tall!) at x = +8.45..+8.85
    # Viewer stands at +X looking -X: left of text (u=0) is -Y (-9.6), right of text (u=1) is +Y (+9.6), top (v=0) is +Z (52.6)!
    scr_part = MeshPart("netsend_screen")
    NX_S, NZ_S = 4, 3
    s_grid = []
    for iz in range(NZ_S + 1):
        vf = iz / float(NZ_S)  # 0 at top (+Z), 1 at bottom (-Z)
        zc = 52.6 - 14.4 * vf
        nz_n = (vf - 0.5) * 2.0
        row = []
        for iy in range(NX_S + 1):
            uf = iy / float(NX_S)  # 0 at -Y (left), 1 at +Y (right)
            yc = -9.6 + 19.2 * uf
            ny_n = (uf - 0.5) * 2.0
            # Authentic subtle convex CRT glass curvature pushed cleanly ahead of x=8.40 bezel (zero Z-fighting!)
            bulge = 0.38 * max(0.0, 1.0 - 0.65 * (ny_n * ny_n + nz_n * nz_n))
            xc = 8.64 + bulge
            nrm = vnorm((1.0, 0.08 * ny_n, -0.08 * nz_n))
            idx = len(scr_part.verts)
            scr_part.verts.append((xc, yc, zc))
            scr_part.norms.append(nrm)
            scr_part.st.append((uf, vf))
            row.append(idx)
        s_grid.append(row)
    for iz in range(NZ_S):
        for iy in range(NX_S):
            a = s_grid[iz][iy]         # top-left (-Y, +Z)
            b = s_grid[iz + 1][iy]     # bot-left (-Y, -Z)
            c = s_grid[iz + 1][iy + 1] # bot-right (+Y, -Z)
            d = s_grid[iz][iy + 1]     # top-right (+Y, +Z)
            # Check cross: (b - a) = (0, 0, -dz), (c - a) = (0, +dy, -dz) -> (b-a) x (c-a) = (+dz*dy, 0, 0) = +X outward!
            scr_part.tris += [(a, b, c), (a, c, d)]

    # --- E. Half-Inserted 3.5" 'LOL.BAT' Floppy Disk in Desktop Case Slot! ---
    # Desktop floppy slot is on the right half of the front panel (+Y side when facing +X: y ~ +4.8, z ~ 28.0, x ~ +7.9)
    # Wait: check UV_CASE_FRONT on +X face: u=0 is at y=-12.2, u=0.5 is at y=+12.2; floppy bay in atlas is x=272..492 of 512 -> u_frac=0.53..0.96 -> y in [+0.8 .. +11.2], slot at y_atlas=112/256 -> z = 32.3 - 9.2*(112/256) = 28.25!
    # Let's place the half-inserted LOL.BAT disk right inside that exact moulded slot (y = +5.9, z = 28.25), flat horizontal, label facing UP (+Z)!
    slot_disk_raw = build_floppy_disk_mesh(half_w=2.85, half_h=3.00, half_t=0.20)
    slot_disk = MeshPart("slot_disk")
    # Rotate raw disk (front=-X, shutter=+Z) so front ('LOL.BAT') faces UP (+Z) and shutter (-X of inserted end) goes into -X slot!
    # Check rot_y(p, -90): (-T, 0, 0) -> (0, 0, -T)? Wait: rot_y((-1,0,0), -90): cos=0, sin=-1 -> (0, 0, -1).
    # rot_y((-1,0,0), +90): cos=0, sin=+1 -> (0, 0, +1) (+Z UP = LOL.BAT label on top!), and shutter (+Z -> (0,0,+1)) goes to (+1,0,0) -> then rot_z(180) puts shutter going INTO slot (-X) and LOL.BAT sticking OUT (+X) right where you can read it!
    def xf_slot_p(p):
        q = rot_z(rot_y(p, +90.0), 180.0)
        return (q[0] + 8.35, q[1] + 5.95, q[2] + 28.25)

    def xf_slot_n(n):
        return rot_z(rot_y(n, +90.0), 180.0)

    slot_disk.append(slot_disk_raw, xf_slot_p, xf_slot_n)

    # Also build the angled Floor-Impact Floppy Disk used in Materialize frames 0..4!
    floor_disk = MeshPart("floor_disk")

    def xf_floor_p(p):
        # Tilted 22 deg from vertical, embedded slightly in floor at z=0, facing +X!
        q = rot_y(rot_z(p, 180.0), -22.0)
        return (q[0], q[1], q[2] + 4.2)

    def xf_floor_n(n):
        return rot_y(rot_z(n, 180.0), -22.0)

    floor_disk.append(slot_disk_raw, xf_floor_p, xf_floor_n)

    return {
        "base": base_part,
        "keys": key_parts,
        "crt": crt_part,
        "screen": scr_part,
        "slot_disk": slot_disk,
        "floor_disk": floor_disk,
        "uv_chrome": UV_CHROME,
    }


def _build_antennas_and_leds_for_frame(ant_bends, pwr_on, drv_on, sq_xy, sq_z, slump_pitch, slump_roll, crt_jitter):
    """Builds dynamic 4 chrome whip/rabbit-ear antennas (into pc_body surface) + emissive LEDs & bright antenna tips
    (into netsend_leds surface) with 100% constant vertex/triangle topology across all 50 frames."""
    ant_mesh = MeshPart("antennas")
    led_mesh = MeshPart("leds")

    UV_CHROME = (0.760, 0.820, 0.990, 0.992)
    UV_LED_GRN = (0.04, 0.04, 0.46, 0.46)
    UV_LED_AMB = (0.54, 0.04, 0.96, 0.46)
    UV_LED_RED = (0.04, 0.54, 0.46, 0.96)
    UV_TIP_CYN = (0.54, 0.54, 0.96, 0.96)

    def apply_crt_xf(p):
        # CRT pivots around neck (-0.8, 0.0, 33.8), then global squash/stretch around (0,0,0)
        piv = (-0.8, 0.0, 33.8)
        d = vsub(p, piv)
        d = rot_x(d, crt_jitter[0] + slump_roll)
        d = rot_y(d, crt_jitter[1] + slump_pitch)
        d = rot_z(d, crt_jitter[2])
        w = vadd(piv, vadd(d, (crt_jitter[3], crt_jitter[4], crt_jitter[5])))
        return (w[0] * sq_xy, w[1] * sq_xy, w[2] * sq_z)

    def apply_case_xf(p):
        piv = (0.0, 0.0, 22.0)
        d = vsub(p, piv)
        d = rot_y(rot_x(d, slump_roll * 0.35), slump_pitch * 0.35)
        w = vadd(piv, d)
        return (w[0] * sq_xy, w[1] * sq_xy, w[2] * sq_z)

    # 4 Articulated 5-segment Chrome Antennas + Bright Glowing Tip Spheres
    for ai, (b_pt, t_pt) in enumerate(ANTENNA_BASES_AND_TIPS):
        bend_x, bend_y, bend_z = ant_bends[ai]
        xf_fn = apply_crt_xf if ai < 2 else apply_case_xf
        pts = []
        for s in range(5):
            u = s / 4.0
            # Quadratic cantilever beam deflection curve (u^2)
            raw_p = (
                b_pt[0] + (t_pt[0] - b_pt[0]) * u + bend_x * (u * u),
                b_pt[1] + (t_pt[1] - b_pt[1]) * u + bend_y * (u * u),
                b_pt[2] + (t_pt[2] - b_pt[2]) * u + bend_z * (u * u),
            )
            pts.append(xf_fn(raw_p))
        rads = [0.36 * sq_xy, 0.30 * sq_xy, 0.24 * sq_xy, 0.19 * sq_xy, 0.14 * sq_xy]
        ant_mesh.add_tube(pts, rads, UV_CHROME, segs=6, cap_end=False)

        # Bright electric cyan-white ball tip on antenna end!
        tip_c = pts[-1]
        tan_t = vnorm(vsub(pts[-1], pts[-2])) if vlen(vsub(pts[-1], pts[-2])) > 1e-5 else (0.0, 0.0, 1.0)
        tr = max(0.05, 0.62 * max(sq_xy, sq_z))
        led_mesh.add_tube(
            [vsub(tip_c, vmul(tan_t, tr * 0.85)), tip_c, vadd(tip_c, vmul(tan_t, tr * 0.85))],
            [tr * 0.55, tr, tr * 0.55],
            UV_TIP_CYN, segs=8,
        )

    # Emissive LEDs (recessed -0.7 units inside opaque bezel when OFF, proud +0.08 units in front when ON!)
    # 1. Desktop Case Green Power LED (near PWR button: y = -1.8, z = 29.5)
    px_pwr = 7.96 if pwr_on else 7.20
    p0 = apply_case_xf((px_pwr - 0.1, -2.1, 29.2))
    p1 = apply_case_xf((px_pwr,       -1.5, 29.8))
    led_mesh.add_box(min(p0[0], p1[0]), max(p0[0], p1[0]) + 0.05, -2.1 * sq_xy, -1.5 * sq_xy, p0[2], p1[2], UV_LED_GRN)

    # 2. Desktop Case Amber Floppy Drive Activity LED (under floppy slot: y = +2.35, z = 26.85)
    px_drv = 7.96 if drv_on else 7.20
    d0 = apply_case_xf((px_drv - 0.1, +2.00, 26.62))
    d1 = apply_case_xf((px_drv,       +2.75, 27.08))
    led_mesh.add_box(min(d0[0], d1[0]), max(d0[0], d1[0]) + 0.05, +2.00 * sq_xy, +2.75 * sq_xy, d0[2], d1[2], UV_LED_AMB)

    # 3. CRT Monitor Green Power LED (bottom-right of bezel chin: y = +7.2, z = 35.8)
    mx_pwr = 8.46 if pwr_on else 7.60
    m0 = apply_crt_xf((mx_pwr - 0.1, +6.9, 35.55))
    m1 = apply_crt_xf((mx_pwr,       +7.5, 36.05))
    led_mesh.add_box(min(m0[0], m1[0]), max(m0[0], m1[0]) + 0.05, m0[1], m1[1], m0[2], m1[2], UV_LED_GRN)

    # 4. Surge-Protector Red Rocker Switch LED on lower shelf
    sx_on = 9.28 if pwr_on else 8.40
    led_mesh.add_box((-2.1) * sq_xy, (-1.4) * sq_xy, (-7.8) * sq_xy, (-7.1) * sq_xy, (sx_on - 0.2) * sq_z, sx_on * sq_z, UV_LED_RED)

    return ant_mesh, led_mesh


def build_netsend_pc_md3():
    """Builds progs/netsend_pc.md3 (50 vertex frames: 0..49):
      - Frames  0-9 : Materialize (disk stuck in floor -> PC pops up w/ cartoon stretch & squash overshoot).
      - Frames 10-19: Boot (Power LED turns on, CRT degauss shudder, floppy LED flickers).
      - Frames 20-39: Active loop (8 key clusters visibly hammered by ghosts, CRT hum/jitter, 4 antennas twitch).
      - Frames 40-49: Shutdown (LEDs go dark, floppy ejects slightly, CRT & case slump, antennas droop).
    """
    parts = _build_pc_static_parts()
    base_p = parts["base"]
    key_ps = parts["keys"]
    crt_p = parts["crt"]
    scr_p = parts["screen"]
    slot_d = parts["slot_disk"]
    floor_d = parts["floor_disk"]

    # Pre-build frame-0 dynamic antenna/LED parts to lock static UV & triangle topology
    ant0, led0 = _build_antennas_and_leds_for_frame([(0, 0, 0)] * 4, False, False, 1.0, 1.0, 0.0, 0.0, (0, 0, 0, 0, 0, 0))

    # Assemble static UV & triangle lists for the 4 surfaces of netsend_pc.md3:
    #   1. netsend_pc_body : base + 8 keys + crt + 4 antennas (shader: progs/netsend_pc_body)
    #   2. netsend_disk    : half-inserted slot disk + floor materialize disk (shader: progs/netsend_disk)
    #   3. netsend_screen  : dedicated high-res curved CRT screen face (shader: progs/netsend_scr_loop; swappable via .skin!)
    #   4. netsend_leds    : unlit green/amber/red LEDs & bright antenna tips (shader: progs/netsend_leds)
    body_st, body_tris = [], []
    vo = 0
    for sp in [base_p] + key_ps + [crt_p, ant0]:
        body_st += sp.st
        body_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    dsk_st = list(slot_d.st) + list(floor_d.st)
    vo_d = len(slot_d.verts)
    dsk_tris = list(slot_d.tris) + [(a + vo_d, b + vo_d, c + vo_d) for (a, b, c) in floor_d.tris]

    body_frames, dsk_frames, scr_frames, led_frames = [], [], [], []
    frame_names = []

    # Materialize squash & stretch schedule for frames 0..9: (sq_xy, sq_z, floor_disk_scale, floor_disk_sink_z)
    mat_sched = [
        (0.14, 0.02, 1.00,  0.0),   # 0: Lone LOL.BAT disk stuck in floor; PC hidden compressed at base
        (0.36, 0.14, 0.96, -0.8),   # 1: Bulging out of floor disk
        (0.60, 0.38, 0.85, -2.0),   # 2: Rising fast
        (0.80, 0.72, 0.60, -3.4),   # 3: Rising
        (0.86, 1.02, 0.00, -4.0),   # 4: Reaching full height, floor disk swallowed cleanly inside stand
        (0.87, 1.15, 0.00, -4.0),   # 5: Cartoon STRETCH overshoot!
        (0.94, 1.08, 0.00, -4.0),   # 6: Peak pop
        (1.07, 0.92, 0.00, -4.0),   # 7: Heavy SQUASH settle onto floor!
        (0.99, 1.02, 0.00, -4.0),   # 8: Crisp rebound
        (1.00, 1.00, 0.00, -4.0),   # 9: Settled upright, ready to boot
    ]

    for f in range(50):
        sq_xy, sq_z = 1.0, 1.0
        fd_sc, fd_z = 0.0, -4.0
        pwr_on = False
        drv_on = False
        slump_pitch = 0.0
        slump_roll = 0.0
        crt_jit = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)  # (roll, pitch, yaw, dx, dy, dz)
        key_dep = [0.0] * 8
        ant_bends = [(0.0, 0.0, 0.0)] * 4
        slot_eject_dx = 0.0

        if f <= 9:
            # --- 0..9: MATERIALIZE ---
            frame_names.append(f"mat_{f:02d}")
            sq_xy, sq_z, fd_sc, fd_z = mat_sched[f]
            # Antennas whip down during upward acceleration (1..5), flare up on squash (7), settle (9)
            whip = -3.2 if 2 <= f <= 5 else (+2.4 if f in (6, 7) else (-0.6 if f == 8 else 0.0))
            ant_bends = [(0.0, +whip * 0.4, whip), (0.0, -whip * 0.4, whip), (0.0, +whip * 0.5, whip * 0.8), (0.0, -whip * 0.5, whip * 0.8)]

        elif f <= 19:
            # --- 10..19: BOOT (Power LED on, monitor degauss shake, floppy LED flickers) ---
            frame_names.append(f"boot_{f:02d}")
            pwr_on = True
            drv_on = f in (11, 12, 14, 15, 17, 18, 19)
            # Crisp CRT degauss shudder on frames 10..14
            if f <= 15:
                amp = math.exp(-(f - 10) * 0.45)
                sgn = 1.0 if (f % 2 == 0) else -1.0
                crt_jit = (3.4 * amp * sgn, -1.6 * amp * sgn, 2.2 * amp * sgn, 0.0, 0.35 * amp * sgn, 0.20 * amp)
            # Half-inserted floppy vibrates slightly when drive LED is reading LOL.BAT
            if drv_on:
                slot_eject_dx = 0.22 * (1.0 if (f % 2 == 0) else -1.0)
            # Antennas perk and quiver with static charge
            qv = 0.8 * math.sin((f - 10) * 1.4)
            ant_bends = [(qv * 0.5, +qv, 0.4), (-qv * 0.5, -qv, 0.4), (0.3, +qv * 0.8, 0.3), (-0.3, -qv * 0.8, 0.3)]

        elif f <= 39:
            # --- 20..39: ACTIVE LOOP (20 frames, 100% seamless wrap 39 -> 20) ---
            frame_names.append(f"act_{f:02d}")
            pwr_on = True
            k = f - 20
            ph = 2.0 * math.pi * (k / 20.0)
            drv_on = (k % 5) in (0, 1, 3)

            # Ghost typing: 8 keycap clusters hammer down (-1.05 units!) in lively staggered waves!
            for ki in range(8):
                w1 = math.sin(ph * 3.0 + ki * 1.95)
                w2 = math.cos(ph * 5.0 - ki * 1.30)
                press = max(0.0, (w1 * 0.6 + w2 * 0.5) - 0.12) / 0.98
                key_dep[ki] = -1.08 * min(1.0, press * 1.35)

            # CRT 60Hz electromagnetic hum & frantic packet-blast jitter
            crt_jit = (
                0.75 * math.sin(ph * 4.0),
                0.55 * math.cos(ph * 3.0 + 0.5),
                0.65 * math.sin(ph * 5.0),
                0.14 * math.cos(ph * 4.0),
                0.20 * math.sin(ph * 6.0),
                0.16 * math.sin(ph * 4.0 + 1.1),
            )
            slot_eject_dx = 0.14 * math.sin(ph * 5.0)

            # Four antennas twitching & whipping energetically out of phase
            ant_bends = [
                (1.6 * math.sin(ph * 3.0),        +2.3 * math.cos(ph * 2.0 + 0.3),  1.1 * math.sin(ph * 4.0)),
                (1.6 * math.cos(ph * 3.0 + 0.8),  -2.3 * math.sin(ph * 2.0),        1.1 * math.cos(ph * 4.0 + 0.5)),
                (1.4 * math.sin(ph * 4.0 + 1.2),  +2.1 * math.sin(ph * 3.0),        1.3 * math.cos(ph * 2.0)),
                (1.4 * math.cos(ph * 4.0 + 0.4),  -2.1 * math.cos(ph * 3.0 + 0.7),  1.3 * math.sin(ph * 2.0 + 0.9)),
            ]

        else:
            # --- 40..49: SHUTDOWN (screen collapses to white dot, LEDs off, case & CRT slump, antennas droop) ---
            frame_names.append(f"off_{f:02d}")
            u = smootherstep((f - 40) / 9.0)
            pwr_on = (f <= 41)
            drv_on = (f == 40)
            if f in (40, 41):
                # Death sputter jolt before slump
                jolt = 1.0 if f == 40 else -0.7
                crt_jit = (4.0 * jolt, -3.5 * abs(jolt), 3.0 * jolt, 0.0, 0.4 * jolt, 0.3)
            # Heavy forward slump of CRT monitor, slight sag of stand/case, popped-out floppy, limp drooping antennas
            slump_pitch = +15.5 * u   # +15.5 deg tips CRT front (+X) DOWNWARD toward floor!
            slump_roll = -5.5 * u
            sq_z = 1.0 - 0.07 * u
            sq_xy = 1.0 + 0.02 * u
            slot_eject_dx = 1.45 * smoothstep(min(1.0, (f - 40) / 3.0))
            ant_bends = [
                (+2.2 * u, +2.8 * u, -6.2 * u),
                (+2.2 * u, -2.8 * u, -6.2 * u),
                (+1.8 * u, +3.2 * u, -6.8 * u),
                (+1.8 * u, -3.2 * u, -6.8 * u),
            ]

        # Transform Helpers matching _build_antennas_and_leds_for_frame
        def xf_case_pt(p):
            piv = (0.0, 0.0, 22.0)
            if p[2] <= 20.0:
                return (p[0] * sq_xy, p[1] * sq_xy, p[2] * sq_z)
            d = rot_y(rot_x(vsub(p, piv), slump_roll * 0.35), slump_pitch * 0.35)
            w = vadd(piv, d)
            return (w[0] * sq_xy, w[1] * sq_xy, w[2] * sq_z)

        def xf_case_nm(n):
            return vnorm(rot_y(rot_x(n, slump_roll * 0.35), slump_pitch * 0.35))

        def xf_crt_pt(p):
            piv = (-0.8, 0.0, 33.8)
            d = vsub(p, piv)
            d = rot_x(d, crt_jit[0] + slump_roll)
            d = rot_y(d, crt_jit[1] + slump_pitch)
            d = rot_z(d, crt_jit[2])
            w = vadd(piv, vadd(d, (crt_jit[3], crt_jit[4], crt_jit[5])))
            return (w[0] * sq_xy, w[1] * sq_xy, w[2] * sq_z)

        def xf_crt_nm(n):
            qn = rot_x(n, crt_jit[0] + slump_roll)
            qn = rot_y(qn, crt_jit[1] + slump_pitch)
            qn = rot_z(qn, crt_jit[2])
            return vnorm(qn)

        ant_m, led_m = _build_antennas_and_leds_for_frame(ant_bends, pwr_on, drv_on, sq_xy, sq_z, slump_pitch, slump_roll, crt_jit)

        # 1. Body vertices
        bv, bn = [], []
        for p, n in zip(base_p.verts, base_p.norms):
            bv.append(xf_case_pt(p))
            bn.append(xf_case_nm(n))
        for ki, kp in enumerate(key_ps):
            dz_k = key_dep[ki]
            for p, n in zip(kp.verts, kp.norms):
                bv.append(xf_case_pt((p[0], p[1], p[2] + dz_k)))
                bn.append(xf_case_nm(n))
        for p, n in zip(crt_p.verts, crt_p.norms):
            bv.append(xf_crt_pt(p))
            bn.append(xf_crt_nm(n))
        bv += ant_m.verts
        bn += ant_m.norms
        body_frames.append((bv, bn))

        # 2. Disk surface vertices (half-inserted slot disk + floor materialize disk)
        dv, dn = [], []
        for p, n in zip(slot_d.verts, slot_d.norms):
            dv.append(xf_case_pt((p[0] + slot_eject_dx, p[1], p[2])))
            dn.append(xf_case_nm(n))
        hide_floor = (0.0, 0.0, 2.0)
        for p, n in zip(floor_d.verts, floor_d.norms):
            if fd_sc <= 1e-5:
                dv.append(hide_floor)
                dn.append((1.0, 0.0, 0.0))
            else:
                dv.append((p[0] * fd_sc, p[1] * fd_sc, max(0.0, p[2] * fd_sc + fd_z)))
                dn.append(n)
        dsk_frames.append((dv, dn))

        # 3. Dedicated CRT Screen surface vertices
        sv = [xf_crt_pt(p) for p in scr_p.verts]
        sn = [xf_crt_nm(n) for n in scr_p.norms]
        scr_frames.append((sv, sn))

        # 4. LEDs & Bright Antenna Tips vertices
        led_frames.append((led_m.verts, led_m.norms))

    surfaces = [
        dict(name="netsend_pc_body", shader="progs/netsend_pc_body", tris=body_tris, st=body_st, frames=body_frames),
        dict(name="netsend_disk",    shader="progs/netsend_disk",    tris=dsk_tris,  st=dsk_st,  frames=dsk_frames),
        dict(name="netsend_screen",  shader="progs/netsend_scr_loop", tris=scr_p.tris, st=scr_p.st, frames=scr_frames),
        dict(name="netsend_leds",    shader="progs/netsend_leds",    tris=led0.tris, st=led0.st, frames=led_frames),
    ]
    return dict(name="netsend_pc", surfaces=surfaces, nframes=50), frame_names


# ==============================================================================
# 5. ELECTRICITY ARC MODEL: progs/netsend_arc.md3 (8 FRAMES: 0..7)
# ==============================================================================
def build_netsend_arc_md3():
    """Builds progs/netsend_arc.md3 (8 frames of jagged crossed-ribbon blue-white lightning arcs):
      - Origin at (0,0,0) matching netsend_pc.md3's floor origin so QC simply sets arc.origin = pc.origin
        and arc.angles = pc.angles while cycling arc.frame = 0..7!
      - Arcs crackle between the 4 antenna tips AND jump from the side whips / desktop case to the floor!
    """
    N_SEGS = 8
    t_tl = ANTENNA_BASES_AND_TIPS[0][1]  # (+2.6, +10.4, 62.8)
    t_tr = ANTENNA_BASES_AND_TIPS[1][1]  # (+2.6, -10.4, 62.8)
    t_sl = ANTENNA_BASES_AND_TIPS[2][1]  # (+0.6, +14.8, 50.2)
    t_sr = ANTENNA_BASES_AND_TIPS[3][1]  # (+0.6, -14.8, 50.2)

    bolt_endpoints = [
        (t_tl, t_tr, 1.35, 3.2),                             # 0: Primary crown arc across top rabbit ears
        (t_tl, t_tr, 0.85, 4.6),                             # 1: Secondary dancing upper crown arc
        (t_tl, t_sl, 1.05, 2.8),                             # 2: Left rabbit-ear <-> left side whip
        (t_tr, t_sr, 1.05, 2.8),                             # 3: Right rabbit-ear <-> right side whip
        ((-1.0, +12.5, 28.2), (+2.5, +14.6, 0.4), 1.15, 3.4),# 4: Left case -> floor ground strike!
        ((-1.0, -12.5, 28.2), (+2.5, -14.6, 0.4), 1.15, 3.4),# 5: Right case -> floor ground strike!
        ((+9.2, +5.9, 28.2),  (+12.5, +4.0, 0.4), 0.95, 2.6),# 6: Half-inserted LOL.BAT floppy -> floor arc!
    ]

    frames = []
    st_fixed, tris_fixed = None, None

    for fi in range(8):
        rng = random.Random(2026 + fi * 131)
        m = MeshPart("netsend_arc")

        for bi, (p0, p1, base_hw, jag) in enumerate(bolt_endpoints):
            # Vary intensity across frames so floor strikes jump & flicker organically
            active_w = base_hw * rng.uniform(0.65, 1.25)
            if bi >= 4 and ((fi + bi) % 3 == 0):
                active_w *= 0.28  # momentary dim flicker on alternating ground arcs

            _, u_ax, v_ax = frame_basis(vsub(p1, p0))
            pts = [p0]
            for s in range(1, N_SEGS):
                u = s / float(N_SEGS)
                env = math.sin(math.pi * u)
                mid = vlerp(p0, p1, u)
                # Slight upward bow on top crown arcs
                if bi in (0, 1):
                    mid = (mid[0], mid[1], mid[2] + (2.2 if bi == 0 else 4.0) * env)
                j1 = rng.uniform(-jag, jag) * env
                j2 = rng.uniform(-jag, jag) * env
                pts.append(vadd(mid, vadd(vmul(u_ax, j1), vmul(v_ax, j2))))
            pts.append(p1)

            # Crossed perpendicular ribbons along pts
            tans = []
            for i in range(N_SEGS + 1):
                d = vsub(pts[min(N_SEGS, i + 1)], pts[max(0, i - 1)])
                tans.append(vnorm(d) if vlen(d) > 1e-6 else (0.0, 0.0, 1.0))

            _, bu, bv = frame_basis(tans[0])
            planes = []
            for ti in tans:
                bu_p = vsub(bu, vmul(ti, vdot(bu, ti)))
                if vlen(bu_p) < 1e-5:
                    _, bu, bv = frame_basis(ti)
                else:
                    bu = vnorm(bu_p)
                    bv = vcross(ti, bu)
                planes.append((bu, bv))

            for pl_i in (0, 1):
                b = len(m.verts)
                for i, pt in enumerate(pts):
                    uc = i / float(N_SEGS)
                    hw = active_hw_taper = active_w * (0.45 + 0.55 * math.sin(math.pi * min(0.95, max(0.05, uc))))
                    ax = planes[i][pl_i]
                    m.verts += [vadd(pt, vmul(ax, -hw)), vadd(pt, vmul(ax, +hw))]
                    m.norms += [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0)]
                    m.st += [(uc, 0.04), (uc, 0.96)]
                for i in range(N_SEGS):
                    a0, a1, a2, a3 = b + 2 * i, b + 2 * i + 1, b + 2 * i + 2, b + 2 * i + 3
                    m.tris += [(a0, a1, a2), (a1, a3, a2)]

        if fi == 0:
            st_fixed = m.st
            tris_fixed = m.tris
        frames.append((m.verts, m.norms))

    surf = dict(name="netsend_arc", shader="progs/netsend_arc", tris=tris_fixed, st=st_fixed, frames=frames)
    return dict(name="netsend_arc", surfaces=[surf], nframes=8), [f"arc_{i}" for i in range(8)]


# ==============================================================================
# 6. OPTIONAL FLOOR-STUCK FLOPPY DISK: progs/netsend_disk.md3 (8 FRAMES: 0..7)
# ==============================================================================
def build_netsend_disk_md3():
    """Builds progs/netsend_disk.md3 (reusing the viewmodel's 3.5" LOL.BAT disk mesh & texture):
      - Frame 0   : Thrown/flying flat pose (centered at origin, spinning in air if needed).
      - Frame 1   : Stuck cleanly at a ~68-deg angle in the floor (z=0 at embedded corner, LOL.BAT facing +X).
      - Frames 2-7: Vibrating / trembling in the floor right before netsend_pc.md3 pops out of it!
    """
    raw = build_floppy_disk_mesh(half_w=4.20, half_h=4.45, half_t=0.28)
    frames = []
    names = []

    for f in range(8):
        vv, nn = [], []
        if f == 0:
            names.append("disk_fly")
            for p, n in zip(raw.verts, raw.norms):
                q = rot_y(p, 90.0)  # flat horizontal, LOL.BAT facing +Z up
                qn = rot_y(n, 90.0)
                vv.append(q)
                nn.append(vnorm(qn))
        else:
            names.append("disk_stuck" if f == 1 else f"disk_tremor_{f - 1}")
            trem_r = 0.0 if f == 1 else 3.8 * math.sin(f * 2.4)
            trem_y = 0.0 if f == 1 else 0.35 * math.cos(f * 3.1)
            for p, n in zip(raw.verts, raw.norms):
                # Rotate 180 around Z so front (-X) faces +X, tilt -22 deg back so LOL.BAT faces out & up,
                # roll 12 deg jauntily so one corner embeds cleanly into the floor at z = 0!
                q = rot_x(rot_y(rot_z(p, 180.0), -22.0), 12.0 + trem_r)
                qn = rot_x(rot_y(rot_z(n, 180.0), -22.0), 12.0 + trem_r)
                vv.append((q[0], q[1] + trem_y, q[2] + 3.65))
                nn.append(vnorm(qn))
        frames.append((vv, nn))

    surf = dict(name="netsend_disk", shader="progs/netsend_disk", tris=raw.tris, st=raw.st, frames=frames)
    return dict(name="netsend_disk", surfaces=[surf], nframes=8), names
