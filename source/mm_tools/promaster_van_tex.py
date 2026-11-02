"""High-Precision 2048x2048 Studio Texture & Translucent Glass Painter for the
Fiat Ducato / Ram ProMaster X290 L2H2 High-Roof Walk-In Cargo Van.

Matched 1:1 against reference video frames (frame_001 .. frame_020):
  - Separate asymmetric Right Side (sliding cargo door + silver/black rail + 2 handles)
    and Left Side (continuous blind panel + 1 driver handle + fuel filler flap)
  - Authentic X290 Front Fascia: matte-black sculpted bumper, silver-framed trapezoidal
    4-slat grille with round chrome center emblem, cheek intakes, fog recesses, and
    swept crystalline cat-eye headlights
  - Dedicated Inner & Outer Open Barn Door panels: upper twin oval stamped pockets,
    middle blind-window recess, matte-charcoal lower ABS trim card, right-door pull latch,
    left-door outer EU-style license plate & black lamp garnish, rotary latches & seals
  - Walk-in Cargo Interior: bright white/light-silver ribbed steel floor, matte-black
    lower wall liners, radially-fluted white wheel arches, perforated white structural
    ribs/bows, stitched charcoal cloth seats, and full Ducato instrument dashboard
  - Separate RGBA translucent cab safety glass (light green studio tint + black ceramic
    frit border) & square steel wire-mesh bulkhead screen!
"""
import math
try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    np = None
    Image = ImageDraw = ImageFilter = None

W_VAN = 2048
H_VAN = 2048

# Exact Van Master Coordinates (Quake units, ~42u / meter, L2H2 5.41m x 2.05m x 2.52m)
VAN_SPEC = dict(
    kind="van",
    x0=-113.5,          # Rear step bumper outer face (body D-pillar at -108.0)
    x_body_rear=-108.0,
    x1=114.0,           # Front bumper nose tip
    hw=43.0,            # Half body width (86u total width excluding mirrors)
    z_bot=10.5,         # Lower rocker sill bottom
    z_bmp=33.5,         # Rear corner / front outer bumper top
    z_belt=47.5,        # Main beltline
    z_roof=104.0,       # H2 High-Roof peak
    z_nose_top=51.0,    # Cowl / base of windshield height
    z_rear_top=101.0,   # Rear roof header top
    wheel_x_f=80.0,     # Front axle X
    wheel_x_r=-68.0,    # Rear axle X
    wheel_y=38.2,       # Wheel center Y track
    wheel_r=15.2,       # 16" commercial tire outer radius (30.4u dia)
    wheel_w=9.6,        # Tire width
    dish=2.2,
    rim_ratio=0.63,
    arch_r=22.2,
    flare=1.8,
    x_cowl=84.5,        # Base of raked panoramic windshield
    x_ws_top=48.5,      # Top header of windshield
    z_ws_top=81.5,      # Height of top of windshield
    x_cab_rear=32.0,    # Bulkhead / B-pillar plane
    x_door0=33.5,       # Cab door rear shutline
    x_door1=81.5,       # Cab door front shutline
    x_roof0=-107.0,
    x_roof1=16.0,
    y_roof=36.0,
    z_interior_floor=19.5,
    z_interior_roof=98.5,
)

# 2048x2048 Dedicated Atlas Rectangles (px0, py0, px1, py1)
R_SIDE_R      = (16,   16,  1008,  496)   # Right (-Y) passenger side w/ sliding door & rail
R_SIDE_L      = (16,  512,  1008,  992)   # Left (+Y) driver side (clean panel + fuel door)
R_FRONT       = (1024, 16,  1520,  496)   # Front bumper, trapezoidal grille, swept headlights
R_REAR_FRAME  = (1536, 16,  2032,  496)   # Rear aperture columns, D-pillar taillights, 3rd brake
R_BARN_IN_L   = (1024, 512, 1264,  992)   # Open left barn door inner stamped panel + dark card
R_BARN_IN_R   = (1280, 512, 1520,  992)   # Open right barn door inner stamped panel + latch handle
R_BARN_OUT_L  = (1536, 512, 1776,  992)   # Open left barn door outer white + EU plate & lamp bar
R_BARN_OUT_R  = (1792, 512, 2032,  992)   # Open right barn door outer white panel
R_TOP_ROOF    = (16,  1008,  752, 1360)   # Crowned H2 white roof with stamped ribs
R_CARGO_FLOOR = (768, 1008, 1184, 1440)   # White/silver corrugated steel cargo floor
R_CARGO_WALL  = (1200, 1008, 1616, 1440)  # White stamped inner cargo walls & perforated ribs
R_LINER_BLK   = (1632, 1008, 1824, 1216)  # Matte dark-charcoal lower cargo wall liner
R_ARCH_WHITE  = (1840, 1008, 2032, 1216)  # White inner wheel arch w/ radial stamped flutes
R_DASH        = (1632, 1232, 2032, 1520)  # Full Ducato/ProMaster dashboard & gauges
R_WHEEL       = (16,  1376,  400, 1760)   # 16" silver commercial steel wheel w/ 12 vent holes
R_TREAD       = (416, 1376,  672, 1760)   # Deep commercial radial tire tread
R_SEAT        = (688, 1456, 1008, 1760)   # Charcoal woven cloth seat upholstery + seam ribs
R_TRIM_BLK    = (1024, 1456, 1280, 1760)  # Fine-grain matte black bumper/mirror/cladding plastic
R_CHROME      = (1296, 1456, 1520, 1760)  # Brushed bright silver/chrome metal
R_WHITE_CLEAN = (1536, 1536, 1776, 1760)  # Pure Alpine White painted sheetmetal swatch
R_CEIL_WHITE  = (1792, 1536, 2032, 1760)  # Perforated white ceiling bow & roof liner swatch
R_ENGINE      = (16,  1776,  336, 2032)   # Turbo-diesel engine bay block/plumbing
R_WRECK       = (352, 1776,  688, 2032)   # Scorched buckled wreck sheetmetal
R_EMBER       = (704, 1776, 1040, 2032)   # Glowing orange fire/coal embers


def clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def uv_in_rect(rect, su, sv, pad=4.0):
    x0, y0, x1, y1 = rect
    px = (x0 + pad) + (x1 - x0 - 2.0 * pad) * clamp01(su)
    py = (y0 + pad) + (y1 - y0 - 2.0 * pad) * clamp01(sv)
    return (round(px / W_VAN, 5), round(py / H_VAN, 5))


def side_uv_van(x, z, is_left):
    rect = R_SIDE_L if is_left else R_SIDE_R
    tx = clamp01((x - VAN_SPEC["x0"]) / (VAN_SPEC["x1"] - VAN_SPEC["x0"]))
    tz = clamp01((z - VAN_SPEC["z_bot"]) / (VAN_SPEC["z_roof"] - VAN_SPEC["z_bot"]))
    return uv_in_rect(rect, tx, 1.0 - tz, pad=6.0)


def front_uv_van(y, z):
    # Viewer at +X looking -X: left of image is -Y, right of image is +Y
    ty = clamp01((y + VAN_SPEC["hw"]) / (2.0 * VAN_SPEC["hw"]))
    tz = clamp01((z - VAN_SPEC["z_bot"]) / (VAN_SPEC["z_nose_top"] - VAN_SPEC["z_bot"]))
    return uv_in_rect(R_FRONT, ty, 1.0 - tz, pad=6.0)


def rear_frame_uv_van(y, z):
    # Viewer at -X looking +X: left of image is +Y, right of image is -Y
    ty = clamp01((VAN_SPEC["hw"] - y) / (2.0 * VAN_SPEC["hw"]))
    tz = clamp01((z - VAN_SPEC["z_bot"]) / (VAN_SPEC["z_roof"] - VAN_SPEC["z_bot"]))
    return uv_in_rect(R_REAR_FRAME, ty, 1.0 - tz, pad=6.0)


def top_uv_van(x, y):
    tx = clamp01((x - VAN_SPEC["x0"]) / (VAN_SPEC["x1"] - VAN_SPEC["x0"]))
    ty = clamp01((y + VAN_SPEC["hw"]) / (2.0 * VAN_SPEC["hw"]))
    return uv_in_rect(R_TOP_ROOF, tx, ty, pad=6.0)


def _side_px(rect, x, z):
    x0, y0, x1, y1 = rect
    pad = 6.0
    tx = clamp01((x - VAN_SPEC["x0"]) / (VAN_SPEC["x1"] - VAN_SPEC["x0"]))
    tz = clamp01((z - VAN_SPEC["z_bot"]) / (VAN_SPEC["z_roof"] - VAN_SPEC["z_bot"]))
    return (
        (x0 + pad) + (x1 - x0 - 2.0 * pad) * tx,
        (y1 - pad) - (y1 - y0 - 2.0 * pad) * tz,
    )


def _front_px(y, z):
    x0, y0, x1, y1 = R_FRONT
    pad = 6.0
    ty = clamp01((y + VAN_SPEC["hw"]) / (2.0 * VAN_SPEC["hw"]))
    tz = clamp01((z - VAN_SPEC["z_bot"]) / (VAN_SPEC["z_nose_top"] - VAN_SPEC["z_bot"]))
    return (
        (x0 + pad) + (x1 - x0 - 2.0 * pad) * ty,
        (y1 - pad) - (y1 - y0 - 2.0 * pad) * tz,
    )


def _rear_px(y, z):
    x0, y0, x1, y1 = R_REAR_FRAME
    pad = 6.0
    ty = clamp01((VAN_SPEC["hw"] - y) / (2.0 * VAN_SPEC["hw"]))
    tz = clamp01((z - VAN_SPEC["z_bot"]) / (VAN_SPEC["z_roof"] - VAN_SPEC["z_bot"]))
    return (
        (x0 + pad) + (x1 - x0 - 2.0 * pad) * ty,
        (y1 - pad) - (y1 - y0 - 2.0 * pad) * tz,
    )


def _paint_side_panel(d, glow_d, rect, is_left):
    x0, y0, x1, y1 = rect
    # Base studio Alpine White with subtle vertical horizon sheen matching reference video
    for py in range(y0, y1):
        t = (py - y0) / max(1, y1 - y0 - 1)
        # Bright studio top -> subtle soft horizon reflection around beltline -> clean lower panel
        v = 247 - int(8 * math.sin(math.pi * min(1.0, t * 1.15))) - int(5 * (t ** 2.2))
        d.line([(x0, py), (x1 - 1, py)], fill=(v, v + 1, v + 3))

    # Subtle stamped sheetmetal creases & blind-window panel recess (matched to frame_005 & frame_015!)
    # 1. H2 high-roof horizontal crown seam (z = 83.5) & upper roof rib (z = 92.5)
    for z_line, hi, lo in [(92.5, 253, 232), (83.5, 254, 226), (45.2, 254, 224), (26.5, 252, 231)]:
        px_a, py_c = _side_px(rect, -107.5, z_line)
        px_b, _ = _side_px(rect, 33.5 if z_line > 50 else 80.0, z_line)
        d.line([(px_a, py_c - 2), (px_b, py_c - 2)], fill=(lo, lo + 1, lo + 3), width=2)
        d.line([(px_a, py_c + 1), (px_b, py_c + 1)], fill=(hi, hi, min(255, hi + 1)), width=2)

    # 2. Recessed Cargo Blind-Panel Bays (z = 50.5 .. 78.5, x = -103 .. +30)
    bays = [(-103.0, -26.5), (-21.5, 29.5)] if not is_left else [(-103.0, 29.5)]
    for bx0, bx1 in bays:
        pa0, pb0 = _side_px(rect, bx0, 78.5)
        pa1, pb1 = _side_px(rect, bx1, 50.5)
        d.rounded_rectangle([pa0, pb0, pa1, pb1], radius=8, fill=(241, 243, 246), outline=(222, 225, 230), width=2)
        d.line([(pa0 + 6, pb1 - 2), (pa1 - 6, pb1 - 2)], fill=(253, 254, 255), width=2)

    # 3. Cab Door Shutlines (B-pillar at x = 33.5, curved front cab door seam x = 81.5)
    px_b, py_b_top = _side_px(rect, 33.5, 81.0)
    _, py_b_bot = _side_px(rect, 33.5, 11.5)
    d.line([(px_b, py_b_top), (px_b, py_b_bot)], fill=(88, 92, 98), width=2)
    d.line([(px_b + 2, py_b_top), (px_b + 2, py_b_bot)], fill=(253, 254, 255), width=1)

    px_f, py_f_top = _side_px(rect, 81.5, 52.0)
    _, py_f_bot = _side_px(rect, 81.5, 34.0)
    d.line([(px_f, py_f_top), (px_f, py_f_bot)], fill=(88, 92, 98), width=2)

    # 4. Asymmetric Right vs Left Features!
    if not is_left:
        # RIGHT (Passenger) SIDE: Full-height Sliding Cargo Door Shutline + Track Rail + TWO Handles!
        sx0, sy_top = _side_px(rect, -24.0, 89.5)
        sx1, _ = _side_px(rect, 33.5, 89.5)
        _, sy_bot = _side_px(rect, -24.0, 12.5)
        d.line([(sx0, sy_top), (sx1, sy_top)], fill=(85, 89, 95), width=2)
        d.line([(sx0, sy_top), (sx0, sy_bot)], fill=(85, 89, 95), width=2)

        # Horizontal Sliding Door Rail (x = -80.5 .. -24.0, z = 45.6 .. 48.0, frame_005!)
        rx0, ry0 = _side_px(rect, -80.5, 48.2)
        rx1, ry1 = _side_px(rect, -24.0, 45.4)
        d.rectangle([rx0, ry0, rx1, ry1], fill=(168, 173, 180), outline=(52, 55, 60), width=1)
        d.line([(rx0 + 4, (ry0 + ry1) * 0.5), (rx1 - 4, (ry0 + ry1) * 0.5)], fill=(58, 62, 68), width=2)
        # Matte-black rail end-caps (visible in frame_005 & frame_007!)
        d.rectangle([rx0, ry0 - 1, rx0 + 12, ry1 + 1], fill=(28, 30, 34))
        d.rectangle([rx1 - 12, ry0 - 1, rx1, ry1 + 1], fill=(28, 30, 34))

        handle_xs = [27.0, 38.2]
    else:
        # LEFT (Driver) SIDE: Fuel filler flap below B-pillar (frame_013, frame_015!) + ONE Handle!
        fx0, fy0 = _side_px(rect, 33.8, 35.0)
        fx1, fy1 = _side_px(rect, 41.2, 25.0)
        d.rounded_rectangle([fx0, fy0, fx1, fy1], radius=3, outline=(135, 140, 148), width=2)
        handle_xs = [38.2]

    # Vertical Matte-Black Oval Recessed Door Handles (frame_005, frame_007, frame_015)
    for hx in handle_xs:
        hx0, hy0 = _side_px(rect, hx - 2.3, 47.6)
        hx1, hy1 = _side_px(rect, hx + 2.3, 39.6)
        d.rounded_rectangle([hx0, hy0, hx1, hy1], radius=7, fill=(24, 26, 30), outline=(55, 58, 64), width=1)
        # Inner pull bar highlight
        d.rounded_rectangle([hx0 + 3, hy0 + 4, hx1 - 3, hy1 - 4], radius=4, fill=(38, 41, 47))
        d.ellipse([hx0 + 4, hy1 - 9, hx1 - 4, hy1 - 3], fill=(16, 18, 20))

    # 5. Matte-Black Lower Rub-Strip Cladding (z = 13.5 .. 23.8, leaving white rocker sill z = 10.5 .. 13.5!)
    # Segmented into 3 molded panels between the wheel arches (-45.5 .. +57.5) with 2 Amber Side Markers!
    seg_bounds = [(-45.5, -24.5), (-23.5, 32.8), (33.8, 57.5)]
    for sg0, sg1 in seg_bounds:
        cx0, cy0 = _side_px(rect, sg0, 23.8)
        cx1, cy1 = _side_px(rect, sg1, 13.5)
        d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=4, fill=(29, 31, 35), outline=(18, 20, 23), width=2)
        d.line([(cx0 + 3, cy0 + 2), (cx1 - 3, cy0 + 2)], fill=(54, 58, 64), width=2)

    # Two Glowing Amber Rectangular Side-Marker Reflectors (frame_005, frame_009, frame_013, frame_015)
    for mx in (-35.0, 41.5):
        mx0, my0 = _side_px(rect, mx - 2.4, 18.8)
        mx1, my1 = _side_px(rect, mx + 2.4, 16.0)
        d.rounded_rectangle([mx0 - 1, my0 - 1, mx1 + 1, my1 + 1], radius=2, fill=(16, 17, 20))
        d.rounded_rectangle([mx0, my0, mx1, my1], radius=2, fill=(235, 118, 18))
        d.line([(mx0 + 2, my0 + 2), (mx1 - 2, my0 + 2)], fill=(255, 188, 70), width=1)
        glow_d.rounded_rectangle([mx0, my0, mx1, my1], radius=2, fill=(95, 42, 4))

    # 6. Continuous Matte-Black Wheel Arch Flares + Front & Rear Wraparound Bumper Corners!
    # Rear Black Corner Bumper Block (x = -113.5 .. -85.0, z = 10.5 .. 33.5)
    rbx0, rby0 = _side_px(rect, -113.5, 33.5)
    rbx1, rby1 = _side_px(rect, -84.0, 10.5)
    d.rectangle([rbx0, rby0, rbx1, rby1], fill=(28, 30, 34))
    d.line([(rbx0, rby0 + 1), (rbx1, rby0 + 1)], fill=(55, 59, 65), width=2)

    # Front Black Wraparound Bumper Corner (x = 92.0 .. 114.0, z = 10.5 .. 36.8)
    d.polygon([
        _side_px(rect, 92.0, 10.5),
        _side_px(rect, 114.0, 10.5),
        _side_px(rect, 114.0, 36.8),
        _side_px(rect, 93.0, 37.2),
        _side_px(rect, 88.0, 28.0),
    ], fill=(28, 30, 34))

    # Sculpted Matte-Black Wheel Arch Flares around Rear (-68.0) & Front (+80.0) Wheels
    for wx in (-68.0, 80.0):
        pts_outer = []
        pts_inner = []
        for k in range(33):
            ang = math.pi * k / 32.0
            pts_outer.append(_side_px(rect, wx - math.cos(ang) * 24.8, 14.5 + math.sin(ang) * 23.0))
            pts_inner.append(_side_px(rect, wx - math.cos(ang) * 18.2, 13.5 + math.sin(ang) * 17.2))
        d.polygon(pts_outer + pts_inner[::-1], fill=(28, 30, 34))
        d.line(pts_outer, fill=(56, 60, 67), width=2)
        # Dark wheelhouse void inside arch
        d.polygon(pts_inner, fill=(14, 15, 18))

    # 7. Side Wrap of Swept Front Headlight (x = 95.5 .. 109.5, z = 36.8 .. 43.2, frame_007, frame_015!)
    hl_pts = [
        _side_px(rect, 109.5, 36.8),
        _side_px(rect, 108.0, 40.2),
        _side_px(rect, 95.5, 43.2),
        _side_px(rect, 97.5, 37.2),
    ]
    d.polygon(hl_pts, fill=(225, 232, 240), outline=(70, 76, 84))
    d.line([hl_pts[1], hl_pts[2]], fill=(252, 254, 255), width=2)

    # 8. Side Wrap of Tall Vertical Ruby-Red D-Pillar Taillight (x = -108.5 .. -101.5, z = 33.5 .. 59.5)
    tl0, tly0 = _side_px(rect, -109.0, 59.5)
    tl1, tly1 = _side_px(rect, -101.8, 33.5)
    d.rounded_rectangle([tl0, tly0, tl1, tly1], radius=5, fill=(192, 20, 24), outline=(65, 10, 12), width=2)
    # Clear reverse/turn lens inset on rear edge
    d.rectangle([tl0 + 2, tly0 + (tly1 - tly0) * 0.34, tl0 + (tl1 - tl0) * 0.45, tly1 - (tly1 - tly0) * 0.16],
                fill=(232, 236, 242))
    glow_d.rounded_rectangle([tl0 + 2, tly0 + 4, tl1 - 2, tly1 - 4], radius=3, fill=(85, 10, 12))


def _paint_front_panel(d, glow_d):
    x0, y0, x1, y1 = R_FRONT
    # Upper white hood & fender zone (top), lower matte-black wraparound bumper
    d.rectangle([x0, y0, x1, y1], fill=(246, 247, 249))

    # Helper for 3D aspect-accurate ellipses in R_FRONT (dy=86u -> 484px, dz=40.5u -> 468px)
    def _ell_3d(cy, cz, ry_u, rz_u, **kw):
        p0 = _front_px(cy - ry_u, cz + rz_u)
        p1 = _front_px(cy + ry_u, cz - rz_u)
        d.ellipse([min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])], **kw)

    # Black windshield wiper cowl band at very top (z = 49.0 .. 51.0)
    _, py_cowl = _front_px(0.0, 49.2)
    d.rectangle([x0, y0, x1, int(py_cowl)], fill=(26, 28, 32))

    # Sculpted Matte-Black Front Bumper Silhouette (high at outer corners z=36.8, dipping around white/silver grille cradle z=23.2)
    bmp_poly = [
        _front_px(-43.0, 10.5),
        _front_px( 43.0, 10.5),
        _front_px( 43.0, 36.8),
        _front_px( 24.5, 34.2),
        _front_px( 19.8, 22.8),
        _front_px(-19.8, 22.8),
        _front_px(-24.5, 34.2),
        _front_px(-43.0, 36.8),
    ]
    d.polygon(bmp_poly, fill=(30, 32, 37))

    # Center Lower Bumper Section below grille
    d.polygon([
        _front_px(-24.5, 23.0),
        _front_px( 24.5, 23.0),
        _front_px( 24.5, 10.5),
        _front_px(-24.5, 10.5),
    ], fill=(28, 30, 35))

    # Subtle upper bumper crease highlight
    d.line([_front_px(-42.5, 36.4), _front_px(-24.5, 33.9), _front_px(-19.8, 22.8),
            _front_px(19.8, 22.8), _front_px(24.5, 33.9), _front_px(42.5, 36.4)],
           fill=(62, 66, 74), width=3)

    # Trapezoidal Silver/White Grille Surround + 4 Horizontal Black Slats + Round Chrome Center Emblem (frame_010!)
    g_outer = [
        _front_px(-22.2, 34.2),
        _front_px( 22.2, 34.2),
        _front_px( 18.2, 23.2),
        _front_px(-18.2, 23.2),
    ]
    g_inner = [
        _front_px(-20.4, 33.3),
        _front_px( 20.4, 33.3),
        _front_px( 16.8, 24.1),
        _front_px(-16.8, 24.1),
    ]
    d.polygon(g_outer, fill=(235, 238, 243), outline=(145, 150, 158))
    d.polygon(g_inner, fill=(16, 18, 21))

    # 4 Crisp Horizontal Grille Slats
    for sz in (26.0, 28.1, 30.2, 32.2):
        frac = (sz - 24.1) / 9.2
        hw_s = 16.6 + frac * 3.5
        sa = _front_px(-hw_s, sz)
        sb = _front_px( hw_s, sz)
        d.line([sa, sb], fill=(48, 52, 58), width=5)
        d.line([(sa[0], sa[1] - 2), (sb[0], sb[1] - 2)], fill=(88, 94, 102), width=1)

    # True 3D Circular Chrome Center Badge with Horizontal Bar (exact match to frame_010 & frame_011!)
    _ell_3d(0.0, 28.8, 3.8, 3.8, fill=(18, 20, 24))
    _ell_3d(0.0, 28.8, 3.3, 3.3, fill=(22, 25, 30), outline=(232, 237, 244), width=5)
    eb0 = _front_px(-3.5, 29.35)
    eb1 = _front_px( 3.5, 28.25)
    d.rectangle([eb0[0], eb0[1], eb1[0], eb1[1]], fill=(232, 237, 244), outline=(90, 96, 105), width=1)

    # Sculpted Cheek Air-Intake Scoops in Bumper under Headlights (frame_010, frame_011)
    for sgn in (-1.0, 1.0):
        scoop = [
            _front_px(sgn * 24.2, 29.8),
            _front_px(sgn * 38.8, 32.2),
            _front_px(sgn * 37.5, 25.0),
            _front_px(sgn * 22.2, 24.4),
        ]
        d.polygon(scoop, fill=(14, 15, 18), outline=(46, 50, 56))
        # Lower circular fog-light pod recess (aspect-corrected 3D circle!)
        _ell_3d(sgn * 33.8, 15.2, 2.5, 2.5, fill=(16, 18, 22), outline=(45, 48, 54), width=2)

    # Center Flat Bumper License Recess & Lower Cooling Slot (frame_010, frame_011)
    lp0 = _front_px(-18.5, 21.0)
    lp1 = _front_px( 18.5, 15.6)
    d.rounded_rectangle([lp0[0], lp0[1], lp1[0], lp1[1]], radius=4, fill=(22, 24, 28), outline=(48, 52, 58), width=2)
    sl0 = _front_px(-17.5, 14.5)
    sl1 = _front_px( 17.5, 12.0)
    d.rectangle([sl0[0], sl0[1], sl1[0], sl1[1]], fill=(12, 13, 16))

    # Swept Crystalline Cat-Eye Headlights (frame_009, frame_010, frame_011!)
    for sgn in (-1.0, 1.0):
        hl = [
            _front_px(sgn * 21.8, 34.2),
            _front_px(sgn * 41.2, 37.0),
            _front_px(sgn * 39.6, 42.6),
            _front_px(sgn * 23.6, 38.4),
        ]
        # Dark anthracite outer housing seal + bright sculpted chrome reflector bed
        d.polygon(hl, fill=(52, 57, 65), outline=(28, 31, 36))
        hl_in = [
            _front_px(sgn * 22.4, 34.6),
            _front_px(sgn * 40.5, 37.3),
            _front_px(sgn * 39.1, 42.1),
            _front_px(sgn * 24.0, 38.1),
        ]
        d.polygon(hl_in, fill=(214, 220, 230), outline=(110, 118, 128))
        # Dark lower internal bezel shelf inside headlamp (gives authentic X290 3D depth!)
        hl_floor = [
            _front_px(sgn * 22.6, 34.7),
            _front_px(sgn * 40.2, 37.3),
            _front_px(sgn * 39.8, 38.4),
            _front_px(sgn * 23.2, 35.6),
        ]
        d.polygon(hl_floor, fill=(84, 90, 102))
        # Faceted chrome dual-parabola reflectors + specular bulb cores
        _ell_3d(sgn * 31.4, 38.3, 3.8, 1.9, fill=(242, 246, 252), outline=(142, 150, 162), width=1)
        _ell_3d(sgn * 31.4, 38.5, 2.2, 1.1, fill=(255, 255, 255))
        _ell_3d(sgn * 31.4, 38.2, 0.9, 0.65, fill=(118, 126, 138))
        _ell_3d(sgn * 25.5, 36.7, 2.3, 1.4, fill=(238, 243, 250), outline=(146, 154, 166), width=1)
        _ell_3d(sgn * 25.5, 36.8, 1.1, 0.7, fill=(255, 255, 255))
        # Subtle outer clear/warm-amber turn-indicator prism facet (frame_009 & frame_010!)
        turn_poly = [
            _front_px(sgn * 36.6, 37.6),
            _front_px(sgn * 40.2, 37.5),
            _front_px(sgn * 39.0, 41.8),
            _front_px(sgn * 36.2, 40.8),
        ]
        d.polygon(turn_poly, fill=(235, 224, 206), outline=(168, 162, 154))
        _ell_3d(sgn * 38.3, 39.4, 0.95, 1.15, fill=(238, 182, 112))
        # Crisp bright LED DRL top eyebrow + dark lower gasket shadow
        d.line([hl[0], hl[1]], fill=(32, 36, 42), width=3)
        d.line([hl_in[2], hl_in[3]], fill=(255, 255, 255), width=4)

        gm0 = _front_px(sgn * 31.2 - 2.8, 38.2 + 1.6)
        gm1 = _front_px(sgn * 31.2 + 2.8, 38.2 - 1.6)
        glow_d.ellipse([min(gm0[0], gm1[0]), min(gm0[1], gm1[1]), max(gm0[0], gm1[0]), max(gm0[1], gm1[1])], fill=(175, 185, 200))

    # Hood shutline across nose above grille & headlights (frame_010!)
    d.line([_front_px(-39.6, 42.6), _front_px(-23.6, 38.4), _front_px(-21.8, 34.5),
            _front_px(21.8, 34.5), _front_px(23.6, 38.4), _front_px(39.6, 42.6)],
           fill=(115, 122, 130), width=2)


def _paint_rear_frame(d, glow_d):
    x0, y0, x1, y1 = R_REAR_FRAME
    d.rectangle([x0, y0, x1, y1], fill=(245, 246, 248))

    # Matte-black rear step bumper & corner blocks (z = 10.5 .. 33.5 at sides, z = 10.5 .. 16.0 across center step)
    for sgn in (-1.0, 1.0):
        pa = _rear_px(sgn * 43.0, 33.5)
        pb = _rear_px(sgn * 32.5, 10.5)
        d.rectangle([min(pa[0], pb[0]), pa[1], max(pa[0], pb[0]), pb[1]], fill=(28, 30, 34))
    sa = _rear_px(34.0, 17.0)
    sb = _rear_px(-34.0, 10.5)
    d.rectangle([sa[0], sa[1], sb[0], sb[1]], fill=(26, 28, 32))

    # Tall Vertical D-Pillar Taillights (z = 33.5 .. 59.5, y = ±35.2 .. ±42.8, frame_001, frame_017, frame_020!)
    for sgn in (-1.0, 1.0):
        ta = _rear_px(sgn * 42.8, 59.5)
        tb = _rear_px(sgn * 35.2, 33.5)
        lx0, lx1 = int(min(ta[0], tb[0])), int(max(ta[0], tb[0]))
        ly0, ly1 = int(ta[1]), int(tb[1])
        d.rounded_rectangle([lx0, ly0, lx1, ly1], radius=6, fill=(172, 14, 20), outline=(42, 6, 10), width=2)
        d.rounded_rectangle([lx0 + 3, ly0 + 4, lx1 - 3, ly1 - 4], radius=4, fill=(198, 20, 26))
        # Clear vertical backup/turn chamber on inner half (frame_001 & frame_017!)
        if sgn > 0:
            cx0, cx1 = lx0 + int((lx1 - lx0) * 0.48), lx1 - 4
        else:
            cx0, cx1 = lx0 + 4, lx0 + int((lx1 - lx0) * 0.52)
        cy0 = ly0 + int((ly1 - ly0) * 0.32)
        cy1 = ly1 - int((ly1 - ly0) * 0.16)
        d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=3, fill=(232, 236, 242), outline=(140, 25, 30), width=1)
        glow_d.rounded_rectangle([lx0 + 3, ly0 + 4, lx1 - 3, ly1 - 4], radius=4, fill=(135, 14, 18))

    # Center High-Mount 3rd Brake Light LED Bar (y = -6.8 .. +6.8, z = 98.0 .. 100.8, frame_001 & frame_020!)
    ba = _rear_px(6.8, 100.8)
    bb = _rear_px(-6.8, 98.0)
    d.rounded_rectangle([ba[0], ba[1], bb[0], bb[1]], radius=4, fill=(175, 16, 20), outline=(40, 8, 10), width=2)
    for k in range(4):
        ex = ba[0] + 8 + k * ((bb[0] - ba[0] - 16) / 3.0)
        ey = 0.5 * (ba[1] + bb[1])
        d.ellipse([ex - 4, ey - 3, ex + 4, ey + 3], fill=(255, 95, 85))
    glow_d.rounded_rectangle([ba[0] + 2, ba[1] + 2, bb[0] - 2, bb[1] - 2], radius=3, fill=(155, 18, 20))

    # Black rubber aperture weatherstrip around open doorway (y = -33.2 .. +33.2, z = 19.0 .. 96.5)
    wa = _rear_px(33.2, 96.5)
    wb = _rear_px(-33.2, 19.0)
    d.rounded_rectangle([wa[0], wa[1], wb[0], wb[1]], radius=10, outline=(24, 26, 30), width=6)


def _paint_barn_doors(d):
    # Inner Left & Right Barn Doors (frame_001 & frame_020!)
    for rect, has_handle in [(R_BARN_IN_L, False), (R_BARN_IN_R, True)]:
        x0, y0, x1, y1 = rect
        w, h = x1 - x0, y1 - y0
        # Pure white stamped inner steel + perimeter black rubber weatherstrip seal
        d.rectangle([x0, y0, x1, y1], fill=(242, 244, 247))
        d.rounded_rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5], radius=10, outline=(28, 30, 34), width=5)

        # Top & Bottom metal rotary striker latches (frame_001, frame_020)
        lx = x0 + 18 if not has_handle else x1 - 36
        d.rectangle([lx, y0 + 10, lx + 18, y0 + 28], fill=(42, 46, 52), outline=(140, 145, 152), width=1)
        d.rectangle([lx, y1 - 28, lx + 18, y1 - 10], fill=(42, 46, 52), outline=(140, 145, 152), width=1)

        # Upper 2 Horizontal Stamped Oval-Ended Structural Pockets (frame_001, frame_020!)
        for py0_f, py1_f in [(0.07, 0.16), (0.19, 0.28)]:
            pa = (x0 + int(w * 0.12), y0 + int(h * py0_f))
            pb = (x1 - int(w * 0.12), y0 + int(h * py1_f))
            d.rounded_rectangle([pa[0], pa[1], pb[0], pb[1]], radius=14, fill=(214, 219, 226), outline=(196, 202, 210), width=2)
            # Soft studio shadow along top edge of stamped pocket
            d.rounded_rectangle([pa[0] + 3, pa[1] + 2, pb[0] - 3, pa[1] + 13], radius=8, fill=(186, 193, 202))

        # Middle Large Rounded-Square Blind-Window Stamped Recess (frame_001, frame_020!)
        ma = (x0 + int(w * 0.13), y0 + int(h * 0.33))
        mb = (x1 - int(w * 0.13), y0 + int(h * 0.59))
        d.rounded_rectangle([ma[0], ma[1], mb[0], mb[1]], radius=18, fill=(235, 238, 242), outline=(212, 216, 223), width=3)

        # Lower Matte Dark-Charcoal ABS Trim Card with 4 Fastener Pins (frame_001, frame_020!)
        ca = (x0 + int(w * 0.10), y0 + int(h * 0.66))
        cb = (x1 - int(w * 0.10), y0 + int(h * 0.94))
        d.rounded_rectangle([ca[0], ca[1], cb[0], cb[1]], radius=6, fill=(46, 49, 54), outline=(28, 30, 34), width=2)
        for px_c in (ca[0] + 10, cb[0] - 10):
            for py_c in (ca[1] + 10, cb[1] - 10):
                d.ellipse([px_c - 3, py_c - 3, px_c + 3, py_c + 3], fill=(26, 28, 32), outline=(72, 76, 82))

        # Right-door Inner Black Rectangular Pull/Release Latch Handle + Small Spec Label (frame_001, frame_020!)
        if has_handle:
            hx0 = x0 + int(w * 0.34)
            hy0 = y0 + int(h * 0.602)
            d.rounded_rectangle([hx0, hy0, hx0 + 48, hy0 + 24], radius=5, fill=(24, 26, 30), outline=(65, 70, 78), width=2)
            d.rounded_rectangle([hx0 + 9, hy0 + 6, hx0 + 39, hy0 + 18], radius=3, fill=(42, 45, 52))
            # Secondary small black rectangular plate to its right (exact detail from frame_001 & frame_020!)
            d.rounded_rectangle([hx0 + 58, hy0 + 5, hx0 + 82, hy0 + 16], radius=2, fill=(38, 41, 46))

    # Outer Left & Right Barn Doors (frame_015 & frame_017!)
    for rect, is_left_door in [(R_BARN_OUT_L, True), (R_BARN_OUT_R, False)]:
        x0, y0, x1, y1 = rect
        w, h = x1 - x0, y1 - y0
        for py in range(y0, y1):
            t = (py - y0) / max(1, h - 1)
            v = 247 - int(7 * (t ** 1.5))
            d.line([(x0, py), (x1 - 1, py)], fill=(v, v + 1, v + 3))
        # Upper blind-panel recess on exterior door
        d.rounded_rectangle([x0 + 18, y0 + int(h * 0.28), x1 - 18, y0 + int(h * 0.56)],
                            radius=8, fill=(241, 243, 246), outline=(222, 226, 232), width=2)
        # Matte-black lower cladding band along bottom of rear doors (matching z = 19.5 .. 33.5!)
        d.rectangle([x0, y0 + int(h * 0.82), x1, y1], fill=(28, 30, 34))
        d.line([(x0, y0 + int(h * 0.82)), (x1, y0 + int(h * 0.82))], fill=(58, 62, 68), width=2)

        if is_left_door:
            # EU/Commercial License Plate + Black Lamp Overhang + Script Badge (frame_015 & frame_017!)
            px_l = x0 + int(w * 0.16)
            px_r = x1 - int(w * 0.14)
            py_p = y0 + int(h * 0.69)
            # Dark script badge above overhang
            d.line([(px_l + 18, py_p - 20), (px_l + 86, py_p - 20)], fill=(45, 48, 54), width=4)
            d.line([(px_l + 14, py_p - 12), (px_l + 96, py_p - 12)], fill=(75, 80, 88), width=2)
            # Black lamp garnish bar
            d.rounded_rectangle([px_l - 4, py_p - 4, px_r + 4, py_p + 8], radius=3, fill=(24, 26, 30))
            # White license plate w/ blue EU band on left
            d.rectangle([px_l, py_p + 8, px_r, py_p + 40], fill=(246, 248, 250), outline=(30, 32, 36), width=2)
            d.rectangle([px_l + 2, py_p + 10, px_l + 20, py_p + 38], fill=(22, 68, 168))
            # Plate characters
            for kx, kw in [(30, 12), (46, 10), (62, 14), (82, 12), (98, 10), (114, 12)]:
                if px_l + kx + kw < px_r - 6:
                    d.rectangle([px_l + kx, py_p + 14, px_l + kx + kw, py_p + 34], fill=(24, 26, 30))
            # Vertical black exterior handle near inner split edge
            hx = x1 - 30
            hy = y0 + int(h * 0.60)
            d.rounded_rectangle([hx, hy, hx + 16, hy + 46], radius=6, fill=(24, 26, 30), outline=(58, 62, 68), width=1)
        else:
            # Right outer door recessed black release handle visible in front 3/4 view (frame_009!)
            hx = x0 + 20
            hy = y0 + int(h * 0.61)
            d.rounded_rectangle([hx, hy, hx + 36, hy + 24], radius=5, fill=(22, 24, 28), outline=(58, 62, 68), width=1)


def _paint_wheel_and_tread(d):
    # 16" Commercial Silver Stamped Steel Wheel ("Steelie", frame_005, frame_007, frame_015!)
    wx0, wy0, wx1, wy1 = R_WHEEL
    cx = (wx0 + wx1) // 2   # 208
    cy = (wy0 + wy1) // 2   # 1568
    r_tire = 178            # urad = 178 / 2048
    d.rectangle([wx0, wy0, wx1, wy1], fill=(22, 24, 27))
    # Outer rubber tire & sidewall rings
    d.ellipse([cx - r_tire, cy - r_tire, cx + r_tire, cy + r_tire], fill=(26, 28, 32), outline=(16, 17, 20), width=3)
    d.ellipse([cx - 156, cy - 156, cx + 156, cy + 156], outline=(40, 43, 49), width=3)
    d.ellipse([cx - 134, cy - 134, cx + 134, cy + 134], outline=(34, 37, 42), width=2)

    # Stamped Silver Steel Rim Lip & Concave Dish (r = 114 px)
    r_rim = 114
    d.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(196, 202, 210), outline=(92, 98, 106), width=3)
    d.ellipse([cx - 102, cy - 102, cx + 102, cy + 102], fill=(214, 220, 228), outline=(145, 152, 162), width=3)
    # Recessed dish ring where ventilation holes sit
    d.ellipse([cx - 88, cy - 88, cx + 88, cy + 88], fill=(178, 184, 193), outline=(130, 136, 145), width=2)

    # 12 Crisp Circular Commercial Steelie Ventilation Holes (exact match to frame_005 & frame_015!)
    n_holes = 12
    for i in range(n_holes):
        ang = 2.0 * math.pi * i / n_holes
        hx = cx + math.cos(ang) * 69.0
        hy = cy + math.sin(ang) * 69.0
        # Silver stamped bevel around dark brake-drum hole
        d.ellipse([hx - 12, hy - 12, hx + 12, hy + 12], fill=(228, 233, 240))
        d.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=(24, 27, 32))

    # Stepped Raised Center Hub Cap & 5 Commercial Lug Bolts (frame_005, frame_015!)
    d.ellipse([cx - 48, cy - 48, cx + 48, cy + 48], fill=(212, 218, 226), outline=(128, 134, 142), width=2)
    for i in range(5):
        ang = 2.0 * math.pi * i / 5.0 - 0.3
        lx = cx + math.cos(ang) * 33.0
        ly = cy + math.sin(ang) * 33.0
        d.ellipse([lx - 7, ly - 7, lx + 7, ly + 7], fill=(150, 156, 165))
        d.ellipse([lx - 5, ly - 5, lx + 5, ly + 5], fill=(38, 42, 48))
    d.ellipse([cx - 19, cy - 19, cx + 19, cy + 19], fill=(182, 188, 198), outline=(95, 102, 110), width=2)
    d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=(55, 60, 68))

    # Commercial Radial Tire Tread
    tx0, ty0, tx1, ty1 = R_TREAD
    d.rectangle([tx0, ty0, tx1, ty1], fill=(25, 27, 31))
    w_t = tx1 - tx0
    for gx in (0.22, 0.42, 0.58, 0.78):
        px = tx0 + int(w_t * gx)
        d.rectangle([px - 4, ty0, px + 4, ty1], fill=(14, 15, 18))
    for py in range(ty0, ty1, 18):
        d.line([(tx0 + 4, py), (tx1 - 4, py + 4)], fill=(17, 18, 22), width=3)


def _paint_interior_and_roof(d):
    # 1. Crowned White H2 Roof w/ 6 Longitudinal Anti-Drum Ribs (strictly on flat cargo roof x < 14, keeping forehead pure Alpine White!)
    rx0, ry0, rx1, ry1 = R_TOP_ROOF
    d.rectangle([rx0, ry0, rx1, ry1], fill=(246, 248, 250))
    rib_x_end = rx0 + int((rx1 - rx0) * 0.54)
    for k in range(1, 7):
        py = ry0 + int((ry1 - ry0) * k / 7.0)
        d.rounded_rectangle([rx0 + 28, py - 4, rib_x_end, py + 4], radius=4, fill=(240, 243, 247), outline=(231, 235, 240))

    # 2. Bright White/Light-Silver Corrugated Cargo Floor (frame_001 & frame_020!)
    fx0, fy0, fx1, fy1 = R_CARGO_FLOOR
    d.rectangle([fx0, fy0, fx1, fy1], fill=(224, 229, 235))
    n_ribs = 14
    rw = (fx1 - fx0) / n_ribs
    for i in range(n_ribs):
        rx = fx0 + i * rw
        d.rectangle([rx + rw * 0.20, fy0, rx + rw * 0.80, fy1], fill=(238, 242, 247))
        d.line([(rx + rw * 0.20, fy0), (rx + rw * 0.20, fy1)], fill=(252, 254, 255), width=2)
        d.line([(rx + rw * 0.80, fy0), (rx + rw * 0.80, fy1)], fill=(192, 198, 208), width=2)
    # Transverse floor seam & tie-down lashing cups
    for sy_f in (0.25, 0.50, 0.75):
        py = fy0 + int((fy1 - fy0) * sy_f)
        d.line([(fx0, py), (fx1, py)], fill=(204, 210, 218), width=2)
        for sx_c in (fx0 + 22, fx1 - 22):
            d.ellipse([sx_c - 8, py - 8, sx_c + 8, py + 8], fill=(175, 182, 192), outline=(110, 116, 126), width=2)

    # 3. Upper White Stamped Cargo Wall w/ Perforated Box-Rail & Lightening Holes (frame_001 & frame_020!)
    wx0, wy0, wx1, wy1 = R_CARGO_WALL
    d.rectangle([wx0, wy0, wx1, wy1], fill=(228, 232, 238))
    wh = wy1 - wy0
    # Horizontal mid-rail with oval lightening holes (exact signature of frame_001!)
    ry_mid = wy0 + int(wh * 0.48)
    d.rectangle([wx0, ry_mid - 18, wx1, ry_mid + 18], fill=(238, 241, 246), outline=(198, 204, 212), width=2)
    for hx in range(wx0 + 24, wx1 - 20, 44):
        d.rounded_rectangle([hx - 11, ry_mid - 6, hx + 11, ry_mid + 6], radius=5, fill=(148, 155, 165), outline=(210, 215, 222))
    # Vertical stamped pillar channels
    for vx in range(wx0 + 36, wx1 - 20, 96):
        d.rectangle([vx - 12, wy0 + 10, vx + 12, wy1 - 10], fill=(239, 242, 247), outline=(202, 208, 216), width=2)
        for hy in (wy0 + 26, wy0 + 52, wy1 - 28):
            d.rounded_rectangle([vx - 5, hy - 8, vx + 5, hy + 8], radius=4, fill=(135, 142, 152))

    # 4. Matte Dark-Charcoal Lower Cargo Wall Liner (frame_001 & frame_020!)
    lx0, ly0, lx1, ly1 = R_LINER_BLK
    d.rectangle([lx0, ly0, lx1, ly1], fill=(28, 30, 34))
    for py in range(ly0 + 12, ly1 - 8, 28):
        d.line([(lx0 + 8, py), (lx1 - 8, py)], fill=(34, 37, 42), width=1)

    # 5. White Inner Wheel Housing w/ Subtle Stamped Radial Flutes (exact match to frame_001!)
    ax0, ay0, ax1, ay1 = R_ARCH_WHITE
    d.rectangle([ax0, ay0, ax1, ay1], fill=(241, 244, 248))
    acx, acy = (ax0 + ax1) // 2, ay1 - 10
    for k in range(6):
        ang = math.pi * (0.18 + 0.64 * k / 5.0)
        x_end = acx + math.cos(ang) * 82
        y_end = acy - math.sin(ang) * 155
        d.line([(acx + math.cos(ang) * 26, acy - math.sin(ang) * 28), (x_end, y_end)], fill=(225, 230, 237), width=6)
        d.line([(acx + math.cos(ang) * 26 + 2, acy - math.sin(ang) * 28), (x_end + 2, y_end)], fill=(250, 252, 255), width=3)

    # 6. Perforated White Ceiling Bow & Roof Liner Swatch (frame_001 & frame_020!)
    cx0, cy0, cx1, cy1 = R_CEIL_WHITE
    d.rectangle([cx0, cy0, cx1, cy1], fill=(234, 238, 243))
    for py in range(cy0 + 24, cy1 - 16, 44):
        d.rectangle([cx0, py - 10, cx1, py + 10], fill=(242, 245, 249), outline=(205, 210, 218))
        for px in range(cx0 + 22, cx1 - 18, 36):
            d.rounded_rectangle([px - 9, py - 4, px + 9, py + 4], radius=3, fill=(142, 148, 158))

    # 7. Pure Alpine White Clean Sheetmetal Swatch (A-pillars, hood, mirror caps/jambs)
    d.rectangle(list(R_WHITE_CLEAN), fill=(245, 247, 250))

    # 8. Charcoal Woven Commercial Seat Upholstery
    sx0, sy0, sx1, sy1 = R_SEAT
    d.rectangle([sx0, sy0, sx1, sy1], fill=(38, 41, 46))
    # Side bolsters darker charcoal + center woven ribs
    d.rectangle([sx0 + 48, sy0 + 24, sx1 - 48, sy1 - 24], fill=(46, 50, 56), outline=(66, 71, 79), width=2)
    for py in range(sy0 + 42, sy1 - 36, 26):
        d.line([(sx0 + 54, py), (sx1 - 54, py)], fill=(32, 35, 40), width=3)
    for px in range(sx0 + 54, sx1 - 50, 8):
        d.line([(px, sy0 + 28), (px, sy1 - 28)], fill=(42, 46, 52), width=1)

    # 9. Full Ducato / ProMaster Commercial Dashboard & Instrument Cluster
    dx0, dy0, dx1, dy1 = R_DASH
    d.rectangle([dx0, dy0, dx1, dy1], fill=(34, 37, 42))
    # Twin gauge dials (left = driver side in cab)
    for gcx in (dx0 + 78, dx0 + 150):
        gcy = dy0 + 76
        d.ellipse([gcx - 28, gcy - 28, gcx + 28, gcy + 28], fill=(16, 18, 22), outline=(165, 172, 182), width=3)
        for a_tick in range(-210, 45, 30):
            ar = math.radians(a_tick)
            d.line([(gcx + math.cos(ar) * 20, gcy + math.sin(ar) * 20),
                    (gcx + math.cos(ar) * 25, gcy + math.sin(ar) * 25)], fill=(230, 235, 242), width=2)
        d.line([(gcx, gcy), (gcx - 14, gcy - 12)], fill=(235, 62, 42), width=3)
    # Center Uconnect / Radio Infotainment Touchscreen + A/C Vents + Rotary Climate Knobs
    d.rounded_rectangle([dx0 + 205, dy0 + 38, dx0 + 318, dy0 + 115], radius=6, fill=(20, 24, 30), outline=(92, 98, 108), width=2)
    d.rectangle([dx0 + 222, dy0 + 48, dx0 + 301, dy0 + 96], fill=(28, 52, 78))
    for k in range(3):
        kx = dx0 + 230 + k * 32
        ky = dy0 + 142
        d.ellipse([kx - 10, ky - 10, kx + 10, ky + 10], fill=(24, 26, 30), outline=(120, 126, 136), width=2)
    # Red hazard triangle button
    d.polygon([(dx0 + 262, dy0 + 166), (dx0 + 252, dy0 + 182), (dx0 + 272, dy0 + 182)], fill=(215, 34, 34))
    # Passenger glovebox outline
    d.rounded_rectangle([dx0 + 220, dy0 + 196, dx1 - 22, dy1 - 18], radius=6, fill=(31, 34, 39), outline=(22, 24, 28), width=2)

    # 10. Matte Black Trim, Brushed Chrome, Engine, Wreck & Ember Swatches
    d.rectangle(list(R_TRIM_BLK), fill=(27, 29, 33))
    cx0, cy0, cx1, cy1 = R_CHROME
    for py in range(cy0, cy1):
        t = (py - cy0) / max(1, cy1 - cy0 - 1)
        v = int(195 + 48 * math.sin(math.pi * t))
        d.line([(cx0, py), (cx1, py)], fill=(v, v + 3, min(255, v + 8)))

    ex0, ey0, ex1, ey1 = R_ENGINE
    d.rectangle([ex0, ey0, ex1, ey1], fill=(24, 26, 30))
    d.rounded_rectangle([ex0 + 48, ey0 + 42, ex1 - 48, ey1 - 52], radius=8, fill=(58, 62, 68), outline=(125, 130, 138), width=3)
    for ry in range(ey0 + 58, ey1 - 64, 22):
        d.line([(ex0 + 60, ry), (ex1 - 60, ry)], fill=(32, 35, 40), width=5)

    # Scorched Wreck & Glowing Ember Swatches
    wx0, wy0, wx1, wy1 = R_WRECK
    d.rectangle([wx0, wy0, wx1, wy1], fill=(32, 29, 27))
    mx0, my0, mx1, my1 = R_EMBER
    for py in range(my0, my1):
        for px in range(mx0, mx1, 8):
            w_em = 0.5 + 0.5 * math.sin(px * 0.05 + math.sin(py * 0.06) * 2.5)
            d.rectangle([px, py, px + 8, py + 1], fill=(int(90 + 165 * w_em), int(25 + 115 * (w_em ** 2)), 12))


def build_van_glass_rgba(size=512, burned=False):
    """Builds 512x512 RGBA texture:
      - Left half  (u: 0.0 .. 0.5): Light green-tinted laminated automotive cab glass w/ black frit border!
      - Right half (u: 0.5 .. 1.0): Cab bulkhead square wire-mesh safety screen (transparent between wires)!"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    half = size // 2

    # 1. Left Half: Cab Laminated Glass (frame_005, frame_009, frame_010!)
    if not burned:
        # Clean, uniform factory green-tinted laminated glass (no fake diagonal white stripe!)
        for py in range(size):
            tf = 1.0 - py / max(1, size - 1)
            al = int(66 + 16 * tf)
            d.line([(0, py), (half - 1, py)], fill=(148, 184, 176, al))
        # Black ceramic frit edge border around perimeter
        d.rectangle([0, 0, half - 1, size - 1], outline=(20, 22, 26, 255), width=11)
    else:
        d.rectangle([0, 0, half - 1, size - 1], fill=(38, 34, 30, 185))
        d.rectangle([0, 0, half - 1, size - 1], outline=(16, 15, 15, 255), width=11)

    # 2. Right Half: Square Steel Wire-Mesh Safety Bulkhead Grille (exact match to frame_020!)
    # Crystal-clear air between wires + crisp 1px dark steel wires so both frame_010 & frame_020 match!
    d.rectangle([half, 0, size - 1, size - 1], fill=(30, 34, 38, 4))
    step = 16
    wire_col = (24, 26, 30, 228) if not burned else (18, 16, 15, 248)
    for gx in range(half, size, step):
        d.line([(gx, 0), (gx, size - 1)], fill=wire_col, width=1)
    for gy in range(0, size, step):
        d.line([(half, gy), (size - 1, gy)], fill=wire_col, width=1)
    # Outer steel frame around mesh panel
    d.rectangle([half, 0, size - 1, size - 1], outline=(24, 26, 30, 255), width=10)
    return im


def build_promaster_van_textures():
    """Returns (intact_rgb_2048, glow_rgb_2048, burn_rgb_2048, burn_glow_rgb_2048, glass_rgba_512, glass_burn_rgba_512)."""
    im = Image.new("RGB", (W_VAN, H_VAN), (28, 30, 34))
    glow = Image.new("RGB", (W_VAN, H_VAN), (0, 0, 0))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow)

    _paint_side_panel(d, gd, R_SIDE_R, is_left=False)
    _paint_side_panel(d, gd, R_SIDE_L, is_left=True)
    _paint_front_panel(d, gd)
    _paint_rear_frame(d, gd)
    _paint_barn_doors(d)
    _paint_wheel_and_tread(d)
    _paint_interior_and_roof(d)

    # Fine subtle micro-grain on dark plastic trim & tires so nothing looks flat plastic
    arr = np.array(im, dtype=np.float32)
    rng = np.random.default_rng(2026)
    noise = rng.normal(0.0, 1.8, size=(H_VAN, W_VAN, 1)).astype(np.float32)
    dark_mask = (arr.mean(axis=2, keepdims=True) < 75.0).astype(np.float32)
    arr = np.clip(arr + noise * (0.35 + 1.15 * dark_mask), 0.0, 255.0)
    im_final = Image.fromarray(arr.astype(np.uint8), "RGB")
    glow_final = glow.filter(ImageFilter.GaussianBlur(radius=3.0))

    # Build scorched/burning variant for Quake CatchFire & Wreck states
    yy, xx = np.mgrid[0:H_VAN, 0:W_VAN].astype(np.float32)
    soot = 0.5 + 0.5 * np.sin(xx * 0.015 + np.cos(yy * 0.019) * 2.4)
    burn_arr = arr * (0.28 + 0.24 * soot[:, :, None])
    burn_arr[:, :, 0] += 18.0 * soot
    burn_arr[:, :, 1] += 7.0 * soot
    burn_im = Image.fromarray(np.clip(burn_arr, 0, 255).astype(np.uint8), "RGB")

    burn_glow = Image.new("RGB", (W_VAN, H_VAN), (0, 0, 0))
    bgd = ImageDraw.Draw(burn_glow)
    bgd.rectangle(list(R_EMBER), fill=(255, 110, 24))
    fx0, fy0, fx1, fy1 = R_FRONT
    bgd.ellipse([fx0 + 110, fy0 + 90, fx1 - 110, fy1 - 80], fill=(235, 85, 16))
    burn_glow = burn_glow.filter(ImageFilter.GaussianBlur(radius=8.0))

    glass_rgba = build_van_glass_rgba(512, burned=False)
    glass_burn_rgba = build_van_glass_rgba(512, burned=True)
    return im_final, glow_final, burn_im, burn_glow, glass_rgba, glass_burn_rgba


if __name__ == "__main__":
    import os
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "vehicles")
    os.makedirs(out_dir, exist_ok=True)
    im, gl, bm, bgl, grgba, gbrgba = build_promaster_van_textures()
    im.save(os.path.join(out_dir, "veh_van_atlas_2k.png"))
    grgba.save(os.path.join(out_dir, "veh_van_glass.png"))
    print("Wrote 2048x2048 veh_van_atlas_2k.png & 512x512 veh_van_glass.png")
