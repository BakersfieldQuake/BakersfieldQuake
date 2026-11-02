"""make_bklan5.py — Standalone generator for maps/bklan5.bsp (Fox Theater + Downtown Bakersfield combined inside bklan4).
Executes make_bklan.py in memory with BKLAN_V3=1, BKLAN_V4=1, BKLAN_V5=1 plus make_bklan_v6.py injected right after v5,
so make_bklan.py and bklan4 remain 100% untouched.

usage: python make_bklan5.py out/maps/bklan5.map
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["BKLAN_V3"] = "1"
os.environ["BKLAN_V4"] = "1"
os.environ["BKLAN_V5"] = "1"

# Default player start at the iconic 20th & H Postcard Corner facing the Fox Marquee & Clock Tower
# unless BKLAN_START="x y z angle" is explicitly provided:
os.environ.setdefault("BKLAN_START", "0 -736 2.8 132")

src_path = os.path.join(HERE, "make_bklan.py")
src = open(src_path, encoding="utf-8").read()

hook = '    exec(open(os.path.join(HERE, "make_bklan_v5.py")).read())\n'
assert hook in src, "make_bklan_v5.py hook not found in make_bklan.py"
inject = hook + '    exec(open(os.path.join(HERE, "make_bklan_v6.py"), encoding="utf-8").read())\n'
src = src.replace(hook, inject, 1)
src = src.replace(
    '"message" "B-LAN 2001 - E 21st St, Bakersfield"',
    '"message" "B-LAN 2001 - Historic Fox Theater & Bakersfield"',
    1,
)

# Upgrade bklan5 directional lighting: replace flat high-minlight wash with crisp golden-hour California sun,
# cool azure sky-dome shadows, raking architectural relief, and deeper contact ambient occlusion (_dirtscale 0.88):
old_light = (
    '    f.write(\'"_minlight" "42"\\n"_minlight_color" "255 245 228"\\n\'\n'
    '            \'"_sunlight" "300"\\n"_sunlight_mangle" "60 -52 0"\\n\'\n'
    '            \'"_sunlight_color" "1 0.94 0.78"\\n\'\n'
    '            \'"_sunlight2" "140"\\n"_sunlight2_color" "0.90 0.92 1"\\n\'\n'
    '            \'"_sunlight3" "55"\\n"_sunlight3_color" "1 0.90 0.72"\\n\'\n'
    '            \'"_sunlight_penumbra" "2"\\n\'\n'
    '            \'"_bounce" "1"\\n"_bouncescale" "0.75"\\n\'\n'
    '            \'"_dirt" "1"\\n"_dirtscale" "0.42"\\n\'\n'
    '            \'"_sunlight_dirt" "0.4"\\n"_sunlight2_dirt" "0.5"\\n\')\n'
)
# Calibrate bklan5 lighting for DarkPlaces 4x overbright (L=46..52 sunlit, L=32..36 shadow => ~1.42:1 gentle contrast,
# zero #FFFFFF roof/stucco blowout, dark-gray asphalt preserved, soft 7-deg penumbra):
new_light = (
    '    f.write(\'"_minlight" "24"\\n"_minlight_color" "226 230 240"\\n\'\n'
    '            \'"_sunlight" "46"\\n"_sunlight_mangle" "132 -46 0"\\n\'\n'
    '            \'"_sunlight_color" "1.0 0.95 0.86"\\n\'\n'
    '            \'"_sunlight2" "62"\\n"_sunlight2_color" "0.88 0.93 1.0"\\n\'\n'
    '            \'"_sunlight3" "18"\\n"_sunlight3_color" "0.96 0.92 0.86"\\n\'\n'
    '            \'"_sunlight_penumbra" "7.0"\\n\'\n'
    '            \'"_bounce" "1"\\n"_bouncescale" "0.32"\\n\'\n'
    '            \'"_dirt" "1"\\n"_dirtscale" "0.34"\\n"_dirtgain" "0.75"\\n"_dirtdepth" "112"\\n\'\n'
    '            \'"_sunlight_dirt" "0.35"\\n"_sunlight2_dirt" "0.45"\\n\')\n'
)
assert old_light in src, "worldspawn lighting block not found in make_bklan.py"
src = src.replace(old_light, new_light, 1)

# Support optional 6th tuple item (pitch) in SPOTS -> bklan5.spots.json for Padre Hotel & Fox Theater views:
old_spots = 'json.dump([{"name": n, "pos": [u(x, OX), u(y, OY), u(z)], "yaw": a} for n, x, y, z, a in SPOTS],'
new_spots = 'json.dump([{"name": r[0], "pos": [u(r[1], OX), u(r[2], OY), u(r[3])], "yaw": r[4], **({"pitch": r[5]} if len(r) > 5 else {})} for r in SPOTS],'
assert old_spots in src, "SPOTS json.dump line not found in make_bklan.py"
src = src.replace(old_spots, new_spots, 1)

ns = dict(globals())
ns["__file__"] = src_path
ns["__name__"] = "__main__"
exec(compile(src, src_path, "exec"), ns)
