"""Unit tests for tools/bq_display.py (Display & Graphics Picker).

python -m unittest discover -s source/ci/tests -v
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

_disp_spec = importlib.util.spec_from_file_location("bq_display", REPO / "tools" / "bq_display.py")
bd = importlib.util.module_from_spec(_disp_spec)
sys.modules["bq_display"] = bd
_disp_spec.loader.exec_module(bd)

_upd_spec = importlib.util.spec_from_file_location("bq_update", REPO / "tools" / "bq_update.py")
bq = importlib.util.module_from_spec(_upd_spec)
sys.modules["bq_update"] = bq
_upd_spec.loader.exec_module(bq)


def _make_mon(
    mon_id="DISPLAY1:0",
    index=0,
    name="ASUS VG249Q",
    device=r"\\.\DISPLAY1",
    is_primary=True,
    x=0,
    y=0,
    w=2560,
    h=1440,
    hz=144,
    modes=None,
):
    raw_modes = modes if modes is not None else [(w, h), (1920, 1080), (1600, 900), (1280, 720)]
    return bd.MonitorInfo(
        id=mon_id,
        index=index,
        name=name,
        device=device,
        is_primary=is_primary,
        x=x,
        y=y,
        width=w,
        height=h,
        native_width=w,
        native_height=h,
        hz=hz,
        resolutions=bd.filter_resolutions(raw_modes, w, h),
    )


def _parse_cfg_cvars(cfg_text):
    cvars = {}
    for line in cfg_text.splitlines():
        s = line.split("//", 1)[0].strip()
        if not s:
            continue
        parts = s.split(None, 2)
        if parts[0].lower() == "seta" and len(parts) >= 3:
            key = parts[1]
            val = parts[2].strip('"')
        else:
            key = parts[0]
            val = s[len(key):].strip().strip('"')
        cvars[key] = val
    return cvars


class AspectAndMathTest(unittest.TestCase):
    def test_aspect_ratio_labels(self):
        self.assertEqual(bd.format_aspect_ratio(1920, 1080), "16:9")
        self.assertEqual(bd.format_aspect_ratio(2560, 1440), "16:9")
        self.assertEqual(bd.format_aspect_ratio(3840, 2160), "16:9")
        self.assertEqual(bd.format_aspect_ratio(1366, 768), "16:9")
        self.assertEqual(bd.format_aspect_ratio(1920, 1200), "16:10")
        self.assertEqual(bd.format_aspect_ratio(1680, 1050), "16:10")
        self.assertEqual(bd.format_aspect_ratio(2560, 1080), "21:9")
        self.assertEqual(bd.format_aspect_ratio(3440, 1440), "21:9")
        self.assertEqual(bd.format_aspect_ratio(3840, 1600), "21:9")
        self.assertEqual(bd.format_aspect_ratio(5120, 1440), "32:9")
        self.assertEqual(bd.format_aspect_ratio(1024, 768), "4:3")
        self.assertEqual(bd.format_aspect_ratio(1280, 1024), "5:4")
        self.assertEqual(bd.format_aspect_ratio(2000, 1000), "2:1")

    def test_conwidth_aspect_matching_and_clamping(self):
        self.assertEqual(bd.compute_conwidth(1920, 1080), 640)
        self.assertEqual(bd.compute_conwidth(2560, 1440), 640)
        self.assertEqual(bd.compute_conwidth(1920, 1200), 576)
        self.assertEqual(bd.compute_conwidth(3440, 1440), 860)
        self.assertEqual(bd.compute_conwidth(5120, 1440), 1280)
        self.assertEqual(bd.compute_conwidth(1024, 768), 480)
        # Clamp extreme ratios
        self.assertEqual(bd.compute_conwidth(800, 1000), 480)
        self.assertEqual(bd.compute_conwidth(7680, 1440), 1280)

    def test_filter_resolutions_and_labels(self):
        raw = [
            (640, 480),     # too small -> filtered out
            (720, 480),     # too small -> filtered out
            (1080, 1920),   # portrait on landscape monitor -> filtered out
            (3840, 2160),   # above native -> filtered out
            (2560, 1440),
            (2560, 1440),   # duplicate
            (1920, 1080),
            (1280, 720),
        ]
        res = bd.filter_resolutions(raw, 2560, 1440)
        self.assertEqual(res[0], (2560, 1440))
        self.assertIn((1920, 1080), res)
        self.assertIn((1600, 900), res)  # standard aspect step auto-included
        self.assertIn((1280, 720), res)
        self.assertNotIn((640, 480), res)
        self.assertNotIn((3840, 2160), res)
        self.assertNotIn((1080, 1920), res)
        self.assertEqual(len(res), len(set(res)))

        self.assertEqual(bd.format_resolution_label(2560, 1440, 2560, 1440), "2560x1440 (16:9, Native)")
        self.assertEqual(bd.format_resolution_label(1920, 1080, 2560, 1440), "1920x1080 (16:9)")

    def test_windowed_fallback_preserves_aspect_and_fits_85_percent(self):
        for w, h in ((1920, 1080), (2560, 1440), (3840, 2160), (3440, 1440), (5120, 1440), (1680, 1050), (1024, 768)):
            ww, wh = bd.compute_windowed_fallback(w, h, w, h)
            self.assertLessEqual(ww, int(w * 0.85) + 2, (w, h, ww, wh))
            self.assertLessEqual(wh, int(h * 0.85) + 2, (w, h, ww, wh))
            orig_ar = w / h
            win_ar = ww / wh
            self.assertLess(abs(win_ar - orig_ar) / orig_ar, 0.03, (w, h, ww, wh))


class MonitorParsingTest(unittest.TestCase):
    def test_finalize_monitors_primary_first_and_labels(self):
        raw = [
            {
                "device": r"\\.\DISPLAY2",
                "name": "Generic PnP Monitor",
                "is_primary": False,
                "x": -1680,
                "y": 31,
                "width": 1680,
                "height": 1050,
                "native_width": 1680,
                "native_height": 1050,
                "hz": 75,
                "modes": [(1680, 1050), (1280, 800)],
            },
            {
                "device": r"\\.\DISPLAY1",
                "name": "ASUS VG249QE5A",
                "is_primary": True,
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "native_width": 1920,
                "native_height": 1080,
                "hz": 144,
                "modes": [(1920, 1080), (1280, 720)],
            },
        ]
        mons = bd._finalize_monitors(raw)
        self.assertEqual(len(mons), 2)
        self.assertTrue(mons[0].is_primary)
        self.assertEqual(mons[0].id, "DISPLAY1:0")
        self.assertEqual(mons[1].id, "DISPLAY2:1")
        self.assertEqual(mons[1].x, -1680)
        self.assertIn("Monitor 1: ASUS VG249QE5A — Primary (1920x1080, 144 Hz)", bd.format_monitor_label(mons[0]))
        self.assertEqual(bd.format_monitor_label(mons[1]), "Monitor 2: Secondary (1680x1050, 75 Hz)")

    def test_parse_xrandr_dual_monitors(self):
        sample = """\
Screen 0: minimum 320 x 200, current 4480 x 1440, maximum 16384 x 16384
HDMI-1 disconnected (normal left inverted right x axis y axis)
DP-2 connected 1920x1080+2560+180 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+  50.00
   1280x720      60.00
DP-1 connected primary 2560x1440+0+0 (normal left inverted right x axis y axis) 597mm x 336mm
   2560x1440    143.97*+ 120.00   59.95
   1920x1080    120.00    60.00
   1600x900      60.00
"""
        mons = bd.parse_xrandr_output(sample)
        self.assertEqual(len(mons), 2)
        self.assertTrue(mons[0].is_primary)
        self.assertEqual(mons[0].device, "DP-1")
        self.assertEqual((mons[0].native_width, mons[0].native_height), (2560, 1440))
        self.assertEqual(mons[0].hz, 144)
        self.assertEqual((mons[0].x, mons[0].y), (0, 0))
        self.assertIn((1920, 1080), mons[0].resolutions)

        self.assertFalse(mons[1].is_primary)
        self.assertEqual(mons[1].device, "DP-2")
        self.assertEqual((mons[1].x, mons[1].y), (2560, 180))
        self.assertEqual(mons[1].hz, 60)

    def test_parse_macos_system_profiler_json(self):
        sample = json.dumps(
            {
                "SPDisplaysDataType": [
                    {
                        "_name": "Apple M3 Pro",
                        "spdisplays_ndrvs": [
                            {
                                "_name": "Studio Display",
                                "_spdisplays_pixels": "5120 x 2880",
                                "_spdisplays_resolution": "2560 x 1440 @ 60.00Hz",
                                "spdisplays_main": "spdisplays_no",
                            },
                            {
                                "_name": "Color LCD",
                                "_spdisplays_pixels": "3024 x 1964",
                                "_spdisplays_resolution": "1512 x 982 @ 120.00Hz",
                                "spdisplays_main": "spdisplays_yes",
                            },
                        ],
                    }
                ]
            }
        )
        mons = bd.parse_macos_system_profiler_json(sample)
        self.assertEqual(len(mons), 2)
        self.assertTrue(mons[0].is_primary)
        self.assertEqual(mons[0].name, "Color LCD")
        self.assertEqual((mons[0].native_width, mons[0].native_height), (3024, 1964))
        self.assertEqual(mons[0].hz, 120)
        self.assertEqual(mons[1].name, "Studio Display")
        self.assertEqual((mons[1].native_width, mons[1].native_height), (5120, 2880))
        self.assertEqual(mons[1].hz, 60)

    def test_recommend_preset_hardware_tiers(self):
        self.assertEqual(bd.recommend_preset(total_ram_gb=8.0, vram_mb=8192, is_igpu=False), "simple")
        self.assertEqual(bd.recommend_preset(total_ram_gb=16.0, vram_mb=2048, is_igpu=False), "simple")
        self.assertEqual(bd.recommend_preset(total_ram_gb=16.0, vram_mb=4096, is_igpu=True), "simple")
        self.assertEqual(bd.recommend_preset(total_ram_gb=16.0, vram_mb=8192, is_igpu=False), "normal")
        self.assertEqual(bd.recommend_preset(total_ram_gb=None, vram_mb=None, is_igpu=False), "normal")


class PersistenceAndReopenTest(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        self.cfg = self.td / "config.cfg"
        self.mon1 = _make_mon(mon_id="DISPLAY1:0", index=0, is_primary=True, w=2560, h=1440, hz=144)
        self.mon2 = _make_mon(mon_id="DISPLAY2:1", index=1, is_primary=False, x=-1920, y=0, w=1920, h=1080, hz=60)
        self.valid_prefs = {
            "version": 1,
            "remember": True,
            "monitor_id": "DISPLAY1:0",
            "monitor_native": [2560, 1440],
            "mode": "borderless",
            "width": 2560,
            "height": 1440,
            "preset": "high",
        }

    def test_skip_gui_when_remembered_and_valid(self):
        skip, sel = bd.should_skip_gui(
            self.valid_prefs, [self.mon1, self.mon2], self.cfg, env={}
        )
        self.assertTrue(skip)
        self.assertEqual(sel.monitor.id, "DISPLAY1:0")
        self.assertEqual((sel.width, sel.height), (2560, 1440))
        self.assertEqual(sel.preset, "high")

    def test_reopens_on_setup_env_shift_or_config_flag(self):
        skip, _ = bd.should_skip_gui(self.valid_prefs, [self.mon1], self.cfg, setup=True, env={})
        self.assertFalse(skip)

        skip, _ = bd.should_skip_gui(self.valid_prefs, [self.mon1], self.cfg, env={"BQ_SETUP": "1"})
        self.assertFalse(skip)

        skip, _ = bd.should_skip_gui(self.valid_prefs, [self.mon1], self.cfg, shift_held=True, env={})
        self.assertFalse(skip)

        # MenuQC sets bm_show_launcher "1"
        self.cfg.write_text('seta bm_show_launcher "1"\n', encoding="utf-8")
        skip, _ = bd.should_skip_gui(self.valid_prefs, [self.mon1], self.cfg, env={})
        self.assertFalse(skip)

        # Later cleared back to "0" -> skips again
        self.cfg.write_text('seta bm_show_launcher "1"\nbm_show_launcher "0"\n', encoding="utf-8")
        skip, _ = bd.should_skip_gui(self.valid_prefs, [self.mon1], self.cfg, env={})
        self.assertTrue(skip)

    def test_reopens_when_monitor_changes_or_resolution_invalid(self):
        # Saved monitor unplugged
        other = _make_mon(mon_id="DISPLAY3:0", index=0, is_primary=True, w=1920, h=1080, hz=60)
        skip, sel = bd.should_skip_gui(self.valid_prefs, [other], self.cfg, env={})
        self.assertFalse(skip)
        self.assertEqual(sel.monitor.id, "DISPLAY3:0")
        self.assertEqual((sel.width, sel.height), (1920, 1080))

        # Same monitor ID, but native resolution changed (e.g. swapped display)
        swapped = _make_mon(mon_id="DISPLAY1:0", index=0, is_primary=True, w=1920, h=1080, hz=60)
        skip, _ = bd.should_skip_gui(self.valid_prefs, [swapped], self.cfg, env={})
        self.assertFalse(skip)

        # Remember unchecked -> always opens GUI pre-filled
        unrem = dict(self.valid_prefs, remember=False)
        skip, sel = bd.should_skip_gui(unrem, [self.mon1], self.cfg, env={})
        self.assertFalse(skip)
        self.assertEqual(sel.preset, "high")


class ConfigAndEnvGenerationTest(unittest.TestCase):
    def test_video_cfg_all_modes_and_alt_enter_safety(self):
        primary = _make_mon(mon_id="DISPLAY1:0", index=0, is_primary=True, w=2560, h=1440, hz=165)
        secondary = _make_mon(mon_id="DISPLAY2:1", index=1, is_primary=False, x=-1920, y=0, w=1920, h=1080, hz=75)

        # 1. Borderless on primary native -> vid_fullscreen 1, vid_desktopfullscreen 1, vid_borderless 0
        c1 = _parse_cfg_cvars(bd.build_video_cfg(bd.PickerSelection(primary, "borderless", 2560, 1440, "normal")))
        self.assertEqual(c1["vid_fullscreen"], "1")
        self.assertEqual(c1["vid_desktopfullscreen"], "1")
        self.assertEqual(c1["vid_borderless"], "0")
        self.assertEqual(c1["vid_width"], "2560")
        self.assertEqual(c1["vid_height"], "1440")
        self.assertEqual(c1["_vid_fullscreen_width"], "2560")
        self.assertEqual(c1["_vid_fullscreen_height"], "1440")
        self.assertEqual(c1["_vid_window_width"], "1920")
        self.assertEqual(c1["_vid_window_height"], "1080")
        self.assertEqual(c1["vid_conwidth"], "640")
        self.assertEqual(c1["vid_conheight"], "360")
        self.assertEqual(c1["vid_refreshrate"], "165")
        self.assertEqual(c1["vid_userefreshrate"], "1")
        self.assertEqual(c1["cl_maxfps"], "250")
        self.assertEqual(c1["bm_show_launcher"], "0")

        # 2. Borderless on secondary -> vid_fullscreen 0, vid_desktopfullscreen 0, vid_borderless 1
        c2 = _parse_cfg_cvars(bd.build_video_cfg(bd.PickerSelection(secondary, "borderless", 1920, 1080, "normal")))
        self.assertEqual(c2["vid_fullscreen"], "0")
        self.assertEqual(c2["vid_desktopfullscreen"], "0")
        self.assertEqual(c2["vid_borderless"], "1")
        self.assertEqual(c2["vid_width"], "1920")
        self.assertEqual(c2["vid_height"], "1080")
        self.assertEqual(c2["_vid_window_width"], "1600")
        self.assertEqual(c2["_vid_window_height"], "900")

        # 3. Exclusive fullscreen on 360 Hz monitor -> cl_maxfps bumps to 360
        mon360 = _make_mon(w=3440, h=1440, hz=360)
        c3 = _parse_cfg_cvars(bd.build_video_cfg(bd.PickerSelection(mon360, "fullscreen", 3440, 1440, "high")))
        self.assertEqual(c3["vid_fullscreen"], "1")
        self.assertEqual(c3["vid_desktopfullscreen"], "0")
        self.assertEqual(c3["vid_borderless"], "0")
        self.assertEqual(c3["vid_conwidth"], "860")
        self.assertEqual(c3["vid_refreshrate"], "360")
        self.assertEqual(c3["cl_maxfps"], "360")

        # 4. Windowed -> _vid_fullscreen_* matches monitor native, _vid_window_* matches chosen res
        c4 = _parse_cfg_cvars(bd.build_video_cfg(bd.PickerSelection(primary, "windowed", 1920, 1080, "simple")))
        self.assertEqual(c4["vid_fullscreen"], "0")
        self.assertEqual(c4["vid_desktopfullscreen"], "0")
        self.assertEqual(c4["vid_borderless"], "0")
        self.assertEqual(c4["vid_width"], "1920")
        self.assertEqual(c4["vid_height"], "1080")
        self.assertEqual(c4["_vid_window_width"], "1920")
        self.assertEqual(c4["_vid_window_height"], "1080")
        self.assertEqual(c4["_vid_fullscreen_width"], "2560")
        self.assertEqual(c4["_vid_fullscreen_height"], "1440")

    def test_video_cfg_all_three_presets_and_base_resets(self):
        mon = _make_mon()
        base_resets = {
            "gl_picmip": "0",
            "gl_picmip_world": "0",
            "gl_picmip_other": "0",
            "gl_picmip_sprites": "0",
            "gl_picmip_force": "0",
            "gl_max_size": "2048",
            "gl_texturecompression": "0",
            "r_dynamic": "1",
            "menu_background": "1",
            "mod_bsp_portalize": "0",
            "mod_freebeforeload": "1",
            "mod_q1bsp_pvs_ondemand": "1",
            "mod_q1bsp_lazy_render_bih": "1",
        }
        for preset in ("simple", "normal", "high"):
            txt = bd.build_video_cfg(bd.PickerSelection(mon, "borderless", 2560, 1440, preset))
            cv = _parse_cfg_cvars(txt)
            for k, v in base_resets.items():
                self.assertEqual(cv.get(k), v, f"preset={preset} missing/wrong reset {k}")

        simple = _parse_cfg_cvars(bd.build_video_cfg(bd.PickerSelection(mon, "borderless", 2560, 1440, "simple")))
        self.assertEqual(simple["lowspec"], "1")
        self.assertEqual(simple["r_bloom"], "0")
        self.assertEqual(simple["r_shadow_realtime_dlight"], "0")
        self.assertEqual(simple["r_load_normalmap"], "0")
        self.assertEqual(simple["vid_samples"], "1")
        self.assertEqual(simple["gl_texture_anisotropy"], "4")
        self.assertEqual(simple["cl_decals_max"], "128")

        normal = _parse_cfg_cvars(bd.build_video_cfg(bd.PickerSelection(mon, "borderless", 2560, 1440, "normal")))
        self.assertEqual(normal["lowspec"], "0")
        self.assertEqual(normal["r_bloom"], "1")
        self.assertEqual(normal["r_shadow_realtime_dlight_shadows"], "1")
        self.assertEqual(normal["r_shadow_shadowmapping"], "0")
        self.assertEqual(normal["r_glsl_offsetmapping"], "1")
        self.assertEqual(normal["r_glsl_offsetmapping_reliefmapping"], "0")
        self.assertEqual(normal["r_water"], "0")
        self.assertEqual(normal["vid_samples"], "4")
        self.assertEqual(normal["gl_texture_anisotropy"], "16")
        self.assertEqual(normal["r_shadow_shadowmapping_texturesize"], "4096")

        high = _parse_cfg_cvars(bd.build_video_cfg(bd.PickerSelection(mon, "borderless", 2560, 1440, "high")))
        self.assertEqual(high["lowspec"], "0")
        self.assertEqual(high["r_glsl_offsetmapping_reliefmapping"], "1")
        self.assertEqual(high["r_glsl_offsetmapping_scale"], "0.04")
        self.assertEqual(high["r_shadow_shadowmapping"], "1")
        self.assertEqual(high["r_shadow_shadowmapping_maxsize"], "1024")
        self.assertEqual(high["r_shadow_glossexact"], "1")
        self.assertEqual(high["r_water"], "1")
        self.assertEqual(high["r_water_lowquality"], "0")
        self.assertEqual(high["r_water_resolutionmultiplier"], "0.75")
        self.assertEqual(high["r_wateralpha"], "0.5")
        self.assertEqual(high["r_glsl_saturation"], "1.1")
        # Ensure high does not emit duplicate contradictory lines for overridden cvars
        high_text = bd.build_video_cfg(bd.PickerSelection(mon, "borderless", 2560, 1440, "high"))
        self.assertEqual(high_text.count("\nr_water "), 1)
        self.assertEqual(high_text.count("\nr_shadow_shadowmapping "), 1)

    def test_env_output_cmd_and_sh(self):
        mon = _make_mon(is_primary=False, x=-1680, y=31, w=1680, h=1050, hz=75)
        sel = bd.PickerSelection(mon, "borderless", 1680, 1050, "high", remember=True)

        cmd_out = bd.format_env_output(sel, cancelled=False, env_format="cmd")
        self.assertIn('set "BQ_PICK_CANCEL=0"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_PRESET=high"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_MODE=borderless"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_WIDTH=1680"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_HEIGHT=1050"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_HZ=75"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_MON_X=-1680"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_MON_Y=31"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_MON_W=1680"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_MON_H=1050"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_MON_PRIMARY=0"\r\n', cmd_out)
        self.assertIn('set "BQ_PICK_CFG=bq_launch_video.cfg"\r\n', cmd_out)

        sh_out = bd.format_env_output(sel, cancelled=False, env_format="sh")
        self.assertNotIn("\r", sh_out)
        self.assertIn("BQ_PICK_CANCEL='0'\n", sh_out)
        self.assertIn("BQ_PICK_MON_X='-1680'\n", sh_out)
        self.assertIn("BQ_PICK_CFG='bq_launch_video.cfg'\n", sh_out)

        cancel_cmd = bd.format_env_output(None, cancelled=True, env_format="cmd")
        self.assertIn('set "BQ_PICK_CANCEL=1"\r\n', cancel_cmd)


class PickerFlowAndCliTest(unittest.TestCase):
    def test_run_picker_confirm_remember_and_cancel(self):
        mon = _make_mon(w=2560, h=1440, hz=144)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            env_file = td / "pick.cmd"

            # 1. User cancels -> exit 4, no video cfg written, env marks cancel=1
            rc = bd.run_picker(
                root=td,
                userdir=td,
                out_env=env_file,
                env_format="cmd",
                monitors=[mon],
                hardware_info={"total_ram_gb": 16.0, "vram_mb": 8192, "is_igpu": False},
                shift_held=False,
                gui_fn=lambda *a, **kw: None,
            )
            self.assertEqual(rc, 4)
            self.assertFalse((td / "BakersfieldQuake" / "bq_launch_video.cfg").exists())
            self.assertIn('set "BQ_PICK_CANCEL=1"', env_file.read_text("utf-8"))

            # 2. User selects High + Remember -> exit 0, saves prefs & video cfg
            called = []

            def fake_gui(mons, initial, rec, pkg_root=None):
                called.append((initial.preset, rec))
                return bd.PickerSelection(mons[0], "fullscreen", 1920, 1080, "high", remember=True)

            rc = bd.run_picker(
                root=td,
                userdir=td,
                out_env=env_file,
                env_format="sh",
                monitors=[mon],
                hardware_info={"total_ram_gb": 16.0, "vram_mb": 8192, "is_igpu": False},
                shift_held=False,
                gui_fn=fake_gui,
            )
            self.assertEqual(rc, 0)
            self.assertEqual(called, [("normal", "normal")])
            self.assertTrue((td / "BakersfieldQuake" / "bq_launcher_prefs.json").is_file())
            self.assertTrue((td / "BakersfieldQuake" / "bq_launch_video.cfg").is_file())
            self.assertIn("BQ_PICK_PRESET='high'", env_file.read_text("utf-8"))

            # 3. Second run with Remember=True skips GUI completely
            def must_not_run(*a, **kw):
                raise AssertionError("GUI should have been skipped when remembered")

            rc = bd.run_picker(
                root=td,
                userdir=td,
                out_env=env_file,
                env_format="sh",
                monitors=[mon],
                hardware_info={"total_ram_gb": 16.0, "vram_mb": 8192, "is_igpu": False},
                shift_held=False,
                gui_fn=must_not_run,
            )
            self.assertEqual(rc, 0)
            self.assertIn("BQ_PICK_WIDTH='1920'", env_file.read_text("utf-8"))

    def test_bq_update_cli_picker_no_gui_ignores_lock_and_no_update_env(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            userdir = td / "user"
            env_cmd = td / "out.cmd"
            env_sh = td / "out.sh"

            # Put an active update.lock in root/.bq AND set BQ_NO_UPDATE=1 — --picker must NOT block or touch .bq
            (td / ".bq").mkdir()
            lock = td / ".bq" / "update.lock"
            lock.write_text("99999\n", encoding="ascii")

            old_no_upd = os.environ.get("BQ_NO_UPDATE")
            os.environ["BQ_NO_UPDATE"] = "1"
            try:
                rc1 = bq.main([
                    "--picker",
                    "--no-gui",
                    "--root", str(td),
                    "--userdir", str(userdir),
                    "--out-env", str(env_cmd),
                    "--env-format", "cmd",
                ])
                rc2 = bq.main([
                    "--picker",
                    "--no-gui",
                    "--setup",
                    "--root", str(td),
                    "--userdir", str(userdir),
                    "--out-env", str(env_sh),
                    "--env-format", "sh",
                ])
            finally:
                if old_no_upd is None:
                    os.environ.pop("BQ_NO_UPDATE", None)
                else:
                    os.environ["BQ_NO_UPDATE"] = old_no_upd

            self.assertEqual(rc1, 0)
            self.assertEqual(rc2, 0)
            # Lock untouched by --picker
            self.assertTrue(lock.exists())
            cfg_path = userdir / "BakersfieldQuake" / "bq_launch_video.cfg"
            self.assertTrue(cfg_path.is_file())
            cfg_text = cfg_path.read_text("utf-8")
            self.assertIn('seta bm_show_launcher "0"', cfg_text)
            self.assertIn("vid_conheight 360", cfg_text)
            self.assertIn('set "BQ_PICK_CANCEL=0"', env_cmd.read_text("utf-8"))
            self.assertIn("BQ_PICK_CANCEL='0'", env_sh.read_text("utf-8"))
            self.assertIn("BQ_PICK_CFG='bq_launch_video.cfg'", env_sh.read_text("utf-8"))

    def test_subprocess_cli_picker_no_gui(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out_env = td / "env.sh"
            res = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "tools" / "bq_update.py"),
                    "--picker",
                    "--no-gui",
                    "--root", str(td),
                    "--userdir", str(td),
                    "--out-env", str(out_env),
                    "--env-format", "sh",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertFalse((td / ".bq").exists())
            self.assertTrue((td / "BakersfieldQuake" / "bq_launch_video.cfg").is_file())
            self.assertIn("BQ_PICK_CANCEL='0'", out_env.read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
