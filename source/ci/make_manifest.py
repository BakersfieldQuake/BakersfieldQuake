"""Writes the updater manifest for one platform package (see tools/bq_update.py and docs/updater-v2-plan.md).

Create mode:
  python -I make_manifest.py <package zip> <zip download URL> <build number> <version> [options]

Patch-DMG mode (updates macOS DMG metadata in an existing manifest-macos-app.json):
  python -I make_manifest.py --patch-manifest <manifest.json> [--output <out.json>] \
      --mac-inputs HASH --dmg-url URL --dmg-vps-url URL --dmg-size INT --dmg-sha256 HEX

Lists every file under BAKOQUAKE/ with its size and sha256. --only keeps just the files under the given prefixes
(relative to BAKOQUAKE/): the macOS app's manifest holds only the game data, since the app has its own engine.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = "BAKOQUAKE/"
# Seeds the player owns after first run: written only when missing, never overwritten.
INSTALL_ONLY = ["BakersfieldQuake/config.cfg"]
# Marked executable on macOS/Linux after an update (zip entries made on Windows carry no mode bits).
EXEC_NAMES = {"darkplaces-sdl", "darkplaces-dedicated", "bq-update"}
EXEC_SUFFIXES = (".sh", ".command")


def _apply_dmg_fields(manifest, a):
    if a.mac_inputs:
        manifest["mac_inputs"] = a.mac_inputs
    if a.dmg_url:
        manifest["dmg_url"] = a.dmg_url
    if a.dmg_vps_url:
        manifest["dmg_vps_url"] = a.dmg_vps_url
    if a.dmg_size is not None and a.dmg_size > 0:
        manifest["dmg_size"] = int(a.dmg_size)
    if a.dmg_sha256:
        manifest["dmg_sha256"] = a.dmg_sha256
    return manifest


def build_manifest(zip_path, url, build, version, only=(), notes="", vps_base="",
                   mac_inputs="", dmg_url="", dmg_vps_url="", dmg_size=None, dmg_sha256=""):
    files, execs = {}, []
    with zipfile.ZipFile(zip_path) as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            if info.is_dir() or not info.filename.startswith(ROOT):
                continue
            rel = info.filename[len(ROOT):]
            if only and not rel.startswith(tuple(only)):
                continue
            h = hashlib.sha256()
            with z.open(info) as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            files[rel] = {"size": info.file_size, "sha256": h.hexdigest()}
            name = rel.rsplit("/", 1)[-1]
            if (info.external_attr >> 16) & 0o111 or name in EXEC_NAMES or name.endswith(EXEC_SUFFIXES):
                execs.append(rel)

    manifest = {
        "schema": 1,
        "build": int(build),
        "version": version,
        "zip": url,
        "root": ROOT,
        "files": files,
        "exec": execs,
        "install_only": [p for p in INSTALL_ONLY if p in files],
    }
    if notes:
        manifest["notes"] = notes
    if vps_base:
        manifest["vps_base"] = vps_base.rstrip("/")
    if mac_inputs:
        manifest["mac_inputs"] = mac_inputs
    if dmg_url:
        manifest["dmg_url"] = dmg_url
    if dmg_vps_url:
        manifest["dmg_vps_url"] = dmg_vps_url
    if dmg_size is not None and int(dmg_size) > 0:
        manifest["dmg_size"] = int(dmg_size)
    if dmg_sha256:
        manifest["dmg_sha256"] = dmg_sha256
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build or patch BAKOQUAKE updater manifest JSON")
    ap.add_argument("positional", nargs="*", help="<zip> <url> <build> <version> (when not using --patch-manifest)")
    ap.add_argument("--only", action="append", default=[], help="keep only files starting with this prefix")
    ap.add_argument("--notes", default="", help="short human-readable summary of changes")
    ap.add_argument("--vps-base", default="", help="base HTTPS URL for VPS fallback (e.g. https://.../updates)")
    ap.add_argument("--mac-inputs", default="", help="macOS bundle inputs hash")
    ap.add_argument("--dmg-url", default="", help="GitHub download URL for macOS DMG")
    ap.add_argument("--dmg-vps-url", default="", help="VPS fallback URL for macOS DMG")
    ap.add_argument("--dmg-size", type=int, default=None, help="byte size of macOS DMG")
    ap.add_argument("--dmg-sha256", default="", help="sha256 hex digest of macOS DMG")
    ap.add_argument("--patch-manifest", type=Path, default=None, help="existing manifest JSON to patch with DMG metadata")
    ap.add_argument("--output", "-o", type=Path, default=None, help="write JSON to file instead of stdout")
    a = ap.parse_args(argv)

    if a.patch_manifest is not None:
        manifest = json.loads(a.patch_manifest.read_text("utf-8"))
        _apply_dmg_fields(manifest, a)
    else:
        if len(a.positional) != 4:
            ap.error("expected 4 positional args: <package zip> <zip download URL> <build number> <version>")
        path, url, build, version = a.positional
        manifest = build_manifest(
            path, url, build, version,
            only=a.only,
            notes=a.notes,
            vps_base=a.vps_base,
            mac_inputs=a.mac_inputs,
            dmg_url=a.dmg_url,
            dmg_vps_url=a.dmg_vps_url,
            dmg_size=a.dmg_size,
            dmg_sha256=a.dmg_sha256,
        )

    out_text = json.dumps(manifest, indent=1) + "\n"
    if a.output is not None:
        a.output.write_text(out_text, "utf-8")
    else:
        sys.stdout.write(out_text)


if __name__ == "__main__":
    main()
