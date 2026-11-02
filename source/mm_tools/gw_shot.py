"""Screenshots of a goldenwest-style test map from chosen spots without rebuilding it: the info_player_start line in the BSP's entity
lump is rewritten in place (same length, space padded: build the map once with GW_START="-600.5 -250.5 25.5 180" so there is room),
then darkplaces is started on the patched copy and writes BakersfieldQuake/zc_<name>.png.
usage: python gw_shot.py <map name> "name x y z yaw" ...      (feet in the casino frame, yaw in degrees; z 2.2 = standing on the floor)"""
import os
import re
import shutil
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, "..", ".."))
COMBAT = os.path.dirname(GAME)
OY = 1690.0                                                         # the map origin of the goldenwest segment: (-520 + 3900) / 2


def patch(src, dst, x, y, z, yaw):
    d = bytearray(open(src, "rb").read())
    ofs, ln = struct.unpack("<ii", d[4:12])                          # BSP2: magic, then lump 0 = entities
    ent = bytes(d[ofs:ofs + ln])
    m = re.search(rb'"classname" "info_player_start"\s*"origin" "([^"]*)"(\s*"angle" "([^"]*)")?', ent)
    if not m:
        sys.exit("no info_player_start in " + src)
    o_new = ("%d %d %d" % (round(x * 12), round((y - OY) * 12), round(z * 12))).encode()
    a_new = str(int(yaw)).encode()
    if len(o_new) > len(m.group(1)) or (m.group(3) is not None and len(a_new) > len(m.group(3))):
        sys.exit("start placeholder too short: build with GW_START=\"-600.5 -250.5 25.5 180\"")
    new = ent[:m.start(1)] + o_new.ljust(len(m.group(1))) + ent[m.end(1):]
    if m.group(3) is not None:
        s = m.start(3) + 0
        new = new[:s] + a_new.ljust(len(m.group(3))) + new[m.end(3):]
    assert len(new) == len(ent)
    d[ofs:ofs + ln] = new
    open(dst, "wb").write(d)


def main():
    mapname = sys.argv[1]
    mp = os.path.join(HERE, "out", "maps")
    if os.path.exists(os.path.join(GAME, "maps", mapname + ".bsp")):
        sys.exit(mapname + ".bsp is installed in maps/ and would be overwritten and deleted: use a private test map (view_gwc.sh builds gwcasino)")
    for spec in sys.argv[2:]:
        name, x, y, z, yaw = spec.split()
        patch(os.path.join(mp, mapname + ".bsp"), os.path.join(GAME, "maps", mapname + ".bsp"), float(x), float(y), float(z), float(yaw))
        shutil.copy(os.path.join(mp, mapname + ".lit"), os.path.join(GAME, "maps", mapname + ".lit"))
        while b"darkplaces" in subprocess.run(["tasklist"], capture_output=True).stdout.lower():
            time.sleep(3)
        shot = os.path.join(GAME, "zc_%s.png" % name)
        if os.path.exists(shot):
            os.remove(shot)
        p = subprocess.Popen([os.path.join(COMBAT, "darkplaces.exe"), "-window", "-width", "1280", "-height", "720", "-game", "quake15", "-game",
                              "BakersfieldQuake", "+deathmatch", "0", "+coop", "0", "+map", mapname, "+defer", "9", "screenshot zc_%s.png" % name,
                              "+defer", "10", "quit"], cwd=COMBAT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            p.kill()
        print(name, "ok" if os.path.exists(shot) else "NO SHOT")
    for ext in (".bsp", ".lit"):
        try:
            os.remove(os.path.join(GAME, "maps", mapname + ext))
        except OSError:
            pass


if __name__ == "__main__":
    main()
