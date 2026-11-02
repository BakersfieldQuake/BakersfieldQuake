"""union2 / union3: the later segments of the S Union Ave street (the casino is in make_goldenwest.py = "goldenwest").
Each map covers about 4400 ft of the street (a map cannot be wider than +-32768 units), built from OpenStreetMap by gw_route.py
in the same frame as the casino map; trigger_changelevel brushes across the street at both ends link the maps.
usage: GW_SEG="union2 3800 8300" python make_union.py out/maps/union2.map   (see build_union.sh)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(HERE, "gwbase.py"), encoding="utf-8").read(), "gwbase.py", "exec"), globals())

ORDER = ["goldenwest", "union2", "union3"]
THIS = ORDER.index(SEG_NAME) if SEG_NAME in ORDER else 2

with unscaled():
    ROADZ = 1 / U
    WALKZ = 0.5
    exec(compile(open(os.path.join(HERE, "gw_route.py"), encoding="utf-8").read(), "gw_route.py", "exec"), globals())     # (defines CUT)
    _hx0, _hx1, _hy0, _hy1 = HX0, HX1, HY0, HY1
    box(_hx0 - 1, _hy0 - 1, SKY_Z, _hx1 + 1, _hy1 + 1, SKY_Z + 1, "sky_bk")
    for x0, y0, x1, y1 in ((_hx0 - 1, _hy0 - 1, _hx0, _hy1 + 1), (_hx1, _hy0 - 1, _hx1 + 1, _hy1 + 1), (_hx0, _hy1, _hx1, _hy1 + 1),
                           (_hx0, _hy0 - 1, _hx1, _hy0)):
        box(x0, y0, -3, x1, y1, SKY_Z, "sky_bk")
    for x0, y0, x1, y1 in ((_hx0, _hy0, _hx0 + 4, _hy1), (_hx1 - 4, _hy0, _hx1, _hy1), (_hx0, _hy1 - 4, _hx1, _hy1), (_hx0, _hy0, _hx1, _hy0 + 4)):
        box(x0, y0, 0, x1, y1, SKY_Z, "clip")
    if CUT:                                                  # floor and ground in pieces round the trench
        _xl, _xr, _ya, _yb = CUT
        _pieces = ((_hx0 - 1, _hy0 - 1, _xl, _hy1 + 1), (_xr, _hy0 - 1, _hx1 + 1, _hy1 + 1), (_xl, _hy0 - 1, _xr, _ya), (_xl, _yb, _xr, _hy1 + 1))
    else:
        _pieces = ((_hx0 - 1, _hy0 - 1, _hx1 + 1, _hy1 + 1),)
    if CUT:                                                  # one continuous 3 ft floor at -23..-20, ground 20 ft deep round the cut: nothing to leak through
        box(_hx0 - 1, _hy0 - 1, -23, _hx1 + 1, _hy1 + 1, -20, "bk_dirt")
        for x0, y0, x1, y1 in _pieces:
            box(max(x0, _hx0), max(y0, _hy0), -20, min(x1, _hx1), min(y1, _hy1), 0, "gw_dirt", {"t": tspec("gw_dirt", 24)})
        for x0, y0, x1, y1 in ((_hx0 - 1, _hy0 - 1, _hx0, _hy1 + 1), (_hx1, _hy0 - 1, _hx1 + 1, _hy1 + 1), (_hx0, _hy1, _hx1, _hy1 + 1), (_hx0, _hy0 - 1, _hx1, _hy0)):
            box(x0, y0, -23, x1, y1, SKY_Z, "sky_bk")
    else:
        for x0, y0, x1, y1 in _pieces:
            box(x0, y0, -3, x1, y1, -2, "bk_dirt")
            box(max(x0, _hx0), max(y0, _hy0), -2, min(x1, _hx1), min(y1, _hy1), 0, "gw_dirt", {"t": tspec("gw_dirt", 24)})

    # --- links to the neighbouring segments: a changelevel brush across the street at each end
    def brush_ent(cls, x1, y1, z1, x2, y2, z2, **kv):
        GROUPS["_t"] = []
        n = len(SOLIDS)
        box(x1, y1, z1, x2, y2, z2, "bk_dirt", group="_t")
        del SOLIDS[n:]
        ENTS.append('{\n"classname" "%s"\n' % cls + "".join('"%s" "%s"\n' % kv_ for kv_ in kv.items()) + GROUPS.pop("_t")[0] + "}\n")

    cN, cS = _C[-1], _C[0]
    if THIS + 1 < len(ORDER):
        brush_ent("trigger_changelevel", cN - 110, SEG_Y1 - 60, 0, cN + 110, SEG_Y1 - 40, 90, map=ORDER[THIS + 1])
    if THIS > 0:
        brush_ent("trigger_changelevel", cS - 110, SEG_Y0 + 40, 0, cS + 110, SEG_Y0 + 60, 90, map=ORDER[THIS - 1])
    # --- spawns and items along the street (each tried at a few offsets until nothing solid is in the way)
    def _clear(x, y, z0, z1):
        lo, hi = (u(x - 1.4, OX), u(y - 1.4, OY), u(z0)), (u(x + 1.4, OX), u(y + 1.4, OY), u(z1))
        return not any(all(lo[i] < b_[i + 3] and hi[i] > b_[i] for i in range(3)) for b_ in SOLIDS)

    def _put(name, x, y, z, **kv):
        for dx, dy in ((0, 0), (14, 0), (-14, 0), (0, 14), (0, -14), (28, 0), (-28, 0)):
            if _clear(x + dx, y + dy, z - 1.95, z + 2.7):
                ent(name, x + dx, y + dy, z, **kv)
                return True
        return False

    for k, i in enumerate(range(8, len(_ys) - 8, max(1, (len(_ys) - 16) // 9))):
        yy, cc = _ys[i], _C[i]
        side = -1 if k % 2 == 0 else 1
        _put("info_player_deathmatch", cc + side * (HALF_SEP + CW / 2 + 3.5), yy, 2.2, angle=90 if side < 0 else 270)
    for k, i in enumerate(range(20, len(_ys) - 20, max(1, (len(_ys) - 40) // 8))):
        yy, cc = _ys[i], _C[i]
        nm = ("item_health", "weapon_supershotgun", "item_armor1", "weapon_nailgun", "item_shells", "weapon_rocketlauncher", "item_spikes", "item_armor2", "item_health")[k % 9]
        _put(nm, cc + (HALF_SEP + CW / 2 + 3.5) * (-1 if k % 2 else 1), yy + 6, 1.0)
    if os.environ.get("UN_START"):                           # test views: UN_START="x y z yaw" in true feet
        _sx, _sy, _sz, _sa = (float(v) for v in os.environ["UN_START"].split())
        ent("info_player_start", _sx, _sy, _sz, angle=int(_sa))
    else:
        _put("info_player_start", _C[10] - 40, _ys[10], 2.2, angle=90)
    SPOTS = [("South end of " + SEG_NAME, _C[6] - 40, _ys[6], 2.2, 90), ("Middle of " + SEG_NAME, _C[len(_ys) // 2] - 40, _ys[len(_ys) // 2], 2.2, 90),
             ("North end of " + SEG_NAME, _C[-8] - 40, _ys[-8], 2.2, 90)]

out = sys.argv[1]
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
json.dump([{"name": n, "pos": [u(x, OX), u(y, OY), u(z)], "yaw": a} for n, x, y, z, a in SPOTS],
          open(os.path.join(os.path.dirname(os.path.abspath(out)), SEG_NAME + ".spots.json"), "w"))
with open(out, "w") as f:
    f.write('{\n"classname" "worldspawn"\n"wad" "%s;goldenwest.wad;bklan3.wad"\n"message" "S Union Ave, Bakersfield - %s"\n' % (WAD_BK, SEG_NAME))
    f.write('"skyname" "bklan_"\n"_minlight" "28"\n"_sunlight" "115"\n"_sunlight_mangle" "60 -52 0"\n'
            '"_sunlight_color" "1 0.94 0.8"\n"_sunlight2" "65"\n"_sunlight2_color" "0.62 0.8 1"\n"_sunlight_penumbra" "1"\n'
            '"_dirt" "1"\n"_dirtscale" "0.8"\n')
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    f.write('{\n"classname" "func_detail"\n' + "".join(GROUPS["detail"]) + "}\n")
    f.write('{\n"classname" "func_wall"\n' + "".join(GROUPS["fence"]) + "}\n")
    f.write('{\n"classname" "func_detail_illusionary"\n' + "".join(GROUPS["illus"]) + "}\n")
    f.write("".join(ENTS))
if check_placed():
    sys.exit("spawns / items inside brushes")
print("wrote", out, len(GROUPS["world"]), "world +", len(GROUPS["detail"]), "detail +", len(GROUPS["fence"]), "fence,", len(ENTS), "entities")
