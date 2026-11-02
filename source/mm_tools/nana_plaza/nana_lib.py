"""nana_lib.py — Pure spec-driven 1:1 Quake BSP2 / Valve-220 brush & entity geometry builder
for Nana Plaza (Sukhumvit Soi 4, Bangkok).

Scale: EXACT real-world 1 Quake unit = 1 inch (39.37007874 Quake units = 1.0000 meter).
Coordinate frame:
  (0, 0) m = Google Pin (13.7413718, 100.5533082)
  +X = Due East (meters)
  +Y = Due North (meters)
  +Z = Elevation above Soi 4 asphalt at Nana Plaza entrance (meters)
"""
import math
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
U_M = 39.37007874015748  # 1 meter = 39.37007874 inches = 39.37007874 Quake units (1 unit = 1 inch!)

# Nana Plaza local architectural frame:
# Origin at West street-front centerline of the Entrance Arch on Soi 4: (-28.60, +10.60) m
# Verified against Ext Entrance Arch GPS (-34.06, +10.49) yaw 90 and z=20 Web Mercator aerial (ref_016.jpg):
#   e_s = (cos(-26.565 deg), sin(-26.565 deg)) = (+0.89442719, -0.44721360)  [into plaza, WNW->ESE]
#   e_w = (+0.44721360, +0.89442719)                                         [across plaza, SSW->NNE: +w is North Wing, -w is South Wing!]
PLAZA_ORIGIN_M = (-28.60, 10.60)
PLAZA_YAW_DEG = -19.2  # Calibrated to z20_sat_grid.jpg / z20_hyb_grid.jpg Nana Plaza canopy & wing axis
_RAD = math.radians(PLAZA_YAW_DEG)
COS_P = math.cos(_RAD)
SIN_P = math.sin(_RAD)


def plaza_to_world(s_m, w_m):
    """Converts Nana Plaza local (s_m, w_m) meters into world (x_m, y_m) meters.
    s_m: distance ESE from Soi 4 frontage line (-29.50, +12.50) along courtyard axis.
    w_m: perpendicular offset NNE from courtyard centerline (+w = North Wing, -w = South Wing).
    """
    wx = PLAZA_ORIGIN_M[0] + s_m * COS_P - w_m * SIN_P
    wy = PLAZA_ORIGIN_M[1] + s_m * SIN_P + w_m * COS_P
    return (wx, wy)


def world_to_plaza(x_m, y_m):
    dx = x_m - PLAZA_ORIGIN_M[0]
    dy = y_m - PLAZA_ORIGIN_M[1]
    s_m = dx * COS_P + dy * SIN_P
    w_m = -dx * SIN_P + dy * COS_P
    return (s_m, w_m)


def compass_to_quake_yaw(compass_deg):
    """Compass bearing (0=N, 90=E, 180=S, 270=W) -> Quake yaw (0=+X East, 90=+Y North)."""
    return (90.0 - compass_deg) % 360.0


class MapBuilder:
    def __init__(self, wad_paths):
        self.wad_paths = list(wad_paths)
        self.texsize = {}
        for wp in self.wad_paths:
            if not os.path.exists(wp):
                continue
            with open(wp, "rb") as f:
                _, n, ofs = struct.unpack("<4sii", f.read(12))
                f.seek(ofs)
                dirs = [struct.unpack("<3i2bh16s", f.read(32)) for _ in range(n)]
                for pos, _, _, _, _, _, raw_name in dirs:
                    f.seek(pos)
                    _, w, h = struct.unpack("<16s2I", f.read(24))
                    self.texsize[raw_name.split(b"\0")[0].decode()] = (w, h)

        self.groups = {
            "world": [],
            "detail": [],
            "phong": [],
            "fence": [],
            "canopy": [],
            "illus": [],
        }
        self.ents = []

    @staticmethod
    def mu(m):
        return round(m * U_M, 3)

    @staticmethod
    def mui(m):
        return int(round(m * U_M))

    @staticmethod
    def vsub(a, b):
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    @staticmethod
    def vadd(a, b):
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    @staticmethod
    def vmul(a, s):
        return (a[0] * s, a[1] * s, a[2] * s)

    @staticmethod
    def vdot(a, b):
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    @staticmethod
    def vcross(a, b):
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )

    @classmethod
    def vnorm(cls, a):
        L = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
        if L < 1e-9:
            return (1.0, 0.0, 0.0)
        return (a[0] / L, a[1] / L, a[2] / L)

    @classmethod
    def _axes(cls, outward, u_hint=None):
        N = cls.vnorm(outward)
        if u_hint is not None:
            uh = cls.vsub(u_hint, cls.vmul(N, cls.vdot(u_hint, N)))
            if cls.vdot(uh, uh) > 1e-6:
                U_ax = cls.vnorm(uh)
                V_ax = cls.vnorm(cls.vcross(U_ax, N))
                if V_ax[2] > 1e-5:
                    V_ax = cls.vmul(V_ax, -1.0)
                return U_ax, V_ax
        if abs(N[2]) < 0.98:
            U_ax = cls.vnorm((-N[1], N[0], 0.0))
            V_ax = cls.vnorm(cls.vcross(U_ax, N))
            if V_ax[2] > 0:
                V_ax = cls.vmul(V_ax, -1.0)
            return U_ax, V_ax
        return (1.0, 0.0, 0.0), (0.0, -1.0, 0.0)

    def vface(self, p0, p1, p2, outward, tex, poly_pts=None, u_hint=None):
        """Formats a Valve-220 brush plane.
        `tex` can be:
          - str: texture name tiled at 2.0m x 2.0m default real-world scale
          - ("tile", name, m_u, m_v): tiled so 1 full texture spans (m_u, m_v) meters
          - ("fit", name) or ("fit", name, rep_u, rep_v): fitted cleanly to `poly_pts`
          - ("raw", name): 1:1 texel per Quake unit (e.g. sky / clip)
        """
        n = self.vcross(self.vsub(p0, p1), self.vsub(p2, p1))
        if self.vdot(n, outward) < 0:
            p0, p2 = p2, p0
        U_ax, V_ax = self._axes(outward, u_hint=u_hint)

        if isinstance(tex, (tuple, list)):
            mode = tex[0]
            tname = tex[1]
            tw, th = self.texsize.get(tname, (128, 128))
            if mode == "fit":
                ru = tex[2] if len(tex) > 2 else 1.0
                rv = tex[3] if len(tex) > 3 else 1.0
                pts = poly_pts if poly_pts else (p0, p1, p2)
                us = [self.vdot(p, U_ax) for p in pts]
                vs = [self.vdot(p, V_ax) for p in pts]
                umin, umax = min(us), max(us)
                vmin, vmax = min(vs), max(vs)
                span_u = max(1.0, umax - umin)
                span_v = max(1.0, vmax - vmin)
                xs = span_u / (tw * ru)
                ys = span_v / (th * rv)
                uoff = -umin / xs
                voff = -vmin / ys
            elif mode == "tile":
                m_u = tex[2]
                m_v = tex[3] if len(tex) > 3 else m_u
                xs = (m_u * U_M) / tw
                ys = (m_v * U_M) / th
                uoff, voff = 0.0, 0.0
            else:
                xs, ys, uoff, voff = 1.0, 1.0, 0.0, 0.0
        else:
            tname = str(tex)
            if tname in ("sky", "sky_np", "clip", "skip", "trigger"):
                xs, ys, uoff, voff = 1.0, 1.0, 0.0, 0.0
            else:
                tw, th = self.texsize.get(tname, (128, 128))
                xs = (2.4 * U_M) / tw
                ys = (2.4 * U_M) / th
                uoff, voff = 0.0, 0.0

        def fp(p):
            return f"( {p[0]:.3f} {p[1]:.3f} {p[2]:.3f} )"

        return (
            f"{fp(p0)} {fp(p1)} {fp(p2)} {tname} "
            f"[ {U_ax[0]:.5f} {U_ax[1]:.5f} {U_ax[2]:.5f} {uoff:.3f} ] "
            f"[ {V_ax[0]:.5f} {V_ax[1]:.5f} {V_ax[2]:.5f} {voff:.3f} ] "
            f"0 {xs:.5f} {ys:.5f}\n"
        )

    def add_brush(self, face_lines, group="detail"):
        self.groups[group].append("{\n" + "".join(face_lines) + "}\n")

    def aabb(self, x1, y1, z1, x2, y2, z2, tex, faces=None, group="world"):
        """Axis-aligned box in world meters."""
        faces = faces or {}
        X1, X2 = sorted((self.mu(x1), self.mu(x2)))
        Y1, Y2 = sorted((self.mu(y1), self.mu(y2)))
        Z1, Z2 = sorted((self.mu(z1), self.mu(z2)))
        if X2 - X1 < 0.25 or Y2 - Y1 < 0.25 or Z2 - Z1 < 0.25:
            return
        if X2 - X1 < 2.0:
            xm = 0.5 * (X1 + X2)
            X1, X2 = xm - 1.0, xm + 1.0
        if Y2 - Y1 < 2.0:
            ym = 0.5 * (Y1 + Y2)
            Y1, Y2 = ym - 1.0, ym + 1.0
        if Z2 - Z1 < 2.0:
            Z2 = Z1 + 2.0
        c000, c100, c110, c010 = (X1, Y1, Z1), (X2, Y1, Z1), (X2, Y2, Z1), (X1, Y2, Z1)
        c001, c101, c111, c011 = (X1, Y1, Z2), (X2, Y1, Z2), (X2, Y2, Z2), (X1, Y2, Z2)
        fl = [
            self.vface(c000, c010, c001, (-1, 0, 0), faces.get("w", tex), (c000, c010, c011, c001)),
            self.vface(c100, c101, c110, (1, 0, 0), faces.get("e", tex), (c100, c110, c111, c101)),
            self.vface(c000, c001, c100, (0, -1, 0), faces.get("s", tex), (c000, c100, c101, c001)),
            self.vface(c010, c110, c011, (0, 1, 0), faces.get("n", tex), (c010, c110, c111, c011)),
            self.vface(c000, c100, c010, (0, 0, -1), faces.get("b", tex), (c000, c100, c110, c010)),
            self.vface(c001, c011, c101, (0, 0, 1), faces.get("t", tex), (c001, c101, c111, c011)),
        ]
        self.add_brush(fl, group=group)

    def obox(self, cx, cy, z1, z2, hl_s, hw_w, yaw_deg, tex, faces=None, group="detail"):
        """Oriented box in world meters centered at (cx, cy), z1..z2, half-length `hl_s` along `yaw_deg`,
        half-width `hw_w` to the left (+90 deg CCW from `yaw_deg`).
        Face keys: 'front' (+s), 'back' (-s), 'left' (+w), 'right' (-w), 't' (+z), 'b' (-z).
        """
        faces = faces or {}
        Z1, Z2 = sorted((self.mu(z1), self.mu(z2)))
        if hl_s * U_M < 0.15 or hw_w * U_M < 0.15 or Z2 - Z1 < 0.25:
            return
        hl_s = max(hl_s, 1.0 / U_M)
        hw_w = max(hw_w, 1.0 / U_M)
        if Z2 - Z1 < 2.0:
            Z2 = Z1 + 2.0
        rad = math.radians(yaw_deg)
        es = (math.cos(rad), math.sin(rad))
        ew = (-math.sin(rad), math.cos(rad))

        def pt(ds, dw, Z):
            wx = cx + ds * es[0] + dw * ew[0]
            wy = cy + ds * es[1] + dw * ew[1]
            return (self.mu(wx), self.mu(wy), Z)

        p_mm0, p_pm0, p_pp0, p_mp0 = pt(-hl_s, -hw_w, Z1), pt(hl_s, -hw_w, Z1), pt(hl_s, hw_w, Z1), pt(-hl_s, hw_w, Z1)
        p_mm1, p_pm1, p_pp1, p_mp1 = pt(-hl_s, -hw_w, Z2), pt(hl_s, -hw_w, Z2), pt(hl_s, hw_w, Z2), pt(-hl_s, hw_w, Z2)
        u_s = (es[0], es[1], 0.0)
        u_w = (ew[0], ew[1], 0.0)
        fl = [
            self.vface(p_pm0, p_pp0, p_pm1, (es[0], es[1], 0.0), faces.get("front", tex), (p_pm0, p_pp0, p_pp1, p_pm1), u_hint=u_w),
            self.vface(p_mm0, p_mm1, p_mp0, (-es[0], -es[1], 0.0), faces.get("back", tex), (p_mm0, p_mp0, p_mp1, p_mm1), u_hint=(-u_w[0], -u_w[1], 0.0)),
            self.vface(p_mp0, p_pp0, p_mp1, (ew[0], ew[1], 0.0), faces.get("left", tex), (p_mp0, p_pp0, p_pp1, p_mp1), u_hint=(-u_s[0], -u_s[1], 0.0)),
            self.vface(p_mm0, p_pm0, p_mm1, (-ew[0], -ew[1], 0.0), faces.get("right", tex), (p_mm0, p_pm0, p_pm1, p_mm1), u_hint=u_s),
            self.vface(p_mm0, p_pm0, p_mp0, (0.0, 0.0, -1.0), faces.get("b", tex), (p_mm0, p_pm0, p_pp0, p_mp0), u_hint=u_s),
            self.vface(p_mm1, p_mp1, p_pm1, (0.0, 0.0, 1.0), faces.get("t", tex), (p_mm1, p_pm1, p_pp1, p_mp1), u_hint=u_s),
        ]
        self.add_brush(fl, group=group)

    def pbox(self, s1, w1, z1, s2, w2, z2, tex, faces=None, group="detail"):
        """Box directly in Nana Plaza local coordinates (s1..s2, w1..w2, z1..z2) in meters!"""
        sc = 0.5 * (s1 + s2)
        wc = 0.5 * (w1 + w2)
        hl = 0.5 * abs(s2 - s1)
        hw = 0.5 * abs(w2 - w1)
        cx, cy = plaza_to_world(sc, wc)
        self.obox(cx, cy, z1, z2, hl, hw, PLAZA_YAW_DEG, tex, faces=faces, group=group)

    def quad_prism(self, pts_ccw_m, z1, z2, tex, top_tex=None, side_tex=None, group="detail", u_hint_top=None):
        """Convex 2D polygon `pts_ccw_m` [(x,y), ...] in meters extruded from `z1` to `z2`."""
        n = len(pts_ccw_m)
        if n < 3:
            return
        Z1, Z2 = sorted((self.mu(z1), self.mu(z2)))
        if Z2 - Z1 < 0.25:
            return
        if Z2 - Z1 < 2.0:
            Z2 = Z1 + 2.0
        # Ensure CCW winding
        area2 = sum(pts_ccw_m[i][0] * pts_ccw_m[(i + 1) % n][1] - pts_ccw_m[(i + 1) % n][0] * pts_ccw_m[i][1] for i in range(n))
        pts = list(pts_ccw_m) if area2 > 0 else list(reversed(pts_ccw_m))
        P0 = [(self.mu(x), self.mu(y), Z1) for x, y in pts]
        P1 = [(self.mu(x), self.mu(y), Z2) for x, y in pts]
        st = side_tex if side_tex is not None else tex
        tt = top_tex if top_tex is not None else tex
        fl = [
            self.vface(P0[0], P0[1], P0[2], (0, 0, -1), tex, P0, u_hint=u_hint_top),
            self.vface(P1[0], P1[2], P1[1], (0, 0, 1), tt, P1, u_hint=u_hint_top),
        ]
        for i in range(n):
            a0, b0 = P0[i], P0[(i + 1) % n]
            a1, b1 = P1[i], P1[(i + 1) % n]
            dx, dy = b0[0] - a0[0], b0[1] - a0[1]
            if dx * dx + dy * dy < 0.05:
                continue
            outward = (dy, -dx, 0.0)
            fl.append(self.vface(a0, b0, a1, outward, st, (a0, b0, b1, a1)))
        self.add_brush(fl, group=group)

    def sloped_slab_plaza(self, s1, s2, w1, z_w1, w2, z_w2, thick_z, tex_top, tex_bot=None, group="detail"):
        """Pitched roof/canopy/ramp slab in Nana Plaza coordinates: spans s1..s2, and slopes from (w1, z_w1) to (w2, z_w2)."""
        tb = tex_bot if tex_bot is not None else tex_top
        if w2 < w1:
            w1, w2 = w2, w1
            z_w1, z_w2 = z_w2, z_w1
        if s2 < s1:
            s1, s2 = s2, s1

        def P(s, w, z):
            wx, wy = plaza_to_world(s, w)
            return (self.mu(wx), self.mu(wy), self.mu(z))

        # 8 vertices of a vertical-sided prism skewed in Z along w
        b00, b10, b11, b01 = P(s1, w1, z_w1 - thick_z), P(s2, w1, z_w1 - thick_z), P(s2, w2, z_w2 - thick_z), P(s1, w2, z_w2 - thick_z)
        t00, t10, t11, t01 = P(s1, w1, z_w1), P(s2, w1, z_w1), P(s2, w2, z_w2), P(s1, w2, z_w2)

        es = (COS_P, SIN_P, 0.0)
        ew = (-SIN_P, COS_P, 0.0)
        dz = z_w2 - z_w1
        dw = max(0.01, w2 - w1)
        # Top normal points +z and slightly -ew if dz > 0
        n_top = (-ew[0] * dz, -ew[1] * dz, dw)
        n_bot = (ew[0] * dz, ew[1] * dz, -dw)
        fl = [
            self.vface(t00, t10, t11, n_top, tex_top, (t00, t10, t11, t01), u_hint=es),
            self.vface(b00, b11, b10, n_bot, tb, (b00, b10, b11, b01), u_hint=es),
            self.vface(b10, t10, t11, es, tb, (b10, b11, t11, t10), u_hint=ew),
            self.vface(b00, t01, t00, (-es[0], -es[1], 0.0), tb, (b00, b01, t01, t00), u_hint=ew),
            self.vface(b01, b11, t11, ew, tb, (b01, b11, t11, t01), u_hint=es),
            self.vface(b00, t10, b10, (-ew[0], -ew[1], 0.0), tb, (b00, b10, t10, t00), u_hint=es),
        ]
        self.add_brush(fl, group=group)

    def oct_prism(self, cx, cy, z1, z2, radius_m, tex, top_tex=None, sides=8, group="detail"):
        """Regular N-sided prism in world meters (uses clean square post for sub-9cm radii to avoid micro-face pinching)."""
        if radius_m < 0.09:
            self.aabb(cx - radius_m, cy - radius_m, z1, cx + radius_m, cy + radius_m, z2, tex, faces={"t": top_tex or tex}, group=group)
            return
        pts = [
            (cx + radius_m * math.cos(2.0 * math.pi * i / sides), cy + radius_m * math.sin(2.0 * math.pi * i / sides))
            for i in range(sides)
        ]
        self.quad_prism(pts, z1, z2, tex, top_tex=top_tex or tex, side_tex=tex, group=group)

    def pstairs(self, s1, w1, s2, w2, z_bot, z_top, n_steps, dir_axis, tex_tread="np_stair_trd", tex_side="np_wall_ochr"):
        """Builds walkable steps in Nana Plaza coordinates (`dir_axis` in ('+s', '-s', '+w', '-w')).
        Keep step rise <= 0.22m (~8.6 Quake units, well below Quake's 18-unit step height!).
        """
        dz = (z_top - z_bot) / max(1, n_steps)
        s_lo, s_hi = sorted((s1, s2))
        w_lo, w_hi = sorted((w1, w2))
        for i in range(n_steps):
            zt = z_bot + (i + 1) * dz
            zb = max(z_bot, zt - 0.35)
            if dir_axis == "+s":
                a = s_lo + (s_hi - s_lo) * (i / n_steps)
                b = s_lo + (s_hi - s_lo) * ((i + 1) / n_steps)
                self.pbox(a, w_lo, zb, b, w_hi, zt, tex_side, faces={"t": ("tile", tex_tread, 1.4, 1.4)})
            elif dir_axis == "-s":
                b = s_hi - (s_hi - s_lo) * (i / n_steps)
                a = s_hi - (s_hi - s_lo) * ((i + 1) / n_steps)
                self.pbox(a, w_lo, zb, b, w_hi, zt, tex_side, faces={"t": ("tile", tex_tread, 1.4, 1.4)})
            elif dir_axis == "+w":
                a = w_lo + (w_hi - w_lo) * (i / n_steps)
                b = w_lo + (w_hi - w_lo) * ((i + 1) / n_steps)
                self.pbox(s_lo, a, zb, s_hi, b, zt, tex_side, faces={"t": ("tile", tex_tread, 1.4, 1.4)})
            elif dir_axis == "-w":
                b = w_hi - (w_hi - w_lo) * (i / n_steps)
                a = w_hi - (w_hi - w_lo) * ((i + 1) / n_steps)
                self.pbox(s_lo, a, zb, s_hi, b, zt, tex_side, faces={"t": ("tile", tex_tread, 1.4, 1.4)})

    def sloped_s_plaza(self, s1, z_s1, s2, z_s2, w1, w2, thick_z, tex_top, tex_bot=None, group="detail"):
        """Sloped ramp/escalator/balustrade beam in Nana Plaza coordinates sloping along `s` from (s1, z_s1) to (s2, z_s2)."""
        tb = tex_bot if tex_bot is not None else tex_top
        if s2 < s1:
            s1, s2 = s2, s1
            z_s1, z_s2 = z_s2, z_s1
        if w2 < w1:
            w1, w2 = w2, w1

        def P(s, w, z):
            wx, wy = plaza_to_world(s, w)
            return (self.mu(wx), self.mu(wy), self.mu(z))

        b00, b10, b11, b01 = P(s1, w1, z_s1 - thick_z), P(s2, w1, z_s2 - thick_z), P(s2, w2, z_s2 - thick_z), P(s1, w2, z_s1 - thick_z)
        t00, t10, t11, t01 = P(s1, w1, z_s1), P(s2, w1, z_s2), P(s2, w2, z_s2), P(s1, w2, z_s1)
        es = (COS_P, SIN_P, 0.0)
        ew = (-SIN_P, COS_P, 0.0)
        dz = z_s2 - z_s1
        ds = max(0.01, s2 - s1)
        n_top = (-es[0] * dz, -es[1] * dz, ds)
        n_bot = (es[0] * dz, es[1] * dz, -ds)
        fl = [
            self.vface(t00, t10, t11, n_top, tex_top, (t00, t10, t11, t01), u_hint=es),
            self.vface(b00, b11, b10, n_bot, tb, (b00, b10, b11, b01), u_hint=es),
            self.vface(b10, t10, t11, es, tb, (b10, b11, t11, t10), u_hint=ew),
            self.vface(b00, t01, t00, (-es[0], -es[1], 0.0), tb, (b00, b01, t01, t00), u_hint=ew),
            self.vface(b01, b11, t11, ew, tb, (b01, b11, t11, t01), u_hint=es),
            self.vface(b00, t10, b10, (-ew[0], -ew[1], 0.0), tb, (b00, b10, t10, t00), u_hint=es),
        ]
        self.add_brush(fl, group=group)

    def polyline_ribbon(self, pts_m, width_m, z1, z2, tex, side_tex=None, group="detail"):
        """Builds mitered/segment convex quad brushes along a 2D polyline in meters."""
        hw = 0.5 * width_m
        for i in range(len(pts_m) - 1):
            x0, y0 = pts_m[i]
            x1, y1 = pts_m[i + 1]
            dx, dy = x1 - x0, y1 - y0
            L = math.hypot(dx, dy)
            if L < 0.05:
                continue
            nx, ny = -dy / L * hw, dx / L * hw
            quad = [(x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny), (x0 + nx, y0 + ny)]
            self.quad_prism(quad, z1, z2, side_tex or tex, top_tex=tex, side_tex=side_tex or tex, group=group, u_hint_top=(dx / L, dy / L, 0.0))

    def ent(self, classname, x_m, y_m, z_m, **kv):
        X, Y, Z = self.mui(x_m), self.mui(y_m), self.mui(z_m)
        lines = [f'"classname" "{classname}"', f'"origin" "{X} {Y} {Z}"']
        for k, v in kv.items():
            lines.append(f'"{k}" "{v}"')
        self.ents.append("{\n" + "\n".join(lines) + "\n}\n")

    def pent(self, classname, s_m, w_m, z_m, **kv):
        wx, wy = plaza_to_world(s_m, w_m)
        self.ent(classname, wx, wy, z_m, **kv)

    def light(self, x_m, y_m, z_m, val=180, color="1 0.94 0.85", **kv):
        self.ent("light", x_m, y_m, z_m, light=val, _color=color, **kv)

    def plight(self, s_m, w_m, z_m, val=180, color="1 0.94 0.85", **kv):
        wx, wy = plaza_to_world(s_m, w_m)
        self.light(wx, wy, z_m, val=val, color=color, **kv)

    def write_map(self, out_path, worldspawn_kv):
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        wad_names = ";".join(os.path.basename(p) for p in self.wad_paths)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write('{\n"classname" "worldspawn"\n')
            f.write('"mapversion" "220"\n')
            f.write(f'"wad" "{wad_names}"\n')
            for k, v in worldspawn_kv.items():
                f.write(f'"{k}" "{v}"\n')
            f.write("".join(self.groups["world"]))
            f.write("}\n")
            if self.groups["detail"]:
                f.write('{\n"classname" "func_detail"\n' + "".join(self.groups["detail"]) + "}\n")
            if self.groups["phong"]:
                f.write('{\n"classname" "func_detail"\n"_phong" "1"\n"_phong_angle" "89"\n' + "".join(self.groups["phong"]) + "}\n")
            if self.groups["canopy"]:
                # Tensile canopy casts soft partial shade while glowing brightly from transmitted daylight!
                f.write('{\n"classname" "func_detail"\n"_minlight" "165"\n"_minlight_color" "255 250 242"\n' + "".join(self.groups["canopy"]) + "}\n")
            for fb in self.groups["fence"]:
                f.write('{\n"classname" "func_wall"\n"_shadow" "0"\n"_minlight" "85"\n' + fb + "}\n")
            if self.groups["illus"]:
                f.write('{\n"classname" "func_detail_illusionary"\n"_shadow" "0"\n"_minlight" "95"\n' + "".join(self.groups["illus"]) + "}\n")
            f.write("".join(self.ents))
