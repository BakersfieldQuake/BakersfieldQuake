"""SimReady -> Quake props, second half: turns the JSON written by simready_export.py (Blender) into MD3 models and
their textures for DarkPlaces, placed in the map with the mod's misc_model entity ("mdl" key).
Writes BakersfieldQuake/progs/bklan/<name>.md3 and progs/bklan/t_*.png (colour maps shrunk to 256 px, darkened for
the mod's ~2x scene brightness; materials without a colour map get a flat swatch of their base colour).
python simready_props.py <json dir>
Assets: NVIDIA SimReady (huggingface.co/datasets/nvidia/simready-assets), CC-BY 4.0; decimated and re-textured here."""
import json
import math
import os
import re
import sys

from PIL import Image, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib  # noqa: E402

JSON_DIR = sys.argv[1]
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "progs", "bklan"))
GAIN = 0.55
TEX = 256

# SimReady asset -> prop name in the map
PROPS = {
    "hvac_vent_system_straight_a01": "duct",
    "hvac_vent_system_corner_a01": "duct_bend",
    "climate_heater_electricBox_a01": "heater",
    "lighting_taskLight_suspendedLinearBench_a01": "striplight",
    "chair_office_fabric_manager_a01": "chair_office",
    "warehouse_chair_office_amf_black_a01": "chair_stack",
    "climate_shopFan_pedestal_a01": "fan_pedestal",
    "fireExtinguisher_abc_a03": "extinguisher",
    "trashCan_office_beige_a03": "trashcan",
    "food_beverage_bottledDrink_a01": "soda_bottle",
    "food_beverage_can_b01": "soda_can",
    "dishware_cup_paper_a01": "cup",
    "box_cardboard_large_b01": "box_large",
    "equipment_cord_reel_electric_a01": "cord_reel",
    "drum_steel_a02": "drum",
    "computer_keyboard_a01": "keyboard",
}


# per prop: colour behind see-through parts of a colour map, and flat colours for glass (OmniGlass imports with the
# wrong texture)
BACKING = {"soda_bottle": (52, 22, 12)}
GLASS = {"soda_bottle": (52, 22, 12)}


def srgb(c):
    return int(255 * max(0.0, min(1.0, c)) ** (1 / 2.2))


def udim_atlas(pattern, cols, rows):
    """UDIM colour maps (name.<UDIM>.png, one material spanning several tiles): the tiles side by side in one 128 px
    per tile atlas. Returns the shader name."""
    base = re.sub(r"(_tile)?_alb(edo)?$", "", os.path.splitext(os.path.basename(pattern))[0].replace(".<UDIM>", ""), flags=re.I)
    name = ("t_" + base.replace("t_", "", 1) + "_atlas").replace(".", "_")
    path = os.path.join(OUT, name[:50] + ".png")
    if not os.path.exists(path):
        T = 128
        atlas = Image.new("RGB", (cols * T, rows * T), (60, 60, 60))
        for r in range(rows):
            for c in range(cols):
                f = pattern.replace("<UDIM>", str(1001 + c + 10 * r))
                if os.path.exists(f):
                    atlas.paste(Image.open(f).convert("RGB").resize((T, T), Image.LANCZOS), (c * T, (rows - 1 - r) * T))
        ImageEnhance.Brightness(atlas).enhance(GAIN).save(path)
    return "progs/bklan/" + name[:50]


def texture(mat, prop):
    """Writes the material's texture once, returns its shader name (progs/bklan/t_...)."""
    if "glass" in mat["name"].lower() and "trans" in mat["name"].lower():
        mat = dict(mat, image=None, color=[(c / 255) ** 2.2 for c in GLASS.get(prop, (60, 70, 72))])
    if mat["image"] and os.path.exists(mat["image"]):
        base = re.sub(r"(_tile)?_alb$", "", os.path.splitext(os.path.basename(mat["image"]))[0])
        name = ("t_" + base.replace("t_", "", 1)).replace(".", "_")
        path = os.path.join(OUT, name + ".png")
        if not os.path.exists(path):
            src = Image.open(mat["image"])
            if src.mode == "RGBA" and prop in BACKING:            # label on a see-through sheet: lay it on the drink
                bg = Image.new("RGBA", src.size, BACKING[prop] + (255,))
                bg.alpha_composite(src)
                src = bg
            im = src.convert("RGB")
            im.thumbnail((TEX, TEX), Image.LANCZOS)
            ImageEnhance.Brightness(im).enhance(GAIN).save(path)
    else:
        rgb = tuple(srgb(c) for c in mat["color"])
        name = "t_flat_%02x%02x%02x" % rgb
        path = os.path.join(OUT, name + ".png")
        if not os.path.exists(path):
            ImageEnhance.Brightness(Image.new("RGB", (8, 8), rgb)).enhance(GAIN).save(path)
    return "progs/bklan/" + name[:50]


def main():
    os.makedirs(OUT, exist_ok=True)
    targets = dict(PROPS)
    if "--all" in sys.argv:                                       # every other exported asset becomes sr_<asset>; the PROPS ones are left alone
        targets = {f[:-5]: "sr_" + f[:-5] for f in sorted(os.listdir(JSON_DIR)) if f.endswith(".json") and f[:-5] not in PROPS}
    for asset, prop in targets.items():
        p = os.path.join(JSON_DIR, asset + ".json")
        if not os.path.exists(p):
            print("missing", asset)
            continue
        d = json.load(open(p))
        surfaces = []
        ext = {}                                                   # UDIM colour map -> columns, rows its UVs cover
        for s in d["surfaces"]:
            im = s["material"]["image"] or ""
            if "<UDIM>" in im and s["tris"]:
                e = ext.setdefault(im, [1, 1])
                e[0] = max(e[0], min(10, math.ceil(max(t[0] for t in s["st"]) - 1e-4)))
                e[1] = max(e[1], math.ceil(max(1.0 - t[1] for t in s["st"]) - 1e-4))
        for i, s in enumerate(d["surfaces"]):
            if not s["tris"]:
                continue
            st, im = s["st"], s["material"]["image"] or ""
            if im in ext:
                cols, rows = ext[im]
                shader = udim_atlas(im, cols, rows)
                st = [[t[0] / cols, 1.0 - (1.0 - t[1]) / rows] for t in st]
            else:
                shader = texture(s["material"], prop)
            surfaces.append(dict(name="s%d" % i, shader=shader, tris=[tuple(t) for t in s["tris"]],
                                 st=[tuple(t) for t in st],
                                 frames=[([tuple(v) for v in s["verts"]], [tuple(n) for n in s["norms"]])]))
        md3lib.write(os.path.join(OUT, prop + ".md3"), dict(name=prop, surfaces=surfaces))
        print("%-14s %5d tris  size %s" % (prop, d["tris"], [round(v) for v in d["size"]]))


if __name__ == "__main__":
    main()
