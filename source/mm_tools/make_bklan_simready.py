# exec'd by make_bklan.py after the ORCOM merge: yard and shop clutter from the 94 NVIDIA SimReady assets
# (simready_props.py --all writes progs/bklan/sr_<asset>.md3 + textures). Everything here is the "plausible
# clutter" kind (salvage yard, body shop yard, 121 E 21st dirt yard, GCI rental yard, the LAN lot's back wall):
# nothing is put inside Unit 130A or the ORCOM hall, whose contents are taken from the footage.
# Positions are map feet. Every prop is checked against the brushes already placed and skipped (with a printed
# line) if it would sit inside one.
import math

_SR_BB = {}


def _sr_bounds(name):
    """(dx, dy, dz) of the MD3 in feet, or None when the model has not been built."""
    if name not in _SR_BB:
        p = os.path.join(HERE, "..", "..", "progs", "bklan", "sr_%s.md3" % name)
        if not os.path.exists(p):
            p = os.path.join(HERE, "..", "..", "..", "_bakersfield_dev", "staged_assets", "progs", "bklan", "sr_%s.md3" % name)
        if not os.path.exists(p):
            _SR_BB[name] = None
        else:
            import md3lib
            vs = [v for s in md3lib.read(p)["surfaces"] for v in s["frames"][0][0]]
            _SR_BB[name] = tuple((max(v[i] for v in vs) - min(v[i] for v in vs)) / 12.0 for i in range(3))
    return _SR_BB[name]


def sr(name, x, y, z=0.0, yaw=0, clip=None, scale=None):
    """One SimReady prop at its base centre (x, y, z). clip=True puts a player clip box round it (default: for
    anything over 2 ft tall); the box follows the rotated footprint."""
    bb = _sr_bounds(name)
    if bb is None:
        print("SR missing model", name)
        return False
    s = scale or 1.0
    a = math.radians(yaw)
    hx = (abs(math.cos(a)) * bb[0] + abs(math.sin(a)) * bb[1]) * s / 2
    hy = (abs(math.sin(a)) * bb[0] + abs(math.cos(a)) * bb[1]) * s / 2
    h = bb[2] * s
    lo = (u(x - hx, OX), u(y - hy, OY), u(z) + 1)
    hi = (u(x + hx, OX), u(y + hy, OY), u(z + h))
    for b in SOLIDS:
        if b[5] > 14 and all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)):
            print("SR blocked %s at %d %d by brush %s" % (name, x, y, tuple(int(q) for q in b)))
            return False
    kv = {"mdl": "progs/bklan/sr_%s.md3" % name, "angles": "0 %d 0" % (yaw % 360)}
    if scale:
        kv["scale"] = scale
    ent("misc_model", x, y, z + 0.15, **kv)                  # origin a hair above the ground slab: inside it the model light sample is black
    if clip is None:
        clip = h > 2.0
    if clip:
        box(x - hx, y - hy, z, x + hx, y + hy, z + min(h, 8), "clip")
    return True


def sr_stack(name, x, y, n, yaw=0, step=0.42, **kw):
    for k in range(n):
        sr(name, x, y, k * step, yaw + (k * 7) % 11 - 5, clip=False, **kw)


# ---- the salvage yard (x -185..-96, y 189..368): a stripped car body, a forklift, pallets, drums
sr("carFrame_car_frame_assembled_a01", -152, 270, 0, 20)
sr("vehicleSupport_floor_jack_a01", -138, 266, 0, 130)
sr("vehicle_forklift_red_c01", -112, 300, 0, 100)
sr("handTruck_convertible_aluminum_a04", -125, 202, 0, 200)
sr_stack("pallet_wood_wing_a01", -105, 215, 3)
sr_stack("pallet_block_a01", -104, 222, 2)
sr("warehouse_pallet_a01", -108, 230, 0, 15, clip=False)
for dx, dy, yw in ((-103, 340, 0), (-101, 342.5, 40), (-104.5, 344, 80)):
    sr("drum_steel_a01", dx, dy, 0, yw)
sr("drum_plastic_blue_a01", -100, 336, 0, 0)
sr("ibcTank_steel_stainless_a01", -103, 320, 0, 10)
sr("crate_plywood_b01", -180, 350, 0, 10)
sr("crate_plywood_a04", -178, 356, 0, 350)
sr("scaffold_rolling_steel_a01", -180, 310, 0, 90)
sr("box_cardboard_large_a02", -128, 355, 0, 25)

# ---- the body shop yard between Building 45 and the north warehouse (x -88..-39, y 185..229)
sr("carFrame_car_frame_assembled_a01", -72, 210, 0, 90)
sr("furniture_workbench_modular_a01", -84, 224, 0, 0)
sr("vehicleSupport_floor_jack_a01", -70, 198, 0, 30)
sr("drum_steel_a01", -85, 196, 0, 0)
sr("drum_steel_a01", -83.5, 197.5, 0, 60)
sr("ladder_rolling_yellow_a02", -62, 223, 0, 270)
sr("table_metal_stainless_a03", -58, 190, 0, 0)

# ---- 121 E 21st's dirt yard (x -280..-144, y -180..-27), west of the grey trailer
sr("vehicle_forklift_blue_c01", -262, -140, 0, 35)
sr_stack("pallet_wood_wing_a01", -165, -150, 4)
sr_stack("warehouse_pallet_a01", -160, -146, 3, step=0.5)
sr("crate_plywood_b01", -175, -165, 0, 20)
sr("crate_plywood_a04", -150, -170, 0, 80)
for dx, dy, yw in ((-270, -170, 0), (-268, -172.5, 50), (-272, -173, 10)):
    sr("drum_steel_a01", dx, dy, 0, yw)
sr("ibcTank_steel_stainless_a01", -250, -170, 0, 0)
sr("handTruck_convertible_aluminum_a04", -255, -60, 0, 100)
sr("tiltTruck_gray_a05", -270, -90, 0, 20)
sr("ladder_step_rolling_a01", -150, -100, 0, 300)

# ---- the GCI equipment rental yard (x -486..-336, y 23..190): free strip behind the boom lifts
sr("scaffold_rolling_steel_a01", -460, 160, 0, 0)
sr("scaffold_rolling_steel_a01", -440, 160, 0, 15)
sr("ladder_rolling_yellow_a02", -420, 165, 0, 90)
sr("ladder_rolling_yellow_a02", -415, 165, 0, 70)
sr("vehicle_forklift_red_c01", -390, 160, 0, 270)
sr_stack("pallet_wood_wing_a01", -360, 172, 3)
sr("palletJack_lowProfile_a01", -350, 150, 0, 40)
sr("palletJack_heavyDuty_a01", -346, 154, 0, 80)
sr("ladder_step_rolling_a01", -372, 168, 0, 200)

# ---- the LAN lot's back wall (2001: dumpster and a drum by the wall)
sr_stack("pallet_wood_wing_a01", -115, 181, 3)
sr("crate_plywood_a04", -123, 181, 0, 10)
sr("pallet_collar_wood_a06", -128, 181, 0, 0, clip=False)
sr("handTruck_convertible_aluminum_a04", -93, 181, 0, 250)

# ---- the west lot between J Appliances and Building 76 (x -270..-232)
sr("palletJack_scale_a01", -255, 60, 0, 60)
sr("vehicle_forklift_orange_a01", -240, 80, 0, 200)
sr_stack("pallet_block_a02", -262, 100, 2, step=0.46)
