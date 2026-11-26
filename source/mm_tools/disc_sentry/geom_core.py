"""Procedural 3D geometry primitives and transform helpers for Disc Sentry Gun concepts.

Coordinate system (Quake / DarkPlaces MD3 standard):
  +X = forward (barrel / CRT front direction)
  +Y = left
  +Z = up
  Z = 0 is the ground contact plane for bases.
"""
from __future__ import annotations

import math
from typing import Callable, Iterable, List, Sequence, Tuple

Vec3 = Tuple[float, float, float]
UV2 = Tuple[float, float]
UVBox = Tuple[float, float, float, float]


def vadd(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vmul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vlen(a: Vec3) -> float:
    return math.sqrt(max(0.0, vdot(a, a)))


def vnorm(a: Vec3) -> Vec3:
    l = vlen(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-9 else (0.0, 0.0, 1.0)


def vlerp(a: Vec3, b: Vec3, t: float) -> Vec3:
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def rot_x(p: Vec3, deg: float) -> Vec3:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y(p: Vec3, deg: float) -> Vec3:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def rot_z(p: Vec3, deg: float) -> Vec3:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def rot_axis(v: Vec3, axis: Vec3, deg: float) -> Vec3:
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


def frame_basis(t: Vec3) -> Tuple[Vec3, Vec3, Vec3]:
    t = vnorm(t)
    ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.88 else (1.0, 0.0, 0.0)
    u = vnorm(vcross(t, ref))
    v = vcross(t, u)
    return t, u, v


class MeshPart:
    """Static-topology triangle mesh builder with outward normals & UVs."""

    def __init__(self, name: str = "part"):
        self.name = name
        self.verts: List[Vec3] = []
        self.norms: List[Vec3] = []
        self.st: List[UV2] = []
        self.tris: List[Tuple[int, int, int]] = []

    def clone(self) -> "MeshPart":
        m = MeshPart(self.name)
        m.verts = list(self.verts)
        m.norms = list(self.norms)
        m.st = list(self.st)
        m.tris = list(self.tris)
        return m

    def append(
        self,
        other: "MeshPart",
        xform_pt: Callable[[Vec3], Vec3] | None = None,
        xform_nrm: Callable[[Vec3], Vec3] | None = None,
    ) -> None:
        b = len(self.verts)
        if xform_pt is None:
            self.verts.extend(other.verts)
        else:
            self.verts.extend(xform_pt(p) for p in other.verts)
        if xform_nrm is None:
            self.norms.extend(other.norms)
        else:
            self.norms.extend(vnorm(xform_nrm(n)) for n in other.norms)
        self.st.extend(other.st)
        self.tris.extend((i0 + b, i1 + b, i2 + b) for (i0, i1, i2) in other.tris)

    def add_quad(
        self,
        p0: Vec3,
        p1: Vec3,
        p2: Vec3,
        p3: Vec3,
        uv0: UV2,
        uv1: UV2,
        uv2: UV2,
        uv3: UV2,
        nrm: Vec3 | None = None,
    ) -> None:
        if nrm is None:
            nrm = vnorm(vcross(vsub(p1, p0), vsub(p2, p0)))
        b = len(self.verts)
        self.verts.extend([p0, p1, p2, p3])
        self.norms.extend([nrm, nrm, nrm, nrm])
        self.st.extend([uv0, uv1, uv2, uv3])
        self.tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])

    def add_box(
        self,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        z0: float,
        z1: float,
        uv_all: UVBox,
        uv_px: UVBox | None = None,
        uv_nx: UVBox | None = None,
        uv_py: UVBox | None = None,
        uv_ny: UVBox | None = None,
        uv_pz: UVBox | None = None,
        uv_nz: UVBox | None = None,
        skip_bottom: bool = False,
    ) -> None:
        upx = uv_px or uv_all
        unx = uv_nx or uv_all
        upy = uv_py or uv_all
        uny = uv_ny or uv_all
        upz = uv_pz or uv_all
        unz = uv_nz or uv_all

        # +X face (viewer at +X looking -X: left=-Y, right=+Y, top=+Z)
        self.add_quad(
            (x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1),
            (upx[0], upx[1]), (upx[0], upx[3]), (upx[2], upx[3]), (upx[2], upx[1]),
            nrm=(1.0, 0.0, 0.0),
        )
        # -X face
        self.add_quad(
            (x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1),
            (unx[0], unx[1]), (unx[0], unx[3]), (unx[2], unx[3]), (unx[2], unx[1]),
            nrm=(-1.0, 0.0, 0.0),
        )
        # +Y face
        self.add_quad(
            (x1, y1, z1), (x1, y1, z0), (x0, y1, z0), (x0, y1, z1),
            (upy[0], upy[1]), (upy[0], upy[3]), (upy[2], upy[3]), (upy[2], upy[1]),
            nrm=(0.0, 1.0, 0.0),
        )
        # -Y face
        self.add_quad(
            (x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1),
            (uny[0], uny[1]), (uny[0], uny[3]), (uny[2], uny[3]), (uny[2], uny[1]),
            nrm=(0.0, -1.0, 0.0),
        )
        # +Z top
        self.add_quad(
            (x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1),
            (upz[0], upz[1]), (upz[0], upz[3]), (upz[2], upz[3]), (upz[2], upz[1]),
            nrm=(0.0, 0.0, 1.0),
        )
        if not skip_bottom:
            self.add_quad(
                (x1, y1, z0), (x1, y0, z0), (x0, y0, z0), (x0, y1, z0),
                (unz[0], unz[1]), (unz[0], unz[3]), (unz[2], unz[3]), (unz[2], unz[1]),
                nrm=(0.0, 0.0, -1.0),
            )

    def add_frustum(
        self,
        bot: Sequence[Vec3],
        top: Sequence[Vec3],
        uv_side: UVBox,
        uv_top: UVBox | None = None,
        uv_bot: UVBox | None = None,
        cap_top: bool = True,
        cap_bot: bool = True,
    ) -> None:
        """4-corner frustum where corners around Z are ordered CCW from above."""
        ut = uv_top or uv_side
        ub = uv_bot or uv_side
        for i in range(4):
            j = (i + 1) % 4
            self.add_quad(
                top[i], bot[i], bot[j], top[j],
                (uv_side[0], uv_side[1]), (uv_side[0], uv_side[3]),
                (uv_side[2], uv_side[3]), (uv_side[2], uv_side[1]),
            )
        if cap_top:
            self.add_quad(
                top[0], top[1], top[2], top[3],
                (ut[0], ut[1]), (ut[0], ut[3]), (ut[2], ut[3]), (ut[2], ut[1]),
            )
        if cap_bot:
            self.add_quad(
                bot[3], bot[2], bot[1], bot[0],
                (ub[0], ub[1]), (ub[0], ub[3]), (ub[2], ub[3]), (ub[2], ub[1]),
            )

    def add_cylinder(
        self,
        p0: Vec3,
        p1: Vec3,
        r0: float,
        r1: float,
        uv_side: UVBox,
        uv_cap: UVBox | None = None,
        segs: int = 14,
        cap0: bool = True,
        cap1: bool = True,
    ) -> None:
        uc = uv_cap or uv_side
        axis = vsub(p1, p0)
        if vlen(axis) < 1e-6:
            return
        t, u, v = frame_basis(axis)
        ring0, ring1 = [], []
        for s in range(segs):
            ang = 2.0 * math.pi * s / segs
            ca, sa = math.cos(ang), math.sin(ang)
            n = vadd(vmul(u, ca), vmul(v, sa))
            ring0.append((vadd(p0, vmul(n, r0)), n))
            ring1.append((vadd(p1, vmul(n, r1)), n))

        for s in range(segs):
            sn = (s + 1) % segs
            u0 = uv_side[0] + (uv_side[2] - uv_side[0]) * (s / segs)
            u1 = uv_side[0] + (uv_side[2] - uv_side[0]) * ((s + 1) / segs)
            q0, n0 = ring0[s]
            q1, n1 = ring0[sn]
            q2, _ = ring1[sn]
            q3, _ = ring1[s]
            b = len(self.verts)
            self.verts.extend([q0, q1, q2, q3])
            self.norms.extend([n0, n1, n1, n0])
            self.st.extend([(u0, uv_side[3]), (u1, uv_side[3]), (u1, uv_side[1]), (u0, uv_side[1])])
            self.tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])

        ucm = 0.5 * (uc[0] + uc[2])
        vcm = 0.5 * (uc[1] + uc[3])
        ur = 0.45 * (uc[2] - uc[0])
        vr = 0.45 * (uc[3] - uc[1])
        if cap0:
            c0 = len(self.verts)
            self.verts.append(p0)
            self.norms.append(vmul(t, -1.0))
            self.st.append((ucm, vcm))
            for s in range(segs):
                ang = 2.0 * math.pi * s / segs
                self.verts.append(ring0[s][0])
                self.norms.append(vmul(t, -1.0))
                self.st.append((ucm + ur * math.cos(ang), vcm + vr * math.sin(ang)))
            for s in range(segs):
                self.tris.append((c0, c0 + 1 + ((s + 1) % segs), c0 + 1 + s))
        if cap1:
            c1 = len(self.verts)
            self.verts.append(p1)
            self.norms.append(t)
            self.st.append((ucm, vcm))
            for s in range(segs):
                ang = 2.0 * math.pi * s / segs
                self.verts.append(ring1[s][0])
                self.norms.append(t)
                self.st.append((ucm + ur * math.cos(ang), vcm + vr * math.sin(ang)))
            for s in range(segs):
                self.tris.append((c1, c1 + 1 + s, c1 + 1 + ((s + 1) % segs)))

    def add_tube(
        self,
        pts: Sequence[Vec3],
        rads: Sequence[float],
        uv_box: UVBox,
        segs: int = 8,
        cap_start: bool = True,
        cap_end: bool = True,
    ) -> None:
        npts = len(pts)
        assert npts >= 2 and len(rads) == npts
        rings = []
        u_prev = None
        for i in range(npts):
            if i == 0:
                tang = vsub(pts[1], pts[0])
            elif i == npts - 1:
                tang = vsub(pts[-1], pts[-2])
            else:
                tang = vadd(vnorm(vsub(pts[i], pts[i - 1])), vnorm(vsub(pts[i + 1], pts[i])))
            tang = vnorm(tang)
            if u_prev is None:
                _, u, v = frame_basis(tang)
            else:
                proj = vsub(u_prev, vmul(tang, vdot(u_prev, tang)))
                u = vnorm(proj) if vlen(proj) > 1e-4 else frame_basis(tang)[1]
                v = vcross(tang, u)
            u_prev = u
            r = rads[i]
            ring = []
            for s in range(segs):
                ang = 2.0 * math.pi * s / segs
                n = vadd(vmul(u, math.cos(ang)), vmul(v, math.sin(ang)))
                ring.append((vadd(pts[i], vmul(n, r)), vnorm(n)))
            rings.append(ring)

        for i in range(npts - 1):
            v0 = uv_box[1] + (uv_box[3] - uv_box[1]) * (i / (npts - 1))
            v1 = uv_box[1] + (uv_box[3] - uv_box[1]) * ((i + 1) / (npts - 1))
            for s in range(segs):
                sn = (s + 1) % segs
                u0 = uv_box[0] + (uv_box[2] - uv_box[0]) * (s / segs)
                u1 = uv_box[0] + (uv_box[2] - uv_box[0]) * ((s + 1) / segs)
                p0, n0 = rings[i][s]
                p1, n1 = rings[i][sn]
                p2, n2 = rings[i + 1][sn]
                p3, n3 = rings[i + 1][s]
                b = len(self.verts)
                self.verts.extend([p0, p1, p2, p3])
                self.norms.extend([n0, n1, n2, n3])
                self.st.extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
                self.tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])

        uc = 0.5 * (uv_box[0] + uv_box[2])
        vc = 0.5 * (uv_box[1] + uv_box[3])
        if cap_start:
            tang0 = vnorm(vsub(pts[0], pts[1]))
            c0 = len(self.verts)
            self.verts.append(pts[0])
            self.norms.append(tang0)
            self.st.append((uc, vc))
            for s in range(segs):
                self.verts.append(rings[0][s][0])
                self.norms.append(tang0)
                self.st.append((uc, vc))
            for s in range(segs):
                self.tris.append((c0, c0 + 1 + ((s + 1) % segs), c0 + 1 + s))
        if cap_end:
            tang1 = vnorm(vsub(pts[-1], pts[-2]))
            c1 = len(self.verts)
            self.verts.append(pts[-1])
            self.norms.append(tang1)
            self.st.append((uc, vc))
            for s in range(segs):
                self.verts.append(rings[-1][s][0])
                self.norms.append(tang1)
                self.st.append((uc, vc))
            for s in range(segs):
                self.tris.append((c1, c1 + 1 + s, c1 + 1 + ((s + 1) % segs)))

    def add_sphere(self, center: Vec3, radius: float, uv_box: UVBox, stacks: int = 8, slices: int = 12) -> None:
        cx, cy, cz = center
        grid = []
        for i in range(stacks + 1):
            phi = math.pi * i / stacks
            sp, cp = math.sin(phi), math.cos(phi)
            row = []
            for j in range(slices + 1):
                th = 2.0 * math.pi * j / slices
                n = (sp * math.cos(th), sp * math.sin(th), cp)
                p = (cx + radius * n[0], cy + radius * n[1], cz + radius * n[2])
                u = uv_box[0] + (uv_box[2] - uv_box[0]) * (j / slices)
                v = uv_box[1] + (uv_box[3] - uv_box[1]) * (i / stacks)
                idx = len(self.verts)
                self.verts.append(p)
                self.norms.append(n)
                self.st.append((u, v))
                row.append(idx)
            grid.append(row)
        for i in range(stacks):
            for j in range(slices):
                a, b, c, d = grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]
                if i > 0:
                    self.tris.append((a, b, d))
                if i < stacks - 1:
                    self.tris.append((b, c, d))


def xform_part_vn(
    part: MeshPart,
    offset: Vec3 = (0.0, 0.0, 0.0),
    rx: float = 0.0,
    ry: float = 0.0,
    rz: float = 0.0,
    pivot: Vec3 = (0.0, 0.0, 0.0),
    scale: Vec3 | float = 1.0,
) -> Tuple[List[Vec3], List[Vec3]]:
    """Transform vertices & normals around pivot without altering topology."""
    sx, sy, sz = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    px, py, pz = pivot
    ox, oy, oz = offset
    vv: List[Vec3] = []
    nn: List[Vec3] = []
    for p, n in zip(part.verts, part.norms):
        q = ((p[0] - px) * sx, (p[1] - py) * sy, (p[2] - pz) * sz)
        qn = n
        if rx:
            q, qn = rot_x(q, rx), rot_x(qn, rx)
        if ry:
            q, qn = rot_y(q, ry), rot_y(qn, ry)
        if rz:
            q, qn = rot_z(q, rz), rot_z(qn, rz)
        vv.append((q[0] + px + ox, q[1] + py + oy, q[2] + pz + oz))
        nn.append(vnorm(qn))
    return vv, nn


def combine_parts_frames(
    named_parts: Sequence[Tuple[MeshPart, Sequence[Tuple[List[Vec3], List[Vec3]]]]],
) -> Tuple[MeshPart, List[Tuple[List[Vec3], List[Vec3]]]]:
    """Combine multiple animated sub-parts (sharing a shader) into one surface's frames."""
    merged = MeshPart("merged")
    nf = len(named_parts[0][1])
    for part, _ in named_parts:
        merged.append(part)
    frames_out: List[Tuple[List[Vec3], List[Vec3]]] = []
    for fi in range(nf):
        fv: List[Vec3] = []
        fn: List[Vec3] = []
        for _, fvn in named_parts:
            vv, nn = fvn[fi]
            fv.extend(vv)
            fn.extend(nn)
        frames_out.append((fv, fn))
    return merged, frames_out


def build_floppy_disk_mesh(half_w: float = 3.2, half_h: float = 3.4, half_t: float = 0.24) -> MeshPart:
    """Detailed 3D 3.5" floppy disk centered at (0,0,0):
      - Front label face at +X (+half_t)
      - Back spindle hub face at -X (-half_t)
      - Top sliding stainless shutter edge at +Z (+half_h)
      - Chamfered top-right corner, recessed shutter pocket, stepped 3D metal shutter!
    """
    m = MeshPart("floppy")
    UV_FRONT = (0.01, 0.01, 0.49, 0.49)
    UV_BACK = (0.51, 0.01, 0.99, 0.49)
    UV_SHUTTER = (0.01, 0.51, 0.49, 0.99)
    UV_RIM = (0.51, 0.51, 0.99, 0.99)

    w, h, t = half_w, half_h, half_t
    # Main plastic body (-t..+t along X, -w..+w along Y, -h..+h along Z)
    m.add_box(
        -t, +t, -w, +w, -h, +h,
        uv_all=UV_RIM,
        uv_px=UV_FRONT,
        uv_nx=UV_BACK,
    )
    # 3D stepped brushed-steel sliding shutter sleeve wrapping top center edge
    sy0, sy1 = -w * 0.48, w * 0.34
    sz0, sz1 = h * 0.38, h * 1.03
    st = t * 1.24
    m.add_box(
        -st, +st, sy0, sy1, sz0, sz1,
        uv_all=UV_SHUTTER,
    )
    # Slight raised label rim on front (+X)
    m.add_box(
        +t * 0.96, +t * 1.07, -w * 0.78, +w * 0.78, -h * 0.90, +h * 0.28,
        uv_all=UV_RIM,
        uv_px=(0.06, 0.18, 0.44, 0.46),
        skip_bottom=False,
    )
    # Raised circular spindle hub on back (-X)
    m.add_cylinder(
        (-t * 0.98, 0.0, -h * 0.14),
        (-t * 1.14, 0.0, -h * 0.14),
        w * 0.34,
        w * 0.32,
        uv_side=UV_SHUTTER,
        uv_cap=(0.66, 0.16, 0.84, 0.34),
        segs=12,
    )
    return m


def build_curved_crt_screen(
    x_front: float,
    y_half: float,
    z_bot: float,
    z_top: float,
    bulge: float = 0.42,
    nx: int = 5,
    nz: int = 4,
) -> MeshPart:
    """Curved 4:3 CRT glass mesh facing +X with clean UVs (u=0 left/-Y .. u=1 right/+Y, v=0 top/+Z .. v=1 bot/-Z)."""
    scr = MeshPart("crt_screen")
    grid = []
    for iz in range(nz + 1):
        vf = iz / float(nz)
        zc = z_top - (z_top - z_bot) * vf
        nz_n = (vf - 0.5) * 2.0
        row = []
        for iy in range(nx + 1):
            uf = iy / float(nx)
            yc = -y_half + 2.0 * y_half * uf
            ny_n = (uf - 0.5) * 2.0
            b = bulge * max(0.0, 1.0 - 0.65 * (ny_n * ny_n + nz_n * nz_n))
            xc = x_front + b
            nrm = vnorm((1.0, 0.10 * ny_n, -0.10 * nz_n))
            idx = len(scr.verts)
            scr.verts.append((xc, yc, zc))
            scr.norms.append(nrm)
            scr.st.append((uf, vf))
            row.append(idx)
        grid.append(row)
    for iz in range(nz):
        for iy in range(nx):
            a = grid[iz][iy]
            b = grid[iz + 1][iy]
            c = grid[iz + 1][iy + 1]
            d = grid[iz][iy + 1]
            scr.tris.extend([(a, b, c), (a, c, d)])
    return scr
