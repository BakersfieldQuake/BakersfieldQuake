"""Builds zz_wewcannon.pk3: adjusted 1st-person pose for progs/v_wewcannon.md3.

    python -I source/mm_tools/wew_cannon/build_wewcannon_pk3.py <path to bakersfield.pk3> [output pk3]

Never edits bakersfield.pk3. Reads progs/v_wewcannon.md3 from bakersfield.pk3, applies the
tuned 1st-person viewmodel placement around the frame-0 bounding-box center (matching
apply_viewmodel_edits.py), and writes a reproducible overlay pk3 (default: zz_wewcannon.pk3
next to bakersfield.pk3).

Reproducible: standard library + source/mm_tools/md3lib.py only; sorted entries, 1980-01-01
timestamp, fixed Unix permissions, and fixed deflate level.
"""
import argparse
import hashlib
import math
import os
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
if str(MM_TOOLS) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS))
import md3lib

ENTRY_PATH = "progs/v_wewcannon.md3"
ASSETS_DIR = HERE / "assets"
SOUND_FILES = (
    "wc_charge.wav",
    "wc_shoot.wav",
    "wc_scream.wav",
    "wc_lrun01.wav",
)
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16

POSE = {
    "pos": (-3.7, -0.87, 0.61),
    "rot": (0.0, 0.0, 0.5),
    "scale": 0.91,
}


def read_frame_names(md3_bytes: bytes) -> list[str]:
    nf, _, _, _, ofs_f = struct.unpack("<5i", md3_bytes[76:96])
    names = []
    for i in range(nf):
        o = ofs_f + 56 * i
        names.append(md3_bytes[o + 40:o + 56].split(b"\0", 1)[0].decode("ascii", "replace"))
    return names


def pivot_of(model: dict) -> tuple[float, float, float]:
    pts = [v for s in model["surfaces"] for v in s["frames"][0][0]]
    return tuple((min(p[k] for p in pts) + max(p[k] for p in pts)) * 0.5 for k in range(3))


def make_xform(pivot, pos, rot, scale):
    r, p, y = (math.radians(a) for a in rot)
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)

    def rotate(v):
        x, yy, z = v
        yy, z = yy * cr - z * sr, yy * sr + z * cr          # roll
        x, z = x * cp - z * sp, x * sp + z * cp              # pitch (nose up)
        x, yy = x * cy - yy * sy, x * sy + yy * cy           # yaw (left)
        return (x, yy, z)

    def point(v):
        d = rotate(tuple((v[k] - pivot[k]) * scale for k in range(3)))
        return tuple(pivot[k] + d[k] + pos[k] for k in range(3))

    return point, rotate


def transform_md3_bytes(raw_bytes: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        in_p = os.path.join(td, "in.md3")
        out_p = os.path.join(td, "out.md3")
        with open(in_p, "wb") as f:
            f.write(raw_bytes)
        m = md3lib.read(in_p)
        m["frame_names"] = read_frame_names(raw_bytes)
        point, rotate = make_xform(pivot_of(m), POSE["pos"], POSE["rot"], POSE["scale"])
        for s in m["surfaces"]:
            s["frames"] = [([point(v) for v in vv], [rotate(n) for n in nn]) for vv, nn in s["frames"]]
        md3lib.write(out_p, m)
        with open(out_p, "rb") as f:
            return f.read()


def write_pk3(out_path: Path, entries: dict[str, bytes]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".pk3.tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w") as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.create_system = 3
            info.external_attr = FILE_ATTR
            zf.writestr(info, entries[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    tmp.replace(out_path)


def build_zz_wewcannon(base_pk3: Path, out_pk3: Path) -> Path:
    if not base_pk3.is_file():
        raise FileNotFoundError(f"base pk3 not found: {base_pk3}")
    with zipfile.ZipFile(base_pk3) as z:
        raw = z.read(ENTRY_PATH)
    entries = {ENTRY_PATH: transform_md3_bytes(raw)}
    for fn in SOUND_FILES:
        src = ASSETS_DIR / fn
        if not src.is_file():
            raise FileNotFoundError(f"missing wewcannon sound asset: {src}")
        entries[f"sound/wcannon/{fn}"] = src.read_bytes()
    write_pk3(out_pk3, entries)
    return out_pk3


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base_pk3", type=Path)
    ap.add_argument("out_pk3", type=Path, nargs="?")
    args = ap.parse_args(argv)
    out_pk3 = args.out_pk3 or args.base_pk3.with_name("zz_wewcannon.pk3")
    build_zz_wewcannon(args.base_pk3, out_pk3)
    sha = hashlib.sha256(out_pk3.read_bytes()).hexdigest()
    print(f"wrote {out_pk3} ({out_pk3.stat().st_size} bytes, sha256={sha[:16]}...)")


if __name__ == "__main__":
    main()
