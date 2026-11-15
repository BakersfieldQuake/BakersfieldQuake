"""blender_build_tuktuk.py — Run headless in Blender 5.2 to sculpt the 3D Bangkok Tuk-Tuk!

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python source/mm_tools/blender_build_tuktuk.py
"""
from __future__ import annotations

import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import veh_specs as vs
import blender_build_vehicles as bbv

OUT_JSON = r"C:\Users\qxdc\.gemini\antigravity\brain\2e8d87c6-94bd-47b0-991f-695f3579ece4\scratch\tuktuk_geom.json"

# Tuk-Tuk 1024x1024 custom swatches placed cleanly inside unused bottom-left (0..512, 800..1024)
# so RECT_CHROME (800..1024, 544..670), RECT_TRIM (800..1024, 672..800), & RECT_WRECK stay 100% pure!
TT_RECTS = {
    "blue_body":   (16, 812, 168, 904),
    "stripe_seat": (176, 812, 336, 904),
    "canopy_dark": (344, 812, 496, 904),
    "roof_glow":   (16, 916, 168, 1012),
    "wire_mesh":   (176, 916, 336, 1012),
    "battery_box": (344, 916, 496, 1012),
}

TUKTUK_SPEC = {
    "x0": -56.0,
    "x1": 58.0,
    "hw": 28.0,
    "z_bot": 8.0,
    "z_sill": 18.0,
    "z_nose_top": 42.5,
    "z_rear_top": 43.0,
    "z_roof": 72.5,
    "wheel_r": 11.8,
    "wheel_w": 5.8,
    "dish": 3.0,
    "rim_ratio": 0.56,
    "wheel_x_f": 43.0,
    "wheel_x_r": -34.0,
    "wheel_y_r": 24.5,
}


class TukTukPartBuilder(bbv.PartBuilder):
    """Extends PartBuilder with dedicated Bangkok Tuk-Tuk material swatches & curved surfaces."""

    def _assign_uv(self, face, region):
        if region in TT_RECTS:
            rect = TT_RECTS[region]
            ls = list(face.loops)
            uv_coords = [(0.05, 0.05), (0.95, 0.05), (0.95, 0.95), (0.05, 0.95)]
            if region == "stripe_seat":
                # Keep red/white stripes parallel to U so stripes run cleanly up/down cushions!
                uv_coords = [(0.04, 0.08), (0.96, 0.08), (0.96, 0.92), (0.04, 0.92)]
            for idx, l in enumerate(ls):
                su, sv = uv_coords[idx % len(uv_coords)]
                l[self.uv_layer].uv = vs.rect_uv(rect, su, sv)
            return
        super()._assign_uv(face, region)

    def add_grid_strip(self, row_a, row_b, region="auto", flip=False):
        n = min(len(row_a), len(row_b))
        for i in range(n - 1):
            self.add_quad(row_a[i], row_a[i + 1], row_b[i + 1], row_b[i], region, flip=flip)

    def add_curved_arch(self, cx, cz, r_in, r_out, y_in, y_out, th0, th1, segs=12, region="side", is_left=True):
        """Extruded wheel arch flare around a rear wheel."""
        s = 1.0 if is_left else -1.0
        for i in range(segs):
            a0 = th0 + (th1 - th0) * (i / segs)
            a1 = th0 + (th1 - th0) * ((i + 1) / segs)
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            pi0 = (cx + c0 * r_in, y_in * s, cz + s0 * r_in)
            pi1 = (cx + c1 * r_in, y_in * s, cz + s1 * r_in)
            po0 = (cx + c0 * r_out, y_out * s, cz + s0 * r_out)
            po1 = (cx + c1 * r_out, y_out * s, cz + s1 * r_out)
            pi0b = (cx + c0 * r_in, y_out * s, cz + s0 * r_in)
            pi1b = (cx + c1 * r_in, y_out * s, cz + s1 * r_in)
            flip = not is_left
            self.add_quad(pi0, po0, po1, pi1, region, flip=flip)
            self.add_quad(po0, pi0b, pi1b, po1, "trim", flip=flip)
            self.add_quad(pi0b, pi0, pi1, pi1b, "trim", flip=flip)


def _nose_y(x, z):
    """Tapered teardrop half-width for the iconic Thai Tuk-Tuk front cowl."""
    # From cockpit doorway (x=28, hw=22) tapering smoothly forward to nose tip (x=47, hw=9.5)
    t = max(0.0, min(1.0, (x - 27.0) / 21.0))
    tz = max(0.0, min(1.0, (z - 15.0) / 27.5))
    return (23.0 - 12.0 * (t ** 1.25)) * (1.0 - 0.14 * tz)


def _add_round_lamp(pb, cx, cy, cz, radius, depth, region_body="chrome", region_lens="ember", segs=16):
    """3D chrome torpedo/headlight housing pointing +X with recessed emissive lens."""
    rings = []
    # 4 longitudinal rings from back mount -> bulge -> rim -> recessed lens
    profile = [
        (cx - depth, radius * 0.42),
        (cx - depth * 0.45, radius * 0.96),
        (cx, radius),
        (cx + 0.65, radius * 0.88),
    ]
    for px, r in profile:
        pts = []
        for i in range(segs):
            th = 2.0 * math.pi * i / segs
            pts.append((px, cy + math.cos(th) * r, cz + math.sin(th) * r))
        rings.append(pts)
    for k in range(len(rings) - 1):
        for i in range(segs):
            j = (i + 1) % segs
            pb.add_quad(rings[k][i], rings[k + 1][i], rings[k + 1][j], rings[k][j], region_body)
    # Recessed bright glowing lens face + center cap
    rim = rings[-1]
    c_lens = (cx + 0.95, cy, cz)
    for i in range(segs):
        j = (i + 1) % segs
        pb.add_tri(c_lens, rim[j], rim[i], region_lens)
    # Back cap
    back = rings[0]
    c_back = (cx - depth - 0.5, cy, cz)
    for i in range(segs):
        j = (i + 1) % segs
        pb.add_tri(c_back, back[i], back[j], region_body)


def build_tuktuk() -> dict:
    sp = dict(TUKTUK_SPEC)
    rng = random.Random(2026)

    # Clear active Blender scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # ==================================================================
    # 1. CHASSIS (floor pan, blue diamond-plate steps, battery box, seats,
    #             rear body skirts, wheel arches, mudflaps, A/B/C pillars)
    # ==================================================================
    ch = TukTukPartBuilder("chassis", sp)

    # 1a. Lower steel chassis frame & blue diamond-plate side step boards
    ch.add_box(-48.0, -20.5, 9.2, 34.0, 20.5, 11.4, "blue_body")
    # Extended left & right diamond-plate boarding steps (between cowl & rear wheels!)
    for sgn in (1.0, -1.0):
        y_a = 19.5 * sgn
        y_b = 26.8 * sgn
        ch.add_box(-21.0, min(y_a, y_b), 8.2, 23.0, max(y_a, y_b), 10.6, "blue_body")
        # Chrome rub-strip trim along outer step lip
        ch.add_box(-21.0, (26.2 if sgn > 0 else -27.2), 8.4, 23.0, (27.2 if sgn > 0 else -26.2), 9.6, "chrome")
        # Front rubber mud-guard skirt under forward step edge
        ch.add_box(19.0, min(y_a, y_b), 5.8, 25.0, max(y_a, y_b), 8.5, "trim")

    # 1b. Sculpted lower front cowl apron (bottom skirt x=25..46, z=14..29)
    z_skirt = [14.0, 19.5, 25.5, 30.0]
    x_skirt = [26.0, 35.0, 42.5, 47.0]
    for sgn in (1.0, -1.0):
        grid = []
        for xi in x_skirt:
            col = []
            for zi in z_skirt:
                # nose bows slightly further out at bumper height z=21..26
                x_fwd = xi + (1.6 if (zi > 18.0 and zi < 27.0 and xi > 40.0) else 0.0)
                col.append((x_fwd, _nose_y(xi, zi) * sgn, zi))
            grid.append(col)
        flip = (sgn > 0)
        for i in range(len(grid) - 1):
            for j in range(len(grid[0]) - 1):
                ch.add_quad(grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1], "side", flip=flip)
    # Front central vertical lower panel bridging left & right cowl skirts (above front wheel)
    z_f = [19.0, 24.5, 29.5]
    for k in range(len(z_f) - 1):
        ya0 = _nose_y(47.0, z_f[k])
        ya1 = _nose_y(47.0, z_f[k + 1])
        ch.add_quad((47.5, -ya0, z_f[k]), (47.5, ya0, z_f[k]), (46.8, ya1, z_f[k + 1]), (46.8, -ya1, z_f[k + 1]), "front")

    # 1c. Exposed Left-Side Silver Battery Box (signature detail from photo!)
    ch.add_box(-13.5, 20.5, 10.6, -2.5, 26.6, 17.8, "battery_box")
    ch.add_box(-13.8, 20.2, 16.4, -2.2, 26.8, 17.8, "trim")  # dark lid lip
    ch.add_cylinder((-5.0, 23.5, 17.8), (-5.0, 23.5, 19.0), 0.75, 0.75, 8, "ember")   # red + terminal
    ch.add_cylinder((-11.0, 23.5, 17.8), (-11.0, 23.5, 19.0), 0.75, 0.75, 8, "trim")   # black - terminal
    # Plastic water bottle holder detail near left step (fun subtle nod to photo!)
    ch.add_cylinder((-0.5, 23.2, 17.6), (-0.5, 23.2, 23.0), 1.35, 1.35, 10, "glass")

    # 1d. Driver Compartment: Red & White Striped Bench + Pedestal + Footwell
    # Engine / seat plinth
    ch.add_box(2.0, -13.0, 11.0, 21.5, 13.0, 20.2, "trim")
    # Horizontal cushion (red & white stripes)
    ch.add_box(3.5, -12.8, 20.2, 20.0, 12.8, 23.8, "stripe_seat")
    # Slanted driver backrest with royal blue side piping
    ch.add_box(2.0, -12.4, 23.5, 6.2, 12.4, 42.5, "stripe_seat")
    ch.add_box(1.5, -13.0, 23.5, 6.6, -12.0, 42.6, "blue_body")
    ch.add_box(1.5, 12.0, 23.5, 6.6, 13.0, 42.6, "blue_body")

    # Wire-mesh divider screen behind driver head (classic Thai Tuk-Tuk cage!)
    ch.add_box(2.8, -11.5, 42.5, 4.2, 11.5, 57.5, "wire_mesh")
    # Chrome frame around wire-mesh divider
    ch.add_cylinder((3.5, -11.5, 42.5), (3.5, -11.5, 58.0), 0.65, 0.65, 8, "chrome")
    ch.add_cylinder((3.5, 11.5, 42.5), (3.5, 11.5, 58.0), 0.65, 0.65, 8, "chrome")
    ch.add_cylinder((3.5, -11.5, 58.0), (3.5, 11.5, 58.0), 0.65, 0.65, 8, "chrome")

    # 1e. Rear Passenger Cabin Body Panels, Curved Fender Arches, Mudflaps & Bench
    # Rear floor tub & lower skirts (step up over rear axle)
    ch.add_box(-49.0, -25.0, 11.2, -16.0, 25.0, 22.0, "blue_body")
    # Rear panel wrap (y=-25..+25, x=-50..-46, z=14..42) -> mapped via RECT_REAR!
    ch.add_quad((-50.2, -25.0, 13.0), (-50.2, 25.0, 13.0), (-49.2, 25.0, 39.0), (-49.2, -25.0, 39.0), "rear", flip=True)
    # Rear luggage tray / engine hatch lip
    ch.add_box(-50.0, -24.5, 13.0, -45.5, 24.5, 22.5, "blue_body")

    # Rear Red & White Striped Passenger Bench (thick angled seat cushion & backrest!)
    ch.add_box(-37.0, -22.8, 21.8, -17.0, 22.8, 26.8, "stripe_seat")
    ch.add_box(-46.5, -23.0, 25.5, -36.5, 23.0, 44.5, "stripe_seat")
    # Royal blue side armrest bolsters flanking passenger bench
    for sgn in (1.0, -1.0):
        yb0, yb1 = sorted((19.5 * sgn, 26.2 * sgn))
        # Side skirt ahead of rear wheel (x=-22..-15) and behind rear wheel (x=-49..-44)
        ch.add_box(-22.0, yb0, 11.2, -13.0, yb1, 29.5, "side")
        ch.add_box(-49.2, yb0, 13.0, -43.5, yb1, 36.5, "side")
        # Armrest body panel over rear wheel arch (z=26..34)
        ch.add_box(-48.5, yb0, 26.5, -17.5, yb1, 33.8, "side")
        # Flared curved wheel arch lip around (-34, ±24.5, 12.0)
        ch.add_curved_arch(-34.0, 12.0, 14.2, 16.8, 22.5, 27.8, math.radians(15), math.radians(165), segs=12, region="blue_body", is_left=(sgn > 0))
        # Dark rubber rear mudflap hanging behind rear wheel
        ym0, ym1 = sorted((20.5 * sgn, 27.2 * sgn))
        ch.add_box(-48.8, ym0, 4.5, -47.4, ym1, 16.0, "trim")

    # Dual Red/Amber Tail Lights + Glowing Rear Brake Pods + Chrome Bangkok Taxi Plate
    for sgn in (1.0, -1.0):
        ch.add_box(-51.2, 17.5 * sgn - 3.2, 22.5, -49.5, 17.5 * sgn + 3.2, 26.5, "chrome")
        ch.add_box(-51.6, 17.5 * sgn - 2.6, 23.0, -50.6, 17.5 * sgn + 2.6, 26.0, "ember")
    ch.add_box(-50.8, -6.5, 16.0, -49.6, 6.5, 21.8, "roof_glow")  # glowing yellow/amber Bangkok license plate

    # Chrome Vertical Roof Stanchions (B-pillars at x=+16, C-pillars at x=-46) & Crossbars
    for sgn in (1.0, -1.0):
        # Slanted front A-pillar post supporting windshield frame
        ch.add_cylinder((29.5, 20.2 * sgn, 41.5), (17.5, 20.5 * sgn, 62.5), 1.15, 1.05, 8, "red" if False else "blue_body")
        # Mid vertical chrome canopy support pole right behind side step
        ch.add_cylinder((-14.5, 24.5 * sgn, 29.0), (-14.5, 22.8 * sgn, 63.2), 0.95, 0.95, 10, "chrome")
        # Rear corner chrome support pole
        ch.add_cylinder((-47.5, 24.2 * sgn, 32.0), (-47.0, 22.8 * sgn, 62.5), 0.95, 0.95, 10, "chrome")

    chassis_dict = ch.export_dict(custom_origin=(0.0, 0.0, 0.0))

    # ==================================================================
    # 2. HOOD (Upper Royal-Blue Cowl Nose, Twin Torpedo Side Lamps,
    #          Big Center Chrome Headlight, Windshield & Cream Badge Plate)
    # ==================================================================
    hood = TukTukPartBuilder("hood", sp)
    # Sculpted curved upper cowl nose bridging z=29.5..43.0, x=28..47
    for sgn in (1.0, -1.0):
        y_top = _nose_y(44.5, 42.5)
        y_bot = _nose_y(46.8, 29.5)
        # Side upper cheeks
        hood.add_quad(
            (28.0, 21.5 * sgn, 29.5), (46.8, y_bot * sgn, 29.5),
            (43.5, y_top * sgn, 42.0), (29.5, 20.5 * sgn, 42.2),
            "side", flip=(sgn > 0),
        )
    # Front nose face (mapped to RECT_FRONT — carries crisp blue + red/white/yellow stripes!)
    hood.add_quad(
        (46.8, -_nose_y(46.8, 29.5), 29.5), (46.8, _nose_y(46.8, 29.5), 29.5),
        (43.8, _nose_y(43.8, 42.2), 42.2), (43.8, -_nose_y(43.8, 42.2), 42.2),
        "front",
    )
    # Dashboard top cap sloping back into windshield base
    hood.add_quad(
        (29.5, -20.5, 42.2), (43.8, -_nose_y(43.8, 42.2), 42.2),
        (43.8, _nose_y(43.8, 42.2), 42.2), (29.5, 20.5, 42.2),
        "blue_body",
    )
    # Cream/Beige Front Shield/Plate right under the windshield (distinctive in photo!)
    hood.add_quad((39.5, -8.5, 39.5), (39.5, 8.5, 39.5), (34.5, 8.2, 47.8), (34.5, -8.2, 47.8), "roof_glow")
    hood.add_quad((39.1, 8.5, 39.5), (39.1, -8.5, 39.5), (34.1, -8.2, 47.8), (34.1, 8.2, 47.8), "trim")

    # Big Center Chrome Headlight (mounted proud on front apron!)
    _add_round_lamp(hood, 47.6, 0.0, 32.5, radius=4.3, depth=5.5, region_body="chrome", region_lens="ember", segs=16)
    # Twin Chrome Torpedo / Bullet Marker Lamps on Left & Right Shoulders!
    for sgn in (1.0, -1.0):
        _add_round_lamp(hood, 44.2, 16.5 * sgn, 33.8, radius=2.3, depth=6.2, region_body="chrome", region_lens="ember", segs=12)
        # Outer wrap strut mount
        hood.add_cylinder((39.5, 16.0 * sgn, 33.8), (42.5, 16.5 * sgn, 33.8), 1.0, 1.0, 8, "chrome")

    # Iconic Sloped Windshield in Red-and-White Frame + Dual Side Mirrors!
    hood.add_framed_window(
        (33.8, -19.5, 42.0), (33.8, 19.5, 42.0),
        (19.0, 18.8, 63.0), (19.0, -18.8, 63.0),
        w_bot=2.4, w_right=2.8, w_top=2.6, w_left=2.8,
        recess=0.65,
        bot_reg="stripe_seat", right_reg="stripe_seat", top_reg="stripe_seat", left_reg="stripe_seat",
        double_sided_frame=True,
    )
    # Twin Rearview Mirrors hanging inside/beside top windshield corners
    for sgn in (1.0, -1.0):
        hood.add_cylinder((23.0, 13.5 * sgn, 60.5), (22.5, 13.5 * sgn, 58.0), 0.45, 0.45, 6, "chrome")
        hood.add_box(21.8, 13.5 * sgn - 2.0, 54.5, 23.0, 13.5 * sgn + 2.0, 58.2, "trim")
        # Outer side wing mirrors
        hood.add_cylinder((26.5, 19.0 * sgn, 52.0), (26.5, 25.0 * sgn, 53.5), 0.45, 0.45, 6, "chrome")
        hood.add_box(25.2, 24.5 * sgn - 1.5, 51.5, 27.2, 24.5 * sgn + 1.5, 56.5, "trim")

    hood_dict = hood.export_dict(hinge_pivot=(30.0, 0.0, 42.0))

    # ==================================================================
    # 3. DOOR_L & DOOR_R (Chrome Safety Grab Rails & Side Passenger Cages)
    # ==================================================================
    doors = {}
    for nm, sgn in (("door_l", 1.0), ("door_r", -1.0)):
        dp = TukTukPartBuilder(nm, sp)
        y_rail = 24.8 * sgn
        # Top armrest chrome bar & vertical cage bars along passenger bench
        dp.add_cylinder((-46.0, y_rail, 36.2), (-16.0, y_rail, 36.2), 0.78, 0.78, 8, "chrome")
        dp.add_cylinder((-46.0, y_rail, 31.8), (-16.0, y_rail, 31.8), 0.62, 0.62, 8, "chrome")
        for rx in (-43.0, -35.0, -27.0, -19.0):
            dp.add_cylinder((rx, y_rail, 31.5), (rx, y_rail, 36.5), 0.52, 0.52, 6, "chrome")
        # Diagonal grab handle by boarding step for passengers hopping in!
        dp.add_cylinder((-14.5, 23.8 * sgn, 36.2), (-14.5, 23.8 * sgn, 52.0), 0.72, 0.72, 8, "chrome")
        # Horizontal chrome safety bar across doorway shoulder
        dp.add_cylinder((-14.5, 23.6 * sgn, 49.5), (24.0, 21.2 * sgn, 49.5), 0.55, 0.55, 8, "chrome")
        doors[nm] = dp.export_dict()

    # ==================================================================
    # 4. EXTRA_PART (Curved Charcoal Canvas Roof Canopy + Yellow Roof Dome!)
    # ==================================================================
    roof = TukTukPartBuilder("extra_part", sp)
    # Multi-segment curved camber across X and Y like stretched canvas on hoops
    xs_r = [-49.5, -36.0, -20.0, -4.0, 10.0, 21.5]
    ys_r = [-24.5, -15.0, 0.0, 15.0, 24.5]
    grid_r = []
    for xi in xs_r:
        row = []
        tx = (xi - (-49.5)) / (21.5 - (-49.5))
        z_drop_fore = 1.6 * max(0.0, (tx - 0.72) / 0.28)
        for yi in ys_r:
            ny = yi / 24.5
            z_crown = 68.4 - 4.2 * (ny * ny) - z_drop_fore
            row.append((xi, yi, z_crown))
        grid_r.append(row)
    roof.add_thick_panel(grid_r, (0.0, 0.0, -1.6), outer_region="canopy_dark", inner_region="canopy_dark")
    # Scalloped canvas valance skirt wrapping around left/right/rear roof eaves
    for sgn in (1.0, -1.0):
        roof.add_box(-49.5, 23.4 * sgn, 60.8, 20.0, 24.9 * sgn, 64.5, "canopy_dark")
    roof.add_box(-50.0, -24.5, 60.8, -48.5, 24.5, 64.5, "canopy_dark")
    roof.add_box(19.0, -22.5, 61.5, 21.8, 22.5, 65.0, "canopy_dark")

    # Iconic Glowing Yellow/Amber Dome Taxi Sign on the Leading Roof Edge!
    roof.add_box(11.5, -8.5, 66.8, 19.5, 8.5, 68.2, "trim")  # black rubber mounting skirt
    roof.add_box(12.2, -7.8, 68.2, 18.8, 7.8, 72.2, "roof_glow")
    # Trapezoid cap bevel on top of roof dome
    roof.add_quad((12.2, -7.8, 72.2), (18.8, -7.8, 72.2), (17.8, -6.2, 73.5), (13.2, -6.2, 73.5), "roof_glow")
    roof.add_quad((18.8, 7.8, 72.2), (12.2, 7.8, 72.2), (13.2, 6.2, 73.5), (17.8, 6.2, 73.5), "roof_glow")
    roof.add_quad((13.2, -6.2, 73.5), (17.8, -6.2, 73.5), (17.8, 6.2, 73.5), (13.2, 6.2, 73.5), "roof_glow")

    extra_dict = roof.export_dict()

    # ==================================================================
    # 5. BUMPER_F (Sculpted Royal-Blue Front Mudguard + Twin Telescopic Fork)
    # ==================================================================
    bf = TukTukPartBuilder("bumper_f", sp)
    # Curved wrap-around fender hugging front wheel centered at (43.0, 0.0, 11.8), radius ~15.5
    ang_steps = 12
    a_start, a_end = math.radians(18.0), math.radians(152.0)
    grid_f = []
    for ai in range(ang_steps + 1):
        a = a_start + (a_end - a_start) * (ai / ang_steps)
        r_f = 15.6
        fx = 43.0 + math.cos(a) * r_f
        fz = 11.8 + math.sin(a) * r_f
        row = [
            (fx, -7.2, fz - 1.2),
            (fx, -4.0, fz),
            (fx, 0.0, fz + 0.8),
            (fx, 4.0, fz),
            (fx, 7.2, fz - 1.2),
        ]
        grid_f.append(row)
    bf.add_thick_panel(grid_f, (-0.8, 0.0, -1.0), outer_region="blue_body", inner_region="trim")

    # Twin Telescopic Front Shock Forks + Chrome Fender Brackets
    for sgn in (1.0, -1.0):
        # Upper fork stanchion into cowl neck
        bf.add_cylinder((38.5, 4.2 * sgn, 31.0), (43.0, 4.2 * sgn, 11.8), 1.35, 1.15, 8, "chrome")
        # Coil spring gaiter sleeve
        bf.add_cylinder((40.2, 4.2 * sgn, 24.5), (41.8, 4.2 * sgn, 17.5), 1.65, 1.65, 8, "trim")
    # Chrome front mini-bumper bar under headlight (visible right above front mudguard!)
    bf.add_cylinder((47.5, -11.0, 27.5), (47.5, 11.0, 27.5), 0.72, 0.72, 8, "chrome")
    bf.add_cylinder((44.5, -8.5, 27.5), (47.5, -8.5, 27.5), 0.55, 0.55, 6, "chrome")
    bf.add_cylinder((44.5, 8.5, 27.5), (47.5, 8.5, 27.5), 0.55, 0.55, 6, "chrome")

    bf_dict = bf.export_dict()

    # ==================================================================
    # 6. BUMPER_R (Rear Chrome Tubular Bumper & License Bracket)
    # ==================================================================
    br = TukTukPartBuilder("bumper_r", sp)
    br.add_cylinder((-52.5, -24.0, 12.8), (-52.5, 24.0, 12.8), 1.05, 1.05, 10, "chrome")
    br.add_cylinder((-52.5, -24.0, 12.8), (-48.0, -25.2, 14.5), 0.9, 0.9, 8, "chrome")
    br.add_cylinder((-52.5, 24.0, 12.8), (-48.0, 25.2, 14.5), 0.9, 0.9, 8, "chrome")
    br.add_cylinder((-52.5, -14.0, 12.8), (-49.0, -14.0, 14.2), 0.85, 0.85, 8, "chrome")
    br.add_cylinder((-52.5, 14.0, 12.8), (-49.0, 14.0, 14.2), 0.85, 0.85, 8, "chrome")
    br_dict = br.export_dict()

    # ==================================================================
    # 7. DETAIL_VIB (Vibrating 2-Stroke Engine + Chrome Exhaust + Handlebars!)
    # ==================================================================
    dv = TukTukPartBuilder("detail_vib", sp)
    # Chrome motorbike-style handlebars + center speedo pod + grips!
    dv.add_cylinder((34.5, 0.0, 34.0), (29.5, 0.0, 41.5), 1.2, 1.1, 8, "chrome")
    dv.add_cylinder((29.5, 0.0, 41.5), (27.5, -10.5, 43.2), 0.82, 0.78, 8, "chrome")
    dv.add_cylinder((29.5, 0.0, 41.5), (27.5, 10.5, 43.2), 0.82, 0.78, 8, "chrome")
    # Dark rubber handlebar grips
    dv.add_cylinder((27.5, -10.5, 43.2), (26.5, -14.8, 43.4), 1.05, 1.05, 8, "trim")
    dv.add_cylinder((27.5, 10.5, 43.2), (26.5, 14.8, 43.4), 1.05, 1.05, 8, "trim")
    # Speedometer dial pod
    dv.add_cylinder((30.2, 0.0, 42.2), (28.5, 0.0, 44.2), 2.3, 2.3, 10, "chrome")
    # Under-floor 2-stroke engine block & chrome tailpipe sticking out rear right!
    dv.add_box(-6.0, -7.5, 7.2, 7.5, 7.5, 12.0, "chrome")
    dv.add_cylinder((-6.0, -5.0, 8.2), (-46.5, -13.5, 8.8), 1.1, 1.35, 8, "chrome")
    dv.add_cylinder((-46.5, -13.5, 8.8), (-53.5, -14.2, 9.5), 1.75, 1.55, 8, "chrome")
    dv_dict = dv.export_dict()

    # ==================================================================
    # 8. 3 UNIQUE GOLD-RIM WHEELS (1 Front Center, 2 Rear Left/Right)
    # ==================================================================
    w_f_mesh = bbv.build_3d_wheel("wheel_f", 11.5, 5.0, 2.2, 0.56, True, sp)
    w_f_mesh["origin"] = [sp["wheel_x_f"], 0.0, 11.5]

    w_rl_mesh = bbv.build_3d_wheel("wheel_rl", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], True, sp)
    w_rl_mesh["origin"] = [sp["wheel_x_r"], sp["wheel_y_r"], sp["wheel_r"]]

    w_rr_mesh = bbv.build_3d_wheel("wheel_rr", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], False, sp)
    w_rr_mesh["origin"] = [sp["wheel_x_r"], -sp["wheel_y_r"], sp["wheel_r"]]

    # ==================================================================
    # 9. WRECK CHASSIS (Bent, Scorched Tubular Frame + Crumpled Panels)
    # ==================================================================
    wc = TukTukPartBuilder("wreck_chassis", sp)
    # Twisted warped chassis bed & mangled rear passenger frame
    grid_floor = []
    for xi in (-48.0, -30.0, -10.0, 10.0, 32.0):
        row = []
        for yi in (-23.0, -8.0, 8.0, 23.0):
            warp_z = 9.5 + 3.8 * math.sin(xi * 0.07 + yi * 0.11) + rng.uniform(-1.5, 1.5)
            row.append((xi, yi * (0.94 if xi > 10.0 else 1.0), warp_z))
        grid_floor.append(row)
    wc.add_thick_panel(grid_floor, (0.0, 0.0, -2.2), outer_region="wreck", inner_region="wreck")
    # Scorched rear bench carcass & bent pillars
    wc.add_box(-46.0, -22.0, 16.0, -34.0, 22.0, 36.0, "wreck")
    wc.add_box(2.0, -11.5, 16.0, 9.0, 11.5, 36.0, "wreck")
    wc.add_box(24.0, -15.0, 15.0, 42.0, 15.0, 29.0, "wreck")
    # Glowing engine embers inside twisted frame
    wc.add_box(-5.0, -6.5, 11.0, 9.0, 6.5, 18.0, "ember")
    wc.add_cylinder((-46.0, 22.0, 32.0), (-41.0, 17.5, 55.0), 1.0, 0.9, 8, "wreck")
    wc.add_cylinder((-46.0, -22.0, 32.0), (-49.0, -25.0, 52.0), 1.0, 0.9, 8, "wreck")
    wc_dict = wc.export_dict(custom_origin=(0.0, 0.0, 0.0))

    # ==================================================================
    # 10. 10 TWISTED SHRAPNEL CHUNKS
    # ==================================================================
    shraps = []
    for si in range(10):
        spb = TukTukPartBuilder(f"shrap_{si}", sp)
        r_sh = 4.0 + (si % 4) * 1.9
        thk = 0.8 + (si % 3) * 0.5
        reg = ("blue_body", "wreck", "stripe_seat", "chrome", "ember")[si % 5]
        pts_grid = []
        for gi in range(3):
            row = []
            for gj in range(3):
                px = (gi - 1) * r_sh + rng.uniform(-1.3, 1.3)
                py = (gj - 1) * r_sh * 0.78 + rng.uniform(-1.2, 1.2)
                pz = math.sin(gi * 1.5 + gj * 1.2 + si) * 2.1
                row.append((px, py, pz))
            pts_grid.append(row)
        spb.add_thick_panel(pts_grid, (0.0, 0.0, -thk), outer_region=reg, inner_region="wreck")
        sd = spb.export_dict(custom_origin=(0.0, 0.0, 0.0))
        ang = 2.0 * math.pi * si / 10.0
        sd["origin"] = [
            round(math.cos(ang) * 28.0, 2),
            round(math.sin(ang) * 17.0, 2),
            round(22.0 + (si % 3) * 5.0, 2),
        ]
        shraps.append(sd)

    parts = {
        "chassis": chassis_dict,
        "wreck_chassis": wc_dict,
        "hood": hood_dict,
        "door_l": doors["door_l"],
        "door_r": doors["door_r"],
        "extra_part": extra_dict,
        "bumper_f": bf_dict,
        "bumper_r": br_dict,
        "detail_vib": dv_dict,
        "wheel_f": w_f_mesh,
        "wheel_rl": w_rl_mesh,
        "wheel_rr": w_rr_mesh,
    }
    for si, sd in enumerate(shraps):
        parts[f"shrap_{si}"] = sd

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"spec": sp, "parts": parts}, f)

    tot_v = sum(len(p["verts"]) for k, p in parts.items() if k != "wreck_chassis" and not k.startswith("shrap_"))
    tot_t = sum(len(p["tris"]) for k, p in parts.items() if k != "wreck_chassis" and not k.startswith("shrap_"))
    print(f"[tuktuk] intact={tot_v} verts / {tot_t} tris | wheel_f={len(w_f_mesh['tris'])} tris | wreck={len(wc_dict['tris'])} tris -> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    build_tuktuk()
