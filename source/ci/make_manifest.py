"""Writes the updater manifest for one platform package (see tools/bq_update.py and docs/auto-update-plan.md).

python -I make_manifest.py <package zip> <zip download URL> <build number> <version> > manifest-<platform>.json

Lists every file under BAKOQUAKE/ with its size and sha256. The zip URL must be the tag-specific one
(releases/download/<tag>/<zip>), so a manifest always points at the zip it was made from.
"""
import hashlib
import json
import sys
import zipfile

ROOT = "BAKOQUAKE/"
# Seeds the player owns after first run: written only when missing, never overwritten.
INSTALL_ONLY = ["BakersfieldQuake/config.cfg"]
# Marked executable on macOS/Linux after an update (zip entries made on Windows carry no mode bits).
EXEC_NAMES = {"darkplaces-sdl", "darkplaces-dedicated", "bq-update"}
EXEC_SUFFIXES = (".sh", ".command")


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    path, url, build, version = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    files, execs = {}, []
    with zipfile.ZipFile(path) as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            if info.is_dir() or not info.filename.startswith(ROOT):
                continue
            rel = info.filename[len(ROOT):]
            h = hashlib.sha256()
            with z.open(info) as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            files[rel] = {"size": info.file_size, "sha256": h.hexdigest()}
            name = rel.rsplit("/", 1)[-1]
            if (info.external_attr >> 16) & 0o111 or name in EXEC_NAMES or name.endswith(EXEC_SUFFIXES):
                execs.append(rel)
    manifest = {"schema": 1, "build": build, "version": version, "zip": url, "root": ROOT, "files": files,
                "exec": execs, "install_only": [p for p in INSTALL_ONLY if p in files]}
    json.dump(manifest, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
