"""Builds zz_karts.pk3: reproducible go-karts overlay (progs/gokart_1..6 + driver + textures + shader).

python -I source/mm_tools/build_gokart_pk3.py <path to bakersfield.pk3> [output pk3]

Generates all 6 procedural go-karts (progs/gokart_1..6.md3, .md3_0.skin, progs/gk*.png) and the
seated Quake Ranger driver (progs/gokart_driver.md3, .md3_0.skin, progs/gk_driver.png from
bakersfield.pk3:progs/player_id1.mdl) inside a clean temporary directory, combines them with
scripts/gokart.shader, and writes a deterministic, reproducible pk3 (default: zz_karts.pk3 next to
bakersfield.pk3).
"""
import argparse
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
SHADER_SRC = REPO_ROOT / "scripts" / "gokart.shader"

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import gokart_1  # noqa: E402
import gokart_2  # noqa: E402
import gokart_3  # noqa: E402
import gokart_4  # noqa: E402
import gokart_5  # noqa: E402
import gokart_6  # noqa: E402
import gokart_driver  # noqa: E402
import gokart_shell  # noqa: E402

STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}
DEFLATE_EXTS = {".md3", ".skin", ".shader"}


def _validate_assets(progs_dir: Path, shader_text: str) -> None:
    expected_models = [f"gokart_{i}.md3" for i in range(1, 7)] + ["gokart_driver.md3", "gokart_shell.md3"]
    for name in expected_models:
        assert (progs_dir / name).is_file(), f"Missing generated model: {name}"
        assert (progs_dir / f"{name}_0.skin").is_file(), f"Missing generated skin: {name}_0.skin"
    for s_idx in (1, 2):
        assert (progs_dir / f"gokart_shell.md3_{s_idx}.skin").is_file(), f"Missing generated skin: gokart_shell.md3_{s_idx}.skin"

    defined_shaders = set(re.findall(r"^(progs/gk\S+)", shader_text, re.MULTILINE))
    used_shaders = set()
    for skin in sorted(progs_dir.glob("*.skin")):
        for line in skin.read_text(encoding="ascii").splitlines():
            if "," in line:
                used_shaders.add(line.split(",", 1)[1].strip())
    missing_shaders = sorted(used_shaders - defined_shaders)
    assert not missing_shaders, f"Shaders referenced by .skin missing in gokart.shader: {missing_shaders}"

    map_refs = set(re.findall(r"^\s*map\s+(progs/gk\S+)", shader_text, re.MULTILINE))
    for tex_ref in sorted(map_refs):
        png_name = Path(tex_ref).name + ".png"
        assert (progs_dir / png_name).is_file(), f"Missing texture for shader {tex_ref}: {png_name}"


def _collect_entries(progs_dir: Path, shader_bytes: bytes) -> dict[str, bytes]:
    entries: dict[str, bytes] = {}
    for p in sorted(progs_dir.iterdir()):
        if not p.is_file():
            continue
        name = p.name
        is_kart_asset = (
            (name.startswith("gokart_") and (name.endswith(".md3") or name.endswith(".skin")))
            or (name.startswith("gk") and name.endswith(".png"))
        )
        if not is_kart_asset:
            continue
        entries[f"progs/{name}"] = p.read_bytes()
    entries["scripts/gokart.shader"] = shader_bytes
    return entries


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


def build_zz_karts(bakersfield_pk3: Path, out_pk3: Path) -> Path:
    if not bakersfield_pk3.is_file():
        raise FileNotFoundError(f"bakersfield.pk3 not found: {bakersfield_pk3}")
    if not SHADER_SRC.is_file():
        raise FileNotFoundError(f"gokart.shader not found: {SHADER_SRC}")

    shader_text = SHADER_SRC.read_text(encoding="ascii").replace("\r\n", "\n")
    shader_bytes = shader_text.encode("ascii")

    with tempfile.TemporaryDirectory(prefix="zz_karts_build_") as tmp:
        progs_dir = Path(tmp) / "progs"
        progs_dir.mkdir(parents=True, exist_ok=True)
        p_str = str(progs_dir)

        gokart_1.main(progs_dir=p_str, meta_dir=None)
        gokart_2.build_gokart_2(progs_dir=p_str, meta_dir=None)
        gokart_3.build_gokart_3(progs_dir=p_str, meta_dir=None)
        gokart_4.main(progs_dir=p_str, meta_dir=None)
        gokart_5.build_gokart_5(progs_dir=p_str, meta_dir=None)
        gokart_6.build_gokart_6(progs_dir=p_str, meta_dir=None)
        gokart_driver.build_driver_md3(
            progs_dir=p_str,
            meta_dir=None,
            bakersfield_pk3=str(bakersfield_pk3),
        )
        gokart_shell.main(progs_dir=p_str, meta_dir=None)

        _validate_assets(progs_dir, shader_text)
        entries = _collect_entries(progs_dir, shader_bytes)
        _write_reproducible_pk3(out_pk3, entries)

    print(f"Built {out_pk3}: {len(entries)} entries ({out_pk3.stat().st_size:,} bytes)")
    return out_pk3


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Build reproducible zz_karts.pk3 overlay from source.")
    parser.add_argument("bakersfield_pk3", help="Path to bakersfield.pk3")
    parser.add_argument("output_pk3", nargs="?", default=None, help="Output pk3 path (default: <bakersfield.pk3 dir>/zz_karts.pk3)")
    args = parser.parse_args(argv)

    src_pk3 = Path(args.bakersfield_pk3).resolve()
    out_pk3 = Path(args.output_pk3).resolve() if args.output_pk3 else src_pk3.with_name("zz_karts.pk3")
    build_zz_karts(src_pk3, out_pk3)


if __name__ == "__main__":
    main()
