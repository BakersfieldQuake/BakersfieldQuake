"""Shared exact dimensions & UV projection math for BakersfieldQuake's 4 Unique 3D Vehicles.
Imported by BOTH blender_build_vehicles.py (Blender 5.2 mesh builder) and veh_textures.py
(1024x1024 PIL texture painter) so every door shutline, window frame, headlight, grille,
taillight, license plate, bumper, and wheel rim aligns to sub-pixel accuracy!
"""

W_ATLAS = 1024
H_ATLAS = 1024

# Atlas pixel rectangles (x0, y0, x1, y1) — top-left origin (0, 0) -> UV = (x / 1024, y / 1024)
RECT_SIDE     = (16,   14,  624, 274)   # u: 0.0156..0.6094, v: 0.0137..0.2676
RECT_TOP      = (16,  302,  624, 530)   # u: 0.0156..0.6094, v: 0.2949..0.5176
RECT_FRONT    = (652,  14, 1012, 260)   # u: 0.6367..0.9883, v: 0.0137..0.2539
RECT_REAR     = (652, 286, 1012, 532)   # u: 0.6367..0.9883, v: 0.2793..0.5195
RECT_WHEEL    = (0,   544,  256, 800)   # center = (128, 672), R_tire = 118
RECT_TREAD    = (256, 544,  512, 800)
RECT_GLASS    = (512, 544,  800, 800)
RECT_CHROME   = (800, 544, 1024, 670)
RECT_TRIM     = (800, 672, 1024, 800)
RECT_ENGINE   = (0,   800,  256, 1024)
RECT_INTERIOR = (256, 800,  512, 1024)
RECT_INT_FLOOR= (256, 800,  384,  912)   # Ribbed anti-skid metal cargo floor
RECT_INT_DASH = (384, 800,  512,  912)   # Speedometer, tach, gauges, stereo, vents, glovebox
RECT_INT_SEAT = (256, 912,  384, 1024)   # High-back bucket seat charcoal woven upholstery
RECT_INT_WALL = (384, 912,  512, 1024)   # Stamped structural ribs, tie-down rails & kick panels
RECT_WRECK    = (512, 800,  768, 1024)
RECT_EMBER    = (768, 800, 1024, 1024)


def get_spec(kind):
    if kind == "truck":
        # Heavy-Duty Extended-Cab 4x4 Pickup Truck
        return dict(
            kind="truck",
            x0=-114.0, x1=114.0, hw=41.0,
            z_bot=11.5, z_bmp=21.7, z_belt=44.5, z_roof=75.0,
            z_nose_top=41.5, z_rear_top=44.5,
            wheel_x_f=68.0, wheel_x_r=-64.0, wheel_y=36.5, wheel_r=16.5, wheel_w=11.5,
            dish=2.8, rim_ratio=0.60, arch_r=21.0, flare=2.5,
            x_cowl=40.0, x_cab_rear=-20.0,
            x_door0=-2.0, x_door1=37.0,
            x_roof0=-18.0, x_roof1=19.0, y_roof=31.5,
            x_bed_f=-22.0, x_bed_r=-110.0,
        )
    elif kind == "sedan":
        # Late-90s Boxy 4-Door Street Sedan
        return dict(
            kind="sedan",
            x0=-98.0, x1=98.0, hw=36.0,
            z_bot=8.0, z_bmp=18.2, z_belt=34.0, z_roof=56.0,
            z_nose_top=30.0, z_rear_top=35.0,
            wheel_x_f=57.0, wheel_x_r=-55.0, wheel_y=32.5, wheel_r=13.0, wheel_w=8.5,
            dish=1.5, rim_ratio=0.64, arch_r=16.5, flare=1.2,
            x_cowl=34.0, x_cab_rear=-48.0,
            x_door0=-4.0, x_door1=31.0,
            x_roof0=-31.0, x_roof1=11.0, y_roof=27.8,
            x_trunk_f=-48.0, x_trunk_r=-95.0,
        )
    elif kind == "van":
        # Accurate Ram ProMaster High-Roof Cargo Van (Walk-In Interior matching reference video)
        return dict(
            kind="van",
            x0=-112.0, x1=108.0, hw=40.0,
            z_bot=8.5, z_bmp=20.0, z_belt=47.0, z_roof=89.5,
            z_nose_top=38.5, z_rear_top=88.5,
            wheel_x_f=64.0, wheel_x_r=-58.0, wheel_y=35.8, wheel_r=15.0, wheel_w=9.5,
            dish=1.8, rim_ratio=0.61, arch_r=18.5, flare=1.8,
            x_cowl=48.0, x_cab_rear=-105.0,
            x_door0=12.0, x_door1=46.0,
            x_roof0=-106.0, x_roof1=22.0, y_roof=36.0,
            z_interior_floor=18.0, z_interior_roof=84.0,
        )
    elif kind == "coupe":
        # Early-2000s 2-Door Tuner Sport Coupe / Fastback
        return dict(
            kind="coupe",
            x0=-92.0, x1=92.0, hw=36.5,
            z_bot=6.2, z_bmp=14.4, z_belt=31.0, z_roof=50.5,
            z_nose_top=25.5, z_rear_top=33.5,
            wheel_x_f=54.0, wheel_x_r=-52.0, wheel_y=32.8, wheel_r=12.6, wheel_w=9.2,
            dish=2.5, rim_ratio=0.68, arch_r=15.8, flare=2.0,
            x_cowl=28.0, x_cab_rear=-66.0,
            x_door0=-16.0, x_door1=25.0,
            x_roof0=-24.0, x_roof1=3.0, y_roof=26.8,
        )
    raise ValueError(kind)


def clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


# --- Exact World <-> Pixel / UV Mappers ---
def side_world_to_px(sp, x, z):
    rx0, ry0, rx1, ry1 = RECT_SIDE
    tx = clamp01((x - sp["x0"]) / (sp["x1"] - sp["x0"]))
    tz = clamp01((z - sp["z_bot"]) / (sp["z_roof"] - sp["z_bot"]))
    return (rx0 + (rx1 - rx0) * tx, ry1 - (ry1 - ry0) * tz)


def side_uv(sp, x, z):
    px, py = side_world_to_px(sp, x, z)
    return (round(px / W_ATLAS, 4), round(py / H_ATLAS, 4))


def top_world_to_px(sp, x, y):
    rx0, ry0, rx1, ry1 = RECT_TOP
    tx = clamp01((x - sp["x0"]) / (sp["x1"] - sp["x0"]))
    ty = clamp01((y + sp["hw"]) / (2.0 * sp["hw"]))
    return (rx0 + (rx1 - rx0) * tx, ry0 + (ry1 - ry0) * ty)


def top_uv(sp, x, y):
    px, py = top_world_to_px(sp, x, y)
    return (round(px / W_ATLAS, 4), round(py / H_ATLAS, 4))


def front_world_to_px(sp, y, z):
    rx0, ry0, rx1, ry1 = RECT_FRONT
    # Looking at front of car (viewer at +X looking -X, up +Z): viewer's LEFT is -Y, viewer's RIGHT is +Y!
    ty = clamp01((y + sp["hw"]) / (2.0 * sp["hw"]))
    tz = clamp01((z - sp["z_bot"]) / (sp["z_nose_top"] - sp["z_bot"]))
    return (rx0 + (rx1 - rx0) * ty, ry1 - (ry1 - ry0) * tz)


def front_uv(sp, y, z):
    px, py = front_world_to_px(sp, y, z)
    return (round(px / W_ATLAS, 4), round(py / H_ATLAS, 4))


def rear_world_to_px(sp, y, z):
    rx0, ry0, rx1, ry1 = RECT_REAR
    # Looking at rear of car (viewer at -X looking +X, up +Z): viewer's LEFT is +Y, viewer's RIGHT is -Y!
    ty = clamp01((sp["hw"] - y) / (2.0 * sp["hw"]))
    tz = clamp01((z - sp["z_bot"]) / (sp["z_rear_top"] - sp["z_bot"]))
    return (rx0 + (rx1 - rx0) * ty, ry1 - (ry1 - ry0) * tz)


def rear_uv(sp, y, z):
    px, py = rear_world_to_px(sp, y, z)
    return (round(px / W_ATLAS, 4), round(py / H_ATLAS, 4))


def rect_uv(rect, su, sv):
    x0, y0, x1, y1 = rect
    pad = 4.0
    px = (x0 + pad) + (x1 - x0 - 2.0 * pad) * clamp01(su)
    py = (y0 + pad) + (y1 - y0 - 2.0 * pad) * clamp01(sv)
    return (round(px / W_ATLAS, 4), round(py / H_ATLAS, 4))
