"""Cars as models for bklan2 (exec'd by make_bklan.py before car() is first used, only when BKLAN_V3=1).
The vehicles agent's models (progs/veh_{sedan,coupe,truck,van}.md3, ~3.5k triangles each, centred on the origin, nose on
+x, frame 0 = idle) stand in for the brush cars. Placed with the mod's misc_model (no collision of its own), plus a
player clip box. Cars painted in a colour that matters to a photo (the lime car at 1608 Manning, the KUZZ van) stay brush
cars. A model's colour is fixed (its skin), so the old body colours are not kept."""
import random as _crnd

_KEEP_BODIES = {"bk_lime", "oc_blue"}
_CAR_SIZE = {"sedan": (17.0, 6.8, 5.3), "coupe": (16.0, 6.9, 4.3), "truck": (19.6, 8.2, 7.5), "van": (18.6, 7.7, 7.8)}
_car_rng = _crnd.Random(31)
_car_count = [0]
CAR_KEEP = 0.3                    # share of the old cars that are still placed


def _car_as_model(x, y, along, body, length, pickup):
    if body in _KEEP_BODIES:
        return False
    if _car_rng.random() > CAR_KEEP:                      # "way too many cars" (video, 2026-10-31): most parked cars are left out
        return True
    if pickup:
        kind = "truck"
    else:
        kind = _car_rng.choices(("sedan", "coupe", "van"), (45, 35, 20))[0]
    if kind == "van" and length < 16:
        kind = "sedan"
    L, W, H = _CAR_SIZE[kind]
    sc = 0.9 if length < 14.5 else 1.0
    yaw = (0 if along == "x" else 90) + (180 if _car_rng.random() < 0.5 else 0)
    if os.environ.get("BKLAN_V4"):          # bklan3: "the cars we created that explode if you shoot them" (vehicles.qc)
        ent("misc_vehicle_" + kind, x, y, 0.2, angle=yaw)
        _car_count[0] += 1
        return True
    ent("misc_model", x, y, 0.2, mdl="progs/veh_%s.md3" % kind, angles="0 %d 0" % yaw, scale="%.2f" % sc)
    hl, hw = (L / 2, W / 2) if along == "x" else (W / 2, L / 2)
    box(x - hl * sc, y - hw * sc, 0.7, x + hl * sc, y + hw * sc, H, "clip")      # starts above the origin: a model whose origin is inside solid is lit black
    _car_count[0] += 1
    return True


CAR_AS_MODEL = _car_as_model
