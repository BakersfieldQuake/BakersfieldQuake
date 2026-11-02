"""3D Procedural Geometry & Articulated Builders for BakersfieldQuake Mega Man Weapon ('The Mega-Slinger' Mk.II):
  1. Recreated 'Mega Man' Contraption (crisp hard-edge normals, mirror-chrome bar, TIG T-collar, steel cross-axle,
     32-seg 5-ribbed pneumatic tires, 4-cutout concave white stamped-steel dish rims, 3D hex nut, cotter pin & valve)
  2. Concept A (Flagship): 'THE MEGA-SLINGER' Mk.II Mag-Pneumatic Rail-Catapult Gun (sleek multi-faceted gunmetal/titanium
     chassis, glowing cyan accelerator chevrons, canted 250 PSI dial, zero-clipping bottles & outriggers, crescent sabot)
  3. Concept B (Variant):  'RANGER GAUNTLET THROW' Articulated Quake Hand-Held Thrower
"""
import math


# --------------------------------------------------------------------------- 3D Vector & Basis Math
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


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def rot_x(p, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y(p, deg):
    """+deg pitches +X up toward +Z."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[2] * s, p[1], p[0] * s + p[2] * c)


def rot_z(p, deg):
    """+deg yaws +X toward +Y (left)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def rot_axis(p, axis, deg):
    """Rodrigues rotation of vector p around unit axis by deg."""
    k = vnorm(axis)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    kv = vcross(k, p)
    kd = vdot(k, p)
    return (
        p[0] * c + kv[0] * s + k[0] * kd * (1.0 - c),
        p[1] * c + kv[1] * s + k[1] * kd * (1.0 - c),
        p[2] * c + kv[2] * s + k[2] * kd * (1.0 - c),
    )


def basis_from_axis(axis, up_hint=(0.0, 0.0, 1.0)):
    """Right-handed orthonormal basis (X, Y, Z) with X = norm(axis) and det([X,Y,Z]) = +1."""
    X = vnorm(axis)
    if abs(vdot(X, up_hint)) > 0.96:
        up_hint = (0.0, 1.0, 0.0) if abs(X[1]) < 0.9 else (1.0, 0.0, 0.0)
    Y = vnorm(vcross(up_hint, X))
    Z = vcross(X, Y)
    return X, Y, Z


def _chamfer_loop_yz(yc, yr, zc, zr, ch):
    c = min(ch, 0.44 * min(max(yr, 1e-4), max(zr, 1e-4)))
    return [
        (yc + yr, zc - zr + c),
        (yc + yr, zc + zr - c),
        (yc + yr - c, zc + zr),
        (yc - yr + c, zc + zr),
        (yc - yr, zc + zr - c),
        (yc - yr, zc - zr + c),
        (yc - yr + c, zc - zr),
        (yc + yr - c, zc - zr),
    ]


# --------------------------------------------------------------------------- Mesh Part Container & Primitives
class MeshPart:
    def __init__(self, mat):
        self.mat = mat
        self.verts = []
        self.norms = []
        self.st = []
        self.tris = []

    def append_part(self, other, offset=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, scale=1.0):
        base = len(self.verts)
        for p, n, uv in zip(other.verts, other.norms, other.st):
            q = vmul(p, scale)
            qn = n
            if rx:
                q, qn = rot_x(q, rx), rot_x(qn, rx)
            if ry:
                q, qn = rot_y(q, ry), rot_y(qn, ry)
            if rz:
                q, qn = rot_z(q, rz), rot_z(qn, rz)
            self.verts.append(vadd(q, offset))
            self.norms.append(vnorm(qn))
            self.st.append(uv)
        for a, b, c in other.tris:
            self.tris.append((a + base, b + base, c + base))

    def add_quad(self, p0, p1, p2, p3, uv0, uv1, uv2, uv3, nrm=None, two_sided=False):
        if nrm is None:
            nrm = vnorm(vcross(vsub(p1, p0), vsub(p2, p0)))
        w_n = vcross(vsub(p1, p0), vsub(p2, p0))
        b = len(self.verts)
        self.verts += [p0, p1, p2, p3]
        self.norms += [nrm, nrm, nrm, nrm]
        self.st += [uv0, uv1, uv2, uv3]
        if vdot(w_n, nrm) >= 0.0:
            self.tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        else:
            self.tris += [(b, b + 2, b + 1), (b, b + 3, b + 2)]
        if two_sided:
            b2 = len(self.verts)
            nr = vmul(nrm, -1.0)
            self.verts += [p0, p1, p2, p3]
            self.norms += [nr, nr, nr, nr]
            self.st += [uv0, uv1, uv2, uv3]
            if vdot(w_n, nrm) >= 0.0:
                self.tris += [(b2, b2 + 2, b2 + 1), (b2, b2 + 3, b2 + 2)]
            else:
                self.tris += [(b2, b2 + 1, b2 + 2), (b2, b2 + 2, b2 + 3)]

    def add_loft(self, sections, uv_rect=(0.02, 0.02, 0.48, 0.23), side_uv=None, top_uv=None, cap_start=True, cap_end=True):
        """Sweeps 8-facet chamfered cross-sections [(x, yc, yr, zc, zr, ch), ...] along +X with crisp per-facet bevel normals!"""
        su = side_uv if side_uv else uv_rect
        tu = top_uv if top_uv else uv_rect
        loops = [_chamfer_loop_yz(yc, yr, zc, zr, ch) for (_, yc, yr, zc, zr, ch) in sections]
        xs = [s[0] for s in sections]
        xmin, xspan = min(xs), max(max(xs) - min(xs), 1e-6)
        n_ring = 8

        for si in range(len(sections) - 1):
            xa, xb = sections[si][0], sections[si + 1][0]
            ua_t = (xa - xmin) / xspan
            ub_t = (xb - xmin) / xspan
            la, lb = loops[si], loops[si + 1]
            for i in range(n_ring):
                ip = (i + 1) % n_ring
                p0 = (xa, la[i][0], la[i][1])
                p1 = (xb, lb[i][0], lb[i][1])
                p2 = (xb, lb[ip][0], lb[ip][1])
                p3 = (xa, la[ip][0], la[ip][1])
                # Outward normal for CCW loop around +X: T_loop x T_x
                t_loop = vadd(vsub(p3, p0), vsub(p2, p1))
                t_x = vadd(vsub(p1, p0), vsub(p2, p3))
                fn = vnorm(vcross(t_loop, t_x))
                if abs(fn[2]) > 0.80:
                    use_uv = tu
                elif abs(fn[1]) > 0.80:
                    use_uv = su
                else:
                    use_uv = uv_rect
                u0, v0, u1, v1 = use_uv
                uu0 = u0 + (u1 - u0) * ua_t
                uu1 = u0 + (u1 - u0) * ub_t
                self.add_quad(
                    p0, p1, p2, p3,
                    (uu0, v1), (uu1, v1), (uu1, v0), (uu0, v0),
                    nrm=fn,
                )

        u0, v0, u1, v1 = uv_rect
        uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
        caps = []
        if cap_start:
            caps.append((sections[0], loops[0], -1.0))
        if cap_end:
            caps.append((sections[-1], loops[-1], +1.0))
        for (x_end, yc, yr, zc, zr, _), lp, nx in caps:
            b_idx = len(self.verts)
            self.verts.append((x_end, yc, zc))
            self.norms.append((nx, 0.0, 0.0))
            self.st.append((uc, vc))
            for ya, za in lp:
                uu = uc + 0.48 * (u1 - u0) * ((ya - yc) / max(yr, 1e-6))
                vv = vc - 0.48 * (v1 - v0) * ((za - zc) / max(zr, 1e-6))
                self.verts.append((x_end, ya, za))
                self.norms.append((nx, 0.0, 0.0))
                self.st.append((uu, vv))
            for i in range(n_ring):
                i1 = b_idx + 1 + i
                i2 = b_idx + 1 + (i + 1) % n_ring
                if nx > 0:
                    self.tris.append((b_idx, i1, i2))
                else:
                    self.tris.append((b_idx, i2, i1))

    def add_chamfer_box(self, x0, x1, y0, y1, z0, z1, ch=0.12, uv_rect=(0.02, 0.02, 0.48, 0.23), side_uv=None, top_uv=None):
        """Machined industrial chamfered rectangular block (8-facet loop extruded along X with capped ends)."""
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        yc, yr = 0.5 * (y0 + y1), 0.5 * (y1 - y0)
        zc, zr = 0.5 * (z0 + z1), 0.5 * (z1 - z0)
        self.add_loft(
            [(x0, yc, yr, zc, zr, ch), (x1, yc, yr, zc, zr, ch)],
            uv_rect=uv_rect, side_uv=side_uv, top_uv=top_uv,
        )

    def add_lathe(self, origin, axis, profile, segs=24, sy=1.0, sz=1.0, uv_mode="cyl", uv_rect=(0.0, 0.0, 1.0, 1.0), up_hint=(0.0, 0.0, 1.0)):
        """Revolves profile = [(x_along, r, uv_tag_or_v), ...] around right-handed basis (X=axis, Y, Z).
        Repeated (x, r) points create razor-sharp hard-edge normal creases!
        """
        X, Y, Z = basis_from_axis(axis, up_hint=up_hint)
        cols = segs + 1
        base = len(self.verts)
        u0, v0, u1, v1 = uv_rect
        xs = [pt[0] for pt in profile]
        xmin, xspan = min(xs), max(max(xs) - min(xs), 1e-6)

        local_pts = []
        for item in profile:
            xp, rp = item[0], item[1]
            tv = item[2] if len(item) > 2 and item[2] is not None else (xp - xmin) / xspan
            for j in range(cols):
                th = 2.0 * math.pi * (j / float(segs))
                cth, sth = math.cos(th), math.sin(th)
                py, pz = rp * cth * sy, rp * sth * sz
                pos = vadd(origin, vadd(vmul(X, xp), vadd(vmul(Y, py), vmul(Z, pz))))
                local_pts.append(pos)
                if uv_mode == "polar":
                    rmax = item[3] if len(item) > 3 else 1.0
                    uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
                    ru, rv = 0.5 * (u1 - u0), 0.5 * (v1 - v0)
                    rr_n = min(1.0, rp / max(rmax, 1e-6))
                    self.st.append((uc + ru * rr_n * cth, vc + rv * rr_n * sth))
                else:
                    uu = u0 + (u1 - u0) * (j / float(segs))
                    vv = v0 + (v1 - v0) * tv
                    self.st.append((uu, vv))

        ring_tris = []
        acc_n = [[0.0, 0.0, 0.0] for _ in local_pts]
        for i in range(len(profile) - 1):
            x_a, r_a = profile[i][0], profile[i][1]
            x_b, r_b = profile[i + 1][0], profile[i + 1][1]
            if abs(x_a - x_b) < 1e-7 and abs(r_a - r_b) < 1e-7:
                continue  # hard-edge normal break!
            for j in range(segs):
                a = i * cols + j
                b = a + 1
                c = a + cols
                d = c + 1
                if r_a > 1e-6:
                    t1 = (a, b, c)
                    fn1 = vcross(vsub(local_pts[t1[1]], local_pts[t1[0]]), vsub(local_pts[t1[2]], local_pts[t1[0]]))
                    ring_tris.append(t1)
                    for vi in t1:
                        acc_n[vi][0] += fn1[0]
                        acc_n[vi][1] += fn1[1]
                        acc_n[vi][2] += fn1[2]
                if r_b > 1e-6:
                    t2 = (b, d, c)
                    fn2 = vcross(vsub(local_pts[t2[1]], local_pts[t2[0]]), vsub(local_pts[t2[2]], local_pts[t2[0]]))
                    ring_tris.append(t2)
                    for vi in t2:
                        acc_n[vi][0] += fn2[0]
                        acc_n[vi][1] += fn2[1]
                        acc_n[vi][2] += fn2[2]

        for i in range(len(profile)):
            i0 = i * cols
            i1 = i * cols + segs
            sn = vadd(acc_n[i0], acc_n[i1])
            acc_n[i0] = list(sn)
            acc_n[i1] = list(sn)

        self.verts += local_pts
        self.norms += [vnorm(n) for n in acc_n]
        self.tris += [(a + base, b + base, c + base) for (a, b, c) in ring_tris]

    def add_tube(self, pts, radii, segs=12, uv_rect=(0.0, 0.0, 1.0, 1.0), cap_start=True, cap_end=True):
        """Sweeps circular/elliptical rings along a 3D polyline with twist-free parallel transport & crisp end-caps."""
        n = len(pts)
        u0, v0, u1, v1 = uv_rect
        tans = []
        for i in range(n):
            p_prev = pts[max(0, i - 1)]
            p_next = pts[min(n - 1, i + 1)]
            tans.append(vnorm(vsub(p_next, p_prev)))

        cols = segs + 1
        rings = []
        _, Y, Z = basis_from_axis(tans[0])
        for i in range(n):
            T = tans[i]
            Y_proj = vsub(Y, vmul(T, vdot(Y, T)))
            if vlen(Y_proj) < 1e-5:
                _, Y, Z = basis_from_axis(T)
            else:
                Y = vnorm(Y_proj)
                Z = vcross(T, Y)
            rad = radii[i]
            ry, rz = rad if isinstance(rad, tuple) else (rad, rad)
            r_base = len(self.verts)
            rings.append(r_base)
            tv = v0 + (v1 - v0) * (i / float(max(1, n - 1)))
            for j in range(cols):
                th = 2.0 * math.pi * (j / float(segs))
                cth, sth = math.cos(th), math.sin(th)
                pos = vadd(pts[i], vadd(vmul(Y, cth * ry), vmul(Z, sth * rz)))
                nrm = vnorm(vadd(vmul(Y, cth / max(ry, 1e-5)), vmul(Z, sth / max(rz, 1e-5))))
                self.verts.append(pos)
                self.norms.append(nrm)
                self.st.append((u0 + (u1 - u0) * (j / float(segs)), tv))

        for i in range(n - 1):
            for j in range(segs):
                a = rings[i] + j
                b = a + 1
                c = rings[i + 1] + j
                d = c + 1
                self.tris += [(a, b, c), (b, d, c)]

        if cap_start:
            r0 = radii[0][0] if isinstance(radii[0], tuple) else radii[0]
            ic = len(self.verts)
            n_cap = vmul(tans[0], -1.0)
            self.verts.append(vsub(pts[0], vmul(tans[0], r0 * 0.28)))
            self.norms.append(n_cap)
            self.st.append((0.5 * (u0 + u1), v0))
            for j in range(segs):
                self.tris.append((ic, rings[0] + j + 1, rings[0] + j))

        if cap_end:
            rn = radii[-1][0] if isinstance(radii[-1], tuple) else radii[-1]
            ic = len(self.verts)
            n_cap = tans[-1]
            self.verts.append(vadd(pts[-1], vmul(tans[-1], rn * 0.35)))
            self.norms.append(n_cap)
            self.st.append((0.5 * (u0 + u1), v1))
            for j in range(segs):
                self.tris.append((ic, rings[-1] + j, rings[-1] + j + 1))


# ===========================================================================
# 1. THE RECREATED 'MEGA MAN' CONTRAPTION (Shared Hero Payload)
# ===========================================================================
MM_WHEEL_Y = 5.72
MM_WHEEL_R = 4.02
MM_TIRE_HW = 1.06


def _build_single_wheel(side_sign):
    """Builds one complete pneumatic wheel at origin (0, 0, 0) with outer dish facing (0, side_sign, 0).
    Uses crisp hard-edge normal creases at rim bead & hub steps so stamped white steel & tire rubber shade cleanly!
    """
    wp = MeshPart("wheel")
    hp = MeshPart("chrome_axle")
    axis = (0.0, float(side_sign), 0.0)
    up_h = (0.0, 0.0, 1.0)

    # 1) Inner Off-White Steel Hub Disc (hard-edge break at rim bead r=2.38)
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-0.86, 0.00, 0.00, 2.38),
            (-0.86, 0.56, 0.24, 2.38),
            (-0.86, 0.56, 0.24, 2.38),
            (-0.74, 1.92, 0.80, 2.38),
            (-0.92, 2.22, 0.93, 2.38),
            (-0.86, 2.38, 1.00, 2.38),
        ],
        segs=32, uv_mode="polar", uv_rect=(0.51, 0.51, 0.99, 0.99), up_hint=up_h,
    )

    # 2) Inner Rubber Tire Sidewall
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-0.86, 2.38, 0.59, 4.02),
            (-0.99, 2.86, 0.71, 4.02),
            (-1.07, 3.38, 0.84, 4.02),
            (-1.01, 3.82, 0.95, 4.02),
            (-0.84, 3.96, 0.98, 4.02),
        ],
        segs=32, uv_mode="polar", uv_rect=(0.51, 0.01, 0.99, 0.49), up_hint=up_h,
    )

    # 3) 5-Ribbed Sculpted Rubber Tread Crown
    X_w, Y_w, Z_w = basis_from_axis(axis, up_hint=up_h)
    tread_prof = [
        (-0.84, 3.96, 0.02),
        (-0.74, 4.02, 0.08),
        (-0.56, 4.03, 0.17),
        (-0.48, 3.91, 0.21),  # groove 1
        (-0.40, 4.03, 0.25),
        (-0.24, 4.04, 0.36),
        (-0.16, 3.91, 0.40),  # groove 2
        (-0.08, 4.04, 0.44),
        (+0.08, 4.04, 0.56),
        (+0.16, 3.91, 0.60),  # groove 3
        (+0.24, 4.04, 0.64),
        (+0.40, 4.03, 0.75),
        (+0.48, 3.91, 0.79),  # groove 4
        (+0.56, 4.03, 0.83),
        (+0.74, 4.02, 0.92),
        (+0.84, 3.96, 0.98),
    ]
    segs = 32
    cols = segs + 1
    b_tr = len(wp.verts)
    tr_pts = []
    for sp, rp, ut in tread_prof:
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(segs))
            cth, sth = math.cos(th), math.sin(th)
            pos = vadd(vmul(X_w, sp), vadd(vmul(Y_w, rp * cth), vmul(Z_w, rp * sth)))
            tr_pts.append(pos)
            wp.st.append((0.01 + 0.48 * ut, 0.01 + 0.48 * (j / float(segs))))
    tr_acc = [[0.0, 0.0, 0.0] for _ in tr_pts]
    tr_tris = []
    for i in range(len(tread_prof) - 1):
        for j in range(segs):
            a = i * cols + j
            b = a + 1
            c = a + cols
            d = c + 1
            for t_tri in ((a, b, c), (b, d, c)):
                fn = vcross(vsub(tr_pts[t_tri[1]], tr_pts[t_tri[0]]), vsub(tr_pts[t_tri[2]], tr_pts[t_tri[0]]))
                tr_tris.append(t_tri)
                for vi in t_tri:
                    tr_acc[vi][0] += fn[0]
                    tr_acc[vi][1] += fn[1]
                    tr_acc[vi][2] += fn[2]
    for i in range(len(tread_prof)):
        i0, i1 = i * cols, i * cols + segs
        sn = vadd(tr_acc[i0], tr_acc[i1])
        tr_acc[i0], tr_acc[i1] = list(sn), list(sn)
    wp.verts += tr_pts
    wp.norms += [vnorm(n) for n in tr_acc]
    wp.tris += [(a + b_tr, b + b_tr, c + b_tr) for (a, b, c) in tr_tris]

    # 4) Outer Rubber Tire Sidewall
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.84, 3.96, 0.98, 4.02),
            (+1.01, 3.82, 0.95, 4.02),
            (+1.07, 3.38, 0.84, 4.02),
            (+0.99, 2.86, 0.71, 4.02),
            (+0.88, 2.38, 0.59, 4.02),
        ],
        segs=32, uv_mode="polar", uv_rect=(0.51, 0.01, 0.99, 0.49), up_hint=up_h,
    )

    # 5) Stamped Off-White Steel Outer Concave Dish Rim (w/ crisp rolled bead & bearing boss creases!)
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.88, 2.38, 1.00, 2.38),
            (+0.97, 2.24, 0.94, 2.38),  # rolled white steel rim bead lip!
            (+0.84, 2.02, 0.85, 2.38),
            (+0.42, 1.72, 0.72, 2.38),  # deep concave dish wall (4 oval cutouts map here!)
            (+0.36, 1.08, 0.45, 2.38),
            (+0.40, 0.62, 0.26, 2.38),
            (+0.40, 0.62, 0.26, 2.38),  # crisp stamped step crease!
            (+0.66, 0.54, 0.23, 2.38),
            (+0.66, 0.54, 0.23, 2.38),  # flat bearing face crease!
            (+0.68, 0.26, 0.11, 2.38),
            (+0.68, 0.00, 0.00, 2.38),
        ],
        segs=32, uv_mode="polar", uv_rect=(0.01, 0.51, 0.49, 0.99), up_hint=up_h,
    )

    # 6) 3D Hub Hardware (Crisp-creased Hex Zinc Nut + Axle Stub + Yellow Cotter Pin + Angled Schrader Valve!)
    hp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.66, 0.24, 0.05),
            (+0.66, 0.42, 0.10),
            (+0.66, 0.42, 0.10),  # crisp hex nut rear crease
            (+0.91, 0.42, 0.90),
            (+0.91, 0.42, 0.90),  # crisp hex nut front flat face!
            (+0.91, 0.21, 0.96),
        ],
        segs=6, uv_rect=(0.52, 0.52, 0.73, 0.73), up_hint=up_h,
    )
    hp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.90, 0.21, 0.10),
            (+1.10, 0.21, 0.88),
            (+1.10, 0.21, 0.88),  # crisp flat axle end-cap!
            (+1.10, 0.00, 1.00),
        ],
        segs=12, uv_rect=(0.52, 0.04, 0.96, 0.46), up_hint=up_h,
    )
    pin_c = vmul(X_w, 0.99)
    hp.add_tube(
        [vadd(pin_c, vmul(Z_w, -0.48)), vadd(pin_c, vmul(Z_w, +0.34))],
        [0.056, 0.056], segs=8, uv_rect=(0.76, 0.52, 0.98, 0.73),
    )
    loop_pts = []
    for k in range(9):
        la = math.radians(k * 45.0)
        loop_pts.append(vadd(pin_c, vadd(vmul(Z_w, 0.42 + 0.095 * math.cos(la)), vmul(Y_w, 0.095 * math.sin(la)))))
    hp.add_tube(loop_pts, [0.046] * len(loop_pts), segs=6, uv_rect=(0.76, 0.52, 0.98, 0.73), cap_start=False, cap_end=False)

    # Angled Schrader Valve Stem at -35 deg (325 deg -> midway between 280 deg and 10 deg cutouts!)
    va = math.radians(-35.0)
    v_rad_dir = vadd(vmul(Y_w, math.cos(va)), vmul(Z_w, math.sin(va)))
    v_base = vadd(vmul(X_w, 0.36), vmul(v_rad_dir, 1.54))
    v_mid = vadd(vmul(X_w, 0.75), vmul(v_rad_dir, 1.35))
    v_tip = vadd(vmul(X_w, 0.94), vmul(v_rad_dir, 1.24))
    hp.add_tube([v_base, v_mid], [0.135, 0.102], segs=8, uv_rect=(0.52, 0.77, 0.73, 0.98))
    hp.add_tube([v_mid, v_tip], [0.088, 0.082], segs=8, uv_rect=(0.77, 0.77, 0.98, 0.98))

    return wp, hp


def build_megaman_payload_parts():
    """Returns dict of static-topology local-space parts for Mega Man with razor-sharp machined normal creases."""
    ba = MeshPart("chrome_axle")

    # 1a. Rear Stepped Matte-Black Rubber End-Cap (x = -4.98 .. -3.82, crisp flat rear face & shoulder!)
    ba.add_lathe(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        [
            (-4.98, 0.00, 0.02),
            (-4.98, 0.58, 0.12),
            (-4.98, 0.58, 0.12),  # crisp rear flat cap crease!
            (-4.88, 0.70, 0.20),
            (-4.52, 0.70, 0.45),
            (-4.48, 0.66, 0.52),
            (-4.18, 0.66, 0.72),
            (-4.14, 0.70, 0.78),
            (-3.84, 0.70, 0.94),
            (-3.84, 0.70, 0.94),  # crisp rubber-to-chrome step shoulder!
            (-3.82, 0.63, 0.98),
        ],
        segs=28, uv_rect=(0.02, 0.52, 0.48, 0.98),
    )

    # 1b. Gleaming Mirror-Chrome Central Bar + Ogive Torpedo Bullet Nose (x = -3.82 .. +5.42)
    chrome_prof = [
        (-3.82, 0.63, 0.02),
        (-1.80, 0.63, 0.24),
        (-0.88, 0.65, 0.36),
        (-0.56, 0.75, 0.42),
        (+0.00, 0.77, 0.46),
        (+0.56, 0.75, 0.50),
        (+0.88, 0.65, 0.56),
        (+3.42, 0.63, 0.79),
    ]
    for k in range(1, 9):
        t = k / 8.0
        xn = 3.42 + 2.00 * t
        rn = 0.63 * (math.cos(t * math.pi * 0.5) ** 0.76)
        if k == 8:
            rn = 0.0
        chrome_prof.append((xn, rn, 0.79 + 0.19 * t))

    ba.add_lathe(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        chrome_prof, segs=28, uv_rect=(0.02, 0.02, 0.48, 0.48),
    )

    # 1c. Welded Transverse T-Collar Sleeve & Twin Machined Retaining Collars along Y (w/ hard-edge shoulders!)
    ba.add_lathe(
        (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        [
            (-1.22, 0.24, 0.96),
            (-1.22, 0.50, 0.92),
            (-1.22, 0.50, 0.92),
            (-0.72, 0.54, 0.82),
            (+0.00, 0.58, 0.74),
            (+0.72, 0.54, 0.82),
            (+1.22, 0.50, 0.92),
            (+1.22, 0.50, 0.92),
            (+1.22, 0.24, 0.96),
        ],
        segs=22, uv_rect=(0.52, 0.02, 0.98, 0.48),
    )
    for sgn in (-1.0, +1.0):
        ba.add_lathe(
            (0.0, sgn * 1.48, 0.0), (0.0, sgn, 0.0),
            [
                (-0.18, 0.24, 0.08),
                (-0.18, 0.43, 0.16),
                (-0.18, 0.43, 0.16),
                (+0.18, 0.43, 0.84),
                (+0.18, 0.43, 0.84),
                (+0.18, 0.24, 0.92),
            ],
            segs=16, uv_rect=(0.52, 0.52, 0.73, 0.73),
        )

    # 1d. Slender Polished Stainless Cross-Axle spanning wheel-to-wheel (y = -5.65 .. +5.65)
    ba.add_lathe(
        (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        [
            (-5.65, 0.00, 0.02),
            (-5.65, 0.35, 0.04),
            (-5.65, 0.35, 0.04),
            (-4.72, 0.35, 0.10),
            (-4.72, 0.35, 0.10),
            (-4.70, 0.23, 0.12),
            (+4.70, 0.23, 0.68),
            (+4.72, 0.35, 0.70),
            (+4.72, 0.35, 0.70),
            (+5.65, 0.35, 0.76),
            (+5.65, 0.35, 0.76),
            (+5.65, 0.00, 0.78),
        ],
        segs=18, uv_rect=(0.52, 0.02, 0.98, 0.36),
    )

    wl, hwl = _build_single_wheel(+1)
    wr, hwr = _build_single_wheel(-1)
    return {
        "bar_axle": ba,
        "wheel_l": wl,
        "wheel_hw_l": hwl,
        "wheel_r": wr,
        "wheel_hw_r": hwr,
    }


def transform_megaman_frame(mm_parts, spin_deg, bar_pitch_deg=0.0, pos=(0.0, 0.0, 0.0), yaw_deg=0.0, roll_deg=0.0, scale=1.0):
    """Transforms Mega Man parts for a given wheel spin angle (deg), bar pitch, roll, yaw, scale, & world/gun offset."""
    def xform_point_nrm(p, n, is_wheel=False, wheel_y=0.0):
        q, qn = p, n
        if is_wheel:
            q = rot_y(q, -spin_deg)
            qn = rot_y(qn, -spin_deg)
            q = (q[0], q[1] + wheel_y, q[2])
        if bar_pitch_deg:
            q = rot_y(q, bar_pitch_deg)
            qn = rot_y(qn, bar_pitch_deg)
        if roll_deg:
            q = rot_x(q, roll_deg)
            qn = rot_x(qn, roll_deg)
        if yaw_deg:
            q = rot_z(q, yaw_deg)
            qn = rot_z(qn, yaw_deg)
        q = vadd(vmul(q, scale), pos)
        return q, vnorm(qn)

    out = {}
    for k, part in mm_parts.items():
        is_w = k.startswith("wheel_")
        wy = +MM_WHEEL_Y if k.endswith("_l") else (-MM_WHEEL_Y if k.endswith("_r") else 0.0)
        vv, nn = [], []
        for p, n in zip(part.verts, part.norms):
            qp, qn = xform_point_nrm(p, n, is_wheel=is_w, wheel_y=wy)
            vv.append(qp)
            nn.append(qn)
        out[k] = (vv, nn)
    return out


# ===========================================================================
# 2. ARTICULATED QUAKE RANGER GLOVED HAND & GAUNTLET BUILDER
# ===========================================================================
def build_articulated_ranger_hand(
    palm_center,
    fwd_dir,
    up_dir,
    side_sign=-1.0,
    finger_curls=(0.75, 0.80, 0.84, 0.86),
    finger_splay=(-8.0, -2.5, +3.0, +8.5),
    thumb_curl=0.65,
    thumb_abd=36.0,
    hand_scale=1.0,
    forearm_len=9.5,
    forearm_dir=None,
):
    """Builds a sculpted, textured Quake Ranger gloved hand + bronze knuckle armor + riveted gauntlet + forearm."""
    hp = MeshPart("hand")
    F = vnorm(fwd_dir)
    U_raw = vsub(up_dir, vmul(F, vdot(up_dir, F)))
    U = vnorm(U_raw)
    L = vnorm(vcross(U, F))
    T_side = vmul(L, -side_sign)

    S = hand_scale

    def to_w(f_c, t_c, u_c):
        return vadd(palm_center, vadd(vmul(F, f_c * S), vadd(vmul(T_side, t_c * S), vmul(U, u_c * S))))

    UV_LEATHER = (0.04, 0.04, 0.46, 0.46)
    UV_PALM = (0.54, 0.04, 0.96, 0.46)
    UV_CUFF = (0.02, 0.53, 0.48, 0.97)
    UV_KNUCKLE = (0.53, 0.53, 0.97, 0.73)
    UV_SLEEVE = (0.53, 0.77, 0.97, 0.98)

    palm_pts = [to_w(-1.85, 0.0, -0.05), to_w(-0.75, 0.04, 0.0), to_w(+0.55, 0.06, 0.02), to_w(+1.62, 0.04, -0.02)]
    palm_rads = [(1.32 * S, 0.72 * S), (1.58 * S, 0.78 * S), (1.76 * S, 0.74 * S), (1.68 * S, 0.66 * S)]
    hp.add_tube(palm_pts, palm_rads, segs=14, uv_rect=UV_LEATHER)

    kn_pts = [to_w(+1.38, +1.35, +0.58), to_w(+1.46, +0.45, +0.66), to_w(+1.44, -0.45, +0.65), to_w(+1.32, -1.32, +0.56)]
    hp.add_tube(kn_pts, [0.36 * S] * 4, segs=10, uv_rect=UV_KNUCKLE)

    th_base = to_w(-0.55, +1.32, -0.22)
    th_dir0 = vnorm(vadd(vmul(F, 0.68), vadd(vmul(T_side, 0.66), vmul(U, -0.28))))
    th_bend_axis = vnorm(vsub(F, vmul(T_side, 0.45)))
    th_d1 = rot_axis(th_dir0, U, -side_sign * (thumb_abd - 30.0))
    th_d2 = rot_axis(th_d1, th_bend_axis, side_sign * 42.0 * thumb_curl)
    th_d3 = rot_axis(th_d2, th_bend_axis, side_sign * 52.0 * thumb_curl)
    tp0 = to_w(-1.10, +0.92, -0.25)
    tp1 = th_base
    tp2 = vadd(tp1, vmul(th_d1, 1.15 * S))
    tp3 = vadd(tp2, vmul(th_d2, 0.98 * S))
    tp4 = vadd(tp3, vmul(th_d3, 0.78 * S))
    hp.add_tube(
        [tp0, tp1, tp2, tp3, tp4],
        [0.64 * S, 0.56 * S, 0.46 * S, 0.41 * S, 0.34 * S],
        segs=10, uv_rect=UV_LEATHER,
    )

    t_offsets = (+1.22, +0.42, -0.38, -1.14)
    len_mults = (0.95, 1.04, 0.97, 0.80)
    rad_mults = (1.00, 1.04, 0.96, 0.86)
    for fi in range(4):
        c_val = finger_curls[fi]
        splay = finger_splay[fi]
        lm = len_mults[fi] * S
        rm = rad_mults[fi] * S
        mcp = to_w(+1.58 - 0.14 * abs(fi - 1.2), t_offsets[fi], -0.02)

        f_dir0 = rot_axis(F, U, -side_sign * splay)
        lat_axis = vnorm(vcross(U, f_dir0))
        a1 = 76.0 * c_val
        a2 = 88.0 * min(1.12, c_val * 1.06)
        a3 = 64.0 * min(1.12, c_val * 0.95)
        d1 = rot_axis(f_dir0, lat_axis, a1)
        d2 = rot_axis(f_dir0, lat_axis, a1 + a2)
        d3 = rot_axis(f_dir0, lat_axis, a1 + a2 + a3)

        p1 = vadd(mcp, vmul(d1, 1.22 * lm))
        p2 = vadd(p1, vmul(d2, 0.92 * lm))
        p3 = vadd(p2, vmul(d3, 0.68 * lm))
        hp.add_tube(
            [mcp, p1, p2, p3],
            [0.44 * rm, 0.40 * rm, 0.35 * rm, 0.29 * rm],
            segs=9, uv_rect=UV_PALM if c_val > 0.5 else UV_LEATHER,
        )

    wrist_dir0 = vnorm(vadd(vmul(F, -0.94), vadd(vmul(T_side, -0.14), vmul(U, -0.18))))
    arm_dir = vnorm(forearm_dir) if forearm_dir is not None else wrist_dir0
    cuff_dir1 = vnorm(vlerp(wrist_dir0, arm_dir, 0.55))
    w0 = to_w(-1.72, 0.0, -0.06)
    w1 = vadd(w0, vmul(cuff_dir1, 1.15 * S))
    w2 = vadd(w1, vmul(arm_dir, 2.70 * S))
    hp.add_tube(
        [w0, w1, w2],
        [(1.42 * S, 1.04 * S), (1.62 * S, 1.22 * S), (1.84 * S, 1.42 * S)],
        segs=14, uv_rect=UV_CUFF,
    )
    if forearm_len > 3.9:
        rem = forearm_len - 3.85
        w3 = vadd(w2, vmul(arm_dir, 0.45 * rem * S))
        w4 = vadd(w2, vmul(arm_dir, rem * S))
        hp.add_tube(
            [w2, w3, w4],
            [(1.76 * S, 1.38 * S), (2.05 * S, 1.66 * S), (2.28 * S, 1.88 * S)],
            segs=14, uv_rect=UV_SLEEVE,
        )

    return hp


# ===========================================================================
# 3. CONCEPT A (FLAGSHIP): 'THE MEGA-SLINGER' MK.II MAG-PNEUMATIC RAIL-CATAPULT
# ===========================================================================
SLINGER_MM_REST_X = 13.60
SLINGER_MM_REST_Z = 2.48


def build_slinger_static_parts():
    """Builds the sleek, zero-clipping Mk.II Mega-Slinger chassis & animated mechanisms:
      - 'receiver'   (mat='gun_metal'): swept multi-faceted gunmetal-titanium chassis, integrated reflex sight arch,
                                         brushed linear-accelerator twin rails, low-profile CNC V-cradle saddles,
                                         cantilevered muzzle cowls, copper booster coils, tucked copper pressure bottles,
                                         zero-clipping swept outrigger roller arms, contoured pistol grip & angled foregrip
      - 'dial_face'  (mat='gauge_glow'): canted illuminated 0-250 PSI pressure dial + twin cyan accelerator rail chevron
                                         strips + glowing cyan muzzle aperture rings!
      - 'ram'        (mat='gun_metal'): sleek crescent sabot pusher sled + twin mirror-chrome hydraulic piston rods
      - 'clamp_l', 'clamp_r' (mat='gun_metal'): sculpted hazard-trimmed magnetic retention claws
      - 'roller_l', 'roller_r' (mat='gun_metal'): tangent knurled brass under-tire spin-rollers (at 11.08, +/-5.72, -1.24)
      - 'elevator'   (mat='gun_metal'): spring-loaded under-rail feed cradle
      - 'trigger'    (mat='gun_metal'): curved steel trigger
      - 'psi_needle' (mat='gauge_glow'): 3D glowing red-orange PSI needle
    """
    UV_IRON = (0.02, 0.02, 0.48, 0.23)
    UV_RAIL = (0.02, 0.27, 0.48, 0.48)
    UV_HAZARD = (0.52, 0.02, 0.98, 0.23)
    UV_TANK = (0.52, 0.27, 0.98, 0.48)
    UV_SERIAL = (0.02, 0.52, 0.48, 0.73)
    UV_COIL = (0.52, 0.52, 0.73, 0.73)
    UV_HOSE = (0.77, 0.52, 0.98, 0.73)
    UV_GRIP = (0.02, 0.77, 0.48, 0.98)
    UV_ROD = (0.52, 0.77, 0.73, 0.98)
    UV_RAM = (0.77, 0.77, 0.98, 0.98)

    rec = MeshPart("gun_metal")

    # 1. Sleek Swept Multi-Faceted Aerospace/Quake Receiver Body (silky gunmetal-titanium, zero stretched text!)
    rec.add_loft(
        [
            (-0.35, 0.0, 1.24, +0.16, 1.18, 0.38),
            (+0.85, 0.0, 1.70, +0.02, 1.48, 0.42),
            (+7.20, 0.0, 1.62, -0.06, 1.40, 0.36),
            (+11.80, 0.0, 1.24, +0.08, 0.98, 0.26),
            (+17.40, 0.0, 1.00, +0.26, 0.74, 0.22),
            (+22.10, 0.0, 0.72, +0.46, 0.50, 0.16),
        ],
        uv_rect=UV_IRON, side_uv=UV_IRON, top_uv=UV_IRON, cap_start=False,
    )
    # Sculpted sloped carbon-polymer rear recoil buttcap (replaces flat pie-wedge octagon at rear!)
    rec.add_loft(
        [
            (-1.12, 0.0, 0.70, +0.22, 0.66, 0.26),
            (-0.74, 0.0, 1.04, +0.18, 0.98, 0.34),
            (-0.35, 0.0, 1.24, +0.16, 1.18, 0.38),
        ],
        uv_rect=UV_GRIP, side_uv=UV_GRIP, top_uv=UV_GRIP, cap_end=False,
    )
    # Crisp undistorted flat recessed 'MEGA-SLINGER // MK.II' side armor plates on BOTH cheeks (x = 5.65 .. 9.45)
    su0, sv0, su1, sv1 = UV_SERIAL
    for sgn in (-1.0, +1.0):
        y_rr = sgn * 1.635
        y_fr = sgn * 1.495
        # Subtle machined gunmetal bezel backing
        rec.add_loft(
            [
                (5.55, sgn * 1.56, 0.075, +0.18, 0.44, 0.04),
                (9.55, sgn * 1.42, 0.075, +0.18, 0.44, 0.04),
            ],
            uv_rect=UV_IRON, side_uv=UV_IRON,
        )
        # Outer face quad oriented left-to-right upright from EACH side's camera viewpoint!
        if sgn > 0:
            rec.add_quad(
                (5.65, y_rr, -0.22), (9.45, y_fr, -0.22),
                (9.45, y_fr, +0.58), (5.65, y_rr, +0.58),
                (su0, sv1), (su1, sv1), (su1, sv0), (su0, sv0),
                nrm=(0.036, +0.999, 0.0),
            )
        else:
            rec.add_quad(
                (9.45, y_fr, -0.22), (5.65, y_rr, -0.22),
                (5.65, y_rr, +0.58), (9.45, y_fr, +0.58),
                (su0, sv1), (su1, sv1), (su1, sv0), (su0, sv0),
                nrm=(0.036, -0.999, 0.0),
            )

    # 2. Integrated Armored Reflex Sight Arch (frames the glowing MEGA-CORE status bar cleanly for 1st-person POV!)
    for sgn in (-1.0, +1.0):
        rec.add_loft(
            [
                (+0.18, sgn * 1.16, 0.18, +1.52, 0.26, 0.05),
                (+0.72, sgn * 1.04, 0.16, +2.02, 0.44, 0.05),
                (+2.35, sgn * 1.02, 0.15, +1.96, 0.38, 0.05),
            ],
            uv_rect=UV_RAIL, side_uv=UV_IRON,
        )
    # Top armored reflex hood visor bridging the sight struts
    rec.add_loft(
        [
            (+0.38, 0.0, 1.12, +2.40, 0.11, 0.04),
            (+2.15, 0.0, 1.06, +2.34, 0.10, 0.04),
        ],
        uv_rect=UV_IRON, top_uv=UV_RAIL,
    )

    # 3. Twin Brushed-Titanium Linear-Accelerator Mag-Rails & Raked Muzzle Fangs (x = 2.4 .. 23.1)
    for sgn in (-1.0, +1.0):
        ry = sgn * 0.94
        rec.add_loft(
            [
                (+2.40, ry, 0.26, +1.30, 0.34, 0.08),
                (+19.80, ry, 0.26, +1.30, 0.34, 0.08),
                (+22.30, ry, 0.22, +1.32, 0.30, 0.07),
                (+23.15, ry, 0.10, +1.38, 0.14, 0.04),  # sleek raked forward rail fang!
            ],
            uv_rect=UV_RAIL, side_uv=UV_RAIL, top_uv=UV_RAIL,
        )
        # Inward T-slot magnetic guide flange
        rec.add_chamfer_box(2.7, 21.8, ry - sgn * 0.34, ry - sgn * 0.14, +1.44, +1.64, ch=0.03, uv_rect=UV_RAIL)

        # Wound Copper Electromagnetic Booster Coil (x = 18.2 .. 21.4) with crisp hard-edge machined bronze flanges!
        rec.add_lathe(
            (18.2, sgn * 1.18, +1.28), (1.0, 0.0, 0.0),
            [
                (0.00, 0.00, 0.00),
                (0.00, 0.44, 0.02),
                (0.00, 0.44, 0.02),  # crisp rear flange crease
                (0.24, 0.44, 0.08),
                (0.26, 0.38, 0.10),
                (2.94, 0.38, 0.90),
                (2.96, 0.44, 0.92),
                (3.20, 0.44, 0.98),
                (3.20, 0.44, 0.98),  # crisp front flange crease
                (3.20, 0.00, 1.00),
            ],
            segs=14, sy=0.82, sz=1.02, uv_rect=UV_COIL,
        )

        # Sleek Cantilevered Titanium Muzzle Brake Shroud wrapping outer side of copper coil (x = 17.8 .. 22.8)
        rec.add_loft(
            [
                (17.80, sgn * 1.42, 0.14, +1.18, 0.36, 0.05),
                (19.20, sgn * 1.50, 0.15, +1.26, 0.46, 0.06),
                (21.60, sgn * 1.46, 0.14, +1.28, 0.42, 0.06),
                (22.85, sgn * 1.28, 0.10, +1.32, 0.24, 0.04),
            ],
            uv_rect=UV_IRON, side_uv=UV_HAZARD, top_uv=UV_RAIL,
        )

    # Central recessed stainless sabot track floor
    rec.add_chamfer_box(2.8, 21.8, -0.68, +0.68, +0.86, +1.12, ch=0.04, uv_rect=UV_RAIL)

    # 4. Sleek Low-Profile CNC-Machined V-Cradle Axle Saddles & Angled Compensator Cheek Trim (ZERO brown Lego cubes!)
    for sgn in (-1.0, +1.0):
        # Sleek tapered hazard trim rail framing cleanly above the 'MEGA-SLINGER // MK.II' cheek armor plate
        rec.add_loft(
            [
                (4.60, sgn * 1.62, 0.10, +0.84, 0.18, 0.04),
                (11.60, sgn * 1.38, 0.09, +0.86, 0.17, 0.04),
            ],
            uv_rect=UV_HAZARD, side_uv=UV_HAZARD,
        )
        rec.add_loft(
            [
                (15.20, sgn * 1.28, 0.10, +0.76, 0.24, 0.04),
                (17.70, sgn * 1.36, 0.11, +0.92, 0.26, 0.04),
            ],
            uv_rect=UV_HAZARD, side_uv=UV_HAZARD,
        )
        # Sculpted low-profile V-notch axle cradle at x = 13.60 (ramps up smoothly, dips to z=2.22 right under r=0.23 axle!)
        sy_cr = sgn * 1.54
        # Rear cradle horn (x = 12.15 -> 13.48)
        rec.add_loft(
            [
                (12.10, sy_cr, 0.24, +1.22, 0.26, 0.06),
                (13.12, sy_cr, 0.28, +1.68, 0.68, 0.07),
                (13.52, sy_cr, 0.28, +1.52, 0.56, 0.06),
            ],
            uv_rect=UV_RAM, side_uv=UV_RAM, top_uv=UV_RAIL,
        )
        # Front cradle lip (x = 13.52 -> 15.05, lower forward lip so launched axle clears effortlessly!)
        rec.add_loft(
            [
                (13.52, sy_cr, 0.28, +1.52, 0.56, 0.06),
                (13.98, sy_cr, 0.28, +1.62, 0.62, 0.07),
                (15.05, sy_cr, 0.22, +1.22, 0.26, 0.06),
            ],
            uv_rect=UV_RAM, side_uv=UV_RAM, top_uv=UV_RAIL,
        )

    # 5. Zero-Clipping Tucked Copper High-Pressure Bottles (x = 2.4 .. 9.6) & Braided Stainless Manifolds
    for sgn in (-1.0, +1.0):
        ty = sgn * 1.76
        tz = -0.78
        rec.add_lathe(
            (2.40, ty, tz), (1.0, 0.0, 0.0),
            [
                (0.00, 0.00, 0.00),
                (0.18, 0.42, 0.03),
                (0.58, 0.60, 0.10),
                (6.62, 0.60, 0.90),
                (7.02, 0.42, 0.97),
                (7.20, 0.00, 1.00),
            ],
            segs=14, uv_rect=UV_TANK,
        )
        # Braided steel high-pressure line curving cleanly from rear of bottle into breech manifold
        hose_pts = [
            (2.50, ty, tz + 0.12),
            (1.55, sgn * 1.92, tz + 0.42),
            (1.28, sgn * 1.66, +0.42),
            (2.05, sgn * 1.28, +0.98),
        ]
        rec.add_tube(hose_pts, [0.15, 0.14, 0.14, 0.16], segs=8, uv_rect=UV_HOSE)

    # 6. Zero-Clipping Swept Aerodynamic Outrigger Wing-Pylons & Under-Roller Cradles (forward of x=9.6 bottles!)
    for sgn in (-1.0, +1.0):
        # Forward-swept wide airfoil pylon blending smoothly from lower receiver out to y = +/-4.85
        wing_pts = [
            (10.05, sgn * 1.12, -0.34),
            (10.65, sgn * 3.05, -0.92),
            (11.08, sgn * 4.86, -1.26),
        ]
        rec.add_tube(wing_pts, [(0.68, 0.22), (0.54, 0.19), (0.44, 0.17)], segs=10, uv_rect=UV_IRON)
        # Brushed-titanium upper pylon spine rib
        rib_pts = [
            (10.20, sgn * 1.18, -0.16),
            (10.74, sgn * 3.08, -0.74),
            (11.08, sgn * 4.84, -1.08),
        ]
        rec.add_tube(rib_pts, [(0.26, 0.11), (0.22, 0.10), (0.18, 0.09)], segs=8, uv_rect=UV_RAIL)
        # Sleek low-profile under-roller fender & outer axle bracket (z <= -1.58 -> 100% clear of R=4.52 tire!)
        y_in_b = min(sgn * 4.78, sgn * 6.64)
        y_out_b = max(sgn * 4.78, sgn * 6.64)
        rec.add_chamfer_box(10.58, 11.26, y_in_b, y_out_b, -1.90, -1.62, ch=0.05, uv_rect=UV_IRON, top_uv=UV_RAIL)
        # Inner & outer clevis bearing cheeks supporting roller axle at (11.08, +/-4.84 & +/-6.58, -1.24)
        rec.add_chamfer_box(10.72, 11.42, sgn * 4.82 - 0.12, sgn * 4.82 + 0.12, -1.78, -0.98, ch=0.04, uv_rect=UV_RAM)
        rec.add_chamfer_box(10.76, 11.38, sgn * 6.58 - 0.10, sgn * 6.58 + 0.10, -1.78, -1.02, ch=0.04, uv_rect=UV_RAM)

        # Crisp hard-edge machined brass hydraulic piston gland at front of sight block
        rec.add_lathe(
            (2.05, sgn * 0.50, +1.54), (1.0, 0.0, 0.0),
            [
                (0.00, 0.00, 0.00),
                (0.00, 0.28, 0.08),
                (0.00, 0.28, 0.08),
                (1.10, 0.28, 0.90),
                (1.10, 0.28, 0.90),
                (1.12, 0.17, 1.00),
            ],
            segs=10, uv_rect=UV_RAM,
        )

    # 7. Contoured Carbon-Polymer Pistol Grip + Trigger Guard + Angled Forward Tactical Grip (zero hand clipping!)
    grip_pts = [
        (3.20, 0.0, -1.32),
        (2.68, 0.0, -2.68),
        (2.08, 0.0, -4.08),
        (1.62, 0.0, -5.22),
    ]
    rec.add_tube(grip_pts, [(0.88, 0.62), (0.84, 0.58), (0.82, 0.56), (0.92, 0.64)], segs=10, uv_rect=UV_GRIP)
    tg_pts = [(4.95, 0.0, -1.42), (4.72, 0.0, -2.58), (3.52, 0.0, -2.84), (2.75, 0.0, -2.48)]
    rec.add_tube(tg_pts, [0.12] * 4, segs=8, uv_rect=UV_IRON)

    # Angled forward ergonomic support grip (x = 11.55 -> 10.45, z = -0.88 -> -3.55)
    fg_pts = [
        (11.55, 0.0, -0.88),
        (11.15, 0.0, -1.85),
        (10.75, 0.0, -2.78),
        (10.45, 0.0, -3.52),
    ]
    rec.add_tube(fg_pts, [(0.74, 0.56), (0.68, 0.54), (0.66, 0.52), (0.74, 0.58)], segs=10, uv_rect=UV_GRIP)

    # 8. Prominent Canted Brass 0-250 PSI Pressure Gauge Pod (mounted at (4.35, +1.76, +1.58), clear in 1st-person POV!)
    dial_center = (4.35, +1.76, +1.58)
    dial_axis = vnorm((-0.86, +0.28, +0.42))
    # Angled manifold stalk connecting receiver cheek to brass gauge bezel
    rec.add_tube([(4.75, +1.32, +1.12), vsub(dial_center, vmul(dial_axis, 0.32))], [0.34, 0.44], segs=8, uv_rect=UV_IRON)
    rec.add_lathe(
        dial_center, dial_axis,
        [
            (-0.48, 0.00, 0.00),
            (-0.48, 0.90, 0.08),
            (-0.48, 0.90, 0.08),  # crisp rear bezel crease
            (+0.05, 0.94, 0.80),
            (+0.13, 0.86, 0.94),
            (+0.13, 0.86, 0.94),  # crisp front rim lip!
            (+0.03, 0.80, 1.00),
        ],
        segs=20, uv_rect=UV_RAM,
    )

    # Illuminated PSI Dial Face + Twin Linear-Accelerator Cyan Chevron Strips + Muzzle Glow Rings ('gauge_glow' mat!)
    dial_face = MeshPart("gauge_glow")
    dial_face.add_lathe(
        dial_center, dial_axis,
        [(+0.04, 0.80, 1.0, 0.80), (+0.04, 0.00, 0.0, 0.80)],
        segs=24, uv_mode="polar", uv_rect=(0.01, 0.01, 0.615, 0.615),
    )

    # Twin Glowing Electric-Cyan Linear-Accelerator Chevron Strips inlaid along BOTH rails (x = 3.8 .. 21.8)!
    # Tiled in 3 segments along X so 18 crisp '>>>' plasma chevrons march forward toward the muzzle!
    for sgn in (-1.0, +1.0):
        ry = sgn * 0.94
        for seg_i in range(3):
            xa = 3.80 + seg_i * 6.00
            xb = xa + 5.85
            # Top-inward rail plasma strip (tilted toward centerline & camera so both rails gleam in POV & Orbit!)
            y_out = ry + sgn * 0.10
            y_in = ry - sgn * 0.22
            dial_face.add_quad(
                (xa, y_out, +1.655), (xb, y_out, +1.655),
                (xb, y_in, +1.652), (xa, y_in, +1.652),
                (0.635, 0.270), (0.990, 0.270), (0.990, 0.440), (0.635, 0.440),
                nrm=(0.0, 0.0, 1.0),
            )
        # Outer rail accent glow line on left (+Y, player-facing) & right (-Y) muzzle cowls
        dial_face.add_quad(
            (18.2, sgn * 1.655, +1.36), (22.2, sgn * 1.545, +1.36),
            (22.2, sgn * 1.545, +1.20), (18.2, sgn * 1.655, +1.20),
            (0.635, 0.270), (0.990, 0.270), (0.990, 0.440), (0.635, 0.440),
            nrm=(0.0, sgn, 0.0),
        )
        # Glowing cyan induction ring at front face of each copper booster coil (x = 21.45)
        dial_face.add_lathe(
            (21.44, sgn * 1.18, +1.28), (1.0, 0.0, 0.0),
            [(0.0, 0.20, 0.48), (0.02, 0.41, 0.62), (0.0, 0.42, 0.64)],
            segs=14, sy=0.82, sz=1.02, uv_rect=(0.64, 0.47, 0.98, 0.64),
        )

    # 3D Red-Orange Indicator Needle
    needle = MeshPart("gauge_glow")
    X_d, Y_d, Z_d = basis_from_axis(dial_axis)
    n_p0 = vadd(vmul(X_d, 0.075), vmul(Z_d, -0.17))
    n_p1 = vadd(vmul(X_d, 0.075), vmul(Z_d, +0.67))
    needle.add_tube([n_p0, n_p1], [0.056, 0.018], segs=6, uv_rect=(0.64, 0.02, 0.98, 0.23))

    # 9. Sleek Machined Crescent Sabot Sled ('ram') + Twin Mirror-Chrome Hydraulic Rods (NO tall square brick!)
    ram = MeshPart("gun_metal")
    # Sloped aerodynamic sabot carriage base
    ram.add_loft(
        [
            (-1.42, 0.0, 0.66, +1.42, 0.30, 0.10),
            (-0.55, 0.0, 0.80, +1.58, 0.44, 0.12),
            (+0.08, 0.0, 0.74, +1.62, 0.42, 0.10),
        ],
        uv_rect=UV_RAM, top_uv=UV_RAM,
    )
    # Curved U-crescent pusher cradle hugging the lower-rear contour of Mega Man's r=0.70 rubber end-cap (at z=2.48)!
    cres_pts = []
    for k in range(7):
        ang = math.radians(-150.0 + k * 20.0)  # wraps lower semi-circle from left-horn (-150) under bottom (-90) to right-horn (-30)!
        # Wait: in (Y, Z),ang=0 -> +Y, ang=-90 -> -Z? Let's write explicit (y, z) around (0, 2.48) with radius 0.80!
        th = math.radians(-105.0 + k * 35.0)  # -105 deg .. +105 deg from -Z bottom!
        cy_p = 0.82 * math.sin(th)
        cz_p = 2.48 - 0.82 * math.cos(th)
        cres_pts.append((-0.08 + 0.14 * abs(math.sin(th)), cy_p, cz_p))
    ram.add_tube(cres_pts, [0.16, 0.19, 0.21, 0.22, 0.21, 0.19, 0.16], segs=8, uv_rect=UV_HAZARD)

    # Twin mirror-chrome hydraulic piston rods
    for sgn in (-1.0, +1.0):
        ram.add_lathe(
            (-7.85, sgn * 0.50, +1.54), (1.0, 0.0, 0.0),
            [(0.0, 0.155, 0.05), (6.50, 0.155, 0.95)],
            segs=12, uv_rect=UV_ROD,
        )

    # 10. Sculpted Magnetic Retention Claws ('clamp_l', 'clamp_r' pivoting around y = +/-1.18, z = 1.48)
    clamp_l = MeshPart("gun_metal")
    clamp_r = MeshPart("gun_metal")
    for sgn, cp in ((+1.0, clamp_l), (-1.0, clamp_r)):
        for cx_off in (10.55, 16.45):
            jaw_pts = [
                (cx_off, 0.0, 0.0),
                (cx_off, sgn * 0.20, +0.58),
                (cx_off, -sgn * 0.14, +1.14),
                (cx_off, -sgn * 0.44, +1.34),
            ]
            cp.add_tube(jaw_pts, [(0.24, 0.18), (0.20, 0.16), (0.16, 0.13), (0.12, 0.10)], segs=8, uv_rect=UV_HAZARD)

    # 11. Tangent Knurled Dark-Titanium Under-Tire Spin-Rollers ('roller_l', 'roller_r' at (11.08, +/-5.72, -1.24), R=0.48)
    roller_l = MeshPart("gun_metal")
    roller_r = MeshPart("gun_metal")
    for rp in (roller_l, roller_r):
        # Dark diamond-knurled drive barrel
        rp.add_lathe(
            (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
            [
                (-0.66, 0.44, 0.05),
                (-0.64, 0.48, 0.10),
                (+0.64, 0.48, 0.90),
                (+0.66, 0.44, 0.95),
            ],
            segs=12, uv_rect=UV_GRIP,
        )
        # Machined brushed-titanium end-collars & axle spindle caps
        for s_end in (-1.0, +1.0):
            y_in_r, y_out_r = (0.64 * s_end, 0.78 * s_end) if s_end > 0 else (-0.78, -0.64)
            rp.add_lathe(
                (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                [
                    (y_in_r, 0.00, 0.00),
                    (y_in_r, 0.46, 0.15),
                    (y_out_r, 0.46, 0.85),
                    (y_out_r, 0.00, 1.00),
                ],
                segs=10, uv_rect=UV_RAIL,
            )

    # 12. Under-Slung Spring Elevator Fork ('elevator')
    elev = MeshPart("gun_metal")
    elev.add_chamfer_box(12.3, 14.9, -1.24, +1.24, -0.30, +0.10, ch=0.06, uv_rect=UV_RAM)
    for sgn in (-1.0, +1.0):
        elev.add_lathe(
            (13.6, sgn * 0.68, -2.35), (0.0, 0.0, 1.0),
            [(0.0, 0.20, 0.05), (2.08, 0.20, 0.95)],
            segs=10, uv_rect=UV_ROD,
        )

    # 13. Curved Machined Steel Trigger
    trig = MeshPart("gun_metal")
    trig.add_tube(
        [(0.0, 0.0, 0.0), (-0.12, 0.0, -0.46), (+0.09, 0.0, -0.88)],
        [0.13, 0.11, 0.085], segs=8, uv_rect=UV_ROD,
    )

    return {
        "receiver": rec,
        "dial_face": dial_face,
        "dial_meta": (dial_center, dial_axis),
        "psi_needle": needle,
        "ram": ram,
        "clamp_l": clamp_l,
        "clamp_r": clamp_r,
        "roller_l": roller_l,
        "roller_r": roller_r,
        "elevator": elev,
        "trigger": trig,
    }


def build_slinger_fx_frame(blast_amp, arc_amp, steam_amp, frame_idx):
    """Fixed-topology volumetric 3D FX ('fx' additive mat):
      1. Translucent hollow-center electric-cyan supersonic Mach shock-ring (feathered inner & outer edges -> zero white pancake!)
      2. 3 slender crossed 3D starburst railgun muzzle flash spikes (volumetric from both POV & Orbit!)
      3. Twin jagged rail plasma lightning arcs + muzzle-coil cross-arc (mapped to Q1)
      4. High-impact forward-visible angled compensator gas plumes at x=16.4 + breech relief vents at x=6.8 (mapped to Right Half)
    """
    fx = MeshPart("fx")
    UV_ARC = (0.03, 0.03, 0.47, 0.47)
    UV_FLASH = (0.02, 0.52, 0.48, 0.98)
    UV_STEAM = (0.53, 0.04, 0.97, 0.96)
    PARK = (6.0, 0.0, 0.35)

    # 1) Translucent Hollow-Ring Electric-Cyan Supersonic Mach Halo (active ONLY when blast_amp > 0.01!)
    if blast_amp > 0.01:
        cone_x0 = 22.55 + 3.4 * (1.0 - blast_amp)
        cone_r = 2.0 + 3.8 * blast_amp
        cone_len = 2.2 * blast_amp
        r_in = cone_r * 0.40
        r_mid = cone_r * 0.68
        # Both inner (r_in/r_in=1.0) and outer (cone_r/cone_r=1.0) lips sample UV edge (alpha=0),
        # while crest (r_mid/(r_mid/0.54)=0.54) samples the pure electric-cyan halo band!
        fx.add_lathe(
            (cone_x0, 0.0, SLINGER_MM_REST_Z - 0.18), (1.0, 0.0, 0.0),
            [
                (+cone_len * 0.30, r_in, 0.00, r_in),
                (+0.00, r_mid, 0.50, r_mid / 0.54),
                (-cone_len * 0.65, cone_r, 1.00, cone_r),
            ],
            segs=28, uv_mode="polar", uv_rect=UV_FLASH,
        )
        fx.add_lathe(
            (cone_x0, 0.0, SLINGER_MM_REST_Z - 0.18), (-1.0, 0.0, 0.0),
            [
                (-cone_len * 0.30, r_in, 0.00, r_in),
                (+0.00, r_mid, 0.50, r_mid / 0.54),
                (+cone_len * 0.65, cone_r, 1.00, cone_r),
            ],
            segs=28, uv_mode="polar", uv_rect=UV_FLASH,
        )
    else:
        for s_ax in (+1.0, -1.0):
            fx.add_lathe(
                PARK, (s_ax, 0.0, 0.0),
                [(0.0, 0.001, 0.0, 0.001), (0.001, 0.001, 0.5, 0.001), (0.002, 0.001, 1.0, 0.001)],
                segs=28, uv_mode="polar", uv_rect=UV_FLASH,
            )

    # 2) 3 Slender Crossed Starburst Muzzle Flash Spikes (0, 60, 120 deg around +X)
    uc_f = 0.5 * (UV_FLASH[0] + UV_FLASH[2])
    vc_f = 0.5 * (UV_FLASH[1] + UV_FLASH[3])
    ru_f = 0.48 * (UV_FLASH[2] - UV_FLASH[0])
    rv_f = 0.48 * (UV_FLASH[3] - UV_FLASH[1])
    for fi_k in range(3):
        ang = math.radians(fi_k * 60.0 + frame_idx * 17.0)
        dy = math.cos(ang)
        dz = math.sin(ang)
        if blast_amp > 0.01:
            cz = SLINGER_MM_REST_Z - 0.18
            x0, x1 = 21.65, 22.85 + 7.2 * blast_amp
            hw = (0.78 + 1.25 * blast_amp) * (1.0 if fi_k != 1 else 0.80)
            p0 = (x0, -dy * hw, cz - dz * hw)
            p1 = (x1, -dy * hw * 0.42, cz - dz * hw * 0.42)
            p2 = (x1, +dy * hw * 0.42, cz + dz * hw * 0.42)
            p3 = (x0, +dy * hw, cz + dz * hw)
        else:
            p0 = p1 = p2 = p3 = PARK
        fx.add_quad(
            p0, p1, p2, p3,
            (uc_f - ru_f, vc_f - rv_f), (uc_f + ru_f, vc_f - rv_f),
            (uc_f + ru_f, vc_f + rv_f), (uc_f - ru_f, vc_f + rv_f),
            two_sided=True,
        )

    # 3) Twin Jagged Rail Plasma Lightning Arcs + Muzzle Booster Cross-Arc
    for bi, sgn in enumerate((-1.0, +1.0)):
        pts = []
        for s in range(9):
            t = s / 8.0
            if arc_amp > 0.01:
                env = math.sin(t * math.pi)
                ph = frame_idx * 2.9 + bi * 2.1 + s * 1.85
                jy = 0.30 * arc_amp * math.sin(ph) * env
                jz = 0.28 * arc_amp * math.cos(ph * 1.37) * env
                pts.append((4.8 + 17.8 * t, sgn * 0.94 + jy, 1.72 + jz))
            else:
                pts.append((PARK[0] + 0.01 * s, PARK[1], PARK[2]))
        r_b = 0.15 * arc_amp if arc_amp > 0.01 else 0.001
        rads = [r_b * 0.35, r_b * 0.9, r_b * 1.15, r_b * 0.95, r_b * 1.2, r_b * 0.95, r_b * 1.1, r_b * 0.85, r_b * 0.35]
        fx.add_tube(pts, rads, segs=6, uv_rect=UV_ARC)

    # Cross-muzzle plasma bridge arc between left & right copper booster coils (x = 21.6)
    c_pts = []
    for s in range(6):
        t = s / 5.0
        if arc_amp > 0.01:
            ph = frame_idx * 3.4 + s * 2.1
            c_pts.append((
                21.55 + 0.22 * arc_amp * math.sin(ph),
                -1.18 + 2.36 * t,
                1.48 + 0.55 * math.sin(t * math.pi) + 0.16 * arc_amp * math.cos(ph),
            ))
        else:
            c_pts.append((PARK[0] + 0.01 * s, PARK[1], PARK[2]))
    rc = 0.13 * arc_amp if arc_amp > 0.01 else 0.001
    fx.add_tube(c_pts, [rc * 0.4, rc, rc * 1.15, rc * 1.15, rc, rc * 0.4], segs=6, uv_rect=UV_ARC)

    # 4) High-Impact Forward-Visible Angled Compensator Exhaust Plumes (x = 16.4, right in POV!) + Breech Vents (x = 6.8)
    for x_vent, scale_v in ((16.4, 1.00), (6.8, 0.78)):
        for sgn in (-1.0, +1.0):
            if steam_amp > 0.01:
                L = 5.4 * steam_amp * scale_v
                s_pts = [
                    (x_vent + 0.12, sgn * 1.18, +1.00),
                    (x_vent - 0.10 * L, sgn * (1.34 + 0.28 * L), +1.08 + 0.20 * L),
                    (x_vent - 0.26 * L, sgn * (1.38 + 0.68 * L), +1.08 + 0.50 * L),
                    (x_vent - 0.44 * L, sgn * (1.42 + 1.12 * L), +1.08 + 0.84 * L),
                ]
                s_rad = [0.14 * steam_amp * scale_v, 0.38 * steam_amp * scale_v, 0.78 * steam_amp * scale_v, 1.24 * steam_amp * scale_v]
            else:
                s_pts = [PARK, (PARK[0] + 0.01, PARK[1], PARK[2]), (PARK[0] + 0.02, PARK[1], PARK[2]), (PARK[0] + 0.03, PARK[1], PARK[2])]
                s_rad = [0.001, 0.001, 0.001, 0.001]
            fx.add_tube(s_pts, s_rad, segs=8, uv_rect=UV_STEAM, cap_start=False, cap_end=False)

    return fx
