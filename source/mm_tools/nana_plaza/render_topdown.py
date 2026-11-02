"""render_topdown.py — Parses the generated `out/nanaplaza.map` brush planes directly, reconstructs exact
3D convex brush hulls in world meters, renders a painter's-sorted orthographic top-down view using the
actual photo-derived textures' colours, and overlays it onto the calibrated Web Mercator satellite aerials:
  - `out/topdown_z20_overlay.jpg` (vs `ref_016.jpg`, 0.232 m/px, 10 m grid — 1 m = 4.3 px)
  - `out/topdown_z19_overlay.jpg` (vs `ref_014.jpg`, 0.464 m/px, 25 m grid — 1 m = 2.2 px)
  - `out/topdown_z18_overlay.jpg` (vs `ref_011.jpg`, 0.928 m/px, 50 m grid — 1 m = 1.1 px)
"""
import itertools
import math
import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(HERE, "out", "nanaplaza.map")
REF_DIR = os.path.join(HERE, "ref_images")
TEX_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "textures"))
OUT_DIR = os.path.join(HERE, "out")

U_M = 39.37007874015748
LAT0, LON0 = 13.7413718, 100.5533082
COS_LAT = math.cos(math.radians(LAT0))

PLANE_RE = re.compile(
    r"\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)\s*"
    r"\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)\s*"
    r"\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)\s*"
    r"(\S+)"
)


def global_wm_px(lat, lon, z):
    n = (2.0 ** z) * 256.0
    gx = (lon + 180.0) / 360.0 * n
    s = math.sin(math.radians(lat))
    gy = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return gx, gy


def load_tex_colors():
    colors = {}
    if os.path.isdir(TEX_DIR):
        for fn in os.listdir(TEX_DIR):
            if fn.startswith(("np_", "{np_")) and fn.endswith(".png") and not fn.endswith("_glow.png"):
                tname = fn[:-4]
                im = Image.open(os.path.join(TEX_DIR, fn)).convert("RGBA")
                arr = np.asarray(im, dtype=np.float32)
                mask = arr[..., 3] > 100
                if np.any(mask):
                    rgb = arr[mask][:, :3].mean(axis=0)
                    colors[tname] = tuple(int(round(v)) for v in rgb)
    return colors


def parse_map_brushes(map_path):
    """Extracts (z_min_m, z_max_m, top_tex, hull_2d_pts_m) for every non-sky brush in `nanaplaza.map`."""
    brushes = []
    in_brush = False
    cur_planes = []

    with open(map_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line == "{":
                # Could be entity start or brush start; brush lines start with '('
                cur_planes = []
                in_brush = True
            elif line == "}":
                if in_brush and len(cur_planes) >= 4:
                    brushes.append(cur_planes)
                in_brush = False
                cur_planes = []
            elif line.startswith('"'):
                # Inside entity header, not brush
                in_brush = False
            elif line.startswith("("):
                in_brush = True
                m = PLANE_RE.match(line)
                if m:
                    vals = [float(m.group(i)) for i in range(1, 10)]
                    p0 = np.array(vals[0:3], dtype=np.float64) / U_M
                    p1 = np.array(vals[3:6], dtype=np.float64) / U_M
                    p2 = np.array(vals[6:9], dtype=np.float64) / U_M
                    tex = m.group(10)
                    # Quake plane convention in nana_lib.vface: cross(p0-p1, p2-p1) points OUTWARD!
                    n = np.cross(p0 - p1, p2 - p1)
                    norm = np.linalg.norm(n)
                    if norm > 1e-9:
                        n = n / norm
                        d = float(np.dot(n, p0))
                        cur_planes.append((n, d, tex))

    parsed = []
    for planes in brushes:
        tex_set = {t for _, _, t in planes}
        if "sky_np" in tex_set or "sky" in tex_set or "clip" in tex_set:
            continue
        # Solve 3-plane intersections: N_i . X <= d_i + eps
        ns = np.array([p[0] for p in planes], dtype=np.float64)
        ds = np.array([p[1] for p in planes], dtype=np.float64)
        top_tex = max(planes, key=lambda p: p[0][2])[2]

        verts = []
        m_cnt = len(planes)
        for i, j, k in itertools.combinations(range(m_cnt), 3):
            A = np.stack([ns[i], ns[j], ns[k]], axis=0)
            if abs(np.linalg.det(A)) < 1e-6:
                continue
            pt = np.linalg.solve(A, np.array([ds[i], ds[j], ds[k]]))
            if np.all(ns @ pt <= ds + 1e-3):
                verts.append(pt)
        if len(verts) < 4:
            continue
        v_arr = np.array(verts)
        zmin = float(v_arr[:, 2].min())
        zmax = float(v_arr[:, 2].max())
        xspan = float(v_arr[:, 0].max() - v_arr[:, 0].min())
        yspan = float(v_arr[:, 1].max() - v_arr[:, 1].min())
        # Skip the two giant background ground base slabs so satellite ground shows around streets/lots
        if zmax <= 0.015 and xspan > 180.0 and yspan > 180.0:
            continue
        # 2D convex hull in XY (monotone chain)
        pts2 = sorted({(round(float(p[0]), 3), round(float(p[1]), 3)) for p in v_arr})
        if len(pts2) < 3:
            continue

        def cross2(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower = []
        for p in pts2:
            while len(lower) >= 2 and cross2(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        upper = []
        for p in reversed(pts2):
            while len(upper) >= 2 and cross2(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        hull = lower[:-1] + upper[:-1]
        if len(hull) >= 3:
            parsed.append((zmin, zmax, top_tex, hull))

    # Painter's sort: lowest zmax first, then larger area first so roof details/props draw on top
    parsed.sort(key=lambda item: (round(item[1], 3), -len(item[3])))
    return parsed


def draw_grid(draw, cx, cy, mpp, img_px, step_m, fnt):
    for xm in range(-500, 501, step_m):
        px = cx + xm / mpp
        if 0 <= px < img_px:
            major = (xm % (step_m * 2) == 0) or xm == 0
            col = (255, 70, 70) if xm == 0 else ((255, 240, 80) if major else (150, 205, 255))
            draw.line([(px, 0), (px, img_px)], fill=col, width=1)
            if major:
                draw.rectangle([px + 1, 2, px + 34, 15], fill=(0, 0, 0))
                draw.text((px + 2, 2), f"{xm:+d}m", fill=col, font=fnt)
    for ym in range(-500, 501, step_m):
        py = cy - ym / mpp
        if 0 <= py < img_px:
            major = (ym % (step_m * 2) == 0) or ym == 0
            col = (255, 70, 70) if ym == 0 else ((255, 240, 80) if major else (150, 205, 255))
            draw.line([(0, py), (img_px, py)], fill=col, width=1)
            if major:
                draw.rectangle([2, py + 1, 38, py + 14], fill=(0, 0, 0))
                draw.text((3, py + 1), f"{ym:+d}m", fill=col, font=fnt)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tex_colors = load_tex_colors()
    brushes = parse_map_brushes(MAP_PATH)
    print(f"Parsed {len(brushes)} non-sky brushes from {MAP_PATH} for top-down overlay.")

    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 11)
        fnt_hdr = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 16)
    except OSError:
        fnt = ImageFont.load_default()
        fnt_hdr = fnt

    configs = [
        ("topdown_z20_overlay.jpg", "ref_016.jpg", 20, 817168, 483872, 5, 800, 10),
        ("topdown_z19_overlay.jpg", "ref_014.jpg", 19, 408583, 241935, 5, 800, 25),
        ("topdown_z18_overlay.jpg", "ref_011.jpg", 18, 204290, 120966, 5, 800, 50),
    ]

    for out_name, src_name, z, stx, sty, tiles_n, img_px, step_m in configs:
        sat = Image.open(os.path.join(REF_DIR, src_name)).convert("RGB")
        gx0, gy0 = global_wm_px(LAT0, LON0, z)
        scale = img_px / (tiles_n * 256.0)
        cx = (gx0 - stx * 256.0) * scale
        cy = (gy0 - sty * 256.0) * scale
        mpp = (156543.03392 * COS_LAT / (2 ** z)) / scale

        map_im = Image.new("RGB", (img_px, img_px), (36, 40, 44))
        dm = ImageDraw.Draw(map_im, "RGBA")

        edge_im = Image.new("RGBA", (img_px, img_px), (0, 0, 0, 0))
        de = ImageDraw.Draw(edge_im, "RGBA")

        for zmin, zmax, tname, hull in brushes:
            if tname.startswith("{"):
                continue
            pts_px = [(cx + xm / mpp, cy - ym / mpp) for xm, ym in hull]
            # Cull off-screen
            xs_p = [p[0] for p in pts_px]
            ys_p = [p[1] for p in pts_px]
            if max(xs_p) < 0 or min(xs_p) > img_px or max(ys_p) < 0 or min(ys_p) > img_px:
                continue

            base_c = tex_colors.get(tname, (150, 150, 155))
            # Subtle height shading so stepped roofs/towers read clearly
            shade = min(1.22, 0.90 + 0.0035 * max(0.0, zmax))
            fill_rgb = tuple(min(255, int(round(c * shade))) for c in base_c)
            alpha = 205 if tname == "np_canopy" else 255
            dm.polygon(pts_px, fill=fill_rgb + (alpha,), outline=(20, 22, 26, 210))

            # Crisp structural outline on overlay panel for roofs/roads/kerbs/vehicles
            if zmax >= 2.2:
                ocol = (0, 255, 255, 215) if tname != "np_canopy" else (255, 255, 120, 235)
                de.polygon(pts_px, fill=fill_rgb + (88,), outline=ocol)
            elif zmax >= 0.02:
                de.polygon(pts_px, fill=fill_rgb + (72,), outline=(255, 190, 60, 155))

        sat_grid = sat.copy()
        draw_grid(ImageDraw.Draw(sat_grid), cx, cy, mpp, img_px, step_m, fnt)

        map_grid = map_im.copy()
        draw_grid(ImageDraw.Draw(map_grid), cx, cy, mpp, img_px, step_m, fnt)

        ov = Image.alpha_composite(sat.convert("RGBA"), edge_im).convert("RGB")
        dov = ImageDraw.Draw(ov)
        draw_grid(dov, cx, cy, mpp, img_px, step_m, fnt)
        # Draw 10m & 1m reference scale bar at bottom-right of overlay
        sb_10 = 10.0 / mpp
        dov.rectangle([img_px - int(sb_10) - 24, img_px - 34, img_px - 10, img_px - 8], fill=(0, 0, 0))
        dov.line([(img_px - int(sb_10) - 16, img_px - 16), (img_px - 16, img_px - 16)], fill=(0, 255, 120), width=3)
        dov.text((img_px - int(sb_10) - 16, img_px - 31), f"10m ({sb_10:.1f}px) | 1m={1/mpp:.1f}px", fill=(0, 255, 120), font=fnt)

        hdr_h = 40
        sheet = Image.new("RGB", (img_px * 3 + 16, img_px + hdr_h), (18, 20, 24))
        ds = ImageDraw.Draw(sheet)
        ds.text((12, 10), f"1. Reference Aerial ({src_name}, z={z}, {mpp:.3f} m/px)", fill=(255, 230, 140), font=fnt_hdr)
        ds.text((img_px + 20, 10), "2. Orthographic .map Brush Render (1:1 Scale)", fill=(140, 235, 255), font=fnt_hdr)
        ds.text((img_px * 2 + 28, 10), "3. Aerial + .map Overlay (Cyan=Buildings, Yellow=Canopy/Roads)", fill=(150, 255, 170), font=fnt_hdr)
        sheet.paste(sat_grid, (0, hdr_h))
        sheet.paste(map_grid, (img_px + 8, hdr_h))
        sheet.paste(ov, (img_px * 2 + 16, hdr_h))

        out_p = os.path.join(OUT_DIR, out_name)
        sheet.save(out_p, quality=93)
        print(f"Wrote {out_p}")


if __name__ == "__main__":
    main()
