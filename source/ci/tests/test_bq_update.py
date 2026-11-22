"""Tests for tools/bq_update.py and source/ci/make_manifest.py against a local Range-capable HTTP server.

python -m unittest discover -s source/ci/tests
"""
import hashlib
import http.server
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("bq_update", REPO / "tools" / "bq_update.py")
bq = importlib.util.module_from_spec(spec)
sys.modules["bq_update"] = bq
spec.loader.exec_module(bq)

mm_spec = importlib.util.spec_from_file_location("make_manifest", REPO / "source" / "ci" / "make_manifest.py")
mm = importlib.util.module_from_spec(mm_spec)
sys.modules["make_manifest"] = mm
mm_spec.loader.exec_module(mm)


class RangeHandler(http.server.BaseHTTPRequestHandler):
    files = {}            # path -> bytes
    fail_paths = {}       # path -> HTTP status int
    honour_range = True
    hits = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        type(self).hits.append((self.path, self.headers.get("Range")))
        if self.path in self.fail_paths:
            self.send_error(self.fail_paths[self.path])
            return
        data = self.files.get(self.path)
        if data is None:
            self.send_error(404)
            return
        rng = self.headers.get("Range")
        if rng and self.honour_range:
            a, b = rng.split("=")[1].split("-")
            a, b = int(a), min(int(b), len(data) - 1)
            body = data[a:b + 1]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {a}-{b}/{len(data)}")
        else:
            body = data
            self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_zip(files):
    """files: {rel: bytes}. .pk3/.png stored, everything else deflated, like build-zip's `zip -n`."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for rel, data in sorted(files.items()):
            ct = zipfile.ZIP_STORED if rel.endswith((".pk3", ".png")) else zipfile.ZIP_DEFLATED
            info = zipfile.ZipInfo("BAKOQUAKE/" + rel)
            info.compress_type = ct
            info.extra = b"\xfe\xca\x04\x00abcd" if rel.endswith(".pk3") else b""
            z.writestr(info, data)
    return buf.getvalue()


def manifest_for(zip_bytes, url, build, **kwargs):
    d = Path(tempfile.mkdtemp())
    (d / "p.zip").write_bytes(zip_bytes)
    extra = []
    if kwargs.get("notes"):
        extra += ["--notes", kwargs["notes"]]
    if kwargs.get("vps_base"):
        extra += ["--vps-base", kwargs["vps_base"]]
    if kwargs.get("mac_inputs"):
        extra += ["--mac-inputs", kwargs["mac_inputs"]]
    if kwargs.get("dmg_url"):
        extra += ["--dmg-url", kwargs["dmg_url"]]
    if kwargs.get("dmg_vps_url"):
        extra += ["--dmg-vps-url", kwargs["dmg_vps_url"]]
    if kwargs.get("dmg_size"):
        extra += ["--dmg-size", str(kwargs["dmg_size"])]
    if kwargs.get("dmg_sha256"):
        extra += ["--dmg-sha256", kwargs["dmg_sha256"]]
    out = subprocess.run(
        [sys.executable, "-I", str(REPO / "source/ci/make_manifest.py"), str(d / "p.zip"), url,
         str(build), f"b{build}", *extra],
        capture_output=True, check=True, text=True,
    ).stdout
    return json.loads(out)


V1 = {
    "BakersfieldQuake/progs.dat": b"progs v1" * 5000,
    "BakersfieldQuake/bakersfield.pk3": os.urandom(300_000),
    "BakersfieldQuake/config.cfg": b"// BAKERSFIELD_SEED\n",
    "BakersfieldQuake/old_thing.cfg": b"bye\n",
    "darkplaces-sdl": b"\x7fELF engine v1",
}


class DecliningUI(bq.UpdateUI):
    """Test UI that always declines prompts (simulates clicking Exit)."""

    def __init__(self):
        self.saw_plan = None

    def run_flow(self, updater, check=False, force=False, launch=False, standalone=False):
        plan = updater.plan_update(force=force)
        self.saw_plan = plan
        if not plan.needs_action:
            return 0
        return 0 if standalone else 4


class ConfirmingProgressUI(bq.UpdateUI):
    """Test UI that confirms prompts and captures all progress callbacks."""

    def __init__(self):
        self.saw_plan = None
        self.progress_events = []

    def run_flow(self, updater, check=False, force=False, launch=False, standalone=False):
        plan = updater.plan_update(force=force)
        self.saw_plan = plan
        if not plan.needs_action:
            return 0
        res = updater.apply_plan(plan, progress_cb=lambda *a: self.progress_events.append(a))
        if plan.kind == "dmg":
            return 4
        return 3 if res else 0


class RateTrackerTest(unittest.TestCase):
    def test_speed_and_eta_formatting(self):
        t = [0.0]
        tracker = bq.RateTracker(alpha=0.5, clock=lambda: t[0])
        tracker.start(10_000_000)
        self.assertEqual(tracker.current_speed(), 0.0)
        self.assertIsNone(tracker.eta_seconds())

        t[0] = 0.5
        tracker.update(2_000_000)  # 4 MB/s in first window
        spd1 = tracker.current_speed()
        self.assertAlmostEqual(spd1, 4_000_000.0, places=1)
        eta1 = tracker.eta_seconds(8_000_000)
        self.assertAlmostEqual(eta1, 2.0, places=2)

        t[0] = 1.5
        tracker.update(4_000_000)  # +2 MB over 1.0s => inst 2 MB/s, EWMA 0.5*2 + 0.5*4 = 3 MB/s
        self.assertAlmostEqual(tracker.current_speed(), 3_000_000.0, places=1)
        self.assertEqual(bq.fmt_speed(tracker.current_speed()), "3.0 MB/s")
        self.assertEqual(bq.fmt_eta(tracker.eta_seconds(6_000_000)), "~2s remaining")
        self.assertEqual(bq.fmt_eta(75), "~1m 15s remaining")
        self.assertEqual(bq.fmt(1_500_000), "1.5 MB")
        self.assertEqual(bq.fmt(512), "512 B")


class ManifestScriptTest(unittest.TestCase):
    def test_notes_vps_base_and_patch_manifest(self):
        zb = make_zip(V1)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            zp = td / "pkg.zip"
            zp.write_bytes(zb)
            mp = td / "manifest-macos-app.json"
            out = subprocess.run(
                [sys.executable, "-I", str(REPO / "source/ci/make_manifest.py"),
                 str(zp), "https://example/pkg.zip", "12", "build-20261121-abc",
                 "--only", "BakersfieldQuake/",
                 "--notes", "Fixed go-karts",
                 "--vps-base", "https://bakersfield.larrywew.fun/updates/"],
                capture_output=True, check=True, text=True,
            ).stdout
            mp.write_text(out, "utf-8")
            data = json.loads(out)
            self.assertEqual(data["notes"], "Fixed go-karts")
            self.assertEqual(data["vps_base"], "https://bakersfield.larrywew.fun/updates")
            self.assertNotIn("darkplaces-sdl", data["files"])

            subprocess.run(
                [sys.executable, "-I", str(REPO / "source/ci/make_manifest.py"),
                 "--patch-manifest", str(mp), "--output", str(mp),
                 "--mac-inputs", "deadbeef",
                 "--dmg-url", "https://github.com/x/y.dmg",
                 "--dmg-vps-url", "https://vps/y.dmg",
                 "--dmg-size", "12345",
                 "--dmg-sha256", "a" * 64],
                check=True,
            )
            patched = json.loads(mp.read_text("utf-8"))
            self.assertEqual(patched["mac_inputs"], "deadbeef")
            self.assertEqual(patched["dmg_size"], 12345)
            self.assertEqual(patched["dmg_vps_url"], "https://vps/y.dmg")


class UpdaterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RangeHandler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        RangeHandler.files = {}
        RangeHandler.fail_paths = {}
        RangeHandler.hits = []
        RangeHandler.honour_range = True
        self.root = Path(tempfile.mkdtemp())
        self.publish(V1, 1)
        with zipfile.ZipFile(io.BytesIO(RangeHandler.files["/1.zip"])) as z:
            for i in z.infolist():
                p = self.root / i.filename[len("BAKOQUAKE/"):]
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(z.read(i))

    def publish(self, files, build, tamper=None, populate_vps=False, **kwargs):
        zb = make_zip(files)
        RangeHandler.files[f"/{build}.zip"] = zb
        if populate_vps:
            kwargs.setdefault("vps_base", f"{self.base}/vps")
        m = manifest_for(zb, f"{self.base}/{build}.zip", build, **kwargs)
        if tamper:
            tamper(m)
        raw = json.dumps(m).encode()
        RangeHandler.files["/manifest.json"] = raw
        if populate_vps:
            RangeHandler.files["/vps/manifest.json"] = raw
            for data in files.values():
                sha = hashlib.sha256(data).hexdigest()
                RangeHandler.files[f"/vps/files/{sha}"] = data
        return m

    def run_updater(self, *extra):
        return bq.main(["--root", str(self.root), "--manifest-url", f"{self.base}/manifest.json",
                        "--no-gui", *extra])

    def state(self):
        return json.loads((self.root / ".bq/state.json").read_text())

    def test_first_run_matches_and_downloads_nothing(self):
        self.assertEqual(self.run_updater(), 0)
        self.assertEqual(self.state()["build"], 1)
        self.assertEqual(self.state()["updater"], bq.VERSION)
        self.assertFalse([h for h in RangeHandler.hits if h[0] == "/1.zip"])

    def test_update_fetches_only_changed_files(self):
        self.run_updater()
        (self.root / "BakersfieldQuake/config.cfg").write_bytes(b"name rob\n")
        (self.root / "id1").mkdir()
        (self.root / "id1/pak0.pak").write_bytes(b"paks")
        v2 = dict(V1)
        v2["BakersfieldQuake/progs.dat"] = b"progs v2" * 5000
        v2["BakersfieldQuake/zz_karts.pk3"] = os.urandom(50_000)
        v2["BakersfieldQuake/config.cfg"] = b"// BAKERSFIELD_SEED v2\n"
        del v2["BakersfieldQuake/old_thing.cfg"]
        self.publish(v2, 2, notes="Added go-karts")
        RangeHandler.hits = []
        self.assertEqual(self.run_updater("--check"), 10)
        self.assertEqual(self.run_updater("--launch"), 3)
        self.assertEqual(self.run_updater("--launch"), 0)
        for rel in ("BakersfieldQuake/progs.dat", "BakersfieldQuake/zz_karts.pk3"):
            self.assertEqual((self.root / rel).read_bytes(), v2[rel])
        self.assertEqual((self.root / "BakersfieldQuake/config.cfg").read_bytes(), b"name rob\n")
        self.assertEqual((self.root / "id1/pak0.pak").read_bytes(), b"paks")
        self.assertFalse((self.root / "BakersfieldQuake/old_thing.cfg").exists())
        self.assertEqual(self.state()["build"], 2)
        if os.name != "nt":
            self.assertTrue(os.access(self.root / "darkplaces-sdl", os.X_OK))
        sizes = [int(r.split("-")[1]) - int(r.split("=")[1].split("-")[0]) for p, r in RangeHandler.hits
                 if p == "/2.zip" and r]
        self.assertTrue(sizes and max(sizes) < 200_000, sizes)
        self.assertEqual(self.run_updater("--check"), 0)

    def test_same_build_repairs_missing_and_corrupt_files(self):
        # First pass records build 1.
        self.assertEqual(self.run_updater("--launch"), 0)

        # Delete bakersfield.pk3 and corrupt progs.dat without changing the build number on the server.
        (self.root / "BakersfieldQuake/bakersfield.pk3").unlink()
        (self.root / "BakersfieldQuake/progs.dat").write_bytes(b"corrupted!")
        RangeHandler.hits = []

        self.assertEqual(self.run_updater("--check"), 10)
        self.assertEqual(self.run_updater("--launch"), 3)
        self.assertEqual((self.root / "BakersfieldQuake/bakersfield.pk3").read_bytes(),
                         V1["BakersfieldQuake/bakersfield.pk3"])
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(),
                         V1["BakersfieldQuake/progs.dat"])
        self.assertEqual(self.run_updater("--launch"), 0)

    def test_vps_manifest_fallback_when_github_down(self):
        self.run_updater()
        v2 = dict(V1, **{"BakersfieldQuake/progs.dat": b"progs vps" * 2000})
        self.publish(v2, 2, populate_vps=True)
        RangeHandler.fail_paths["/manifest.json"] = 503
        RangeHandler.hits = []

        rc = bq.main([
            "--root", str(self.root),
            "--manifest-url", f"{self.base}/manifest.json",
            "--fallback-url", f"{self.base}/vps/manifest.json",
            "--no-gui", "--launch",
        ])
        self.assertEqual(rc, 3)
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(), v2["BakersfieldQuake/progs.dat"])
        sha = hashlib.sha256(v2["BakersfieldQuake/progs.dat"]).hexdigest()
        self.assertTrue(any(p == f"/vps/files/{sha}" for p, _ in RangeHandler.hits))

    def test_per_file_vps_fallback_when_github_zip_fails(self):
        self.run_updater()
        v2 = dict(V1, **{"BakersfieldQuake/zz_sound.pk3": b"soundpack v2" * 500})
        self.publish(v2, 2, populate_vps=True)
        RangeHandler.fail_paths["/2.zip"] = 500
        RangeHandler.hits = []

        rc = bq.main([
            "--root", str(self.root),
            "--manifest-url", f"{self.base}/manifest.json",
            "--fallback-url", f"{self.base}/vps/manifest.json",
            "--no-gui", "--launch",
        ])
        self.assertEqual(rc, 3)
        self.assertEqual((self.root / "BakersfieldQuake/zz_sound.pk3").read_bytes(),
                         v2["BakersfieldQuake/zz_sound.pk3"])
        sha = hashlib.sha256(v2["BakersfieldQuake/zz_sound.pk3"]).hexdigest()
        self.assertTrue(any(p == f"/vps/files/{sha}" for p, _ in RangeHandler.hits))

    def test_declining_update_blocks_launch_with_exit_4(self):
        self.run_updater()
        v2 = dict(V1, **{"BakersfieldQuake/progs.dat": b"new v2"})
        self.publish(v2, 2, notes="New weapons")
        ui = DecliningUI()
        up = bq.Updater(self.root, "windows-x64", f"{self.base}/manifest.json", lambda _m: None)
        rc = up.run(launch=True, ui=ui)
        self.assertEqual(rc, 4)
        self.assertEqual(ui.saw_plan.kind, "update")
        self.assertEqual(ui.saw_plan.notes, "New weapons")
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(),
                         V1["BakersfieldQuake/progs.dat"])
        self.assertEqual(self.state()["build"], 1)

    def test_bad_hash_keeps_old_version_and_blocks_launch(self):
        self.run_updater()
        v2 = dict(V1, **{"BakersfieldQuake/progs.dat": b"evil"})

        def tamper(m):
            m["files"]["BakersfieldQuake/progs.dat"]["sha256"] = "0" * 64
        self.publish(v2, 2, tamper)
        self.assertEqual(self.run_updater("--launch"), 4)
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(), V1["BakersfieldQuake/progs.dat"])
        self.assertEqual(self.state()["build"], 1)

    def test_rollback_refused(self):
        self.publish(dict(V1, **{"BakersfieldQuake/progs.dat": b"new"}), 5)
        self.run_updater()
        self.publish(V1, 3)
        self.run_updater()
        self.assertEqual(self.state()["build"], 5)
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(), b"new")

    def test_offline_allows_launch_but_failed_range_blocks_launch(self):
        # Both primary and fallback unreachable -> exit 0 (offline play allowed).
        rc = bq.main(["--root", str(self.root), "--manifest-url", "http://127.0.0.1:9/m.json",
                      "--fallback-url", "http://127.0.0.1:9/vps.json", "--no-gui", "--launch"])
        self.assertEqual(rc, 0)

        # Manifest reachable (update exists) but download fails -> exit 4 (never play outdated).
        self.run_updater()
        self.publish(dict(V1, **{"BakersfieldQuake/progs.dat": b"v2"}), 2)
        RangeHandler.honour_range = False
        self.assertEqual(self.run_updater("--launch"), 4)
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(), V1["BakersfieldQuake/progs.dat"])
        self.assertEqual(self.state()["build"], 1)

    def test_macos_dmg_required_downloads_verifies_opens_and_blocks_launch(self):
        self.run_updater()
        mac_inputs_file = self.root / "mac-inputs"
        mac_inputs_file.write_text("old-inputs-hash\n", "utf-8")
        dmg_bytes = b"UDIF_FAKE_DMG_DATA" * 4096
        dmg_sha = hashlib.sha256(dmg_bytes).hexdigest()
        RangeHandler.files["/BAKOQUAKE.dmg"] = dmg_bytes

        self.publish(
            V1, 2,
            mac_inputs="new-inputs-hash",
            dmg_url=f"{self.base}/missing.dmg",
            dmg_vps_url=f"{self.base}/BAKOQUAKE.dmg",
            dmg_size=len(dmg_bytes),
            dmg_sha256=dmg_sha,
        )
        RangeHandler.fail_paths["/missing.dmg"] = 404

        opened = []
        with tempfile.TemporaryDirectory() as dl_dir:
            ui = ConfirmingProgressUI()
            up = bq.Updater(
                self.root, "macos-app", f"{self.base}/manifest.json", lambda _m: None,
                bundle_mac_inputs=mac_inputs_file,
                open_dmg=lambda p: opened.append(Path(p)),
                downloads_dir=dl_dir,
            )
            rc = up.run(launch=True, ui=ui)
            self.assertEqual(rc, 4)
            self.assertEqual(ui.saw_plan.kind, "dmg")
            self.assertEqual(len(opened), 1)
            self.assertEqual(opened[0].read_bytes(), dmg_bytes)
            self.assertTrue(ui.progress_events)

    def test_cache_avoids_rehash(self):
        self.run_updater()
        cached = self.state()["cache"]["BakersfieldQuake/progs.dat"]
        self.assertEqual(cached[2], hashlib.sha256(V1["BakersfieldQuake/progs.dat"]).hexdigest())

    def test_legacy_tools_updater_cleaned_up_on_windows(self):
        legacy = self.root / "tools" / "bq-update.exe"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(b"old v1 updater")
        self.run_updater()
        if os.name == "nt":
            self.assertFalse(legacy.exists())

    def test_no_update_env(self):
        os.environ["BQ_NO_UPDATE"] = "1"
        try:
            self.assertEqual(self.run_updater("--launch"), 0)
            self.assertFalse((self.root / ".bq").exists())
        finally:
            del os.environ["BQ_NO_UPDATE"]

    def test_truncated_local_header_does_not_hang(self):
        self.run_updater()
        v2 = dict(V1, **{"BakersfieldQuake/progs.dat": b"progs v2" * 5000})
        zb = make_zip(v2)
        m = manifest_for(zb, f"{self.base}/2.zip", 2)
        RangeHandler.files["/2.zip"] = zb
        RangeHandler.files["/manifest.json"] = json.dumps(m).encode()

        class TruncatedHeaderResponse:
            def __init__(self, header_bytes):
                self._buf = io.BytesIO(header_bytes)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self, n=-1):
                return self._buf.read(n)

        orig_ranged = bq.Updater.ranged
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            info = z.getinfo("BAKOQUAKE/BakersfieldQuake/progs.dat")
        hdr30 = zb[info.header_offset:info.header_offset + 30]

        def patched_ranged(up_self, start, end):
            if start == info.header_offset:
                return TruncatedHeaderResponse(hdr30)
            return orig_ranged(up_self, start, end)

        bq.Updater.ranged = patched_ranged
        try:
            self.assertEqual(self.run_updater("--launch"), 4)
        finally:
            bq.Updater.ranged = orig_ranged
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(), V1["BakersfieldQuake/progs.dat"])
        self.assertEqual(self.state()["build"], 1)


if __name__ == "__main__":
    unittest.main()
