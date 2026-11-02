"""Builds maps/vehtest.bsp: an open parking-lot vehicle showcase & explosion test map
with all 4 unique shootable/explodable 3D vehicles (misc_vehicle_truck, misc_vehicle_sedan,
misc_vehicle_van, misc_vehicle_coupe) in a front showcase lineup plus a closely-parked
north row for testing domino chain-reaction explosions.
"""
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(HERE, "out")
os.makedirs(OUT_DIR, exist_ok=True)

WAD = "G:/Quake/QBJ3/qbj3/mapsrc/dev_tools_kebby.wad"
ERICW = r"D:\vibe\quake1opensource\tools\ericw"


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def face(p0, p1, p2, outward, tex):
    n = cross(sub(p0, p1), sub(p2, p1))
    if sum(n[i] * outward[i] for i in range(3)) < 0:
        p0, p2 = p2, p0
    pts = " ".join("( %d %d %d )" % p for p in (p0, p1, p2))
    return "%s %s 0 0 0 1 1\n" % (pts, tex)


def box(x1, y1, z1, x2, y2, z2, tex, top=None):
    top = top or tex
    s = "{\n"
    s += face((x1, y1, z1), (x1, y2, z1), (x1, y1, z2), (-1, 0, 0), tex)
    s += face((x2, y1, z1), (x2, y1, z2), (x2, y2, z1), (1, 0, 0), tex)
    s += face((x1, y1, z1), (x1, y1, z2), (x2, y1, z1), (0, -1, 0), tex)
    s += face((x1, y2, z1), (x2, y2, z1), (x1, y2, z2), (0, 1, 0), tex)
    s += face((x1, y1, z1), (x2, y1, z1), (x1, y2, z1), (0, 0, -1), tex)
    s += face((x1, y1, z2), (x1, y2, z2), (x2, y1, z2), (0, 0, 1), top)
    return s + "}\n"


def main():
    H = 1408
    Z = 704
    T = 32
    brushes = [
        box(-H - T, -H - T, -T, H + T, H + T, 0, "02_grey", "02_grey"),    # dark asphalt lot floor
        box(-H - T, -H - T, Z, H + T, H + T, Z + T, "21_blue"),            # sky-blue ceiling
        box(-H - T, -H - T, 0, -H, H + T, Z, "32_check"),
        box(H, -H - T, 0, H + T, H + T, Z, "32_check"),
        box(-H, -H - T, 0, H, -H, Z, "32_check"),
        box(-H, H, 0, H, H + T, Z, "32_check"),
        # Low parking-lot curb islands at far edges
        box(-H, -H, 0, -H + 96, H, 12, "96_bright"),
        box(H - 96, -H, 0, H, H, 12, "96_bright"),
    ]

    ents = []
    ents.append('{\n"classname" "info_player_start"\n"origin" "-340 0 28"\n"angle" "0"\n}\n')
    for i in range(6):
        ang = i * 60
        x = round(-520 + 260 * math.cos(math.radians(ang)))
        y = round(260 * math.sin(math.radians(ang)))
        ents.append('{\n"classname" "info_player_deathmatch"\n"origin" "%d %d 28"\n"angle" "0"\n}\n' % (x, y))

    # Front Showcase Row: all 4 unique vehicles angled in scenic 3/4 view ahead of player!
    showcase = [
        ("misc_vehicle_truck", 135, -265, 208),
        ("misc_vehicle_sedan",  95,  -88, 194),
        ("misc_vehicle_van",    95,   88, 166),
        ("misc_vehicle_coupe", 135,  265, 152),
    ]
    for cname, vx, vy, vang in showcase:
        ents.append('{\n"classname" "%s"\n"origin" "%d %d 8"\n"angles" "0 %d 0"\n}\n' % (cname, vx, vy, vang))

    # North Domino Chain-Reaction Row: closely parked side-by-side!
    chain_row = [
        ("misc_vehicle_truck", -195, 860, 270),
        ("misc_vehicle_sedan",  -65, 860, 270),
        ("misc_vehicle_van",     65, 860, 270),
        ("misc_vehicle_coupe",  195, 860, 270),
    ]
    for cname, vx, vy, vang in chain_row:
        ents.append('{\n"classname" "%s"\n"origin" "%d %d 8"\n"angles" "0 %d 0"\n}\n' % (cname, vx, vy, vang))

    # Weapons & ammo right beside player start
    pickups = [
        ("weapon_supershotgun",    -280, -140),
        ("weapon_rocketlauncher",  -280,  140),
        ("weapon_grenadelauncher", -380,  140),
        ("item_shells",            -220, -190),
        ("item_rockets",           -220,  190),
        ("item_rockets",           -170,  190),
        ("item_armorInv",          -440,    0),
    ]
    for cname, px, py in pickups:
        ents.append('{\n"classname" "%s"\n"origin" "%d %d 24"\n}\n' % (cname, px, py))

    # Balanced lighting calibrated for DarkPlaces 2.5x HDR scene brightness
    for lx in (-850, 0, 850):
        for ly in (-850, 0, 850):
            ents.append('{\n"classname" "light"\n"origin" "%d %d 560"\n"light" "460"\n}\n' % (lx, ly))

    map_path = os.path.join(OUT_DIR, "vehtest.map")
    bsp_path = os.path.join(OUT_DIR, "vehtest.bsp")
    with open(map_path, "w", encoding="ascii") as f:
        f.write('{\n"classname" "worldspawn"\n"wad" "%s"\n"message" "Bakersfield Parking Lot - Shootable Vehicles"\n"_minlight" "62"\n' % WAD)
        f.write("".join(brushes))
        f.write("}\n")
        f.write("".join(ents))
    print(f"Wrote {map_path}")

    for tool, args in [("qbsp.exe", [map_path, bsp_path]), ("vis.exe", [bsp_path]), ("light.exe", [bsp_path])]:
        r = subprocess.run([os.path.join(ERICW, tool)] + args, cwd=OUT_DIR)
        if r.returncode != 0:
            sys.exit(f"{tool} failed with code {r.returncode}")

    dest_dir = os.path.join(MOD_DIR, "maps")
    os.makedirs(dest_dir, exist_ok=True)
    dest_bsp = os.path.join(dest_dir, "vehtest.bsp")
    shutil.copy(bsp_path, dest_bsp)
    print(f"Installed {dest_bsp} ({os.path.getsize(dest_bsp) // 1024} KB)")


if __name__ == "__main__":
    main()
