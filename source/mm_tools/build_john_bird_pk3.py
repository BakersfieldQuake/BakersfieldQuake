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
import struct
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


def _md3_same_within_noise(old: bytes, new: bytes) -> bool:
    """True when two MD3s have the same layout and differ only by last-digit float noise.

    The head is rebuilt with numpy, and GitHub runners with different CPUs round a few
    values differently (seen: 9 bytes out of 10.5 MB, one vertex step or one float ulp).
    Every structural byte must match; frame floats and texture coordinates may differ by
    1e-3, packed vertex positions and normal angles by one step.
    """
    import numpy as np

    if len(old) != len(new) or old[:108] != new[:108]:
        return False
    if old == new:
        return True
    hdr = struct.unpack("<4si64s9i", old[:108])
    nf, ns, ofs_f, ofs_s = hdr[4], hdr[6], hdr[8], hdr[10]
    a = np.frombuffer(old, dtype=np.uint8)
    b = np.frombuffer(new, dtype=np.uint8)
    checked = np.zeros(len(old), dtype=bool)

    def floats_close(start: int, count: int) -> bool:
        fa = a[start:start + 4 * count].view("<f4")
        fb = b[start:start + 4 * count].view("<f4")
        checked[start:start + 4 * count] = True
        return bool(np.all(np.abs(fa.astype(np.float64) - fb.astype(np.float64)) <= 1e-3))

    for i in range(nf):                      # frame: 10 floats (mins, maxs, origin, radius) + name
        if not floats_close(ofs_f + 56 * i, 10):
            return False
    o = ofs_s
    for _ in range(ns):
        sh = struct.unpack("<4s64s10i", old[o:o + 108])
        if old[o:o + 108] != new[o:o + 108]:
            return False
        snf, nv, o_st, o_xyz, o_end = sh[3], sh[5], sh[9], sh[10], sh[11]
        if not floats_close(o + o_st, 2 * nv):
            return False
        start, count = o + o_xyz, snf * nv
        xa = a[start:start + 8 * count].view("<i2").reshape(count, 4)
        xb = b[start:start + 8 * count].view("<i2").reshape(count, 4)
        if np.any(np.abs(xa[:, :3].astype(np.int32) - xb[:, :3].astype(np.int32)) > 1):
            return False
        na = a[start:start + 8 * count].reshape(count, 8)[:, 6:8].astype(np.int32)
        nb = b[start:start + 8 * count].reshape(count, 8)[:, 6:8].astype(np.int32)
        dn = np.abs(na - nb)
        if np.any(np.minimum(dn, 256 - dn) > 1):      # normal angles wrap at 256
            return False
        checked[start:start + 8 * count] = True
        o += o_end
    return bool(np.all((a == b) | checked))  # everything not checked above must be identical


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
    base_head = None
    with zipfile.ZipFile(base_pk3, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if info.filename == "progs/john_bird_head.md3":
                base_head = zf.read(info.filename)
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
    # Keep the shipped head when the rebuild only differs by CPU rounding noise, so players
    # do not re-download 11 MB for a model that did not change.
    if base_head is not None and base_head != head_md3_bytes and _md3_same_within_noise(base_head, head_md3_bytes):
        print("john_bird_head.md3: rebuild differs from the base only by rounding noise; keeping the base bytes")
        head_md3_bytes = base_head
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
