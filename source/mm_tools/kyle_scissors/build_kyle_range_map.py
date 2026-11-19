"""Build a clean, bright, wide-open temporary practice & simulation map:
    maps/kyle_range.bsp (+ maps/kyle_range.lit)

Features:
  - Wide sunlit 2048 x 2048 x 960 open-sky courtyard (zero traffic, zero clutter!)
  - Clean concrete/grass arena floor, low perimeter walls, 4 low practice crates/pillars
    (to test throwing Kyle at objects & watching him navigate around them!)
  - Player spawn at south-center facing north toward the open yard & blue sky
  - Paired with KY_RangeThink in kyle.qc which automatically spawns 1 patrolling enemy
    in the yard + 1 circling flying Winged John Bird overhead (both respawn 3s after death)
    and auto-equips The Pocket Kyle!

Run:
    python -I source/mm_tools/kyle_scissors/build_kyle_range_map.py
"""

import subprocess
from pathlib import Path

REPO = Path(r"g:\Quake\Combat\BakersfieldQuake")
ERICW = Path(r"g:\Quake\Combat\tools\ericw")
WAD_PATH = REPO / "source" / "mm_tools" / "morro_rock" / "out" / "morrorock.wad"
OUT_WORK = Path(r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671\scratch\kyle_range")
OUT_WORK.mkdir(parents=True, exist_ok=True)


def brush_box(x0, y0, z0, x1, y1, z1, tex_top, tex_side=None, tex_bot=None):
    if tex_side is None:
        tex_side = tex_top
    if tex_bot is None:
        tex_bot = tex_side
    lines = ["{"]
    # Top (+Z)
    lines.append(f"( {x0} {y1} {z1} ) ( {x1} {y1} {z1} ) ( {x1} {y0} {z1} ) {tex_top} 0 0 0 1 1")
    # Bottom (-Z)
    lines.append(f"( {x0} {y0} {z0} ) ( {x1} {y0} {z0} ) ( {x1} {y1} {z0} ) {tex_bot} 0 0 0 1 1")
    # Left (-X)
    lines.append(f"( {x0} {y1} {z1} ) ( {x0} {y0} {z1} ) ( {x0} {y0} {z0} ) {tex_side} 0 0 0 1 1")
    # Right (+X)
    lines.append(f"( {x1} {y0} {z1} ) ( {x1} {y1} {z1} ) ( {x1} {y1} {z0} ) {tex_side} 0 0 0 1 1")
    # Back (+Y)
    lines.append(f"( {x1} {y1} {z1} ) ( {x0} {y1} {z1} ) ( {x0} {y1} {z0} ) {tex_side} 0 0 0 1 1")
    # Front (-Y)
    lines.append(f"( {x0} {y0} {z1} ) ( {x1} {y0} {z1} ) ( {x1} {y0} {z0} ) {tex_side} 0 0 0 1 1")
    lines.append("}")
    return "\n".join(lines)


def build_map():
    S = 1024  # 2048 x 2048 wide open courtyard
    H = 960   # high open skybox for soaring Sky Throws & Winged John Bird!
    W = 64    # wall thickness
    LOW_WALL = 160

    wad_str = str(WAD_PATH).replace("\\", "/")
    brushes = [
        # Main sunlit asphalt courtyard (crisp contrast for Kyle, chrome scissors & US bills!)
        brush_box(-S, -S, -64, S, S, 0, "mr_asphalt", "mr_asphalt", "mr_asphalt"),
        # Green practice lawn stripes on east & west edges
        brush_box(-S + 32, -S + 32, 0, -S + 288, S - 32, 2, "mr_lawn", "mr_lawn"),
        brush_box(S - 288, -S + 32, 0, S - 32, S - 32, 2, "mr_lawn", "mr_lawn"),
        # Crisp perimeter concrete walls
        brush_box(-S - W, -S - W, -64, -S, S + W, LOW_WALL, "mr_rock_tan", "mr_rock_tan"),
        brush_box(S, -S - W, -64, S + W, S + W, LOW_WALL, "mr_rock_tan", "mr_rock_tan"),
        brush_box(-S, -S - W, -64, S, -S, LOW_WALL, "mr_rock_tan", "mr_rock_tan"),
        brush_box(-S, S, -64, S, S + W, LOW_WALL, "mr_rock_tan", "mr_rock_tan"),
        # Upper skybox enclosure (bright blue Bakersfield bklan_ sky!)
        brush_box(-S - W, -S - W, LOW_WALL, -S, S + W, H, "sky", "sky"),
        brush_box(S, -S - W, LOW_WALL, S + W, S + W, H, "sky", "sky"),
        brush_box(-S, -S - W, LOW_WALL, S, -S, H, "sky", "sky"),
        brush_box(-S, S, LOW_WALL, S, S + W, H, "sky", "sky"),
        brush_box(-S - W, -S - W, H, S + W, S + W, H + W, "sky", "sky"),
        # 3 clean practice blocks/objects (to test throwing Kyle at objects & watching him steer/climb!)
        brush_box(-360, 120, 0, -240, 240, 72, "mr_rock_grey", "mr_rock_tan"),
        brush_box(240, 180, 0, 360, 300, 96, "mr_rock_grey", "mr_rock_tan"),
        brush_box(-80, 560, 0, 80, 640, 56, "mr_rock_grey", "mr_rock_tan"),
    ]

    map_text = f'''{{
"classname" "worldspawn"
"message" "Kyle Tillet Practice Range (Enemy + Flying Bird)"
"wad" "{wad_str}"
"skyname" "bklan_"
"_minlight" "38"
"_minlight_color" "255 245 228"
"_sunlight" "175"
"_sunlight_mangle" "60 -52 0"
"_sunlight_color" "1 0.94 0.78"
"_sunlight2" "75"
"_sunlight2_color" "0.90 0.92 1"
{chr(10).join(brushes)}
}}
{{
"classname" "info_player_start"
"origin" "0 -420 28"
"angle" "90"
}}
{{
"classname" "info_player_deathmatch"
"origin" "0 -420 28"
"angle" "90"
}}
{{
"classname" "info_player_deathmatch"
"origin" "0 -480 28"
"angle" "90"
}}
'''
    map_path = OUT_WORK / "kyle_range.map"
    map_path.write_text(map_text, encoding="ascii")

    print("Compiling kyle_range.map with qbsp + light...")
    subprocess.run([str(ERICW / "qbsp.exe"), "-bsp2", str(map_path)], cwd=str(OUT_WORK), check=True)
    bsp_work = OUT_WORK / "kyle_range.bsp"
    subprocess.run([str(ERICW / "vis.exe"), "-fast", str(bsp_work)], cwd=str(OUT_WORK), check=True)
    subprocess.run([str(ERICW / "light.exe"), str(bsp_work)], cwd=str(OUT_WORK), check=True)

    dst_bsp = REPO / "maps" / "kyle_range.bsp"
    dst_lit = REPO / "maps" / "kyle_range.lit"
    dst_bsp.write_bytes(bsp_work.read_bytes())
    if (OUT_WORK / "kyle_range.lit").exists():
        dst_lit.write_bytes((OUT_WORK / "kyle_range.lit").read_bytes())
    print(f"Installed {dst_bsp} ({dst_bsp.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build_map()
