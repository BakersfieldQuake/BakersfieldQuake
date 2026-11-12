"""Pack BakersfieldQuake runtime assets (progs/, textures/, sound/, gfx/, scripts/, models/) into
BakersfieldQuake/bakersfield.pk3 for O(1) VFS lookup and compact LAN distribution.

Usage:
  python build_pk3.py           # Sync bakersfield.pk3 from staged_assets/ + loose overrides
                                # (if staged_assets/ is active, folds new loose overrides into staged_assets/)
  python build_pk3.py --stage   # Build bakersfield.pk3 and stage loose asset files into
                                # G:\\Quake\\Combat\\_bakersfield_dev\\staged_assets\\ (keeps empty dirs for generators)
  python build_pk3.py --unpack  # Restore staged loose asset files back into BakersfieldQuake/
"""
import fnmatch
import os
import shutil
import sys
import time
import zipfile

ROOT = r"G:\Quake\Combat"
MOD = os.path.join(ROOT, "BakersfieldQuake")
STAGED = os.path.join(ROOT, "_bakersfield_dev", "staged_assets")
PK3_OUT = os.path.join(MOD, "bakersfield.pk3")

ASSET_DIRS = ("progs", "textures", "sound", "gfx", "scripts", "models")  # models/: md3 skins (CS M4, DoD Thompson + Garand)
STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg", ".pk3", ".zip"}
SKIP_PATTERNS = (
    "*.bak*",
    "*.pre_*",
    "*_bak*",
    "*.tmp",
    "*.psd",
    "*.blend*",
    "*.xcf",
    "wheelman_actions.spr32",
)


def is_skipped(rel_posix: str) -> bool:
    name = rel_posix.rsplit("/", 1)[-1].lower()
    rel_low = rel_posix.lower()
    if rel_low == "gfx/env/bklan_old" or rel_low.startswith("gfx/env/bklan_old/"):
        return True
    for pat in SKIP_PATTERNS:
        if fnmatch.fnmatch(name, pat.lower()):
            return True
    return False


def collect_tree(base_dir: str) -> dict:
    """Return {rel_posix: abs_path} for ASSET_DIRS under base_dir."""
    found = {}
    if not os.path.isdir(base_dir):
        return found
    for sub in ASSET_DIRS:
        sub_abs = os.path.join(base_dir, sub)
        if not os.path.isdir(sub_abs):
            continue
        for dirpath, _, filenames in os.walk(sub_abs):
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, base_dir).replace("\\", "/")
                if is_skipped(rel):
                    continue
                found[rel] = full
    return found


def unpack_staged() -> None:
    if not os.path.isdir(STAGED):
        print("Nothing staged in", STAGED)
        return
    restored = 0
    for sub in ASSET_DIRS:
        s_dir = os.path.join(STAGED, sub)
        if not os.path.isdir(s_dir):
            continue
        for dirpath, _, filenames in os.walk(s_dir):
            for fn in filenames:
                src = os.path.join(dirpath, fn)
                rel = os.path.relpath(src, STAGED)
                dst = os.path.join(MOD, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                # Loose override in MOD is newer/custom -> keep MOD copy, remove stale staged copy
                if os.path.isfile(dst) and os.path.getmtime(dst) > os.path.getmtime(src) + 0.5:
                    os.remove(src)
                else:
                    shutil.move(src, dst)
                restored += 1
    print(f"Restored {restored} loose asset files into {MOD}")


def stage_loose_into_staged() -> int:
    os.makedirs(STAGED, exist_ok=True)
    moved = 0
    for sub in ASSET_DIRS:
        sub_abs = os.path.join(MOD, sub)
        os.makedirs(sub_abs, exist_ok=True)
        for dirpath, _, filenames in os.walk(sub_abs, topdown=False):
            for fn in filenames:
                src = os.path.join(dirpath, fn)
                rel = os.path.relpath(src, MOD).replace("\\", "/")
                if is_skipped(rel):
                    continue
                dst = os.path.join(STAGED, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.isfile(dst):
                    os.remove(dst)
                shutil.move(src, dst)
                moved += 1
            # Prune empty nested subdirectories while keeping top-level ASSET_DIRS intact for generator scripts
            if os.path.normcase(dirpath) != os.path.normcase(sub_abs):
                try:
                    if not os.listdir(dirpath):
                        os.rmdir(dirpath)
                except OSError:
                    pass
    return moved


def build_pk3(stage: bool = False) -> None:
    t0 = time.perf_counter()
    if stage:
        moved = stage_loose_into_staged()
        if moved:
            print(f"Staged {moved} loose asset files -> {STAGED}")

    entries = collect_tree(STAGED)
    # Loose files currently in MOD override staged_assets
    entries.update(collect_tree(MOD))

    if not entries:
        raise RuntimeError("No runtime assets found in staged_assets or BakersfieldQuake!")

    tmp_pk3 = PK3_OUT + ".tmp"
    if os.path.isfile(tmp_pk3):
        os.remove(tmp_pk3)

    raw_bytes = 0
    with zipfile.ZipFile(tmp_pk3, "w", allowZip64=True) as zf:
        for rel in sorted(entries.keys()):
            src = entries[rel]
            raw_bytes += os.path.getsize(src)
            ext = os.path.splitext(rel)[1].lower()
            if ext in STORE_EXTS:
                zf.write(src, rel, compress_type=zipfile.ZIP_STORED)
            else:
                zf.write(src, rel, compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)

    os.replace(tmp_pk3, PK3_OUT)
    pk3_bytes = os.path.getsize(PK3_OUT)
    dt = time.perf_counter() - t0
    print(
        f"Built {PK3_OUT}: {len(entries):,} files, "
        f"{raw_bytes / 1048576:.1f} MB raw -> {pk3_bytes / 1048576:.1f} MB pk3 in {dt:.1f}s"
    )


def main() -> None:
    if "--unpack" in sys.argv:
        unpack_staged()
        return
    build_pk3(stage=("--stage" in sys.argv))


if __name__ == "__main__":
    main()
