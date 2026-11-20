"""Build reproducible zz_johnbird.pk3 overlay with the 164-frame progs/john_bird_head.md3.

Reads all existing non-head entries from the base zz_johnbird.pk3 into memory
(progs/jb_*, scripts/jb_combat_props.shader, sound/john_bird/jb_*.wav), builds
(or loads via --md3) the 164-frame progs/john_bird_head.md3 from source, and
atomically writes a deterministic, reproducible pk3.

Usage:
  py -3.13 source/mm_tools/build_john_bird_pk3.py
  py -3.13 source/mm_tools/build_john_bird_pk3.py --base-pk3 zz_johnbird.pk3 --out-pk3 zz_johnbird.pk3
"""
import argparse
import hashlib
import os
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
DEFAULT_PK3 = REPO_ROOT / "zz_johnbird.pk3"

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import build_john_bird_head as JBH  # noqa: E402
import md3lib  # noqa: E402

STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}
DEFLATE_EXTS = {".md3", ".skin", ".shader", ".wav"}


def _validate_md3(md3_bytes: bytes) -> None:
    with tempfile.NamedTemporaryFile(suffix=".md3", delete=False) as tf:
        tf.write(md3_bytes)
        tmp_path = tf.name
    try:
        m = md3lib.read(tmp_path)
    finally:
        os.unlink(tmp_path)
    assert m["nframes"] == JBH.TOTAL_FRAMES, f"Expected {JBH.TOTAL_FRAMES} frames, got {m['nframes']}"
    s_names = [s["name"] for s in m["surfaces"]]
    assert s_names == ["head", "hair_breezy", "wings_bird"], f"Unexpected surfaces: {s_names}"


def _write_reproducible_pk3(out_pk3: Path, entries: dict[str, bytes]) -> None:
    out_pk3.parent.mkdir(parents=True, exist_ok=True)
    tmp_pk3 = out_pk3.with_suffix(".pk3.tmp")
    if tmp_pk3.exists():
        tmp_pk3.unlink()

    with zipfile.ZipFile(tmp_pk3, "w") as zf:
        for arcname in sorted(entries.keys()):
            data = entries[arcname]
            ext = Path(arcname).suffix.lower()
            zi = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            zi.create_system = 3
            zi.external_attr = 0o644 << 16
            if ext in STORE_EXTS:
                zf.writestr(zi, data, compress_type=zipfile.ZIP_STORED)
            elif ext in DEFLATE_EXTS:
                zf.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
            else:
                zf.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    os.replace(tmp_pk3, out_pk3)


def build_zz_johnbird(base_pk3: Path, out_pk3: Path, md3_path: Path | None = None) -> Path:
    if not base_pk3.is_file():
        raise FileNotFoundError(f"Base zz_johnbird.pk3 not found: {base_pk3}")

    # Load all existing non-head entries into memory before atomically replacing out_pk3
    entries: dict[str, bytes] = {}
    with zipfile.ZipFile(base_pk3, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if info.filename == "progs/john_bird_head.md3":
                continue
            entries[info.filename] = zf.read(info.filename)

    if md3_path is not None:
        if not md3_path.is_file():
            raise FileNotFoundError(f"MD3 file not found: {md3_path}")
        head_md3_bytes = md3_path.read_bytes()
    else:
        with tempfile.TemporaryDirectory(prefix="zz_johnbird_build_") as tmp:
            built_md3 = Path(JBH.build_john_bird_model(out_dir=tmp, render_verify=False, md3_only=True))
            head_md3_bytes = built_md3.read_bytes()

    _validate_md3(head_md3_bytes)
    entries["progs/john_bird_head.md3"] = head_md3_bytes

    _write_reproducible_pk3(out_pk3, entries)
    sha256 = hashlib.sha256(out_pk3.read_bytes()).hexdigest()
    print(f"Built {out_pk3}: {len(entries)} entries ({out_pk3.stat().st_size:,} bytes) sha256={sha256}")
    return out_pk3


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Build reproducible zz_johnbird.pk3 overlay.")
    parser.add_argument("--base-pk3", default=str(DEFAULT_PK3), help="Input base zz_johnbird.pk3 to preserve non-head entries from")
    parser.add_argument("--out-pk3", default=str(DEFAULT_PK3), help="Output pk3 path (default: g:/Quake/Combat/BakersfieldQuake/zz_johnbird.pk3)")
    parser.add_argument("--md3", default=None, help="Optional pre-built 164-frame john_bird_head.md3 (default: build fresh from source)")
    args = parser.parse_args(argv)

    base_pk3 = Path(args.base_pk3).resolve()
    out_pk3 = Path(args.out_pk3).resolve()
    md3_path = Path(args.md3).resolve() if args.md3 else None
    build_zz_johnbird(base_pk3, out_pk3, md3_path=md3_path)


if __name__ == "__main__":
    main()
