"""Dedicated Builder & Exporter for BakersfieldQuake's Accurate Ram ProMaster Walk-In Van.
Matches reference video grok-video-3f2de7de-cdc4-4d85-a228-0dc8ac13ba50.mp4:
  - Exact Ram ProMaster / Fiat Ducato high-roof commercial cargo body
  - Multi-tier front commercial bumper with air intakes and fog pods
  - Horizontal black slat grille with prominent center chrome emblem
  - High-mounted swept modern aerodynamic headlights wrapping into fenders
  - Short steep snub nose hood with cowl grille and dual wipers
  - High-roof stepped profile rising smoothly above cab (standing interior height!)
  - Wide satin-black lower protective body cladding with amber side markers
  - Passenger side sliding cargo door with horizontal silver guide rail
  - Driver side clean blind panel with fuel door
  - Heavy-duty commercial dual-lens wing mirrors with side indicators
  - Rear step bumper with low center non-slip step for easy walk-in
  - Vertical D-pillar taillights and high-mount 3rd brake light
  - Swung-open 50/50 rear cargo barn doors showing realistic inner door cards and handles
  - Full walk-in interior:
      * Corrugated/ribbed metal cargo floor with anti-skid ribs and tie-downs
      * Stamped structural inner walls with vertical hat-channel ribs and horizontal rails
      * Ribbed inner wheel well tubs
      * Arched structural ceiling bows with dual cargo dome lights
      * Cab safety bulkhead partition with wire-mesh screen and open walkthrough aisle
      * High-back driver bucket seat with headrest
      * High-back passenger bucket seat with headrest
      * Center console / doghouse with cup holders
      * Full dashboard console with instrument cluster binnacle, A/C louvers, stereo, climate knobs, glovebox
      * Steering column with angled 3D steering wheel and turn signal stalk
      * Accelerator and brake foot pedals
      * Clear windshield safety glass, sun visors, interior rearview mirror
"""
import json
import math
import os
import sys

import bmesh
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import veh_specs as vs

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


class MeshPart:
    """Accumulates vertices, quads, and triangles with veh_specs UV projection."""
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
        L = axis.length
        if L < 1e-4:
            return
        d = axis / L
        ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        u = d.cross(ref).normalized()
        v = d.cross(u).normalized()
        ring0, ring1 = [], []
        for i in range(segs):
            th = 2.0 * math.pi * i / segs
            cu, cv = math.cos(th), math.sin(th)
            ring0.append(a + (u * cu + v * cv) * r0)
            ring1.append(b + (u * cu + v * cv) * r1)
        for i in range(segs):
            j = (i + 1) % segs
            self.add_quad(ring0[i], ring0[j], ring1[j], ring1[i], region)
        if cap:
            for i in range(1, segs - 1):
                self.add_tri(ring0[0], ring0[i + 1], ring0[i], region)
                self.add_tri(ring1[0], ring1[i], ring1[i + 1], region)

    def add_thick_panel(self, grid_pts, thickness_vec, outer_region="auto", inner_region="trim"):
        nx = len(grid_pts)
        ny = len(grid_pts[0])
        tv = Vector(thickness_vec)
        top_g = [[Vector(grid_pts[i][j]) for j in range(ny)] for i in range(nx)]
        bot_g = [[top_g[i][j] + tv for j in range(ny)] for i in range(nx)]
        for i in range(nx - 1):
            for j in range(ny - 1):
                self.add_quad(top_g[i][j], top_g[i + 1][j], top_g[i + 1][j + 1], top_g[i][j + 1], outer_region)
                self.add_quad(bot_g[i][j], bot_g[i][j + 1], bot_g[i + 1][j + 1], bot_g[i + 1][j], inner_region)
        for i in range(nx - 1):
            self.add_quad(top_g[i][0], bot_g[i][0], bot_g[i + 1][0], top_g[i + 1][0], inner_region)
            self.add_quad(top_g[i][ny - 1], top_g[i + 1][ny - 1], bot_g[i + 1][ny - 1], bot_g[i][ny - 1], inner_region)
        for j in range(ny - 1):
            self.add_quad(top_g[0][j], top_g[0][j + 1], bot_g[0][j + 1], bot_g[0][j], inner_region)
            self.add_quad(top_g[nx - 1][j], bot_g[nx - 1][j], bot_g[nx - 1][j + 1], top_g[nx - 1][j + 1], inner_region)

    def add_framed_window(self, p_bl, p_br, p_tr, p_tl, w_bot, w_right, w_top, w_left,
                          recess=0.8, bot_reg="auto", right_reg="auto", top_reg="auto", left_reg="auto",
                          double_sided_frame=False):
        c0, c1, c2, c3 = Vector(p_bl), Vector(p_br), Vector(p_tr), Vector(p_tl)
        e_bot = c1 - c0
        e_right = c2 - c1
        e_top = c3 - c2
        e_left = c0 - c3
        n = (e_bot.cross(e_right)).normalized()
        inward_b = (n.cross(e_bot)).normalized()
        inward_r = (n.cross(e_right)).normalized()
        inward_t = (n.cross(e_top)).normalized()
        inward_l = (n.cross(e_left)).normalized()
        i0 = c0 + inward_b * w_bot + inward_l * w_left - n * recess
        i1 = c1 + inward_b * w_bot + inward_r * w_right - n * recess
        i2 = c2 + inward_t * w_top + inward_r * w_right - n * recess
        i3 = c3 + inward_t * w_top + inward_l * w_left - n * recess
        self.add_quad(c0, c1, i1, i0, bot_reg)
        self.add_quad(c1, c2, i2, i1, right_reg)
        self.add_quad(c2, c3, i3, i2, top_reg)
        self.add_quad(c3, c0, i0, i3, left_reg)
        self.add_quad(i0, i1, i2, i3, "glass")
        self.add_quad(i0, i3, i2, i1, "glass")
        if double_sided_frame:
            ib0 = c0 + inward_b * w_bot + inward_l * w_left + n * (recess + 0.4)
            ib1 = c1 + inward_b * w_bot + inward_r * w_right + n * (recess + 0.4)
            ib2 = c2 + inward_t * w_top + inward_r * w_right + n * (recess + 0.4)
            ib3 = c3 + inward_t * w_top + inward_l * w_left + n * (recess + 0.4)
            self.add_quad(c1, c0, ib0, ib1, bot_reg)
            self.add_quad(c2, c1, ib1, ib2, right_reg)
            self.add_quad(c3, c2, ib2, ib3, top_reg)
            self.add_quad(c0, c3, ib3, ib0, left_reg)

    def to_dict(self):
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces[:])
        self.bm.verts.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()
        verts, norms, uvs, tris = [], [], [], []
        v_map = {}
        for f in self.bm.faces:
            tri_indices = []
            for l in f.loops:
                v = l.vert
                pos = (round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3))
                nor = (round(f.normal.x, 4), round(f.normal.y, 4), round(f.normal.z, 4))
                uv = (round(l[self.uv_layer].uv.x, 4), round(l[self.uv_layer].uv.y, 4))
                key = (pos, nor, uv)
                idx = v_map.get(key)
                if idx is None:
                    idx = len(verts)
                    v_map[key] = idx
                    verts.append(pos)
                    norms.append(nor)
                    uvs.append(uv)
                tri_indices.append(idx)
            tris.append((tri_indices[0], tri_indices[1], tri_indices[2]))
        self.bm.free()
        return dict(verts=verts, norms=norms, uvs=uvs, tris=tris)


def build_3d_wheel(radius, width, dish_depth, rim_ratio, is_left, sp):
    """Builds sculpted 8-lug commercial steel wheel synced to RECT_WHEEL."""
    pb = MeshPart("wheel", sp)
    n_segs = 16
    r_hub = radius * rim_ratio
    sgn = 1.0 if is_left else -1.0
    r_px_center = (128.0, 672.0)
    R_px_tire = 116.0
    R_px_rim = R_px_tire * rim_ratio

    def rim_uv(r_world, th):
        s = r_world / radius
        r_px = R_px_tire * s
        px = r_px_center[0] + r_px * math.cos(th)
        py = r_px_center[1] + r_px * math.sin(th)
        return (round(px / vs.W_ATLAS, 4), round(py / vs.H_ATLAS, 4))

    for i in range(n_segs):
        th0 = 2.0 * math.pi * i / n_segs
        th1 = 2.0 * math.pi * (i + 1) / n_segs
        c0, s0 = math.cos(th0), math.sin(th0)
        c1, s1 = math.cos(th1), math.sin(th1)

        y_out = sgn * (width * 0.5)
        y_dish = sgn * (width * 0.5 - dish_depth)
        y_in = -sgn * (width * 0.5)

        p_t0 = (radius * c0, y_out, radius * s0)
        p_t1 = (radius * c1, y_out, radius * s1)
        p_r0 = (r_hub * c0, y_dish, r_hub * s0)
        p_r1 = (r_hub * c1, y_dish, r_hub * s1)
        p_c0 = (0.0, y_dish + sgn * 0.4, 0.0)

        # Outer sidewall & rim face
        if is_left:
            pb.add_quad(p_r0, p_r1, p_t1, p_t0, "wheel")
            pb.add_tri(p_c0, p_r1, p_r0, "wheel")
        else:
            pb.add_quad(p_t0, p_t1, p_r1, p_r0, "wheel")
            pb.add_tri(p_c0, p_r0, p_r1, "wheel")

        # Outer tire tread
        p_ti0 = (radius * c0, y_in, radius * s0)
        p_ti1 = (radius * c1, y_in, radius * s1)
        if is_left:
            pb.add_quad(p_t0, p_ti0, p_ti1, p_t1, "trim")
        else:
            pb.add_quad(p_ti0, p_t0, p_t1, p_ti1, "trim")

        # Inner sidewall & back
        p_in_c = (0.0, y_in, 0.0)
        if is_left:
            pb.add_tri(p_in_c, p_ti0, p_ti1, "trim")
        else:
            pb.add_tri(p_in_c, p_ti1, p_ti0, "trim")

    return pb.to_dict()


def build_promaster_van():
    """Builds complete Ram ProMaster High-Roof Cargo Van with walk-in interior."""
    sp = vs.get_spec("van")
    x0, x1, hw = sp["x0"], sp["x1"], sp["hw"]
    z0, z_bmp, zb, z1 = sp["z_bot"], sp["z_bmp"], sp["z_belt"], sp["z_roof"]
    zn_top, zr_top = sp["z_nose_top"], sp["z_rear_top"]
    x_cowl = sp["x_cowl"] # 48.0
    x_tail = -106.0
    x_nose = 100.0

    chassis = MeshPart("chassis", sp)
    hood = MeshPart("hood", sp)
    door_l = MeshPart("door_l", sp)
    door_r = MeshPart("door_r", sp)
    extra = MeshPart("extra_part", sp)
    bumper_f = MeshPart("bumper_f", sp)
    bumper_r = MeshPart("bumper_r", sp)
    detail = MeshPart("detail_vib", sp)

    # ------------------------------------------------------------------
    # 1. FRONT BUMPER & NOSE FASCIA (frame 010)
    # Multi-piece black commercial bumper with lower intake & fog pods
    bumper_f.add_box(x_nose - 2.0, -hw * 0.98, z0, x1, hw * 0.98, z_bmp + 2.0, "front")
    # Lower radiator cooling intake scoop
    bumper_f.add_box(x1 - 1.5, -hw * 0.44, z0 + 3.0, x1 + 0.6, hw * 0.44, z_bmp - 2.0, "trim")
    # Outer fog light / tow hook pods
    for sy in (-1.0, 1.0):
        bumper_f.add_box(x1 - 2.5, sy * hw * 0.60, z0 + 3.0, x1 + 0.4, sy * hw * 0.88, z_bmp - 1.5, "trim")

    # Front commercial grille & swept headlights
    chassis.add_box(x_nose - 5.0, -hw * 0.62, z_bmp + 2.0, x_nose - 0.5, hw * 0.62, zn_top - 1.0, "front")
    # Swept modern headlight housings extending back into fenders
    for sy in (-1.0, 1.0):
        chassis.add_box(x_nose - 8.0, sy * hw * 0.62, z_bmp + 2.0, x_nose - 1.0, sy * hw * 0.96, zn_top + 1.0, "front")

    # Snub nose hood (short steep slope x: 48 .. 94, z: 48 .. 38.5)
    hood_grid = []
    nx_h, ny_h = 4, 5
    for i in range(nx_h):
        tx = i / (nx_h - 1)
        xh = x_cowl + (x_nose - 3.0 - x_cowl) * tx
        zh = 47.5 + (zn_top - 47.5) * (tx ** 0.9)
        row = []
        for j in range(ny_h):
            ty = -1.0 + 2.0 * j / (ny_h - 1)
            yh = hw * 0.82 * (1.0 - 0.08 * tx) * ty
            crown = (1.0 - ty * ty) * 1.8
            row.append((xh, yh, zh + crown))
        hood_grid.append(row)
    hood.add_thick_panel(hood_grid, (0.0, 0.0, -1.4), outer_region="top", inner_region="trim")

    # Cowl intake ventilation grille & dual wipers
    chassis.add_box(x_cowl - 3.0, -hw * 0.76, 46.5, x_cowl + 1.0, hw * 0.76, 48.5, "trim")
    for wx_pos in (-14.0, 14.0):
        detail.add_cylinder((x_cowl + 0.5, wx_pos, 48.2), (x_cowl - 14.0, wx_pos + 12.0, 56.0), 0.55, 0.55, segs=6, region="trim")
        detail.add_box(x_cowl - 14.5, wx_pos + 10.0, 55.5, x_cowl - 13.5, wx_pos + 26.0, 56.5, "trim")

    # ------------------------------------------------------------------
    # 2. CAB GREENHOUSE & DOORS (x: 12 .. 48)
    # Windshield A-pillars & safety glass (x: 22 .. 48, z: 48 .. 68)
    chassis.add_framed_window(
        (48.0, hw * 0.84, 48.0), (48.0, -hw * 0.84, 48.0),
        (22.0, -hw * 0.76, 68.0), (22.0, hw * 0.76, 68.0),
        w_bot=2.0, w_right=3.5, w_top=2.4, w_left=3.5, recess=0.85,
        bot_reg="top", right_reg="side", top_reg="top", left_reg="side",
    )

    # Cab door lower outer bodies & windows (door_l, door_r)
    for d_pb, sy in ((door_l, 1.0), (door_r, -1.0)):
        # Lower door outer skin
        d_pb.add_box(12.0, sy * (hw * 0.90), z_bmp + 2.0, 46.0, sy * (hw * 0.96), zb, "side")
        # Lower black cladding strip
        d_pb.add_box(12.0, sy * (hw * 0.90), z0, 46.0, sy * (hw * 0.96), z_bmp + 2.0, "side")
        # Vertical black commercial handle
        d_pb.add_box(18.0, sy * (hw * 0.96 + 0.5), zb - 4.0, 22.0, sy * (hw * 0.96 + 1.8), zb + 4.0, "trim")
        # Framed cab upper window
        d_pb.add_framed_window(
            (46.0, sy * hw * 0.88, zb), (12.0, sy * hw * 0.92, zb),
            (12.0, sy * hw * 0.82, 68.0), (22.0, sy * hw * 0.78, 68.0),
            w_bot=1.6, w_right=3.0, w_top=2.2, w_left=2.8, recess=0.80,
            bot_reg="side", right_reg="side", top_reg="top", left_reg="side", double_sided_frame=True,
        )
        # Commercial dual-lens wing mirror (frame 010, 015)
        d_pb.add_box(42.0, sy * (hw * 0.90), zb + 4.0, 45.0, sy * (hw * 0.90 + 7.5), zb + 5.5, "trim")
        d_pb.add_box(41.0, sy * (hw * 0.90 + 6.0), zb + 1.0, 46.0, sy * (hw * 0.90 + 13.5), zb + 14.5, "trim",
                     {("-y" if sy > 0 else "+y"): "glass"})

    # ------------------------------------------------------------------
    # 3. HIGH-ROOF EXPEDITION BODY (x: -106 .. 22)
    # Stepped aerodynamic roof over cab (x: 10 .. 22, z: 68 .. 89.5)
    chassis.add_box(10.0, -hw * 0.80, 68.0, 22.0, hw * 0.80, 89.5, "top")

    # Main high-roof crown skin (x: -106 .. 10, y: -36 .. 36, z: 87 .. 89.5)
    n_strips = 6
    yr_w = 36.0
    for j in range(n_strips):
        ya = -yr_w + 2.0 * yr_w * j / n_strips
        yb = -yr_w + 2.0 * yr_w * (j + 1) / n_strips
        za = 87.0 + (1.0 - (ya / yr_w) ** 2) * 2.5
        zb_r = 87.0 + (1.0 - (yb / yr_w) ** 2) * 2.5
        chassis.add_quad((-106.0, ya, za), (10.0, ya, za), (10.0, yb, zb_r), (-106.0, yb, zb_r), "top")
    # Roof drip rails / gutters
    for sy in (-1.0, 1.0):
        chassis.add_box(-106.0, sy * yr_w - 0.8, 86.2, 10.0, sy * (yr_w + 1.0), 87.6, "trim")

    # Outer cargo side body panels (x: -106 .. 12)
    # Upper sheet metal
    chassis.add_quad((12.0, hw * 0.92, zb), (-106.0, hw * 0.92, zb), (-106.0, yr_w, 87.0), (12.0, yr_w, 87.0), "side")
    chassis.add_quad((-106.0, -hw * 0.92, zb), (12.0, -hw * 0.92, zb), (12.0, -yr_w, 87.0), (-106.0, -yr_w, 87.0), "side")
    # Mid sheet metal
    chassis.add_quad((12.0, hw * 0.94, z_bmp + 2.0), (-106.0, hw * 0.94, z_bmp + 2.0),
                     (-106.0, hw * 0.92, zb), (12.0, hw * 0.92, zb), "side")
    chassis.add_quad((-106.0, -hw * 0.94, z_bmp + 2.0), (12.0, -hw * 0.94, z_bmp + 2.0),
                     (12.0, -hw * 0.92, zb), (-106.0, -hw * 0.92, zb), "side")
    # Lower black protective cladding
    chassis.add_box(-106.0, hw * 0.92, z0, 12.0, hw * 0.95, z_bmp + 2.0, "side")
    chassis.add_box(-106.0, -hw * 0.95, z0, 12.0, -hw * 0.92, z_bmp + 2.0, "side")

    # Passenger side sliding door rail & vertical handle (frame 005)
    detail.add_box(-48.0, -hw * 0.96, zb + 1.5, 8.0, -hw * 0.93, zb + 3.5, "chrome")
    detail.add_box(3.0, -hw * 0.98, zb - 4.0, 7.0, -hw * 0.94, zb + 4.0, "trim")

    # Wheel arches & flared lips
    for wx in (sp["wheel_x_f"], sp["wheel_x_r"]):
        for sy in (-1.0, 1.0):
            chassis.add_box(wx - 19.0, sy * (hw * 0.92), z0, wx + 19.0, sy * (hw * 0.97), z0 + 17.5, "trim")

    # ------------------------------------------------------------------
    # 4. REAR FASCIA, STEP BUMPER & WALK-IN ENTRANCE (frame 001, 020)
    # Rear D-pillar taillight columns
    for sy in (-1.0, 1.0):
        chassis.add_box(-106.5, sy * 26.0, z_bmp + 2.0, -105.0, sy * (hw * 0.94), 86.5, "rear")
    # Top header arch with center 3rd brake light
    chassis.add_box(-106.5, -26.0, 82.0, -105.0, 26.0, 87.5, "rear")
    detail.add_box(-107.0, -5.5, 84.0, -106.0, 5.5, 86.2, "trim")

    # Black rear commercial step bumper (recessed center step at z=13.5!)
    # Outer bumper wings
    for sy in (-1.0, 1.0):
        bumper_r.add_box(-112.5, sy * 24.0, z0, -105.0, sy * (hw * 0.96), z_bmp + 2.0, "rear")
    # Low central step for smooth walk-in entry!
    bumper_r.add_box(-113.5, -24.0, z0, -105.0, 24.0, 13.5, "trim")
    bumper_r.add_box(-106.0, -26.0, 13.5, -105.0, 26.0, 18.0, "trim")

    # ------------------------------------------------------------------
    # 5. SWUNG-OPEN 50/50 REAR BARN DOORS (in extra_part, frame 001, 020)
    # Doorway between y=-26 and +26 is 100% open and walk-in accessible!
    # Left rear barn door: swung open outward ~100 degrees
    # Outer white face (+Y) and inner stamped door card (-Y)
    extra.add_box(-128.0, 29.5, 19.5, -106.0, 32.0, 81.5, "rear",
                  {"+y": "rear", "-y": "int_wall", "+x": "trim", "-x": "trim"})
    # Heavy-duty exterior hinges
    for hz in (28.0, 72.0):
        extra.add_cylinder((-106.0, 28.0, hz - 2.5), (-106.0, 28.0, hz + 2.5), 1.2, 1.2, segs=8, region="trim")
        extra.add_box(-108.0, 27.0, hz - 1.5, -105.0, 30.5, hz + 1.5, "trim")

    # Right rear barn door: swung open outward ~100 degrees
    # Outer white face (-Y) with license plate bracket & inner stamped door card (+Y) with latch handle
    extra.add_box(-128.0, -32.0, 19.5, -106.0, -29.5, 81.5, "rear",
                  {"-y": "rear", "+y": "int_wall", "+x": "trim", "-x": "trim"})
    for hz in (28.0, 72.0):
        extra.add_cylinder((-106.0, -28.0, hz - 2.5), (-106.0, -28.0, hz + 2.5), 1.2, 1.2, segs=8, region="trim")
        extra.add_box(-108.0, -30.5, hz - 1.5, -105.0, -27.0, hz + 1.5, "trim")
    # Interior release latch handle on right door (frame 001, 020)
    extra.add_box(-118.0, -29.0, 46.0, -114.0, -27.8, 51.0, "trim")

    # ------------------------------------------------------------------
    # 6. WALK-IN INTERIOR CARGO BAY (frame 001, 020)
    # Cargo floor deck (x: -105 .. 10, y: -35 .. 35, z=18.0)
    chassis.add_quad((-105.0, -34.5, 18.0), (10.0, -34.5, 18.0), (10.0, 34.5, 18.0), (-105.0, 34.5, 18.0), "int_floor")
    # Floor undercarriage base
    chassis.add_quad((-105.0, 34.5, z0 + 1.0), (10.0, 34.5, z0 + 1.0),
                     (10.0, -34.5, z0 + 1.0), (-105.0, -34.5, z0 + 1.0), "bottom")

    # Inward-facing stamped interior cargo walls (no backface culling!)
    # Left inner wall (y = 34.0, facing -Y into cargo bay)
    chassis.add_quad((10.0, 34.0, 18.0), (-105.0, 34.0, 18.0), (-105.0, 34.0, 84.0), (10.0, 34.0, 84.0), "int_wall")
    # Right inner wall (y = -34.0, facing +Y into cargo bay)
    chassis.add_quad((-105.0, -34.0, 18.0), (10.0, -34.0, 18.0), (10.0, -34.0, 84.0), (-105.0, -34.0, 84.0), "int_wall")

    # Ribbed inner wheel well tubs (arches) on floor
    for sy in (-1.0, 1.0):
        y_w0 = sy * 25.0
        y_w1 = sy * 34.2
        chassis.add_box(-72.0, min(y_w0, y_w1), 18.0, -44.0, max(y_w0, y_w1), 32.5, "int_wall")

    # Inward-facing ceiling & structural roof cross-bows
    chassis.add_quad((-105.0, 34.0, 84.5), (10.0, 34.0, 84.5), (10.0, -34.0, 84.5), (-105.0, -34.0, 84.5), "interior")
    for rx in (-85.0, -60.0, -35.0, -10.0):
        chassis.add_box(rx - 1.5, -34.0, 83.5, rx + 1.5, 34.0, 85.0, "trim")
    # Dual cargo dome lights
    for lx in (-75.0, -25.0):
        detail.add_box(lx - 3.5, -4.5, 83.5, lx + 3.5, 4.5, 84.5, "glass")

    # ------------------------------------------------------------------
    # 7. CAB SAFETY BULKHEAD PARTITION & CENTRAL WALKTHROUGH AISLE (frame 020)
    # Bulkhead at x = 10.0:
    # Left partition behind driver (y: 10 .. 34)
    chassis.add_box(9.0, 10.0, 18.0, 10.5, 34.0, 44.0, "int_wall")
    chassis.add_box(9.5, 10.0, 44.0, 10.5, 34.0, 74.0, "trim", {"+x": "glass", "-x": "glass"})
    # Right partition behind passenger (y: -34 .. -10)
    chassis.add_box(9.0, -34.0, 18.0, 10.5, -10.0, 44.0, "int_wall")
    chassis.add_box(9.5, -34.0, 44.0, 10.5, -10.0, 74.0, "trim", {"+x": "glass", "-x": "glass"})
    # Central Walkthrough Aisle between y=-10 and +10 is COMPLETELY OPEN for walk-in access into the cab!

    # ------------------------------------------------------------------
    # 8. FRONT COCKPIT / CAB INTERIOR (frame 010, 020)
    # Cockpit floor continuing at z=18.0
    chassis.add_quad((10.0, -34.0, 18.0), (48.0, -34.0, 18.0), (48.0, 34.0, 18.0), (10.0, 34.0, 18.0), "interior")

    # High-Back Driver Bucket Seat (y: 12 .. 28, frame 010, 020)
    # Seat pedestal
    chassis.add_box(20.0, 12.0, 18.0, 34.0, 28.0, 22.0, "trim")
    # Ergonomic seat cushion
    chassis.add_box(20.0, 12.0, 22.0, 34.0, 28.0, 26.5, "int_seat")
    # High-back contoured backrest
    chassis.add_box(18.0, 12.0, 26.5, 21.5, 28.0, 48.0, "int_seat")
    # Integrated headrest
    chassis.add_box(17.5, 16.0, 48.0, 21.0, 24.0, 55.0, "int_seat")

    # High-Back Passenger Bucket Seat (y: -28 .. -12)
    chassis.add_box(20.0, -28.0, 18.0, 34.0, -12.0, 22.0, "trim")
    chassis.add_box(20.0, -28.0, 22.0, 34.0, -12.0, 26.5, "int_seat")
    chassis.add_box(18.0, -28.0, 26.5, 21.5, -12.0, 48.0, "int_seat")
    chassis.add_box(17.5, -24.0, 48.0, 21.0, -16.0, 55.0, "int_seat")

    # Center Console / Transmission Doghouse Cowl between seats (y: -8 .. 8)
    chassis.add_box(18.0, -8.0, 18.0, 42.0, 8.0, 27.0, "trim")
    # Molded dual cup holders
    for cy in (-4.0, 4.0):
        detail.add_cylinder((30.0, cy, 27.1), (30.0, cy, 25.5), 2.2, 2.0, segs=8, region="trim")

    # Full Dashboard Console (x: 42 .. 52, y: -34 .. 34, z: 27 .. 45)
    chassis.add_box(42.0, -34.0, 27.0, 52.0, 34.0, 43.0, "int_dash")
    # Instrument cluster binnacle in front of driver (y: 11 .. 27)
    chassis.add_box(40.0, 11.0, 34.0, 50.0, 27.0, 45.0, "int_dash")
    # Passenger glove box & recessed tray (y: -34 .. -10)
    chassis.add_box(42.5, -32.0, 29.0, 51.5, -12.0, 36.0, "int_dash")

    # Steering Column & 3D Steering Wheel (in front of driver seat)
    detail.add_cylinder((46.0, 20.0, 33.0), (36.0, 20.0, 39.5), 1.6, 1.4, segs=8, region="trim")
    # Turn signal / wiper control stalk
    detail.add_cylinder((38.0, 20.0, 38.0), (37.5, 25.5, 39.5), 0.5, 0.4, segs=6, region="trim")
    # 3D Steering wheel rim (angled toward driver)
    center_sw = Vector((35.0, 20.0, 40.0))
    sw_radius = 5.2
    sw_segs = 14
    # Plane normal ~ Vector((1, 0, 0.65)).normalized()
    n_sw = Vector((0.85, 0.0, 0.52)).normalized()
    u_sw = Vector((0.0, 1.0, 0.0))
    v_sw = n_sw.cross(u_sw).normalized()
    pts_rim = []
    for k in range(sw_segs):
        ang = 2.0 * math.pi * k / sw_segs
        p_pt = center_sw + (u_sw * math.cos(ang) + v_sw * math.sin(ang)) * sw_radius
        pts_rim.append(p_pt)
    for k in range(sw_segs):
        k_next = (k + 1) % sw_segs
        detail.add_cylinder(pts_rim[k], pts_rim[k_next], 0.65, 0.65, segs=6, region="trim", cap=False)
    # 3 spokes and horn hub
    detail.add_cylinder(center_sw - n_sw * 0.4, center_sw + n_sw * 0.4, 1.8, 1.8, segs=8, region="trim")
    for ang in (0.0, 2.2, 4.1):
        sp_end = center_sw + (u_sw * math.cos(ang) + v_sw * math.sin(ang)) * (sw_radius - 0.5)
        detail.add_cylinder(center_sw, sp_end, 0.6, 0.5, segs=6, region="trim")

    # Driver foot pedals on firewall floorboard
    detail.add_box(48.0, 21.0, 19.0, 50.0, 23.5, 24.0, "trim") # accelerator
    detail.add_box(48.0, 15.5, 20.0, 50.0, 19.5, 25.0, "trim") # brake

    # Overhead sun visors & rearview mirror
    for vy in (-18.0, 18.0):
        detail.add_box(24.0, vy - 7.0, 66.5, 28.0, vy + 7.0, 67.5, "trim")
    detail.add_box(24.0, -3.5, 63.5, 25.5, 3.5, 66.0, "trim", {"-x": "glass"})

    # ------------------------------------------------------------------
    # 9. SCULPTED 3D 8-LUG COMMERCIAL WHEELS (4 wheels)
    w_rad = sp["wheel_r"]  # 15.0
    w_wid = sp["wheel_w"]  # 9.5
    wheel_fl = build_3d_wheel(w_rad, w_wid, sp["dish"], sp["rim_ratio"], is_left=True, sp=sp)
    wheel_fr = build_3d_wheel(w_rad, w_wid, sp["dish"], sp["rim_ratio"], is_left=False, sp=sp)
    wheel_rl = build_3d_wheel(w_rad, w_wid, sp["dish"], sp["rim_ratio"], is_left=True, sp=sp)
    wheel_rr = build_3d_wheel(w_rad, w_wid, sp["dish"], sp["rim_ratio"], is_left=False, sp=sp)

    parts_dict = {
        "chassis": chassis.to_dict(),
        "hood": hood.to_dict(),
        "door_l": door_l.to_dict(),
        "door_r": door_r.to_dict(),
        "extra_part": extra.to_dict(),
        "bumper_f": bumper_f.to_dict(),
        "bumper_r": bumper_r.to_dict(),
        "detail_vib": detail.to_dict(),
        "wheel_fl": wheel_fl,
        "wheel_fr": wheel_fr,
        "wheel_rl": wheel_rl,
        "wheel_rr": wheel_rr,
    }

    # Add shrapnel shards for explosion physics
    shrap_parts = {}
    for i in range(1, 5):
        sp_sh = MeshPart(f"shrap_{i}", sp)
        sz = 4.0 + i * 1.5
        sp_sh.add_box(-sz, -sz, -sz, sz, sz, sz, "trim")
        shrap_parts[f"shrap_{i}"] = sp_sh.to_dict()
    parts_dict.update(shrap_parts)

    return dict(kind="van", parts=parts_dict)


def main():
    print("Building Accurate Ram ProMaster High-Roof Cargo Van...")
    veh_data = build_promaster_van()
    out_json = os.path.join(HERE, "out", "promaster_van_parts.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(veh_data, f)
    total_verts = sum(len(p["verts"]) for p in veh_data["parts"].values())
    total_tris = sum(len(p["tris"]) for p in veh_data["parts"].values())
    print(f"Generated {out_json}: {total_verts} verts, {total_tris} tris across {len(veh_data['parts'])} parts.")


if __name__ == "__main__":
    main()
