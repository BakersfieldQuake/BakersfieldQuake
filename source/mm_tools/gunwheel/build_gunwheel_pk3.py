"""Zip the Gun Wheel icons (assets/*.png) into zz_gunwheel.pk3 as gfx/gunwheel/<name>.png.

    python3 -I source/mm_tools/gunwheel/build_gunwheel_pk3.py <out.pk3>

Standard library only, byte-identical for the same icons. The icons are made by render_icons.py.
"""
import glob
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
COUNT = 18      # one per wheel slot (source/qc_combat_decomp/csqc/gunwheel.qc)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    icons = sorted(glob.glob(os.path.join(HERE, "assets", "*.png")))
    if len(icons) != COUNT:
        sys.exit("expected %d icons, found %d" % (COUNT, len(icons)))
    with zipfile.ZipFile(sys.argv[1], "w") as z:
        for path in icons:
            info = zipfile.ZipInfo("gfx/gunwheel/" + os.path.basename(path), date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            with open(path, "rb") as f:
                z.writestr(info, f.read())
    print("%s: %d icons" % (sys.argv[1], len(icons)))


if __name__ == "__main__":
    main()
