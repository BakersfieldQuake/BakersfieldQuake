import os
import re
import struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def inspect_bsp(rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        return
    raw = open(path, "rb").read()
    magic = raw[:4]
    is_bsp2 = (magic == b"BSP2")
    lumps = [struct.unpack_from("<2i", raw, 4 + 8 * i) for i in range(15)]
    ent_ofs, ent_ln = lumps[0]
    ent_txt = raw[ent_ofs:ent_ofs + ent_ln].decode("latin1", errors="replace")

    ents = []
    for b in re.findall(r"\{([^}]*)\}", ent_txt):
        d = dict(re.findall(r'"([^"]+)"\s+"([^"]*)"', b))
        ents.append(d)

    by_cls = {}
    for e in ents:
        c = e.get("classname", "?")
        by_cls[c] = by_cls.get(c, 0) + 1

    print(f"\n================ {rel_path} (magic={magic}, size={len(raw)/1e6:.2f} MB, {len(ents)} ents) ================")
    for k, v in sorted(by_cls.items()):
        print(f"  {k:30s}: {v}")

    # World model 0 bounds + sky bounds from BSP vertices & miptex names
    mdl_ofs, mdl_ln = lumps[14]
    m_min = struct.unpack_from("<3f", raw, mdl_ofs)
    m_max = struct.unpack_from("<3f", raw, mdl_ofs + 12)
    print(f"  World bounds: min={tuple(round(v,1) for v in m_min)} max={tuple(round(v,1) for v in m_max)}")

    # Find miptex names matching fox / padre / sky and compute approximate face vertex centroids!
    tex_ofs, tex_ln = lumps[2]
    ntex = struct.unpack_from("<i", raw, tex_ofs)[0]
    tex_names = []
    for i in range(ntex):
        tofs = struct.unpack_from("<i", raw, tex_ofs + 4 + 4 * i)[0]
        if tofs < 0:
            tex_names.append("")
        else:
            nm = raw[tex_ofs + tofs : tex_ofs + tofs + 16].split(b"\x00", 1)[0].decode("latin1", errors="replace")
            tex_names.append(nm)

    # Vertices, surfedges, edges, texinfo, faces
    v_ofs, v_ln = lumps[3]
    nverts = v_ln // 12
    verts = [struct.unpack_from("<3f", raw, v_ofs + 12 * i) for i in range(nverts)]

    e_ofs, e_ln = lumps[12]
    se_ofs, se_ln = lumps[13]
    ti_ofs, ti_ln = lumps[6]
    f_ofs, f_ln = lumps[7]

    nti = ti_ln // 40
    ti_texid = [struct.unpack_from("<i", raw, ti_ofs + 40 * i + 32)[0] for i in range(nti)]

    # Locate landmark texture bounding boxes (fox*, padre*, etc.)
    group_pts = {"fox": [], "padre": [], "sky": []}
    if is_bsp2:
        nfaces = f_ln // 28
        for fi in range(nfaces):
            plane_id, side, firstedge, numedges, texinfo_id = struct.unpack_from("<5i", raw, f_ofs + 28 * fi)
            if 0 <= texinfo_id < nti:
                tid = ti_texid[texinfo_id]
                tnm = tex_names[tid].lower() if 0 <= tid < len(tex_names) else ""
                key = None
                if "fox" in tnm or "marquee" in tnm:
                    key = "fox"
                elif "padre" in tnm:
                    key = "padre"
                elif "sky" in tnm:
                    key = "sky"
                if key:
                    se = struct.unpack_from("<i", raw, se_ofs + 4 * firstedge)[0]
                    ei = abs(se)
                    v0, v1 = struct.unpack_from("<2I", raw, e_ofs + 8 * ei)
                    group_pts[key].append(verts[v0 if se >= 0 else v1])
    else:
        nfaces = f_ln // 20
        for fi in range(nfaces):
            plane_id, side, firstedge, numedges, texinfo_id = struct.unpack_from("<2hi2h", raw, f_ofs + 20 * fi)
            if 0 <= texinfo_id < nti:
                tid = ti_texid[texinfo_id]
                tnm = tex_names[tid].lower() if 0 <= tid < len(tex_names) else ""
                key = None
                if "fox" in tnm or "marquee" in tnm:
                    key = "fox"
                elif "padre" in tnm:
                    key = "padre"
                elif "sky" in tnm:
                    key = "sky"
                if key:
                    se = struct.unpack_from("<i", raw, se_ofs + 4 * firstedge)[0]
                    ei = abs(se)
                    v0, v1 = struct.unpack_from("<2H", raw, e_ofs + 4 * ei)
                    group_pts[key].append(verts[v0 if se >= 0 else v1])

    for k, pts in group_pts.items():
        if pts:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            zs = [p[2] for p in pts]
            print(f"  Landmark [{k:5s}] ({len(pts)} faces): X=[{min(xs):.0f}..{max(xs):.0f}], Y=[{min(ys):.0f}..{max(ys):.0f}], Z=[{min(zs):.0f}..{max(zs):.0f}]")

    print("  Notable entities (spawns, vehicles, bikes, NPCs, teleports):")
    for e in ents:
        c = e.get("classname", "")
        if c in ("info_player_start", "info_player_deathmatch") or any(w in c for w in ("veh", "bike", "bird", "npc", "crowd", "lan", "eric")):
            print(f"    {c:28s} origin={e.get('origin',''):22s} angle={e.get('angle','')}")


if __name__ == "__main__":
    for f in sorted(os.listdir(os.path.join(ROOT, "maps"))):
        if f.endswith(".bsp"):
            print("MAP FILE:", f)
    inspect_bsp("maps/downtownsmall.bsp")
    inspect_bsp("maps/downtown.bsp")
