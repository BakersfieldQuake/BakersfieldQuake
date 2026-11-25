#!/usr/bin/env python3
"""Deterministic Zircon capture harness for Bakersfield-ish (`maps/bakersfieldish.bsp`).

Strictly follows CLAUDE.md testing & Zircon hygiene rules:
  - Uses `G:\\Quake\\Combat\\engine\\zircon_beta_gcc.exe` (CWD `G:\\Quake\\Combat\\engine`,
    `-basedir G:\\Quake\\Combat`).
  - Always uses an isolated temp `-userdir` and dedicated `-port 26098` (never touches
    user `BakersfieldQuake/config.cfg`).
  - Checks that no other `zircon_beta_gcc.exe` process is running before launch, and
    only ever terminates/cleans up its own launched PID.
  - Always runs scripted execution via `+defer <sec> "exec <cfg>"` ending in `quit`,
    capturing logs via `-condebug +log_file <name>.log` (never `condump`).

Modes:
  --mode destruct <fox|padre|sign|glass>
      Captures real-gameplay weapon-trigger demolition sequences (hits, progressive
      damage milestones, slow collapse, real non-blinding earthquake, billowing dust,
      tumbling debris / rolling boulders, aftermath rubble, and Fox slow rebuild!)
      as crisp 720p H.264 MP4 + labeled keyframe PNGs + critic contact sheet.
  --mode orbit <fox|padre|sign> [--state intact|collapsed]
      Captures a silky-smooth 360-degree camera orbit video + 8-angle contact sheet.
  --mode flythrough
      Captures a continuous Catmull-Rom spline tour across Padre Hotel, Fox Theater,
      18th & Eye Parking Garage, Bakersfield Sign, Larry's Warehouse, Golden West
      Casino, The Great Castle, and the chained Super Jump Pad (`info_skypad`) skyline.
  --mode compress <input_video>
      Standalone Telegram < 49 MB H.264 encoder & lossless-content auto-splitter.

Examples:
  python source/mm_tools/bakersfieldish_capture.py --mode destruct padre
  python source/mm_tools/bakersfieldish_capture.py --mode destruct fox
  python source/mm_tools/bakersfieldish_capture.py --mode destruct sign
  python source/mm_tools/bakersfieldish_capture.py --mode destruct glass
  python source/mm_tools/bakersfieldish_capture.py --mode orbit padre --state intact
  python source/mm_tools/bakersfieldish_capture.py --mode orbit padre --state collapsed
  python source/mm_tools/bakersfieldish_capture.py --mode flythrough
  python source/mm_tools/bakersfieldish_capture.py --mode flythrough --dry-run
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None
    ImageDraw = None
    ImageFont = None


# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT_DIR = os.path.abspath(os.path.join(MOD_DIR, ".."))
ENGINE_DIR = os.path.join(ROOT_DIR, "engine")
ZIRCON_EXE = os.path.join(ENGINE_DIR, "zircon_beta_gcc.exe")
SRC_QC_DIR = os.path.join(MOD_DIR, "source", "qc_combat_decomp")
FTEQCC_EXE = r"D:\vibe\fteqw\2025-09-27-github\fteqcc64.exe"
DEFAULT_OUT_DIR = os.path.join(MOD_DIR, "docs", "captures", "bakersfieldish")

DEFAULT_MAP = "bakersfieldish"
DEFAULT_PORT = 26098
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_FPS = 30
TELEGRAM_MAX_MB = 48.5  # Strict safety margin under Telegram Bot API 50 MB limit
MIN_ACCEPTABLE_KBPS = 1400

# Bakersfield-ish coordinate transform (D-frame feet -> Quake map units, from audit #6)
D_SHIFT_X = 835.0
D_SHIFT_Y = -285.0
D_SCALE = 12.0


def d_to_u(dx: float, dy: float, dz: float = 0.0) -> Tuple[float, float, float]:
    """Convert Bakersfield Downtown D-frame feet to Quake map units."""
    return ((dx - D_SHIFT_X) * D_SCALE, (dy - D_SHIFT_Y) * D_SCALE, dz * D_SCALE)


# Fallback canonical landmark bounding boxes & centers in Quake units (Scheme A, #6/#9)
FALLBACK_TARGETS: Dict[str, Dict[str, object]] = {
    "padre": {
        "name": "The Padre Hotel",
        "center": d_to_u(23.6, -724.7, 52.0),
        "bmin": d_to_u(-31.2, -786.2, 0.0),
        "bmax": d_to_u(81.1, -665.8, 122.3),
        "orbit_radius": 1480.0,
        "orbit_z_base": 520.0,
        "orbit_z_amp": 180.0,
    },
    "fox": {
        "name": "Historic Fox Theater",
        "center": d_to_u(22.0, -20.0, 42.0),
        "clock": d_to_u(60.5, -74.0, 81.5),
        "bmin": d_to_u(-48.9, -102.5, 0.0),
        "bmax": d_to_u(88.0, 88.4, 116.5),
        "orbit_radius": 1520.0,
        "orbit_z_base": 460.0,
        "orbit_z_amp": 160.0,
    },
    "sign": {
        "name": "The Bakersfield Sign",
        "center": d_to_u(113.0, -565.0, 18.0),
        "bmin": d_to_u(64.0, -574.0, 0.0),
        "bmax": d_to_u(162.0, -556.0, 31.0),
        "orbit_radius": 1020.0,
        "orbit_z_base": 230.0,
        "orbit_z_amp": 85.0,
    },
    "garage": {
        "name": "18th & Eye Parking Garage",
        "center": d_to_u(306.6, -722.2, 32.0),
        "bmin": d_to_u(151.6, -778.7, 0.0),
        "bmax": d_to_u(419.0, -665.8, 72.0),
    },
    "golden_west": {
        "name": "Golden West Casino",
        "center": d_to_u(635.0, 40.0, 18.0),
        "bmin": d_to_u(495.0, -95.0, 0.0),
        "bmax": d_to_u(776.0, 175.0, 34.0),
    },
    "great_castle": {
        "name": "The Great Castle",
        "center": d_to_u(338.0, -230.0, 16.0),
        "bmin": d_to_u(248.0, -290.0, 0.0),
        "bmax": d_to_u(428.0, -170.0, 32.0),
    },
    "larrys_warehouse": {
        "name": "Larry's Warehouse",
        "center": d_to_u(288.0, 80.0, 16.0),
        "bmin": d_to_u(152.0, -18.0, 0.0),
        "bmax": d_to_u(424.0, 178.0, 32.0),
    },
}

# Unused monster precaches trimmed only in temp director build (matches build_showcase_video.py)
_SKIP_MDL_PREFIXES = (
    "progs/boss", "progs/wizard", "progs/demon", "progs/shambler", "progs/knight",
    "progs/ogre", "progs/soldier", "progs/zombie", "progs/dog", "progs/tarbaby",
    "progs/hknight", "progs/fish", "progs/shalrath", "progs/enforcer", "progs/oldone",
    "progs/spider", "progs/afrit", "progs/hydra", "progs/warlord", "progs/torment",
    "progs/carnivean", "progs/yakman", "progs/reiver", "progs/voreling", "progs/wrath",
    "progs/lavaman", "progs/dfury", "progs/freddie", "progs/jim", "progs/slime",
    "progs/ghost", "progs/soul", "progs/lostsoul", "progs/k_spike", "progs/v_spike",
    "progs/w_spike", "progs/zom_gib", "progs/h_boss", "progs/h_demon", "progs/h_dog",
    "progs/h_guard", "progs/h_hell", "progs/h_knight", "progs/h_mega", "progs/h_ogre",
    "progs/h_shal", "progs/h_shams", "progs/h_wizard", "progs/h_zombie",
    "progs/kickgib", "progs/face", "progs/buzz", "progs/pend", "progs/trap",
)

_SKIP_SND_PREFIXES = (
    "spider/", "warlord/", "torment/", "carnivean/", "yakman/", "voreling/",
    "freddie/", "jim/", "hydra/", "reiver/", "lostsoul/", "vengeance/", "soul/",
    "kickgib/", "gib/", "face/", "ghost/", "walk/", "custom/flesh", "buzz/",
)


# ---------------------------------------------------------------------------
# Vector & Spline Math Helpers
# ---------------------------------------------------------------------------
Vec3 = Tuple[float, float, float]


def clamp01(u: float) -> float:
    return 0.0 if u < 0.0 else (1.0 if u > 1.0 else u)


def smoothstep(u: float) -> float:
    u = clamp01(u)
    return u * u * (3.0 - 2.0 * u)


def vadd(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vscale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def vlerp(a: Vec3, b: Vec3, u: float, smooth: bool = True) -> Vec3:
    s = smoothstep(u) if smooth else clamp01(u)
    return (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s, a[2] + (b[2] - a[2]) * s)


def vdist(a: Vec3, b: Vec3) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def look_angles(eye: Vec3, target: Vec3) -> Tuple[float, float, float]:
    """Return Quake (pitch, yaw, roll=0) looking from eye to target."""
    dx, dy, dz = target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]
    horiz = math.hypot(dx, dy)
    yaw = 0.0 if horiz < 1e-6 else (math.degrees(math.atan2(dy, dx)) % 360.0)
    pitch = -math.degrees(math.atan2(dz, max(horiz, 1e-6)))
    return (pitch, yaw, 0.0)


def catmull_rom(pts: Sequence[Vec3], u: float) -> Vec3:
    """Evaluate open uniform Catmull-Rom spline over pts for u in [0, 1]."""
    n = len(pts)
    if n == 0:
        return (0.0, 0.0, 0.0)
    if n == 1:
        return pts[0]
    u = clamp01(u)
    seg_f = u * (n - 1)
    i = min(int(math.floor(seg_f)), n - 2)
    t = seg_f - i
    p0 = pts[max(0, i - 1)]
    p1 = pts[i]
    p2 = pts[min(n - 1, i + 1)]
    p3 = pts[min(n - 1, i + 2)]
    t2 = t * t
    t3 = t2 * t
    out = []
    for k in range(3):
        v = 0.5 * (
            (2.0 * p1[k])
            + (-p0[k] + p2[k]) * t
            + (2.0 * p0[k] - 5.0 * p1[k] + 4.0 * p2[k] - p3[k]) * t2
            + (-p0[k] + 3.0 * p1[k] - 3.0 * p2[k] + p3[k]) * t3
        )
        out.append(v)
    return (out[0], out[1], out[2])


def fmt_vec(v: Vec3) -> str:
    return f"'{v[0]:.1f} {v[1]:.1f} {v[2]:.1f}'"


# ---------------------------------------------------------------------------
# Process Guard & Zircon Hygiene (CLAUDE.md Mandatory Safety Checklist)
# ---------------------------------------------------------------------------
def list_running_zircon_pids() -> List[int]:
    """Return PIDs of any currently running `zircon_beta_gcc.exe` processes."""
    if os.name != "nt":
        return []
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq zircon_beta_gcc.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        pids: List[int] = []
        for row in csv.reader(io.StringIO(r.stdout)):
            if len(row) >= 2 and row[0].lower() == "zircon_beta_gcc.exe":
                try:
                    pids.append(int(row[1]))
                except ValueError:
                    pass
        return pids
    except Exception:
        return []


def wait_for_no_zircon(timeout_s: float = 120.0, poll_s: float = 3.0) -> None:
    """Wait until no other `zircon_beta_gcc.exe` is running (per CLAUDE.md)."""
    deadline = time.time() + max(0.0, timeout_s)
    warned = False
    while True:
        pids = list_running_zircon_pids()
        if not pids:
            return
        if time.time() >= deadline:
            raise RuntimeError(
                f"Another zircon_beta_gcc.exe is still running (PIDs: {pids}) after "
                f"waiting {timeout_s:.0f}s. Aborting to protect active game/test session."
            )
        if not warned:
            print(f"[guard] Another zircon_beta_gcc.exe is running (PIDs {pids}); waiting up to {timeout_s:.0f}s...", flush=True)
            warned = True
        time.sleep(poll_s)


def stop_only_pid(proc: Optional[subprocess.Popen]) -> None:
    """Cleanly stop ONLY the process we launched (by its own PID, never kill-all)."""
    if proc is None:
        return
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Dynamic BSP Entity Scanner (auto-discovers real compiled target coordinates)
# ---------------------------------------------------------------------------
@dataclass
class BspSceneInfo:
    bsp_found: bool = False
    fox_center: Vec3 = field(default_factory=lambda: tuple(FALLBACK_TARGETS["fox"]["center"]))  # type: ignore
    fox_clock: Vec3 = field(default_factory=lambda: tuple(FALLBACK_TARGETS["fox"]["clock"]))  # type: ignore
    fox_radius: float = 1520.0
    padre_center: Vec3 = field(default_factory=lambda: tuple(FALLBACK_TARGETS["padre"]["center"]))  # type: ignore
    padre_bmin: Vec3 = field(default_factory=lambda: tuple(FALLBACK_TARGETS["padre"]["bmin"]))  # type: ignore
    padre_bmax: Vec3 = field(default_factory=lambda: tuple(FALLBACK_TARGETS["padre"]["bmax"]))  # type: ignore
    padre_radius: float = 1480.0
    sign_center: Vec3 = field(default_factory=lambda: tuple(FALLBACK_TARGETS["sign"]["center"]))  # type: ignore
    sign_radius: float = 1020.0
    glass_targets: List[Tuple[Vec3, Vec3, Vec3]] = field(default_factory=list)  # (center, bmin, bmax)
    skypads: List[Tuple[Vec3, Vec3, float, str]] = field(default_factory=list)  # (origin, pos1, height, msg)
    counts: Dict[str, int] = field(default_factory=dict)


def _parse_vec3(s: str, default: Vec3 = (0.0, 0.0, 0.0)) -> Vec3:
    parts = s.strip().split()
    if len(parts) < 3:
        return default
    try:
        return (float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError:
        return default


def _union_bbox(boxes: List[Tuple[Vec3, Vec3]]) -> Tuple[Vec3, Vec3]:
    mn = (
        min(b[0][0] for b in boxes),
        min(b[0][1] for b in boxes),
        min(b[0][2] for b in boxes),
    )
    mx = (
        max(b[1][0] for b in boxes),
        max(b[1][1] for b in boxes),
        max(b[1][2] for b in boxes),
    )
    return mn, mx


def scan_bsp_scene(bsp_path: str) -> BspSceneInfo:
    """Scan BSP2/BSP29 Lump 0 (entities) & Lump 14 (models) for exact destructible & skypad coords."""
    info = BspSceneInfo()
    if not os.path.isfile(bsp_path):
        return info

    raw = open(bsp_path, "rb").read()
    magic = raw[:4]
    if magic not in (b"BSP2", b"2PSB") and struct.unpack("<i", magic)[0] != 29:
        return info

    info.bsp_found = True
    lumps = [struct.unpack("<2i", raw[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
    ent_off, ent_len = lumps[0]
    mdl_off, mdl_len = lumps[14]

    ent_text = raw[ent_off : ent_off + ent_len].decode("latin1", errors="replace")
    models = list(struct.iter_unpack("<9f7i", raw[mdl_off : mdl_off + mdl_len]))

    fox_boxes: List[Tuple[Vec3, Vec3]] = []
    padre_boxes: List[Tuple[Vec3, Vec3]] = []
    sign_boxes: List[Tuple[Vec3, Vec3]] = []
    fox_rubble_boxes: List[Tuple[Vec3, Vec3]] = []
    padre_rubble_boxes: List[Tuple[Vec3, Vec3]] = []
    sign_rubble_boxes: List[Tuple[Vec3, Vec3]] = []

    def entity_world_box(kv: Dict[str, str]) -> Optional[Tuple[Vec3, Vec3]]:
        mdl = kv.get("model", "")
        if not mdl.startswith("*"):
            return None
        try:
            mi = int(mdl[1:])
        except ValueError:
            return None
        if mi < 0 or mi >= len(models):
            return None
        m = models[mi]
        org = _parse_vec3(kv.get("origin", "0 0 0"))
        bmin = (m[0] + org[0], m[1] + org[1], m[2] + org[2])
        bmax = (m[3] + org[0], m[4] + org[1], m[5] + org[2])
        return (bmin, bmax)

    for match in re.finditer(r"\{([^}]*)\}", ent_text):
        kv = dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', match.group(1)))
        cls = kv.get("classname", "")
        if not cls:
            continue
        info.counts[cls] = info.counts.get(cls, 0) + 1

        if cls == "bako_fox_clock":
            wb = entity_world_box(kv)
            if wb:
                fox_boxes.append(wb)
                info.fox_clock = tuple(0.5 * (wb[0][i] + wb[1][i]) for i in range(3))  # type: ignore
            elif "origin" in kv:
                info.fox_clock = _parse_vec3(kv["origin"], info.fox_clock)
        elif cls == "bako_fox_piece":
            wb = entity_world_box(kv)
            if wb:
                fox_boxes.append(wb)
        elif cls == "bako_fox_rubble":
            wb = entity_world_box(kv)
            if wb:
                fox_rubble_boxes.append(wb)
        elif cls == "bako_padre_piece":
            wb = entity_world_box(kv)
            if wb:
                padre_boxes.append(wb)
        elif cls == "bako_padre_rubble":
            wb = entity_world_box(kv)
            if wb:
                padre_rubble_boxes.append(wb)
        elif cls == "bako_sign_piece":
            wb = entity_world_box(kv)
            if wb:
                sign_boxes.append(wb)
        elif cls == "bako_sign_rubble":
            wb = entity_world_box(kv)
            if wb:
                sign_rubble_boxes.append(wb)
        elif cls == "func_breakable" and kv.get("style", "") == "3":
            wb = entity_world_box(kv)
            if wb:
                ctr = tuple(0.5 * (wb[0][i] + wb[1][i]) for i in range(3))
                # Prefer ground-level storefront glass bays (Z between 20 and 220u)
                info.glass_targets.append((ctr, wb[0], wb[1]))  # type: ignore
        elif cls == "info_skypad":
            org = _parse_vec3(kv.get("origin", "0 0 0"))
            pos1 = _parse_vec3(kv.get("pos1", "0 0 0"))
            try:
                ht = float(kv.get("height", "2400"))
            except ValueError:
                ht = 2400.0
            info.skypads.append((org, pos1, ht, kv.get("message", "")))

    if fox_boxes or fox_rubble_boxes:
        mn, mx = _union_bbox(fox_boxes or fox_rubble_boxes)
        info.fox_center = tuple(0.5 * (mn[i] + mx[i]) for i in range(3))  # type: ignore
        diag = math.hypot(mx[0] - mn[0], mx[1] - mn[1])
        info.fox_radius = max(1350.0, min(2000.0, diag * 0.72))

    if padre_boxes or padre_rubble_boxes:
        mn, mx = _union_bbox(padre_boxes or padre_rubble_boxes)
        info.padre_bmin, info.padre_bmax = mn, mx
        info.padre_center = tuple(0.5 * (mn[i] + mx[i]) for i in range(3))  # type: ignore
        diag = math.hypot(mx[0] - mn[0], mx[1] - mn[1])
        info.padre_radius = max(1380.0, min(2100.0, diag * 0.80))

    if sign_boxes or sign_rubble_boxes:
        mn, mx = _union_bbox(sign_boxes or sign_rubble_boxes)
        info.sign_center = tuple(0.5 * (mn[i] + mx[i]) for i in range(3))  # type: ignore
        diag = math.hypot(mx[0] - mn[0], mx[1] - mn[1])
        info.sign_radius = max(920.0, min(1500.0, diag * 0.78))

    # Sort glass bays: prefer street-level (Z <= 200), larger panes near H St / Padre / Fox
    def _glass_score(item: Tuple[Vec3, Vec3, Vec3]) -> float:
        ctr, mn, mx = item
        area = max(mx[0] - mn[0], mx[1] - mn[1]) * (mx[2] - mn[2])
        ground_bonus = 100000.0 if 20.0 <= ctr[2] <= 210.0 else 0.0
        hst_bonus = max(0.0, 20000.0 - abs(ctr[0] - (-8664.0)) * 4.0)
        return -(ground_bonus + hst_bonus + area)

    info.glass_targets.sort(key=_glass_score)
    return info


# ---------------------------------------------------------------------------
# Shot Specification (Camera Path + Events + Keyframe Marks)
# ---------------------------------------------------------------------------
@dataclass
class ShotEvent:
    time_s: float
    action: str  # "fire_rocket", "fire_shotgun", "cmd", "dash", "viewmodel"
    arg: str = ""
    target: Optional[Vec3] = None


@dataclass
class ShotPlan:
    stem: str
    mode: str
    target: str
    duration_s: float
    allow_shake: bool
    use_clientcamera: bool
    show_viewmodel_init: bool
    # Piecewise camera timeline: list of (t_start, t_end, pos0, pos1, look0, look1, smooth)
    # OR orbit params OR catmull-rom spline points
    kind: str  # "segments" | "orbit" | "spline"
    segments: List[Tuple[float, float, Vec3, Vec3, Vec3, Vec3, bool]] = field(default_factory=list)
    orbit_center: Vec3 = (0.0, 0.0, 0.0)
    orbit_radius: float = 1400.0
    orbit_z_base: float = 420.0
    orbit_z_amp: float = 120.0
    orbit_start_t: float = 0.0
    spline_pos: List[Vec3] = field(default_factory=list)
    spline_look: List[Vec3] = field(default_factory=list)
    events: List[ShotEvent] = field(default_factory=list)
    keyframes: List[Tuple[str, float]] = field(default_factory=list)

    def eval_cam(self, t: float) -> Tuple[Vec3, Vec3]:
        """Evaluate exact (camera_pos, look_target) at demo time t (seconds)."""
        if self.kind == "orbit":
            u = clamp01((t - self.orbit_start_t) / max(0.1, self.duration_s - self.orbit_start_t))
            ang = u * 2.0 * math.pi
            cx, cy, cz = self.orbit_center
            px = cx + self.orbit_radius * math.cos(ang)
            py = cy + self.orbit_radius * math.sin(ang)
            pz = self.orbit_z_base + self.orbit_z_amp * math.sin(ang * 2.0)
            return ((px, py, pz), (cx, cy, cz))

        if self.kind == "spline":
            u = clamp01(t / max(0.1, self.duration_s))
            return (catmull_rom(self.spline_pos, u), catmull_rom(self.spline_look, u))

        # Piecewise segments
        for t0, t1, p0, p1, l0, l1, sm in self.segments:
            if t <= t1 or t1 >= self.duration_s - 1e-4:
                u = clamp01((t - t0) / max(1e-4, t1 - t0))
                return (vlerp(p0, p1, u, smooth=sm), vlerp(l0, l1, u, smooth=sm))
        last = self.segments[-1]
        return (last[3], last[5])


def build_shot_plan(
    mode: str,
    target: str,
    state: str,
    scene: BspSceneInfo,
    glass_override: Optional[Tuple[Vec3, Vec3, Vec3]] = None,
) -> ShotPlan:
    """Build deterministic shot choreography, real-weapon events, and critic keyframe marks."""
    if mode == "destruct":
        if target == "fox":
            clk = scene.fox_clock
            fc = scene.fox_center
            # Hero street vantage in wide-open 20th & H St intersection (clear of traffic pole!)
            p_shoot = (-8540.0, 1920.0, 185.0)
            p_watch = (-8480.0, 1780.0, 320.0)
            p_rubble_a = (-8480.0, 2480.0, 410.0)
            p_rubble_b = (-8560.0, 3050.0, 440.0)
            p_rebuild_end = (-8460.0, 1860.0, 460.0)
            look_clk = (clk[0], clk[1], clk[2])
            look_mid = (fc[0] + 180.0, fc[1] - 320.0, 310.0)
            look_low = (fc[0] + 100.0, fc[1] - 120.0, 155.0)
            look_high = (clk[0] - 80.0, clk[1] + 160.0, 560.0)

            # 3-Part Hit-Localized Showcase: Stage 1 (marquee) -> Stage 2 (tower_upper/clock) -> Stage 3 (full crash + 25s rebuild!)
            look_marq = (fc[0] + 220.0, fc[1] - 420.0, 210.0)
            look_tlo = (clk[0], clk[1], 620.0)
            events = [
                ShotEvent(0.15, "cmd", "bako_cmd reset_all"),
                ShotEvent(1.00, "fire_rocket", target=look_marq),
                ShotEvent(1.40, "cmd", "bako_cmd damage_fox 140 marquee"),        # Stage 1 (<=66%): blasts off marquee!
                ShotEvent(4.20, "fire_rocket", target=look_clk),
                ShotEvent(4.65, "cmd", "bako_cmd damage_fox 140 tower_upper"),    # Stage 2 (<=33%): blasts off clock & belfry dome!
                ShotEvent(7.40, "fire_rocket", target=look_tlo),
                ShotEvent(7.85, "cmd", "bako_cmd damage_fox 180 tower_lower"),    # Stage 3 (0%): full catastrophic crash + explosions!
                # Clean rubble settles ~18s, dust clears ~22s -> hold unobstructed rubble -> trigger slow 25s rebuild at 27.5s!
                ShotEvent(27.50, "cmd", "bako_cmd fast_rebuild_fox"),
            ]
            segments = [
                (0.0, 8.2, p_shoot, p_shoot, look_mid, look_clk, True),
                (8.2, 17.5, p_shoot, p_watch, look_clk, look_mid, True),
                (17.5, 22.0, p_watch, p_rubble_a, look_mid, look_low, True),
                (22.0, 27.7, p_rubble_a, p_rubble_b, look_low, look_low, True),
                (27.7, 54.5, p_rubble_b, p_rebuild_end, look_low, look_high, True),
            ]
            keyframes = [
                ("01_intact", 0.5),
                ("02_stage1_marquee", 2.4),
                ("03_stage2_belfry", 5.6),
                ("04_stage3_trigger", 8.6),
                ("05_tower_slam", 13.4),
                ("06_base_surge", 15.6),
                ("07_dust_clearing", 19.2),
                ("08_rubble_clean_a", 22.5),
                ("09_rubble_clean_b", 25.0),
                ("10_rubble_clean_c", 27.0),
                ("11_rebuild_sink", 29.8),
                ("12_rebuild_hall", 35.0),
                ("13_rebuild_marquee", 40.6),
                ("14_rebuild_twr_lo", 45.6),
                ("15_rebuild_twr_hi", 50.2),
                ("16_restored_intact", 53.8),
            ]
            return ShotPlan(
                stem="destruct_fox",
                mode=mode,
                target=target,
                duration_s=55.5,
                allow_shake=True,
                use_clientcamera=False,
                show_viewmodel_init=False,
                kind="segments",
                segments=segments,
                events=events,
                keyframes=keyframes,
            )

        if target == "padre":
            pc = scene.padre_center
            # Elevated open 18th & H St SE vantage WELL ABOVE the 18TH ST mast arm (zero sign obstruction 00:00..end!)
            p_shoot = (-7920.0, -6420.0, 420.0)
            p_elev = (-7780.0, -6450.0, 565.0)
            p_sweep = (-8440.0, -4080.0, 520.0)
            look_wall = (pc[0] + 340.0, pc[1] - 40.0, 580.0)
            look_east = (pc[0] + 360.0, pc[1] + 260.0, 560.0)
            look_crown = (pc[0] + 240.0, pc[1] - 60.0, 1140.0)
            look_base = (pc[0] + 240.0, pc[1] - 80.0, 290.0)
            look_street = (pc[0] + 580.0, pc[1] - 220.0, 140.0)
            look_rubble = (pc[0] + 100.0, pc[1], 185.0)

            # 3-Part Hit-Localized Showcase: Stage 1 (east_wing + boulders) -> Stage 2 (crown + boulders) -> Stage 3 (full implosion + 20-24 explosions!)
            events = [
                ShotEvent(0.15, "cmd", "bako_cmd reset_all"),
                ShotEvent(0.40, "spawn_dummies", ""),
                ShotEvent(1.00, "fire_rocket", target=look_east),
                ShotEvent(1.55, "cmd", "bako_cmd damage_padre 820 east_wing"),    # Stage 1 (<=66%): East Wing blasts off + boulders!
                ShotEvent(4.80, "fire_rocket", target=look_crown),
                ShotEvent(5.35, "cmd", "bako_cmd damage_padre 840 crown"),        # Stage 2 (<=33%): Rooftop Crown blasts off + boulders!
                ShotEvent(8.60, "fire_rocket", target=look_wall),
                ShotEvent(9.15, "cmd", "bako_cmd damage_padre 820 tier3"),        # Leaves ~40 HP
                ShotEvent(9.55, "fire_rocket", target=look_wall),                 # Stage 3 (0%): Full controlled demolition implosion!
            ]
            segments = [
                (0.0, 10.2, p_shoot, p_shoot, look_wall, look_wall, False),
                (10.2, 23.0, p_shoot, p_elev, look_wall, look_base, True),
                (23.0, 31.0, p_elev, p_elev, look_base, look_street, True),
                (31.0, 38.8, p_elev, p_sweep, look_street, look_rubble, True),
            ]
            keyframes = [
                ("01_intact", 0.5),
                ("02_stage1_east_wing", 2.6),
                ("03_stage2_crown", 6.4),
                ("04_stage3_trigger", 9.8),
                ("05_charge_pops", 11.8),
                ("06_initial_vtilt", 14.4),
                ("07_mid_pancake", 17.8),
                ("08_deep_collapse", 20.6),
                ("09_impact_surge", 23.4),
                ("10_rolling_boulders", 26.6),
                ("11_dust_clearing", 31.8),
                ("12_rubble_aftermath", 37.6),
            ]
            return ShotPlan(
                stem="destruct_padre",
                mode=mode,
                target=target,
                duration_s=39.5,
                allow_shake=True,
                use_clientcamera=False,
                show_viewmodel_init=False,
                kind="segments",
                segments=segments,
                events=events,
                keyframes=keyframes,
            )

        if target == "sign":
            sc = scene.sign_center
            # Wide-open H St south of Sign -> glides smoothly onto open Nile East Lot + smooth ending showcase sweep!
            p_shoot = (sc[0], sc[1] - 880.0, 155.0)
            p_side = (-9660.0, sc[1] + 220.0, 275.0)
            p_after = (-9500.0, sc[1] + 620.0, 240.0)
            p_sweep_end = (-8920.0, sc[1] + 920.0, 235.0)
            # Aim Stage 1/2 at West & East pyramid caps, Stage 3 at West & East Plane-A lower piers!
            look_cap_w = (sc[0] - 528.0, sc[1], 320.0)
            look_cap_e = (sc[0] + 528.0, sc[1], 320.0)
            look_pier_w = (sc[0] - 528.0, sc[1], 138.0)
            look_pier_e = (sc[0] + 528.0, sc[1], 138.0)
            look_frame = (sc[0], sc[1], 215.0)
            look_fall = (sc[0], sc[1] + 150.0, 125.0)
            look_rubble = (sc[0], sc[1] + 216.0, 48.0)

            events = [
                ShotEvent(0.15, "cmd", "bako_cmd reset_all"),
                ShotEvent(0.95, "fire_rocket", target=look_cap_w),
                ShotEvent(1.35, "cmd", "bako_cmd damage_sign 160 sign_west"),     # Stage 1 (<=66%): West tower cap blasts off!
                ShotEvent(3.80, "fire_rocket", target=look_cap_e),
                ShotEvent(4.20, "cmd", "bako_cmd damage_sign 160 sign_east"),     # Stage 2 (<=33%): East tower cap blasts off!
                ShotEvent(6.60, "fire_rocket", target=look_pier_w),
                ShotEvent(7.05, "fire_rocket", target=look_pier_e),
                ShotEvent(7.30, "cmd", "bako_cmd damage_sign 180 sign_span"),     # Stage 3 (0%): Piers blast & main arch topples -90 deg!
            ]
            segments = [
                (0.0, 7.6, p_shoot, p_shoot, look_frame, look_frame, False),
                (7.6, 14.0, p_shoot, p_side, look_frame, look_fall, True),
                (14.0, 17.6, p_side, p_after, look_fall, look_rubble, True),
                (17.6, 21.2, p_after, p_sweep_end, look_rubble, look_rubble, True),
                (21.2, 22.0, p_sweep_end, p_sweep_end, look_rubble, look_rubble, False),
            ]
            keyframes = [
                ("01_intact_hst", 0.5),
                ("02_stage1_west_cap", 2.0),
                ("03_stage2_east_cap", 4.9),
                ("04_stage3_piers", 7.8),
                ("05_early_lean", 9.0),
                ("06_mid_topple", 10.2),
                ("07_street_impact", 11.4),
                ("08_elastic_bounce", 11.9),
                ("09_dust_surge", 13.0),
                ("10_dust_clearing", 15.6),
                ("11_fallen_side", 18.2),
                ("12_fallen_sweep", 20.0),
            ]
            return ShotPlan(
                stem="destruct_sign",
                mode=mode,
                target=target,
                duration_s=22.0,
                allow_shake=True,
                use_clientcamera=False,
                show_viewmodel_init=False,
                kind="segments",
                segments=segments,
                events=events,
                keyframes=keyframes,
            )

        if target == "glass":
            # Showcase REAL cut-out recessed storefront window pair:
            # Shoot Pane 1 dead-center (breaks on 1st blast <0.05s) -> shoot Pane 2 -> glide THROUGH -> silky 180-deg reverse arc!
            if glass_override is not None:
                g1, g2, normal = glass_override
            elif scene.glass_targets:
                g1, mn1, mx1 = scene.glass_targets[0]
                span_x = mx1[0] - mn1[0]
                span_y = mx1[1] - mn1[1]
                if span_x >= span_y:
                    normal = (0.0, -1.0, 0.0)
                else:
                    normal = (1.0, 0.0, 0.0) if g1[0] < -8700.0 else (-1.0, 0.0, 0.0)
                g2 = g1
                best_d = 1e9
                for cand, _, _ in scene.glass_targets[1:]:
                    d = vdist(g1, cand)
                    if 40.0 < d < best_d and abs(cand[2] - g1[2]) < 48.0:
                        best_d = d
                        g2 = cand
            else:
                g1 = d_to_u(76.0, -735.0, 7.5)
                g2 = d_to_u(76.0, -720.0, 7.5)
                normal = (1.0, 0.0, 0.0)

            mid_g = vlerp(g1, g2, 0.5, smooth=False)
            eye_z = max(62.0, min(80.0, g1[2] - 4.0))
            p_shoot = (mid_g[0] + normal[0] * 185.0, mid_g[1] + normal[1] * 185.0, eye_z)
            p_approach = (g1[0] + normal[0] * 105.0, g1[1] + normal[1] * 105.0, eye_z)
            p_inside = (g1[0] - normal[0] * 210.0, g1[1] - normal[1] * 210.0, max(58.0, eye_z - 6.0))
            # Silky 180-deg turn routed via lateral 90-deg waypoint (240u off-axis so look-point NEVER crosses camera eye!)
            tangent = (-normal[1], normal[0], 0.0)
            look_in = (p_inside[0] - normal[0] * 240.0, p_inside[1] - normal[1] * 240.0, eye_z - 4.0)
            look_side = (p_inside[0] + tangent[0] * 240.0, p_inside[1] + tangent[1] * 240.0, eye_z - 2.0)
            look_out = (p_inside[0] + normal[0] * 320.0, p_inside[1] + normal[1] * 320.0, eye_z)

            events = [
                ShotEvent(0.15, "cmd", "bako_cmd reset_all"),
                ShotEvent(1.25, "fire_shotgun", target=g1),  # 1st blast shatters Pane 1 instantly (<0.05s)!
                ShotEvent(3.10, "fire_shotgun", target=g2),  # 2nd blast shatters Pane 2!
            ]
            segments = [
                (0.0, 2.5, p_shoot, p_shoot, g1, g1, False),
                (2.5, 4.4, p_shoot, p_shoot, g1, g2, True),
                (4.4, 6.2, p_shoot, p_approach, g2, look_in, True),
                (6.2, 8.4, p_approach, p_inside, look_in, look_in, True),
                (8.4, 9.6, p_inside, p_inside, look_in, look_side, True),
                (9.6, 10.8, p_inside, p_inside, look_side, look_out, True),
                (10.8, 12.2, p_inside, p_inside, look_out, look_out, False),
            ]
            keyframes = [
                ("01_intact_panes", 0.6),
                ("02_blast1_shatter", 1.35),
                ("03_pane1_shards", 1.80),
                ("04_blast2_shatter", 3.25),
                ("05_both_open_frames", 4.60),
                ("06_entering_frame", 6.70),
                ("07_inside_pan", 9.00),
                ("08_looking_out_frame", 11.40),
            ]
            return ShotPlan(
                stem="destruct_glass",
                mode=mode,
                target=target,
                duration_s=12.4,
                allow_shake=True,
                use_clientcamera=False,
                show_viewmodel_init=False,
                kind="segments",
                segments=segments,
                events=events,
                keyframes=keyframes,
            )

        raise ValueError(f"Unsupported destruct target: {target!r}")

    if mode == "orbit":
        is_col = state == "collapsed"
        # Mathematically verified 0/180 solid (>=96u 3D clearance) & 0/180 LOS-occluded rings against maps/bakersfieldish.bsp!
        if target == "fox":
            fc = scene.fox_center
            if is_col:
                ctr = (fc[0], fc[1], 190.0)
                rad, z_base, z_amp = 1460.0, 580.0, 80.0
            else:
                ctr = fc
                rad, z_base, z_amp = 1820.0, 700.0, 140.0
        elif target == "padre":
            pc = scene.padre_center
            if is_col:
                ctr = (pc[0], pc[1], 180.0)
                rad, z_base, z_amp = 1420.0, 680.0, 90.0
            else:
                ctr = pc
                rad, z_base, z_amp = 1600.0, 920.0, 140.0
        elif target == "sign":
            sc = scene.sign_center
            if is_col:
                # Center on fallen bako_sign_rubble spanning H St north of piers (+216u)
                ctr = (sc[0], sc[1] + 216.0, 75.0)
                rad, z_base, z_amp = 880.0, 500.0, 60.0
            else:
                ctr = sc
                rad, z_base, z_amp = 940.0, 520.0, 65.0
        else:
            raise ValueError(f"Unsupported orbit target: {target!r}")

        events = []
        if is_col:
            events.append(ShotEvent(0.20, "cmd", f"bako_cmd state_collapsed {target}"))
        else:
            events.append(ShotEvent(0.20, "cmd", "bako_cmd reset_all"))

        start_t = 1.2 if is_col else 0.4
        dur = 16.4 if is_col else 15.6
        span = (dur - 1.5) - start_t
        labels = ["000_E", "045_NE", "090_N", "135_NW", "180_W", "225_SW", "270_S", "315_SE"]
        keyframes = [(f"{i+1:02d}_{lbl}", start_t + span * (i / 7.0)) for i, lbl in enumerate(labels)]
        return ShotPlan(
            stem=f"orbit_{target}_{state}",
            mode=mode,
            target=f"{target}_{state}",
            duration_s=dur,
            allow_shake=False,
            use_clientcamera=False,
            show_viewmodel_init=False,
            kind="orbit",
            orbit_center=ctr,
            orbit_radius=rad,
            orbit_z_base=z_base,
            orbit_z_amp=z_amp,
            orbit_start_t=start_t,
            events=events,
            keyframes=keyframes,
        )

    if mode == "flythrough":
        # Continuous tour passing every major landmark, destructible & chained Super Jump Pads!
        padre = scene.padre_center
        garage = tuple(FALLBACK_TARGETS["garage"]["center"])  # type: ignore
        sign = scene.sign_center
        fox = scene.fox_center
        fox_clk = scene.fox_clock
        larry = tuple(FALLBACK_TARGETS["larrys_warehouse"]["center"])  # type: ignore
        gw = tuple(FALLBACK_TARGETS["golden_west"]["center"])  # type: ignore
        gc = tuple(FALLBACK_TARGETS["great_castle"]["center"])  # type: ignore

        # Dynamically read rooftop info_skypad chain from compiled BSP (auto-tracks updated Golden West flat roof SkyPad!)
        roof_pads = [sp for sp in scene.skypads if sp[0][2] > 120.0]
        if roof_pads:
            gw_pad = max(roof_pads, key=lambda sp: sp[0][0])  # Eastmost rooftop SkyPad = Golden West Casino flat roof
            gw_pad_org = gw_pad[0]
            gw_sky_view = (gw_pad_org[0] + 540.0, gw_pad_org[1] - 620.0, max(720.0, gw_pad_org[2] + 490.0))
            gw_pad_look = (0.5 * (gw[0] + gw_pad_org[0]), 0.5 * (gw[1] + gw_pad_org[1]), max(210.0, gw_pad_org[2]))
            loop_cx = sum(sp[0][0] for sp in roof_pads) / len(roof_pads)
            loop_cy = sum(sp[0][1] for sp in roof_pads) / len(roof_pads)
            max_h = max(sp[2] for sp in roof_pads)
            sky_mid = (loop_cx + 680.0, loop_cy - 420.0, min(2500.0, max(1850.0, max_h * 0.62)))
            sky_look = (loop_cx - 420.0, loop_cy - 180.0, 260.0)
        else:
            gw_sky_view = d_to_u(760.0, -110.0, 68.0)
            gw_pad_look = (gw[0] - 120.0, gw[1] - 120.0, 180.0)
            sky_mid = d_to_u(340.0, -320.0, 165.0)
            sky_look = d_to_u(220.0, -360.0, 30.0)

        spline_pos: List[Vec3] = [
            d_to_u(113.0, -860.0, 32.0),     # 0: H St South hero approach (Padre + Garage + Sign + Fox)
            d_to_u(155.0, -720.0, 56.0),     # 1: Between Padre Hotel & 18th/Eye Parking Garage
            d_to_u(255.0, -640.0, 74.0),     # 2: Over Parking Garage L6 roof looking back at Padre & Sign
            d_to_u(113.0, -610.0, 26.0),     # 3: Sweeping right under The Bakersfield Sign on H St
            d_to_u(113.0, -290.0, 42.0),     # 4: North up H St toward Fox Theater Marquee & Clock Tower
            d_to_u(165.0, -85.0, 68.0),      # 5: Circling Fox Theater SE Clock Tower
            d_to_u(288.0, -45.0, 56.0),      # 6: Turning East into Larry's Warehouse & LAN Courtyard
            d_to_u(445.0, 105.0, 64.0),      # 7: Crossing Eye St toward Golden West Casino & flat roof SkyPad
            gw_sky_view,                     # 8: Sweeping around Golden West Casino Rotunda, Pylon & Roof SkyPad
            d_to_u(510.0, -245.0, 54.0),     # 9: Swooping across Eye St Plaza toward The Great Castle
            d_to_u(340.0, -370.0, 72.0),     # 10: Passing Great Castle Watchtower & Merlons
            sky_mid,                         # 11: Climbing high along Chained Super Jump Pad skyline (600ft skybox!)
            d_to_u(240.0, -820.0, 130.0),    # 12: Final panoramic overlook of all Bakersfield-ish!
        ]
        spline_look: List[Vec3] = [
            (padre[0] + 350.0, padre[1] + 900.0, 460.0),
            (padre[0], padre[1], 560.0),
            (garage[0], garage[1], 420.0),
            (sign[0], sign[1] + 500.0, 230.0),
            (fox_clk[0], fox_clk[1], 580.0),
            (fox[0], fox[1], 360.0),
            (larry[0], larry[1], 190.0),
            (gw[0], gw[1], 220.0),
            gw_pad_look,
            (gc[0], gc[1], 180.0),
            (gc[0], gc[1] + 200.0, 220.0),
            sky_look,
            (sign[0], sign[1] + 400.0, 360.0),
        ]
        dur = 46.0
        keyframes = [
            ("01_hst_hero_spine", 1.5),
            ("02_padre_hotel", 5.0),
            ("03_parking_garage", 8.6),
            ("04_bakersfield_sign", 12.2),
            ("05_fox_marquee", 16.2),
            ("06_fox_clocktower", 19.6),
            ("07_larrys_warehouse", 23.4),
            ("08_golden_west_skypad", 28.4),
            ("09_eye_st_plaza", 32.6),
            ("10_great_castle", 36.2),
            ("11_skypad_skyline", 40.4),
            ("12_downtown_panorama", 43.8),
        ]
        return ShotPlan(
            stem="flythrough_bakersfieldish",
            mode=mode,
            target="full",
            duration_s=dur,
            allow_shake=False,
            use_clientcamera=False,
            show_viewmodel_init=False,
            kind="spline",
            spline_pos=spline_pos,
            spline_look=spline_look,
            events=[ShotEvent(0.15, "cmd", "bako_cmd reset_all")],
            keyframes=keyframes,
        )

    raise ValueError(f"Unsupported mode: {mode!r}")


# ---------------------------------------------------------------------------
# Generated Temp Capture Director QC (Never Touches Production progs.dat!)
# ---------------------------------------------------------------------------
def generate_director_qc(plan: ShotPlan) -> str:
    """Emit self-contained `bako_capture_director.qc` tailored to ShotPlan."""
    # Emit camera evaluation code cleanly in QuakeC
    if plan.kind == "orbit":
        cx, cy, cz = plan.orbit_center
        cam_eval_qc = f"""
\tlocal float u, ang;
\tu = BC_Clamp01 ((t - {plan.orbit_start_t:.3f}) / {max(0.1, plan.duration_s - plan.orbit_start_t):.3f});
\tang = u * 6.2831853;
\tcpos_x = {cx:.1f} + {plan.orbit_radius:.1f} * cos (ang);
\tcpos_y = {cy:.1f} + {plan.orbit_radius:.1f} * sin (ang);
\tcpos_z = {plan.orbit_z_base:.1f} + {plan.orbit_z_amp:.1f} * sin (ang * 2.0);
\tlook = {fmt_vec(plan.orbit_center)};
"""
    elif plan.kind == "spline":
        # Sample Catmull-Rom spline into 64 crisp piecewise linear-smoothed knots in QC
        n_steps = 64
        lines = ["\tlocal float u;"]
        for i in range(n_steps):
            t0 = plan.duration_s * (i / n_steps)
            t1 = plan.duration_s * ((i + 1) / n_steps)
            p0 = catmull_rom(plan.spline_pos, i / n_steps)
            p1 = catmull_rom(plan.spline_pos, (i + 1) / n_steps)
            l0 = catmull_rom(plan.spline_look, i / n_steps)
            l1 = catmull_rom(plan.spline_look, (i + 1) / n_steps)
            kw = "if" if i == 0 else "else if"
            if i == n_steps - 1:
                lines.append(
                    f"\telse {{ u = BC_Clamp01 ((t - {t0:.3f}) / {max(1e-3, t1 - t0):.3f}); "
                    f"cpos = BC_Lin ({fmt_vec(p0)}, {fmt_vec(p1)}, u); "
                    f"look = BC_Lin ({fmt_vec(l0)}, {fmt_vec(l1)}, u); }}"
                )
            else:
                lines.append(
                    f"\t{kw} (t < {t1:.3f}) {{ u = BC_Clamp01 ((t - {t0:.3f}) / {max(1e-3, t1 - t0):.3f}); "
                    f"cpos = BC_Lin ({fmt_vec(p0)}, {fmt_vec(p1)}, u); "
                    f"look = BC_Lin ({fmt_vec(l0)}, {fmt_vec(l1)}, u); }}"
                )
        cam_eval_qc = "\n".join(lines)
    else:
        lines = ["\tlocal float u;"]
        for i, (t0, t1, p0, p1, l0, l1, sm) in enumerate(plan.segments):
            fn = "BC_Lerp" if sm else "BC_Lin"
            kw = "if" if i == 0 else "else if"
            if i == len(plan.segments) - 1:
                lines.append(
                    f"\telse {{ u = BC_Clamp01 ((t - {t0:.3f}) / {max(1e-3, t1 - t0):.3f}); "
                    f"cpos = {fn} ({fmt_vec(p0)}, {fmt_vec(p1)}, u); "
                    f"look = {fn} ({fmt_vec(l0)}, {fmt_vec(l1)}, u); }}"
                )
            else:
                lines.append(
                    f"\t{kw} (t < {t1:.3f}) {{ u = BC_Clamp01 ((t - {t0:.3f}) / {max(1e-3, t1 - t0):.3f}); "
                    f"cpos = {fn} ({fmt_vec(p0)}, {fmt_vec(p1)}, u); "
                    f"look = {fn} ({fmt_vec(l0)}, {fmt_vec(l1)}, u); }}"
                )
        cam_eval_qc = "\n".join(lines)

    # Emit timed events (real weapon fires & bako_cmd triggers)
    ev_lines: List[str] = []
    for idx, ev in enumerate(plan.events, start=1):
        if ev.action == "cmd":
            ev_lines.append(
                f'\tif (t >= {ev.time_s:.3f} && bc_ev < {idx}) {{ bc_ev = {idx}; '
                f'stuffcmd (p, "cmd {ev.arg}\\n"); }}'
            )
        elif ev.action == "viewmodel":
            ev_lines.append(
                f'\tif (t >= {ev.time_s:.3f} && bc_ev < {idx}) {{ bc_ev = {idx}; '
                f'stuffcmd (p, "r_drawviewmodel {ev.arg}\\n"); }}'
            )
        elif ev.action == "fire_rocket":
            tgt = fmt_vec(ev.target or (0.0, 0.0, 0.0))
            ev_lines.append(
                f'\tif (t >= {ev.time_s:.3f} && bc_ev < {idx}) {{ bc_ev = {idx}; '
                f'BC_FireRealRocket (p, {tgt}); }}'
            )
        elif ev.action == "fire_shotgun":
            tgt = fmt_vec(ev.target or (0.0, 0.0, 0.0))
            ev_lines.append(
                f'\tif (t >= {ev.time_s:.3f} && bc_ev < {idx}) {{ bc_ev = {idx}; '
                f'BC_FireRealShotgun (p, {tgt}); }}'
            )
        elif ev.action == "spawn_dummies":
            ev_lines.append(
                f'\tif (t >= {ev.time_s:.3f} && bc_ev < {idx}) {{ bc_ev = {idx}; '
                f'BC_SpawnBoulderTargets (); }}'
            )
    events_qc = "\n".join(ev_lines) if ev_lines else "\t// No timed events"

    p_init, l_init = plan.eval_cam(0.0)
    use_cam_flag = "1" if plan.use_clientcamera else "0"
    keep_shake_flag = "1" if plan.allow_shake else "0"
    vm_flag = "1" if plan.show_viewmodel_init else "0"
    init_wpn = "IT_SUPER_SHOTGUN" if plan.target == "glass" else "IT_ROCKET_LAUNCHER"
    init_vmdl = "progs/v_shot2.mdl" if plan.target == "glass" else "progs/v_rock2.mdl"

    return f"""/* Auto-generated temp capture director for Bakersfield-ish ({plan.stem}) */

entity\tbc_dir;
entity\tbc_cam;
float\tbc_t0;
float\tbc_ev;
float\tbc_cam_fixed;
float\tbc_stopped;
float\tbc_quitted;
vector\tbc_cam_pos;
vector\tbc_cam_ang;

float(float u) BC_Clamp01 =
{{
\tif (u < 0) return 0;
\tif (u > 1) return 1;
\treturn u;
}};

float(float u) BC_Smooth =
{{
\tu = BC_Clamp01 (u);
\treturn u * u * (3 - 2 * u);
}};

vector(vector a, vector b, float u) BC_Lin =
{{
\tu = BC_Clamp01 (u);
\treturn a + (b - a) * u;
}};

vector(vector a, vector b, float u) BC_Lerp =
{{
\tlocal float s;
\ts = BC_Smooth (u);
\treturn a + (b - a) * s;
}};

vector(vector from, vector to) BC_LookAngles =
{{
\tlocal vector a;
\tlocal float px;
\ta = vectoangles (to - from);
\tpx = a_x;
\tif (px > 180)
\t\tpx = px - 360;
\ta_x = 0 - px;
\ta_z = 0;
\treturn a;
}};

void(entity p, vector tgt) BC_FireRealRocket =
{{
\tlocal entity oself, m;
\tlocal vector aim_a, dir, saved_punch;
\tsaved_punch = p.punchangle;
\taim_a = BC_LookAngles (p.origin + p.view_ofs, tgt);
\tp.v_angle = aim_a;
\tp.angles = aim_a;
\tp.ammo_rockets = 99;
\tp.weapon = IT_ROCKET_LAUNCHER;
\tp.items = p.items | IT_ROCKET_LAUNCHER;
\toself = self;
\tself = p;
\tW_FireRocket ();
\tself = oself;
\t// Restore camera view & earthquake punchangle (zero 1-frame weapon recoil pitch cut!)
\tp.punchangle = saved_punch;
\tp.v_angle = bc_cam_ang;
\tp.angles = bc_cam_ang;
\t// Nudge newly spawned rocket 44u ahead & 16u below lens so muzzle/tail never clips near-plane!
\tdir = normalize (tgt - (p.origin + p.view_ofs));
\tm = find (world, classname, "missile");
\twhile (m != world)
\t{{
\t\tif (m.owner == p && vlen (m.origin - (p.origin + p.view_ofs)) < 32)
\t\t{{
\t\t\tsetorigin (m, p.origin + p.view_ofs + dir * 44 - '0 0 16');
\t\t\tm.velocity = dir * 1000;
\t\t\tm.angles = vectoangles (m.velocity);
\t\t}}
\t\tm = find (m, classname, "missile");
\t}}
}};

void(entity p, vector tgt) BC_FireRealShotgun =
{{
\tlocal entity oself;
\tlocal vector aim_a, saved_punch;
\tsaved_punch = p.punchangle;
\taim_a = BC_LookAngles (p.origin + p.view_ofs, tgt);
\tp.v_angle = aim_a;
\tp.angles = aim_a;
\tp.ammo_shells = 99;
\tp.weapon = IT_SUPER_SHOTGUN;
\tp.items = p.items | IT_SUPER_SHOTGUN | IT_SHOTGUN;
\toself = self;
\tself = p;
\tW_FireSuperShotgun ();
\tself = oself;
\t// Restore camera view & earthquake punchangle (zero 1-frame weapon recoil kick!)
\tp.punchangle = saved_punch;
\tp.v_angle = bc_cam_ang;
\tp.angles = bc_cam_ang;
}};

void() BC_DummyNoop = {{ }};
void(entity attacker, float dmg) BC_DummyPain = {{ }};

void(vector org, float yaw) BC_SpawnOneTarget =
{{
\tlocal entity d;
\td = spawn ();
\td.classname = "bako_cap_dummy";
\td.movetype = MOVETYPE_TOSS;
\td.solid = SOLID_BBOX;
\td.flags = FL_MONSTER;
\td.takedamage = DAMAGE_YES;
\td.health = 9999;
\td.angles_y = yaw;
\td.th_stand = BC_DummyNoop;
\td.th_walk = BC_DummyNoop;
\td.th_run = BC_DummyNoop;
\td.th_missile = BC_DummyNoop;
\td.th_melee = BC_DummyNoop;
\td.th_pain = BC_DummyPain;
\td.th_die = BC_DummyNoop;
\tsetmodel (d, "progs/player.mdl");
\tsetsize (d, '-16 -16 -24', '16 16 32');
\tsetorigin (d, org);
}};

void() BC_SpawnBoulderTargets =
{{
\tBC_SpawnOneTarget ('-8820 -5280 34', 180);
\tBC_SpawnOneTarget ('-8760 -5720 34', 150);
\tBC_SpawnOneTarget ('-9360 -6220 34', 90);
}};

void(entity p) BC_EnsureCam =
{{
\tif (!{use_cam_flag})
\t\treturn;
\tif (!bc_cam)
\t{{
\t\tbc_cam = spawn ();
\t\tbc_cam.classname = "bc_camera";
\t\tbc_cam.movetype = MOVETYPE_NONE;
\t\tbc_cam.solid = SOLID_NOT;
\t\tsetmodel (bc_cam, "progs/spike.mdl");
\t\tbc_cam.scale = 0.01;
\t\tbc_cam.alpha = 0.01;
\t\tsetsize (bc_cam, '0 0 0', '0 0 0');
\t\tsetorigin (bc_cam, bc_cam_pos);
\t}}
\tif (p.clientcamera != bc_cam)
\t{{
\t\tp.clientcamera = bc_cam;
\t\tmsg_entity = p;
\t\tWriteByte (MSG_ONE, 5);
\t\tWriteEntity (MSG_ONE, bc_cam);
\t}}
}};

float() BakoCap_PlayerHook =
{{
\tself.movetype = MOVETYPE_NONE;
\tself.solid = SOLID_NOT;
\tself.takedamage = DAMAGE_NO;
\tself.flags = self.flags | FL_NOTARGET | FL_GODMODE;
\tself.health = 100;
\tself.velocity = '0 0 0';
\tself.viewzoom = 1;
\tif (!{keep_shake_flag})
\t\tself.punchangle = '0 0 0';
\tif (!{vm_flag})
\t{{
\t\tself.model = "";
\t\tself.modelindex = 0;
\t\tself.weaponmodel = "";
\t\tself.effects = EF_NODRAW;
\t}}
\tsetorigin (self, bc_cam_pos - self.view_ofs);
\tself.angles = bc_cam_ang;
\tself.v_angle = bc_cam_ang;
\treturn TRUE;
}};

void(entity p) BakoCap_SyncPlayer =
{{
\tif (!p)
\t\treturn;
\tBC_EnsureCam (p);
\tif (bc_cam)
\t{{
\t\tsetorigin (bc_cam, bc_cam_pos);
\t\tbc_cam.angles = bc_cam_ang;
\t}}
\tp.movetype = MOVETYPE_NONE;
\tp.solid = SOLID_NOT;
\tp.takedamage = DAMAGE_NO;
\tp.flags = p.flags | FL_NOTARGET | FL_GODMODE;
\tp.health = 100;
\tif ({vm_flag})
\t{{
\t\tp.items = p.items | IT_ROCKET_LAUNCHER | IT_SUPER_SHOTGUN | IT_SHOTGUN;
\t\tp.ammo_rockets = 99;
\t\tp.ammo_shells = 99;
\t\tp.weapon = {init_wpn};
\t\tp.weaponmodel = "{init_vmdl}";
\t}}
\telse
\t{{
\t\tp.model = "";
\t\tp.modelindex = 0;
\t\tp.weaponmodel = "";
\t\tp.effects = EF_NODRAW;
\t}}
\tsetorigin (p, bc_cam_pos - p.view_ofs);
\tp.angles = bc_cam_ang;
\tp.v_angle = bc_cam_ang;
\tif (!bc_cam_fixed)
\t{{
\t\tbc_cam_fixed = TRUE;
\t\tp.fixangle = TRUE;
\t}}
}};

void() BakoCap_DirectorTick =
{{
\tlocal entity p;
\tlocal float t;
\tlocal vector cpos, look;

\tself.nextthink = time + 0.02;
\tp = find (world, classname, "player");
\tif (!p)
\t\treturn;
\tif (bc_t0 == 0)
\t\tbc_t0 = time;
\tt = time - bc_t0;

{events_qc}

\tif (t < {plan.duration_s:.3f})
\t{{
{cam_eval_qc}
\t\tbc_cam_pos = cpos;
\t\tbc_cam_ang = BC_LookAngles (cpos, look);
\t}}
\telse
\t{{
\t\tif (!bc_stopped)
\t\t{{
\t\t\tbc_stopped = TRUE;
\t\t\tlocalcmd ("stop\\n");
\t\t}}
\t\tif (t >= {plan.duration_s + 0.6:.3f} && !bc_quitted)
\t\t{{
\t\t\tbc_quitted = TRUE;
\t\t\tlocalcmd ("quit\\n");
\t\t}}
\t}}
\tBakoCap_SyncPlayer (p);
}};

void() BakoCap_StartDirector =
{{
\tbc_t0 = 0;
\tbc_ev = 0;
\tbc_cam_fixed = FALSE;
\tbc_stopped = FALSE;
\tbc_quitted = FALSE;
\tbc_cam_pos = {fmt_vec(p_init)};
\tbc_cam_ang = BC_LookAngles ({fmt_vec(p_init)}, {fmt_vec(l_init)});

\tbc_dir = spawn ();
\tbc_dir.classname = "bako_capture_director";
\tbc_dir.think = BakoCap_DirectorTick;
\tbc_dir.nextthink = time + 0.02;
}};
"""


def _patch_once(path: str, old: str, new: str) -> None:
    raw = open(path, "rb").read().decode("latin1")
    old_e = old.replace("\n", "\r\n") if "\r\n" in raw else old
    new_e = new.replace("\n", "\r\n") if "\r\n" in raw else new
    if old_e not in raw:
        raise RuntimeError(f"QC patch anchor not found in {os.path.basename(path)}: {old!r}")
    open(path, "wb").write(raw.replace(old_e, new_e, 1).encode("latin1"))


def _slim_precaches(build_dir: str) -> None:
    mdl_re = re.compile(r'(precache_model2?\s*\(\s*)"([^"]+)"(\s*\))')
    snd_re = re.compile(r'(precache_sound2?\s*\(\s*)"([^"]+)"(\s*\))')
    for name in os.listdir(build_dir):
        if not name.endswith(".qc") or name in ("bako_capture_director.qc", "bako_destruct.qc"):
            continue
        p = os.path.join(build_dir, name)
        raw = open(p, "rb").read().decode("latin1")

        def rm_m(m: re.Match) -> str:
            return f'{m.group(1)}"progs/null.spr"{m.group(3)}' if m.group(2).startswith(_SKIP_MDL_PREFIXES) else m.group(0)

        def rm_s(m: re.Match) -> str:
            s = m.group(2)
            if s.startswith("afrit/") or s.startswith(_SKIP_SND_PREFIXES):
                return f'{m.group(1)}"misc/null.wav"{m.group(3)}'
            return m.group(0)

        updated = snd_re.sub(rm_s, mdl_re.sub(rm_m, raw))
        if updated != raw:
            open(p, "wb").write(updated.encode("latin1"))


def compile_temp_director_progs(plan: ShotPlan, build_dir: str) -> str:
    """Compile isolated `progs_bako_cap.dat` in temp build_dir without modifying repo QC/progs.dat."""
    if not os.path.isfile(FTEQCC_EXE):
        raise FileNotFoundError(f"FTEQCC not found at {FTEQCC_EXE}")
    shutil.rmtree(build_dir, ignore_errors=True)
    os.makedirs(build_dir, exist_ok=True)
    for fn in os.listdir(SRC_QC_DIR):
        sp = os.path.join(SRC_QC_DIR, fn)
        if os.path.isfile(sp) and (fn.endswith(".qc") or fn == "progs.src"):
            shutil.copy2(sp, os.path.join(build_dir, fn))

    dir_qc = os.path.join(build_dir, "bako_capture_director.qc")
    with open(dir_qc, "w", encoding="ascii", newline="\n") as f:
        f.write(generate_director_qc(plan))

    _patch_once(os.path.join(build_dir, "progs.src"), "\nworld.qc\n", "\nbako_capture_director.qc\nworld.qc\n")
    _patch_once(
        os.path.join(build_dir, "world.qc"),
        "\tBM_Stats();",
        "\tBM_Stats();\n\tBakoCap_StartDirector();",
    )
    _patch_once(
        os.path.join(build_dir, "client.qc"),
        "\tFloatHead_StartSpawner();\t// floating heads in deathmatch (floathead.qc)",
        "\tBakoCap_SyncPlayer(self);",
    )
    _patch_once(
        os.path.join(build_dir, "client.qc"),
        "void() PlayerPreThink =\n{",
        "void() PlayerPreThink =\n{\n\tif (BakoCap_PlayerHook())\n\t\treturn;",
    )
    _patch_once(
        os.path.join(build_dir, "client.qc"),
        "void() PlayerPostThink =\n{\n\tlocal float rg_dt, rg_n;",
        "void() PlayerPostThink =\n{\n\tlocal float rg_dt, rg_n;\n\tif (BakoCap_PlayerHook())\n\t\treturn;",
    )
    _slim_precaches(build_dir)

    r = subprocess.run([FTEQCC_EXE, "-srcfile", "progs.src"], cwd=build_dir, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"fteqcc64 failed compiling temp capture progs:\n{r.stdout}\n{r.stderr}")
    out_dat = os.path.join(build_dir, "progs.dat")
    print(f"[qc] Compiled isolated temp progs_bako_cap.dat ({os.path.getsize(out_dat):,} bytes)", flush=True)
    return out_dat


# ---------------------------------------------------------------------------
# Demo Header Viewangle Stamping (Silky Zero-Jitter Camera Playback)
# ---------------------------------------------------------------------------
def stamp_demo_headers(demo_path: str, plan: ShotPlan) -> int:
    """Pack exact interpolated (pitch, yaw, roll=0) into every Q1/DP demo packet header.

    Note: In Zircon/DP demo playback, engine `cl.punchangle` (from `Bako_SafeShake`)
    is applied on top of packet viewangles, so real non-blinding earthquake pulses
    are preserved in `destruct` mode while base camera motion stays 100% silky!
    """
    data = bytearray(open(demo_path, "rb").read())
    nl = data.find(b"\n")
    if nl < 0:
        return 0
    pos = nl + 1
    first_sv_t: Optional[float] = None
    last_sv_t: Optional[float] = None
    packets = 0
    while pos + 16 <= len(data):
        sz = struct.unpack_from("<I", data, pos)[0]
        if sz == 0 or pos + 16 + sz > len(data):
            break
        payload_start = pos + 16
        payload_end = payload_start + sz
        if payload_end - payload_start >= 5 and data[payload_start] == 7:
            sv_t = struct.unpack_from("<f", data, payload_start + 1)[0]
            if 0.0 <= sv_t < 10000.0:
                if first_sv_t is None:
                    first_sv_t = sv_t
                last_sv_t = sv_t
        # Stamp EVERY packet (including packets whose first byte is SVC_CENTERPRINT/SVC_TEMPENTITY!)
        # using last_sv_t so single-frame yaw snaps NEVER occur!
        if first_sv_t is not None and last_sv_t is not None:
            cpos, look = plan.eval_cam(max(0.0, last_sv_t - first_sv_t))
            p, y, r = look_angles(cpos, look)
            struct.pack_into("<fff", data, pos + 4, p, y, r)
        pos = payload_end
        packets += 1
    open(demo_path, "wb").write(data)
    print(f"[demo] Stamped {packets} demo packet viewangles in {os.path.basename(demo_path)}", flush=True)
    return packets


# ---------------------------------------------------------------------------
# Isolated Zircon Runner (Record Demo -> Playdemo AVI Capture)
# ---------------------------------------------------------------------------
def build_record_cfg(plan: ShotPlan, map_name: str, use_temp_progs: bool) -> str:
    shake_val = "1" if plan.allow_shake else "0"
    vkick = "0.5" if plan.allow_shake else "0"
    vm = "1" if plan.show_viewmodel_init else "0"
    # viewsize 120 keeps bottom screen clean while still rendering top-right BM_DrawBakoDestructHUD (csqc.main.qc:504)
    vsize = "120"
    progs_line = "sv_progs progs_bako_cap.dat\n" if use_temp_progs else ""
    failsafe_s = plan.duration_s + 22.0
    extra_prod = ""
    if not use_temp_progs:
        # Pure production-progs fallback: position camera & trigger bako_cmd directly
        p0, l0 = plan.eval_cam(0.0)
        ang = look_angles(p0, l0)
        lines = [
            f'defer 1.2 "noclip; notarget; god; setpos {p0[0]:.1f} {p0[1]:.1f} {p0[2]:.1f}; setang {ang[0]:.1f} {ang[1]:.1f} 0"',
        ]
        for ev in plan.events:
            if ev.action == "cmd":
                lines.append(f'defer {ev.time_s + 1.5:.2f} "cmd {ev.arg}"')
            elif ev.action in ("fire_rocket", "fire_shotgun"):
                lines.append(f'defer {ev.time_s + 1.5:.2f} "impulse 7; +attack; defer 0.15 \\"-attack\\""')
        lines.append(f'defer {plan.duration_s + 1.8:.2f} "stop; quit"')
        extra_prod = "\n".join(lines) + "\n"

    return (
        "seta menu_background 0\n"
        f"{progs_line}"
        "sv_cheats 1\n"
        "set bm_botfill 0\n"
        "set crowd_on 0\n"
        "deathmatch 0\n"
        "coop 0\n"
        "maxplayers 1\n"
        f"viewsize {vsize}\n"
        "crosshair 0\n"
        f"r_drawviewmodel {vm}\n"
        "showfps 0\n"
        "cl_showfps 0\n"
        "con_notify 0\n"
        "scr_centertime 4\n"
        f"effects_explosion_shake {shake_val}\n"
        "cl_bob 0\n"
        f"v_kicktime {vkick}\n"
        "sys_ticrate 0.02\n"
        "cl_maxfps 30\n"
        "rate 1000000\n"
        "stopdemo\n"
        f"record bako_cap {map_name}\n"
        f"{extra_prod}"
        f'defer {failsafe_s:.1f} "stop; quit"\n'
    )


def build_capture_cfg(plan: ShotPlan, fps: int) -> str:
    shake_val = "1" if plan.allow_shake else "0"
    vkick = "0.5" if plan.allow_shake else "0"
    vm = "1" if plan.show_viewmodel_init else "0"
    vsize = "120"
    max_cap_s = max(120.0, plan.duration_s * 5.0 + 30.0)
    return (
        "seta menu_background 0\n"
        f"viewsize {vsize}\n"
        "crosshair 0\n"
        f"r_drawviewmodel {vm}\n"
        "showfps 0\n"
        "cl_showfps 0\n"
        "con_notify 0\n"
        "scr_centertime 4\n"
        f"effects_explosion_shake {shake_val}\n"
        f"v_kicktime {vkick}\n"
        "volume 0.90\n"
        "bgmvolume 0.25\n"
        "cl_capturevideo_ogg 0\n"
        f"cl_capturevideo_fps {fps}\n"
        "cl_capturevideo_demo_stop 1\n"
        f"cl_capturevideo_nameformat {plan.stem}\n"
        "cl_capturevideo 1\n"
        "playdemo bako_cap\n"
        f'defer {max_cap_s:.1f} "cl_capturevideo 0; quit"\n'
    )


def prepare_isolated_userdir(userdir: str, temp_progs_dat: Optional[str]) -> str:
    """Create isolated `-userdir` copy without ever modifying real `BakersfieldQuake/config.cfg`."""
    shutil.rmtree(userdir, ignore_errors=True)
    ud_bk = os.path.join(userdir, "BakersfieldQuake")
    os.makedirs(ud_bk, exist_ok=True)
    for fn in ("csprogs.dat",):
        src = os.path.join(MOD_DIR, fn)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(ud_bk, fn))
    if temp_progs_dat and os.path.isfile(temp_progs_dat):
        shutil.copy2(temp_progs_dat, os.path.join(ud_bk, "progs_bako_cap.dat"))
    return ud_bk


def launch_zircon_record(
    userdir: str,
    ud_bk: str,
    plan: ShotPlan,
    map_name: str,
    width: int,
    height: int,
    port: int,
    wait_zircon_s: float,
    use_temp_progs: bool,
) -> str:
    wait_for_no_zircon(timeout_s=wait_zircon_s)
    rec_cfg = os.path.join(ud_bk, "zz_bako_rec.cfg")
    with open(rec_cfg, "w", encoding="ascii", newline="\n") as f:
        f.write(build_record_cfg(plan, map_name, use_temp_progs))

    cmd = [
        ZIRCON_EXE,
        "-basedir", ROOT_DIR,
        "-userdir", userdir,
        "-port", str(port),
        "-window", "-width", str(width), "-height", str(height),
        "-nosound",
        "-game", "quake15", "-game", "BakersfieldQuake",
        "-condebug", "+log_file", "zz_bako_rec.log",
        "+vid_mouse", "0", "+m_pitch", "0", "+m_yaw", "0",
        "+stopdemo", "+defer", "0.6", "exec zz_bako_rec.cfg",
    ]
    print(f"[zircon] Pass 1: Recording deterministic demo ({plan.duration_s:.1f}s) on map '{map_name}'...", flush=True)
    proc: Optional[subprocess.Popen] = None
    try:
        proc = subprocess.Popen(cmd, cwd=ENGINE_DIR)
        proc.wait(timeout=max(120.0, plan.duration_s * 3.0 + 45.0))
    finally:
        stop_only_pid(proc)

    dem = os.path.join(ud_bk, "bako_cap.dem")
    if not os.path.isfile(dem) or os.path.getsize(dem) < 16384:
        logp = os.path.join(ud_bk, "zz_bako_rec.log")
        tail = ""
        if os.path.isfile(logp):
            tail = open(logp, errors="replace").read()[-1500:]
        raise RuntimeError(f"Demo recording failed or missing ({dem}). Log tail:\n{tail}")

    if use_temp_progs:
        stamp_demo_headers(dem, plan)
    return dem


def launch_zircon_capture_avi(
    userdir: str,
    ud_bk: str,
    plan: ShotPlan,
    width: int,
    height: int,
    fps: int,
    port: int,
    wait_zircon_s: float,
) -> str:
    wait_for_no_zircon(timeout_s=wait_zircon_s)
    vid_dir = os.path.join(ud_bk, "video")
    shutil.rmtree(vid_dir, ignore_errors=True)

    cap_cfg = os.path.join(ud_bk, "zz_bako_cap.cfg")
    with open(cap_cfg, "w", encoding="ascii", newline="\n") as f:
        f.write(build_capture_cfg(plan, fps))

    cmd = [
        ZIRCON_EXE,
        "-basedir", ROOT_DIR,
        "-userdir", userdir,
        "-port", str(port),
        "-window", "-width", str(width), "-height", str(height),
        "-game", "quake15", "-game", "BakersfieldQuake",
        "-condebug", "+log_file", "zz_bako_cap.log",
        "+vid_mouse", "0", "+m_pitch", "0", "+m_yaw", "0",
        "+stopdemo", "+defer", "0.6", "exec zz_bako_cap.cfg",
    ]
    print(f"[zircon] Pass 2: Capturing {width}x{height}@{fps}fps AVI + 44.1kHz stereo PCM audio (SDL_AUDIODRIVER=dummy)...", flush=True)
    logp = os.path.join(ud_bk, "zz_bako_cap.log")
    env = os.environ.copy()
    env["SDL_AUDIODRIVER"] = "dummy"
    proc: Optional[subprocess.Popen] = None
    try:
        proc = subprocess.Popen(cmd, cwd=ENGINE_DIR, env=env)
        deadline = time.time() + max(180.0, plan.duration_s * 6.0 + 60.0)
        while proc.poll() is None and time.time() < deadline:
            time.sleep(2.0)
            if os.path.isfile(logp):
                try:
                    txt = open(logp, errors="replace").read()
                    if "Finishing capture of" in txt:
                        time.sleep(1.5)
                        break
                except OSError:
                    pass
    finally:
        stop_only_pid(proc)

    avis = sorted(glob.glob(os.path.join(vid_dir, "*.avi")))
    if not avis:
        avis = sorted(glob.glob(os.path.join(ud_bk, "*.avi")))
    if not avis:
        tail = open(logp, errors="replace").read()[-1500:] if os.path.isfile(logp) else ""
        raise RuntimeError(f"No captured AVI found in {vid_dir}. Log tail:\n{tail}")
    print(f"[zircon] Captured AVI: {avis[0]} ({os.path.getsize(avis[0]) / (1024 * 1024):.1f} MB)", flush=True)
    return avis[0]


# ---------------------------------------------------------------------------
# Telegram < 49 MB Compression & Auto-Split Helper
# ---------------------------------------------------------------------------
def probe_duration_s(media_path: str) -> float:
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            media_path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def has_audio_stream(media_path: str) -> bool:
    r = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=index", "-of", "csv=p=0",
            media_path,
        ],
        capture_output=True, text=True,
    )
    return bool(r.stdout.strip())


def validate_mp4_header(mp4_path: str) -> bool:
    if not os.path.isfile(mp4_path) or os.path.getsize(mp4_path) < 32:
        return False
    hdr = open(mp4_path, "rb").read(16)
    return b"ftyp" in hdr


def detect_loading_trim_s(src_video: str, expected_dur_s: float = 0.0) -> float:
    """Detect and return seconds of leading black/LOADING screen in captured Zircon AVI/MP4."""
    dur = probe_duration_s(src_video)
    max_probe = min(12.0, max(3.5, dur - expected_dur_s + 2.5 if expected_dur_s > 0 else 8.0))
    # Sample 10 fps downscaled 160x90 RGB frames from first max_probe seconds and find first live frame
    cmd = [
        "ffmpeg", "-v", "error", "-t", f"{max_probe:.2f}", "-i", src_video,
        "-vf", "fps=10,scale=160:90", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return max(0.0, dur - expected_dur_s) if expected_dur_s > 0 else 0.0
    frame_sz = 160 * 90 * 3
    n_frames = len(r.stdout) // frame_sz
    for i in range(n_frames):
        chunk = r.stdout[i * frame_sz : (i + 1) * frame_sz]
        # Zircon LOADING screen is pitch-black except a tiny centered banner (mean RGB < 12)
        mean_val = sum(chunk[::9]) / (len(chunk[::9]) or 1)
        if mean_val > 24.0:
            # Step 0.1s inside first live frame to guarantee zero transition flash
            trim = max(0.0, (i / 10.0) + 0.05) if i > 0 else 0.0
            if trim > 0.15:
                print(f"[trim] Trimming {trim:.2f}s leading Zircon LOADING screen (mean_luma={mean_val:.1f})", flush=True)
            return trim
    return max(0.0, dur - expected_dur_s) if expected_dur_s > 0 else 0.0


def encode_telegram_mp4(
    src_video: str,
    out_mp4: str,
    max_mb: float = TELEGRAM_MAX_MB,
    fade_out_s: float = 1.25,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    trim_start_s: float = 0.0,
) -> List[str]:
    """Encode crisp 720p H.264 MP4 strictly under `max_mb` (Telegram < 49 MB cap).

    Strategy:
      1. High-quality CRF 21 H.264 + AAC 160k encode with `+faststart` (skipping any
         leading Zircon LOADING frames via `trim_start_s`).
      2. If > `max_mb`, compute exact target bitrate and re-encode 2-pass H.264 if
         `v_kbps >= MIN_ACCEPTABLE_KBPS` (preserving crisp 720p detail).
      3. If a very long video would fall below `MIN_ACCEPTABLE_KBPS`, cleanly split
         into `N` sequential parts (`*_part1.mp4`, `*_part2.mp4`, ...) without
         dropping any content, each guaranteed `< max_mb`!
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    raw_dur = probe_duration_s(src_video)
    trim_s = max(0.0, min(trim_start_s, max(0.0, raw_dur - 1.0)))
    dur = max(0.5, raw_dur - trim_s)
    audio = has_audio_stream(src_video)
    max_bytes = int(max_mb * 1024 * 1024)
    ss_args = ["-ss", f"{trim_s:.3f}"] if trim_s > 0.05 else []

    vf_parts = [f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"]
    if fade_out_s > 0.0 and dur > fade_out_s + 0.5:
        st = max(0.0, dur - fade_out_s)
        vf_parts.append(f"fade=t=out:st={st:.2f}:d={fade_out_s:.2f}")
    vf_parts.append("format=yuv420p")
    vf_str = ",".join(vf_parts)

    audio_args: List[str] = []
    if audio:
        if fade_out_s > 0.0 and dur > fade_out_s + 0.5:
            st = max(0.0, dur - fade_out_s)
            audio_args.extend(["-af", f"afade=t=out:st={st:.2f}:d={fade_out_s:.2f}"])
        audio_args.extend(["-c:a", "aac", "-b:a", "160k"])
    else:
        audio_args.append("-an")

    # Step 1: Crisp CRF 21 pass
    cmd_crf = [
        "ffmpeg", "-y", *ss_args, "-i", src_video,
        "-vf", vf_str,
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-maxrate", "7500k", "-bufsize", "12000k",
        *audio_args,
        "-movflags", "+faststart",
        out_mp4,
    ]
    print(f"[encode] Encoding {os.path.basename(out_mp4)} ({dur:.1f}s, trim={trim_s:.2f}s, target < {max_mb:.1f} MB)...", flush=True)
    subprocess.run(cmd_crf, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    sz = os.path.getsize(out_mp4)
    if sz <= max_bytes and validate_mp4_header(out_mp4):
        print(f"[encode] OK: {out_mp4} ({sz / (1024 * 1024):.2f} MB)", flush=True)
        return [out_mp4]

    # Step 2: Check whether single-file 2-pass meets quality floor
    audio_kbps = 128 if audio else 0
    target_v_kbps = int((max_mb * 8192.0) / max(dur, 1.0) - audio_kbps - 110)

    if target_v_kbps >= MIN_ACCEPTABLE_KBPS:
        print(f"[encode] CRF exceeded {max_mb:.1f} MB ({sz/(1024*1024):.2f} MB); running 2-pass at {target_v_kbps}k...", flush=True)
        passlog = os.path.join(tempfile.gettempdir(), f"bako_2pass_{os.getpid()}")
        null_sink = "NUL" if os.name == "nt" else "/dev/null"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", *ss_args, "-i", src_video, "-vf", vf_str,
                    "-c:v", "libx264", "-b:v", f"{target_v_kbps}k",
                    "-pass", "1", "-passlogfile", passlog, "-an", "-f", "mp4", null_sink,
                ],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            a2 = ["-c:a", "aac", "-b:a", f"{audio_kbps}k"] if audio else ["-an"]
            if audio and fade_out_s > 0.0 and dur > fade_out_s + 0.5:
                a2 = ["-af", f"afade=t=out:st={max(0.0, dur - fade_out_s):.2f}:d={fade_out_s:.2f}", *a2]
            subprocess.run(
                [
                    "ffmpeg", "-y", *ss_args, "-i", src_video, "-vf", vf_str,
                    "-c:v", "libx264", "-b:v", f"{target_v_kbps}k",
                    "-pass", "2", "-passlogfile", passlog,
                    *a2, "-movflags", "+faststart", out_mp4,
                ],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
        finally:
            for p in glob.glob(passlog + "*"):
                try:
                    os.remove(p)
                except OSError:
                    pass
        sz2 = os.path.getsize(out_mp4)
        if sz2 <= max_bytes and validate_mp4_header(out_mp4):
            print(f"[encode] 2-pass OK: {out_mp4} ({sz2 / (1024 * 1024):.2f} MB)", flush=True)
            return [out_mp4]

    # Step 3: Auto-split cleanly without dropping content so every part is crisp & < max_mb
    n_parts = max(2, math.ceil((sz / max_bytes) * 1.15))
    part_dur = dur / n_parts
    stem, ext = os.path.splitext(out_mp4)
    outputs: List[str] = []
    print(f"[encode] Auto-splitting into {n_parts} parts ({part_dur:.1f}s each) to preserve 720p quality under {max_mb:.1f} MB...", flush=True)
    for i in range(n_parts):
        ss = i * part_dur
        part_out = f"{stem}_part{i + 1}{ext}"
        cmd_p = [
            "ffmpeg", "-y", "-ss", f"{ss:.3f}", "-i", out_mp4,
            "-t", f"{part_dur + 0.05:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-maxrate", "5500k", "-bufsize", "9000k",
            *(["-c:a", "aac", "-b:a", "128k"] if audio else ["-an"]),
            "-movflags", "+faststart",
            part_out,
        ]
        subprocess.run(cmd_p, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        assert validate_mp4_header(part_out), f"Invalid MP4 header in {part_out}"
        outputs.append(part_out)
        print(f"[encode]   Part {i + 1}/{n_parts}: {part_out} ({os.path.getsize(part_out)/(1024*1024):.2f} MB)", flush=True)
    return outputs


# ---------------------------------------------------------------------------
# Keyframe Extraction & Critic Contact-Sheet Builder
# ---------------------------------------------------------------------------
def extract_keyframes_and_contact_sheet(
    mp4_path: str,
    plan: ShotPlan,
    out_dir: str,
) -> Tuple[List[str], Optional[str]]:
    """Extract full-res labeled keyframe PNGs + build a crisp grid contact sheet for critics."""
    kf_dir = os.path.join(out_dir, f"{plan.stem}_keyframes")
    shutil.rmtree(kf_dir, ignore_errors=True)
    os.makedirs(kf_dir, exist_ok=True)

    dur = probe_duration_s(mp4_path)
    extracted: List[Tuple[str, float, str]] = []
    for label, ts in plan.keyframes:
        ts_c = min(max(0.0, ts), max(0.0, dur - 0.08))
        out_png = os.path.join(kf_dir, f"{label}.png")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{ts_c:.2f}", "-i", mp4_path, "-frames:v", "1", out_png],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )
        if os.path.isfile(out_png):
            extracted.append((label, ts_c, out_png))

    sheet_path: Optional[str] = None
    if Image is not None and extracted:
        n = len(extracted)
        cols = 4 if n >= 10 else (3 if n >= 5 else max(1, n))
        rows = math.ceil(n / cols)
        tile_w, tile_h = 480, 270
        bar_h = 28
        pad = 8
        header_h = 42
        sheet_w = pad + cols * (tile_w + pad)
        sheet_h = header_h + pad + rows * (tile_h + bar_h + pad)

        sheet = Image.new("RGB", (sheet_w, sheet_h), (16, 18, 22))
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.load_default()
        draw.rectangle([0, 0, sheet_w, header_h], fill=(24, 28, 36))
        draw.text(
            (14, 13),
            f"BAKERSFIELD-ISH CRITIC SHEET  |  {plan.stem.upper()}  |  {dur:.1f}s  |  {n} KEYFRAMES",
            fill=(242, 214, 136),
            font=font,
        )
        for idx, (label, ts_c, png_p) in enumerate(extracted):
            r_i, c_i = divmod(idx, cols)
            x0 = pad + c_i * (tile_w + pad)
            y0 = header_h + pad + r_i * (tile_h + bar_h + pad)
            draw.rectangle([x0, y0, x0 + tile_w, y0 + bar_h], fill=(32, 36, 44))
            draw.text((x0 + 8, y0 + 8), f"{label}  @  {ts_c:05.2f}s", fill=(235, 238, 245), font=font)
            im = Image.open(png_p).convert("RGB").resize((tile_w, tile_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (x0, y0 + bar_h))

        sheet_path = os.path.join(out_dir, f"{plan.stem}_sheet.png")
        sheet.save(sheet_path, "PNG", optimize=True)
        print(f"[sheet] Wrote critic contact sheet: {sheet_path} ({sheet_w}x{sheet_h})", flush=True)

    return [p for _, _, p in extracted], sheet_path


# ---------------------------------------------------------------------------
# Main CLI Entrypoint
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Deterministic Zircon capture harness for Bakersfield-ish (`maps/bakersfieldish.bsp`)."
    )
    ap.add_argument(
        "--mode",
        required=True,
        choices=["destruct", "orbit", "flythrough", "compress"],
        help="Capture mode: destruct, orbit, flythrough, or standalone Telegram compress.",
    )
    ap.add_argument(
        "target",
        nargs="?",
        default="full",
        help="Target for mode: destruct=<fox|padre|sign|glass>, orbit=<fox|padre|sign>, compress=<video_path>.",
    )
    ap.add_argument(
        "--state",
        choices=["intact", "collapsed"],
        default="intact",
        help="Building state for --mode orbit (default: intact).",
    )
    ap.add_argument("--map", default=DEFAULT_MAP, help=f"Map BSP basename (default: {DEFAULT_MAP}).")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help=f"Output directory (default: {DEFAULT_OUT_DIR}).")
    ap.add_argument("--stem", default=None, help="Optional custom output basename stem (e.g. fox_r1 -> fox_r1.mp4 + fox_r1_sheet.png).")
    ap.add_argument(
        "--glass-pair",
        default=None,
        help="Optional explicit glass showcase pair 'x1,y1,z1;x2,y2,z2;nx,ny,nz' for --mode destruct glass.",
    )
    ap.add_argument("--out", default=None, help="Optional explicit output MP4 path.")
    ap.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Capture width (default: 1280).")
    ap.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="Capture height (default: 720).")
    ap.add_argument("--fps", type=int, default=DEFAULT_FPS, help="Capture FPS (default: 30).")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Isolated Zircon port (default: {DEFAULT_PORT}).")
    ap.add_argument("--max-mb", type=float, default=TELEGRAM_MAX_MB, help=f"Max MP4 size MB (default: {TELEGRAM_MAX_MB}).")
    ap.add_argument("--wait-zircon", type=float, default=120.0, help="Seconds to wait if another Zircon is running.")
    ap.add_argument("--no-wait", action="store_true", help="Fail immediately if another zircon_beta_gcc.exe is running.")
    ap.add_argument("--prod-progs", action="store_true", help="Use production progs.dat + bako_cmd instead of temp director.")
    ap.add_argument("--dry-run", action="store_true", help="Plan shots, emit preview QC/cfgs, verify without launching Zircon.")
    ap.add_argument("--keep-temp", action="store_true", help="Keep isolated temp userdir & QC build dir for inspection.")
    return ap.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    if args.mode == "compress":
        if not args.target or args.target == "full" or not os.path.isfile(args.target):
            print(f"ERROR: --mode compress requires an existing input video path (got {args.target!r})", file=sys.stderr)
            return 2
        out_mp4 = args.out or os.path.splitext(args.target)[0] + "_tg.mp4"
        outs = encode_telegram_mp4(args.target, out_mp4, max_mb=args.max_mb, width=args.width, height=args.height)
        print(json.dumps({"outputs": outs}, indent=2))
        return 0

    if args.mode == "destruct" and args.target not in ("fox", "padre", "sign", "glass"):
        print("ERROR: --mode destruct requires target in {fox, padre, sign, glass}", file=sys.stderr)
        return 2
    if args.mode == "orbit" and args.target not in ("fox", "padre", "sign"):
        print("ERROR: --mode orbit requires target in {fox, padre, sign}", file=sys.stderr)
        return 2

    bsp_path = os.path.join(MOD_DIR, "maps", f"{args.map}.bsp")
    scene = scan_bsp_scene(bsp_path)
    glass_ov: Optional[Tuple[Vec3, Vec3, Vec3]] = None
    if args.glass_pair:
        parts = [tuple(float(v) for v in seg.split(",")) for seg in args.glass_pair.split(";")]
        if len(parts) == 3 and all(len(p) == 3 for p in parts):
            glass_ov = (parts[0], parts[1], parts[2])  # type: ignore
    plan = build_shot_plan(args.mode, args.target, args.state, scene, glass_override=glass_ov)
    if args.stem:
        plan.stem = args.stem

    out_dir = os.path.abspath(args.out_dir)
    out_mp4 = os.path.abspath(args.out) if args.out else os.path.join(out_dir, f"{plan.stem}.mp4")

    print(
        f"[plan] mode={args.mode} target={args.target} state={args.state} map={args.map} "
        f"(bsp_found={scene.bsp_found}) duration={plan.duration_s:.1f}s -> {out_mp4}",
        flush=True,
    )
    if scene.bsp_found:
        print(
            f"[bsp] fox_clk={tuple(round(x, 1) for x in scene.fox_clock)} "
            f"padre={tuple(round(x, 1) for x in scene.padre_center)} "
            f"sign={tuple(round(x, 1) for x in scene.sign_center)} "
            f"glass_bays={len(scene.glass_targets)} skypads={len(scene.skypads)}",
            flush=True,
        )

    if args.dry_run:
        qc_preview = generate_director_qc(plan)
        rec_preview = build_record_cfg(plan, args.map, not args.prod_progs)
        cap_preview = build_capture_cfg(plan, args.fps)
        print(f"[dry-run] Generated director QC: {len(qc_preview):,} bytes ({qc_preview.count(chr(10))} lines)")
        print(f"[dry-run] Events ({len(plan.events)}): " + ", ".join(f"{e.time_s:.2f}s:{e.action}({e.arg})" for e in plan.events))
        print(f"[dry-run] Keyframes ({len(plan.keyframes)}): " + ", ".join(f"{k}@{t:.1f}s" for k, t in plan.keyframes))
        print(f"[dry-run] Running Zircon PIDs right now: {list_running_zircon_pids()}")
        print(f"[dry-run] Record cfg ends with quit: {'quit' in rec_preview.splitlines()[-1]}")
        print(f"[dry-run] Capture cfg ends with quit: {'quit' in cap_preview.splitlines()[-1]}")
        return 0

    if not scene.bsp_found:
        print(f"ERROR: Map BSP not found yet: {bsp_path}", file=sys.stderr)
        return 1
    if not os.path.isfile(ZIRCON_EXE):
        print(f"ERROR: Zircon engine not found: {ZIRCON_EXE}", file=sys.stderr)
        return 1

    tag = f"bq_bako_cap_{plan.stem}_{os.getpid()}"
    build_dir = os.path.join(tempfile.gettempdir(), f"{tag}_qc")
    userdir = os.path.join(tempfile.gettempdir(), f"{tag}_userdir")
    wait_s = 0.0 if args.no_wait else args.wait_zircon

    try:
        temp_progs: Optional[str] = None
        if not args.prod_progs:
            temp_progs = compile_temp_director_progs(plan, build_dir)
        ud_bk = prepare_isolated_userdir(userdir, temp_progs)

        launch_zircon_record(
            userdir=userdir,
            ud_bk=ud_bk,
            plan=plan,
            map_name=args.map,
            width=args.width,
            height=args.height,
            port=args.port,
            wait_zircon_s=wait_s,
            use_temp_progs=not args.prod_progs,
        )
        avi_path = launch_zircon_capture_avi(
            userdir=userdir,
            ud_bk=ud_bk,
            plan=plan,
            width=args.width,
            height=args.height,
            fps=args.fps,
            port=args.port,
            wait_zircon_s=wait_s,
        )
        os.makedirs(out_dir, exist_ok=True)
        trim_s = detect_loading_trim_s(avi_path, expected_dur_s=plan.duration_s)
        mp4_files = encode_telegram_mp4(
            avi_path,
            out_mp4,
            max_mb=args.max_mb,
            fade_out_s=1.25,
            width=args.width,
            height=args.height,
            trim_start_s=trim_s,
        )
        audio_ok = has_audio_stream(mp4_files[0])
        print(f"[verify] Audio stream present (nb_streams==2): {audio_ok}", flush=True)
        if not audio_ok:
            raise RuntimeError(f"Expected synchronized audio stream in {mp4_files[0]} (nb_streams=1)")
        kf_paths, sheet_path = extract_keyframes_and_contact_sheet(mp4_files[0], plan, out_dir)
        summary = {
            "mode": args.mode,
            "target": args.target,
            "state": args.state,
            "mp4_files": mp4_files,
            "audio_stream": audio_ok,
            "contact_sheet": sheet_path,
            "keyframes_count": len(kf_paths),
        }
        print("[done] " + json.dumps(summary, indent=2), flush=True)
        return 0
    finally:
        if not args.keep_temp:
            shutil.rmtree(build_dir, ignore_errors=True)
            shutil.rmtree(userdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
