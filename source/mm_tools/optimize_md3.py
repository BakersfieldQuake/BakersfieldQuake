"""Strip provably unplayed animation frames from skyveh_v3.md3 and jw_air_v1.md3.
Originals are backed up in G:\\Quake\\Combat\\_bakersfield_dev\\orig_md3_tex\\.
(Full 2048x2048 PNG textures on veh_van_* and megaman.png are preserved at native resolution.)
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import md3lib

ROOT = r"G:\Quake\Combat"
MOD = os.path.join(ROOT, "BakersfieldQuake")
PROGS = os.path.join(MOD, "progs")
STAGED_PROGS = os.path.join(ROOT, "_bakersfield_dev", "staged_assets", "progs")
BACKUP_DIR = os.path.join(ROOT, "_bakersfield_dev", "orig_md3_tex")


def _resolve_progs_target(filename: str) -> str:
    p_mod = os.path.join(PROGS, filename)
    if os.path.isfile(p_mod):
        return p_mod
    p_staged = os.path.join(STAGED_PROGS, filename)
    if os.path.isfile(p_staged):
        return p_staged
    return p_mod


def slice_md3_frames(filename: str, keep_indices: list[int]):
    src = _resolve_progs_target(filename)
    bak = os.path.join(BACKUP_DIR, filename)
    if not os.path.isfile(bak):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copy2(src, bak)
    m = md3lib.read(bak)
    old_nf = m["nframes"]
    for s in m["surfaces"]:
        s["frames"] = [s["frames"][i] for i in keep_indices]
    md3lib.write(src, m)
    b_sz = os.path.getsize(bak)
    a_sz = os.path.getsize(src)
    print(f"  {filename:24s}: {old_nf:2d}f -> {len(keep_indices):2d}f | {b_sz/1048576:6.2f} MB -> {a_sz/1048576:6.2f} MB")


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    # skyveh_v3.md3 only ever plays fly_cruise (0..15) in bklan_movers.qc and intro_director.qc
    slice_md3_frames("skyveh_v3.md3", list(range(0, 16)))


if __name__ == "__main__":
    main()
