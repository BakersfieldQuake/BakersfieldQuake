"""make_nanaplaza.py — Pure spec-driven 1:1 Quake map generator for Nana Plaza (Sukhumvit Soi 4, Bangkok).
Reads declarative JSON specs from `specs/*.json` and writes Valve-220 `out/nanaplaza.map`.
NEVER hand-edit `nanaplaza.map`; all fixes flow from `specs/*.json` + `make_nanaplaza.py`.
"""
import json
import math
import os
import sys
from nana_lib import (
    HERE,
    PLAZA_YAW_DEG,
    MapBuilder,
    plaza_to_world,
)

SPEC_DIR = os.path.join(HERE, "specs")
OUT_MAP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "nanaplaza.map")
WAD_PATH = os.path.join(HERE, "out", "nanaplaza.wad")


def load_spec(name):
    with open(os.path.join(SPEC_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


class NanaPlazaGenerator:
    def __init__(self):
        self.tex_spec = load_spec("textures.json")
        self.roads = load_spec("roads.json")
        self.bridges = load_spec("bridges.json")
        self.landmarks = load_spec("landmarks.json")
        self.plaza = load_spec("nana_plaza.json")
        self.buildings = load_spec("buildings.json")
        self.props = load_spec("props_vehicles.json")

        self.mb = MapBuilder([WAD_PATH])
        self.tscale = {}
        for t in self.tex_spec["textures"]:
            self.tscale[t["name"]] = tuple(t["scale_m"])

    def tt(self, name):
        """Returns ('tile', name, mu, mv) using the logged real-world scale in textures.json."""
        if name in self.tscale:
            mu, mv = self.tscale[name]
            return ("tile", name, mu, mv)
        return name

    def ft(self, name, ru=1.0, rv=1.0):
        return ("fit", name, ru, rv)

    # ------------------------------------------------------------------
    # STAGE 7 (outer hull first so world bounds are airtight)
    # ------------------------------------------------------------------
    def build_world_hull(self):
        b = self.roads["world_bounds_m"]
        x0, x1 = b["xmin"], b["xmax"]
        y0, y1 = b["ymin"], b["ymax"]
        z0, z1 = b["zmin"], b["zmax"]
        th = 4.0
        # Subdivided 5x5 base ground slab & sky lid + split sky walls so max brush span <= 165m (~6500u < 8192u on all hulls!)
        xs = [x0 - th + (x1 - x0 + 2.0 * th) * i / 5.0 for i in range(6)]
        ys = [y0 - th + (y1 - y0 + 2.0 * th) * i / 5.0 for i in range(6)]
        for i in range(5):
            for j in range(5):
                self.mb.aabb(xs[i], ys[j], z0 - th, xs[i + 1], ys[j + 1], 0.0, ("tile", "np_sidewalk", 9.6, 9.6), group="world")
                self.mb.aabb(xs[i], ys[j], z1, xs[i + 1], ys[j + 1], z1 + th, "sky_np", group="world")
        ys_w = [y0 - th + (y1 - y0 + 2.0 * th) * i / 5.0 for i in range(6)]
        xs_w = [x0 + (x1 - x0) * i / 5.0 for i in range(6)]
        for j in range(5):
            self.mb.aabb(x0 - th, ys_w[j], 0.0, x0, ys_w[j + 1], z1, "sky_np", group="world")
            self.mb.aabb(x1, ys_w[j], 0.0, x1 + th, ys_w[j + 1], z1, "sky_np", group="world")
        for i in range(5):
            self.mb.aabb(xs_w[i], y0 - th, 0.0, xs_w[i + 1], y0, z1, "sky_np", group="world")
            self.mb.aabb(xs_w[i], y1, 0.0, xs_w[i + 1], y1 + th, z1, "sky_np", group="world")

    @staticmethod
    def _interp_y_yaw(pts, xm):
        if xm <= pts[0][0]:
            x0, y0 = pts[0]
            x1, y1 = pts[1]
        elif xm >= pts[-1][0]:
            x0, y0 = pts[-2]
            x1, y1 = pts[-1]
        else:
            x0, y0, x1, y1 = pts[0][0], pts[0][1], pts[1][0], pts[1][1]
            for i in range(len(pts) - 1):
                if pts[i][0] <= xm <= pts[i + 1][0]:
                    x0, y0 = pts[i]
                    x1, y1 = pts[i + 1]
                    break
        t = (xm - x0) / max(1e-6, (x1 - x0))
        ym = y0 + t * (y1 - y0)
        yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
        return ym, yaw

    # ------------------------------------------------------------------
    # STAGE 1: ROADS, STREETS, KERBS, POLES, WIRES & TRANSFORMER
    # ------------------------------------------------------------------
    def build_stage1_roads(self):
        sr = self.roads["sukhumvit_rd"]
        pts = sr["centerline_pts_m"]
        cw = sr["carriageway_width_m"]
        sw = sr["sidewalk_width_m"]
        # Sukhumvit Rd sidewalks + asphalt carriageway
        self.mb.polyline_ribbon(pts, cw + 2.0 * sw, 0.0, 0.16, self.tt("np_sidewalk"), side_tex=self.tt("np_forecrt"), group="detail")
        self.mb.polyline_ribbon(pts, cw, 0.0, 0.195, self.tt("np_asphalt"), side_tex=self.tt("np_asphalt"), group="detail")

        # Sukhumvit Rd central median + trimmed hedge (with intersection gaps)
        gaps = sr["median_gaps_x_m"]
        for x_step in range(-380, 336, 12):
            xm = x_step + 6.0
            ym, yaw = self._interp_y_yaw(pts, xm)
            if any(g0 <= xm <= g1 for g0, g1 in gaps):
                if -44.0 <= xm <= -26.0:
                    self.mb.obox(xm, ym, 0.195, 0.92, 2.2, 0.32, yaw, self.tt("np_kerb_rw"), group="detail")
                continue
            self.mb.obox(xm, ym, 0.195, 0.42, 5.8, 0.85, yaw, self.tt("np_forecrt"), group="detail")
            self.mb.obox(xm, ym, 0.42, 1.15, 5.4, 0.65, yaw, self.tt("np_foliage"), group="detail")

        # Secondary neighborhood streets & alleys
        for st in self.roads["secondary_streets"]:
            self.mb.polyline_ribbon(st["pts"], st["width"] + 2.6, 0.0, 0.13, self.tt("np_sidewalk"), group="detail")
            self.mb.polyline_ribbon(st["pts"], st["width"], 0.0, 0.165, self.tt("np_asphalt"), group="detail")

        # Sukhumvit Soi 4 carriageway & crisp centreline markings
        s4 = self.roads["soi_4"]
        self.mb.polyline_ribbon(s4["centerline_pts_m"], s4["carriageway_width_m"], -0.04, 0.0, self.tt("np_asphalt"), group="detail")
        # Crisp 1:1 double-yellow mouth centreline band (Y=+38..+67.2, 3.6m rectified road+stripe crop)
        self.mb.aabb(-36.05, 38.0, -0.03, -32.45, 67.2, 0.012, self.ft("np_road_ylw", 1.0, 8.0), group="detail")
        # Crisp 1:1 dashed mid-soi centreline band (Y=-140..+38)
        self.mb.aabb(-35.95, -140.0, -0.03, -32.35, 38.0, 0.012, self.ft("np_road_dsh", 1.0, 48.0), group="detail")
        # Brick-red & white zebra crosswalk across Soi 4 mouth (ref_016, ref_045)
        xw = s4["mouth_crosswalk"]
        self.mb.aabb(xw["x1"], xw["y1"], -0.02, xw["x2"], xw["y2"], xw["z2"], self.ft(xw["tex"], 1.0, 1.0), group="detail")
        # Northbound white directional arrow in west lane (ref_052, ref_037)
        ax, ay = s4["northbound_arrow_m"]
        self.mb.aabb(ax - 0.12, ay - 1.6, -0.02, ax + 0.12, ay + 0.8, 0.018, self.tt("np_white_pnl"), group="detail")
        self.mb.quad_prism([(ax - 0.42, ay + 0.8), (ax + 0.42, ay + 0.8), (ax, ay + 1.9)], -0.02, 0.018, self.tt("np_white_pnl"), group="detail")

        # Exact West & East Soi 4 kerb & sidewalk segments
        for seg in s4["west_kerb_segments"]:
            self.mb.aabb(seg["x1"], seg["y1"], -0.02, seg["x2"] - 0.25, seg["y2"], seg["z2"], self.tt(seg["walk_tex"]), group="detail")
            self.mb.aabb(
                seg["x2"] - 0.25, seg["y1"], -0.02, seg["x2"], seg["y2"], seg["z2"],
                self.tt(seg["kerb_tex"]),
                faces={"e": self.tt(seg["kerb_tex"]), "t": self.tt(seg["kerb_tex"])},
                group="detail",
            )
        for seg in s4["east_kerb_segments"]:
            self.mb.aabb(seg["x1"] + 0.25, seg["y1"], -0.02, seg["x2"], seg["y2"], seg["z2"], self.tt(seg["walk_tex"]), group="detail")
            self.mb.aabb(
                seg["x1"], seg["y1"], -0.02, seg["x1"] + 0.25, seg["y2"], seg["z2"],
                self.tt(seg["kerb_tex"]),
                faces={"w": self.tt(seg["kerb_tex"]), "t": self.tt(seg["kerb_tex"])},
                group="detail",
            )

        # 3 linked stainless pedestrian barriers at Soi 4 east mouth (ref_045, ref_046)
        for pb in s4["pedestrian_barriers"]:
            self.mb.aabb(pb["x"] - 0.03, pb["y1"], pb["z1"], pb["x"] + 0.03, pb["y2"], pb["z2"], self.tt(pb["tex"]), group="fence")

        # Square prestressed concrete utility poles + compact junction boxes + cobra streetlights
        for idx_p, p in enumerate(s4["utility_poles"]):
            px, py, ph = p["x"], p["y"], p["h"]
            self.mb.aabb(px - 0.14, py - 0.14, 0.0, px + 0.14, py + 0.14, ph, ("tile", "np_pier_conc", 0.6, 2.4), group="detail")
            self.mb.aabb(px - 0.55, py - 0.06, ph - 0.65, px + 0.55, py + 0.06, ph - 0.52, self.tt("np_shutter"), group="detail")
            if p.get("box") and idx_p % 2 == 0:
                bx = px + (0.14 if p["side"] == "west" else -0.30)
                self.mb.aabb(bx, py - 0.12, 2.25, bx + 0.14, py + 0.12, 2.65, self.tt("np_pier_conc"), group="detail")
            if p.get("lamp"):
                lx = px + (1.4 if p["side"] == "west" else -1.4)
                xlo, xhi = sorted((px, lx))
                self.mb.aabb(xlo, py - 0.05, ph - 1.1, xhi, py + 0.05, ph - 0.96, self.tt("np_shutter"), group="detail")
                self.mb.light(lx, py, ph - 1.35, val=190, color="1.0 0.96 0.88")

        # Twin-pole H-frame 3-phase oil transformer north of Pharmacy World (ref_298)
        xf = s4["transformer_hframe"]
        self.mb.aabb(xf["x"] - 0.42, xf["y1"], xf["z1"] - 0.18, xf["x"] + 0.42, xf["y2"], xf["z1"], self.tt("np_shutter"), group="detail")
        self.mb.aabb(
            xf["x"] - 0.45, xf["y1"] + 0.22, xf["z1"], xf["x"] + 0.45, xf["y2"] - 0.22, xf["z2"],
            self.ft(xf["tex"]),
            group="detail",
        )

        # Overhead black cable spans at crossarm height ({np_wire_blk)
        for ws in s4["wire_spans"]:
            dx, dy = ws["x2"] - ws["x1"], ws["y2"] - ws["y1"]
            L = math.hypot(dx, dy)
            yaw = math.degrees(math.atan2(dy, dx))
            cx, cy = 0.5 * (ws["x1"] + ws["x2"]), 0.5 * (ws["y1"] + ws["y2"])
            self.mb.obox(cx, cy, ws["z1"], ws["z2"], 0.5 * L, 0.04, yaw, self.tt(ws["tex"]), group="fence")

    # ------------------------------------------------------------------
    # STAGE 2: BRIDGES, BTS VIADUCT, BTS NANA STATION & SKYBRIDGES
    # ------------------------------------------------------------------
    def build_stage2_bridges(self):
        bv = self.bridges["bts_viaduct"]
        pts = bv["centerline_pts_m"]
        hump_x0, hump_x1 = bv["overpass_hump_over_expressway"]["x_range_m"]
        hump_dz = bv["overpass_hump_over_expressway"]["extra_z_m"]

        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            seg_len = math.hypot(x1 - x0, y1 - y0)
            n_sub = max(1, int(round(seg_len / 24.0)))
            yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
            for k in range(n_sub):
                t0, t1 = k / n_sub, (k + 1) / n_sub
                xa, ya = x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0
                xb, yb = x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1
                xc, yc = 0.5 * (xa + xb), 0.5 * (ya + yb)
                hl = 0.5 * math.hypot(xb - xa, yb - ya) + 0.05
                dz = 0.0
                if hump_x0 <= xc <= hump_x1:
                    u = (xc - hump_x0) / (hump_x1 - hump_x0)
                    dz = hump_dz * math.sin(math.pi * u) ** 2
                z_sof = bv["soffit_z_m"] + dz
                z_top = bv["girder_top_z_m"] + dz
                z_par = bv["parapet_top_z_m"] + dz
                self.mb.obox(xc, yc, z_sof, z_sof + 1.0, hl, 0.5 * bv["girder_bottom_width_m"], yaw, self.tt("np_pier_conc"), group="detail")
                self.mb.obox(xc, yc, z_sof + 1.0, z_top, hl, 0.5 * bv["deck_width_m"], yaw, self.tt("np_viaduct"), group="detail")
                rad = math.radians(yaw)
                ew = (-math.sin(rad), math.cos(rad))
                for sgn in (-1.0, 1.0):
                    off = sgn * (0.5 * bv["deck_width_m"] - 0.28)
                    self.mb.obox(xc + off * ew[0], yc + off * ew[1], z_top, z_par, hl, 0.28, yaw, self.tt("np_viaduct"), group="detail")

        for px in bv["piers_x_m"]:
            py, yaw = self._interp_y_yaw(bv["centerline_pts_m"], px)
            dz = 0.0
            if hump_x0 <= px <= hump_x1:
                u = (px - hump_x0) / (hump_x1 - hump_x0)
                dz = hump_dz * math.sin(math.pi * u) ** 2
            z_sof = bv["soffit_z_m"] + dz
            self.mb.oct_prism(px, py, 0.18, z_sof - 1.1, 1.15, self.tt("np_pier_conc"), sides=8, group="detail")
            self.mb.obox(px, py, z_sof - 1.1, z_sof, 1.4, 3.6, yaw, self.tt("np_pier_conc"), group="detail")

        # BTS Nana Station (E3) + walkable Exit 2 stairs down to Sukhumvit SW sidewalk
        st = self.bridges["bts_nana_station"]
        sx, sy = st["center_m"]
        syaw = st["yaw_deg"]
        shl = 0.5 * st["length_m"]
        self.mb.obox(sx, sy, st["concourse_z_m"][0], st["concourse_z_m"][1], shl, 0.5 * st["concourse_width_m"], syaw, self.tt("np_viaduct"), group="detail")
        self.mb.obox(sx, sy, st["platform_z_m"][0], st["platform_z_m"][1], shl, 0.5 * st["platform_width_m"], syaw, self.tt("np_viaduct"), group="detail")
        self.mb.obox(sx, sy, st["canopy_z_m"][0], st["canopy_z_m"][1], shl, 0.5 * st["platform_width_m"] + 1.2, syaw, self.tt("np_canopy"), group="detail")
        rad_st = math.radians(syaw)
        ew_st = (-math.sin(rad_st), math.cos(rad_st))
        for ds in (-48.0, -24.0, 0.0, 24.0, 48.0):
            cx = sx + ds * math.cos(rad_st)
            cy = sy + ds * math.sin(rad_st)
            self.mb.oct_prism(cx, cy, 0.18, st["concourse_z_m"][0], 1.25, self.tt("np_pier_conc"), group="detail")
            for sgn in (-1.0, 1.0):
                self.mb.obox(
                    cx + sgn * 9.5 * ew_st[0], cy + sgn * 9.5 * ew_st[1],
                    st["platform_z_m"][1], st["canopy_z_m"][0],
                    0.45, 0.45, syaw, self.tt("np_pier_conc"), group="detail"
                )
        # Walkable Exit 2 staircase descending from West end of BTS Nana concourse to SW sidewalk
        n_bts_steps = 25
        for k in range(n_bts_steps):
            ds_step = -68.0 - k * 0.48
            zt = st["concourse_z_m"][0] * (1.0 - k / n_bts_steps) + 0.18 * (k / n_bts_steps)
            zb = max(0.16, zt - 0.35)
            cx_s = sx + ds_step * math.cos(rad_st) - 14.5 * ew_st[0]
            cy_s = sy + ds_step * math.sin(rad_st) - 14.5 * ew_st[1]
            self.mb.obox(cx_s, cy_s, zb, zt, 0.28, 1.1, syaw, self.tt("np_stair_trd"), group="detail")

        sb = st["skybridge_ones"]
        self.mb.polyline_ribbon(sb["pts_m"], sb["width_m"], sb["z_m"][0], sb["z_m"][0] + 0.5, self.tt("np_pier_conc"), group="detail")
        self.mb.polyline_ribbon(sb["pts_m"], sb["width_m"] + 0.4, sb["z_m"][1] - 0.35, sb["z_m"][1], self.tt("np_canopy"), group="detail")

        # Chaloem Maha Nakhon Elevated Expressway Overpass
        ex = self.bridges["chaloem_expressway"]
        self.mb.polyline_ribbon(ex["centerline_pts_m"], ex["deck_width_m"], ex["soffit_z_m"], ex["deck_top_z_m"], self.tt("np_asphalt"), side_tex=self.tt("np_viaduct"), group="detail")
        for i in range(len(ex["centerline_pts_m"]) - 1):
            x0, y0 = ex["centerline_pts_m"][i]
            x1, y1 = ex["centerline_pts_m"][i + 1]
            L = math.hypot(x1 - x0, y1 - y0)
            npier = max(1, int(L / ex["pier_spacing_m"]))
            for k in range(npier):
                t = (k + 0.5) / npier
                px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                if 172.0 <= py <= 198.0:
                    continue
                for dx_p in (-6.5, 6.5):
                    self.mb.oct_prism(px + dx_p, py, 0.0, ex["soffit_z_m"], 1.1, self.tt("np_pier_conc"), group="detail")

        # JW Marriott — Ploenchit pedestrian skybridge
        dp = self.bridges["duang_phithak_skybridge"]
        self.mb.polyline_ribbon(dp["pts_m"], dp["width_m"], dp["z_m"][0], dp["z_m"][0] + 0.45, self.tt("np_pier_conc"), group="detail")
        self.mb.polyline_ribbon(dp["pts_m"], dp["width_m"] + 0.3, dp["z_m"][1] - 0.3, dp["z_m"][1], self.tt("np_canopy"), group="detail")

    # ------------------------------------------------------------------
    # STAGE 3: LANDMARKS (ARCH, TENSILE CANOPY, TOWERS, MONUMENTS)
    # ------------------------------------------------------------------
    def _build_canopy_vault(self, bs0, bs1, w1, w2, ze, zr, draw_start_rib=True, draw_end_rib=False):
        wm = 0.5 * (w1 + w2)
        wh = 0.5 * (w2 - w1)
        w_lo = wm - 0.48 * wh
        w_hi = wm + 0.48 * wh
        z_mid = ze + 0.68 * (zr - ze)
        self.mb.sloped_slab_plaza(bs0, bs1, w1, ze, w_lo, z_mid, 0.14, self.tt("np_canopy"), group="canopy")
        self.mb.sloped_slab_plaza(bs0, bs1, w_lo, z_mid, wm, zr, 0.14, self.tt("np_canopy"), group="canopy")
        self.mb.sloped_slab_plaza(bs0, bs1, wm, zr, w_hi, z_mid, 0.14, self.tt("np_canopy"), group="canopy")
        self.mb.sloped_slab_plaza(bs0, bs1, w_hi, z_mid, w2, ze, 0.14, self.tt("np_canopy"), group="canopy")
        for sr_pos in ((bs0 if draw_start_rib else None), (bs1 if draw_end_rib else None)):
            if sr_pos is None:
                continue
            self.mb.sloped_slab_plaza(sr_pos - 0.15, sr_pos + 0.15, w1, ze - 0.20, wm, zr - 0.16, 0.20, self.tt("np_pier_conc"), group="detail")
            self.mb.sloped_slab_plaza(sr_pos - 0.15, sr_pos + 0.15, wm, zr - 0.16, w2, ze - 0.20, 0.20, self.tt("np_pier_conc"), group="detail")
            for w_mast in (w1, w2):
                self.mb.pbox(sr_pos - 0.16, w_mast - 0.20, 11.2, sr_pos + 0.16, w_mast + 0.20, ze, self.tt("np_pier_conc"), group="detail")

    def build_stage3_landmarks(self):
        # 1. Nana Plaza Iconic Main Entrance Arch on Soi 4 (ref_182, ref_031, ref_287)
        ar = self.landmarks["nana_plaza_arch"]
        xf = ar["x_front_m"]
        ys, yn = ar["y_south_m"], ar["y_north_m"]
        # Main concave signboard bridge spanning Y=6.0..15.2m at Z=4.65..8.2m (unclipped NANA PLAZA, no duplicate lower banner!)
        self.mb.aabb(
            xf - 0.45, ys, 4.65, xf + 0.45, yn, ar["arch_top_z_m"],
            self.tt("np_slat_blk"),
            faces={"w": self.ft("np_arch_main"), "e": self.ft("np_arch_main")},
            group="detail",
        )
        # Yellow triangle + red lips central crown (Z=8.2..9.5m — visible from both Soi 4 AND 3F East courtyard!)
        ym = 0.5 * (ys + yn)
        self.mb.aabb(
            xf - 0.35, ym - 1.9, ar["arch_top_z_m"], xf + 0.35, ym + 1.9, ar["crown_top_z_m"],
            self.tt("np_slat_blk"),
            faces={"w": self.ft("np_arch_crn"), "e": self.ft("np_arch_crn")},
            group="detail",
        )
        # Curved red 'The Worlds Largest Adult Playground' banner underneath (Z=4.05..4.64m for clear GEISHA sightline!)
        self.mb.aabb(
            xf - 0.30, ys + 1.2, 4.05, xf + 0.30, yn - 1.2, 4.64,
            self.tt("np_slat_blk"),
            faces={"w": self.ft("np_arch_ban"), "e": self.ft("np_arch_ban")},
            group="detail",
        )
        # North pier ('Nana Safety Zone / Lumpini Police Station') & South pier ('Land of Smiles / Your Second Home') lightboxes!
        self.mb.aabb(xf - 0.50, yn - 1.65, 3.15, xf + 0.15, yn - 0.05, 4.05, self.tt("np_white_pnl"), faces={"w": self.ft("np_arch_safe")}, group="detail")
        self.mb.aabb(xf - 0.50, ys + 0.05, 3.15, xf + 0.15, ys + 1.65, 4.05, self.tt("np_white_pnl"), faces={"w": self.ft("np_arch_land")}, group="detail")
        # Projecting vertical 'NANA PLAZA' neon blade sign on South front wall (ref_020, ref_182)
        bs = ar["blade_sign"]
        self.mb.aabb(
            bs["x1"], bs["y1"], bs["z1"], bs["x2"], bs["y2"], bs["z2"],
            self.tt("np_slat_blk"),
            faces={"n": self.ft(bs["tex"]), "s": self.ft(bs["tex"]), "w": self.ft(bs["tex"])},
            group="detail",
        )

        # 2. 2018 5-Bay Scalloped White Steel-Ribbed Tensile Roof Canopy (calibrated strictly east of Soi 4!)
        tc = self.landmarks["tensile_canopy"]
        tb = tc["throat_bay"]
        ze, zr = tc["eave_z_m"], tc["ridge_z_m"]
        self._build_canopy_vault(tb["s1_m"], tb["s2_m"], tb["w1_m"], tb["w2_m"], ze, zr - 0.6, draw_start_rib=True, draw_end_rib=False)
        s1, s2 = tc["s1_m"], tc["s2_m"]
        w1, w2 = tc["w1_m"], tc["w2_m"]
        nb = tc["bays"]
        bay_len = (s2 - s1) / nb
        for b_idx in range(nb):
            bs0 = s1 + b_idx * bay_len
            bs1 = bs0 + bay_len
            self._build_canopy_vault(bs0, bs1, w1, w2, ze, zr, draw_start_rib=True, draw_end_rib=(b_idx == nb - 1))

        # 3. Surrounding High-Rise Towers & Neighborhood Landmarks (structural world cores for PVS occlusion!)
        for tm in self.landmarks["towers_and_monuments"]:
            cx, cy = tm["cx"], tm["cy"]
            hl, hw = tm["hl"], tm["hw"]
            yaw = tm["yaw"]
            z1, z2 = tm["z1"], tm["z2"]
            t_main = self.tt(tm["tex"])
            faces = {}
            if tm.get("top_tex"):
                faces["t"] = self.tt(tm["top_tex"])
            if tm.get("soffit_tex"):
                faces["b"] = self.tt(tm["soffit_tex"])
            is_struct = (z1 <= 0.2 and hl >= 5.0 and hw >= 4.0)
            if tm.get("fit_east") or tm.get("fit_both"):
                faces["right"] = self.ft(tm["tex"])
                faces["left"] = self.ft(tm["tex"])
                is_struct = False
            self.mb.obox(cx, cy, z1, z2, hl, hw, yaw, t_main, faces=faces, group="world" if is_struct else "detail")

            if tm.get("octagonal_wings"):
                # Stepped octagonal cross-wings of The Landmark Bangkok 31F Tower (z20_sat_grid.jpg, cam_09)
                self.mb.obox(cx, cy, z1, z2 - 4.0, hl * 1.18, hw * 0.72, yaw, t_main, group="detail")
                self.mb.obox(cx, cy, z1, z2 - 4.0, hl * 0.72, hw * 1.16, yaw, t_main, group="detail")

            if tm.get("fit_east"):
                # IN (south) & OUT (north) granite gate pillars + photo-derived plaques + compound pole & white cabinets (ref_035)
                self.mb.aabb(-40.9, 5.2, 0.16, -39.9, 5.9, 3.3, self.tt("np_brick_col"), group="detail")
                self.mb.aabb(-39.92, 5.33, 2.35, -39.82, 5.77, 2.82, self.ft("np_in_plq"), group="detail")
                self.mb.aabb(-40.9, 15.5, 0.16, -39.9, 16.2, 3.3, self.tt("np_brick_col"), group="detail")
                self.mb.aabb(-39.92, 15.63, 2.35, -39.82, 16.07, 2.82, self.ft("np_out_plq"), group="detail")
                self.mb.aabb(-39.65, 16.25, 0.16, -39.25, 16.65, 9.2, ("tile", "np_pier_conc", 0.6, 2.4), group="detail")
                self.mb.aabb(-39.25, 16.15, 1.95, -38.85, 16.85, 2.95, self.tt("np_white_pnl"), group="detail")
                self.mb.aabb(-39.25, 16.20, 3.05, -38.85, 16.80, 3.55, self.tt("np_white_pnl"), group="detail")

            if "step_top" in tm:
                st = tm["step_top"]
                self.mb.obox(cx, cy, st["z1"], st["z2"], hl * st["scale"], hw * st["scale"], yaw, t_main, group="detail")

            if "sloped_crown_z2" in tm:
                self.mb.obox(cx - 4.0, cy, z2, tm["sloped_crown_z2"], hl * 0.55, hw * 0.9, yaw, t_main, group="detail")

            if "chang_banner" in tm:
                cb = tm["chang_banner"]
                self.mb.aabb(cb["x1"], cb["y1"], cb["z1"], cb["x2"], cb["y2"], cb["z2"], self.ft(cb["tex"]), group="detail")

            if tm.get("cooling_towers"):
                n_ct = tm["cooling_towers"]
                for i in range(n_ct):
                    ox = cx - 12.0 + i * 4.8
                    oy = cy + 1.0 - i * 0.8
                    self.mb.oct_prism(ox, oy, z2, z2 + 2.6, 2.0, self.tt("np_pier_conc"), top_tex=self.tt("np_shutter"), group="detail")

            if "columns" in tm:
                for col_x, col_y in tm["columns"]:
                    self.mb.oct_prism(col_x, col_y, 0.0, z1, 0.45, self.tt("np_white_pnl"), group="detail")

            if "pylon" in tm:
                px, py, pz1, pz2 = tm["pylon"]
                self.mb.oct_prism(px, py, pz1, pz2, 0.55, self.tt("np_pier_conc"), group="detail")

            if "ptt_totem" in tm:
                tx_p, ty_p, tz1, tz2 = tm["ptt_totem"]
                self.mb.aabb(tx_p - 0.25, ty_p - 0.65, tz1, tx_p + 0.25, ty_p + 0.65, tz2 - 1.8, self.tt("np_umb_blue"), group="detail")
                self.mb.aabb(tx_p - 0.28, ty_p - 0.70, tz2 - 1.8, tx_p + 0.28, ty_p + 0.70, tz2, self.ft("np_ptt_can"), group="detail")
            if "ptt_roadside_fascia" in tm:
                fx1, fx2, fy1, fy2, fz1, fz2 = tm["ptt_roadside_fascia"]
                self.mb.aabb(
                    fx1, fy1, fz1, fx2, fy2, fz2,
                    self.tt("np_umb_blue"),
                    faces={"e": self.ft("np_ptt_can", 2.0, 1.0), "b": self.tt("np_white_pnl")},
                    group="detail",
                )

        # Nana Hotel outdoor swimming pool (z20_sat_grid.jpg)
        pl = self.landmarks["nana_hotel_pool"]
        self.mb.aabb(pl["x1"], pl["y1"], 0.0, pl["x2"], pl["y2"], pl["z2"], self.tt(pl["tex"]), group="detail")

    # ------------------------------------------------------------------
    # STAGE 4A: NANA PLAZA 3-STOREY COMPLEX + ROOM-BY-ROOM INTERIORS
    # ------------------------------------------------------------------
    def build_stage4a_nana_plaza(self):
        lv = self.plaza["levels"]
        z1, z2, z3, ze = lv["z_1f"], lv["z_2f"], lv["z_3f"], lv["z_eave"]
        cy = self.plaza["courtyard"]
        cs1, cs2 = cy["s1"], cy["s2"]             # 13.0 .. 41.2
        cw1, cw2 = cy["w1"], cy["w2"]             # -8.2 .. +8.2
        ww = cy["walkway_width_m"]                # 3.0m
        eww = cy.get("east_walkway_width_m", ww)  # 2.6m
        wd = cy["wing_depth_m"]                   # 5.2m
        ewd = cy["east_wing_depth_m"]             # 2.4m
        s_n_max = cy["north_wing_s_max"]          # 43.8m
        s_s_min = cy["south_wing_s_min"]          # 16.5m

        w_in_n = cw2 + ww                         # +11.2m
        w_out_n = w_in_n + wd                     # +16.4m
        w_in_s = cw1 - ww                         # -11.2m
        w_out_s = w_in_s - wd                     # -16.4m
        s_in_e = cs2 + eww                        # +43.8m
        s_out_e = s_in_e + ewd                    # +46.2m

        # 1. Ground Floor Paving:
        # West Entrance Throat & Forecourt (s=0..13.0, w=-8.2..+8.2): washed-aggregate forecourt concrete
        self.mb.pbox(0.0, cw1, -0.02, cs1, cw2, z1, self.tt("np_forecrt"), group="detail")
        # Central Open-Air Courtyard + Walkways (s=13.0..43.8, w=-11.2..+11.2): red-brick herringbone paving!
        self.mb.pbox(cs1, w_in_s, -0.02, s_in_e, w_in_n, z1, self.tt("np_brick_cy"), group="detail")

        # West Forecourt Ground-Truth Features (Spirit House, Security Bag-Check, ATM, Luke's Tiki Bar, Temptations 1F):
        # Ornate Golden Spirit House Shrine (ref_190, ref_255)
        self.mb.pbox(8.5, -4.4, z1, 9.9, -3.0, z1 + 0.55, self.tt("np_brick_col"), group="detail")
        self.mb.pbox(8.7, -4.2, z1 + 0.55, 9.7, -3.2, z1 + 2.35, self.ft("np_shrine_gd"), group="detail")
        # Yellow storage container + dark bar front on South Forecourt (ref_190, ref_255, ref_018)
        self.mb.pbox(4.8, -8.2, z1, 7.6, -6.4, z1 + 2.35, self.tt("np_awn_ylw"), group="detail")
        self.mb.pbox(7.8, -8.2, z1, 9.6, -6.0, z1 + 1.05, self.tt("np_mahog_wd"), group="detail")
        # Security Bag-Check Table + Chrome Stanchions & Red Barrier at Entrance Throat (ref_031, gallery_stripped.html L33)
        self.mb.pbox(2.4, -3.6, z1, 3.2, -2.0, z1 + 0.86, self.tt("np_mahog_wd"), group="detail")
        self.mb.pbox(2.6, -1.9, z1, 2.9, -1.6, z1 + 0.96, self.tt("np_chrome"), group="detail")
        self.mb.pbox(2.7, -3.6, z1 + 0.88, 2.8, -1.7, z1 + 0.96, self.tt("np_red_pnt"), group="detail")
        # CIMB / SCB ATM Kiosk on North Entrance Pier (gallery_stripped.html L33, ref_001.jpg)
        self.mb.pbox(2.4, 4.0, z1, 3.6, 4.9, z1 + 2.15, self.tt("np_white_pnl"), faces={"right": self.tt("np_awn_ylw")}, group="detail")
        # Luke's Tiki Bar + Blue Awning on North West Forecourt (ref_190.jpg)
        self.mb.pbox(7.0, 5.4, z1, 10.2, 6.2, z1 + 1.04, self.tt("np_mahog_wd"), group="detail")
        self.mb.sloped_slab_plaza(6.8, 10.2, 4.8, z1 + 2.35, 7.6, z1 + 2.95, 0.10, self.tt("np_umb_blue"), group="detail")
        self.mb.pbox(6.8, 4.72, z1 + 2.10, 10.2, 4.86, z1 + 2.45, self.tt("np_umb_blue"), faces={"right": self.ft("np_lukes_tiki")}, group="detail")
        # Temptations 1F Open Sports-TV Bar Counter immediately West of Front-North Stairs (ref_247.jpg — cam_10 left!)
        self.mb.pbox(10.2, 8.3, z1, 13.5, 8.7, z1 + 2.75, self.tt("np_bar_dark"), group="detail")
        self.mb.pbox(10.7, 8.18, z1 + 1.65, 11.7, 8.30, z1 + 2.22, self.tt("np_slat_blk"), faces={"right": self.ft("np_tv_pitch")}, group="detail")
        self.mb.pbox(12.0, 8.18, z1 + 1.65, 13.0, 8.30, z1 + 2.22, self.tt("np_slat_blk"), faces={"right": self.ft("np_tv_pitch")}, group="detail")
        self.mb.pbox(10.4, 5.6, z1, 13.4, 6.2, z1 + 1.02, self.tt("np_slat_blk"), group="detail")
        self.mb.pbox(10.35, 5.55, z1 + 1.02, 13.45, 6.25, z1 + 1.10, self.tt("np_mahog_wd"), group="detail")
        self.mb.plight(11.9, 7.0, z1 + 2.25, val=185, color="1.0 0.72 0.48")

        # 2. Central Courtyard Beer Garden Island Bars, Umbrellas, Chang Dispensers & Bunting (ref_018, ref_208, ref_297)
        for ib in cy["island_bars"]:
            bs1, bs2, bw1, bw2 = ib["s1"], ib["s2"], ib["w1"], ib["w2"]
            cth = 0.55
            self.mb.pbox(bs1, bw1, z1, bs2, bw1 + cth, z1 + 1.05, self.tt("np_mahog_wd"), group="detail")
            self.mb.pbox(bs1, bw2 - cth, z1, bs2, bw2, z1 + 1.05, self.tt("np_mahog_wd"), group="detail")
            self.mb.pbox(bs1, bw1 + cth, z1, bs1 + cth, bw2 - cth, z1 + 1.05, self.tt("np_mahog_wd"), group="detail")
            self.mb.pbox(bs2 - cth, bw1 + cth, z1, bs2, bw2 - cth, z1 + 1.05, self.tt("np_mahog_wd"), group="detail")
            # Central liquor-rack / TV gantry frame (lowered on East island so cam_11 rear bar signs are 100% unobstructed!)
            sm = 0.5 * (bs1 + bs2)
            z_cad = z1 + (1.32 if "East" in ib["name"] else 2.05)
            self.mb.pbox(sm - 1.5, -0.42, z1, sm + 1.5, 0.42, z_cad, self.tt("np_slat_blk"), group="detail")
            # Yellow & red beer-tower dispensers on counter corners (visible in cam_11 / ref_297!)
            for tw_s in (bs1 + 0.8, bs2 - 0.8):
                self.mb.pbox(tw_s - 0.12, bw1 + 0.12, z1 + 1.05, tw_s + 0.12, bw1 + 0.36, z1 + 1.58, self.tt("np_awn_ylw"), group="detail")
                self.mb.pbox(tw_s - 0.12, bw2 - 0.36, z1 + 1.05, tw_s + 0.12, bw2 - 0.12, z1 + 1.58, self.tt("np_red_pnt"), group="detail")
            # Bar stools around perimeter
            for st_s in range(int(bs1) + 1, int(bs2), 2):
                for st_w in (bw1 - 0.52, bw2 + 0.52):
                    self.mb.pbox(st_s - 0.18, st_w - 0.18, z1, st_s + 0.18, st_w + 0.18, z1 + 0.74, self.tt("np_mahog_wd"), group="detail")
            # High wooden communal tables beside North & South walkways (shifted east of West-courtyard pickup!)
            t_off = 2.6 if "West" in ib["name"] else 1.2
            self.mb.pbox(bs1 + t_off, bw2 + 1.3, z1 + 0.85, bs1 + t_off + 2.6, bw2 + 2.2, z1 + 0.96, self.tt("np_mahog_wd"), group="detail")
            self.mb.pbox(bs1 + t_off + 0.2, bw2 + 1.5, z1, bs1 + t_off + 0.4, bw2 + 2.0, z1 + 0.85, self.tt("np_slat_blk"), group="detail")
            self.mb.pbox(bs1 + t_off + 2.2, bw2 + 1.5, z1, bs1 + t_off + 2.4, bw2 + 2.0, z1 + 0.85, self.tt("np_slat_blk"), group="detail")
            self.mb.pbox(bs2 - 3.6, bw1 - 2.1, z1 + 0.85, bs2 - 1.0, bw1 - 1.3, z1 + 0.96, self.tt("np_mahog_wd"), group="detail")
            self.mb.pbox(bs2 - 3.3, bw1 - 1.9, z1, bs2 - 3.1, bw1 - 1.5, z1 + 0.85, self.tt("np_slat_blk"), group="detail")
            self.mb.pbox(bs2 - 1.5, bw1 - 1.9, z1, bs2 - 1.3, bw1 - 1.5, z1 + 0.85, self.tt("np_slat_blk"), group="detail")

        # Cluster of turquoise & blue Beer Garden parasols across West/Mid courtyard (ref_018 cam_14, kept west of s=30 so cam_11 is 100% clear!)
        for ps_s, ps_w, ps_tex in (
            (18.5, -4.5, "np_umb_blue"),
            (22.5, 0.0, "np_umb_turq"),
            (26.8, 0.0, "np_umb_blue"),
            (24.5, -4.8, "np_umb_turq"),
            (29.0, 4.4, "np_umb_turq"),
        ):
            ux, uy = plaza_to_world(ps_s, ps_w)
            z_base_u = z1 + (1.0 if abs(ps_w) < 1.0 else 0.0)
            self.mb.aabb(ux - 0.05, uy - 0.05, z_base_u, ux + 0.05, uy + 0.05, z1 + 2.55, self.tt("np_chrome"), group="detail")
            self.mb.oct_prism(ux, uy, z1 + 2.35, z1 + 2.65, 1.35, self.tt(ps_tex), sides=8, group="detail")

        # Overhead international flag bunting strings across 2F courtyard gallery ({np_bunting, ref_018 — clear of 1F bar signs!)
        for bs_m in cy["bunting_s_m"]:
            self.mb.pbox(bs_m - 0.03, cw1, 4.25, bs_m + 0.03, cw2, 4.95, self.tt("{np_bunting"), group="fence")

        # 3. Upper Perimeter Walkways (2F z=4.15m, 3F z=7.95m — 100% Continuous Loops & Exact Stair Cutouts!)
        for z_flr, is_3f in ((z2, False), (z3, True)):
            zb = z_flr - 0.30
            if not is_3f:
                # 2F North walkway: cut s=13.8..15.8 (w=8.2..9.8) for Front-North 1F->2F, then 100% solid s=15.8..43.0!
                self.mb.pbox(9.8, cw2, zb, 13.8, w_in_n, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(13.8, 9.8, zb, 15.8, w_in_n, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(15.8, cw2, zb, cs2, w_in_n, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
            else:
                # 3F North walkway: solid s=9.8..19.8 (unbroken Erotica NW landing!), cut s=19.8..25.0 (w=8.2..9.80), solid s=25.0..43.0!
                # Underside ('b') uses linear cyan/green LED soffit np_led_cyan (ref_101)!
                f_n3 = {"t": self.tt("np_brick_cy"), "b": self.tt("np_led_cyan")}
                self.mb.pbox(9.8, cw2, zb, 19.8, w_in_n, z_flr, self.tt("np_wall_ochr"), faces=f_n3, group="detail")
                self.mb.pbox(19.8, 9.80, zb, 25.0, w_in_n, z_flr, self.tt("np_wall_ochr"), faces=f_n3, group="detail")
                self.mb.pbox(25.0, cw2, zb, cs2, w_in_n, z_flr, self.tt("np_wall_ochr"), faces=f_n3, group="detail")

            # South walkway (w = -11.2 .. -8.2): cut s=13.6..19.2 on 2F (for 1F->2F) and s=20.6..26.0 on 3F (for 2F->3F)!
            if not is_3f:
                self.mb.pbox(9.8, w_in_s, zb, 13.6, cw1, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(13.6, w_in_s, zb, 19.2, -9.80, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(19.2, w_in_s, zb, cs2, cw1, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
            else:
                self.mb.pbox(9.8, w_in_s, zb, 20.6, cw1, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(20.6, w_in_s, zb, 26.0, -9.80, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(26.0, w_in_s, zb, cs2, cw1, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")

            # East gallery bridge (s = 43.0 .. 46.0, w = -11.2 .. +11.2)
            self.mb.pbox(cs2, w_in_s, zb, s_in_e, w_in_n, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")

            # West gallery bridge:
            # 2F: escalator cutout at s=9.8..11.4, w=-2.2..+0.8, continuous landing s=11.4..13.0!
            # 3F: continuous walkable catwalk loop s=11.4..13.0 across w=-11.2..+11.2 with 0.80m glass rail (open above z=8.75m for arch & GEISHA sightlines!)
            if not is_3f:
                self.mb.pbox(9.8, w_in_s, zb, cs1, -2.2, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(9.8, 0.8, zb, cs1, w_in_n, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(11.4, -2.2, zb, cs1, 0.8, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
            else:
                self.mb.pbox(9.8, w_in_s, zb, 11.4, -3.8, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(9.8, 4.6, zb, 11.4, w_in_n, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")
                self.mb.pbox(11.4, w_in_s, zb, cs1, w_in_n, z_flr, self.tt("np_wall_ochr"), faces={"t": self.tt("np_brick_cy")}, group="detail")

            # Courtyard balustrades & drink rails:
            r_tex_n = self.tt("np_glass_rl") if is_3f else self.tt("np_balust")
            r_tex_s = self.tt("np_glass_rl") if is_3f else self.tt("np_balust")
            if not is_3f:
                self.mb.pbox(15.9, cw2, z_flr, cs2, cw2 + 0.22, z_flr + 0.90, r_tex_n, group="detail")
                self.mb.pbox(19.3, cw1 - 0.16, z_flr, cs2, cw1, z_flr + 0.90, r_tex_s, group="detail")
                self.mb.pbox(cs1 - 0.22, cw1, z_flr, cs1, -2.2, z_flr + 0.88, r_tex_n, group="detail")
                self.mb.pbox(cs1 - 0.08, -2.2, z_flr, cs1, 6.0, z_flr + 0.58, self.tt("{np_ped_rail"), group="fence")
                self.mb.pbox(cs1 - 0.22, 6.0, z_flr, cs1, cw2, z_flr + 0.88, r_tex_n, group="detail")
            else:
                self.mb.pbox(25.1, cw2, z_flr, cs2, cw2 + 0.22, z_flr + 0.92, r_tex_n, group="detail")
                self.mb.pbox(cs1, cw2, z_flr, 19.7, cw2 + 0.22, z_flr + 0.92, r_tex_n, group="detail")
                self.mb.pbox(26.1, cw1 - 0.22, z_flr, cs2, cw1, z_flr + 0.92, r_tex_s, group="detail")
                self.mb.pbox(cs1, cw1 - 0.22, z_flr, 20.5, cw1, z_flr + 0.92, r_tex_s, group="detail")
                self.mb.pbox(cs1 - 0.20, cw1, z_flr, cs1, -3.8, z_flr + 0.80, r_tex_n, group="detail")
                self.mb.pbox(cs1 - 0.08, -3.8, z_flr, cs1, 4.6, z_flr + 0.80, self.tt("{np_ped_rail"), group="fence")
                self.mb.pbox(cs1 - 0.20, 4.6, z_flr, cs1, cw2, z_flr + 0.80, r_tex_n, group="detail")
                self.mb.pbox(11.4, -3.8, z_flr, 11.48, 4.6, z_flr + 0.80, self.tt("{np_ped_rail"), group="fence")
            self.mb.pbox(cs2, cw1, z_flr, cs2 + 0.22, cw2, z_flr + 0.92, r_tex_n, group="detail")

        # Continuous 3F Walkway Ceiling Soffit (prevents any raw sky leak above 3F storefronts like Erotica in cam_16!)
        self.mb.pbox(9.8, cw2, ze - 0.25, s_n_max, w_in_n, ze, self.tt("np_wall_ochr"), group="detail")
        self.mb.pbox(9.8, w_in_s, ze - 0.25, s_in_e, cw1, ze, self.tt("np_wall_ochr"), group="detail")
        self.mb.pbox(cs2, w_in_s, ze - 0.25, s_in_e, w_in_n, ze, self.tt("np_wall_ochr"), group="detail")

        # RED DRAGON & BALCONY BAR iconic inner-west 2F/3F fascia facing courtyard (outside central w=-2.4..+4.6 sightline!)
        self.mb.pbox(
            cs1 - 0.15, -8.2, z2 + 1.85, cs1 + 0.18, -2.4, z2 + 3.40,
            self.tt("np_slat_blk"),
            faces={"front": self.ft("np_reddragon")},
            group="detail",
        )
        self.mb.plight(cs1 + 0.9, -5.3, z2 + 2.6, val=210, color="1.0 0.58 0.28")
        self.mb.pbox(
            cs1 - 0.15, 5.8, z2 + 2.30, cs1 + 0.18, 8.2, z2 + 3.30,
            self.tt("np_slat_blk"),
            faces={"front": self.ft("np_balcony_b")},
            group="detail",
        )
        # TEMPTATIONS / MERCURY overhead lintel banner facing West Forecourt above escalators (z=6.9..7.7m so cam_18 -> GEISHA is 100% open!)
        self.mb.pbox(9.6, -2.8, z3 - 1.05, 9.9, 2.4, z3 - 0.25, self.tt("np_slat_blk"), faces={"back": self.ft("np_tempt_mrc")}, group="detail")

        # Pitched dark-brown clay-tile inner roof eaves on 3F around courtyard (trimmed strictly to w_in_n / w_in_s so they NEVER poke inside 3F rooms!)
        self.mb.sloped_slab_plaza(12.5, cs2 + 0.8, cw2 - 0.35, ze - 0.80, w_in_n - 0.05, ze + 0.10, 0.16, self.tt("np_roof_tile"), group="detail")
        self.mb.sloped_slab_plaza(12.5, cs2 + 0.8, w_in_s + 0.05, ze + 0.10, cw1 + 0.35, ze - 0.80, 0.16, self.tt("np_roof_tile"), group="detail")

        # Structural walkway columns around courtyard (skipping stairs & keeping cam_11 -> Obsession 100% unobstructed!)
        for col_s in (13.2, 28.5, cs2):
            self.mb.pbox(col_s - 0.18, cw2 + 0.14 - 0.18, z1, col_s + 0.18, cw2 + 0.14 + 0.18, ze, self.tt("np_wall_ochr"), group="detail")
        for col_s in (13.2, 28.5, 35.8, cs2):
            self.mb.pbox(col_s - 0.18, cw1 - 0.14 - 0.18, z1, col_s + 0.18, cw1 - 0.14 + 0.18, ze, self.tt("np_wall_ochr"), group="detail")

        # 4. All Walkable Staircases, Dual Escalators & Passenger Lift Shaft (100% Passable!)
        sl = self.plaza["stairs_and_lifts"]
        # Front-North curved-base stone-balustrade stairs climbing +w North (1F -> 2F, ref_247, ref_057)
        fn1 = sl["front_north_1f_2f"]
        self.mb.pbox(fn1["s1"] - 0.45, fn1["w1"] - 1.10, z1, fn1["s2"] + 0.45, fn1["w1"], z1 + 0.20, self.tt("np_wall_ochr"), faces={"t": self.tt("np_forecrt")}, group="detail")
        self.mb.pstairs(fn1["s1"], fn1["w1"], fn1["s2"], fn1["w2"], z1 + 0.20, z2, 19, "+w")
        self.mb.sloped_slab_plaza(fn1["s1"] - 0.16, fn1["s1"], fn1["w1"], z1 + 1.05, fn1["w2"], z2 + 0.90, 0.82, self.tt("np_balust"))
        self.mb.sloped_slab_plaza(fn1["s2"], fn1["s2"] + 0.16, fn1["w1"], z1 + 1.05, fn1["w2"], z2 + 0.90, 0.82, self.tt("np_balust"))

        # Front-North 2F -> 3F stairs + 'Billboard 3rd floor ->' sign (ref_139)
        fn2 = sl["front_north_2f_3f"]
        self.mb.pstairs(fn2["s1"], fn2["w1"], fn2["s2"], fn2["w2"], z2, z3, 18, "+s")
        self.mb.pbox(fn2["s1"] + 0.6, fn2["w2"], z2 + 1.35, fn2["s1"] + 2.4, fn2["w2"] + 0.10, z2 + 2.25, self.ft("np_billb_arr"), group="detail")

        # Front-South stairs (1F -> 2F at s=13.6..19.2, then 2F -> 3F at s=20.6..26.0 — zero slab collisions!)
        fs1 = sl["front_south_1f_2f"]
        self.mb.pstairs(fs1["s1"], fs1["w1"], fs1["s2"], fs1["w2"], z1, z2, 19, "+s")
        self.mb.sloped_s_plaza(fs1["s1"], z1 + 0.95, fs1["s2"], z2 + 0.90, fs1["w2"], fs1["w2"] + 0.16, 0.80, self.tt("np_balust"))
        fs2 = sl["front_south_2f_3f"]
        self.mb.pstairs(fs2["s1"], fs2["w1"], fs2["s2"], fs2["w2"], z2, z3, 18, "+s")

        # West Dual Escalators (1F -> 2F, clear open throat overhead!)
        esc = sl["west_escalators_1f_2f"]
        self.mb.pstairs(esc["s1"], esc["w1"], esc["s2"], -0.8, z1, z2, 20, "+s", tex_tread="np_shutter", tex_side="np_shutter")
        self.mb.pstairs(esc["s1"], -0.6, esc["s2"], esc["w2"], z1, z2, 20, "+s", tex_tread="np_shutter", tex_side="np_shutter")
        for ew_pos in (esc["w1"] - 0.12, -0.7, esc["w2"] + 0.12):
            self.mb.sloped_s_plaza(esc["s1"], z1 + 0.82, esc["s2"], z2 + 0.72, ew_pos - 0.08, ew_pos + 0.08, 0.68, self.tt("np_glass_rl"))

        # Passenger Lift (Elevator) Shaft with stainless-steel doors on 1F, 2F, 3F (ref_058, ref_130)
        lf = sl["lift_shaft"]
        self.mb.pbox(lf["s1"], lf["w1"], z1, lf["s2"], lf["w2"], ze, self.tt("np_wall_ochr"), group="detail")
        for zf in (z1, z2, z3):
            self.mb.pbox(lf["s1"] + 0.40, lf["w1"] - 0.08, zf, lf["s2"] - 0.40, lf["w1"], zf + 2.20, self.ft("np_lift_door"), group="detail")

        # NE Enclosed Stairwell (s=39.0..43.8, w=11.2..15.6 — 1.40m landings for smooth world-AABB player turns + Pop-Art Mural ref_187!)
        nes = sl["ne_enclosed_stairwell"]
        zh1 = 0.5 * (z1 + z2)
        zh2 = 0.5 * (z2 + z3)
        self.mb.pbox(nes["s1"] - 0.22, nes["w1"], z1, nes["s1"], nes["w2"], ze, self.tt("np_wall_ochr"), group="world")
        self.mb.pbox(nes["s1"] - 0.22, nes["w2"], z1, nes["s2"], nes["w2"] + 0.25, ze, self.tt("np_wall_ochr"), group="world")
        self.mb.pstairs(nes["s1"] + 1.40, nes["w1"] + 0.1, nes["s2"] - 1.40, nes["w1"] + 1.6, z1, zh1, 9, "+s")
        self.mb.pbox(nes["s2"] - 1.40, nes["w1"], zh1 - 0.25, nes["s2"], nes["w2"], zh1, self.tt("np_wall_ochr"), faces={"t": self.tt("np_stair_trd")}, group="detail")
        self.mb.pstairs(nes["s1"] + 1.40, nes["w2"] - 1.6, nes["s2"] - 1.40, nes["w2"] - 0.1, zh1, z2, 9, "-s")
        self.mb.pbox(nes["s1"], nes["w1"], z2 - 0.25, nes["s1"] + 1.40, nes["w2"], z2, self.tt("np_wall_ochr"), faces={"t": self.tt("np_stair_trd")}, group="detail")
        self.mb.pbox(nes["s2"] - 0.08, nes["w1"] + 0.8, z2 + 0.15, nes["s2"], nes["w1"] + 3.6, z2 + 2.95, self.ft("np_mural"), group="detail")
        self.mb.pstairs(nes["s1"] + 1.40, nes["w1"] + 0.1, nes["s2"] - 1.40, nes["w1"] + 1.6, z2, zh2, 9, "+s")
        self.mb.pbox(nes["s2"] - 1.40, nes["w1"], zh2 - 0.25, nes["s2"], nes["w2"], zh2, self.tt("np_wall_ochr"), faces={"t": self.tt("np_stair_trd")}, group="detail")
        self.mb.pstairs(nes["s1"] + 1.40, nes["w2"] - 1.6, nes["s2"] - 1.40, nes["w2"] - 0.1, zh2, z3, 9, "-s")
        self.mb.pbox(nes["s1"], nes["w1"], z3 - 0.25, nes["s1"] + 1.40, nes["w2"], z3, self.tt("np_wall_ochr"), faces={"t": self.tt("np_stair_trd")}, group="detail")
        self.mb.pbox(nes["s1"] + 0.02, nes["w2"] - 0.85, z3 + 1.25, nes["s1"] + 0.10, nes["w2"] - 0.40, z3 + 1.85, self.ft("np_fl3_plq"), group="detail")

        # SE Enclosed Cream-Ochre Stairwell (s=42.25..46.15, w=-16.1..-11.2 — 1.45m landings + 1.55m open doorway s=42.25..43.80 onto East gallery!)
        ses = sl["se_enclosed_stairwell"]
        self.mb.pbox(ses["s1"], w_out_s, -0.02, ses["s2"], w_in_s, z1, self.tt("np_stair_trd"), group="world")
        self.mb.pbox(ses["s2"], w_out_s - 0.35, 0.0, ses["s2"] + 0.35, w_in_s, ze, self.tt("np_wall_ochr"), group="world")
        self.mb.pbox(ses["s1"], w_out_s, z1, ses["s2"], ses["w1"], ze, self.tt("np_wall_ochr"), group="world")
        self.mb.pbox(ses["s1"] - 0.22, w_out_s, z2 - 0.25, ses["s1"], w_in_s, ze, self.tt("np_wall_ochr"), group="world")
        self.mb.pbox(s_in_e, w_in_s, z1, ses["s2"], w_in_s + 0.22, ze, self.tt("np_wall_ochr"), group="world")
        self.mb.pbox(ses["s1"], w_out_s - 0.35, ze, ses["s2"] + 0.35, w_in_s, ze + 0.25, self.tt("np_wall_ochr"), group="world")
        self.mb.pstairs(ses["s1"] + 0.10, ses["w1"] + 1.45, ses["s1"] + 1.60, ses["w2"] - 1.45, z1, zh1, 8, "-w")
        self.mb.pbox(ses["s1"], ses["w1"], zh1 - 0.25, ses["s2"], ses["w1"] + 1.45, zh1, self.tt("np_wall_ochr"), faces={"t": self.tt("np_stair_trd")}, group="detail")
        self.mb.pstairs(ses["s2"] - 1.60, ses["w1"] + 1.45, ses["s2"] - 0.10, ses["w2"] - 1.45, zh1, z2, 8, "+w")
        self.mb.pbox(ses["s1"], ses["w2"] - 1.45, z2 - 0.25, ses["s2"], ses["w2"], z2, self.tt("np_wall_ochr"), faces={"t": self.tt("np_stair_trd")}, group="detail")
        self.mb.pbox(s_in_e + 0.45, w_in_s - 0.08, z2 + 1.25, s_in_e + 0.90, w_in_s, z2 + 1.85, self.ft("np_fl2_plq"), group="detail")
        self.mb.pstairs(ses["s1"] + 0.10, ses["w1"] + 1.45, ses["s1"] + 1.60, ses["w2"] - 1.45, z2, zh2, 8, "-w")
        self.mb.pbox(ses["s1"], ses["w1"], zh2 - 0.25, ses["s2"], ses["w1"] + 1.45, zh2, self.tt("np_wall_ochr"), faces={"t": self.tt("np_stair_trd")}, group="detail")
        self.mb.pstairs(ses["s2"] - 1.60, ses["w1"] + 1.45, ses["s2"] - 0.10, ses["w2"] - 1.45, zh2, z3, 8, "+w")
        self.mb.pbox(ses["s1"], ses["w2"] - 1.45, z3 - 0.25, ses["s2"], ses["w2"], z3, self.tt("np_wall_ochr"), faces={"t": self.tt("np_stair_trd")}, group="detail")

        # 5. Wing Structural Perimeter & Roofs (group="world" for real PVS culling, strictly calibrated to z20_sat_grid.jpg!)
        self.mb.pbox(9.8, w_out_n, 0.0, s_n_max, w_out_n + 0.35, ze, self.tt("np_placehld"), group="world")
        self.mb.pbox(s_s_min, w_out_s - 0.35, 0.0, s_out_e, w_out_s, ze, self.tt("np_placehld"), group="world")
        self.mb.pbox(s_out_e, w_in_s, 0.0, s_out_e + 0.35, 9.8, ze, self.tt("np_placehld"), group="world")
        self.mb.pbox(s_n_max, 9.8, 0.0, s_out_e + 0.35, 10.15, ze, self.tt("np_placehld"), group="world")
        self.mb.pbox(s_n_max, 10.15, 0.0, s_n_max + 0.35, w_out_n + 0.35, ze, self.tt("np_placehld"), group="world")
        self.mb.pbox(s_s_min - 0.35, w_out_s - 0.35, 0.0, s_s_min, w_in_s, ze, self.tt("np_placehld"), group="world")

        # Wing floor/ceiling slabs (stopping z2/z3 slabs outside NE & SE enclosed stairwells so vertical shafts are 100% open!)
        pb = self.plaza["se_pooltable_bar_interior"]
        for z_slab in (z1, z2, z3, ze + 0.25):
            n_s_hi = s_n_max if z_slab in (z1, ze + 0.25) else nes["s1"]
            self.mb.pbox(9.8, w_in_n, z_slab - 0.25, n_s_hi, w_out_n, z_slab, self.tt("np_wall_ochr"), group="world")
            self.mb.pbox(s_s_min, w_out_s, z_slab - 0.25, pb["s1"], w_in_s, z_slab, self.tt("np_wall_ochr"), group="world")
            self.mb.pbox(s_in_e, w_in_s, z_slab - 0.25, s_out_e, 9.8, z_slab, self.tt("np_wall_ochr"), group="world")
        # Slab over SE Pool-Table Bar (s=35.8..42.25, with green-LED ceiling on underside!)
        self.mb.pbox(
            pb["s1"], w_out_s, z2 - 0.25, pb["s2"], w_in_s, z2,
            self.tt("np_wall_ochr"),
            faces={"b": self.tt("np_pool_ceil")},
            group="world",
        )
        for z_slab in (z3, ze + 0.25):
            self.mb.pbox(pb["s1"], w_out_s, z_slab - 0.25, pb["s2"], w_in_s, z_slab, self.tt("np_wall_ochr"), group="world")

        # 6. Ground-Floor Bars (1F) — Open-Front Beer Bars + Unclipped Signs + Clean Material Counters
        self.mb.pbox(s_in_e, w_in_s, z1, s_in_e + 0.28, -2.4, z2 - 0.25, self.tt("np_placehld"), group="detail")
        for b in self.plaza["bars_1f"]:
            if b["wing"] == "north":
                bs1, bs2 = b["s1"], b["s2"]
                self.mb.pbox(bs1, cw2 - 0.22, z1 + 2.50, bs2, cw2 + 0.10, z1 + 3.68, self.tt("np_slat_blk"), faces={"right": self.ft(b["sign"])}, group="detail")
                if b["name"] == "Lollipop":
                    # Clean crimson-red Lollipop bar counter (np_red_pnt — ZERO arch banner text!) + warm red lantern interior wall (np_loll_int)!
                    self.mb.pbox(bs1 + 0.15, 6.2, z1, bs1 + 4.4, 6.85, z1 + 1.02, self.tt("np_red_pnt"), group="detail")
                    self.mb.pbox(bs1, 9.8, z1, bs2, 10.15, z2 - 0.25, self.tt("np_red_pnt"), faces={"right": self.ft("np_loll_int")}, group="detail")
                    self.mb.plight(bs1 + 2.2, 7.6, z1 + 2.3, val=215, color="1.0 0.45 0.36")
                if b.get("awning"):
                    self.mb.sloped_slab_plaza(bs1, bs2, cw2 - 0.85, z1 + 1.98, w_in_n, z1 + 2.45, 0.09, self.tt(b["awning"]), group="detail")
                self.mb.pbox(bs1, w_in_n, z1, bs1 + 0.42, w_in_n + 0.42, z2 - 0.25, self.tt("np_brick_col"), group="detail")
                cnt_s2 = min(bs2 - 0.55, nes["s1"] - 0.35)
                if bs1 + 0.55 < cnt_s2:
                    self.mb.pbox(bs1 + 0.55, w_in_n - 0.2, z1, cnt_s2, w_in_n + 0.42, z1 + 1.05, self.tt("np_red_pnt" if b["name"] == "Lollipop" else "np_mahog_wd"), group="detail")
                rear_n_s2 = min(bs2, nes["s1"] - 0.25)
                if bs1 < rear_n_s2:
                    self.mb.pbox(bs1, w_in_n + 2.8, z1, rear_n_s2, w_in_n + 3.1, z2 - 0.25, self.tt("np_placehld"), group="detail")
            elif b["wing"] == "south":
                bs1, bs2 = b["s1"], b["s2"]
                if b.get("alt_sign"):
                    sm_b = 0.5 * (bs1 + bs2)
                    self.mb.pbox(bs1, cw1 - 0.10, z1 + 2.55, sm_b, cw1 + 0.22, z1 + 3.70, self.tt("np_slat_blk"), faces={"left": self.ft(b["alt_sign"])}, group="detail")
                    self.mb.pbox(sm_b, cw1 - 0.10, z1 + 2.55, bs2, cw1 + 0.22, z1 + 3.70, self.tt("np_slat_blk"), faces={"left": self.ft(b["sign"])}, group="detail")
                elif b["name"] == "London Calling":
                    # Angled SE corner roundel signboard facing NW into courtyard for cam_11 (ref_297) + South fascia!
                    lc_x, lc_y = plaza_to_world(39.8, -6.9)
                    self.mb.obox(lc_x, lc_y, z1 + 2.50, z1 + 3.68, 1.85, 0.15, PLAZA_YAW_DEG + 42.0, self.tt("np_slat_blk"), faces={"left": self.ft(b["sign"]), "right": self.ft(b["sign"])}, group="detail")
                else:
                    self.mb.pbox(bs1, cw1 - 0.10, z1 + 2.55, bs2, cw1 + 0.22, z1 + 3.70, self.tt("np_slat_blk"), faces={"left": self.ft(b["sign"])}, group="detail")
                if b.get("awning"):
                    self.mb.sloped_slab_plaza(bs1, bs2, w_in_s, z1 + 2.45, cw1 + 0.85, z1 + 1.98, 0.09, self.tt(b["awning"]), group="detail")
                if bs1 >= s_s_min and not b.get("skip_ext_counter"):
                    self.mb.pbox(bs1, w_in_s - 0.42, z1, bs1 + 0.42, w_in_s, z2 - 0.25, self.tt("np_brick_col"), group="detail")
                    ct_tex = self.tt(b["inner_tex"]) if b.get("inner_tex") else self.tt("np_mahog_wd")
                    self.mb.pbox(bs1 + 0.55, w_in_s - 0.42, z1, bs2 - 0.55, w_in_s + 0.2, z1 + 1.05, ct_tex, group="detail")
                # Capped strictly west of se_pooltable_bar_interior (pb["s1"] = 35.8) so ZERO wall ever intrudes into cam_12!
                rear_s2 = min(bs2, pb["s1"] - 0.25)
                if not b.get("skip_rear_wall") and max(bs1, s_s_min) < rear_s2 - 0.3:
                    r_tex = self.tt(b["inner_tex"]) if b.get("inner_tex") else self.tt("np_placehld")
                    self.mb.pbox(max(bs1, s_s_min), w_in_s - 2.9, z1, rear_s2, w_in_s - 2.6, z2 - 0.25, r_tex, group="detail")
            elif b["wing"] == "east":
                bw1, bw2 = b["w1"], b["w2"]
                self.mb.pbox(cs2 - 0.15, bw1, z1 + 2.55, cs2 + 0.18, bw2, z1 + 3.70, self.tt("np_slat_blk"), faces={"back": self.ft(b["sign"])}, group="detail")
                itex = self.ft(b["inner_tex"]) if b["inner_tex"] == "np_obs_wall" else self.tt(b["inner_tex"])
                self.mb.pbox(s_in_e + 1.1, bw1, z1, s_in_e + 1.4, bw2, z2 - 0.25, itex, group="detail")

        # 7. FULL ROOM-BY-ROOM INTERIOR: SE Pool-Table Bar (s=35.8..42.25, w=-16.4..-11.2 — 100% Unobstructed Doorway s=37.3..38.8!)
        ps1, ps2, pw1, pw2 = pb["s1"], pb["s2"], pb["w1"], pb["w2"]
        self.mb.pbox(ps1, pw1, -0.02, ps2, pw2, z1, self.tt("np_shutter"), group="detail")
        # West & East interior walls (geometric orange/black/grey polygon accent wall np_pool_wall fitted cleanly!)
        self.mb.pbox(ps1, pw1, z1, ps1 + 0.22, pw2, z2 - 0.25, self.tt(pb["wall_tex"]), group="detail")
        self.mb.pbox(
            ps2 - 0.22, pw1, z1, ps2, pw2, z2 - 0.25,
            self.tt("np_slat_blk"),
            faces={"back": self.ft(pb["wall_tex"], 2.0, 1.0)},
            group="detail",
        )
        # Dark curtained rear doorway on focal East wall + wooden cue rack (ref_083)
        self.mb.pbox(ps2 - 0.28, -14.3, z1, ps2 - 0.21, -13.4, z1 + 2.15, self.tt("np_slat_blk"), group="detail")
        self.mb.pbox(ps2 - 0.29, -15.2, z1, ps2 - 0.21, -14.6, z1 + 1.65, self.tt("np_mahog_wd"), group="detail")
        # South interior wall + doorway notice
        self.mb.pbox(ps1, pw1, z1, ps2, pw1 + 0.25, z2 - 0.25, self.tt(pb["wall_tex"]), group="detail")
        self.mb.pbox(ps2 - 2.3, pw1 + 0.25, z1, ps2 - 1.2, pw1 + 0.33, z1 + 2.20, self.ft(pb["door_tex"]), group="detail")
        # North entrance wall facing courtyard: open walkable doorway (s=37.3..38.8) flanked by 'NO CUSTOMERS NO TOILET PUBLIC' entry door & dark wood bar backwall!
        self.mb.pbox(ps1, pw2 - 0.18, z1, ps1 + 1.5, pw2, z2 - 0.25, self.ft(pb["door_tex"]), group="detail")
        self.mb.pbox(ps1 + 1.5, pw2 - 0.18, z1 + 2.25, ps1 + 3.0, pw2, z2 - 0.25, self.tt("np_slat_blk"), group="detail")
        self.mb.pbox(ps1 + 3.0, pw2 - 0.18, z1, ps2, pw2, z2 - 0.25, self.tt("np_mahog_wd"), group="detail")
        # Regulation Pool Table in center of room (cyan felt np_pool_felt, mahogany rails, 3 hanging dome lamps, ref_083!)
        tc_s, tc_w = pb["table_center_sw"]
        tl_s, tl_w = 0.5 * pb["table_size_sw"][0], 0.5 * pb["table_size_sw"][1]
        self.mb.pbox(tc_s - tl_s + 0.26, tc_w - tl_w + 0.20, z1, tc_s + tl_s - 0.26, tc_w + tl_w - 0.20, z1 + 0.62, self.tt("np_mahog_wd"), group="detail")
        self.mb.pbox(
            tc_s - tl_s, tc_w - tl_w, z1 + 0.62, tc_s + tl_s, tc_w + tl_w, z1 + 0.86,
            self.tt("np_mahog_wd"),
            faces={"t": self.ft(pb["felt_tex"])},
            group="detail",
        )
        for ds_lamp in (-0.72, 0.0, 0.72):
            lx_s = tc_s + ds_lamp
            self.mb.pbox(lx_s - 0.03, tc_w - 0.03, z1 + 2.25, lx_s + 0.03, tc_w + 0.03, z2 - 0.25, self.tt("np_chrome"), group="detail")
            self.mb.pbox(lx_s - 0.22, tc_w - 0.22, z1 + 2.12, lx_s + 0.22, tc_w + 0.22, z1 + 2.26, self.tt("np_slat_blk"), group="detail")
        self.mb.plight(tc_s, tc_w, z1 + 1.95, val=210, color="0.72 1.0 0.90")
        self.mb.plight(ps1 + 1.5, tc_w, z1 + 2.9, val=165, color="0.45 1.0 0.72")
        # Left side (North wall inside room): mahogany bar counter + clean red cooler (np_red_pnt) + football broadcast TV (np_tv_pitch)!
        self.mb.pbox(ps1 + 3.1, pw2 - 1.05, z1, ps1 + 6.1, pw2 - 0.22, z1 + 1.04, self.tt("np_mahog_wd"), group="detail")
        self.mb.pbox(ps1 + 5.0, pw2 - 1.50, z1, ps1 + 6.1, pw2 - 1.05, z1 + 0.72, self.tt("np_red_pnt"), group="detail")
        self.mb.pbox(ps1 + 2.9, pw2 - 0.30, z1 + 1.75, ps1 + 4.5, pw2 - 0.20, z1 + 2.65, self.tt("np_slat_blk"), faces={"right": self.ft("np_tv_pitch")}, group="detail")
        # Right side (South wall inside room): cocktail tables & clean green-cushioned bar stools (np_stool_gn)!
        for rt_s in (ps1 + 2.7, ps1 + 4.1, ps1 + 5.5):
            self.mb.pbox(rt_s - 0.28, pw1 + 0.85, z1 + 0.76, rt_s + 0.28, pw1 + 1.40, z1 + 0.82, self.tt("np_mahog_wd"), group="detail")
            self.mb.pbox(rt_s - 0.05, pw1 + 1.08, z1, rt_s + 0.05, pw1 + 1.18, z1 + 0.76, self.tt("np_chrome"), group="detail")
            self.mb.pbox(rt_s - 0.16, pw1 + 1.50, z1, rt_s + 0.16, pw1 + 1.82, z1 + 0.68, self.tt("np_stool_gn"), group="detail")

        # 8. Middle-Floor Bars (2F, z=4.15..7.65m — Open w=-3.8..+4.6 West Throat!)
        for b in self.plaza["bars_2f"]:
            if b["wing"] == "west":
                bw1, bw2 = b["w1"], b["w2"]
                ftex = self.tt("np_placehld") if b["face_tex"] == "np_placehld" else self.ft(b["face_tex"])
                self.mb.pbox(9.4, bw1, z2, 9.8, bw2, z3 - 0.30, self.tt("np_wall_ochr"), faces={"front": ftex}, group="detail")
            elif b["wing"] == "north":
                bs1, bs2 = b["s1"], b["s2"]
                ftex = self.tt(b.get("tile_tex", b["face_tex"])) if b["face_tex"] == "np_wall_ochr" else self.ft(b["face_tex"])
                self.mb.pbox(bs1, w_in_n, z2, bs2, w_in_n + 0.28, z3 - 0.30, self.tt("np_wall_ochr"), faces={"right": ftex}, group="detail")
                if b.get("sign"):
                    self.mb.pbox(bs1 + 0.5, w_in_n - 0.16, z2 + 2.25, bs2 - 0.5, w_in_n, z2 + 3.22, self.tt("np_slat_blk"), faces={"right": self.ft(b["sign"])}, group="detail")
                if b.get("blade_sign"):
                    sm_b = 0.5 * (bs1 + bs2)
                    self.mb.pbox(sm_b - 0.06, cw2 + 0.2, z2 + 2.0, sm_b + 0.06, cw2 + 1.7, z2 + 3.3, self.ft(b["blade_sign"]), group="detail")
                if b.get("walkway_bar"):
                    # DC-10 / Sexy Night wooden walkway drink rail & pink cushion bar stools (np_stool_pk + np_chrome — ZERO car textures!)
                    self.mb.pbox(bs1 + 0.3, cw2 + 0.22, z2 + 0.88, bs2 - 0.3, cw2 + 0.62, z2 + 0.98, self.tt("np_mahog_wd"), group="detail")
                    for st_s in range(int(bs1) + 1, int(bs2), 2):
                        self.mb.pbox(st_s - 0.05, cw2 + 0.78, z2, st_s + 0.05, cw2 + 0.88, z2 + 0.62, self.tt("np_chrome"), group="detail")
                        self.mb.pbox(st_s - 0.18, cw2 + 0.66, z2 + 0.62, st_s + 0.18, cw2 + 1.00, z2 + 0.74, self.tt("np_stool_pk"), group="detail")
            elif b["wing"] == "east":
                bw1, bw2 = b["w1"], b["w2"]
                ftex = self.tt("np_placehld") if b["face_tex"] == "np_placehld" else self.ft(b["face_tex"])
                self.mb.pbox(s_in_e, bw1, z2, s_in_e + 0.28, bw2, z3 - 0.30, self.tt("np_wall_ochr"), faces={"back": ftex}, group="detail")
                if b.get("sign"):
                    # Casanova BAR glowing sign + white bar counter flush at East end of 2F North walkway (1.83m clear walkway — ref_101)!
                    self.mb.pbox(s_in_e - 0.25, 8.3, z2 + 1.75, s_in_e - 0.02, 11.0, z2 + 2.95, self.tt("np_slat_blk"), faces={"back": self.ft(b["sign"])}, group="detail")
                    self.mb.pbox(s_in_e - 0.55, 8.4, z2, s_in_e - 0.05, 10.9, z2 + 1.02, self.tt("np_white_pnl"), group="detail")
            elif b["wing"] == "south":
                bs1, bs2 = b["s1"], b["s2"]
                self.mb.pbox(bs1, w_in_s - 0.28, z2, bs2, w_in_s, z3 - 0.30, self.tt(b["face_tex"]), group="detail")
        # 'ENTER ->' directional walkway sign on 2F East corner (ref_231)
        self.mb.pbox(cs2 - 0.3, cw2 - 0.10, z2 + 2.15, cs2 + 1.2, cw2 + 0.04, z2 + 2.80, self.ft("np_enter_sgn"), group="detail")

        # 9. Top-Floor Bars (3F, z=7.95..11.20m) + NW EROTICA 3F + EXPLICITLY LABELLED BILLBOARD STAGE ROOM!
        for b in self.plaza["bars_3f"]:
            if b["wing"] == "west":
                self.mb.pbox(9.4, b["w1"], z3, 9.8, b["w2"], ze - 0.25, self.tt(b["face_tex"]), group="detail")
            elif b["wing"] == "north":
                bs1, bs2 = b["s1"], b["s2"]
                if b.get("is_erotica3"):
                    # Erotica 3F at its true NW 3F corner (Plan A ref_003 & ref_137) + WELCOME blade + 2-step NW terrazzo corner platform!
                    self.mb.pbox(13.0, w_in_n, z3, bs1, w_in_n + 0.28, ze - 0.25, self.tt("np_wall_ochr"), group="detail")
                    self.mb.pbox(bs1, w_in_n, z3, bs2, w_in_n + 0.28, ze - 0.25, self.tt("np_wall_ochr"), faces={"right": self.ft("np_erotica3")}, group="detail")
                    self.mb.pbox(bs1 - 0.26, w_in_n - 0.55, z3 + 1.65, bs1 - 0.02, w_in_n, z3 + 2.58, self.tt("np_slat_blk"), faces={"front": self.ft("np_welcome_v"), "back": self.ft("np_welcome_v"), "right": self.ft("np_welcome_v")}, group="detail")
                    self.mb.pbox(13.0, 9.55, z3, 15.6, w_in_n, z3 + 0.15, self.tt("np_forecrt"), group="detail")
                    self.mb.pbox(13.0, 10.05, z3 + 0.15, 14.8, w_in_n, z3 + 0.30, self.tt("np_forecrt"), group="detail")
                elif b.get("has_stage_room"):
                    # Billboard Bangkok 3F walkway facade: single clean fitted sign on walkway side ('right') ONLY, np_placehld on interior ('left')!
                    self.mb.pbox(bs1, w_in_n, z3, 24.0, w_in_n + 0.28, ze - 0.25, self.tt("np_placehld"), group="detail")
                    self.mb.pbox(24.0, w_in_n, z3 + 2.25, 25.8, w_in_n + 0.28, ze - 0.25, self.tt("np_placehld"), group="detail")
                    self.mb.pbox(
                        25.8, w_in_n, z3, 32.4, w_in_n + 0.28, ze - 0.25,
                        self.tt("np_placehld"),
                        faces={"right": self.ft("np_billboard")},
                        group="detail",
                    )
                    self.mb.pbox(32.4, w_in_n, z3, bs2, w_in_n + 0.28, ze - 0.25, self.tt("np_placehld"), group="detail")
                    # Unphotographed interior side partitions use plain np_placehld (logged in gaps.md)!
                    self.mb.pbox(bs1, w_in_n + 0.28, z3, bs1 + 0.25, w_out_n, ze - 0.25, self.tt("np_placehld"), group="detail")
                    self.mb.pbox(bs2 - 0.25, w_in_n + 0.28, z3, bs2, w_out_n, ze - 0.25, self.tt("np_placehld"), group="detail")
                    # Central raised stage carpeted in white plush fur (np_bill_fur + np_mahog_wd apron, ref_028.jpg)!
                    self.mb.pbox(
                        26.6, w_in_n + 1.4, z3, 33.4, w_in_n + 3.4, z3 + 0.56,
                        self.tt("np_mahog_wd"),
                        faces={"t": self.tt("np_bill_fur")},
                        group="detail",
                    )
                    # Overhead glowing cyan/purple carousel ring + brushed chrome dance poles (np_chrome — ZERO elevator doors!)
                    self.mb.pbox(26.8, w_in_n + 1.6, ze - 0.65, 33.2, w_in_n + 3.2, ze - 0.35, self.tt("np_led_cyan"), group="detail")
                    for pole_s in (28.2, 30.0, 31.8):
                        self.mb.pbox(pole_s - 0.04, w_in_n + 2.36, z3 + 0.56, pole_s + 0.04, w_in_n + 2.44, ze - 0.65, self.tt("np_chrome"), group="detail")
                    # Backlit liquor bottle shelf bar along back wall (np_bill_bar + np_mahog_wd counter, ref_028.jpg)!
                    self.mb.pbox(26.2, w_out_n - 0.55, z3 + 0.90, 34.0, w_out_n - 0.08, z3 + 2.35, self.tt("np_bill_bar"), group="detail")
                    self.mb.pbox(26.2, w_out_n - 1.25, z3, 34.0, w_out_n - 0.75, z3 + 1.02, self.tt("np_mahog_wd"), group="detail")
                    # Explicit interior room label ('Billboard BANGKOK' neon plaque above bottle bar, per prompt & gallery guide!)
                    self.mb.pbox(
                        28.2, w_out_n - 0.62, z3 + 2.38, 32.0, w_out_n - 0.50, z3 + 3.12,
                        self.tt("np_slat_blk"),
                        faces={"right": self.ft("np_billboard")},
                        group="detail",
                    )
                    self.mb.plight(30.0, w_in_n + 2.4, z3 + 2.3, val=220, color="0.92 0.55 1.0")
                else:
                    self.mb.pbox(bs1, w_in_n, z3, bs2, w_in_n + 0.28, ze - 0.25, self.tt(b["face_tex"]), group="detail")
            elif b["wing"] == "east":
                bw1, bw2 = b["w1"], b["w2"]
                self.mb.pbox(s_in_e, bw1, z3, s_in_e + 0.28, bw2, ze - 0.25, self.tt(b["face_tex"]), group="detail")
                if b.get("sign"):
                    # GEISHA sign on 3F East storefront wall north of escalators (clear in cam_18 ref_020, occluded from steep courtyard below in cam_11 ref_297)!
                    self.mb.pbox(s_in_e - 0.32, 0.8, z3 + 1.55, s_in_e - 0.04, 8.0, z3 + 3.05, self.tt("np_slat_blk"), faces={"back": self.ft(b["sign"])}, group="detail")
                    self.mb.plight(s_in_e - 0.9, 4.4, z3 + 2.3, val=260, color="1.0 0.82 0.88")
            elif b["wing"] == "south":
                bs1, bs2 = b["s1"], b["s2"]
                ftex = self.tt("np_placehld") if b["face_tex"] == "np_placehld" else self.ft(b["face_tex"], 2.0, 1.0)
                self.mb.pbox(bs1, w_in_s - 0.28, z3, bs2, w_in_s, ze - 0.25, ftex, group="detail")
                if b.get("sign"):
                    self.mb.pbox(bs1 + 3.0, cw1 - 0.15, z3 + 1.5, bs1 + 6.2, cw1 + 0.18, z3 + 3.0, self.ft(b["sign"]), group="detail")

    # ------------------------------------------------------------------
    # STAGE 4B: SURROUNDING LOT-BY-LOT BUILDINGS
    # ------------------------------------------------------------------
    def build_stage4b_buildings(self):
        for lot in self.buildings["soi4_east_lots"]:
            if lot.get("is_exchange_booth"):
                # 3-part PRO EXCHANGE booth (ref_031, ref_032, ref_182): dark step + clean white panel booth + blue EXCHANGE fascia!
                x1, x2, y1, y2 = lot["x1"], lot["x2"], lot["y1"], lot["y2"]
                self.mb.aabb(x1 - 0.20, y1 - 0.12, 0.15, x2, y2 + 0.20, 0.38, self.tt("np_slat_blk"), group="detail")
                self.mb.aabb(
                    x1, y1, 0.38, x2, y2, 2.32,
                    self.tt("np_white_pnl"),
                    faces={"w": self.ft("np_exchange"), "n": self.tt("np_white_pnl")},
                    group="detail",
                )
                self.mb.aabb(
                    x1 - 0.20, y1 - 0.12, 2.32, x2 + 0.05, y2 + 0.20, 2.86,
                    self.tt("np_umb_blue"),
                    faces={"w": self.ft("np_exch_hdr"), "n": self.tt("np_umb_blue")},
                    group="detail",
                )
                continue

            ft = self.tt(lot["tex"])
            rt = self.tt(lot.get("rear_tex", "np_placehld"))
            b_tex = self.tt("np_slat_blk") if lot.get("open_ground") else rt
            faces = {"w": ft, "n": ft, "s": ft, "e": rt, "t": rt, "b": b_tex}
            z_bot = lot["z1"] + (2.6 if lot.get("open_ground") else 0.0)
            if "poly" in lot:
                self.mb.quad_prism(lot["poly"], z_bot, lot["z2"], b_tex, top_tex=rt, side_tex=ft, group="world")
            else:
                self.mb.aabb(lot["x1"], lot["y1"], z_bot, lot["x2"], lot["y2"], lot["z2"], rt, faces=faces, group="world")

            if lot.get("open_ground"):
                # Deep open-front ground-floor pub recess (np_bar_dark + entrance steps + split counters + lush planters, ref_048/039/032!)
                y_in_s = lot["y1"] + (2.4 if "throat_bar" in lot else 0.2)
                y_in_n = lot.get("y_max_inner", lot["y2"] - 0.2)
                rec_depth = 3.2 if "Kickoff" in lot["name"] else 5.2
                x_rec = lot["x1"] + rec_depth
                x_back = -24.5 if "Kickoff" in lot["name"] else (-18.2 if "Stumble" in lot["name"] else lot["x2"])
                self.mb.aabb(x_rec, y_in_s, lot["z1"], x_back, y_in_n, z_bot, rt, faces={"w": self.tt("np_bar_dark"), "s": self.tt("np_bar_dark"), "n": self.tt("np_bar_dark")}, group="world")
                self.mb.aabb(lot["x1"] - 0.25, y_in_s + 0.4, lot["z1"], x_rec, y_in_n - 0.4, lot["z1"] + 0.18, self.tt("np_forecrt"), group="detail")
                self.mb.aabb(lot["x1"] + 0.15, y_in_s + 0.4, lot["z1"] + 0.18, x_rec, y_in_n - 0.4, lot["z1"] + 0.34, self.tt("np_forecrt"), group="detail")
                ym_lot = 0.5 * (y_in_s + y_in_n)
                if y_in_s + 0.6 < ym_lot - 1.5:
                    self.mb.aabb(lot["x1"] + 1.3, y_in_s + 0.6, lot["z1"] + 0.34, lot["x1"] + 2.0, ym_lot - 1.5, lot["z1"] + 1.24, self.tt("np_mahog_wd"), group="detail")
                if ym_lot + 1.5 < y_in_n - 0.6:
                    self.mb.aabb(lot["x1"] + 1.3, ym_lot + 1.5, lot["z1"] + 0.34, lot["x1"] + 2.0, y_in_n - 0.6, lot["z1"] + 1.24, self.tt("np_mahog_wd"), group="detail")
                if "Morning Night" in lot["name"]:
                    self.mb.aabb(lot["x1"] + 0.3, 42.2, lot["z1"] + 0.34, lot["x1"] + 1.2, 43.8, lot["z1"] + 1.22, self.tt("np_umb_blue"), group="detail")
                if "Stumble" in lot["name"]:
                    for py_pl in (16.4, 28.8):
                        self.mb.aabb(-30.05, py_pl - 0.42, 0.15, -29.20, py_pl + 0.42, 0.62, self.tt("np_brick_col"), group="detail")
                        self.mb.oct_prism(-29.62, py_pl, 0.58, 1.85, 0.52, self.tt("np_foliage"), sides=6, group="detail")
                self.mb.light(lot["x1"] + 2.6, ym_lot, 2.15, val=180, color="1.0 0.82 0.58")
                for by in range(int(lot["y1"]) + 3, int(y_in_n) - 2, 5):
                    if 8.8 + 1.0 < lot["z2"]:
                        self.mb.aabb(lot["x1"] - 0.45, by - 0.85, 8.8, lot["x1"], by + 0.85, 9.75, self.tt("np_balust"), group="detail")

            if "slat_balcony" in lot:
                sb = lot["slat_balcony"]
                self.mb.aabb(sb["x1"], sb["y1"], sb["z1"], sb["x2"], sb["y2"], sb["z2"], self.tt(sb["tex"]), group="detail")
            if "awning" in lot:
                aw = lot["awning"]
                self.mb.aabb(aw["x1"], aw["y1"], aw["z_out"], aw["x2"], aw["y2"], aw["z_in"], self.tt(aw["tex"]), group="detail")
            for fkey in ("fascia", "sub_fascia"):
                if fkey in lot:
                    fa = lot[fkey]
                    self.mb.aabb(fa["x1"], fa["y1"], fa["z1"], fa["x2"], fa["y2"], fa["z2"], self.tt("np_slat_blk"), faces={"w": self.ft(fa["tex"])}, group="detail")
            if "throat_bar" in lot:
                tb = lot["throat_bar"]
                self.mb.aabb(tb["x1"], tb["y1"], tb["z1"], tb["x2"], tb["y2"], tb["z2"], self.tt("np_slat_blk"), faces={"s": self.ft(tb["tex"])}, group="detail")
                self.mb.aabb(tb["x1"] - 0.08, tb["y1"] - 0.12, tb["z2"], tb["x2"], tb["y2"] + 0.15, tb["z2"] + 0.08, self.tt("np_mahog_wd"), group="detail")
                self.mb.aabb(tb["x1"] - 0.35, tb["y1"] - 0.45, 2.38, tb["x2"], tb["y2"] + 0.25, 2.52, self.tt("np_shutter"), group="detail")
                self.mb.aabb(tb["x1"] - 0.30, tb["y1"] - 0.44, 1.98, tb["x2"], tb["y1"] - 0.40, 2.38, self.tt("{np_bunting"), group="fence")
            if "blade" in lot:
                bl = lot["blade"]
                self.mb.aabb(bl["x1"], bl["y1"], bl["z1"], bl["x2"], bl["y2"], bl["z2"], self.ft(bl["tex"]), group="detail")

        # West side of Soi 4 lots
        for lot in self.buildings["soi4_west_lots"]:
            ft = self.tt(lot["tex"])
            rt = self.tt(lot.get("rear_tex", "np_placehld"))
            faces = {"e": ft, "n": ft, "s": ft, "w": rt, "t": rt}
            if lot.get("open_patio"):
                # Hooters Nana open-air sports-bar patio (ref_033, ref_035): recessed dark bar interior + horizontal mahogany upper fascia + orange pillars!
                self.mb.aabb(lot["x1"], lot["y1"], lot["z1"], lot["x2"] - 3.4, lot["y2"], 3.00, rt, faces={"e": self.tt("np_bar_dark"), "n": self.tt("np_bar_dark"), "s": self.tt("np_bar_dark")}, group="world")
                self.mb.aabb(lot["x2"] - 3.4, lot["y1"], 0.0, lot["x2"], lot["y2"], 0.24, self.tt("np_forecrt"), group="detail")
                self.mb.aabb(lot["x1"], lot["y1"], 3.00, lot["x2"], lot["y2"], lot["z2"], rt, faces=faces, group="world")
                for yp_h in (-16.8, -8.5, 0.2):
                    self.mb.aabb(lot["x2"] - 0.42, yp_h - 0.24, 0.24, lot["x2"], yp_h + 0.24, 3.00, self.tt("np_red_pnt"), group="detail")
                self.mb.aabb(lot["x2"] - 0.30, lot["y1"] + 0.5, 0.24, lot["x2"], lot["y2"] - 0.5, 0.94, self.tt("np_wall_crm"), group="detail")
                self.mb.aabb(lot["x2"] - 0.34, lot["y1"] + 0.45, 0.94, lot["x2"] + 0.04, lot["y2"] - 0.45, 1.04, self.tt("np_mahog_wd"), group="detail")
                for tv_y in (-11.5, -5.8):
                    self.mb.aabb(lot["x2"] - 3.38, tv_y, 1.65, lot["x2"] - 3.26, tv_y + 1.6, 2.45, self.tt("np_slat_blk"), faces={"e": self.ft("np_tv_pitch")}, group="detail")
                self.mb.light(lot["x2"] - 1.6, -5.0, 2.45, val=185, color="1.0 0.80 0.55")
                self.mb.light(lot["x2"] - 1.6, -12.0, 2.45, val=185, color="1.0 0.80 0.55")
            else:
                is_wall = (lot["x2"] - lot["x1"]) < 1.5
                self.mb.aabb(lot["x1"], lot["y1"], lot["z1"], lot["x2"], lot["y2"], lot["z2"], rt, faces=faces, group="detail" if is_wall else "world")
            if "patio_awning" in lot:
                pa = lot["patio_awning"]
                self.mb.aabb(pa["x1"], pa["y1"], pa["z1"], pa["x2"], pa["y2"], pa["z2"], self.tt(pa["tex"]), group="detail")
                if not lot.get("open_patio"):
                    self.mb.aabb(pa["x2"] - 0.22, pa["y1"] + 0.5, 0.16, pa["x2"], pa["y2"] - 0.5, 1.02, self.tt("np_mahog_wd"), group="detail")
            if "fascia" in lot:
                fa = lot["fascia"]
                self.mb.aabb(
                    fa["x1"], fa["y1"], fa["z1"], fa["x2"], fa["y2"], fa["z2"],
                    self.tt("np_slat_blk"),
                    faces={"e": self.ft(fa["tex"]), "s": self.ft(fa["tex"]) if fa["tex"] == "np_cannabis" else self.tt("np_slat_blk")},
                    group="detail",
                )
            if "blade" in lot:
                bl = lot["blade"]
                self.mb.aabb(
                    bl["x1"], bl["y1"], bl["z1"], bl["x2"], bl["y2"], bl["z2"],
                    self.tt("np_white_pnl"),
                    faces={"n": self.ft(bl["tex"]), "s": self.ft(bl["tex"]), "e": self.ft(bl["tex"])},
                    group="detail",
                )

        # Oriented Sukhumvit & neighborhood blocks (world structural for PVS culling)
        for blk in self.buildings["neighborhood_oriented_blocks"]:
            self.mb.obox(blk["cx"], blk["cy"], 0.0, blk["z2"], blk["hl"], blk["hw"], blk["yaw"], self.tt(blk["tex"]), group="world")

    # ------------------------------------------------------------------
    # STAGE 5: CARS, TRUCKS, TUK-TUKS, SCOOTERS, CARTS, UMBRELLAS & TREES
    # ------------------------------------------------------------------
    def _build_vehicle(self, v):
        if v["frame"] == "plaza":
            cx, cy = plaza_to_world(v["s"], v["w"])
            yaw = PLAZA_YAW_DEG + v["yaw_rel"]
        else:
            cx, cy = v["x"], v["y"]
            yaw = v["yaw"]
        z0 = v["z"]
        vt = v["type"]
        tname = v.get("tex", "np_pickup_sv")
        tex = self.ft(tname)
        wheel_t = self.tt("np_asphalt")

        def add_wheels(dx, dy, r=0.32):
            rad = math.radians(yaw)
            es = (math.cos(rad), math.sin(rad))
            ew = (-math.sin(rad), math.cos(rad))
            for sx in (-dx, dx):
                for sy in (-dy, dy):
                    wx = cx + sx * es[0] + sy * ew[0]
                    wy = cy + sx * es[1] + sy * ew[1]
                    self.mb.obox(wx, wy, z0, z0 + 2 * r, r, 0.14, yaw, wheel_t, group="detail")

        if vt == "vw_bus":
            # VW Type 2 Camper ('Sports Bus' inside SE courtyard: single unified body so windows NEVER double-stack!)
            add_wheels(1.35, 0.78, 0.33)
            self.mb.obox(
                cx, cy, z0 + 0.30, z0 + 1.98, 2.22, 0.86, yaw,
                self.tt("np_stool_gn"),
                faces={"left": tex, "right": tex, "t": self.tt("np_white_pnl")},
                group="detail",
            )
        elif vt in ("taxi", "sedan_white"):
            add_wheels(1.35, 0.80, 0.31)
            body_solid = self.tt("np_white_pnl") if vt == "sedan_white" else (self.tt("np_stool_gn") if tname == "np_taxi_grn" else self.tt("np_stool_pk" if tname == "np_taxi_pnk" else tname))
            side_f = self.tt("np_white_pnl") if vt == "sedan_white" else tex
            fb_f = tex if tname in ("np_taxi_gy", "np_taxi_grn") else body_solid
            self.mb.obox(cx, cy, z0 + 0.24, z0 + 0.92, 2.26, 0.88, yaw, body_solid, faces={"left": side_f, "right": side_f, "front": fb_f, "back": body_solid}, group="detail")
            self.mb.obox(cx - 0.15 * math.cos(math.radians(yaw)), cy - 0.15 * math.sin(math.radians(yaw)), z0 + 0.92, z0 + 1.46, 1.25, 0.76, yaw, self.tt("np_glass_rl"), faces={"t": body_solid}, group="detail")
            if vt == "taxi":
                self.mb.obox(cx, cy, z0 + 1.46, z0 + 1.62, 0.28, 0.48, yaw, self.tt("np_awn_ylw"), group="detail")
        elif vt in ("pickup", "pickup_canopy"):
            add_wheels(1.55, 0.84, 0.35)
            sv_paint = self.tt("np_silv_pnt")
            self.mb.obox(cx, cy, z0 + 0.30, z0 + 1.06, 2.55, 0.90, yaw, sv_paint, faces={"left": tex, "right": tex, "front": sv_paint, "back": sv_paint, "t": sv_paint}, group="detail")
            rad = math.radians(yaw)
            cab_x, cab_y = cx + 0.55 * math.cos(rad), cy + 0.55 * math.sin(rad)
            bed_x, bed_y = cx - 1.25 * math.cos(rad), cy - 1.25 * math.sin(rad)
            self.mb.obox(cab_x, cab_y, z0 + 1.06, z0 + 1.74, 0.95, 0.82, yaw, self.tt("np_glass_rl"), faces={"t": sv_paint}, group="detail")
            if vt == "pickup_canopy":
                self.mb.obox(bed_x, bed_y, z0 + 1.06, z0 + 1.90, 1.25, 0.88, yaw, self.tt("np_white_pnl"), group="detail")
        elif vt == "tuktuk":
            # Authentic 3-wheeled open-sided Thai tuk-tuk (ref_020, ref_046): blue front cowl, windshield, open passenger bay, yellow roof!
            rad = math.radians(yaw)
            es = (math.cos(rad), math.sin(rad))
            ew = (-math.sin(rad), math.cos(rad))
            self.mb.obox(cx + 1.02 * es[0], cy + 1.02 * es[1], z0, z0 + 0.50, 0.25, 0.13, yaw, wheel_t, group="detail")
            for sgn in (-1.0, 1.0):
                self.mb.obox(cx - 0.85 * es[0] + sgn * 0.60 * ew[0], cy - 0.85 * es[1] + sgn * 0.60 * ew[1], z0, z0 + 0.52, 0.26, 0.14, yaw, wheel_t, group="detail")
            # Blue front cowl & mudguard
            self.mb.obox(cx + 0.78 * es[0], cy + 0.78 * es[1], z0 + 0.20, z0 + 0.90, 0.40, 0.58, yaw, self.tt("np_umb_blue"), faces={"front": tex}, group="detail")
            # Front windshield + chrome A-pillars
            self.mb.obox(cx + 0.42 * es[0], cy + 0.42 * es[1], z0 + 0.90, z0 + 1.58, 0.06, 0.56, yaw, self.tt("np_glass_rl"), group="detail")
            for sgn in (-1.0, 1.0):
                self.mb.obox(cx + 0.42 * es[0] + sgn * 0.56 * ew[0], cy + 0.42 * es[1] + sgn * 0.56 * ew[1], z0 + 0.90, z0 + 1.58, 0.04, 0.04, yaw, self.tt("np_chrome"), group="detail")
            # Low passenger floorpan + rear seat + rear tail panel + rear chrome struts + yellow roof
            self.mb.obox(cx - 0.38 * es[0], cy - 0.38 * es[1], z0 + 0.20, z0 + 0.34, 0.78, 0.64, yaw, self.tt("np_slat_blk"), group="detail")
            self.mb.obox(cx - 0.72 * es[0], cy - 0.72 * es[1], z0 + 0.34, z0 + 0.78, 0.30, 0.58, yaw, self.tt("np_stool_pk"), group="detail")
            self.mb.obox(cx - 1.10 * es[0], cy - 1.10 * es[1], z0 + 0.22, z0 + 0.92, 0.08, 0.64, yaw, self.tt("np_umb_blue"), faces={"back": tex}, group="detail")
            for sgn in (-1.0, 1.0):
                self.mb.obox(cx - 1.08 * es[0] + sgn * 0.58 * ew[0], cy - 1.08 * es[1] + sgn * 0.58 * ew[1], z0 + 0.92, z0 + 1.58, 0.04, 0.04, yaw, self.tt("np_chrome"), group="detail")
            self.mb.obox(cx - 0.34 * es[0], cy - 0.34 * es[1], z0 + 1.58, z0 + 1.72, 0.84, 0.66, yaw, self.tt("np_awn_ylw"), group="detail")

    def build_stage5_props(self):
        for v in self.props["vehicles"]:
            if v["type"] == "scooter_row":
                cnt = v["count"]
                s_rad = math.radians(v["yaw"])
                es = (math.cos(s_rad), math.sin(s_rad))
                cowl_palette = ("np_white_pnl", "np_red_pnt", "np_silv_pnt")
                for i in range(cnt):
                    sy = v["y1"] + (v["y2"] - v["y1"]) * (i / max(1, cnt - 1))
                    cowl_t = self.tt(cowl_palette[i % 3])
                    for wx_s in (-0.48, 0.48):
                        self.mb.obox(v["x"] + wx_s * es[0], sy + wx_s * es[1], 0.0, 0.44, 0.22, 0.09, v["yaw"], self.tt("np_asphalt"), group="detail")
                    self.mb.obox(v["x"] - 0.14 * es[0], sy - 0.14 * es[1], 0.34, 0.76, 0.32, 0.20, v["yaw"], self.tt("np_slat_blk"), group="detail")
                    self.mb.obox(v["x"] + 0.33 * es[0], sy + 0.33 * es[1], 0.32, 0.96, 0.15, 0.22, v["yaw"], cowl_t, group="detail")
                    self.mb.obox(v["x"] + 0.30 * es[0], sy + 0.30 * es[1], 0.96, 1.12, 0.08, 0.34, v["yaw"], self.tt("np_chrome"), group="detail")
            else:
                self._build_vehicle(v)

        for u in self.props["umbrellas_and_carts"]:
            ux, uy, uz = u["x"], u["y"], u["z"]
            self.mb.aabb(ux - 0.04, uy - 0.04, uz, ux + 0.04, uy + 0.04, uz + 2.28, self.tt("np_chrome"), group="detail")
            self.mb.oct_prism(ux, uy, uz + 2.08, uz + 2.38, 1.32, self.tt(u["tex"]), sides=8, group="detail")
            if u.get("cart"):
                self.mb.aabb(ux - 0.48, uy - 0.80, uz, ux + 0.48, uy + 0.80, uz + 0.90, self.tt("np_shutter"), group="detail")
            if u.get("blue_metal_cart"):
                self.mb.aabb(ux - 0.52, uy - 1.55, uz, ux + 0.52, uy + 1.55, uz + 1.02, self.tt("np_umb_blue"), group="detail")
                self.mb.aabb(ux - 0.56, uy - 1.60, uz + 1.82, ux + 0.56, uy + 1.60, uz + 1.92, self.tt("np_white_pnl"), group="detail")
            if u.get("green_bin"):
                # Municipal green wheelie bin using clean np_stool_gn plastic crop (ZERO taxi photo!)
                self.mb.aabb(ux - 0.30, uy - 1.30, uz, ux + 0.30, uy - 0.72, uz + 1.02, self.tt("np_stool_gn"), group="detail")

        cb = self.props["cones_and_barriers"]["arch_cone_barrier"]

        def make_cone(cx_c, cy_c, z_base):
            self.mb.aabb(cx_c - 0.18, cy_c - 0.18, z_base, cx_c + 0.18, cy_c + 0.18, z_base + 0.05, self.tt("np_slat_blk"), group="detail")
            self.mb.oct_prism(cx_c, cy_c, z_base + 0.05, z_base + 0.34, 0.14, self.tt("np_kerb_rw"), sides=6, group="detail")
            self.mb.oct_prism(cx_c, cy_c, z_base + 0.34, z_base + 0.52, 0.10, self.tt("np_white_pnl"), sides=6, group="detail")
            self.mb.oct_prism(cx_c, cy_c, z_base + 0.52, z_base + 0.72, 0.06, self.tt("np_kerb_rw"), sides=6, group="detail")

        for cy_pos in cb["y_list"]:
            make_cone(cb["x"], cy_pos, 0.08)
        for sy_p in cb["pole_bar_y"]:
            self.mb.oct_prism(cb["x"], sy_p, 0.08, 0.92, 0.04, self.tt("np_chrome"), sides=6, group="detail")
        self.mb.aabb(cb["x"] - 0.03, cb["pole_bar_y"][0], 0.80, cb["x"] + 0.03, cb["pole_bar_y"][1], 0.86, self.tt("np_red_pnt"), group="detail")
        for cx_p, cy_p in self.props["cones_and_barriers"]["extra_cones"]:
            make_cone(cx_p, cy_p, 0.15)

        for tr in self.props["trees"]:
            tx, ty, th = tr["x"], tr["y"], tr["h"]
            self.mb.oct_prism(tx, ty, 0.0, th * 0.48, 0.26, self.tt("np_brick_col"), sides=6, group="detail")
            self.mb.oct_prism(tx, ty, th * 0.42, th, 2.3, self.tt("np_foliage"), sides=8, group="detail")

    # ------------------------------------------------------------------
    # STAGE 7: LIGHTING, NEON ACCENTS & PLAYER SPAWNS
    # ------------------------------------------------------------------
    def build_stage7_lighting_and_spawns(self):
        if os.environ.get("NANA_START"):
            vals = [float(v) for v in os.environ["NANA_START"].split()]
            if len(vals) >= 5:
                self.mb.ent("info_player_start", vals[0], vals[1], vals[2], angles=f"{vals[4]:.1f} {vals[3]:.1f} 0")
            else:
                self.mb.ent("info_player_start", vals[0], vals[1], vals[2], angle=int(round(vals[3])) % 360)
        else:
            self.mb.ent("info_player_start", -34.0, 10.6, 0.85, angle=0)

        dm_spawns = [
            ("world", -34.2, 22.0, 0.85, 270),
            ("world", -34.2, 41.0, 0.85, 270),
            ("plaza", 17.5, 0.0, 0.95, 0),
            ("plaza", 35.0, 5.4, 0.95, 180),
            ("plaza", 37.3, -13.5, 0.95, 0),
            ("plaza", 26.0, 9.6, 4.95, 0),
            ("plaza", 28.0, -9.6, 4.95, 0),
            ("plaza", 28.0, 9.6, 8.75, 180),
        ]
        for frm, a, b, z, ang in dm_spawns:
            if frm == "plaza":
                self.mb.pent("info_player_deathmatch", a, b, z, angle=int(round(PLAZA_YAW_DEG + ang)) % 360)
            else:
                self.mb.ent("info_player_deathmatch", a, b, z, angle=ang)

        # Vibrant neon & warm bar accent lights across Arch, Courtyard, 1F/2F/3F Galleries & Stairwells
        self.mb.light(-28.4, 10.6, 4.2, val=240, color="1.0 0.78 0.62")
        self.mb.light(-30.2, 5.6, 2.75, val=185, color="0.55 0.78 1.0")
        self.mb.light(-30.2, 16.5, 3.4, val=195, color="0.40 0.70 1.0")
        self.mb.light(-30.5, 3.0, 6.8, val=210, color="1.0 0.72 0.35")

        for s_m in (16.5, 23.0, 29.5, 35.0, 39.8):
            w_walk_n = 10.5 if (s_m < 25.5 or s_m > 38.2) else 9.8
            w_walk_s = -10.5 if s_m < 26.5 else -9.6
            self.mb.plight(s_m, 0.0, 3.8, val=215, color="1.0 0.88 0.70")
            self.mb.plight(s_m, w_walk_n, 2.9, val=205, color="1.0 0.55 0.68")
            self.mb.plight(s_m, w_walk_s, 2.9, val=205, color="1.0 0.52 0.60")
            self.mb.plight(s_m, w_walk_n, 6.7, val=215, color="0.88 0.55 0.95")
            self.mb.plight(s_m, w_walk_s, 6.7, val=190, color="1.0 0.72 0.58")
            self.mb.plight(s_m, w_walk_n, 10.3, val=215, color="0.72 0.65 1.0")
            self.mb.plight(s_m, w_walk_s, 10.3, val=195, color="1.0 0.62 0.78")

        # Warm magenta/pink neon bar accents on West/South 1F/2F (ref_018 cam_14) + NW 3F Erotica + 3F East Geisha + NE/SE stairwell lights
        self.mb.plight(12.2, -5.5, 3.2, val=195, color="1.0 0.36 0.72")
        self.mb.plight(17.5, -9.5, 3.2, val=195, color="1.0 0.36 0.72")
        self.mb.plight(16.8, 9.8, 10.2, val=220, color="0.58 0.58 1.0")
        self.mb.plight(42.4, 4.4, 10.2, val=195, color="1.0 0.90 0.92")
        for z_l in (2.8, 6.6, 10.4):
            self.mb.plight(41.4, 13.4, z_l, val=185, color="1.0 0.95 0.84")
            self.mb.plight(44.2, -13.6, z_l, val=185, color="1.0 0.95 0.84")

    def build_all(self):
        self.build_world_hull()
        self.build_stage1_roads()
        self.build_stage2_bridges()
        self.build_stage3_landmarks()
        self.build_stage4a_nana_plaza()
        self.build_stage4b_buildings()
        self.build_stage5_props()
        self.build_stage7_lighting_and_spawns()

        worldspawn_kv = {
            "message": "Nana Plaza - Sukhumvit Soi 4, Bangkok (1:1 Replica)",
            "skyname": "nanaplaza_",
            "_sunlight": "235",
            "_sunlight_color": "1 0.97 0.90",
            "_sunlight_mangle": "139 -47 0",
            "_sunlight_penumbra": "3",
            "_sunlight2": "165",
            "_sunlight2_color": "0.78 0.87 1.0",
            "_minlight": "54",
            "_minlight_color": "0.86 0.88 0.92",
            "_dirt": "1",
            "_dirtscale": "0.45",
        }
        self.mb.write_map(OUT_MAP, worldspawn_kv)
        n_brushes = sum(len(v) for v in self.mb.groups.values())
        print(f"Wrote {OUT_MAP}: {n_brushes} brushes ({len(self.mb.groups['world'])} structural world, {n_brushes - len(self.mb.groups['world'])} detail), {len(self.mb.ents)} point entities.")


if __name__ == "__main__":
    NanaPlazaGenerator().build_all()
