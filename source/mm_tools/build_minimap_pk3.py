"""Builds zz_minimap.pk3: top-down CoD-style BSP blueprint textures, shader & circular radar assets.

    python -I source/mm_tools/build_minimap_pk3.py <bakersfield_dir> [output_pk3] [--qc-out <minimap_bounds.qc>]

Scans:
  - <bakersfield_dir>/maps/*.bsp (all custom Bakersfield maps)
  - <bakersfield_dir>/../quake15/q15.pk3 (playable maps/*.bsp, skipping item-box b_*.bsp & sub-folders)
  - <bakersfield_dir>/bakersfield.pk3 (if any maps/*.bsp exist inside)
  - <bakersfield_dir>/../id1/pak0.pak, pak1.pak (optional: included only when present locally; CI skips cleanly)

Outputs into zz_minimap.pk3:
  - gfx/minimap/<mapname>.png   (top-down North-up CoD charcoal/grey/ivory floorplan blueprint)
  - gfx/minimap/<mapname>.txt   ("cx cy half_size" world bounds for fallback lookup)
  - gfx/minimap/white.png       (solid white 8x8 for 2D R_BeginPolygon shapes)
  - gfx/minimap/heat.png        (64x64 soft radial glow for fuzzy heat zones)
  - gfx/minimap/rim.png         (256x256 anti-aliased CoD circular bezel ring)
  - scripts/minimap.shader      (clampmap + nomipmaps + vertex color/alpha shaders for 2D R_BeginPolygon)

Reproducible: fixed 1980-01-01 zip timestamps, sorted entry order, fixed permissions, ZIP_STORED PNGs/txts,
and deterministic Pillow/NumPy output (pinned numpy==2.5.4, pillow==13.0.0).
"""
import argparse
import glob
import io
import os
import re
import struct
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16

SKIP_TEX_PREFIXES = ("sky", "clip", "trigger", "aaatrigger", "hint", "skip", "nodraw", "origin", "null")


def is_skip_tex(name: str) -> bool:
    low = name.strip().lower()
    if not low:
        return False
    return any(low.startswith(p) for p in SKIP_TEX_PREFIXES)


def parse_bsp(data: bytes):
    """Parse BSP29 or BSP2 into world walkable/wall faces and entity origins."""
    magic = data[:4]
    if magic == b"BSP2":
        bsp2 = True
    elif struct.unpack_from("<i", data, 0)[0] == 29:
        bsp2 = False
    else:
        return None

    lumps = [struct.unpack_from("<ii", data, 4 + i * 8) for i in range(15)]

    ent_off, ent_len = lumps[0]
    ent_text = data[ent_off:ent_off + ent_len].decode("latin-1", "ignore")
    ent_orgs = [
        (float(m.group(1)), float(m.group(2)), float(m.group(3)))
        for m in re.finditer(r'"origin"\s+"([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"', ent_text)
    ]

    po, pl = lumps[1]
    planes = [struct.unpack_from("<4f", data, po + 20 * i) for i in range(pl // 20)]

    to, tl = lumps[2]
    tex_names = []
    if tl >= 4:
        ntex = struct.unpack_from("<i", data, to)[0]
        for i in range(max(0, ntex)):
            mo = struct.unpack_from("<i", data, to + 4 + 4 * i)[0]
            if mo >= 0 and to + mo + 16 <= len(data):
                tex_names.append(data[to + mo:to + mo + 16].split(b"\0")[0].decode("latin-1", "ignore"))
            else:
                tex_names.append("")

    vo, vl = lumps[3]
    verts = [struct.unpack_from("<3f", data, vo + 12 * i) for i in range(vl // 12)]

    tio, til = lumps[6]
    texinfo = [struct.unpack_from("<i", data, tio + 40 * i + 32)[0] for i in range(til // 40)]

    eo, el = lumps[12]
    if bsp2:
        edges = [struct.unpack_from("<II", data, eo + 8 * i) for i in range(el // 8)]
    else:
        edges = [struct.unpack_from("<HH", data, eo + 4 * i) for i in range(el // 4)]

    seo, sel = lumps[13]
    surfedges = struct.unpack_from(f"<{sel // 4}i", data, seo)

    fo, fl = lumps[7]
    fsz = 28 if bsp2 else 20

    mo, ml = lumps[14]
    wmin = struct.unpack_from("<3f", data, mo)
    wmax = struct.unpack_from("<3f", data, mo + 12)
    ff, nf = struct.unpack_from("<ii", data, mo + 56)

    floors = []
    walls = []

    for i in range(ff, ff + nf):
        b = fo + fsz * i
        if bsp2:
            pl_idx, side, fe, ne, ti = struct.unpack_from("<iiiii", data, b)
        else:
            pl_idx, side, fe, ne, ti = struct.unpack_from("<HhihH", data, b)
        if ne < 3 or pl_idx < 0 or pl_idx >= len(planes):
            continue
        tname = ""
        if 0 <= ti < len(texinfo):
            mi = texinfo[ti]
            if 0 <= mi < len(tex_names):
                tname = tex_names[mi]
        if is_skip_tex(tname):
            continue

        nx, ny, nz, _ = planes[pl_idx]
        if side:
            nz = -nz

        pts = []
        for k in range(ne):
            se = surfedges[fe + k]
            v = verts[edges[se][0]] if se >= 0 else verts[edges[-se][1]]
            pts.append(v)

        zs = [p[2] for p in pts]
        avg_z = sum(zs) / len(zs)

        if nz > 0.50:
            low_t = tname.lower()
            kind = "water" if low_t.startswith("*") else "floor"
            if "lava" in low_t:
                kind = "lava"
            floors.append((avg_z, kind, [(p[0], p[1]) for p in pts]))
        elif abs(nz) <= 0.50:
            if max(zs) - min(zs) > 10.0:
                best_d2 = -1.0
                p0 = (pts[0][0], pts[0][1])
                p1 = p0
                for a_idx in range(len(pts)):
                    ax, ay = pts[a_idx][0], pts[a_idx][1]
                    for b_idx in range(a_idx + 1, len(pts)):
                        bx, by = pts[b_idx][0], pts[b_idx][1]
                        d2 = (bx - ax) ** 2 + (by - ay) ** 2
                        if d2 > best_d2:
                            best_d2 = d2
                            p0 = (ax, ay)
                            p1 = (bx, by)
                if best_d2 > 16.0:
                    walls.append((avg_z, p0, p1))

    return {
        "wmin": wmin,
        "wmax": wmax,
        "ent_orgs": ent_orgs,
        "floors": floors,
        "walls": walls,
    }


def compute_bounds(parsed):
    floors = parsed["floors"]
    ents = parsed["ent_orgs"]
    xs = []
    ys = []
    zs = []
    for avg_z, _, poly in floors:
        zs.append(avg_z)
        for x, y in poly:
            xs.append(x)
            ys.append(y)
    if not xs:
        wmin, wmax = parsed["wmin"], parsed["wmax"]
        xs = [wmin[0], wmax[0]]
        ys = [wmin[1], wmax[1]]
        zs = [wmin[2], wmax[2]]

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if ents:
        exs = [e[0] for e in ents]
        eys = [e[1] for e in ents]
        ezs = [e[2] for e in ents]
        exmin, exmax = min(exs) - 1600.0, max(exs) + 1600.0
        eymin, eymax = min(eys) - 1600.0, max(eys) + 1600.0
        if (xmax - xmin) > (exmax - exmin) * 1.45:
            xmin = max(xmin, exmin)
            xmax = min(xmax, exmax)
        if (ymax - ymin) > (eymax - eymin) * 1.45:
            ymin = max(ymin, eymin)
            ymax = min(ymax, eymax)
        zmin = min(ezs) - 256.0
        zmax = max(ezs) + 512.0
    else:
        zmin, zmax = min(zs), max(zs)

    cx = (xmin + xmax) * 0.5
    cy = (ymin + ymax) * 0.5
    # Add generous margin so clampmap edge pixels stay dark charcoal near map borders
    half = max(xmax - xmin, ymax - ymin) * 0.5 * 1.12 + 128.0
    if half < 640.0:
        half = 640.0
    return cx, cy, half, zmin, zmax


def render_blueprint(parsed):
    cx, cy, half, zmin, zmax = compute_bounds(parsed)
    size = 1024 if (half * 2.0) > 9000.0 else 512
    scale = size / (2.0 * half)

    def to_px(x, y):
        px = (x - (cx - half)) * scale
        py = ((cy + half) - y) * scale
        return (px, py)

    # CoD-style smoky dark charcoal void background
    img = Image.new("RGBA", (size, size), (14, 16, 18, 215))
    draw = ImageDraw.Draw(img, "RGBA")

    zspan = max(128.0, zmax - zmin)
    floors = sorted(parsed["floors"], key=lambda f: f[0])
    for avg_z, kind, poly in floors:
        if len(poly) < 3:
            continue
        t = (avg_z - zmin) / zspan
        t = max(0.0, min(1.0, t))
        if kind == "water":
            col = (24, 34, 42, 215)
        elif kind == "lava":
            col = (72, 32, 24, 215)
        else:
            # Neutral tactical slate-grey elevation blocks (matches CoD minimap contrast)
            v = int(46 + 44 * t)
            col = (v, v + 2, v + 4, 228)
        pts = [to_px(x, y) for x, y in poly]
        draw.polygon(pts, fill=col)

    # Crisp off-white / warm-ivory architectural wall edges
    line_w = 3 if size >= 1024 else 2
    for avg_z, p0, p1 in sorted(parsed["walls"], key=lambda w: w[0]):
        if avg_z > zmax + 640.0 or avg_z < zmin - 512.0:
            continue
        a = to_px(p0[0], p0[1])
        b = to_px(p1[0], p1[1])
        draw.line([a, b], fill=(236, 236, 228, 244), width=line_w)

    # Force a clean 2px dark charcoal outer edge so clampmap never streaks wall lines
    draw.rectangle([0, 0, size - 1, size - 1], outline=(14, 16, 18, 215), width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG", compress_level=6)
    return buf.getvalue(), (cx, cy, half)


def make_helper_pngs():
    """Generate white.png, heat.png (soft radial falloff), and rim.png (CoD circular bezel)."""
    out = {}

    w = Image.new("RGBA", (8, 8), (255, 255, 255, 255))
    b = io.BytesIO()
    w.save(b, format="PNG", compress_level=6)
    out["gfx/minimap/white.png"] = b.getvalue()

    # Soft radial heat glow (64x64)
    yy, xx = np.mgrid[0:64, 0:64]
    dist = np.sqrt((xx - 31.5) ** 2 + (yy - 31.5) ** 2) / 31.0
    falloff = np.clip(1.0 - dist, 0.0, 1.0)
    alpha = np.clip((falloff ** 1.7) * 255.0, 0, 255).astype(np.uint8)
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[:, :, :3] = 255
    rgba[:, :, 3] = alpha
    b = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(b, format="PNG", compress_level=6)
    out["gfx/minimap/heat.png"] = b.getvalue()

    # Anti-aliased CoD circular bezel ring (256x256)
    sz = 256
    yy, xx = np.mgrid[0:sz, 0:sz]
    r = np.sqrt((xx - 127.5) ** 2 + (yy - 127.5) ** 2) / 127.5
    rim = np.zeros((sz, sz, 4), dtype=np.uint8)

    # Outer dark gunmetal bezel (r in 0.94..0.995) + subtle inner light ring (r in 0.93..0.945) + soft inner vignette
    vig = np.clip((r - 0.80) / 0.14, 0.0, 1.0) * (r <= 0.945)
    rim[:, :, 0] = 12
    rim[:, :, 1] = 14
    rim[:, :, 2] = 17
    rim[:, :, 3] = np.clip(vig * 135.0, 0, 255).astype(np.uint8)

    # Soft bright hairline at r ~ 0.945
    line_mask = np.exp(-((r - 0.948) / 0.011) ** 2)
    rim[:, :, 0] = np.clip(rim[:, :, 0] + line_mask * 195.0, 0, 255).astype(np.uint8)
    rim[:, :, 1] = np.clip(rim[:, :, 1] + line_mask * 200.0, 0, 255).astype(np.uint8)
    rim[:, :, 2] = np.clip(rim[:, :, 2] + line_mask * 205.0, 0, 255).astype(np.uint8)
    rim[:, :, 3] = np.clip(np.maximum(rim[:, :, 3], line_mask * 215.0), 0, 255).astype(np.uint8)

    # Crisp dark outer rim (0.955..0.992) fading cleanly to 0 outside 0.995
    bezel = np.clip((r - 0.955) / 0.008, 0.0, 1.0) * np.clip((0.996 - r) / 0.008, 0.0, 1.0)
    mask_b = bezel > 0.05
    rim[mask_b, 0] = np.clip(rim[mask_b, 0] * (1.0 - bezel[mask_b]) + 18 * bezel[mask_b], 0, 255).astype(np.uint8)
    rim[mask_b, 1] = np.clip(rim[mask_b, 1] * (1.0 - bezel[mask_b]) + 20 * bezel[mask_b], 0, 255).astype(np.uint8)
    rim[mask_b, 2] = np.clip(rim[mask_b, 2] * (1.0 - bezel[mask_b]) + 24 * bezel[mask_b], 0, 255).astype(np.uint8)
    rim[mask_b, 3] = np.clip(np.maximum(rim[mask_b, 3], bezel[mask_b] * 245.0), 0, 255).astype(np.uint8)

    b = io.BytesIO()
    Image.fromarray(rim, "RGBA").save(b, format="PNG", compress_level=6)
    out["gfx/minimap/rim.png"] = b.getvalue()
    return out


def make_shader_text(map_names) -> bytes:
    blocks = []
    all_names = ["white", "heat", "rim"] + sorted(map_names)
    for name in all_names:
        blocks.append(
            f"gfx/minimap/{name}\n"
            "{\n"
            "\tnomipmaps\n"
            "\tnopicmip\n"
            "\tcull none\n"
            "\t{\n"
            f"\t\tclampmap gfx/minimap/{name}.png\n"
            "\t\tblendfunc blend\n"
            "\t\trgbGen vertex\n"
            "\t\talphaGen vertex\n"
            "\t}\n"
            "}\n"
        )
    return ("\n".join(blocks)).encode("ascii")


def collect_bsps(game_dir: Path):
    """Return sorted dict mapname -> bsp bytes from BakersfieldQuake, q15.pk3, and optional id1 paks."""
    maps = {}

    id1_dir = game_dir.parent / "id1"
    for pak_name in ("pak0.pak", "pak1.pak"):
        pak_path = id1_dir / pak_name
        if not pak_path.is_file():
            continue
        with open(pak_path, "rb") as fh:
            magic, off, size = struct.unpack("<4sii", fh.read(12))
            if magic != b"PACK":
                continue
            fh.seek(off)
            entries = [fh.read(64) for _ in range(size // 64)]
            for raw in entries:
                name = raw[:56].split(b"\0")[0].decode("latin-1", "ignore").lower()
                foff, fsize = struct.unpack("<ii", raw[56:64])
                if name.startswith("maps/") and name.endswith(".bsp") and "/" not in name[5:]:
                    mname = Path(name).stem
                    if mname.startswith("b_"):
                        continue
                    fh.seek(foff)
                    maps[mname] = fh.read(fsize)

    q15_pk3 = game_dir.parent / "quake15" / "q15.pk3"
    if q15_pk3.is_file():
        with zipfile.ZipFile(q15_pk3) as z:
            for n in sorted(z.namelist()):
                nl = n.lower()
                if nl.startswith("maps/") and nl.endswith(".bsp") and "/" not in nl[5:]:
                    mname = Path(nl).stem
                    if mname.startswith("b_"):
                        continue
                    maps[mname] = z.read(n)

    bako_pk3 = game_dir / "bakersfield.pk3"
    if bako_pk3.is_file():
        with zipfile.ZipFile(bako_pk3) as z:
            for n in sorted(z.namelist()):
                nl = n.lower()
                if nl.startswith("maps/") and nl.endswith(".bsp") and "/" not in nl[5:]:
                    mname = Path(nl).stem
                    if mname.startswith("b_"):
                        continue
                    maps[mname] = z.read(n)

    for bsp_path in sorted(glob.glob(str(game_dir / "maps" / "*.bsp"))):
        p = Path(bsp_path)
        maps[p.stem.lower()] = p.read_bytes()

    return dict(sorted(maps.items()))


def write_pk3(out_path: Path, entries: dict):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".pk3.tmp")
    with zipfile.ZipFile(tmp, "w") as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, entries[name])
    tmp.replace(out_path)


def write_bounds_qc(qc_path: Path, bounds: dict):
    lines = [
        "// Auto-generated by source/mm_tools/build_minimap_pk3.py -- do not hand-edit.",
        "// Maps world XY center (cx, cy) and half-extent R for each pre-rendered gfx/minimap/<map>.png.",
        "",
        "float\tmm_map_cx;",
        "float\tmm_map_cy;",
        "float\tmm_map_half;",
        "",
        "float(string mname) BM_MinimapLookupBounds =",
        "{",
    ]
    for mname, (cx, cy, half) in sorted(bounds.items()):
        lines.append(f'\tif (mname == "{mname}")')
        lines.append("\t{")
        lines.append(f"\t\tmm_map_cx = {cx:.2f};")
        lines.append(f"\t\tmm_map_cy = {cy:.2f};")
        lines.append(f"\t\tmm_map_half = {half:.2f};")
        lines.append("\t\treturn TRUE;")
        lines.append("\t}")
    lines.extend([
        "\treturn FALSE;",
        "};",
        "",
    ])
    qc_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def preserve_missing_maps(prev_pk3: Path, entries: dict, bounds: dict) -> int:
    """Carry over pre-rendered minimap PNGs/bounds from an existing zz_minimap.pk3 for maps whose
    BSPs are absent on the build host (e.g. id1/pak0.pak + pak1.pak dm1..dm6 on CI)."""
    if not prev_pk3 or not prev_pk3.is_file():
        return 0
    helper_names = {"white", "heat", "rim"}
    preserved = 0
    with zipfile.ZipFile(prev_pk3) as z:
        by_lower = {n.lower(): n for n in z.namelist()}
        for low in sorted(by_lower):
            if not (low.startswith("gfx/minimap/") and low.endswith(".png")):
                continue
            mname = low[len("gfx/minimap/"):-4]
            if not mname or "/" in mname or mname in helper_names or mname in bounds:
                continue
            txt_low = f"gfx/minimap/{mname}.txt"
            if txt_low not in by_lower:
                continue
            parts = z.read(by_lower[txt_low]).decode("ascii", "ignore").split()
            if len(parts) < 3:
                continue
            try:
                cx, cy, half = float(parts[0]), float(parts[1]), float(parts[2])
            except ValueError:
                continue
            if half <= 0:
                continue
            entries[f"gfx/minimap/{mname}.png"] = z.read(by_lower[low])
            entries[f"gfx/minimap/{mname}.txt"] = f"{cx:.2f} {cy:.2f} {half:.2f}\n".encode("ascii")
            bounds[mname] = (cx, cy, half)
            preserved += 1
    return preserved


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("game_dir", type=Path, help="Path to BakersfieldQuake game directory")
    ap.add_argument("out_pk3", type=Path, nargs="?", help="Output zz_minimap.pk3 path")
    ap.add_argument("--qc-out", type=Path, default=None, help="Optional generated minimap_bounds.qc path")
    ap.add_argument("--preserve-from", type=Path, default=None,
                    help="Preserve pre-rendered minimaps from an existing zz_minimap.pk3 for maps not present locally (e.g. id1 maps in CI)")
    args = ap.parse_args()

    game_dir = args.game_dir.resolve()
    out_pk3 = args.out_pk3 or (game_dir / "zz_minimap.pk3")

    maps = collect_bsps(game_dir)
    entries = make_helper_pngs()
    bounds = {}
    for mname, raw in maps.items():
        parsed = parse_bsp(raw)
        if not parsed:
            continue
        png_bytes, bnd = render_blueprint(parsed)
        entries[f"gfx/minimap/{mname}.png"] = png_bytes
        entries[f"gfx/minimap/{mname}.txt"] = f"{bnd[0]:.2f} {bnd[1]:.2f} {bnd[2]:.2f}\n".encode("ascii")
        bounds[mname] = bnd

    preserved = preserve_missing_maps(args.preserve_from, entries, bounds) if args.preserve_from else 0

    entries["scripts/minimap.shader"] = make_shader_text(bounds.keys())

    write_pk3(out_path=out_pk3, entries=entries)
    extra = f", {preserved} preserved" if preserved else ""
    print(f"wrote {out_pk3} ({len(bounds)} maps{extra}, {out_pk3.stat().st_size} bytes)")

    if args.qc_out:
        write_bounds_qc(args.qc_out, bounds)
        print(f"wrote {args.qc_out} ({len(bounds)} entries)")


if __name__ == "__main__":
    main()
