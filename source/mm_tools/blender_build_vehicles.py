"""Headless Blender 5.2 3D Sculpted Multi-Part Vehicle Builder for BakersfieldQuake.

Builds 4 totally unique early-2000s vehicles in Quake units (+X forward, +Y left, +Z up, z=0 ground),
synced to sub-pixel accuracy with veh_specs.py & veh_textures.py:
  1. truck : Heavy-Duty Extended-Cab 4x4 Pickup (3D body-colored A/C pillars, hollow Rhino-lined open bed,
             wheel tubs, diamond-plate aluminum toolbox, tubular roll bar + 4 KC off-road spotlights,
             tow mirrors, chrome step bumpers + hitch, twin chrome exhausts, 33" mud-terrain tires)
  2. sedan : Late-90s Boxy 4-Door Street Sedan (clean 3-box greenhouse with 3D body-colored A/C pillars,
             satin-black B-pillars & window frames, tinted sunroof, 4 doors, wraparound rub-strip bumpers,
             flexible whip radio antenna, chrome exhaust tip, 15" 5-spoke alloy wheels)
  3. van   : Classic Ford Econoline White Cargo Van (short steep snub hood, tall boxy cargo body with
             recessed blind-panel bays, rain-drip gutters, twin steel roof ladder-rack crossbars,
             commercial loop mirrors, 50/50 split rear barn doors with defroster glass, 8-lug steelies)
  4. coupe : Early-2000s 2-Door Tuner Sport Coupe / Fastback (low-slung wedge nose, twin vented hood,
             3D fastback A/C pillars + recessed hatch glass, high-mount JDM pedestal wing + endplates,
             front FMIC bumper + lip splitter, rear diffuser, angled N1 titanium canister, bronze 6-spokes)
"""
import json
import math
import os
import random
import sys

import bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import veh_specs as vs

OUT_JSON = argv[0] if len(argv) > 0 else os.path.join(HERE, "out", "vehicles_parts.json")

SWATCH_RECTS = {
    "glass":     vs.RECT_GLASS,
    "chrome":    vs.RECT_CHROME,
    "trim":      vs.RECT_TRIM,
    "engine":    vs.RECT_ENGINE,
    "interior":  vs.RECT_INTERIOR,
    "int_floor": vs.RECT_INT_FLOOR,
    "int_dash":  vs.RECT_INT_DASH,
    "int_seat":  vs.RECT_INT_SEAT,
    "int_wall":  vs.RECT_INT_WALL,
    "wreck":     vs.RECT_WRECK,
    "ember":     vs.RECT_EMBER,
}


# --------------------------------------------------------------------------- Pure BMesh Mesh Builder Class
class PartBuilder:
    """Accumulates outward-wound CCW triangles with exact veh_specs UVs and smooth/sharp crease normals."""
    def __init__(self, name, sp):
        self.name = name
        self.sp = sp
        self.bm = bmesh.new()
        self.uv_layer = self.bm.loops.layers.uv.new("UVMap")
        self.mat_layer = self.bm.faces.layers.string.new("region")

    def add_quad(self, p0, p1, p2, p3, region="auto", flip=False):
        pts = [Vector(p0), Vector(p3), Vector(p2), Vector(p1)] if flip else [Vector(p0), Vector(p1), Vector(p2), Vector(p3)]
        if (pts[1] - pts[0]).length < 1e-4 or (pts[2] - pts[1]).length < 1e-4:
            return
        verts = [self.bm.verts.new(p) for p in pts]
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return
        f[self.mat_layer] = region.encode("ascii")
        self._assign_face_uv(f, region)

    def add_tri(self, p0, p1, p2, region="auto", flip=False):
        pts = [Vector(p0), Vector(p2), Vector(p1)] if flip else [Vector(p0), Vector(p1), Vector(p2)]
        if (pts[1] - pts[0]).cross(pts[2] - pts[0]).length < 1e-5:
            return
        verts = [self.bm.verts.new(p) for p in pts]
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return
        f[self.mat_layer] = region.encode("ascii")
        self._assign_face_uv(f, region)

    def _assign_face_uv(self, f, region):
        f.normal_update()
        fn = f.normal
        sp = self.sp

        if region in SWATCH_RECTS:
            rect = SWATCH_RECTS[region]
            # Upward +Z tangent t2 so top of glass/swatch maps to sv=0 (top of atlas rect)!
            up_r = Vector((0, 0, 1)) if abs(fn.z) < 0.88 else Vector((1, 0, 0))
            t1 = up_r.cross(fn).normalized()
            t2 = fn.cross(t1).normalized()
            coords = [l.vert.co for l in f.loops]
            us = [p.dot(t1) for p in coords]
            vs_p = [p.dot(t2) for p in coords]
            umin, umax = min(us), max(us)
            vmin, vmax = min(vs_p), max(vs_p)
            du = max(6.0, umax - umin)
            dv = max(6.0, vmax - vmin)
            for l, pu, pv in zip(f.loops, us, vs_p):
                su = (pu - umin) / du
                sv = 1.0 - (pv - vmin) / dv
                l[self.uv_layer].uv = vs.rect_uv(rect, su, sv)
            return

        ax, ay, az = abs(fn.x), abs(fn.y), abs(fn.z)
        x0, x1, hw = sp["x0"], sp["x1"], sp["hw"]
        for l in f.loops:
            p = l.vert.co
            if region == "front" or (region == "auto" and fn.x > 0.62 and ax >= ay and ax >= az):
                l[self.uv_layer].uv = vs.front_uv(sp, p.y, p.z)
            elif region == "rear" or (region == "auto" and fn.x < -0.62 and ax >= ay and ax >= az):
                l[self.uv_layer].uv = vs.rear_uv(sp, p.y, p.z)
            elif region == "top" or (region == "auto" and fn.z > 0.52 and az >= ay):
                l[self.uv_layer].uv = vs.top_uv(sp, p.x, p.y)
            elif region == "bottom" or (region == "auto" and fn.z < -0.65):
                l[self.uv_layer].uv = vs.rect_uv(
                    vs.RECT_TRIM,
                    (p.x - x0) / max(1.0, x1 - x0),
                    (p.y + hw) / max(1.0, 2.0 * hw),
                )
            else:
                l[self.uv_layer].uv = vs.side_uv(sp, p.x, p.z)

    def add_box(self, x0, y0, z0, x1, y1, z1, region="trim", face_regions=None):
        xa, xb = min(x0, x1), max(x0, x1)
        ya, yb = min(y0, y1), max(y0, y1)
        za, zb = min(z0, z1), max(z0, z1)
        fr = face_regions or {}
        self.add_quad((xb, ya, za), (xb, yb, za), (xb, yb, zb), (xb, ya, zb), fr.get("+x", region))
        self.add_quad((xa, yb, za), (xa, ya, za), (xa, ya, zb), (xa, yb, zb), fr.get("-x", region))
        self.add_quad((xb, yb, za), (xa, yb, za), (xa, yb, zb), (xb, yb, zb), fr.get("+y", region))
        self.add_quad((xa, ya, za), (xb, ya, za), (xb, ya, zb), (xa, ya, zb), fr.get("-y", region))
        self.add_quad((xa, ya, zb), (xb, ya, zb), (xb, yb, zb), (xa, yb, zb), fr.get("+z", region))
        self.add_quad((xa, yb, za), (xb, yb, za), (xb, ya, za), (xa, ya, za), fr.get("-z", region))

    def add_cylinder(self, p_start, p_end, r0, r1=None, segs=12, region="chrome", cap=True):
        if r1 is None:
            r1 = r0
        a = Vector(p_start)
        b = Vector(p_end)
        axis = b - a
        if axis.length < 1e-4:
            return
        d = axis.normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        u = d.cross(up).normalized()
        v = d.cross(u).normalized()

        ring0, ring1 = [], []
        for i in range(segs):
            th = 2.0 * math.pi * i / segs
            cs, sn = math.cos(th), math.sin(th)
            ring0.append(a + (u * cs + v * sn) * r0)
            ring1.append(b + (u * cs + v * sn) * r1)

        for i in range(segs):
            j = (i + 1) % segs
            self.add_quad(ring0[i], ring0[j], ring1[j], ring1[i], region)
        if cap:
            for i in range(1, segs - 1):
                self.add_tri(ring0[0], ring0[i + 1], ring0[i], region)
                self.add_tri(ring1[0], ring1[i], ring1[i + 1], region)

    def add_thick_panel(self, grid_pts, thickness_vec, outer_region="auto", inner_region="interior"):
        nx = len(grid_pts)
        ny = len(grid_pts[0])
        tv = Vector(thickness_vec)
        top_g = [[Vector(grid_pts[i][j]) for j in range(ny)] for i in range(nx)]
        bot_g = [[top_g[i][j] + tv for j in range(ny)] for i in range(nx)]

        e1 = top_g[1][0] - top_g[0][0]
        e2 = top_g[0][1] - top_g[0][0]
        flip = e1.cross(e2).dot(-tv) < 0

        for i in range(nx - 1):
            for j in range(ny - 1):
                self.add_quad(top_g[i][j], top_g[i + 1][j], top_g[i + 1][j + 1], top_g[i][j + 1], outer_region, flip=flip)
                self.add_quad(bot_g[i][j], bot_g[i][j + 1], bot_g[i + 1][j + 1], bot_g[i][j + 1], inner_region, flip=flip)

        for i in range(nx - 1):
            self.add_quad(top_g[i][0], bot_g[i][0], bot_g[i + 1][0], top_g[i + 1][0], "trim", flip=flip)
            self.add_quad(top_g[i + 1][ny - 1], bot_g[i + 1][ny - 1], bot_g[i][ny - 1], top_g[i][ny - 1], "trim", flip=flip)
        for j in range(ny - 1):
            self.add_quad(top_g[0][j + 1], bot_g[0][j + 1], bot_g[0][j], top_g[0][j], "trim", flip=flip)
            self.add_quad(top_g[nx - 1][j], bot_g[nx - 1][j], bot_g[nx - 1][j + 1], top_g[nx - 1][j + 1], "trim", flip=flip)

    def add_framed_window(
        self, p_bl, p_br, p_tr, p_tl,
        w_bot=1.8, w_right=3.5, w_top=2.4, w_left=3.5,
        recess=0.85,
        bot_reg="trim", right_reg="auto", top_reg="auto", left_reg="auto",
        double_sided_frame=False,
    ):
        """Builds 3D automotive pillars/header + rubber weatherstrip bevel + recessed smoked glass!
        Input quad (p_bl, p_br, p_tr, p_tl) must be outward CCW."""
        bl, br, tr, tl = Vector(p_bl), Vector(p_br), Vector(p_tr), Vector(p_tl)
        n_raw = (br - bl).cross(tl - bl)
        if n_raw.length < 1e-4:
            return
        fn = n_raw.normalized()

        w_avg = max(5.0, 0.5 * ((br - bl).length + (tr - tl).length))
        h_avg = max(5.0, 0.5 * ((tl - bl).length + (tr - br).length))
        u0 = min(0.36, max(0.03, w_left / w_avg))
        u1 = 1.0 - min(0.36, max(0.03, w_right / w_avg))
        v0 = min(0.36, max(0.03, w_bot / h_avg))
        v1 = 1.0 - min(0.36, max(0.03, w_top / h_avg))

        def B(u, v):
            return (1.0 - v) * ((1.0 - u) * bl + u * br) + v * ((1.0 - u) * tl + u * tr)

        f_bl, f_br, f_tr, f_tl = B(u0, v0), B(u1, v0), B(u1, v1), B(u0, v1)
        g_bl = f_bl - fn * recess
        g_br = f_br - fn * recess
        g_tr = f_tr - fn * recess
        g_tl = f_tl - fn * recess

        # 4 outer structural pillar / cant-rail strips
        self.add_quad(bl, br, f_br, f_bl, bot_reg)
        self.add_quad(br, tr, f_tr, f_br, right_reg)
        self.add_quad(f_tl, f_tr, tr, tl, top_reg)
        self.add_quad(bl, f_bl, f_tl, tl, left_reg)

        if double_sided_frame:
            bk = -fn * (recess * 1.45)
            self.add_quad(bl + bk, f_bl + bk, f_br + bk, br + bk, "trim")
            self.add_quad(br + bk, f_br + bk, f_tr + bk, tr + bk, "trim")
            self.add_quad(f_tl + bk, tl + bk, tr + bk, f_tr + bk, "trim")
            self.add_quad(bl + bk, tl + bk, f_tl + bk, f_bl + bk, "trim")

        # 4 rubber weatherstripping bevels into recessed glass
        self.add_quad(f_bl, f_br, g_br, g_bl, "trim")
        self.add_quad(f_br, f_tr, g_tr, g_br, "trim")
        self.add_quad(g_tl, g_tr, f_tr, f_tl, "trim")
        self.add_quad(f_bl, g_bl, g_tl, f_tl, "trim")

        # Double-sided recessed smoked safety glass
        self.add_quad(g_bl, g_br, g_tr, g_tl, "glass")
        self.add_quad(g_bl, g_tl, g_tr, g_br, "glass")

    def export_dict(self, custom_origin=None, hinge_pivot=None):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=0.02)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces[:])
        self.bm.normal_update()

        if len(self.bm.verts) == 0 or len(self.bm.faces) == 0:
            self.bm.free()
            return None

        if custom_origin is not None:
            ctr = Vector(custom_origin)
        else:
            xs = [v.co.x for v in self.bm.verts]
            ys = [v.co.y for v in self.bm.verts]
            zs = [v.co.z for v in self.bm.verts]
            ctr = Vector(((min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, (min(zs) + max(zs)) * 0.5))

        v_map = {}
        verts, norms, uvs, tris = [], [], [], []
        for f in self.bm.faces:
            fn = f.normal
            t_idx = []
            for l in f.loops:
                v = l.vert
                vn = v.normal
                n_use = vn if vn.dot(fn) > 0.74 else fn
                p_rel = v.co - ctr
                uv = l[self.uv_layer].uv
                key = (
                    round(p_rel.x, 3), round(p_rel.y, 3), round(p_rel.z, 3),
                    round(n_use.x, 3), round(n_use.y, 3), round(n_use.z, 3),
                    round(uv.x, 4), round(uv.y, 4),
                )
                if key not in v_map:
                    v_map[key] = len(verts)
                    verts.append([key[0], key[1], key[2]])
                    norms.append([key[3], key[4], key[5]])
                    uvs.append([key[6], key[7]])
                t_idx.append(v_map[key])
            tris.append(t_idx)

        self.bm.free()
        out = {
            "name": self.name,
            "origin": [round(ctr.x, 3), round(ctr.y, 3), round(ctr.z, 3)],
            "verts": verts,
            "norms": norms,
            "uvs": uvs,
            "tris": tris,
        }
        if hinge_pivot is not None:
            out["hinge"] = [round(x, 3) for x in hinge_pivot]
        return out


# --------------------------------------------------------------------------- 3D Wheel Builder (Synced 1:1 w/ RECT_WHEEL)
def build_3d_wheel(name, radius, width, dish_depth, rim_ratio, is_left, sp):
    """Builds a sculpted 3D pneumatic wheel centered at (0, 0, 0) with axle along +Y.
    Synced 1:1 with RECT_WHEEL center (128, 672) and r_tire = 116px."""
    pb = PartBuilder(name, sp)
    segs = 24
    hw = width * 0.5
    r_sh = radius * 0.92
    r_rim = radius * rim_ratio
    r_hub = radius * 0.22
    sgn = 1.0 if is_left else -1.0

    def ring_pts(r, y_val):
        return [
            Vector((math.cos(2.0 * math.pi * i / segs) * r, y_val * sgn, math.sin(2.0 * math.pi * i / segs) * r))
            for i in range(segs)
        ]

    r_tread_out = ring_pts(r_sh, hw * 0.80)
    r_crown_out = ring_pts(radius, hw * 0.48)
    r_crown_in = ring_pts(radius, -hw * 0.48)
    r_tread_in = ring_pts(r_sh, -hw * 0.80)
    r_side_out = ring_pts(r_rim, hw * 0.98)
    r_dish_out = ring_pts(r_rim * 0.78, (hw * 0.98 - dish_depth))
    r_hub_out = ring_pts(r_hub, hw * 0.90)
    r_side_in = ring_pts(r_rim, -hw * 0.96)
    r_hub_in = ring_pts(r_hub * 1.1, -hw * 0.78)

    flip_w = not is_left
    uc = 128.0 / vs.W_ATLAS
    vc = 672.0 / vs.H_ATLAS
    urad = 116.0 / vs.W_ATLAS

    def map_disc_uv(f, sign_y):
        for l in f.loops:
            p = l.vert.co
            nx = p.x / max(1.0, radius)
            nz = p.z / max(1.0, radius)
            l[pb.uv_layer].uv = (round(uc + nx * urad * sign_y, 4), round(vc - nz * urad, 4))

    def map_tread_uv(f, th_mid):
        for l in f.loops:
            p = l.vert.co
            ang = (math.atan2(p.z, p.x) / (2.0 * math.pi)) % 1.0
            if abs(ang - th_mid) > 0.5:
                ang = ang + 1.0 if ang < th_mid else ang - 1.0
            tw = max(0.0, min(1.0, (p.y * sgn + hw) / max(1.0, 2.0 * hw)))
            l[pb.uv_layer].uv = vs.rect_uv(vs.RECT_TREAD, tw, ang % 1.0)

    for i in range(segs):
        j = (i + 1) % segs
        t_mid = (i + 0.5) / segs
        for a_r, b_r in ((r_crown_out, r_crown_in), (r_tread_out, r_crown_out), (r_crown_in, r_tread_in)):
            before_n = len(pb.bm.faces)
            pb.add_quad(a_r[i], a_r[j], b_r[j], b_r[i], "trim", flip=flip_w)
            if len(pb.bm.faces) > before_n:
                pb.bm.faces.ensure_lookup_table()
                map_tread_uv(pb.bm.faces[-1], t_mid)

        for a_r, b_r in ((r_side_out, r_tread_out), (r_dish_out, r_side_out), (r_hub_out, r_dish_out)):
            before_n = len(pb.bm.faces)
            pb.add_quad(a_r[i], a_r[j], b_r[j], b_r[i], "trim", flip=flip_w)
            if len(pb.bm.faces) > before_n:
                pb.bm.faces.ensure_lookup_table()
                map_disc_uv(pb.bm.faces[-1], 1.0)

        for a_r, b_r in ((r_tread_in, r_side_in), (r_side_in, r_hub_in)):
            before_n = len(pb.bm.faces)
            pb.add_quad(a_r[i], a_r[j], b_r[j], b_r[i], "trim", flip=flip_w)
            if len(pb.bm.faces) > before_n:
                pb.bm.faces.ensure_lookup_table()
                map_disc_uv(pb.bm.faces[-1], -1.0)

    c_out = Vector((0.0, hw * 0.94 * sgn, 0.0))
    c_in = Vector((0.0, -hw * 0.80 * sgn, 0.0))
    for i in range(segs):
        j = (i + 1) % segs
        before_n = len(pb.bm.faces)
        pb.add_tri(c_out, r_hub_out[i], r_hub_out[j], "trim", flip=flip_w)
        if len(pb.bm.faces) > before_n:
            pb.bm.faces.ensure_lookup_table()
            map_disc_uv(pb.bm.faces[-1], 1.0)
        before_n = len(pb.bm.faces)
        pb.add_tri(c_in, r_hub_in[j], r_hub_in[i], "trim", flip=flip_w)
        if len(pb.bm.faces) > before_n:
            pb.bm.faces.ensure_lookup_table()
            map_disc_uv(pb.bm.faces[-1], -1.0)

    return pb.export_dict(custom_origin=(0.0, 0.0, 0.0))


# --------------------------------------------------------------------------- Fuselage & Bumper Helpers
def arch_lift(x, wheel_xs, arch_r, flare_amt):
    dz = 0.0
    dy = 0.0
    for wx in wheel_xs:
        dx = abs(x - wx)
        if dx < arch_r:
            h = math.sqrt(max(0.0, arch_r * arch_r - dx * dx))
            dz = max(dz, h * 0.88)
            dy = max(dy, math.sin(math.pi * (1.0 - dx / arch_r)) * flare_amt)
    return dz, dy


def add_curved_fascia(pb, x_base, bow_x, y_half, z_lo, z_hi, is_front, n_strips=6):
    """Builds a gently V-bowed multi-strip front (+X) or rear (-X) fascia wall mapped cleanly to 'front'/'rear'."""
    reg = "front" if is_front else "rear"
    for k in range(n_strips):
        ta = -1.0 + 2.0 * k / n_strips
        tb = -1.0 + 2.0 * (k + 1) / n_strips
        ya, yb = y_half * ta, y_half * tb
        xa = x_base + bow_x * (1.0 - ta * ta)
        xb = x_base + bow_x * (1.0 - tb * tb)
        if is_front:
            pb.add_quad((xa, ya, z_lo), (xb, yb, z_lo), (xb, yb, z_hi), (xa, ya, z_hi), reg)
        else:
            pb.add_quad((xb, yb, z_lo), (xa, ya, z_lo), (xa, ya, z_hi), (xb, yb, z_hi), reg)


def add_wraparound_bumper(pb, x_body, x_out, bow_x, y_half, z_lo, z_hi, wing_len, is_front, top_reg="trim"):
    """Builds a sculpted 3D wrap-around front or rear bumper spanning z_lo..z_hi with side wings."""
    f_reg = "front" if is_front else "rear"
    n_s = 6
    pts_out = []
    pts_in = []
    for k in range(n_s + 1):
        t = -1.0 + 2.0 * k / n_s
        yk = y_half * t
        xk = x_out + bow_x * (1.0 - t * t)
        pts_out.append((xk, yk))
        pts_in.append((x_body, yk * 0.96))

    for k in range(n_s):
        xa, ya = pts_out[k]
        xb, yb = pts_out[k + 1]
        xia, yia = pts_in[k]
        xib, yib = pts_in[k + 1]
        if is_front:
            pb.add_quad((xa, ya, z_lo), (xb, yb, z_lo), (xb, yb, z_hi), (xa, ya, z_hi), f_reg)
            pb.add_quad((xia, yia, z_hi), (xa, ya, z_hi), (xb, yb, z_hi), (xib, yib, z_hi), top_reg)
            pb.add_quad((xa, ya, z_lo), (xia, yia, z_lo), (xib, yib, z_lo), (xb, yb, z_lo), "trim")
            pb.add_quad((xib, yib, z_lo), (xia, yia, z_lo), (xia, yia, z_hi), (xib, yib, z_hi), "trim")
        else:
            pb.add_quad((xb, yb, z_lo), (xa, ya, z_lo), (xa, ya, z_hi), (xb, yb, z_hi), f_reg)
            pb.add_quad((xa, ya, z_hi), (xia, yia, z_hi), (xib, yib, z_hi), (xb, yb, z_hi), top_reg)
            pb.add_quad((xia, yia, z_lo), (xa, ya, z_lo), (xb, yb, z_lo), (xib, yib, z_lo), "trim")
            pb.add_quad((xia, yia, z_lo), (xib, yib, z_lo), (xib, yib, z_hi), (xia, yia, z_hi), "trim")

    # Side wrap-around wings along +-Y fenders
    xw_end = (x_body - wing_len) if is_front else (x_body + wing_len)
    for sgn, p_end in ((-1.0, pts_out[0]), (1.0, pts_out[-1])):
        xe, ye = p_end
        yi = ye - sgn * 2.5
        xa, xb = min(xe, xw_end), max(xe, xw_end)
        ya, yb = min(ye, yi), max(ye, yi)
        pb.add_box(xa, ya, z_lo, xb, yb, z_hi, "auto", {"+z": top_reg, "-z": "trim"})


# --------------------------------------------------------------------------- Vehicle Builder
def build_single_vehicle(kind):
    if kind == "van":
        import promaster_van_mesh
        vdata = promaster_van_mesh.build_promaster_van_data(barn_open_deg=126.0)
        print(f"  [van   ] ProMaster L2H2 studio walk-in van: {len(vdata['parts'])} parts")
        return vdata

    sp = dict(vs.get_spec(kind))
    x0, x1, hw = sp["x0"], sp["x1"], sp["hw"]
    z0, z_bmp, zb, z1 = sp["z_bot"], sp["z_bmp"], sp["z_belt"], sp["z_roof"]
    zn_top, zr_top = sp["z_nose_top"], sp["z_rear_top"]
    wxs = (sp["wheel_x_f"], sp["wheel_x_r"])

    chassis = PartBuilder("chassis", sp)
    hood = PartBuilder("hood", sp)
    door_l = PartBuilder("door_l", sp)
    door_r = PartBuilder("door_r", sp)
    extra = PartBuilder("extra_part", sp)
    bumper_f = PartBuilder("bumper_f", sp)
    bumper_r = PartBuilder("bumper_r", sp)
    detail = PartBuilder("detail_vib", sp)

    x_nose = x1 - 3.0
    x_tail = x0 + 2.5

    # ------------------------------------------------------------------ 1. Lower Body Sides & Wheel Wells
    xs = sorted(set(
        [round(x_tail + (x_nose - x_tail) * i / 36.0, 2) for i in range(37)]
        + [sp["x_door0"], sp["x_door1"], sp["x_cowl"]]
    ))

    def side_profile(x):
        """Returns (y_sill, y_shoulder, y_belt, z_sill_arch, z_belt_here) matched to veh_specs!"""
        t_f = max(0.0, (x - (x_nose - 20.0)) / 20.0)
        t_r = max(0.0, ((x_tail + 15.0) - x) / 15.0)
        taper = 1.0 - 0.09 * (t_f ** 1.6) - 0.05 * (t_r ** 1.6)
        dz_a, dy_f = arch_lift(x, wxs, sp["arch_r"], sp["flare"])

        if x > sp["x_cowl"]:
            ft = min(1.0, (x - sp["x_cowl"]) / max(1.0, x_nose - sp["x_cowl"]))
            zb_x = zb + (zn_top - zb) * (ft ** 1.15)
        elif kind in ("sedan", "coupe") and x < sp["x_cab_rear"]:
            rt = min(1.0, (sp["x_cab_rear"] - x) / max(1.0, sp["x_cab_rear"] - x_tail))
            zb_x = zb + (zr_top - zb) * rt
        else:
            zb_x = zb

        y_sh = hw * taper + dy_f
        y_sill = hw * 0.91 * taper + dy_f * 0.4
        y_blt = hw * 0.95 * taper
        # At nose & tail, sill meets z_bmp cleanly above the wrap-around bumpers!
        z_floor_here = z0 + dz_a
        if x > x_nose - 5.5 or x < x_tail + 5.5:
            z_floor_here = max(z_floor_here, z_bmp - 0.5)
        z_sl = min(zb_x - 4.0, z_floor_here)
        return y_sill, y_sh, y_blt, z_sl, zb_x

    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1]
        xm = 0.5 * (xa + xb)
        ys_a, ysh_a, yb_a, zs_a, zba = side_profile(xa)
        ys_b, ysh_b, yb_b, zs_b, zbb = side_profile(xb)
        zmid_a = 0.50 * zs_a + 0.50 * zba
        zmid_b = 0.50 * zs_b + 0.50 * zbb

        in_door = (xm > sp["x_door0"] + 0.05) and (xm < sp["x_door1"] - 0.05)
        target_l = door_l if in_door else chassis
        target_r = door_r if in_door else chassis

        # Left (+Y) outer sculpted lower skin
        target_l.add_quad((xb, ys_b, zs_b), (xa, ys_a, zs_a), (xa, ysh_a, zmid_a), (xb, ysh_b, zmid_b), "auto")
        target_l.add_quad((xb, ysh_b, zmid_b), (xa, ysh_a, zmid_a), (xa, yb_a, zba), (xb, yb_b, zbb), "auto")
        if in_door:
            yi = 2.4
            door_l.add_quad((xa, ys_a - yi, zs_a + 1.5), (xb, ys_b - yi, zs_b + 1.5),
                            (xb, yb_b - yi, zbb - 0.4), (xa, yb_a - yi, zba - 0.4), "interior")
            door_l.add_quad((xa, yb_a, zba), (xa, yb_a - yi, zba - 0.4), (xb, yb_b - yi, zbb - 0.4), (xb, yb_b, zbb), "trim")

        # Right (-Y) outer sculpted lower skin
        target_r.add_quad((xa, -ys_a, zs_a), (xb, -ys_b, zs_b), (xb, -ysh_b, zmid_b), (xa, -ysh_a, zmid_a), "auto")
        target_r.add_quad((xa, -ysh_a, zmid_a), (xb, -ysh_b, zmid_b), (xb, -yb_b, zbb), (xa, -yb_a, zba), "auto")
        if in_door:
            yi = 2.4
            door_r.add_quad((xb, -ys_b + yi, zs_b + 1.5), (xa, -ys_a + yi, zs_a + 1.5),
                            (xa, -yb_a + yi, zba - 0.4), (xb, -yb_b + yi, zbb - 0.4), "interior")
            door_r.add_quad((xb, -yb_b, zbb), (xb, -yb_b + yi, zbb - 0.4), (xa, -yb_a + yi, zba - 0.4), (xa, -yb_a, zba), "trim")

        # Flat central undercarriage floor pan (|y| <= 18) + outer sill/wheelhouse tubs (never pokes into truck bed!)
        yw = 18.0
        chassis.add_quad((xa, -yw, z0), (xa, yw, z0), (xb, yw, z0), (xb, -yw, z0), "bottom")
        chassis.add_quad((xa, yw, zs_a), (xa, ys_a, zs_a), (xb, ys_b, zs_b), (xb, yw, zs_b), "trim")
        chassis.add_quad((xa, -ys_a, zs_a), (xa, -yw, zs_a), (xb, -yw, zs_b), (xb, -ys_b, zs_b), "trim")
        if zs_a > z0 + 0.5 or zs_b > z0 + 0.5:
            chassis.add_quad((xa, yw, z0), (xb, yw, z0), (xb, yw, zs_b), (xa, yw, zs_a), "trim")
            chassis.add_quad((xb, -yw, z0), (xa, -yw, z0), (xa, -yw, zs_a), (xb, -yw, zs_b), "trim")

    # Seal front & rear door jambs
    for x_edge, flip_e in ((sp["x_door0"], False), (sp["x_door1"], True)):
        ys_e, _, yb_e, zs_e, zbe = side_profile(x_edge)
        door_l.add_quad((x_edge, ys_e, zs_e + 1.5), (x_edge, ys_e - 2.4, zs_e + 1.5),
                        (x_edge, yb_e - 2.4, zbe - 0.4), (x_edge, yb_e, zbe), "trim", flip=flip_e)
        door_r.add_quad((x_edge, -ys_e, zs_e + 1.5), (x_edge, -yb_e, zbe),
                        (x_edge, -yb_e + 2.4, zbe - 0.4), (x_edge, -ys_e + 2.4, zs_e + 1.5), "trim", flip=flip_e)

    # ------------------------------------------------------------------ 2. Seamless Curved Front Fascia, Bumper & Engine Bay
    _, _, yb_f, _, zbf = side_profile(x_nose)
    add_curved_fascia(chassis, x_nose, 2.0, yb_f, z_bmp, zn_top, is_front=True, n_strips=6)
    f_bmp_top_reg = "chrome" if kind == "truck" else ("auto" if kind == "sedan" else "trim")
    add_wraparound_bumper(bumper_f, x_nose - 0.5, x1 + 0.5, 2.2, hw * 0.96, z0, z_bmp, wing_len=6.5, is_front=True, top_reg=f_bmp_top_reg)

    # Recessed 3D Engine Bay + Engine Block + Cowl Wiper Deck!
    xc = sp["x_cowl"]
    ye = yb_f * 0.82
    ze_flr = zn_top - 10.5
    chassis.add_box(xc + 2.0, -ye, ze_flr, x_nose - 2.5, ye, ze_flr + 2.0, "trim")
    chassis.add_box(xc + 7.0, -13.0, ze_flr + 2.0, x_nose - 11.0, 13.0, zn_top - 1.5, "engine")
    chassis.add_box(x_nose - 7.5, -ye * 0.80, ze_flr + 2.0, x_nose - 3.5, ye * 0.80, zn_top - 1.2, "chrome")
    # Cowl wiper plenum strip at base of windshield + flanking fender crowns
    _, _, yb_cowl, _, zb_cowl = side_profile(xc)
    chassis.add_quad((xc - 2.5, -yb_cowl, zb_cowl - 0.2), (xc + 1.2, -yb_cowl * 0.98, zb_cowl),
                     (xc + 1.2, yb_cowl * 0.98, zb_cowl), (xc - 2.5, yb_cowl, zb_cowl - 0.2), "top")
    for sgn_y in (-1.0, 1.0):
        y_in = ye * sgn_y
        y_out_f = yb_f * sgn_y
        y_out_c = yb_cowl * sgn_y
        if sgn_y > 0:
            chassis.add_quad((xc, y_in, zb_cowl - 0.4), (x_nose, y_in, zn_top - 0.4),
                             (x_nose, y_out_f, zn_top), (xc, y_out_c, zb_cowl), "top")
        else:
            chassis.add_quad((xc, y_out_c, zb_cowl), (x_nose, y_out_f, zn_top),
                             (x_nose, y_in, zn_top - 0.4), (xc, y_in, zb_cowl - 0.4), "top")

    # Detachable 3D Sculpted Hood (`hood`, hinges at cowl x=xc!)
    hood_nx, hood_ny = 5, 7
    hood_grid = []
    for i in range(hood_nx):
        tx = i / (hood_nx - 1)
        xh = (xc + 0.8) + (x_nose + 0.8 - (xc + 0.8)) * tx
        _, _, yb_h, _, zbh = side_profile(xh)
        yh_max = yb_h * 0.85
        row = []
        for j in range(hood_ny):
            ty = -1.0 + 2.0 * j / (hood_ny - 1)
            yh = yh_max * ty
            crown = (1.0 - ty * ty) * (2.8 if kind == "truck" else (1.4 if kind == "van" else 2.0))
            if kind == "truck" and abs(ty) < 0.50:
                crown += 1.6 * math.sin(math.pi * (0.12 + 0.78 * tx))
            elif kind == "coupe" and 0.24 < abs(ty) < 0.66 and 0.24 < tx < 0.78:
                crown -= 0.85
            row.append((xh, yh, zbh + crown))
        hood_grid.append(row)
    hood.add_thick_panel(hood_grid, (0.0, 0.0, -1.5), outer_region="top", inner_region="trim")

    # ------------------------------------------------------------------ 3. Framed 3D Cabin Greenhouse, Interior & Rear!
    _, _, yb_r, _, _ = side_profile(x_tail)
    yr = sp["y_roof"]
    xr0, xr1 = sp["x_roof0"], sp["x_roof1"]
    zr_edge = z1 - 1.6

    # 3D Cabin Interior (floor, dashboard, steering wheel, seats)
    if kind != "van":
        z_cab_flr = z0 + 4.5
        chassis.add_box(sp["x_cab_rear"] + 4.0, -hw * 0.72, z_cab_flr, xc - 2.0, hw * 0.72, z_cab_flr + 2.2, "interior")
        chassis.add_box(xc - 13.0, -hw * 0.70, z_cab_flr + 2.2, xc - 2.0, hw * 0.70, zb + 1.2, "interior")
        chassis.add_cylinder((xc - 13.5, 13.5, zb - 1.0), (xc - 17.0, 13.5, zb + 1.5), 5.2, 5.2, segs=10, region="trim")
        for sy in (-14.0, 14.0):
            chassis.add_box(sp["x_door0"] + 4.5, sy - 8.5, z_cab_flr + 2.2, sp["x_door0"] + 21.0, sy + 8.5, zb - 3.5, "interior")
            chassis.add_box(sp["x_door0"] + 3.5, sy - 8.0, zb - 3.5, sp["x_door0"] + 9.5, sy + 8.0, zb + 9.5, "interior")
            chassis.add_box(sp["x_door0"] + 4.5, sy - 4.2, zb + 9.5, sp["x_door0"] + 9.0, sy + 4.2, zb + 15.0, "trim")

    # Crowned Roof Skin + Watertight Curved Front/Rear Crown Header Caps across all 4 vehicles!
    n_roof_strips = 6 if kind == "van" else 4
    crown_h = 2.3 if kind == "van" else 1.7
    for j in range(n_roof_strips):
        ya = -yr + 2.0 * yr * j / n_roof_strips
        yb_s = -yr + 2.0 * yr * (j + 1) / n_roof_strips
        za = zr_edge + (1.0 - (ya / yr) ** 2) * crown_h
        zbs = zr_edge + (1.0 - (yb_s / yr) ** 2) * crown_h
        chassis.add_quad((xr0, ya, za), (xr1, ya, za), (xr1, yb_s, zbs), (xr0, yb_s, zbs), "top")
        chassis.add_quad((xr1, ya, zr_edge), (xr1, yb_s, zr_edge), (xr1, yb_s, zbs), (xr1, ya, za), "top")
        chassis.add_quad((xr0, yb_s, zr_edge), (xr0, ya, zr_edge), (xr0, ya, za), (xr0, yb_s, zbs), "top")
    # Dark interior headliner under roof so cabin ceiling looks finished!
    chassis.add_quad((xr0 + 2.0, yr - 1.5, zr_edge - 0.8), (xr1 - 2.0, yr - 1.5, zr_edge - 0.8),
                     (xr1 - 2.0, -yr + 1.5, zr_edge - 0.8), (xr0 + 2.0, -yr + 1.5, zr_edge - 0.8), "interior")

    yb_cab = side_profile(0.5 * (sp["x_door0"] + sp["x_door1"]))[2]

    # Framed Windshield with 3D Body-Colored A-Pillars & Roof Header!
    chassis.add_framed_window(
        (xc, -yb_cowl, zb), (xc, yb_cowl, zb),
        (xr1, yr, zr_edge), (xr1, -yr, zr_edge),
        w_bot=2.2, w_right=4.2, w_top=2.8, w_left=4.2, recess=0.95,
        bot_reg="trim", right_reg="auto", top_reg="top", left_reg="auto",
    )

    if kind == "truck":
        # Rear Cab Wall + Framed Sliding Backlight Window
        chassis.add_framed_window(
            (-20.0, yb_cab, zb), (-20.0, -yb_cab, zb),
            (xr0, -yr, zr_edge), (xr0, yr, zr_edge),
            w_bot=3.0, w_right=6.5, w_top=3.0, w_left=6.5, recess=0.85,
            bot_reg="auto", right_reg="auto", top_reg="auto", left_reg="auto",
        )
        # Extended-Cab Quarter Windows (B-pillar trim in front, wide body-colored C-pillar at rear!)
        chassis.add_framed_window(
            (-2.0, yb_cab, zb), (-20.0, yb_cab, zb), (xr0, yr, zr_edge), (-2.0, yr, zr_edge),
            w_bot=1.6, w_right=4.5, w_top=2.5, w_left=2.2, recess=0.80,
            bot_reg="trim", right_reg="auto", top_reg="auto", left_reg="trim",
        )
        chassis.add_framed_window(
            (-20.0, -yb_cab, zb), (-2.0, -yb_cab, zb), (-2.0, -yr, zr_edge), (xr0, -yr, zr_edge),
            w_bot=1.6, w_right=2.2, w_top=2.5, w_left=4.5, recess=0.80,
            bot_reg="trim", right_reg="trim", top_reg="auto", left_reg="auto",
        )
        # Framed Detachable Front Door Upper Windows!
        door_l.add_framed_window(
            (37.0, yb_cowl * 0.96, zb), (-2.0, yb_cab, zb), (-2.0, yr, zr_edge), (xr1, yr, zr_edge),
            w_bot=1.4, w_right=2.6, w_top=2.4, w_left=3.0, recess=0.75,
            bot_reg="trim", right_reg="trim", top_reg="auto", left_reg="auto", double_sided_frame=True,
        )
        door_r.add_framed_window(
            (-2.0, -yb_cab, zb), (37.0, -yb_cowl * 0.96, zb), (xr1, -yr, zr_edge), (-2.0, -yr, zr_edge),
            w_bot=1.4, w_right=3.0, w_top=2.4, w_left=2.6, recess=0.75,
            bot_reg="trim", right_reg="auto", top_reg="auto", left_reg="trim", double_sided_frame=True,
        )

        # HOLLOW 3D OPEN PICKUP CARGO BED (-110 .. -22) mapped to Rhino bedliner & diamond toolbox in RECT_TOP!
        xb0, xb1 = sp["x_bed_r"], sp["x_bed_f"]
        y_bed_in = hw * 0.78
        z_bed_flr = z0 + 19.2
        chassis.add_quad((xb0, -y_bed_in, z_bed_flr), (xb1, -y_bed_in, z_bed_flr),
                         (xb1, y_bed_in, z_bed_flr), (xb0, y_bed_in, z_bed_flr), "top")
        chassis.add_quad((xb1, y_bed_in, z_bed_flr), (xb1, -y_bed_in, z_bed_flr),
                         (xb1, -y_bed_in, zb), (xb1, y_bed_in, zb), "trim")
        for sgn_y in (-1.0, 1.0):
            yo = yb_cab * sgn_y
            yi = y_bed_in * sgn_y
            if sgn_y > 0:
                chassis.add_quad((xb0, yi, z_bed_flr), (xb0, yi, zb), (xb1, yi, zb), (xb1, yi, z_bed_flr), "trim")
                chassis.add_quad((xb0, yi, zb), (xb0, yo, zb), (xb1, yo, zb), (xb1, yi, zb), "trim")
                chassis.add_box(sp["wheel_x_r"] - 18.0, yi - 7.5, z_bed_flr, sp["wheel_x_r"] + 18.0, yi, z_bed_flr + 6.5, "trim", {"+z": "top"})
            else:
                chassis.add_quad((xb1, yi, z_bed_flr), (xb1, yi, zb), (xb0, yi, zb), (xb0, yi, z_bed_flr), "trim")
                chassis.add_quad((xb1, yi, zb), (xb1, yo, zb), (xb0, yo, zb), (xb0, yi, zb), "trim")
                chassis.add_box(sp["wheel_x_r"] - 18.0, yi, z_bed_flr, sp["wheel_x_r"] + 18.0, yi + 7.5, z_bed_flr + 6.5, "trim", {"+z": "top"})

        # 3D Diamond-Plate Aluminum Truck Toolbox (-42 .. -23.5)
        chassis.add_box(-42.0, -y_bed_in - 1.2, z_bed_flr + 1.5, -23.5, y_bed_in + 1.2, zb + 4.2, "chrome", {"+z": "top"})

        # Corner rear taillight pillars (z_bmp .. zr_top) + Chrome Rear Step Bumper + Hitch!
        for sgn_y in (-1.0, 1.0):
            ya, yb_p = min(y_bed_in * sgn_y, yb_r * sgn_y), max(y_bed_in * sgn_y, yb_r * sgn_y)
            chassis.add_quad((x_tail, yb_p, z_bmp), (x_tail, ya, z_bmp), (x_tail, ya, zr_top), (x_tail, yb_p, zr_top), "rear")
        add_wraparound_bumper(bumper_r, x_tail + 0.5, x0 - 0.8, -1.6, hw * 0.96, z0, z_bmp, wing_len=6.5, is_front=False, top_reg="trim")
        bumper_r.add_cylinder((x0 - 2.8, 0.0, z_bmp - 2.5), (x0 - 2.8, 0.0, z_bmp + 2.2), 2.0, 1.8, segs=8, region="chrome")

        # EXTRA PART (Truck): Detachable Tailgate (z_bmp .. zr_top) + Roll-Bar + 4 KC Off-Road Spotlights!
        extra.add_box(x_tail - 0.6, -y_bed_in, z_bmp + 0.4, x_tail + 2.4, y_bed_in, zr_top, "trim", {"-x": "rear", "+x": "trim"})
        z_rb = z1 + 4.5
        for sgn_y in (-1.0, 1.0):
            yrb = (y_bed_in - 3.5) * sgn_y
            extra.add_cylinder((-26.0, yrb, zb), (-28.0, yrb * 0.86, z_rb), 2.1, 1.9, segs=8, region="trim")
            extra.add_cylinder((-28.0, yrb * 0.86, z_rb - 1.0), (-58.0, yrb, zb), 1.7, 1.7, segs=8, region="trim")
        extra.add_cylinder((-28.0, -(y_bed_in - 3.5) * 0.86, z_rb), (-28.0, (y_bed_in - 3.5) * 0.86, z_rb), 2.0, 2.0, segs=8, region="trim")
        for ly in (-18.0, -6.0, 6.0, 18.0):
            extra.add_cylinder((-30.0, ly, z_rb + 5.0), (-25.5, ly, z_rb + 5.0), 3.9, 4.2, segs=10, region="chrome")

        # Wide Chrome Tow Mirrors + Twin Dual Exhausts
        for d_pb, sy in ((door_l, 1.0), (door_r, -1.0)):
            d_pb.add_box(28.0, sy * (yb_cab - 0.5), zb + 2.0, 31.0, sy * (yb_cab + 8.0), zb + 4.0, "trim")
            d_pb.add_box(27.0, sy * (yb_cab + 7.2), zb + 0.5, 31.5, sy * (yb_cab + 10.2), zb + 11.2, "chrome")
        for ey in (-16.0, 16.0):
            detail.add_cylinder((-85.0, ey, z0 + 1.0), (x0 - 3.5, ey * 1.15, z0 - 0.8), 2.2, 2.4, segs=10, region="chrome")

    elif kind == "sedan":
        # Framed Rear Backlight Window with wide 90s Body-Colored C-Pillars!
        _, _, yb_cr, _, zb_cr = side_profile(-48.0)
        chassis.add_framed_window(
            (-48.0, yb_cr * 0.95, zb_cr), (-48.0, -yb_cr * 0.95, zb_cr),
            (xr0, -yr, zr_edge), (xr0, yr, zr_edge),
            w_bot=2.4, w_right=6.2, w_top=2.8, w_left=6.2, recess=0.85,
            bot_reg="auto", right_reg="auto", top_reg="top", left_reg="auto",
        )
        # Rear Door + C-Pillar Side Windows (satin-black B-pillar in front, wide emerald C-pillar behind!)
        chassis.add_framed_window(
            (-4.0, yb_cab, zb), (-48.0, yb_cr * 0.95, zb_cr), (xr0, yr, zr_edge), (-4.0, yr, zr_edge),
            w_bot=1.5, w_right=6.5, w_top=2.5, w_left=2.4, recess=0.80,
            bot_reg="trim", right_reg="auto", top_reg="auto", left_reg="trim",
        )
        chassis.add_framed_window(
            (-48.0, -yb_cr * 0.95, zb_cr), (-4.0, -yb_cab, zb), (-4.0, -yr, zr_edge), (xr0, -yr, zr_edge),
            w_bot=1.5, w_right=2.4, w_top=2.5, w_left=6.5, recess=0.80,
            bot_reg="trim", right_reg="trim", top_reg="auto", left_reg="auto",
        )
        # Framed Detachable Front Door Windows!
        door_l.add_framed_window(
            (31.0, yb_cowl * 0.96, zb), (-4.0, yb_cab, zb), (-4.0, yr, zr_edge), (xr1, yr, zr_edge),
            w_bot=1.4, w_right=2.4, w_top=2.4, w_left=3.2, recess=0.75,
            bot_reg="trim", right_reg="trim", top_reg="auto", left_reg="auto", double_sided_frame=True,
        )
        door_r.add_framed_window(
            (-4.0, -yb_cab, zb), (31.0, -yb_cowl * 0.96, zb), (xr1, -yr, zr_edge), (-4.0, -yr, zr_edge),
            w_bot=1.4, w_right=3.2, w_top=2.4, w_left=2.4, recess=0.75,
            bot_reg="trim", right_reg="auto", top_reg="auto", left_reg="trim", double_sided_frame=True,
        )
        chassis.add_box(-42.0, -hw * 0.66, z_cab_flr + 2.2, -22.0, hw * 0.66, zb + 5.5, "interior")

        # Seamless Curved Rear Fascia (z_bmp .. zr_top) + Wraparound Rear Bumper + Recessed Trunk Bay!
        add_curved_fascia(chassis, x_tail, -1.8, yb_r, z_bmp, zr_top, is_front=False, n_strips=6)
        add_wraparound_bumper(bumper_r, x_tail + 0.5, x0 - 0.5, -2.0, hw * 0.95, z0, z_bmp, wing_len=6.5, is_front=False, top_reg="auto")
        chassis.add_box(-92.0, -yb_r * 0.82, zr_top - 8.5, -49.0, yb_r * 0.82, zr_top - 6.5, "interior")

        # EXTRA PART (Sedan): Sculpted 3D Trunk Decklid (-95 .. -48)
        tr_grid = []
        for i in range(4):
            tx = i / 3.0
            xt = (x_tail + 0.5) + (-48.0 - (x_tail + 0.5)) * tx
            _, _, ybt, _, zbt = side_profile(xt)
            yt_m = ybt * 0.88
            tr_grid.append([(xt, yt_m * (-1.0 + 2.0 * j / 4.0), zbt + 1.3 * (1.0 - (-1.0 + 2.0 * j / 4.0) ** 2)) for j in range(5)])
        extra.add_thick_panel(tr_grid, (0.0, 0.0, -1.4), outer_region="top", inner_region="trim")

        # Molded Mirrors + Whip Radio Antenna + Exhaust Tip!
        for d_pb, sy in ((door_l, 1.0), (door_r, -1.0)):
            d_pb.add_box(22.0, sy * (yb_cab - 0.5), zb + 0.6, 27.5, sy * (yb_cab + 6.2), zb + 5.0, "auto", {"-x": "glass"})
        detail.add_cylinder((-68.0, yb_r * 0.84, zr_top), (-74.0, yb_r * 0.88, zr_top + 27.0), 0.72, 0.26, segs=6, region="chrome")
        detail.add_cylinder((-76.0, -15.5, z0 + 0.2), (x0 - 3.0, -15.5, z0 - 0.6), 2.0, 2.2, segs=10, region="chrome")

    elif kind == "van":
        # Accurate Ram ProMaster High-Roof Cargo Van with Full Walk-In Interior & Swung-Open Barn Doors!
        # (Matched to reference video: grok-video-3f2de7de-cdc4-4d85-a228-0dc8ac13ba50.mp4)

        # 1. Front Fascia Grille & Swept Headlight Units
        chassis.add_box(x_nose - 5.0, -hw * 0.62, z_bmp + 2.0, x_nose - 0.5, hw * 0.62, zn_top - 1.0, "front")
        for sy in (-1.0, 1.0):
            chassis.add_box(x_nose - 8.0, sy * hw * 0.62, z_bmp + 2.0, x_nose - 1.0, sy * hw * 0.96, zn_top + 1.0, "front")

        # 2. Stepped High-Roof Aerodynamic Transition over Cab (x: 10 .. 22, z: 68 .. 89.5)
        chassis.add_box(10.0, -hw * 0.80, 68.0, 22.0, hw * 0.80, 89.5, "top")
        for sy in (-1.0, 1.0):
            chassis.add_box(xr0, sy * yr - 0.8, z1 - 3.2, 10.0, sy * (yr + 1.0), z1 - 1.8, "trim")

        # 3. Outer Cargo Sides (x: xr0 .. 12) & Thick Lower Protective Cladding
        chassis.add_quad((12.0, hw * 0.92, zb), (xr0, hw * 0.92, zb), (xr0, yr, z1 - 2.5), (12.0, yr, z1 - 2.5), "side")
        chassis.add_quad((xr0, -hw * 0.92, zb), (12.0, -hw * 0.92, zb), (12.0, -yr, z1 - 2.5), (xr0, -yr, z1 - 2.5), "side")
        chassis.add_box(xr0, hw * 0.92, z0, 12.0, hw * 0.95, z_bmp + 2.0, "side")
        chassis.add_box(xr0, -hw * 0.95, z0, 12.0, -hw * 0.92, z_bmp + 2.0, "side")

        # Passenger Side Sliding Door Rail & Vertical Handle (frame 005)
        detail.add_box(-48.0, -hw * 0.96, zb + 1.5, 8.0, -hw * 0.93, zb + 3.5, "chrome")
        detail.add_box(3.0, -hw * 0.98, zb - 4.0, 7.0, -hw * 0.94, zb + 4.0, "trim")

        # Framed Cab Door Windows (door_l / door_r) from x: 12 .. 46
        door_l.add_framed_window(
            (46.0, hw * 0.88, zb), (12.0, hw * 0.92, zb),
            (12.0, hw * 0.82, 68.0), (22.0, hw * 0.78, 68.0),
            w_bot=1.6, w_right=3.0, w_top=2.2, w_left=2.8, recess=0.80,
            bot_reg="side", right_reg="side", top_reg="top", left_reg="side", double_sided_frame=True,
        )
        door_r.add_framed_window(
            (12.0, -hw * 0.92, zb), (46.0, -hw * 0.88, zb),
            (22.0, -hw * 0.78, 68.0), (12.0, -hw * 0.82, 68.0),
            w_bot=1.6, w_right=2.8, w_top=2.2, w_left=3.0, recess=0.80,
            bot_reg="side", right_reg="side", top_reg="top", left_reg="side", double_sided_frame=True,
        )
        # Commercial Dual-Lens Wing Mirrors on Doors
        for d_pb, sy in ((door_l, 1.0), (door_r, -1.0)):
            d_pb.add_box(42.0, sy * (hw * 0.90), zb + 4.0, 45.0, sy * (hw * 0.90 + 7.5), zb + 5.5, "trim")
            d_pb.add_box(41.0, sy * (hw * 0.90 + 6.0), zb + 1.0, 46.0, sy * (hw * 0.90 + 13.5), zb + 14.5, "trim",
                         {("-y" if sy > 0 else "+y"): "glass"})

        # 4. Rear Fascia & Open Walk-In Doorway (y: -26 .. +26, z: 18 .. 82)
        # Rear D-pillar vertical taillight columns
        for sy in (-1.0, 1.0):
            chassis.add_box(-106.5, sy * 26.0, z_bmp + 2.0, -105.0, sy * (hw * 0.94), 86.5, "rear")
        # Rear top header arch with high-mount 3rd brake light
        chassis.add_box(-106.5, -26.0, 82.0, -105.0, 26.0, 87.5, "rear")
        detail.add_box(-107.0, -5.5, 84.0, -106.0, 5.5, 86.2, "trim")

        # Black Rear Step Bumper with Low Center Step (z=13.5) for Smooth Walk-In!
        for sy in (-1.0, 1.0):
            bumper_r.add_box(-112.5, sy * 24.0, z0, -105.0, sy * (hw * 0.96), z_bmp + 2.0, "rear")
        bumper_r.add_box(-113.5, -24.0, z0, -105.0, 24.0, 13.5, "trim")
        bumper_r.add_box(-106.0, -26.0, 13.5, -105.0, 26.0, 18.0, "trim")

        # 5. Swung-Open 50/50 Rear Barn Doors (in extra_part, frame 001, 020)
        # Left rear door: swung open outward ~100 degrees
        extra.add_box(-128.0, 29.5, 19.5, -106.0, 32.0, 81.5, "rear",
                      {"+y": "rear", "-y": "int_wall", "+x": "trim", "-x": "trim"})
        for hz in (28.0, 72.0):
            extra.add_cylinder((-106.0, 28.0, hz - 2.5), (-106.0, 28.0, hz + 2.5), 1.2, 1.2, segs=8, region="trim")
            extra.add_box(-108.0, 27.0, hz - 1.5, -105.0, 30.5, hz + 1.5, "trim")

        # Right rear door: swung open outward ~100 degrees (with license plate & inner latch handle)
        extra.add_box(-128.0, -32.0, 19.5, -106.0, -29.5, 81.5, "rear",
                      {"-y": "rear", "+y": "int_wall", "+x": "trim", "-x": "trim"})
        for hz in (28.0, 72.0):
            extra.add_cylinder((-106.0, -28.0, hz - 2.5), (-106.0, -28.0, hz + 2.5), 1.2, 1.2, segs=8, region="trim")
            extra.add_box(-108.0, -30.5, hz - 1.5, -105.0, -27.0, hz + 1.5, "trim")
        extra.add_box(-118.0, -29.0, 46.0, -114.0, -27.8, 51.0, "trim")

        # 6. Walk-In Interior Cargo Bay (frame 001, 020)
        # Corrugated metal cargo floor deck (x: -105 .. 10, y: -34.5 .. 34.5, z=18.0)
        chassis.add_quad((-105.0, -34.5, 18.0), (10.0, -34.5, 18.0), (10.0, 34.5, 18.0), (-105.0, 34.5, 18.0), "int_floor")
        chassis.add_quad((-105.0, 34.5, z0 + 1.0), (10.0, 34.5, z0 + 1.0),
                         (10.0, -34.5, z0 + 1.0), (-105.0, -34.5, z0 + 1.0), "bottom")
        # Inward-facing stamped interior cargo walls (no backface culling!)
        chassis.add_quad((10.0, 34.0, 18.0), (-105.0, 34.0, 18.0), (-105.0, 34.0, 84.0), (10.0, 34.0, 84.0), "int_wall")
        chassis.add_quad((-105.0, -34.0, 18.0), (10.0, -34.0, 18.0), (10.0, -34.0, 84.0), (-105.0, -34.0, 84.0), "int_wall")
        # Inner wheel well tubs (arches) on cargo floor (walkthrough aisle = 50 units wide!)
        for sy in (-1.0, 1.0):
            y_w0, y_w1 = sy * 25.0, sy * 34.2
            chassis.add_box(-72.0, min(y_w0, y_w1), 18.0, -44.0, max(y_w0, y_w1), 32.5, "int_wall")
        # Inward-facing ceiling & structural roof cross-bows
        chassis.add_quad((-105.0, 34.0, 84.5), (10.0, 34.0, 84.5), (10.0, -34.0, 84.5), (-105.0, -34.0, 84.5), "interior")
        for rx in (-85.0, -60.0, -35.0, -10.0):
            chassis.add_box(rx - 1.5, -34.0, 83.5, rx + 1.5, 34.0, 85.0, "trim")
        for lx in (-75.0, -25.0):
            detail.add_box(lx - 3.5, -4.5, 83.5, lx + 3.5, 4.5, 84.5, "glass")

        # 7. Cab Safety Bulkhead Partition & Central Walkthrough Aisle (frame 020)
        chassis.add_box(9.0, 10.0, 18.0, 10.5, 34.0, 44.0, "int_wall")
        chassis.add_box(9.5, 10.0, 44.0, 10.5, 34.0, 74.0, "trim", {"+x": "glass", "-x": "glass"})
        chassis.add_box(9.0, -34.0, 18.0, 10.5, -10.0, 44.0, "int_wall")
        chassis.add_box(9.5, -34.0, 44.0, 10.5, -10.0, 74.0, "trim", {"+x": "glass", "-x": "glass"})
        # (Central aisle y: -10 .. +10 is completely open into the front cab!)

        # 8. Front Cockpit Interior (frame 010, 020)
        chassis.add_quad((10.0, -34.0, 18.0), (48.0, -34.0, 18.0), (48.0, 34.0, 18.0), (10.0, 34.0, 18.0), "interior")
        # High-Back Driver Bucket Seat (y: 12 .. 28)
        chassis.add_box(20.0, 12.0, 18.0, 34.0, 28.0, 22.0, "trim")
        chassis.add_box(20.0, 12.0, 22.0, 34.0, 28.0, 26.5, "int_seat")
        chassis.add_box(18.0, 12.0, 26.5, 21.5, 28.0, 48.0, "int_seat")
        chassis.add_box(17.5, 16.0, 48.0, 21.0, 24.0, 55.0, "int_seat")
        # High-Back Passenger Bucket Seat (y: -28 .. -12)
        chassis.add_box(20.0, -28.0, 18.0, 34.0, -12.0, 22.0, "trim")
        chassis.add_box(20.0, -28.0, 22.0, 34.0, -12.0, 26.5, "int_seat")
        chassis.add_box(18.0, -28.0, 26.5, 21.5, -12.0, 48.0, "int_seat")
        chassis.add_box(17.5, -24.0, 48.0, 21.0, -16.0, 55.0, "int_seat")

        # Center Console & Engine Doghouse Cowl with Dual Cup Holders
        chassis.add_box(18.0, -8.0, 18.0, 42.0, 8.0, 27.0, "trim")
        for cy in (-4.0, 4.0):
            detail.add_cylinder((30.0, cy, 27.1), (30.0, cy, 25.5), 2.2, 2.0, segs=8, region="trim")

        # Full Dashboard Console (speedometer, gauges, stereo, A/C louvers, glovebox)
        chassis.add_box(42.0, -34.0, 27.0, 52.0, 34.0, 43.0, "int_dash")
        chassis.add_box(40.0, 11.0, 34.0, 50.0, 27.0, 45.0, "int_dash")
        chassis.add_box(42.5, -32.0, 29.0, 51.5, -12.0, 36.0, "int_dash")

        # Steering Column & 3D Steering Wheel
        detail.add_cylinder((46.0, 20.0, 33.0), (36.0, 20.0, 39.5), 1.6, 1.4, segs=8, region="trim")
        detail.add_cylinder((38.0, 20.0, 38.0), (37.5, 25.5, 39.5), 0.5, 0.4, segs=6, region="trim")
        center_sw = Vector((35.0, 20.0, 40.0))
        sw_radius = 5.2
        sw_segs = 14
        n_sw = Vector((0.85, 0.0, 0.52)).normalized()
        u_sw = Vector((0.0, 1.0, 0.0))
        v_sw = n_sw.cross(u_sw).normalized()
        pts_rim = [center_sw + (u_sw * math.cos(2.0 * math.pi * k / sw_segs) + v_sw * math.sin(2.0 * math.pi * k / sw_segs)) * sw_radius
                   for k in range(sw_segs)]
        for k in range(sw_segs):
            detail.add_cylinder(pts_rim[k], pts_rim[(k + 1) % sw_segs], 0.65, 0.65, segs=6, region="trim", cap=False)
        detail.add_cylinder(center_sw - n_sw * 0.4, center_sw + n_sw * 0.4, 1.8, 1.8, segs=8, region="trim")
        for ang in (0.0, 2.2, 4.1):
            sp_end = center_sw + (u_sw * math.cos(ang) + v_sw * math.sin(ang)) * (sw_radius - 0.5)
            detail.add_cylinder(center_sw, sp_end, 0.6, 0.5, segs=6, region="trim")

        # Driver Foot Pedals on Firewall
        detail.add_box(48.0, 21.0, 19.0, 50.0, 23.5, 24.0, "trim")
        detail.add_box(48.0, 15.5, 20.0, 50.0, 19.5, 25.0, "trim")

        # Overhead Sun Visors & Interior Rearview Mirror
        for vy in (-18.0, 18.0):
            detail.add_box(24.0, vy - 7.0, 66.5, 28.0, vy + 7.0, 67.5, "trim")
        detail.add_box(24.0, -3.5, 63.5, 25.5, 3.5, 66.0, "trim", {"-x": "glass"})
        detail.add_cylinder((-72.0, -22.0, z0 + 0.5), (-82.0, -hw - 1.2, z0 - 0.8), 2.0, 2.2, segs=10, region="chrome")

    elif kind == "coupe":
        # Long Sweeping Fastback Rear Hatch Glass with Watertight 3D Milano-Red Sail C-Pillars!
        _, _, yb_cr, _, zb_cr = side_profile(-66.0)
        chassis.add_framed_window(
            (-66.0, yb_cr, zb_cr), (-66.0, -yb_cr, zb_cr),
            (xr0, -yr, zr_edge), (xr0, yr, zr_edge),
            w_bot=2.5, w_right=5.8, w_top=2.6, w_left=5.8, recess=0.85,
            bot_reg="top", right_reg="auto", top_reg="top", left_reg="auto",
        )
        # Sleek Rear Quarter Windows sharing exact C-pillar edge (-66.0, +-yb_cr, zb_cr) -> (xr0, +-yr, zr_edge)!
        chassis.add_framed_window(
            (-16.0, yb_cab, zb), (-66.0, yb_cr, zb_cr), (xr0, yr, zr_edge), (-16.0, yr, zr_edge),
            w_bot=1.4, w_right=7.2, w_top=2.4, w_left=2.2, recess=0.75,
            bot_reg="trim", right_reg="auto", top_reg="auto", left_reg="trim",
        )
        chassis.add_framed_window(
            (-66.0, -yb_cr, zb_cr), (-16.0, -yb_cab, zb), (-16.0, -yr, zr_edge), (xr0, -yr, zr_edge),
            w_bot=1.4, w_right=2.2, w_top=2.4, w_left=7.2, recess=0.75,
            bot_reg="trim", right_reg="trim", top_reg="auto", left_reg="auto",
        )
        # Framed Coupe Door Upper Windows
        door_l.add_framed_window(
            (25.0, yb_cowl, zb), (-16.0, yb_cab, zb), (-16.0, yr, zr_edge), (xr1, yr, zr_edge),
            w_bot=1.2, w_right=2.2, w_top=2.0, w_left=2.8, recess=0.70,
            bot_reg="trim", right_reg="trim", top_reg="auto", left_reg="auto", double_sided_frame=True,
        )
        door_r.add_framed_window(
            (-16.0, -yb_cab, zb), (25.0, -yb_cowl, zb), (xr1, -yr, zr_edge), (-16.0, -yr, zr_edge),
            w_bot=1.2, w_right=2.8, w_top=2.0, w_left=2.2, recess=0.70,
            bot_reg="trim", right_reg="auto", top_reg="auto", left_reg="trim", double_sided_frame=True,
        )

        # Short Rear Trunk Deck (-90 .. -66) + Seamless Curved Rear Fascia + Diffuser Bumper!
        chassis.add_quad((x_tail, -yb_r, zr_top), (-66.0, -yb_cr, zb_cr),
                         (-66.0, yb_cr, zb_cr), (x_tail, yb_r, zr_top), "top")
        add_curved_fascia(chassis, x_tail, -2.0, yb_r, z_bmp, zr_top, is_front=False, n_strips=6)
        add_wraparound_bumper(bumper_r, x_tail + 0.5, x0 - 0.5, -2.0, hw * 0.96, z0, z_bmp, wing_len=6.5, is_front=False, top_reg="auto")

        # EXTRA PART (Sport Coupe): High-Mount JDM Pedestal Wing Spoiler + Aero Endplates!
        zw = zr_top + 11.0
        yw = yb_r * 0.92
        for sgn_y in (-1.0, 1.0):
            yp = sgn_y * (yw * 0.68)
            extra.add_box(-86.0, yp - 1.2, zr_top, -76.0, yp + 1.2, zw, "auto")
            extra.add_box(-89.5, sgn_y * yw - 0.8, zw - 3.2, -75.0, sgn_y * yw + 0.8, zw + 3.2, "trim")
        wing_grid = [
            [(-88.5, -yw, zw + 0.8), (-88.5, 0.0, zw + 1.5), (-88.5, yw, zw + 0.8)],
            [(-76.5, -yw, zw - 1.0), (-76.5, 0.0, zw - 0.4), (-76.5, yw, zw - 1.0)],
        ]
        extra.add_thick_panel(wing_grid, (0.0, 0.0, -1.4), outer_region="top", inner_region="trim")

        # Aero Teardrop Mirrors + Angled N1 Titanium Exhaust Canister!
        for d_pb, sy in ((door_l, 1.0), (door_r, -1.0)):
            d_pb.add_cylinder((21.0, sy * (yb_cab - 0.5), zb + 1.5), (17.5, sy * (yb_cab + 5.6), zb + 3.6), 1.7, 2.3, segs=8, region="auto")
        detail.add_cylinder((-72.0, -17.0, z0 + 1.0), (-86.0, -20.5, z0), 3.4, 3.4, segs=12, region="chrome")
        detail.add_cylinder((-86.0, -20.5, z0), (x0 - 3.5, -22.2, z0 - 0.4), 2.8, 3.0, segs=12, region="chrome")

    # ------------------------------------------------------------------ 4. Undercarriage Frame Rails, Axles & Brake Discs
    for sgn_y in (-1.0, 1.0):
        chassis.add_box(x_tail + 12.0, sgn_y * 15.0 - 2.2, z0 - 1.2, x_nose - 12.0, sgn_y * 15.0 + 2.2, z0 + 1.8, "trim")
    for wx in wxs:
        chassis.add_cylinder((wx, -sp["wheel_y"] + 3.0, sp["wheel_r"]), (wx, sp["wheel_y"] - 3.0, sp["wheel_r"]), 1.8, 1.8, segs=8, region="trim")
        chassis.add_cylinder((wx, -5.0, sp["wheel_r"]), (wx, 5.0, sp["wheel_r"]), 4.2, 4.2, segs=8, region="trim")
        for sgn_y in (-1.0, 1.0):
            chassis.add_cylinder((wx, sgn_y * (sp["wheel_y"] - 3.5), sp["wheel_r"]),
                                 (wx, sgn_y * (sp["wheel_y"] - 1.5), sp["wheel_r"]),
                                 sp["wheel_r"] * 0.52, sp["wheel_r"] * 0.52, segs=12, region="chrome")

    chassis_dict = chassis.export_dict(custom_origin=(0.0, 0.0, 0.0))

    # ------------------------------------------------------------------ 5. Build Buckled, Scorched `wreck_chassis`
    wreck_verts, wreck_norms, wreck_uvs = [], [], []
    rng_w = random.Random({"truck": 71, "sedan": 72, "van": 73, "coupe": 74}[kind])
    z_slump = -sp["wheel_r"] * 0.52
    v_eng_min = 800.0 / vs.H_ATLAS
    for (vx, vy, vz), (nx, ny, nz), (u, v) in zip(chassis_dict["verts"], chassis_dict["norms"], chassis_dict["uvs"]):
        h_frac = max(0.0, (vz - zb) / max(1.0, z1 - zb))
        cave_z = -h_frac * (7.5 + 4.5 * math.sin(vx * 0.045 + 0.6))
        twist_y = h_frac * 4.2 * math.cos(vx * 0.035)
        banana_z = ((vx / max(1.0, x1)) ** 2) * 4.5
        dent_y = -0.07 * vy * (0.5 + 0.5 * math.sin(vx * 0.09 + vz * 0.07))
        nx_v = vx * 0.985 + math.sin(vz * 0.11 + vy * 0.08) * 1.4
        ny_v = vy + twist_y + dent_y
        nz_v = max(0.4, vz + z_slump + cave_z + banana_z)
        wreck_verts.append([round(nx_v, 3), round(ny_v, 3), round(nz_v, 3)])
        wreck_norms.append([nx, ny, nz])
        if v >= v_eng_min and u < 0.25:
            wu, wv = vs.rect_uv(vs.RECT_EMBER, u / 0.25, (v - v_eng_min) / (1.0 - v_eng_min))
        else:
            su = (abs(vx * 0.007 + vy * 0.011)) % 1.0
            sv = (abs(vz * 0.013 + vx * 0.005)) % 1.0
            wu, wv = vs.rect_uv(vs.RECT_WRECK, su, sv)
        wreck_uvs.append([wu, wv])

    wreck_dict = {
        "name": "wreck_chassis",
        "origin": [0.0, 0.0, 0.0],
        "verts": wreck_verts,
        "norms": wreck_norms,
        "uvs": wreck_uvs,
        "tris": chassis_dict["tris"],
    }

    # ------------------------------------------------------------------ 6. Build 4 Unique 3D Wheels
    w_l_mesh = build_3d_wheel("wheel_left_proto", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], True, sp)
    w_r_mesh = build_3d_wheel("wheel_right_proto", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], False, sp)

    def place_wheel(proto, nm, wx, wy, wz):
        cp = dict(proto)
        cp["name"] = nm
        cp["origin"] = [round(wx, 3), round(wy, 3), round(wz, 3)]
        return cp

    wh_fl = place_wheel(w_l_mesh, "wheel_fl", sp["wheel_x_f"], sp["wheel_y"], sp["wheel_r"])
    wh_fr = place_wheel(w_r_mesh, "wheel_fr", sp["wheel_x_f"], -sp["wheel_y"], sp["wheel_r"])
    wh_rl = place_wheel(w_l_mesh, "wheel_rl", sp["wheel_x_r"], sp["wheel_y"], sp["wheel_r"])
    wh_rr = place_wheel(w_r_mesh, "wheel_rr", sp["wheel_x_r"], -sp["wheel_y"], sp["wheel_r"])

    # ------------------------------------------------------------------ 7. Build 10 Twisted 3D Shrapnel Chunks
    shraps = []
    for si in range(10):
        spb = PartBuilder(f"shrap_{si}", sp)
        r_sh = 4.5 + (si % 4) * 2.2
        thk = 0.9 + (si % 3) * 0.6
        reg = ("auto", "wreck", "glass", "chrome", "ember")[si % 5]
        pts_grid = []
        for gi in range(3):
            row = []
            for gj in range(3):
                px = (gi - 1) * r_sh + rng_w.uniform(-1.6, 1.6)
                py = (gj - 1) * r_sh * 0.78 + rng_w.uniform(-1.4, 1.4)
                pz = math.sin(gi * 1.4 + gj * 1.1 + si) * 2.4
                row.append((px, py, pz))
            pts_grid.append(row)
        spb.add_thick_panel(pts_grid, (0.0, 0.0, -thk), outer_region=reg, inner_region="wreck")
        sd = spb.export_dict(custom_origin=(0.0, 0.0, 0.0))
        ang = 2.0 * math.pi * si / 10.0
        sd["origin"] = [
            round(math.cos(ang) * (x1 * 0.48), 2),
            round(math.sin(ang) * (hw * 0.62), 2),
            round(zb * 0.78 + (si % 3) * 5.5, 2),
        ]
        shraps.append(sd)

    parts = {
        "chassis": chassis_dict,
        "wreck_chassis": wreck_dict,
        "hood": hood.export_dict(hinge_pivot=(xc, 0.0, zb_cowl)),
        "door_l": door_l.export_dict(),
        "door_r": door_r.export_dict(),
        "extra_part": extra.export_dict(),
        "bumper_f": bumper_f.export_dict(),
        "bumper_r": bumper_r.export_dict(),
        "detail_vib": detail.export_dict(),
        "wheel_fl": wh_fl,
        "wheel_fr": wh_fr,
        "wheel_rl": wh_rl,
        "wheel_rr": wh_rr,
    }
    for si, sd in enumerate(shraps):
        parts[f"shrap_{si}"] = sd

    tot_v = sum(len(p["verts"]) for k, p in parts.items() if k != "wreck_chassis" and not k.startswith("shrap_"))
    tot_t = sum(len(p["tris"]) for k, p in parts.items() if k != "wreck_chassis" and not k.startswith("shrap_"))
    print(f"  [{kind:6s}] intact={tot_v:4d} verts / {tot_t:4d} tris | wheel={len(wh_fl['tris']):3d} tris | wreck={len(wreck_dict['tris']):4d} tris")
    return {"spec": sp, "parts": parts}


def main():
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    all_vehicles = {}
    for kind in ("truck", "sedan", "van", "coupe"):
        all_vehicles[kind] = build_single_vehicle(kind)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_vehicles, f)
    print(f"Wrote {OUT_JSON} ({os.path.getsize(OUT_JSON) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
