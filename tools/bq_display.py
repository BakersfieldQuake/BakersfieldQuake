#!/usr/bin/env python3
"""BAKOQUAKE pre-launch Display & Graphics Picker.

Cross-platform (Windows, macOS, Linux) monitor/resolution/refresh-rate detection,
hardware-aware graphics preset recommendation, dark charcoal/gold Tkinter UI
matching bq_update.py, preference persistence, and Zircon video config generation.

Stdlib + optional tkinter only, so it freezes cleanly with PyInstaller alongside bq_update.py.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional

PREFS_FILENAME = "bq_launcher_prefs.json"
VIDEO_CFG_FILENAME = "bq_launch_video.cfg"

DISPLAY_MODES = (
    ("borderless", "Borderless Fullscreen"),
    ("fullscreen", "Fullscreen"),
    ("windowed", "Windowed"),
)
VALID_MODES = {m[0] for m in DISPLAY_MODES}

GRAPHICS_PRESETS = (
    (
        "simple",
        "Simple",
        "Fastest FPS for laptops & integrated GPUs — disables bloom, dynamic shadows, normal maps, and MSAA.",
    ),
    (
        "normal",
        "Normal",
        "Recommended — full BAKOQUAKE lighting, subtle bloom, normal maps, 4x MSAA, and 16x anisotropic filtering.",
    ),
    (
        "high",
        "High",
        "Maximum eye candy — adds relief parallax mapping, realtime shadowmaps, water reflections, and vivid color.",
    ),
)
VALID_PRESETS = {p[0] for p in GRAPHICS_PRESETS}
PRESET_DESC = {p[0]: p[2] for p in GRAPHICS_PRESETS}

# Known aspect ratios: (ratio_value, label)
_KNOWN_ASPECTS = (
    (16.0 / 9.0, "16:9"),
    (16.0 / 10.0, "16:10"),
    (64.0 / 27.0, "21:9"),
    (43.0 / 18.0, "21:9"),
    (21.0 / 9.0, "21:9"),
    (32.0 / 9.0, "32:9"),
    (4.0 / 3.0, "4:3"),
    (5.0 / 4.0, "5:4"),
    (3.0 / 2.0, "3:2"),
)

# Standard gaming resolutions used to ensure clean aspect-matching steps & Alt+Enter windowed sizes
STANDARD_RESOLUTIONS = (
    # 32:9
    (5120, 1440),
    (3840, 1080),
    # 21:9
    (3840, 1600),
    (3440, 1440),
    (2560, 1080),
    # 16:9
    (3840, 2160),
    (3200, 1800),
    (2560, 1440),
    (1920, 1080),
    (1600, 900),
    (1366, 768),
    (1280, 720),
    # 16:10
    (2560, 1600),
    (1920, 1200),
    (1680, 1050),
    (1440, 900),
    (1280, 800),
    # 3:2
    (3000, 2000),
    (2160, 1440),
    (1440, 960),
    # 4:3
    (1600, 1200),
    (1280, 960),
    (1024, 768),
    (800, 600),
    # 5:4
    (1280, 1024),
)

_GENERIC_MONITOR_NAMES = {
    "",
    "generic pnp monitor",
    "generic non-pnp monitor",
    "generic monitor",
    "default monitor",
    "unknown",
    "display",
}

# Dark charcoal / gold theme matching tools/bq_update.py
THEME = {
    "BG": "#14151a",
    "CARD": "#1d1f27",
    "SUNKEN": "#101217",
    "BORDER": "#2d2f3a",
    "FG": "#f0f2f7",
    "MUTED": "#9aa2b2",
    "ACCENT": "#e8ae12",
    "ACCENT_HOVER": "#f4be2a",
    "ACCENT_TEXT": "#141418",
    "BTN_SEC": "#2b2d36",
    "BTN_SEC_HOVER": "#373a46",
    "GREEN": "#46c97a",
    "AMBER": "#f59e0b",
}


@dataclass
class MonitorInfo:
    id: str
    index: int
    name: str
    device: str
    is_primary: bool
    x: int
    y: int
    width: int
    height: int
    native_width: int
    native_height: int
    hz: int
    resolutions: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class PickerSelection:
    monitor: MonitorInfo
    mode: str
    width: int
    height: int
    preset: str
    remember: bool = False


# ---------------------------------------------------------------------------
# Aspect ratio, resolution filtering, and HUD/window math
# ---------------------------------------------------------------------------

def format_aspect_ratio(width: int, height: int) -> str:
    """Returns a friendly aspect ratio label like '16:9', '21:9', '16:10', or reduced ratio."""
    if width <= 0 or height <= 0:
        return "16:9"
    ratio = float(width) / float(height)
    best_label = None
    best_err = 0.031
    for target, label in _KNOWN_ASPECTS:
        err = abs(ratio - target) / target
        if err < best_err:
            best_err = err
            best_label = label
    if best_label:
        return best_label
    g = math.gcd(int(width), int(height))
    return f"{int(width) // g}:{int(height) // g}"


def filter_resolutions(
    modes: Iterable[tuple[int, int]],
    native_w: int,
    native_h: int,
) -> list[tuple[int, int]]:
    """Deduplicates and filters hardware resolutions to sensible gaming sizes up to native.

    Always includes native and standard aspect-matching steps up to native.
    Sorted descending by pixel area then width.
    """
    native_w = max(640, int(native_w))
    native_h = max(480, int(native_h))
    is_landscape = native_w >= native_h
    native_aspect = float(native_w) / float(native_h)

    res_set: set[tuple[int, int]] = {(native_w, native_h)}
    for raw_w, raw_h in modes:
        w, h = int(raw_w), int(raw_h)
        if w < 800 or h < 600:
            continue
        if w > native_w or h > native_h:
            continue
        if is_landscape and w < h:
            continue
        if not is_landscape and w > h:
            continue
        res_set.add((w, h))

    # Ensure standard aspect-matching steps are always available up to native
    for sw, sh in STANDARD_RESOLUTIONS:
        if sw < 800 or sh < 600:
            continue
        if sw > native_w or sh > native_h:
            continue
        if is_landscape and sw < sh:
            continue
        step_aspect = float(sw) / float(sh)
        if abs(step_aspect - native_aspect) / native_aspect <= 0.035:
            res_set.add((sw, sh))

    return sorted(res_set, key=lambda r: (r[0] * r[1], r[0]), reverse=True)


def format_resolution_label(
    width: int,
    height: int,
    native_w: Optional[int] = None,
    native_h: Optional[int] = None,
) -> str:
    """Formats a resolution entry like '2560x1440 (16:9, Native)'."""
    ar = format_aspect_ratio(width, height)
    if native_w is not None and native_h is not None and width == native_w and height == native_h:
        return f"{width}x{height} ({ar}, Native)"
    return f"{width}x{height} ({ar})"


def format_monitor_label(mon: MonitorInfo) -> str:
    """Formats a monitor dropdown entry like 'Monitor 1: Primary (2560x1440, 144 Hz)'."""
    num = mon.index + 1
    clean_name = (mon.name or "").strip()
    is_generic = clean_name.lower() in _GENERIC_MONITOR_NAMES
    if mon.is_primary:
        tag = f"{clean_name} — Primary" if not is_generic else "Primary"
    else:
        tag = clean_name if not is_generic else "Secondary"
    return f"Monitor {num}: {tag} ({mon.native_width}x{mon.native_height}, {mon.hz} Hz)"


def compute_conwidth(width: int, height: int) -> int:
    """Computes aspect-matched vid_conwidth for vid_conheight=360, clamped to [480, 1280]."""
    if width <= 0 or height <= 0:
        return 640
    cw = int(math.floor(360.0 * float(width) / float(height) + 0.5))
    return max(480, min(1280, cw))


def compute_windowed_fallback(
    width: int,
    height: int,
    mon_w: int,
    mon_h: int,
) -> tuple[int, int]:
    """Computes an aspect-matched windowed size <= 85% of the monitor for clean Alt+Enter switching."""
    mon_w = max(640, int(mon_w))
    mon_h = max(480, int(mon_h))
    aspect = float(width) / float(height) if (width > 0 and height > 0) else float(mon_w) / float(mon_h)
    max_w = max(640, int(mon_w * 0.85))
    max_h = max(480, int(mon_h * 0.85))

    # Prefer a crisp standard resolution matching the aspect ratio within [60%..85%] of the monitor
    best_std = None
    for sw, sh in STANDARD_RESOLUTIONS:
        if sw > max_w or sh > max_h:
            continue
        if sw < 800 or sh < 600:
            continue
        if sw < int(mon_w * 0.55):
            continue
        if abs((float(sw) / float(sh)) - aspect) / aspect <= 0.025:
            if best_std is None or sw * sh > best_std[0] * best_std[1]:
                best_std = (sw, sh)
    if best_std is not None:
        return best_std

    # Fall back to exact aspect-matched scaled dimensions snapped to even pixels
    if float(max_w) / float(max_h) > aspect:
        win_h = max_h
        win_w = int(round(win_h * aspect))
    else:
        win_w = max_w
        win_h = int(round(win_w / aspect))

    win_w = max(640, min(mon_w, win_w - (win_w % 2)))
    win_h = max(480, min(mon_h, win_h - (win_h % 2)))
    return win_w, win_h


def _sanitize_hz(hz: float | int | None) -> int:
    try:
        val = int(round(float(hz or 0)))
    except (TypeError, ValueError):
        return 60
    if val < 30 or val > 1000:
        return 60
    return val


def _clean_device_token(device: str, fallback_idx: int) -> str:
    raw = (device or "").strip()
    if raw.startswith("\\\\.\\"):
        raw = raw[4:]
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("_")
    return cleaned or f"DISPLAY{fallback_idx + 1}"


def _finalize_monitors(raw_list: list[dict]) -> list[MonitorInfo]:
    """Sorts monitors primary-first, assigns stable IDs/indices, and filters resolutions."""
    if not raw_list:
        return []
    # Sort primary first, then left-to-right, top-to-bottom, then device name
    ordered = sorted(
        raw_list,
        key=lambda m: (
            not bool(m.get("is_primary", False)),
            int(m.get("x", 0)),
            int(m.get("y", 0)),
            str(m.get("device", "")).upper(),
        ),
    )
    if not any(m.get("is_primary") for m in ordered):
        ordered[0]["is_primary"] = True

    monitors: list[MonitorInfo] = []
    for idx, item in enumerate(ordered):
        device = str(item.get("device") or f"DISPLAY{idx + 1}")
        token = _clean_device_token(device, idx)
        mon_id = f"{token}:{idx}"
        w = max(640, int(item.get("width") or item.get("native_width") or 1920))
        h = max(480, int(item.get("height") or item.get("native_height") or 1080))
        nw = max(640, int(item.get("native_width") or w))
        nh = max(480, int(item.get("native_height") or h))
        hz = _sanitize_hz(item.get("hz", 60))
        modes = item.get("modes") or []
        resolutions = filter_resolutions(modes, nw, nh)
        name = str(item.get("name") or "").strip()
        monitors.append(
            MonitorInfo(
                id=mon_id,
                index=idx,
                name=name,
                device=device,
                is_primary=bool(item.get("is_primary", idx == 0)),
                x=int(item.get("x", 0)),
                y=int(item.get("y", 0)),
                width=w,
                height=h,
                native_width=nw,
                native_height=nh,
                hz=hz,
                resolutions=resolutions,
            )
        )
    return monitors


# ---------------------------------------------------------------------------
# Platform monitor detection (Windows / macOS / Linux + pure parsers)
# ---------------------------------------------------------------------------

def enable_windows_dpi_awareness() -> None:
    """Enables Per-Monitor V2 DPI awareness on Windows so monitor queries return real physical pixels."""
    if os.name != "nt":
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.SetProcessDpiAwarenessContext.restype = ctypes.c_bool
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = (DPI_AWARENESS_CONTEXT)-4
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except Exception:
        pass
    try:
        import ctypes
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def detect_monitors_windows() -> list[MonitorInfo]:
    """Enumerates all active Windows monitors in real physical pixels via Win32 ctypes."""
    if os.name != "nt":
        return []
    enable_windows_dpi_awareness()
    try:
        import ctypes
        import ctypes.wintypes as wt

        user32 = ctypes.windll.user32

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", wt.LONG),
                ("top", wt.LONG),
                ("right", wt.LONG),
                ("bottom", wt.LONG),
            ]

        class MONITORINFOEXW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wt.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wt.DWORD),
                ("szDevice", wt.WCHAR * 32),
            ]

        class DISPLAY_DEVICEW(ctypes.Structure):
            _fields_ = [
                ("cb", wt.DWORD),
                ("DeviceName", wt.WCHAR * 32),
                ("DeviceString", wt.WCHAR * 128),
                ("StateFlags", wt.DWORD),
                ("DeviceID", wt.WCHAR * 128),
                ("DeviceKey", wt.WCHAR * 128),
            ]

        class POINTL(ctypes.Structure):
            _fields_ = [("x", wt.LONG), ("y", wt.LONG)]

        class _DEVMODE_DISPLAY(ctypes.Structure):
            _fields_ = [
                ("dmPosition", POINTL),
                ("dmDisplayOrientation", wt.DWORD),
                ("dmDisplayFixedOutput", wt.DWORD),
            ]

        class _DEVMODE_PRINTER(ctypes.Structure):
            _fields_ = [
                ("dmOrientation", ctypes.c_short),
                ("dmPaperSize", ctypes.c_short),
                ("dmPaperLength", ctypes.c_short),
                ("dmPaperWidth", ctypes.c_short),
                ("dmScale", ctypes.c_short),
                ("dmCopies", ctypes.c_short),
                ("dmDefaultSource", ctypes.c_short),
                ("dmPrintQuality", ctypes.c_short),
            ]

        class _DEVMODE_U1(ctypes.Union):
            _fields_ = [("printer", _DEVMODE_PRINTER), ("display", _DEVMODE_DISPLAY)]

        class _DEVMODE_U2(ctypes.Union):
            _fields_ = [("dmDisplayFlags", wt.DWORD), ("dmNup", wt.DWORD)]

        class DEVMODEW(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", wt.WCHAR * 32),
                ("dmSpecVersion", wt.WORD),
                ("dmDriverVersion", wt.WORD),
                ("dmSize", wt.WORD),
                ("dmDriverExtra", wt.WORD),
                ("dmFields", wt.DWORD),
                ("u1", _DEVMODE_U1),
                ("dmColor", ctypes.c_short),
                ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short),
                ("dmFormName", wt.WCHAR * 32),
                ("dmLogPixels", wt.WORD),
                ("dmBitsPerPel", wt.DWORD),
                ("dmPelsWidth", wt.DWORD),
                ("dmPelsHeight", wt.DWORD),
                ("u2", _DEVMODE_U2),
                ("dmDisplayFrequency", wt.DWORD),
                ("dmICMMethod", wt.DWORD),
                ("dmICMIntent", wt.DWORD),
                ("dmMediaType", wt.DWORD),
                ("dmDitherType", wt.DWORD),
                ("dmReserved1", wt.DWORD),
                ("dmReserved2", wt.DWORD),
                ("dmPanningWidth", wt.DWORD),
                ("dmPanningHeight", wt.DWORD),
            ]

        hmonitors: list[int] = []
        MONENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HMONITOR, wt.HDC, ctypes.POINTER(RECT), wt.LPARAM)

        def _enum_cb(hmon, _hdc, _lprect, _lparam):
            hmonitors.append(hmon)
            return True

        cb_ref = MONENUMPROC(_enum_cb)
        user32.EnumDisplayMonitors(None, None, cb_ref, 0)

        raw_monitors: list[dict] = []
        for hmon in hmonitors:
            mi = MONITORINFOEXW()
            mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
            if not user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                continue
            dev_name = mi.szDevice
            rect_x = int(mi.rcMonitor.left)
            rect_y = int(mi.rcMonitor.top)
            rect_w = int(mi.rcMonitor.right - mi.rcMonitor.left)
            rect_h = int(mi.rcMonitor.bottom - mi.rcMonitor.top)
            is_primary = bool(mi.dwFlags & 0x1)

            friendly_name = ""
            dd = DISPLAY_DEVICEW()
            dd.cb = ctypes.sizeof(DISPLAY_DEVICEW)
            if user32.EnumDisplayDevicesW(dev_name, 0, ctypes.byref(dd), 0):
                friendly_name = (dd.DeviceString or "").strip()

            cur_w, cur_h, cur_hz = rect_w, rect_h, 60
            dm_cur = DEVMODEW()
            dm_cur.dmSize = ctypes.sizeof(DEVMODEW)
            if user32.EnumDisplaySettingsExW(dev_name, -1, ctypes.byref(dm_cur), 0):
                if dm_cur.dmPelsWidth > 0 and dm_cur.dmPelsHeight > 0:
                    cur_w = int(dm_cur.dmPelsWidth)
                    cur_h = int(dm_cur.dmPelsHeight)
                if dm_cur.dmDisplayFrequency >= 30:
                    cur_hz = int(dm_cur.dmDisplayFrequency)

            modes: list[tuple[int, int]] = []
            max_hz_at_cur = 0
            mode_idx = 0
            while mode_idx < 4096:
                dm = DEVMODEW()
                dm.dmSize = ctypes.sizeof(DEVMODEW)
                if not user32.EnumDisplaySettingsExW(dev_name, mode_idx, ctypes.byref(dm), 0):
                    break
                mode_idx += 1
                mw = int(dm.dmPelsWidth)
                mh = int(dm.dmPelsHeight)
                mhz = int(dm.dmDisplayFrequency)
                if mw > 0 and mh > 0:
                    modes.append((mw, mh))
                    if mw == cur_w and mh == cur_h and mhz > max_hz_at_cur:
                        max_hz_at_cur = mhz

            hz = cur_hz if cur_hz >= 30 else (max_hz_at_cur or 60)
            raw_monitors.append(
                {
                    "device": dev_name,
                    "name": friendly_name,
                    "is_primary": is_primary,
                    "x": rect_x,
                    "y": rect_y,
                    "width": rect_w or cur_w,
                    "height": rect_h or cur_h,
                    "native_width": cur_w or rect_w,
                    "native_height": cur_h or rect_h,
                    "hz": hz,
                    "modes": modes,
                }
            )
        return _finalize_monitors(raw_monitors)
    except Exception:
        return []


def parse_macos_system_profiler_json(raw_json: str) -> list[MonitorInfo]:
    """Parses `system_profiler SPDisplaysDataType -json` output into MonitorInfo records."""
    try:
        data = json.loads(raw_json)
    except (TypeError, ValueError):
        return []
    gpus = data.get("SPDisplaysDataType") or []
    raw_monitors: list[dict] = []
    x_cursor = 0
    for gpu in gpus:
        if not isinstance(gpu, dict):
            continue
        ndrvs = gpu.get("spdisplays_ndrvs") or []
        for idx, drv in enumerate(ndrvs):
            if not isinstance(drv, dict):
                continue
            name = str(drv.get("_name") or f"Display {len(raw_monitors) + 1}").strip()
            is_primary = str(drv.get("spdisplays_main") or "").lower() in ("spdisplays_yes", "yes", "true", "1")
            res_str = str(drv.get("_spdisplays_pixels") or drv.get("_spdisplays_resolution") or "")
            m_wh = re.search(r"(\d+)\s*[xX×]\s*(\d+)", res_str)
            if not m_wh:
                continue
            nw, nh = int(m_wh.group(1)), int(m_wh.group(2))
            hz = 60
            m_hz = re.search(r"@\s*([0-9]+(?:\.[0-9]+)?)\s*[Hh][Zz]", str(drv.get("_spdisplays_resolution") or res_str))
            if m_hz:
                hz = _sanitize_hz(float(m_hz.group(1)))
            raw_monitors.append(
                {
                    "device": f"MACDISPLAY{len(raw_monitors) + 1}",
                    "name": name,
                    "is_primary": is_primary,
                    "x": 0 if is_primary else x_cursor,
                    "y": 0,
                    "width": nw,
                    "height": nh,
                    "native_width": nw,
                    "native_height": nh,
                    "hz": hz,
                    "modes": [(nw, nh)],
                }
            )
            x_cursor += nw
    return _finalize_monitors(raw_monitors)


def detect_monitors_macos_coregraphics() -> list[MonitorInfo]:
    """Detects macOS monitors via CoreGraphics ctypes."""
    if sys.platform != "darwin":
        return []
    try:
        import ctypes

        cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")

        class CGPoint(ctypes.Structure):
            _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

        class CGSize(ctypes.Structure):
            _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]

        class CGRect(ctypes.Structure):
            _fields_ = [("origin", CGPoint), ("size", CGSize)]

        cg.CGGetActiveDisplayList.argtypes = [
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
        ]
        cg.CGGetActiveDisplayList.restype = ctypes.c_int32
        cg.CGDisplayIsMain.argtypes = [ctypes.c_uint32]
        cg.CGDisplayIsMain.restype = ctypes.c_bool
        cg.CGDisplayBounds.argtypes = [ctypes.c_uint32]
        cg.CGDisplayBounds.restype = CGRect
        cg.CGDisplayCopyDisplayMode.argtypes = [ctypes.c_uint32]
        cg.CGDisplayCopyDisplayMode.restype = ctypes.c_void_p
        cg.CGDisplayModeGetPixelWidth.argtypes = [ctypes.c_void_p]
        cg.CGDisplayModeGetPixelWidth.restype = ctypes.c_size_t
        cg.CGDisplayModeGetPixelHeight.argtypes = [ctypes.c_void_p]
        cg.CGDisplayModeGetPixelHeight.restype = ctypes.c_size_t
        cg.CGDisplayModeGetRefreshRate.argtypes = [ctypes.c_void_p]
        cg.CGDisplayModeGetRefreshRate.restype = ctypes.c_double
        cg.CGDisplayModeRelease.argtypes = [ctypes.c_void_p]
        cg.CGDisplayCopyAllDisplayModes.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        cg.CGDisplayCopyAllDisplayModes.restype = ctypes.c_void_p

        cf.CFArrayGetCount.argtypes = [ctypes.c_void_p]
        cf.CFArrayGetCount.restype = ctypes.c_long
        cf.CFArrayGetValueAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_long]
        cf.CFArrayGetValueAtIndex.restype = ctypes.c_void_p
        cf.CFRelease.argtypes = [ctypes.c_void_p]

        max_displays = 16
        arr = (ctypes.c_uint32 * max_displays)()
        count = ctypes.c_uint32(0)
        if cg.CGGetActiveDisplayList(max_displays, arr, ctypes.byref(count)) != 0 or count.value == 0:
            return []

        raw_monitors: list[dict] = []
        for i in range(int(count.value)):
            did = int(arr[i])
            is_primary = bool(cg.CGDisplayIsMain(did))
            bounds = cg.CGDisplayBounds(did)
            cur_mode = cg.CGDisplayCopyDisplayMode(did)
            nw = int(round(bounds.size.width))
            nh = int(round(bounds.size.height))
            hz = 60
            if cur_mode:
                try:
                    pw = int(cg.CGDisplayModeGetPixelWidth(cur_mode))
                    ph = int(cg.CGDisplayModeGetPixelHeight(cur_mode))
                    if pw > 0 and ph > 0:
                        nw, nh = pw, ph
                    rate = float(cg.CGDisplayModeGetRefreshRate(cur_mode))
                    if rate >= 30.0:
                        hz = _sanitize_hz(rate)
                finally:
                    cg.CGDisplayModeRelease(cur_mode)

            modes: list[tuple[int, int]] = [(nw, nh)]
            all_modes = cg.CGDisplayCopyAllDisplayModes(did, None)
            if all_modes:
                try:
                    n_modes = int(cf.CFArrayGetCount(all_modes))
                    for j in range(n_modes):
                        mptr = cf.CFArrayGetValueAtIndex(all_modes, j)
                        if not mptr:
                            continue
                        mw = int(cg.CGDisplayModeGetPixelWidth(mptr))
                        mh = int(cg.CGDisplayModeGetPixelHeight(mptr))
                        if mw > 0 and mh > 0:
                            modes.append((mw, mh))
                            if hz == 60 and mw == nw and mh == nh:
                                r = float(cg.CGDisplayModeGetRefreshRate(mptr))
                                if r >= 30.0:
                                    hz = _sanitize_hz(r)
                finally:
                    cf.CFRelease(all_modes)

            raw_monitors.append(
                {
                    "device": f"CGDISPLAY_{did}",
                    "name": "Built-in Display" if is_primary and count.value == 1 else f"Display {i + 1}",
                    "is_primary": is_primary,
                    "x": int(round(bounds.origin.x)),
                    "y": int(round(bounds.origin.y)),
                    "width": nw,
                    "height": nh,
                    "native_width": nw,
                    "native_height": nh,
                    "hz": hz,
                    "modes": modes,
                }
            )
        return _finalize_monitors(raw_monitors)
    except Exception:
        return []


def detect_monitors_macos() -> list[MonitorInfo]:
    """Detects macOS monitors via CoreGraphics with system_profiler JSON fallback."""
    mons = detect_monitors_macos_coregraphics()
    if mons:
        return mons
    try:
        res = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout:
            return parse_macos_system_profiler_json(res.stdout)
    except Exception:
        pass
    return []


def parse_xrandr_output(text: str) -> list[MonitorInfo]:
    """Parses `xrandr --query` text output into MonitorInfo records."""
    if not text:
        return []
    raw_monitors: list[dict] = []
    current: Optional[dict] = None

    conn_re = re.compile(
        r"^(\S+)\s+connected\s+(primary\s+)?(?:(\d+)x(\d+)\+(-?\d+)\+(-?\d+))?"
    )
    mode_re = re.compile(r"^\s+(\d+)x(\d+)\s+(.+)$")

    for line in text.splitlines():
        m_conn = conn_re.match(line)
        if m_conn:
            if current is not None and (current["native_width"] > 0 or current["modes"]):
                raw_monitors.append(current)
            dev = m_conn.group(1)
            is_primary = bool(m_conn.group(2))
            w = int(m_conn.group(3)) if m_conn.group(3) else 0
            h = int(m_conn.group(4)) if m_conn.group(4) else 0
            x = int(m_conn.group(5)) if m_conn.group(5) else 0
            y = int(m_conn.group(6)) if m_conn.group(6) else 0
            current = {
                "device": dev,
                "name": dev,
                "is_primary": is_primary,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "native_width": w,
                "native_height": h,
                "hz": 60,
                "modes": [],
                "_has_active_hz": False,
                "_has_pref": False,
            }
            continue

        if re.match(r"^\S+\s+(disconnected|unknown)", line):
            if current is not None and (current["native_width"] > 0 or current["modes"]):
                raw_monitors.append(current)
            current = None
            continue

        if current is not None:
            m_mode = mode_re.match(line)
            if m_mode:
                mw, mh = int(m_mode.group(1)), int(m_mode.group(2))
                rest = m_mode.group(3)
                current["modes"].append((mw, mh))
                rate_matches = re.findall(r"(\d+(?:\.\d+)?)([*+]*)", rest)
                for rate_s, flags in rate_matches:
                    rval = _sanitize_hz(float(rate_s))
                    if "*" in flags:
                        current["hz"] = rval
                        current["_has_active_hz"] = True
                        if current["width"] == 0:
                            current["width"], current["height"] = mw, mh
                        if not current["_has_pref"] and current["native_width"] == 0:
                            current["native_width"], current["native_height"] = mw, mh
                    if "+" in flags:
                        current["_has_pref"] = True
                        if current["native_width"] == 0:
                            current["native_width"], current["native_height"] = mw, mh
                        if not current["_has_active_hz"]:
                            current["hz"] = rval
                if current["native_width"] == 0:
                    current["native_width"], current["native_height"] = mw, mh
                if current["width"] == 0:
                    current["width"], current["height"] = mw, mh

    if current is not None and (current["native_width"] > 0 or current["modes"]):
        raw_monitors.append(current)

    return _finalize_monitors(raw_monitors)


def detect_monitors_linux() -> list[MonitorInfo]:
    """Detects Linux monitors via `xrandr --query`, falling back to tkinter screen metrics."""
    try:
        res = subprocess.run(["xrandr", "--query"], capture_output=True, text=True, timeout=4)
        if res.returncode == 0 and res.stdout:
            mons = parse_xrandr_output(res.stdout)
            if mons:
                return mons
    except Exception:
        pass
    return _detect_monitors_tk_fallback()


def _detect_monitors_tk_fallback() -> list[MonitorInfo]:
    try:
        if os.name != "nt" and sys.platform != "darwin" and not (
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        ):
            return []
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        try:
            sw = int(r.winfo_screenwidth())
            sh = int(r.winfo_screenheight())
        finally:
            r.destroy()
        if sw >= 640 and sh >= 480:
            return _finalize_monitors(
                [
                    {
                        "device": "DISPLAY1",
                        "name": "Primary",
                        "is_primary": True,
                        "x": 0,
                        "y": 0,
                        "width": sw,
                        "height": sh,
                        "native_width": sw,
                        "native_height": sh,
                        "hz": 60,
                        "modes": [(sw, sh)],
                    }
                ]
            )
    except Exception:
        pass
    return []


def detect_monitors() -> list[MonitorInfo]:
    """Cross-platform monitor detection; always returns at least one MonitorInfo."""
    mons: list[MonitorInfo] = []
    if os.name == "nt":
        mons = detect_monitors_windows()
    elif sys.platform == "darwin":
        mons = detect_monitors_macos()
    else:
        mons = detect_monitors_linux()

    if not mons:
        mons = _detect_monitors_tk_fallback()
    if not mons:
        mons = _finalize_monitors(
            [
                {
                    "device": "DISPLAY1",
                    "name": "Primary",
                    "is_primary": True,
                    "x": 0,
                    "y": 0,
                    "width": 1920,
                    "height": 1080,
                    "native_width": 1920,
                    "native_height": 1080,
                    "hz": 60,
                    "modes": [(1920, 1080)],
                }
            ]
        )
    return mons


# ---------------------------------------------------------------------------
# Shift key & hardware preset recommendation
# ---------------------------------------------------------------------------

def is_shift_held() -> bool:
    """Returns True if either Shift key is currently held down."""
    if os.name == "nt":
        try:
            import ctypes
            return bool(ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000)
        except Exception:
            return False
    if sys.platform == "darwin":
        try:
            import ctypes
            cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
            cg.CGEventSourceKeyState.argtypes = [ctypes.c_int32, ctypes.c_uint16]
            cg.CGEventSourceKeyState.restype = ctypes.c_bool
            # kCGEventSourceStateCombinedSessionState = 0; Left Shift = 56, Right Shift = 60
            return bool(cg.CGEventSourceKeyState(0, 56) or cg.CGEventSourceKeyState(0, 60))
        except Exception:
            return False
    return False


def get_total_ram_gb() -> Optional[float]:
    """Returns total physical system RAM in GiB using lightweight native OS APIs."""
    if os.name == "nt":
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_uint32),
                    ("dwMemoryLoad", ctypes.c_uint32),
                    ("ullTotalPhys", ctypes.c_uint64),
                    ("ullAvailPhys", ctypes.c_uint64),
                    ("ullTotalPageFile", ctypes.c_uint64),
                    ("ullAvailPageFile", ctypes.c_uint64),
                    ("ullTotalVirtual", ctypes.c_uint64),
                    ("ullAvailVirtual", ctypes.c_uint64),
                    ("ullAvailExtendedVirtual", ctypes.c_uint64),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return float(stat.ullTotalPhys) / float(1024 ** 3)
        except Exception:
            return None
    elif sys.platform == "darwin":
        try:
            res = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return float(int(res.stdout.strip())) / float(1024 ** 3)
        except Exception:
            return None
    else:
        try:
            for line in Path("/proc/meminfo").read_text("utf-8", errors="ignore").splitlines():
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return float(int(parts[1])) / float(1024 ** 2)
        except OSError:
            return None
    return None


def _classify_gpu_name(name: str, vram_mb: int) -> str:
    low = (name or "").strip()
    if re.search(
        r"Parsec|Virtual|Indirect|Basic Display|Remote|RDP|Citrix|Meta |Oculus|"
        r"Spacedesk|Immersed|LuminonCore|IDD|VDD|Hyper-V|VMware|VirtualBox|QXL|Microsoft Basic",
        low,
        re.IGNORECASE,
    ):
        return "VIRTUAL"
    if re.search(r"Intel", low, re.IGNORECASE) and not re.search(r"Arc\s+(?:A|B|Pro)\d", low, re.IGNORECASE):
        return "iGPU"
    if re.search(r"Radeon", low, re.IGNORECASE) and (
        re.match(r"^AMD Radeon(?:\(TM\))? Graphics$", low, re.IGNORECASE)
        or re.search(r"Radeon.*(?:Vega\s+[0-9]|6[0-9]0M|7[0-9]0M|8[0-9]0M)", low, re.IGNORECASE)
        or (0 < vram_mb <= 2048 and not re.search(r"RX\s+\d|Pro\s+W|FirePro", low, re.IGNORECASE))
    ):
        return "iGPU"
    if re.search(r"Integrated|APU", low, re.IGNORECASE):
        return "iGPU"
    return "dGPU"


def detect_gpu_windows() -> tuple[Optional[int], bool]:
    """Fast (<5ms) Windows VRAM/iGPU check via cached preflight file and Display Class registry."""
    if os.name != "nt":
        return None, False

    # 1. Check Windows display adapter registry (64-bit qwMemorySize, zero subprocess cost)
    try:
        import winreg

        base_path = r"SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        dgpu_vrams: list[int] = []
        igpu_vrams: list[int] = []
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path) as base_key:
            idx = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(base_key, idx)
                except OSError:
                    break
                idx += 1
                if not re.match(r"^\d{4}$", sub_name):
                    continue
                try:
                    with winreg.OpenKey(base_key, sub_name) as sub_key:
                        try:
                            desc, _ = winreg.QueryValueEx(sub_key, "DriverDesc")
                        except OSError:
                            continue
                        vram_bytes = 0
                        for val_name in ("HardwareInformation.qwMemorySize", "HardwareInformation.MemorySize"):
                            try:
                                raw_val, _ = winreg.QueryValueEx(sub_key, val_name)
                                if isinstance(raw_val, int) and raw_val > 0:
                                    vram_bytes = raw_val
                                    break
                                if isinstance(raw_val, (bytes, bytearray)):
                                    if len(raw_val) >= 8:
                                        vram_bytes = int.from_bytes(raw_val[:8], "little")
                                        break
                                    if len(raw_val) >= 4:
                                        vram_bytes = int.from_bytes(raw_val[:4], "little")
                                        break
                            except OSError:
                                pass
                        vram_mb = int(round(vram_bytes / (1024 * 1024))) if vram_bytes > 0 else 0
                        kind = _classify_gpu_name(str(desc), vram_mb)
                        if kind == "dGPU":
                            dgpu_vrams.append(vram_mb)
                        elif kind == "iGPU":
                            igpu_vrams.append(vram_mb)
                except OSError:
                    continue
        if dgpu_vrams:
            best = max(dgpu_vrams)
            return (best if best > 0 else None), False
        if igpu_vrams:
            best = max(igpu_vrams)
            return (best if best > 0 else None), True
    except Exception:
        pass

    # 2. Fallback to cached %LOCALAPPDATA%\BAKOQUAKE\vram-mb.txt
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        vram_file = Path(local_app) / "BAKOQUAKE" / "vram-mb.txt"
        try:
            raw = vram_file.read_text("utf-8").strip()
            if raw.isdigit() and int(raw) > 0:
                vram_mb = int(raw)
                return vram_mb, (vram_mb < 3000)
        except OSError:
            pass
    return None, False


def detect_hardware_info() -> dict:
    """Returns lightweight hardware summary: total_ram_gb, vram_mb, is_igpu."""
    total_ram_gb = get_total_ram_gb()
    vram_mb, is_igpu = detect_gpu_windows() if os.name == "nt" else (None, False)
    return {
        "total_ram_gb": total_ram_gb,
        "vram_mb": vram_mb,
        "is_igpu": is_igpu,
    }


def recommend_preset(
    total_ram_gb: Optional[float] = None,
    vram_mb: Optional[int] = None,
    is_igpu: bool = False,
) -> str:
    """Recommends 'simple' on <=8 GB RAM or <3000 MB VRAM / iGPU, otherwise 'normal'."""
    if total_ram_gb is not None and total_ram_gb <= 8.2:
        return "simple"
    if is_igpu:
        return "simple"
    if vram_mb is not None and 0 < int(vram_mb) < 3000:
        return "simple"
    return "normal"


# ---------------------------------------------------------------------------
# Persistence & auto-reopen logic
# ---------------------------------------------------------------------------

def config_requests_launcher(config_cfg_path: Path) -> bool:
    """Returns True if config.cfg sets `bm_show_launcher` to '1' (or non-zero)."""
    try:
        text = Path(config_cfg_path).read_text("utf-8", errors="ignore")
    except OSError:
        return False

    result = False
    pat = re.compile(r'^\s*(?:seta?\s+)?bm_show_launcher\s+"?([^"\s;]+)"?', re.IGNORECASE)
    for line in text.splitlines():
        stripped = line.split("//", 1)[0].strip()
        if not stripped:
            continue
        m = pat.match(stripped)
        if m:
            val = m.group(1).strip()
            try:
                result = float(val) != 0.0
            except ValueError:
                result = val.lower() in ("true", "on", "yes")
    return result


def load_prefs(prefs_path: Path) -> Optional[dict]:
    try:
        data = json.loads(Path(prefs_path).read_text("utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def save_prefs(prefs_path: Path, selection: PickerSelection) -> None:
    prefs_path = Path(prefs_path)
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "remember": bool(selection.remember),
        "monitor_id": selection.monitor.id,
        "monitor_name": selection.monitor.name,
        "monitor_native": [selection.monitor.native_width, selection.monitor.native_height],
        "mode": selection.mode,
        "width": int(selection.width),
        "height": int(selection.height),
        "preset": selection.preset,
    }
    tmp = prefs_path.with_suffix(prefs_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, prefs_path)


def _match_saved_monitor(monitors: list[MonitorInfo], prefs: dict) -> Optional[MonitorInfo]:
    saved_id = prefs.get("monitor_id")
    if not saved_id:
        return None
    for mon in monitors:
        if mon.id == saved_id:
            return mon
    return None


def resolve_initial_selection(
    monitors: list[MonitorInfo],
    prefs: Optional[dict],
    default_preset: str,
) -> tuple[PickerSelection, bool]:
    """Builds the initial PickerSelection and reports whether saved monitor/res fully matched."""
    primary = next((m for m in monitors if m.is_primary), monitors[0])
    if not isinstance(prefs, dict):
        return (
            PickerSelection(
                monitor=primary,
                mode="borderless",
                width=primary.native_width,
                height=primary.native_height,
                preset=default_preset if default_preset in VALID_PRESETS else "normal",
                remember=False,
            ),
            False,
        )

    mon = _match_saved_monitor(monitors, prefs)
    mon_exact = mon is not None
    if mon is None:
        mon = primary

    # Verify saved native size still matches monitor (detects monitor swaps or resolution changes)
    saved_native = prefs.get("monitor_native")
    if (
        mon_exact
        and isinstance(saved_native, list)
        and len(saved_native) == 2
        and (int(saved_native[0]), int(saved_native[1])) != (mon.native_width, mon.native_height)
    ):
        mon_exact = False

    mode = str(prefs.get("mode") or "borderless").lower()
    mode_valid = mode in VALID_MODES
    if not mode_valid:
        mode = "borderless"

    preset = str(prefs.get("preset") or default_preset).lower()
    preset_valid = preset in VALID_PRESETS
    if not preset_valid:
        preset = default_preset if default_preset in VALID_PRESETS else "normal"

    res_valid = False
    try:
        sw = int(prefs.get("width", 0))
        sh = int(prefs.get("height", 0))
        if (sw, sh) in mon.resolutions and sw <= mon.native_width and sh <= mon.native_height:
            width, height = sw, sh
            res_valid = True
        else:
            width, height = mon.native_width, mon.native_height
    except (TypeError, ValueError):
        width, height = mon.native_width, mon.native_height

    fully_valid = mon_exact and mode_valid and preset_valid and res_valid
    return (
        PickerSelection(
            monitor=mon,
            mode=mode,
            width=width,
            height=height,
            preset=preset,
            remember=bool(prefs.get("remember", False)),
        ),
        fully_valid,
    )


def should_skip_gui(
    prefs: Optional[dict],
    monitors: list[MonitorInfo],
    config_cfg_path: Path,
    *,
    setup: bool = False,
    env: Optional[dict[str, str]] = None,
    shift_held: bool = False,
    default_preset: str = "normal",
) -> tuple[bool, PickerSelection]:
    """Decides whether to skip the GUI and immediately apply remembered settings.

    Returns (skip_gui, selection).
    """
    selection, fully_valid = resolve_initial_selection(monitors, prefs, default_preset)
    active_env = os.environ if env is None else env
    if setup:
        return False, selection
    if active_env.get("BQ_SETUP") == "1":
        return False, selection
    if shift_held:
        return False, selection
    if config_requests_launcher(config_cfg_path):
        return False, selection
    if not isinstance(prefs, dict) or prefs.get("remember") is not True:
        return False, selection
    if not fully_valid:
        return False, selection
    return True, selection


# ---------------------------------------------------------------------------
# Video config (bq_launch_video.cfg) and --out-env generation
# ---------------------------------------------------------------------------

def _preset_cvars(preset: str) -> list[tuple[str, str]]:
    """Returns exact ordered preset cvars matching menu_options.qc."""
    p = preset.lower()
    if p == "simple":
        return [
            ("seta lowspec", "1"),
            ("r_bloom", "0"),
            ("r_shadow_realtime_dlight", "0"),
            ("r_shadow_realtime_dlight_shadows", "0"),
            ("r_shadow_gloss", "0"),
            ("r_shadow_glossexact", "0"),
            ("r_shadow_shadowmapping", "0"),
            ("r_shadow_usenormalmap", "0"),
            ("r_load_normalmap", "0"),
            ("r_load_gloss", "0"),
            ("r_glsl_offsetmapping", "0"),
            ("r_glsl_offsetmapping_reliefmapping", "0"),
            ("r_glsl_deluxemapping", "0"),
            ("r_water", "0"),
            ("r_coronas", "0"),
            ("r_glsl_saturation", "1"),
            ("cl_particles_quality", "0.5"),
            ("cl_decals", "1"),
            ("cl_decals_max", "128"),
            ("cl_decals_time", "12"),
            ("cl_decals_fadetime", "4"),
            ("cl_decals_models", "0"),
            ("cl_stainmaps", "0"),
            ("vid_samples", "1"),
            ("gl_texture_anisotropy", "4"),
            ("gl_texturemode", '"GL_LINEAR_MIPMAP_LINEAR"'),
            ("r_minlight", "3"),
            ("gl_overbright_models", "0"),
            ("r_lerpmodels", "1"),
            ("r_lerplightstyles", "1"),
            ("r_lerpsprites", "0"),
            ("v_glslgamma_2d", "1"),
        ]

    # Normal baseline (also extended by High)
    normal: list[tuple[str, str]] = [
        ("seta lowspec", "0"),
        ("r_bloom", "1"),
        ("r_bloom_blur", "0.1"),
        ("r_bloom_brighten", "0.1"),
        ("r_shadow_realtime_dlight", "1"),
        ("r_shadow_realtime_dlight_shadows", "1"),
        ("r_shadow_gloss", "1"),
        ("r_shadow_glossexact", "0"),
        ("r_shadow_shadowmapping", "0"),
        ("r_shadow_usenormalmap", "1"),
        ("r_load_normalmap", "1"),
        ("r_load_gloss", "1"),
        ("r_glsl_offsetmapping", "1"),
        ("r_glsl_offsetmapping_reliefmapping", "0"),
        ("r_glsl_deluxemapping", "1"),
        ("r_water", "0"),
        ("r_coronas", "0.6"),
        ("r_glsl_saturation", "1"),
        ("cl_particles_quality", "1"),
        ("cl_decals", "1"),
        ("cl_decals_max", "256"),
        ("cl_decals_time", "16"),
        ("cl_decals_fadetime", "4"),
        ("cl_decals_models", "0"),
        ("cl_stainmaps", "0"),
        ("vid_samples", "4"),
        ("gl_texture_anisotropy", "16"),
        ("gl_texturemode", '"GL_LINEAR_MIPMAP_LINEAR"'),
        ("r_minlight", "3"),
        ("gl_overbright_models", "0"),
        ("r_lerpmodels", "1"),
        ("r_lerplightstyles", "1"),
        ("r_lerpsprites", "0"),
        ("v_glslgamma_2d", "1"),
        ("r_shadow_shadowmapping_texturesize", "4096"),
    ]
    if p != "high":
        return normal

    # High overrides / additions on top of Normal (deduplicated cleanly in order)
    high_overrides = {
        "r_glsl_offsetmapping_reliefmapping": "1",
        "r_glsl_offsetmapping_scale": "0.04",
        "r_shadow_shadowmapping": "1",
        "r_shadow_shadowmapping_maxsize": "1024",
        "r_shadow_glossexact": "1",
        "r_water": "1",
        "r_water_lowquality": "0",
        "r_water_resolutionmultiplier": "0.75",
        "r_wateralpha": "0.5",
        "r_glsl_saturation": "1.1",
    }
    merged: list[tuple[str, str]] = []
    seen: set[str] = set()
    for k, v in normal:
        merged.append((k, high_overrides.get(k, v)))
        seen.add(k)
    for k, v in high_overrides.items():
        if k not in seen:
            merged.append((k, v))
    return merged


def build_video_cfg(selection: PickerSelection) -> str:
    """Generates bq_launch_video.cfg contents for the chosen display mode, resolution, and preset."""
    mon = selection.monitor
    w = int(selection.width)
    h = int(selection.height)
    mon_w = int(mon.width or mon.native_width)
    mon_h = int(mon.height or mon.native_height)
    hz = _sanitize_hz(mon.hz)
    con_w = compute_conwidth(w, h)
    win_w, win_h = compute_windowed_fallback(w, h, mon_w, mon_h)
    maxfps = max(250, hz)
    mode = selection.mode if selection.mode in VALID_MODES else "borderless"
    preset = selection.preset if selection.preset in VALID_PRESETS else "normal"

    lines = [
        "// Auto-generated by BAKOQUAKE Display & Graphics Setup (bq_display.py)",
        f"// Monitor: {mon.id} ({mon.native_width}x{mon.native_height} @ {hz} Hz, primary={int(mon.is_primary)})",
        f"// Mode: {mode} | Resolution: {w}x{h} | Preset: {preset}",
        "",
        "// ---- Display mode & Alt+Enter-safe resolution cvars ----",
    ]

    if mode == "borderless":
        if mon.is_primary and w == mon_w and h == mon_h:
            lines += [
                "vid_fullscreen 1",
                "vid_desktopfullscreen 1",
                "vid_borderless 0",
            ]
        else:
            # Secondary monitor or non-native borderless: use borderless window placed by watchdog
            lines += [
                "vid_fullscreen 0",
                "vid_desktopfullscreen 0",
                "vid_borderless 1",
            ]
        lines += [
            f"vid_width {w}",
            f"vid_height {h}",
            f"_vid_fullscreen_width {w}",
            f"_vid_fullscreen_height {h}",
            f"_vid_window_width {win_w}",
            f"_vid_window_height {win_h}",
        ]
    elif mode == "fullscreen":
        lines += [
            "vid_fullscreen 1",
            "vid_desktopfullscreen 0",
            "vid_borderless 0",
            f"vid_width {w}",
            f"vid_height {h}",
            f"_vid_fullscreen_width {w}",
            f"_vid_fullscreen_height {h}",
            f"_vid_window_width {win_w}",
            f"_vid_window_height {win_h}",
        ]
    else:  # windowed
        lines += [
            "vid_fullscreen 0",
            "vid_desktopfullscreen 0",
            "vid_borderless 0",
            f"vid_width {w}",
            f"vid_height {h}",
            f"_vid_window_width {w}",
            f"_vid_window_height {h}",
            f"_vid_fullscreen_width {mon_w}",
            f"_vid_fullscreen_height {mon_h}",
        ]

    lines += [
        f"vid_conwidth {con_w}",
        "vid_conheight 360",
        "",
        "// ---- Refresh rate & frame cap ----",
        f"vid_refreshrate {hz}",
        "vid_userefreshrate 1",
        f"cl_maxfps {maxfps}",
        "",
        "// ---- Clear one-shot menu reopen flag ----",
        'seta bm_show_launcher "0"',
        "",
        "// ---- Reset texture & engine load optimizations ----",
        "gl_picmip 0",
        "gl_picmip_world 0",
        "gl_picmip_other 0",
        "gl_picmip_sprites 0",
        "gl_picmip_force 0",
        "gl_max_size 2048",
        "gl_texturecompression 0",
        "r_dynamic 1",
        "menu_background 1",
        "mod_bsp_portalize 0",
        "mod_freebeforeload 1",
        "mod_q1bsp_pvs_ondemand 1",
        "mod_q1bsp_lazy_render_bih 1",
        "",
        f"// ---- Graphics preset: {preset} ----",
    ]
    for k, v in _preset_cvars(preset):
        lines.append(f"{k} {v}")
    lines.append("")
    return "\n".join(lines)


def write_video_cfg(cfg_path: Path, selection: PickerSelection) -> None:
    cfg_path = Path(cfg_path)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cfg_path.with_suffix(cfg_path.suffix + ".tmp")
    tmp.write_text(build_video_cfg(selection), encoding="utf-8", newline="\n")
    os.replace(tmp, cfg_path)


def format_env_output(
    selection: Optional[PickerSelection],
    cancelled: bool,
    env_format: str = "cmd",
) -> str:
    """Formats BQ_PICK_* environment assignments in 'cmd' or 'sh' syntax."""
    if cancelled or selection is None:
        pairs = [
            ("BQ_PICK_CANCEL", "1"),
            ("BQ_PICK_PRESET", ""),
            ("BQ_PICK_MODE", ""),
            ("BQ_PICK_WIDTH", ""),
            ("BQ_PICK_HEIGHT", ""),
            ("BQ_PICK_HZ", ""),
            ("BQ_PICK_MON_X", ""),
            ("BQ_PICK_MON_Y", ""),
            ("BQ_PICK_MON_W", ""),
            ("BQ_PICK_MON_H", ""),
            ("BQ_PICK_MON_PRIMARY", ""),
            ("BQ_PICK_CFG", ""),
        ]
    else:
        mon = selection.monitor
        pairs = [
            ("BQ_PICK_CANCEL", "0"),
            ("BQ_PICK_PRESET", selection.preset),
            ("BQ_PICK_MODE", selection.mode),
            ("BQ_PICK_WIDTH", str(int(selection.width))),
            ("BQ_PICK_HEIGHT", str(int(selection.height))),
            ("BQ_PICK_HZ", str(_sanitize_hz(mon.hz))),
            ("BQ_PICK_MON_X", str(int(mon.x))),
            ("BQ_PICK_MON_Y", str(int(mon.y))),
            ("BQ_PICK_MON_W", str(int(mon.width or mon.native_width))),
            ("BQ_PICK_MON_H", str(int(mon.height or mon.native_height))),
            ("BQ_PICK_MON_PRIMARY", "1" if mon.is_primary else "0"),
            ("BQ_PICK_CFG", VIDEO_CFG_FILENAME),
        ]

    if env_format == "sh":
        out_lines = []
        for k, v in pairs:
            safe_v = str(v).replace("'", "'\"'\"'")
            out_lines.append(f"{k}='{safe_v}'")
        return "\n".join(out_lines) + "\n"

    # Windows cmd format
    out_lines = []
    for k, v in pairs:
        safe_v = re.sub(r'["\r\n&|<>^%]', "", str(v))
        out_lines.append(f'set "{k}={safe_v}"')
    return "\r\n".join(out_lines) + "\r\n"


def write_env_file(
    out_env_path: Path,
    selection: Optional[PickerSelection],
    cancelled: bool,
    env_format: str = "cmd",
) -> None:
    out_env_path = Path(out_env_path)
    out_env_path.parent.mkdir(parents=True, exist_ok=True)
    content = format_env_output(selection, cancelled, env_format=env_format)
    with open(out_env_path, "wb") as f:
        f.write(content.encode("utf-8"))


# ---------------------------------------------------------------------------
# Dark-theme Tkinter Picker UI
# ---------------------------------------------------------------------------

def _load_window_icon(root, pkg_root: Optional[Path]) -> None:
    """Loads the BAKOQUAKE icon from package tools/ or repo source/icons/."""
    candidates: list[Path] = []
    if pkg_root is not None:
        pr = Path(pkg_root)
        candidates += [
            pr / "tools",
            pr / "source" / "icons",
            pr / "BakersfieldQuake" / "source" / "icons",
        ]
    here = Path(__file__).resolve().parent
    candidates += [here, here.parent / "source" / "icons"]

    try:
        if os.name == "nt":
            for folder in candidates:
                for name in ("bakoquake.ico", "bakoquake-update.ico"):
                    ico = folder / name
                    if ico.is_file():
                        root.iconbitmap(str(ico))
                        return
        for folder in candidates:
            for name in ("bakoquake-256.png", "bakoquake-update-256.png"):
                png = folder / name
                if png.is_file():
                    img = root.tk.call("image", "create", "photo", "-file", str(png))
                    root.iconphoto(True, img)
                    root._bq_icon_ref = img  # prevent GC
                    return
    except Exception:
        pass


def show_picker_gui(
    monitors: list[MonitorInfo],
    initial: PickerSelection,
    recommended_preset: str,
    pkg_root: Optional[Path] = None,
    _on_ready: Optional[Callable] = None,
) -> Optional[PickerSelection]:
    """Displays the dark charcoal/gold Display & Graphics Picker.

    Returns PickerSelection if the user clicks Play BAKOQUAKE, or None if cancelled.
    """
    if os.name != "nt" and sys.platform != "darwin" and not (
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    ):
        raise RuntimeError("No display server available for Tkinter UI")

    enable_windows_dpi_awareness()
    import tkinter as tk
    from tkinter import ttk

    BG = THEME["BG"]
    CARD = THEME["CARD"]
    SUNKEN = THEME["SUNKEN"]
    BORDER = THEME["BORDER"]
    FG = THEME["FG"]
    MUTED = THEME["MUTED"]
    ACCENT = THEME["ACCENT"]
    ACCENT_HOVER = THEME["ACCENT_HOVER"]
    ACCENT_TEXT = THEME["ACCENT_TEXT"]
    BTN_SEC = THEME["BTN_SEC"]
    BTN_SEC_HOVER = THEME["BTN_SEC_HOVER"]
    GREEN = THEME["GREEN"]

    ui_font = "Segoe UI" if os.name == "nt" else ("SF Pro Text" if sys.platform == "darwin" else "DejaVu Sans")

    root = tk.Tk()
    root.title("BAKOQUAKE — Display & Graphics Setup")
    root.configure(bg=BG)
    root.resizable(False, False)
    _load_window_icon(root, pkg_root)

    # Dark combobox popup menu styling
    root.option_add("*TCombobox*Listbox.background", SUNKEN)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", ACCENT_TEXT)
    root.option_add("*TCombobox*Listbox.font", (ui_font, 10))

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "BQ.TCombobox",
        fieldbackground=SUNKEN,
        background=BTN_SEC,
        foreground=FG,
        arrowcolor=ACCENT,
        bordercolor=BORDER,
        darkcolor=BORDER,
        lightcolor=BORDER,
        selectbackground=SUNKEN,
        selectforeground=FG,
        padding=(10, 6),
    )
    style.map(
        "BQ.TCombobox",
        fieldbackground=[("readonly", SUNKEN), ("focus", SUNKEN)],
        foreground=[("readonly", FG), ("focus", FG)],
        background=[("readonly", BTN_SEC), ("active", BTN_SEC_HOVER)],
        bordercolor=[("focus", ACCENT), ("!focus", BORDER)],
    )

    state: dict = {
        "result": None,
        "mon_idx": max(0, next((i for i, m in enumerate(monitors) if m.id == initial.monitor.id), 0)),
        "mode": initial.mode if initial.mode in VALID_MODES else "borderless",
        "preset": initial.preset if initial.preset in VALID_PRESETS else recommended_preset,
        "res_list": [],
    }

    outer = tk.Frame(root, bg=BG, padx=22, pady=20)
    outer.pack(fill="both", expand=True)

    card = tk.Frame(
        outer,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1,
        padx=24,
        pady=20,
    )
    card.pack(fill="both", expand=True)

    # ---- Header ----
    header_row = tk.Frame(card, bg=CARD)
    header_row.pack(fill="x", anchor="w")
    tk.Label(
        header_row,
        text="PRE-LAUNCH SETUP",
        bg=CARD,
        fg=ACCENT,
        font=(ui_font, 8, "bold"),
    ).pack(anchor="w")
    tk.Label(
        header_row,
        text="BAKOQUAKE — Display & Graphics Setup",
        bg=CARD,
        fg=FG,
        font=(ui_font, 14, "bold"),
    ).pack(anchor="w", pady=(2, 0))

    # Compact detected-hardware subtitle (always shown when 1 monitor; subtle info otherwise)
    mon_sub_var = tk.StringVar()
    lbl_subtitle = tk.Label(
        card,
        textvariable=mon_sub_var,
        bg=CARD,
        fg=MUTED,
        font=(ui_font, 9),
    )
    lbl_subtitle.pack(anchor="w", pady=(3, 12))

    # Divider
    tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(0, 14))

    def section_label(parent, text):
        lbl = tk.Label(
            parent,
            text=text,
            bg=CARD,
            fg=MUTED,
            font=(ui_font, 9, "bold"),
        )
        lbl.pack(anchor="w", pady=(0, 5))
        return lbl

    # ---- Monitor dropdown (only when 2+ monitors) ----
    mon_var = tk.StringVar()
    mon_combo = None
    if len(monitors) >= 2:
        section_label(card, "MONITOR")
        mon_labels = [format_monitor_label(m) for m in monitors]
        mon_var.set(mon_labels[state["mon_idx"]])
        mon_combo = ttk.Combobox(
            card,
            textvariable=mon_var,
            values=mon_labels,
            state="readonly",
            style="BQ.TCombobox",
            font=(ui_font, 10),
        )
        mon_combo.pack(fill="x", pady=(0, 14))

    # ---- Display Mode segmented selector ----
    section_label(card, "DISPLAY MODE")
    mode_row = tk.Frame(card, bg=CARD)
    mode_row.pack(fill="x", pady=(0, 14))
    mode_buttons: dict[str, tk.Button] = {}

    def refresh_mode_buttons():
        cur = state["mode"]
        for key, btn in mode_buttons.items():
            if key == cur:
                btn.config(
                    bg=ACCENT,
                    fg=ACCENT_TEXT,
                    activebackground=ACCENT_HOVER,
                    activeforeground=ACCENT_TEXT,
                    font=(ui_font, 9, "bold"),
                )
            else:
                btn.config(
                    bg=BTN_SEC,
                    fg=FG,
                    activebackground=BTN_SEC_HOVER,
                    activeforeground=FG,
                    font=(ui_font, 9, "normal"),
                )

    def select_mode(key):
        state["mode"] = key
        refresh_mode_buttons()

    for idx, (m_key, m_label) in enumerate(DISPLAY_MODES):
        btn = tk.Button(
            mode_row,
            text=m_label,
            command=lambda k=m_key: select_mode(k),
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
        )
        pad_r = 0 if idx == len(DISPLAY_MODES) - 1 else 8
        btn.pack(side="left", fill="x", expand=True, padx=(0, pad_r))
        mode_buttons[m_key] = btn
    refresh_mode_buttons()

    # ---- Resolution dropdown ----
    section_label(card, "RESOLUTION")
    res_var = tk.StringVar()
    res_combo = ttk.Combobox(
        card,
        textvariable=res_var,
        state="readonly",
        style="BQ.TCombobox",
        font=(ui_font, 10),
    )
    res_combo.pack(fill="x", pady=(0, 10))

    # ---- Refresh Rate read-only hardware badge ----
    hz_frame = tk.Frame(
        card,
        bg=SUNKEN,
        highlightbackground=BORDER,
        highlightthickness=1,
        padx=12,
        pady=7,
    )
    hz_frame.pack(fill="x", pady=(0, 16))
    tk.Label(
        hz_frame,
        text="●",
        bg=SUNKEN,
        fg=GREEN,
        font=(ui_font, 9, "bold"),
    ).pack(side="left", padx=(0, 7))
    hz_var = tk.StringVar()
    tk.Label(
        hz_frame,
        textvariable=hz_var,
        bg=SUNKEN,
        fg=FG,
        font=(ui_font, 9),
    ).pack(side="left")

    # ---- Graphics Preset segmented selector ----
    preset_hdr = tk.Frame(card, bg=CARD)
    preset_hdr.pack(fill="x", pady=(0, 5))
    tk.Label(
        preset_hdr,
        text="GRAPHICS PRESET",
        bg=CARD,
        fg=MUTED,
        font=(ui_font, 9, "bold"),
    ).pack(side="left")
    rec_name = recommended_preset.capitalize()
    tk.Label(
        preset_hdr,
        text=f"Recommended for this PC: {rec_name}",
        bg=CARD,
        fg=ACCENT,
        font=(ui_font, 8),
    ).pack(side="right")

    preset_row = tk.Frame(card, bg=CARD)
    preset_row.pack(fill="x", pady=(0, 8))
    preset_buttons: dict[str, tk.Button] = {}
    preset_desc_var = tk.StringVar()

    def refresh_preset_buttons():
        cur = state["preset"]
        for key, btn in preset_buttons.items():
            if key == cur:
                btn.config(
                    bg=ACCENT,
                    fg=ACCENT_TEXT,
                    activebackground=ACCENT_HOVER,
                    activeforeground=ACCENT_TEXT,
                    font=(ui_font, 9, "bold"),
                )
            else:
                btn.config(
                    bg=BTN_SEC,
                    fg=FG,
                    activebackground=BTN_SEC_HOVER,
                    activeforeground=FG,
                    font=(ui_font, 9, "normal"),
                )
        preset_desc_var.set(PRESET_DESC.get(cur, ""))

    def select_preset(key):
        state["preset"] = key
        refresh_preset_buttons()

    for idx, (p_key, p_label, _desc) in enumerate(GRAPHICS_PRESETS):
        btn = tk.Button(
            preset_row,
            text=p_label,
            command=lambda k=p_key: select_preset(k),
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
        )
        pad_r = 0 if idx == len(GRAPHICS_PRESETS) - 1 else 8
        btn.pack(side="left", fill="x", expand=True, padx=(0, pad_r))
        preset_buttons[p_key] = btn

    tk.Label(
        card,
        textvariable=preset_desc_var,
        bg=CARD,
        fg=MUTED,
        wraplength=470,
        justify="left",
        anchor="w",
        font=(ui_font, 9),
    ).pack(fill="x", anchor="w", pady=(0, 14))
    refresh_preset_buttons()

    # ---- Remember checkbox ----
    remember_var = tk.BooleanVar(value=bool(initial.remember))
    chk = tk.Checkbutton(
        card,
        text="Remember my settings (hold Shift or use Options to change later)",
        variable=remember_var,
        bg=CARD,
        fg=FG,
        activebackground=CARD,
        activeforeground=FG,
        selectcolor=SUNKEN,
        highlightthickness=0,
        bd=0,
        font=(ui_font, 9),
        cursor="hand2",
    )
    chk.pack(anchor="w", pady=(0, 16))

    # ---- Populate monitor-dependent controls ----
    def update_for_monitor(mon_idx: int, prefer_res: Optional[tuple[int, int]] = None):
        state["mon_idx"] = mon_idx
        mon = monitors[mon_idx]
        state["res_list"] = list(mon.resolutions)
        labels = [format_resolution_label(w, h, mon.native_width, mon.native_height) for w, h in state["res_list"]]
        res_combo["values"] = labels

        target = prefer_res if (prefer_res in state["res_list"]) else (mon.native_width, mon.native_height)
        try:
            r_idx = state["res_list"].index(target)
        except ValueError:
            r_idx = 0
        res_var.set(labels[r_idx])
        hz_var.set(f"{mon.hz} Hz detected — applied automatically")

        if len(monitors) == 1:
            clean_name = (mon.name or "").strip()
            disp = clean_name if clean_name.lower() not in _GENERIC_MONITOR_NAMES else "Primary Display"
            mon_sub_var.set(f"Detected: {disp} ({mon.native_width}x{mon.native_height}, {mon.hz} Hz)")
        else:
            mon_sub_var.set(f"{len(monitors)} displays detected — select your monitor, resolution, and graphics preset")

    if mon_combo is not None:
        def _on_mon_changed(_event=None):
            idx = mon_combo.current()
            if 0 <= idx < len(monitors):
                update_for_monitor(idx, prefer_res=None)
        mon_combo.bind("<<ComboboxSelected>>", _on_mon_changed)

    update_for_monitor(state["mon_idx"], prefer_res=(initial.width, initial.height))

    # ---- Action buttons ----
    tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(0, 14))
    btn_row = tk.Frame(card, bg=CARD)
    btn_row.pack(fill="x")

    def on_play(_event=None):
        mon = monitors[state["mon_idx"]]
        r_idx = res_combo.current()
        if 0 <= r_idx < len(state["res_list"]):
            w, h = state["res_list"][r_idx]
        else:
            w, h = mon.native_width, mon.native_height
        state["result"] = PickerSelection(
            monitor=mon,
            mode=state["mode"],
            width=w,
            height=h,
            preset=state["preset"],
            remember=bool(remember_var.get()),
        )
        root.destroy()

    def on_cancel(_event=None):
        state["result"] = None
        root.destroy()

    def make_button(parent, text, cmd, primary=False):
        bg = ACCENT if primary else BTN_SEC
        fg = ACCENT_TEXT if primary else FG
        hv = ACCENT_HOVER if primary else BTN_SEC_HOVER
        btn = tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=bg,
            fg=fg,
            activebackground=hv,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=20,
            pady=9,
            font=(ui_font, 10, "bold" if primary else "normal"),
            cursor="hand2",
        )
        btn.bind("<Enter>", lambda _e: btn.config(bg=hv))
        btn.bind("<Leave>", lambda _e: btn.config(bg=bg))
        return btn

    btn_cancel = make_button(btn_row, "Cancel", on_cancel, primary=False)
    btn_cancel.pack(side="right")
    btn_play = make_button(btn_row, "Play BAKOQUAKE", on_play, primary=True)
    btn_play.pack(side="right", padx=(0, 10))

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.bind("<Return>", on_play)
    root.bind("<Escape>", on_cancel)

    # Auto-fit window cleanly to content and center on primary monitor
    root.update_idletasks()
    if os.name == "nt":
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
            val = ctypes.c_int(1)
            # DWMWA_USE_IMMERSIVE_DARK_MODE (20 on Win10 2004+/Win11, 19 on older Win10)
            for attr in (20, 19):
                if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)) == 0:
                    break
        except Exception:
            pass
    win_w = max(540, root.winfo_reqwidth())
    win_h = root.winfo_reqheight()
    primary_mon = next((m for m in monitors if m.is_primary), monitors[0])
    scr_w, scr_h = primary_mon.width, primary_mon.height
    if sys.platform == "darwin":
        # macOS monitors are measured in pixels (5120x2880 on a 5K Retina) but Tk places windows in points
        # (2560x1440); centering in pixels put the window bottom-right, half off screen. Tk's screen size is the
        # main display in points, and the main display sits at 0,0.
        scr_w, scr_h = root.winfo_screenwidth(), root.winfo_screenheight()
    pos_x = primary_mon.x + max(0, (scr_w - win_w) // 2)
    pos_y = primary_mon.y + max(0, (scr_h - win_h) // 2)
    root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
    root.lift()
    if sys.platform == "darwin" or os.name == "nt":
        try:
            root.attributes("-topmost", True)
            root.after(150, lambda: root.attributes("-topmost", False))
        except tk.TclError:
            pass

    if _on_ready is not None:
        root.after(250, lambda: _on_ready(root))

    root.mainloop()
    return state["result"]


# ---------------------------------------------------------------------------
# Entry point called by tools/bq_update.py --picker
# ---------------------------------------------------------------------------

def run_picker(
    *,
    root: Optional[Path] = None,
    userdir: Optional[Path] = None,
    out_env: Optional[Path] = None,
    env_format: Optional[str] = None,
    setup: bool = False,
    no_gui: bool = False,
    monitors: Optional[list[MonitorInfo]] = None,
    hardware_info: Optional[dict] = None,
    shift_held: Optional[bool] = None,
    gui_fn: Optional[Callable] = None,
) -> int:
    """Runs the pre-launch Display & Graphics Picker.

    Returns 0 on launch (config + env written) or 4 on user cancel.
    """
    pkg_root = Path(root).resolve() if root else Path(__file__).resolve().parent.parent
    udir = Path(userdir).resolve() if userdir else pkg_root
    gamedir = udir / "BakersfieldQuake"
    prefs_path = gamedir / PREFS_FILENAME
    config_cfg_path = gamedir / "config.cfg"
    video_cfg_path = gamedir / VIDEO_CFG_FILENAME
    fmt = env_format or ("cmd" if os.name == "nt" else "sh")

    detected_monitors = list(monitors) if monitors else detect_monitors()
    hw = hardware_info if hardware_info is not None else detect_hardware_info()
    rec_preset = recommend_preset(
        total_ram_gb=hw.get("total_ram_gb"),
        vram_mb=hw.get("vram_mb"),
        is_igpu=bool(hw.get("is_igpu", False)),
    )
    prefs = load_prefs(prefs_path)
    shift = is_shift_held() if shift_held is None else bool(shift_held)

    skip, selection = should_skip_gui(
        prefs,
        detected_monitors,
        config_cfg_path,
        setup=setup,
        shift_held=shift,
        default_preset=rec_preset,
    )

    if skip or no_gui:
        write_video_cfg(video_cfg_path, selection)
        if out_env is not None:
            write_env_file(Path(out_env), selection, cancelled=False, env_format=fmt)
        return 0

    show_fn = gui_fn or show_picker_gui
    try:
        chosen = show_fn(detected_monitors, selection, rec_preset, pkg_root=pkg_root)
    except Exception:
        # Headless / broken Tk fallback: never crash launch; apply detected defaults cleanly
        write_video_cfg(video_cfg_path, selection)
        if out_env is not None:
            write_env_file(Path(out_env), selection, cancelled=False, env_format=fmt)
        return 0

    if chosen is None:
        if out_env is not None:
            write_env_file(Path(out_env), None, cancelled=True, env_format=fmt)
        return 4

    save_prefs(prefs_path, chosen)
    write_video_cfg(video_cfg_path, chosen)
    if out_env is not None:
        write_env_file(Path(out_env), chosen, cancelled=False, env_format=fmt)
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="BAKOQUAKE pre-launch Display & Graphics Picker")
    ap.add_argument("--root", type=Path, default=None)
    ap.add_argument("--userdir", type=Path, default=None)
    ap.add_argument("--out-env", type=Path, default=None)
    ap.add_argument("--env-format", choices=("cmd", "sh"), default=None)
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--no-gui", action="store_true")
    ns = ap.parse_args()
    sys.exit(
        run_picker(
            root=ns.root,
            userdir=ns.userdir,
            out_env=ns.out_env,
            env_format=ns.env_format,
            setup=ns.setup,
            no_gui=ns.no_gui,
        )
    )
