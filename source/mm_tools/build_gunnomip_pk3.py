"""Builds zz_gunnomip.pk3: three gun view models drawn without mipmaps, like the milky and pickle guns already are.

    python -I source/mm_tools/build_gunnomip_pk3.py <path to bakersfield.pk3> [output pk3]

Why: the dookie, green-jar and robhead-drone view models are one PNG per animation frame (114 + 112 + 2 x 112 frames)
and their shaders let the engine build mipmaps for every frame. A view model is drawn at roughly 1:1, so those
mipmaps are never used, but they cost about 52 MB of texture memory and about 120 MB of process commit on every map
(docs/gunframes-atlas-2026-11-18.md). scripts/milkyvm.shader and scripts/picklevm.shader already say "nomipmaps".

What it does: copies scripts/dookievm.shader, scripts/greenjarvm.shader and scripts/rh_dronevm.shader out of
bakersfield.pk3 and adds a "nomipmaps" line after "cull none" in every shader, the same place milkyvm.shader has it.
Nothing else changes. The overlay's file replaces the base file of the same name: the engine lists each shader file
name once and loads it from the highest-priority pack (a second definition of a shader name would be ignored).
No textures are copied, so the pack is about 55 KB.

Do not ship this together with zz_gunframes.pk3 (build_gunframe_atlas_pk3.py): both replace these three files,
zz_gunnomip sorts later and would win, and the atlas shaders already carry "nomipmaps".

Reproducible: needs only the standard library; entries are sorted, dated 1980-01-01, with fixed attributes, and
stored (not deflated), so the bytes do not depend on the zlib version either.
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path

SHADER_FILES = ("scripts/dookievm.shader", "scripts/greenjarvm.shader", "scripts/rh_dronevm.shader")
SCRIPT_NAME = "source/mm_tools/build_gunnomip_pk3.py"
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16

# a top-level shader block: name line, "{", then "\tcull none" as its first keyword
BLOCK_HEAD = re.compile(r"^(\S+)\n\{\n\tcull none\n", re.M)


def add_nomipmaps(name, text):
    if "nomipmaps" in text:
        sys.exit(f"{name} already has nomipmaps: the base pack changed, check this builder")
    blocks = len(re.findall(r"^\{$", text, re.M))
    out, n = BLOCK_HEAD.subn(lambda m: m.group(0) + "\tnomipmaps\n", text)
    if n != blocks or n == 0:
        sys.exit(f"{name}: {blocks} shader blocks but {n} start with 'cull none'; check this builder")
    if out.replace("\tnomipmaps\n", "") != text:
        sys.exit(f"{name}: the rewrite changed more than the added lines")
    header = f"// zz_gunnomip.pk3: {name} from bakersfield.pk3 with nomipmaps added by {SCRIPT_NAME}\n"
    return header + out, n


def write_pk3(out_path, entries):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".pk3.tmp")
    with zipfile.ZipFile(tmp, "w") as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, entries[name])
    tmp.replace(out_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("base_pk3", type=Path)
    ap.add_argument("out_pk3", type=Path, nargs="?")
    args = ap.parse_args()
    out_pk3 = args.out_pk3 or args.base_pk3.with_name("zz_gunnomip.pk3")

    with zipfile.ZipFile(args.base_pk3) as z:
        entries = {}
        for name in SHADER_FILES:
            text = z.read(name).decode("latin-1")
            new, n = add_nomipmaps(name, text)
            entries[name] = new.encode("latin-1")
            print(f"{name}: nomipmaps added to {n} shaders")
    write_pk3(out_pk3, entries)
    print(f"wrote {out_pk3} ({out_pk3.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
