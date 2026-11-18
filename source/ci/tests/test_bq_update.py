"""Tests for tools/bq_update.py against a local HTTP server that honours Range (stock http.server does not).

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
spec.loader.exec_module(bq)


class RangeHandler(http.server.BaseHTTPRequestHandler):
    files = {}            # path -> bytes
    honour_range = True
    hits = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        type(self).hits.append((self.path, self.headers.get("Range")))
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
            info.extra = b"\xfe\xca\x04\x00abcd" if rel.endswith(".pk3") else b""  # extra field in the local header
            z.writestr(info, data)
    return buf.getvalue()


def manifest_for(zip_bytes, url, build):
    d = Path(tempfile.mkdtemp())
    (d / "p.zip").write_bytes(zip_bytes)
    out = subprocess.run([sys.executable, "-I", str(REPO / "source/ci/make_manifest.py"), str(d / "p.zip"), url,
                          str(build), f"b{build}"], capture_output=True, check=True, text=True).stdout
    return json.loads(out)


V1 = {
    "BakersfieldQuake/progs.dat": b"progs v1" * 5000,
    "BakersfieldQuake/bakersfield.pk3": os.urandom(300_000),
    "BakersfieldQuake/config.cfg": b"// BAKERSFIELD_SEED\n",
    "BakersfieldQuake/old_thing.cfg": b"bye\n",
    "darkplaces-sdl": b"\x7fELF engine v1",
}


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
        RangeHandler.files, RangeHandler.hits, RangeHandler.honour_range = {}, [], True
        self.root = Path(tempfile.mkdtemp())
        self.publish(V1, 1)
        with zipfile.ZipFile(io.BytesIO(RangeHandler.files["/1.zip"])) as z:   # install v1 as a player would
            for i in z.infolist():
                p = self.root / i.filename[len("BAKOQUAKE/"):]
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(z.read(i))

    def publish(self, files, build, tamper=None):
        zb = make_zip(files)
        RangeHandler.files[f"/{build}.zip"] = zb
        m = manifest_for(zb, f"{self.base}/{build}.zip", build)
        if tamper:
            tamper(m)
        RangeHandler.files["/manifest.json"] = json.dumps(m).encode()

    def run_updater(self, *extra):
        return bq.main(["--root", str(self.root), "--manifest-url", f"{self.base}/manifest.json", *extra])

    def state(self):
        return json.loads((self.root / ".bq/state.json").read_text())

    def test_first_run_matches_and_downloads_nothing(self):
        self.assertEqual(self.run_updater(), 0)
        self.assertEqual(self.state()["build"], 1)
        self.assertFalse([h for h in RangeHandler.hits if h[0] == "/1.zip"])

    def test_update_fetches_only_changed_files(self):
        self.run_updater()
        (self.root / "BakersfieldQuake/config.cfg").write_bytes(b"name rob\n")       # player-owned
        (self.root / "id1").mkdir()
        (self.root / "id1/pak0.pak").write_bytes(b"paks")                           # not in any manifest
        v2 = dict(V1)
        v2["BakersfieldQuake/progs.dat"] = b"progs v2" * 5000                         # deflated, changed
        v2["BakersfieldQuake/zz_karts.pk3"] = os.urandom(50_000)                      # stored, new, local extra
        v2["BakersfieldQuake/config.cfg"] = b"// BAKERSFIELD_SEED v2\n"
        del v2["BakersfieldQuake/old_thing.cfg"]
        self.publish(v2, 2)
        RangeHandler.hits = []
        self.assertEqual(self.run_updater("--check"), 10)
        self.assertEqual(self.run_updater(), 3)
        self.assertEqual(self.run_updater(), 0)
        for rel in ("BakersfieldQuake/progs.dat", "BakersfieldQuake/zz_karts.pk3"):
            self.assertEqual((self.root / rel).read_bytes(), v2[rel])
        self.assertEqual((self.root / "BakersfieldQuake/config.cfg").read_bytes(), b"name rob\n")
        self.assertEqual((self.root / "id1/pak0.pak").read_bytes(), b"paks")
        self.assertFalse((self.root / "BakersfieldQuake/old_thing.cfg").exists())
        self.assertEqual(self.state()["build"], 2)
        if os.name != "nt":
            self.assertTrue(os.access(self.root / "darkplaces-sdl", os.X_OK))
        # the 300 KB base pk3 was never downloaded: every zip read is far smaller than it
        sizes = [int(r.split("-")[1]) - int(r.split("=")[1].split("-")[0]) for p, r in RangeHandler.hits
                 if p == "/2.zip" and r]
        self.assertTrue(sizes and max(sizes) < 200_000, sizes)
        self.assertEqual(self.run_updater("--check"), 0)

    def test_bad_hash_keeps_old_version(self):
        self.run_updater()
        v2 = dict(V1, **{"BakersfieldQuake/progs.dat": b"evil"})

        def tamper(m):
            m["files"]["BakersfieldQuake/progs.dat"]["sha256"] = "0" * 64
        self.publish(v2, 2, tamper)
        self.assertEqual(self.run_updater(), 0)
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(), V1["BakersfieldQuake/progs.dat"])
        self.assertEqual(self.state()["build"], 1)

    def test_rollback_refused(self):
        self.publish(dict(V1, **{"BakersfieldQuake/progs.dat": b"new"}), 5)
        self.run_updater()
        self.publish(V1, 3)
        self.run_updater()
        self.assertEqual(self.state()["build"], 5)
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(), b"new")

    def test_offline_and_no_range(self):
        self.assertEqual(bq.main(["--root", str(self.root), "--manifest-url", "http://127.0.0.1:9/m.json"]), 0)
        self.run_updater()
        self.publish(dict(V1, **{"BakersfieldQuake/progs.dat": b"v2"}), 2)
        RangeHandler.honour_range = False
        self.assertEqual(self.run_updater(), 0)
        self.assertEqual((self.root / "BakersfieldQuake/progs.dat").read_bytes(), V1["BakersfieldQuake/progs.dat"])
        self.assertEqual(self.state()["build"], 1)

    def test_cache_avoids_rehash(self):
        self.run_updater()
        cached = self.state()["cache"]["BakersfieldQuake/progs.dat"]
        self.assertEqual(cached[2], hashlib.sha256(V1["BakersfieldQuake/progs.dat"]).hexdigest())

    def test_no_update_env(self):
        os.environ["BQ_NO_UPDATE"] = "1"
        try:
            self.assertEqual(self.run_updater(), 0)
            self.assertFalse((self.root / ".bq").exists())
        finally:
            del os.environ["BQ_NO_UPDATE"]


if __name__ == "__main__":
    unittest.main()
