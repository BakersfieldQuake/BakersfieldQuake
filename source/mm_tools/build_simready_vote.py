"""Builds simready_vote.html: a one-file gallery of the NVIDIA SimReady assets (two Blender workbench renders each) where
you vote Yes / Maybe / No per asset for the bklan map. Votes live in the browser (localStorage) and export as text/JSON.
python build_simready_vote.py <thumbs dir with <asset>_a.jpg/_b.jpg + meta.json> <out.html>"""
import base64
import html
import json
import os
import sys

THUMBS, OUT = sys.argv[1], sys.argv[2]
meta = json.load(open(os.path.join(THUMBS, "meta.json")))

CATS = [  # (prefix list, label)
    (("vehicle_forklift", "palletJack", "tiltTruck", "handTruck", "cart_", "vehicleSupport", "carFrame"), "Vehicles and trucks"),
    (("pallet", "warehouse_pallet", "crate", "box_", "drum", "warehouse_barrel", "ibcTank", "hopper"), "Pallets, crates, drums"),
    (("rack", "shelve", "storage_shelf", "warehouse_palletHolder"), "Racks and shelving"),
    (("desk", "chair", "warehouse_chair", "cabinet", "facilityFurniture", "storage_locker", "sofa", "table", "furniture",
      "warehouse_packingTable", "computer", "machine_coffee", "water_cooler", "trashCan"), "Office and furniture"),
    (("ladder", "scaffold", "conveyor", "warehouse_conveyor", "barrier", "rail", "ramp", "machineGuard", "wire_machineGuard"), "Site and yard gear"),
    (("fire", "safety", "sign", "tape", "warehouse_EF", "warehouse_fire", "lamp", "lighting", "hvac"), "Safety, lights, services"),
]


def cat(name):
    for prefixes, label in CATS:
        if name.startswith(prefixes):
            return label
    return "Other"


# asset -> where it would go (my pick), and a note
PICK = {
    "vehicle_forklift_red_c01": "yards, GCI rental, LMC dock", "vehicle_forklift_blue_c01": "yards, GCI rental",
    "vehicle_forklift_orange_a01": "130A, LMC dock (walkie stacker)",
    "palletJack_lowProfile_a01": "130A, yards", "handTruck_convertible_aluminum_a04": "130A, LMC dock",
    "tiltTruck_gray_a05": "yards", "pallet_wood_wing_a01": "everywhere", "warehouse_pallet_a01": "everywhere (304 tris)",
    "pallet_block_a01": "yards", "crate_plywood_a04": "130A, yards", "crate_plywood_b01": "130A, yards",
    "carFrame_car_frame_assembled_a01": "body shop, Performance Driveline, salvage", "vehicleSupport_floor_jack_a01": "body shop",
    "ladder_rolling_yellow_a02": "GCI rental, shops", "scaffold_rolling_steel_a01": "GCI rental, body shop",
    "furniture_workbench_modular_a01": "body shop", "drum_plastic_blue_a01": "paint supply, shops", "drum_steel_a01": "yards",
    "ibcTank_steel_stainless_a01": "paint supply, yards", "rack_large_empty_a01": "130A back room, LMC",
    "shelve_steel_heavyDuty_a06": "LMC, J Appliances", "computer_desktop_tower_a01": "130A PC rows",
    "computer_monitor_office_a01": "130A PC rows", "computer_printer_office_a01": "130A", "table_metal_stainless_a03": "130A tables",
    "safety_firstAidCabinet_wallMounted_a01": "130A wall", "sign_wetFloor_a01": "130A", "warehouse_EF_electricPanel_a01": "130A wall",
    "warehouse_fireAlarmLight_a01": "130A wall", "lamp_ceiling_1m_rectangle_a01": "fluorescent fixtures",
}
IN_MAP = {  # already in bklan as a prop
    "fireProtection_extinguisher_portable_a01": "extinguisher", "chair_office_fabric_manager_a01": "chair_office",
    "warehouse_chair_office_amf_black_a01": "chair_stack", "hvac_vent_system_straight_a01": "duct", "trashCan_office_beige_a03": "trashcan",
}
NOTES = {
    "vehicle_forklift_orange_a01": "Walkie pallet stacker, not a sit-down forklift. Same model as the blue a01.",
    "vehicle_forklift_blue_a01": "Walkie pallet stacker. Same model as the orange a01.",
    "vehicle_forklift_blue_c01": "Real sit-down LPG forklift (about 1M tris raw). Same model as the red c01.",
    "vehicle_forklift_red_c01": "Real sit-down LPG forklift (about 1M tris raw). Same model as the blue c01.",
    "vehicle_forklift_red_b01": "Reach / order-picker truck, not a regular forklift.",
    "tiltTruck_gray_a01": "Tilt-dump bin cart (laundry/trash style), not a vehicle.",
    "carFrame_car_frame_assembled_a01": "2.8M triangles raw; decimates fine, it is a plain frame.",
    "storage_shelf_basic_a01": "1.3M triangles raw; thin members may decimate badly.",
    "facilityFurniture_lockerUnit_multiDoor_a01": "1.9M triangles raw.",
    "tape_safety_yellow_black_12m15cm_f06": "12 triangles: a flat strip. A floor texture does this better.",
}


def ft(m):
    inches = round(m * 39.3701)
    return f"{inches // 12}'{inches % 12}\"" if inches >= 12 else f'{inches}"'


def img(name, tag):
    p = os.path.join(THUMBS, f"{name}_{tag}.jpg")
    return "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()


items = []
for name in sorted(meta):
    m = meta[name]
    items.append(dict(id=name, cat=cat(name), a=img(name, "a"), b=img(name, "b"),
                      dims=f"{ft(m['w'])} x {ft(m['d'])} x {ft(m['h'])} (W x D x H)", tris=m["tris"], tex=m["tex"],
                      pick=PICK.get(name, ""), inmap=IN_MAP.get(name, ""), note=NOTES.get(name, "")))

TEMPLATE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "simready_vote_template.html"), encoding="utf-8").read()
open(OUT, "w", encoding="utf-8").write(TEMPLATE.replace("/*DATA*/[]", json.dumps(items)))
print("wrote", OUT, len(items), "assets", round(os.path.getsize(OUT) / 1e6, 1), "MB")
