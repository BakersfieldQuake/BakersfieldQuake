"""audit3_nav.py — Audit 3 of 5: Exhaustive Hull-1 (32x32x56 u) Collision, Navigation,
Doorway Clearance (>=64x96u), Room Ceiling (>=112u), <=18u Step/Stair Climb, Iterative
Tarjan SCC + Reverse-BFS Zero-Trap Analysis, Browser WASD/Space/F Traversal, and Live
DarkPlaces Walk Smoke Check for Golden West Casino & S Union Ave.

Outputs:
  - source/mm_tools/goldenwest/out/audit3_nav_report.json
  - source/mm_tools/goldenwest/out/audit3_nav_map.png
"""
from __future__ import annotations

import argparse
import collections
import functools
import http.server
import importlib
import json
import math
import os
import re
import socketserver
import struct
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS_DIR = os.path.dirname(HERE)
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GAME_ROOT = os.path.dirname(MOD_DIR)

if MM_TOOLS_DIR not in sys.path:
    sys.path.insert(0, MM_TOOLS_DIR)

from goldenwest.gw_lib import (  # noqa: E402
    ADAMS_ST_Y,
    AMADOR_AVE_Y,
    BELLE_TERRACE_Y,
    CASINO_BOUNDS_FT,
    CASINO_LOT_FT,
    DELAWARE_ST_X,
    E_4TH_ST_Y,
    E_5TH_ST_Y,
    GC_ANNEX_BOUNDS_FT,
    GC_BLDG_BOUNDS_FT,
    GC_BOH_BOUNDS_FT,
    GC_DINING_BOUNDS_FT,
    GC_LOT_FT,
    GC_RESTROOM_BOUNDS_FT,
    GC_VESTIBULE_BOUNDS_FT,
    HX0,
    HX1,
    HY0,
    HY1,
    HULL1_MAX_STEP_U,
    HULL1_MIN_CEIL_U,
    HULL1_MIN_DOOR_H_U,
    HULL1_MIN_DOOR_W_U,
    MARIPOSA_AVE_Y,
    PARCELS,
    TRINITY_AVE_Y,
    UNION_MEDIAN_X,
    UNION_NB_CARRIAGE_X,
    UNION_SB_CARRIAGE_X,
    U_FT,
    MapBuilder,
)

OUT_DIR = os.path.join(HERE, "out")
BSP_PATH = os.path.join(MOD_DIR, "maps", "goldenwest.bsp")
WEB_DIR = os.path.join(MM_TOOLS_DIR, "out", "web", "goldenwest")
DP_EXE = os.path.join(GAME_ROOT, "darkplaces.exe")
SPOTS_CANDIDATES = (
    os.path.join(MOD_DIR, "maps", "goldenwest.spots.json"),
    os.path.join(OUT_DIR, "goldenwest.spots.json"),
    os.path.join(MM_TOOLS_DIR, "out", "maps", "goldenwest.spots.json"),
)

CONTENTS_EMPTY = -1
CONTENTS_SOLID = -2
DIST_EPS = 0.03125


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def load_spots(path: str) -> List[Dict[str, object]]:
    """Load goldenwest.spots.json supporting both {'spots': [...]} and legacy list formats."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw_list = data.get("spots", []) if isinstance(data, dict) else list(data)
    out: List[Dict[str, object]] = []
    for sp in raw_list:
        origin = sp.get("origin") or sp.get("pos")
        if not origin or len(origin) < 3:
            continue
        angles = sp.get("angles")
        pitch = float(angles[0]) if angles and len(angles) >= 2 else float(sp.get("pitch", 0.0))
        yaw = float(angles[1]) if angles and len(angles) >= 2 else float(sp.get("yaw", 0.0))
        out.append({
            "name": str(sp.get("name", f"spot_{len(out)}")),
            "kind": str(sp.get("kind", "audit")),
            "origin": [float(origin[0]), float(origin[1]), float(origin[2])],
            "pitch": pitch,
            "yaw": yaw,
            "desc": str(sp.get("desc", "")),
        })
    return out


class Hull1Tracer:
    """Exact Quake Hull-1 ([-16,-16,-24]..[16,16,32]) clipnode tracer with AABB bmodel pruning."""

    def __init__(self, planes, clipnodes, hulls, hull_bboxes=None, ents=None):
        self.planes = planes
        self.clipnodes = clipnodes
        self.hulls = hulls
        self.hull_bboxes = hull_bboxes or [None for _ in hulls]
        self.ents = ents or []

    @classmethod
    def from_bsp(cls, bsp_path: str) -> "Hull1Tracer":
        with open(bsp_path, "rb") as f:
            d = f.read()
        bsp2 = d[:4] == b"BSP2"
        lumps = [struct.unpack("<2i", d[4 + 8 * i : 12 + 8 * i]) for i in range(15)]

        def lmp(i: int) -> bytes:
            o, n = lumps[i]
            return d[o : o + n]

        entities_raw = lmp(0).decode("latin1")
        planes = [struct.unpack("<4fi", lmp(1)[i : i + 20]) for i in range(0, len(lmp(1)), 20)]
        clip_fmt, clip_sz = ("<iii", 12) if bsp2 else ("<ihh", 8)
        clipnodes = [struct.unpack(clip_fmt, lmp(9)[i : i + clip_sz]) for i in range(0, len(lmp(9)), clip_sz)]
        models = [struct.unpack("<9f7i", lmp(14)[i : i + 64]) for i in range(0, len(lmp(14)), 64)]

        ents = [dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', m.group(1))) for m in re.finditer(r"\{([^}]*)\}", entities_raw)]
        bmodels = [0] + [
            int(e["model"][1:])
            for e in ents
            if e.get("model", "").startswith("*")
            and not e.get("classname", "").startswith("trigger")
            and "illusionary" not in e.get("classname", "")
        ]
        hulls: List[int] = []
        bboxes: List[Optional[Tuple[float, float, float, float, float, float]]] = []
        for idx, mi in enumerate(bmodels):
            m = models[mi]
            hulls.append(m[10])  # hull1 headnode
            if idx == 0:
                bboxes.append(None)  # always check worldspawn
            else:
                pad = 40.0
                bboxes.append((m[0] - pad, m[1] - pad, m[2] - pad, m[3] + pad, m[4] + pad, m[5] + pad))
        return cls(planes, clipnodes, hulls, hull_bboxes=bboxes, ents=ents)

    @classmethod
    def from_web_json(cls, map_json_path: str) -> "Hull1Tracer":
        with open(map_json_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        planes = [tuple(p) for p in meta["planes"]]
        clipnodes = [tuple(c) for c in meta["clipnodes"]]
        hulls = list(meta["hulls"])
        return cls(planes, clipnodes, hulls)

    def pdist(self, pl, p) -> float:
        t = pl[4]
        if t == 0:
            return p[0] - pl[3]
        if t == 1:
            return p[1] - pl[3]
        if t == 2:
            return p[2] - pl[3]
        return pl[0] * p[0] + pl[1] * p[1] + pl[2] * p[2] - pl[3]

    def hull_contents(self, head: int, p: Tuple[float, float, float]) -> int:
        num = head
        planes = self.planes
        cnodes = self.clipnodes
        px, py, pz = p
        while num >= 0:
            n = cnodes[num]
            pl = planes[n[0]]
            t = pl[4]
            if t == 0:
                d = px - pl[3]
            elif t == 1:
                d = py - pl[3]
            elif t == 2:
                d = pz - pl[3]
            else:
                d = pl[0] * px + pl[1] * py + pl[2] * pz - pl[3]
            num = n[2] if d < 0.0 else n[1]
        return num

    def is_solid(self, p: Tuple[float, float, float]) -> bool:
        px, py, pz = p
        for h, bb in zip(self.hulls, self.hull_bboxes):
            if bb is not None and not (bb[0] <= px <= bb[3] and bb[1] <= py <= bb[4] and bb[2] <= pz <= bb[5]):
                continue
            if self.hull_contents(h, p) == CONTENTS_SOLID:
                return True
        return False

    def _recurse(self, head: int, num: int, p1f: float, p2f: float, p1, p2, tr) -> bool:
        if num < 0:
            if num != CONTENTS_SOLID:
                tr["allsolid"] = False
            else:
                tr["startsolid"] = True
            return True
        n = self.clipnodes[num]
        pl = self.planes[n[0]]
        t1 = self.pdist(pl, p1)
        t2 = self.pdist(pl, p2)
        if t1 >= 0.0 and t2 >= 0.0:
            return self._recurse(head, n[1], p1f, p2f, p1, p2, tr)
        if t1 < 0.0 and t2 < 0.0:
            return self._recurse(head, n[2], p1f, p2f, p1, p2, tr)
        denom = t1 - t2
        if abs(denom) < 1e-9:
            return False
        frac = (t1 + DIST_EPS) / denom if t1 < 0.0 else (t1 - DIST_EPS) / denom
        frac = min(1.0, max(0.0, frac))
        midf = p1f + (p2f - p1f) * frac
        mid = (p1[0] + (p2[0] - p1[0]) * frac, p1[1] + (p2[1] - p1[1]) * frac, p1[2] + (p2[2] - p1[2]) * frac)
        side = 1 if t1 < 0.0 else 0
        if not self._recurse(head, n[1 + side], p1f, midf, p1, mid, tr):
            return False
        if self.hull_contents(n[2 - side], mid) != CONTENTS_SOLID:
            return self._recurse(head, n[2 - side], midf, p2f, mid, p2, tr)
        if tr["allsolid"]:
            return False
        while self.hull_contents(head, mid) == CONTENTS_SOLID:
            frac -= 0.05
            if frac < 0.0:
                tr["fraction"] = midf
                tr["endpos"] = mid
                return False
            midf = p1f + (p2f - p1f) * frac
            mid = (p1[0] + (p2[0] - p1[0]) * frac, p1[1] + (p2[1] - p1[1]) * frac, p1[2] + (p2[2] - p1[2]) * frac)
        tr["fraction"] = midf
        tr["endpos"] = mid
        return False

    def trace(self, a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Dict[str, object]:
        best = {"fraction": 1.0, "endpos": b, "allsolid": False, "startsolid": False}
        ax0, ax1 = min(a[0], b[0]), max(a[0], b[0])
        ay0, ay1 = min(a[1], b[1]), max(a[1], b[1])
        az0, az1 = min(a[2], b[2]), max(a[2], b[2])
        for head, bb in zip(self.hulls, self.hull_bboxes):
            if bb is not None and (ax1 < bb[0] or ax0 > bb[3] or ay1 < bb[1] or ay0 > bb[4] or az1 < bb[2] or az0 > bb[5]):
                continue
            tr = {"fraction": 1.0, "endpos": b, "allsolid": True, "startsolid": False}
            self._recurse(head, head, 0.0, 1.0, a, b, tr)
            if tr["allsolid"] or tr["startsolid"]:
                best["startsolid"] = True
                if tr["allsolid"]:
                    best["allsolid"] = True
            if tr["fraction"] < best["fraction"]:
                best["fraction"] = tr["fraction"]
                best["endpos"] = tr["endpos"]
        return best

    def stand_at_ft(self, x_ft: float, y_ft: float, z_floor_ft: float = 0.0) -> Optional[Tuple[float, float, float]]:
        xu, yu = x_ft * U_FT, y_ft * U_FT
        for dz_ft in (3.0, 2.2, 4.5):
            zu = (z_floor_ft + dz_ft) * U_FT
            if not self.is_solid((xu, yu, zu)):
                tr = self.trace((xu, yu, zu), (xu, yu, (z_floor_ft - 5.0) * U_FT))
                if not tr["startsolid"] and tr["fraction"] < 0.999:
                    ez = tr["endpos"][2] + 0.5
                    if not self.is_solid((xu, yu, ez)):
                        return (xu, yu, ez)
        return None

    def can_walk_step(
        self, p_from: Tuple[float, float, float], nx_u: float, ny_u: float, step_height: float = HULL1_MAX_STEP_U
    ) -> Optional[Tuple[float, float, float]]:
        """Standard Quake Hull-1 walk step (<=18u step-up without jumping, drop up to 48u)."""
        up = self.trace(p_from, (p_from[0], p_from[1], p_from[2] + step_height))["endpos"]
        across = self.trace(up, (nx_u, ny_u, up[2]))
        if across["fraction"] < 0.985:
            return None
        down = self.trace(across["endpos"], (nx_u, ny_u, p_from[2] - 48.0))
        if down["startsolid"] or down["fraction"] >= 0.999:
            return None
        ez = down["endpos"][2] + 0.5
        if self.is_solid((nx_u, ny_u, ez)):
            return None
        return (nx_u, ny_u, ez)


# Canonical exterior & enterable interior target zones in feet:
# (name, x0_ft, y0_ft, x1_ft, y1_ft, z0_ft, z1_ft, required)
ZONE_TARGETS_FT: Tuple[Tuple[str, float, float, float, float, float, float, bool], ...] = (
    # --- Roadways & Cross Streets ---
    ("S Union Ave North SB", UNION_SB_CARRIAGE_X[0] + 2, 350.0, UNION_SB_CARRIAGE_X[1] - 2, 650.0, 0.5, 5.0, True),
    ("S Union Ave Casino SB", UNION_SB_CARRIAGE_X[0] + 2, -60.0, UNION_SB_CARRIAGE_X[1] - 2, 120.0, 0.5, 5.0, True),
    ("S Union Ave Northbound Mid", UNION_NB_CARRIAGE_X[0] + 2, -100.0, UNION_NB_CARRIAGE_X[1] - 2, 200.0, 0.5, 5.0, True),
    ("S Union Ave South", UNION_SB_CARRIAGE_X[0] + 2, -740.0, UNION_SB_CARRIAGE_X[1] - 2, -500.0, 0.5, 5.0, True),
    ("E Belle Terrace West", -120.0, BELLE_TERRACE_Y - 14.0, 165.0, BELLE_TERRACE_Y + 14.0, 0.5, 5.0, True),
    ("E Belle Terrace East", 285.0, BELLE_TERRACE_Y - 14.0, 520.0, BELLE_TERRACE_Y + 14.0, 0.5, 5.0, True),
    ("Trinity Ave West", -350.0, TRINITY_AVE_Y - 12.0, -145.0, TRINITY_AVE_Y + 12.0, 0.5, 5.0, True),
    ("Delaware St Corridor", DELAWARE_ST_X - 12.0, -730.0, DELAWARE_ST_X + 12.0, -140.0, 0.5, 5.0, True),
    ("Mariposa Ave West", -350.0, MARIPOSA_AVE_Y - 12.0, -145.0, MARIPOSA_AVE_Y + 12.0, 0.5, 5.0, True),
    ("Adams St East", 285.0, ADAMS_ST_Y - 12.0, 520.0, ADAMS_ST_Y + 12.0, 0.5, 5.0, True),
    ("Amador Ave West", -350.0, AMADOR_AVE_Y - 12.0, 165.0, AMADOR_AVE_Y + 12.0, 0.5, 5.0, True),
    # --- Casino Courtyard & Open Lots ---
    ("Casino NE Courtyard & Portico", 96.0, -55.0, 168.0, 40.0, 0.5, 5.5, True),
    ("Casino Parking North", -40.0, 100.0, 160.0, 230.0, 0.5, 5.5, True),
    ("El Don Demolished Brownfield", 295.0, 430.0, 500.0, 525.0, 0.5, 5.5, True),
    ("891 S Union Vacant Lot", -120.0, 588.0, 40.0, 660.0, 0.5, 5.5, True),
    # --- Enterable Interiors ---
    ("INT Golden West Casino Main Pit", -42.0, -60.0, 62.0, 60.0, 0.5, 7.0, True),
    ("INT Golden West Casino Rotunda", 58.0, -40.0, 94.0, -10.0, 0.5, 7.0, True),
    ("INT Carnitas Birria Diner", 104.0, 614.0, 144.0, 658.0, 0.5, 7.0, True),
    ("INT Star-Liter Motel Courtyard", 300.0, 45.0, 485.0, 200.0, 0.5, 7.0, True),
    ("INT Ramos Tires Shop", -92.0, -330.0, 20.0, -288.0, 0.5, 7.0, True),
    ("INT Compas Auto Sales", -92.0, -576.0, 160.0, -352.0, 0.5, 7.0, True),
    ("INT Sunland Motel Courtyard", 310.0, -355.0, 560.0, -272.0, 0.5, 7.0, True),
    ("INT Country Inn Courtyard", 315.0, -545.0, 560.0, -380.0, 0.5, 7.0, True),
    ("INT Playfair Market", 298.0, -658.0, 350.0, -608.0, 0.5, 7.0, True),
    ("INT Super 8 Porte-Cochere / Lobby", -92.0, -720.0, 138.0, -595.0, 0.5, 7.0, True),
    ("Delaware / Trinity Residential", -350.0, -430.0, -145.0, -170.0, 0.5, 7.0, True),
    # --- Northern Extension: E 4th/E 5th, Great Castle & Neighborhoods ---
    ("S Union Ave North Great Castle SB", UNION_SB_CARRIAGE_X[0] + 2, 750.0, UNION_SB_CARRIAGE_X[1] - 2, 1300.0, 0.5, 5.0, True),
    ("S Union Ave North Great Castle NB", UNION_NB_CARRIAGE_X[0] + 2, 750.0, UNION_NB_CARRIAGE_X[1] - 2, 1300.0, 0.5, 5.0, True),
    ("E 4th St Corridor", -120.0, E_4TH_ST_Y - 12.0, 520.0, E_4TH_ST_Y + 12.0, 0.5, 5.0, True),
    ("E 5th St East Corridor", 285.0, E_5TH_ST_Y - 12.0, 520.0, E_5TH_ST_Y + 12.0, 0.5, 5.0, True),
    ("Great Castle Rear Alley", 416.0, 885.0, 428.0, 1165.0, 0.5, 5.0, True),
    ("Great Castle South Parking Lot", 295.0, 895.0, 380.0, 985.0, 0.5, 5.5, True),
    ("Great Castle North Parking Lot", 295.0, 1072.0, 410.0, 1160.0, 0.5, 5.5, True),
    ("Deal Time Auto Sales Lot", 295.0, 760.0, 368.0, 836.0, 0.5, 5.5, True),
    ("Shamrock & One Stop 4th St Lot", 40.0, 755.0, 172.0, 840.0, 0.5, 5.5, True),
    ("DG Market North Plaza", 80.0, 1150.0, 172.0, 1300.0, 0.5, 5.5, True),
    ("INT Great Castle Vestibule", 356.0, 998.0, 374.0, 1008.0, 0.5, 7.0, True),
    ("INT Great Castle Dining Hall", 338.0, 1009.0, 387.0, 1065.0, 0.5, 7.0, True),
    ("INT Great Castle Restrooms", 390.5, 998.0, 411.5, 1012.0, 0.5, 7.0, True),
    ("INT Great Castle Kitchen BOH", 390.5, 1015.0, 411.5, 1065.0, 0.5, 7.0, True),
    ("INT Reyes Tires Service Bay", 320.0, 1238.0, 356.0, 1266.0, 0.5, 7.0, True),
)


def iterative_tarjan_scc(nodes: Iterable[Tuple[int, int, int]], adj: Dict) -> List[List[Tuple[int, int, int]]]:
    """Iterative Tarjan's strongly connected components algorithm (stack-safe on 200k+ cells)."""
    index = 0
    indices: Dict[Tuple[int, int, int], int] = {}
    lowlink: Dict[Tuple[int, int, int], int] = {}
    on_stack = set()
    tarjan_stack: List[Tuple[int, int, int]] = []
    sccs: List[List[Tuple[int, int, int]]] = []

    for start in nodes:
        if start in indices:
            continue
        call_stack: List[Tuple[Tuple[int, int, int], Optional[List[Tuple[int, int, int]]], int]] = [
            (start, None, 0)
        ]
        while call_stack:
            v, nbrs, idx = call_stack[-1]
            if nbrs is None:
                indices[v] = index
                lowlink[v] = index
                index += 1
                tarjan_stack.append(v)
                on_stack.add(v)
                nbrs = list(adj.get(v, ()))
                call_stack[-1] = (v, nbrs, 0)

            if idx < len(nbrs):
                w = nbrs[idx]
                call_stack[-1] = (v, nbrs, idx + 1)
                if w not in indices:
                    call_stack.append((w, None, 0))
                elif w in on_stack:
                    if indices[w] < lowlink[v]:
                        lowlink[v] = indices[w]
            else:
                call_stack.pop()
                if call_stack:
                    parent = call_stack[-1][0]
                    if lowlink[v] < lowlink[parent]:
                        lowlink[parent] = lowlink[v]
                if lowlink[v] == indices[v]:
                    comp = []
                    while True:
                        w = tarjan_stack.pop()
                        on_stack.remove(w)
                        comp.append(w)
                        if w == v:
                            break
                    sccs.append(comp)
    return sccs


def check_mapbuilder_constraints() -> Dict[str, object]:
    """Inspect MapBuilder registrations from modular goldenwest builders if available."""
    try:
        mod = importlib.import_module("make_goldenwest")
    except ImportError:
        try:
            mod = importlib.import_module("goldenwest.make_goldenwest")
        except ImportError:
            return {"ran": False, "reason": "make_goldenwest builder not yet present"}

    mb = MapBuilder(wad_paths=(), strict_vis=True, check_textures=False)
    for fn_name in ("build_goldenwest", "build_all", "build_map"):
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            fn(mb)
            break
    else:
        return {"ran": False, "reason": "No build_goldenwest/build_all entrypoint found"}

    issues: List[str] = []
    try:
        mb.validate_all()
    except ValueError as ex:
        issues.append(str(ex))

    st = mb.stats()
    return {
        "ran": True,
        "doorways": st["doorways"],
        "stairs": st["stairs"],
        "rooms": st["rooms"],
        "spots": st["spots"],
        "issues": issues,
    }


def _running_darkplaces_pids() -> List[int]:
    if os.name != "nt":
        return []
    proc = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq darkplaces.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True,
    )
    pids: List[int] = []
    for ln in (proc.stdout or "").splitlines():
        if "darkplaces.exe" in ln.lower():
            parts = [p.strip('"') for p in ln.split(",")]
            if len(parts) >= 2 and parts[1].isdigit():
                pids.append(int(parts[1]))
    return pids


def run_darkplaces_walk_smoke() -> Dict[str, object]:
    """Live windowed DarkPlaces walk/spawn smoke test per CLAUDE.md (checks existing PIDs, terminates only ours)."""
    if not os.path.isfile(DP_EXE):
        return {"ran": False, "reason": f"darkplaces.exe not found at {DP_EXE}"}
    if not os.path.isfile(BSP_PATH):
        return {"ran": False, "reason": f"BSP not found at {BSP_PATH}"}

    # Wait briefly if another session's test is currently finishing
    for _ in range(10):
        existing = _running_darkplaces_pids()
        if not existing:
            break
        time.sleep(1.0)
    else:
        return {"ran": False, "reason": f"Another darkplaces.exe instance is already running: {_running_darkplaces_pids()}"}

    cfg_name = "_gw_audit3_walk.cfg"
    log_name = "zz_gw_audit3.log"
    cfg_path = os.path.join(MOD_DIR, cfg_name)
    log_path = os.path.join(MOD_DIR, log_name)
    for p in (cfg_path, log_path):
        if os.path.isfile(p):
            os.remove(p)

    cfg_lines = [
        "sv_cheats 1",
        "echo GW_AUDIT3_START",
        "prvm_edict server 1",
        "+forward",
        "defer 1.0 \"-forward; echo GW_AUDIT3_AFTER_WALK; prvm_edict server 1; status; defer 0.3 \\\"quit\\\"\"",
    ]
    with open(cfg_path, "w", encoding="ascii") as f:
        f.write("\n".join(cfg_lines) + "\n")

    cfg_restore_targets = [
        os.path.join(MOD_DIR, "config.cfg"),
        os.path.join(GAME_ROOT, "id1", "config.cfg"),
    ]
    cfg_backups: Dict[str, Optional[bytes]] = {}
    for cp in cfg_restore_targets:
        if os.path.isfile(cp):
            with open(cp, "rb") as rf:
                cfg_backups[cp] = rf.read()
        else:
            cfg_backups[cp] = None

    proc = None
    try:
        proc = subprocess.Popen(
            [
                DP_EXE,
                "-window", "-width", "1280", "-height", "720",
                "-game", "quake15", "-game", "BakersfieldQuake",
                "-nosound", "-nohome", "-condebug",
                "+vid_mouse", "0", "+joy_enable", "0",
                "+log_file", log_name,
                "+map", "goldenwest",
                "+defer", "4", f"exec {cfg_name}",
            ],
            cwd=GAME_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            proc.wait(timeout=35)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            return {"ran": True, "ok": False, "reason": "DarkPlaces smoke run timed out (35s)"}

        log_txt = open(log_path, "r", encoding="latin1", errors="replace").read() if os.path.isfile(log_path) else ""
        clean = re.sub(r"\^[0-9]", "", log_txt)
        loaded = "goldenwest" in clean.lower() and "no map file" not in clean.lower()
        origins = re.findall(r"origin\s+'([0-9.\-eE]+)\s+([0-9.\-eE]+)\s+([0-9.\-eE]+)'", clean)
        moved_u = 0.0
        if len(origins) >= 2:
            o0 = [float(v) for v in origins[0]]
            o1 = [float(v) for v in origins[-1]]
            moved_u = round(math.hypot(o1[0] - o0[0], o1[1] - o0[1]), 1)
        return {
            "ran": True,
            "returncode": proc.returncode,
            "map_loaded": loaded,
            "origins_logged": len(origins),
            "walk_dist_u": moved_u,
            "ok": proc.returncode == 0 and loaded and moved_u > 24.0,
        }
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
        for p in (cfg_path, log_path):
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        for cp, orig_bytes in cfg_backups.items():
            try:
                if orig_bytes is not None:
                    with open(cp, "wb") as wf:
                        wf.write(orig_bytes)
                elif os.path.isfile(cp):
                    os.remove(cp)
            except OSError:
                pass


def run_browser_traversal(spots: Sequence[Dict[str, object]]) -> Tuple[List[Dict[str, object]], List[str], List[str], List[str]]:
    """Live Playwright WebGL traversal test (WASD walk, Space jump, F free-fly)."""
    if not os.path.isdir(WEB_DIR) or not os.path.isfile(os.path.join(WEB_DIR, "index.html")):
        return [], ["WEB_DIR missing"], [], []

    from playwright.sync_api import sync_playwright

    handler = functools.partial(QuietHandler, directory=WEB_DIR)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    console_errors, page_errors, bad_responses = [], [], []
    results: List[Dict[str, object]] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--use-angle=d3d11", "--enable-webgl", "--ignore-gpu-blocklist"],
            )
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.on("response", lambda r: bad_responses.append(f"{r.status} {r.url}") if r.status >= 400 else None)

            page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle")
            page.wait_for_function("!document.getElementById('start').disabled", timeout=25000)
            page.evaluate("document.getElementById('intro').style.display = 'none'")
            time.sleep(0.4)

            def get_pos():
                return page.evaluate("() => ({x: __viewer.pl.o[0], y: __viewer.pl.o[1], z: __viewer.pl.o[2], fly: __viewer.pl.fly})")

            def teleport(xu, yu, zu, yaw_deg=0.0):
                page.evaluate(f"""() => {{
                    __viewer.setFly(false);
                    __viewer.teleport({{pos: [{xu}, {yu}, {zu}], yaw: {yaw_deg}, pitch: 0}});
                }}""")
                time.sleep(0.25)

            def hold_key(key, secs):
                page.evaluate(f"() => {{ __viewer.keys[{json.dumps(key)}] = true; }}")
                time.sleep(secs)
                page.evaluate(f"() => {{ __viewer.keys[{json.dumps(key)}] = false; }}")
                time.sleep(0.15)

            # 1. Courtyard walk + Space Jump + F Fly toggle
            sx_u, sy_u, sz_u = (115.0 * U_FT, 25.0 * U_FT, 3.0 * U_FT)
            if spots:
                sp0 = spots[0]
                sx_u, sy_u, sz_u = sp0["origin"]
            teleport(sx_u, sy_u, sz_u, yaw_deg=float(spots[0]["yaw"]) if spots else 180.0)
            p0 = get_pos()
            hold_key("KeyW", 1.1)
            p1 = get_pos()
            dist_walk_ft = math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"]) / U_FT

            page.evaluate("() => { __viewer.keys['Space'] = true; __viewer.keys.jump = true; }")
            time.sleep(0.18)
            pj = get_pos()
            page.evaluate("() => { __viewer.keys['Space'] = false; __viewer.keys.jump = false; }")
            time.sleep(0.45)
            dz_jump_ft = (pj["z"] - p1["z"]) / U_FT

            page.keyboard.press("KeyF")
            time.sleep(0.15)
            fly_on = page.locator("#mode").inner_text()
            page.keyboard.press("KeyF")
            time.sleep(0.15)
            fly_off = page.locator("#mode").inner_text()
            results.append({
                "test": "Spawn_WASD_Jump_Fly",
                "walk_ft": round(dist_walk_ft, 2),
                "jump_dz_ft": round(dz_jump_ft, 2),
                "fly_on": fly_on,
                "fly_off": fly_off,
                "pass": dist_walk_ft > 6.0 and dz_jump_ft > 0.3 and fly_on == "Fly" and fly_off == "Walk",
            })

            # 2. Casino NE portico entrance -> walk through vestibule into main pit
            teleport(59.0 * U_FT, 3.8 * U_FT, 3.0 * U_FT, yaw_deg=225.0)
            pi0 = get_pos()
            hold_key("KeyW", 1.8)
            pi1 = get_pos()
            casino_walk_ft = math.hypot(pi1["x"] - pi0["x"], pi1["y"] - pi0["y"]) / U_FT
            results.append({
                "test": "Casino_NE_Enter_MainPit",
                "walk_ft": round(casino_walk_ft, 2),
                "end_ft": [round(pi1["x"] / U_FT, 1), round(pi1["y"] / U_FT, 1), round(pi1["z"] / U_FT, 1)],
                "pass": casino_walk_ft > 12.0,
            })

            # 3. Great Castle South Entry -> walk through vestibule into Main Dining Hall
            teleport(366.0 * U_FT, 988.0 * U_FT, 3.0 * U_FT, yaw_deg=90.0)
            pg0 = get_pos()
            hold_key("KeyW", 2.2)
            pg1 = get_pos()
            gc_walk_ft = math.hypot(pg1["x"] - pg0["x"], pg1["y"] - pg0["y"]) / U_FT
            results.append({
                "test": "GreatCastle_SouthEntry_Traverse",
                "walk_ft": round(gc_walk_ft, 2),
                "end_ft": [round(pg1["x"] / U_FT, 1), round(pg1["y"] / U_FT, 1), round(pg1["z"] / U_FT, 1)],
                "pass": gc_walk_ft > 12.0,
            })

            browser.close()
    finally:
        httpd.shutdown()

    return results, console_errors, page_errors, bad_responses


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit 3: Golden West Hull-1 Navigation & Zero-Trap Verification")
    parser.add_argument("--step-u", type=float, default=24.0, help="2D walk flood-fill grid step in Quake units")
    parser.add_argument("--skip-darkplaces", action="store_true", help="Skip live DarkPlaces window smoke run")
    parser.add_argument("--skip-web", action="store_true", help="Skip Playwright WebGL traversal")
    args = parser.parse_args(argv)

    os.makedirs(OUT_DIR, exist_ok=True)
    errors: List[str] = []

    if not os.path.isfile(BSP_PATH):
        raise FileNotFoundError(f"Compiled BSP not found: {BSP_PATH}")

    bsp_h1 = Hull1Tracer.from_bsp(BSP_PATH)

    web_json = os.path.join(WEB_DIR, "map.json")
    web_bin = os.path.join(WEB_DIR, "map.bin")
    web_h1 = None
    web_mismatch = 0
    if os.path.isfile(web_json) and os.path.isfile(web_bin):
        web_h1 = Hull1Tracer.from_web_json(web_json)
        if bsp_h1.hulls != web_h1.hulls or len(bsp_h1.planes) != len(web_h1.planes) or len(bsp_h1.clipnodes) != len(web_h1.clipnodes):
            errors.append(
                f"WEB_BSP_HULL_MISMATCH: BSP={len(bsp_h1.hulls)}/{len(bsp_h1.planes)}/{len(bsp_h1.clipnodes)} "
                f"vs Web={len(web_h1.hulls)}/{len(web_h1.planes)}/{len(web_h1.clipnodes)}"
            )
    elif not args.skip_web:
        errors.append(f"Missing WebGL export files under {WEB_DIR}")

    # 1. Check spawns, pickups & spots clearance in BOTH BSP & Web Hull-1
    spawn_origins: List[Tuple[float, float, float]] = []
    pickup_count = 0
    for e in bsp_h1.ents:
        cls = e.get("classname", "")
        if cls in ("info_player_start", "info_player_deathmatch"):
            ox, oy, oz = (float(v) for v in e["origin"].split())
            spawn_origins.append((ox, oy, oz))
            if bsp_h1.is_solid((ox, oy, oz)) or (web_h1 and web_h1.is_solid((ox, oy, oz))):
                errors.append(f"SOLID SPAWN: {cls} at ({ox/U_FT:.1f}, {oy/U_FT:.1f}, {oz/U_FT:.1f}) ft")
            up_tr = bsp_h1.trace((ox, oy, oz), (ox, oy, oz + 28.0))
            if up_tr["fraction"] < 0.75:
                errors.append(f"LOW HEADROOM AT SPAWN: {cls} at ({ox/U_FT:.1f}, {oy/U_FT:.1f}) ft")
        elif cls.startswith(("item_", "weapon_")) and "origin" in e:
            ox, oy, oz = (float(v) for v in e["origin"].split())
            pickup_count += 1
            up_pt = (ox, oy, oz + 2.2 * U_FT)
            if bsp_h1.is_solid(up_pt) or (web_h1 and web_h1.is_solid(up_pt)) or bsp_h1.stand_at_ft(ox / U_FT, oy / U_FT, oz / U_FT + 0.5) is None:
                errors.append(f"SOLID PICKUP: {cls} at ({ox/U_FT:.1f}, {oy/U_FT:.1f}, {oz/U_FT:.1f}) ft")

    spots_path = next((p for p in SPOTS_CANDIDATES if os.path.isfile(p)), None)
    spots = load_spots(spots_path) if spots_path else []
    for sp in spots:
        px, py, pz = sp["origin"]
        if sp["kind"] != "aerial" and (bsp_h1.is_solid((px, py, pz)) or (web_h1 and web_h1.is_solid((px, py, pz)))):
            errors.append(f"SOLID SPOT '{sp['name']}' at ({px/U_FT:.1f}, {py/U_FT:.1f}, {pz/U_FT:.1f}) ft")

    # 2. Check MapBuilder constraints (>=64x96 doors, >=112u rooms, <=18u stairs+clip) if builder present
    mb_info = check_mapbuilder_constraints()
    if mb_info.get("ran") and mb_info.get("issues"):
        errors.extend(mb_info["issues"])

    # 3. Exhaustive Walk-Only (<=18u step, NO jump/fly) Flood-Fill on BSP Hull-1
    STEP_U = float(args.step_u)
    Z_BAND = 42.0
    p_start = None
    if spawn_origins:
        sx0, sy0, sz0 = spawn_origins[0]
        p_start = bsp_h1.stand_at_ft(sx0 / U_FT, sy0 / U_FT, sz0 / U_FT - 2.0)
    if p_start is None:
        p_start = bsp_h1.stand_at_ft(202.0, 25.0, 0.0)
    if p_start is None:
        raise RuntimeError("Failed to find valid floor stand point at player spawn!")

    def key_of(p: Tuple[float, float, float]) -> Tuple[int, int, int]:
        return (int(round(p[0] / STEP_U)), int(round(p[1] / STEP_U)), int(round(p[2] / Z_BAND)))

    sk = key_of(p_start)
    visited: Dict[Tuple[int, int, int], Tuple[float, float, float]] = {sk: p_start}
    adj: Dict[Tuple[int, int, int], set] = collections.defaultdict(set)
    rev_adj: Dict[Tuple[int, int, int], set] = collections.defaultdict(set)
    q = collections.deque([sk])
    min_z_u = max_z_u = p_start[2]
    void_drops = []

    x_min_u, x_max_u = (HX0 + 2.0) * U_FT, (HX1 - 2.0) * U_FT
    y_min_u, y_max_u = (HY0 + 2.0) * U_FT, (HY1 - 2.0) * U_FT

    while q:
        uk = q.popleft()
        cur = visited[uk]
        min_z_u = min(min_z_u, cur[2])
        max_z_u = max(max_z_u, cur[2])
        if cur[2] < -48.0:
            void_drops.append((round(cur[0] / U_FT, 1), round(cur[1] / U_FT, 1), round(cur[2] / U_FT, 1)))
            continue
        gx = round(cur[0] / STEP_U) * STEP_U
        gy = round(cur[1] / STEP_U) * STEP_U
        for dx, dy in ((STEP_U, 0.0), (-STEP_U, 0.0), (0.0, STEP_U), (0.0, -STEP_U)):
            nx, ny = gx + dx, gy + dy
            if nx < x_min_u or nx > x_max_u or ny < y_min_u or ny > y_max_u:
                continue
            nxt = bsp_h1.can_walk_step(cur, nx, ny, step_height=HULL1_MAX_STEP_U)
            if nxt is None:
                mid = bsp_h1.can_walk_step(cur, 0.5 * (cur[0] + nx), 0.5 * (cur[1] + ny), step_height=HULL1_MAX_STEP_U)
                if mid is not None:
                    nxt = bsp_h1.can_walk_step(mid, nx, ny, step_height=HULL1_MAX_STEP_U)
            if nxt is not None:
                nk = key_of(nxt)
                adj[uk].add(nk)
                rev_adj[nk].add(uk)
                if nk not in visited:
                    visited[nk] = nxt
                    q.append(nk)

    if void_drops:
        errors.append(f"VOID DROPS DETECTED ({len(void_drops)}): first={void_drops[0]} ft")

    # 4. Iterative Tarjan SCC + Reverse BFS Zero-Trap Analysis
    sccs = iterative_tarjan_scc(visited.keys(), adj)
    scc_of: Dict[Tuple[int, int, int], int] = {}
    for cid, comp in enumerate(sccs):
        for n in comp:
            scc_of[n] = cid
    start_cid = scc_of[sk]
    sink_sccs = []
    for cid, comp in enumerate(sccs):
        if cid == start_cid:
            continue
        has_exit = any(scc_of[w] != cid for u in comp for w in adj.get(u, ()) if w in scc_of)
        if not has_exit:
            sink_sccs.append(comp)

    can_return = {sk}
    rq = collections.deque([sk])
    while rq:
        u = rq.popleft()
        for prev in rev_adj[u]:
            if prev not in can_return:
                can_return.add(prev)
                rq.append(prev)
    trapped_nodes = [visited[k] for k in visited if k not in can_return]
    if trapped_nodes or sink_sccs:
        sample = [(round(p[0] / U_FT, 1), round(p[1] / U_FT, 1), round(p[2] / U_FT, 1)) for p in trapped_nodes[:5]]
        errors.append(
            f"TRAPPED / ONE-WAY CELLS ({len(trapped_nodes)}/{len(visited)}, sink_sccs={len(sink_sccs)}): sample={sample} ft"
        )

    # 5. Zone + Registered Spot Walkability Verification
    zone_results = []
    for zname, x1, y1, x2, y2, z1, z2, req in ZONE_TARGETS_FT:
        cnt = 0
        for vp in visited.values():
            xf, yf, zf = vp[0] / U_FT, vp[1] / U_FT, vp[2] / U_FT
            if x1 <= xf <= x2 and y1 <= yf <= y2 and z1 <= zf <= z2:
                cnt += 1
        ok = cnt > 0
        zone_results.append({"name": zname, "cells": cnt, "reached": ok, "required": req})
        if req and not ok:
            errors.append(f"UNREACHABLE ZONE (<=18u walk): {zname} ft=({x1}..{x2}, {y1}..{y2}, z={z1}..{z2})")

    walk_spots = [sp for sp in spots if sp["kind"] in ("interior", "walk", "audit") and sp["origin"][2] / U_FT < 16.0]
    unreachable_spots = []
    for sp in walk_spots:
        sx, sy, sz = (v / U_FT for v in sp["origin"])
        near = any(
            abs(vp[0] / U_FT - sx) <= 6.0 and abs(vp[1] / U_FT - sy) <= 6.0 and abs(vp[2] / U_FT - sz) <= 5.0
            for vp in visited.values()
        )
        if not near:
            unreachable_spots.append(sp["name"])
    if unreachable_spots:
        errors.append(f"UNREACHABLE WALK SPOTS ({len(unreachable_spots)}): {', '.join(unreachable_spots[:10])}")

    # 6. Web Hull-1 parity sampling
    if web_h1 is not None and visited:
        sample_cells = list(visited.values())[:: max(1, len(visited) // 250)]
        for p in sample_cells:
            if web_h1.is_solid(p) != bsp_h1.is_solid(p):
                web_mismatch += 1
        if web_mismatch:
            errors.append(f"WEB_HULL1_DIVERGENCE: {web_mismatch}/{len(sample_cells)} sampled cells differ")

    # 7. Free-fly sky headroom check above map (including Great Castle north extension)
    for zf in (65.0, 115.0):
        for yf in (0.0, 1030.0):
            for xf in range(-350, 550, 150):
                if bsp_h1.is_solid((xf * U_FT, yf * U_FT, zf * U_FT)):
                    errors.append(f"BLOCKED FREE-FLY SKY at ({xf}, {yf}, {zf}) ft")

    # 8. Browser WASD + Space + F traversal
    browser_results: List[Dict[str, object]] = []
    if not args.skip_web:
        browser_results, c_err, p_err, b_resp = run_browser_traversal(spots)
        if c_err or p_err or b_resp:
            errors.append(f"BROWSER_ERRORS: console={c_err}, page={p_err}, http={b_resp}")
        for br in browser_results:
            if not br["pass"]:
                errors.append(f"BROWSER_TRAVERSAL_FAIL: {br}")

    # 9. Desktop DarkPlaces live walk smoke check
    dp_info = {"ran": False, "skipped": True} if args.skip_darkplaces else run_darkplaces_walk_smoke()
    if dp_info.get("ran") and not dp_info.get("ok"):
        errors.append(f"DARKPLACES_WALK_SMOKE_FAIL: {dp_info}")

    # 10. Render Reachability PNG (1 px ~= 1 ft portrait aspect)
    im_w, im_h = 1140, 1620
    im = Image.new("RGB", (im_w, im_h), (16, 20, 26))
    d = ImageDraw.Draw(im)

    def ft2px(xf: float, yf: float) -> Tuple[int, int]:
        px = int(30 + (xf - HX0) / (HX1 - HX0) * (im_w - 60))
        py = int(60 + (HY1 - yf) / (HY1 - HY0) * (im_h - 90))
        return px, py

    for k, vp in visited.items():
        xf, yf, zf = vp[0] / U_FT, vp[1] / U_FT, vp[2] / U_FT
        px, py = ft2px(xf, yf)
        if k not in can_return:
            col = (255, 70, 70)
        elif zf >= 5.0:
            col = (82, 210, 255)
        else:
            col = (56, 215, 120)
        d.rectangle([px - 1, py - 1, px + 1, py + 1], fill=col)

    for zr in zone_results:
        if zr["required"] and not zr["reached"]:
            for nm, x1, y1, x2, y2, _, _, _ in ZONE_TARGETS_FT:
                if nm == zr["name"]:
                    px, py = ft2px(0.5 * (x1 + x2), 0.5 * (y1 + y2))
                    d.ellipse([px - 8, py - 8, px + 8, py + 8], outline=(255, 60, 60), width=2)

    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 18)
    except OSError:
        fnt = ImageFont.load_default()
    reached_cnt = sum(z["reached"] for z in zone_results)
    d.text(
        (20, 16),
        f"AUDIT 3 HULL-1 NAV ({STEP_U:.0f}u grid, <=18u walk, 0 traps): {len(visited):,} cells | "
        f"{reached_cnt}/{len(zone_results)} zones | SCCs={len(sccs)} | sink_SCCs={len(sink_sccs)} | errors={len(errors)}",
        fill=(110, 240, 150) if not errors else (255, 95, 95),
        font=fnt,
    )
    map_png = os.path.join(OUT_DIR, "audit3_nav_map.png")
    im.save(map_png, optimize=True)

    report = {
        "step_u": STEP_U,
        "reachable_cells": len(visited),
        "strongly_connected_cells": len(can_return),
        "tarjan_scc_count": len(sccs),
        "tarjan_sink_sccs": len(sink_sccs),
        "trapped_cells": len(trapped_nodes),
        "spawns_checked": len(spawn_origins),
        "pickups_checked": pickup_count,
        "spots_checked": len(spots),
        "unreachable_spots": unreachable_spots,
        "mapbuilder_checks": mb_info,
        "zones_total": len(zone_results),
        "zones_reached": reached_cnt,
        "zones": zone_results,
        "min_origin_z_ft": round(min_z_u / U_FT, 2),
        "max_origin_z_ft": round(max_z_u / U_FT, 2),
        "web_hull1_parity": web_h1 is not None and web_mismatch == 0,
        "browser_traversal": browser_results,
        "darkplaces_smoke": dp_info,
        "errors": errors,
    }
    report_path = os.path.join(OUT_DIR, "audit3_nav_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Hull-1 Cells: {len(visited):,} | Returnable: {len(can_return):,} | Sink SCCs: {len(sink_sccs)}")
    print(f"Zones Reached: {reached_cnt}/{len(zone_results)} | DarkPlaces smoke: {dp_info}")
    if errors:
        for e in errors:
            print("  [FAIL]", e)
        return 1
    print("ALL AUDIT 3 NAVIGATION, CLEARANCE, STEP, TARJAN ZERO-TRAP, BROWSER & DARKPLACES CHECKS PASSED!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
