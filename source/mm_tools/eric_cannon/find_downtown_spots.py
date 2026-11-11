import math
import os
import re
import struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class BSPInspector:
    def __init__(self, rel_path):
        self.path = os.path.join(ROOT, rel_path)
        self.raw = open(self.path, "rb").read()
        self.is_bsp2 = (self.raw[:4] == b"BSP2")
        self.lumps = [struct.unpack_from("<2i", self.raw, 4 + 8 * i) for i in range(15)]

        # Planes (lump 1)
        p_ofs, p_ln = self.lumps[1]
        self.planes = [struct.unpack_from("<4fi", self.raw, p_ofs + 20 * i) for i in range(p_ln // 20)]

        # Nodes (lump 5) & Leaves (lump 10) & Clipnodes (lump 9)
        n_ofs, n_ln = self.lumps[5]
        l_ofs, l_ln = self.lumps[10]
        c_ofs, c_ln = self.lumps[9]
        m_ofs, _ = self.lumps[14]
        self.headnode0, self.headnode1 = struct.unpack_from("<2i", self.raw, m_ofs + 36)

        if self.is_bsp2:
            self.nodes = [struct.unpack_from("<3i", self.raw, n_ofs + 44 * i) for i in range(n_ln // 44)]
            self.leaves = [struct.unpack_from("<i", self.raw, l_ofs + 44 * i)[0] for i in range(l_ln // 44)]
            self.clipnodes = [struct.unpack_from("<3i", self.raw, c_ofs + 12 * i) for i in range(c_ln // 12)]
        else:
            self.nodes = []
            for i in range(n_ln // 24):
                pl, c0, c1 = struct.unpack_from("<i2h", self.raw, n_ofs + 24 * i)
                self.nodes.append((pl, c0, c1))
            self.leaves = [struct.unpack_from("<i", self.raw, l_ofs + 28 * i)[0] for i in range(l_ln // 28)]
            self.clipnodes = [struct.unpack_from("<i2h", self.raw, c_ofs + 8 * i) for i in range(c_ln // 8)]

        # Entities
        e_ofs, e_ln = self.lumps[0]
        ent_txt = self.raw[e_ofs:e_ofs + e_ln].decode("latin1", errors="replace")
        self.ents = []
        for b in re.findall(r"\{([^}]*)\}", ent_txt):
            d = dict(re.findall(r'"([^"]+)"\s+"([^"]*)"', b))
            if "origin" in d:
                try:
                    d["_org"] = tuple(float(x) for x in d["origin"].split())
                except Exception:
                    pass
            self.ents.append(d)

    def hull0_contents(self, x, y, z):
        idx = self.headnode0
        while idx >= 0:
            pl_id, c0, c1 = self.nodes[idx]
            nx, ny, nz, dist, _ = self.planes[pl_id]
            d = nx * x + ny * y + nz * z - dist
            idx = c0 if d >= 0 else c1
        return self.leaves[~idx]

    def hull1_contents(self, x, y, z):
        idx = self.headnode1
        while idx >= 0:
            pl_id, c0, c1 = self.clipnodes[idx]
            nx, ny, nz, dist, _ = self.planes[pl_id]
            d = nx * x + ny * y + nz * z - dist
            idx = c0 if d >= 0 else c1
        return idx

    def floor_z(self, x, y, z_start=80.0):
        for z in range(int(z_start), -60, -1):
            c = self.hull0_contents(x, y, float(z))
            if c != -1:  # -1 is CONTENT_EMPTY
                return z + 1, c
        return None, None

    def check_spot(self, name, x, y):
        fz, fc = self.floor_z(x, y, 80)
        if fz is None:
            return f"{name} ({x},{y}): NO FLOOR"
        # Check 64u radius walk-around clearance at z = fz+24 and z = fz+72
        blocked = []
        for ang in range(0, 360, 30):
            for r in (0, 32, 64):
                px = x + r * math.cos(math.radians(ang))
                py = y + r * math.sin(math.radians(ang))
                c1 = self.hull1_contents(px, py, fz + 28)
                c2 = self.hull0_contents(px, py, fz + 75)
                if c1 != -1 or c2 != -1:
                    blocked.append((r, ang, c1, c2))
        # Check sky clearance straight up to z = 3200!
        ceil_hit = None
        for z in range(fz + 40, 3400, 20):
            c = self.hull0_contents(x, y, float(z))
            if c != -1:
                ceil_hit = (z, c)
                break
        # Nearest entities within 260u
        near = []
        for e in self.ents:
            if "_org" in e and e.get("classname") != "light":
                ox, oy, oz = e["_org"]
                d2 = math.hypot(ox - x, oy - y)
                if d2 < 260 and abs(oz - fz) < 160:
                    near.append((round(d2), e.get("classname"), e.get("model", ""), (round(ox), round(oy), round(oz))))
        near.sort()
        return f"{name} ({x}, {y}) -> floor_z={fz} (below={fc}), walk_blocked={len(blocked)}, sky_ceil={ceil_hit}, near_ents={near[:6]}"


if __name__ == "__main__":
    for mp in ("maps/bakersfielddowntown.bsp", "maps/downtownsmall.bsp", "maps/downtown.bsp"):
        if not os.path.isfile(os.path.join(ROOT, mp)):
            continue
        b = BSPInspector(mp)
        print(f"*** {mp} ***")
        print("  -- Entities near Fox Theater (-9900..-8800, 1800..3000) --")
        for e in b.ents:
            if "_org" in e and e.get("classname") != "light":
                ox, oy, oz = e["_org"]
                if -9900 <= ox <= -8800 and 1800 <= oy <= 3000 and oz < 150:
                    print(f"    {e.get('classname'):26s} ({ox:7.0f}, {oy:7.0f}, {oz:5.0f}) mdl={e.get('model','')}")
        print("  -- Entities near Padre Hotel (-9800..-8500, -6200..-5000) --")
        for e in b.ents:
            if "_org" in e and e.get("classname") != "light":
                ox, oy, oz = e["_org"]
                if -9800 <= ox <= -8500 and -6200 <= oy <= -5000 and oz < 150:
                    print(f"    {e.get('classname'):26s} ({ox:7.0f}, {oy:7.0f}, {oz:5.0f}) mdl={e.get('model','')}")

        # Test candidate spots at Fox Theater & Padre Hotel!
        for nm, cx, cy in [
            ("Fox Plaza Street Center", -9120, 2480),
            ("Fox Marquee Curbside",    -9230, 2480),
            ("Fox Intersection 20th&H", -9120, 2120),
            ("Padre Street Center",     -8860, -5640),
            ("Padre Curbside",          -8960, -5640),
            ("Padre Intersection 18th&H",-8860, -5980),
        ]:
            print(" ", b.check_spot(nm, cx, cy))
