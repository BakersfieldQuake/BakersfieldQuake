"""Unit tests for source/ci/sync_vps.py."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("sync_vps", REPO / "source" / "ci" / "sync_vps.py")
sv = importlib.util.module_from_spec(spec)
sys.modules["sync_vps"] = sv
spec.loader.exec_module(sv)


class SyncVpsTest(unittest.TestCase):
    def test_collect_missing_and_prune(self):
        h1 = "a" * 64
        h2 = "b" * 64
        h3 = "c" * 64
        h_old = "d" * 64

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            m1 = td / "manifest-windows-x64.json"
            m2 = td / "manifest-linux-x86_64.json"
            m1.write_text(json.dumps({
                "zip": "https://example/BAKOQUAKE.zip",
                "root": "BAKOQUAKE/",
                "files": {
                    "BakersfieldQuake/bakersfield.pk3": {"size": 100, "sha256": h1},
                    "zircon.exe": {"size": 10, "sha256": h2},
                },
            }), "utf-8")
            m2.write_text(json.dumps({
                "zip": "https://example/BAKOQUAKE-linux-x86_64.zip",
                "root": "BAKOQUAKE/",
                "files": {
                    "BakersfieldQuake/bakersfield.pk3": {"size": 100, "sha256": h1},
                    "darkplaces-sdl": {"size": 12, "sha256": h3},
                },
            }), "utf-8")

            needed = sv.collect_needed_blobs([m1, m2])
            self.assertEqual(set(needed.keys()), {h1, h2, h3})
            self.assertEqual(len(needed[h1]), 2)

            existing = {h1, h_old, "not-a-sha-file"}
            self.assertEqual(sv.compute_missing_hashes(needed.keys(), existing), [h2, h3])

            keep = sv.update_keep_state({"current": [h1, "e" * 64], "previous": [h_old]}, needed.keys())
            self.assertEqual(keep["current"], [h1, h2, h3])
            self.assertEqual(keep["previous"], [h1, "e" * 64])

            # Same-release re-sync must NOT overwrite previous with current.
            keep_same = sv.update_keep_state(keep, needed.keys())
            self.assertEqual(keep_same, keep)

            prune = sv.compute_prune_list(existing | {h2, h3}, keep)
            self.assertEqual(prune, [h_old])

    def test_skips_cleanly_when_unconfigured(self):
        old_host = os.environ.pop("VPS_SYNC_HOST", None)
        try:
            self.assertEqual(sv.main(["--manifests", "m.json", "--zips", "z.zip"]), 0)
        finally:
            if old_host is not None:
                os.environ["VPS_SYNC_HOST"] = old_host


if __name__ == "__main__":
    unittest.main()
