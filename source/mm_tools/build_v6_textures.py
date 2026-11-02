"""Textures for make_bklan_v6.py (bklan5: The Historic Bakersfield Fox Theater & Downtown combined inside bklan4).
bk6_* only, written to BakersfieldQuake/textures (full size) and out/maps/bklan6.wad (quarter size, for qbsp).
    bk6_lsign6    launch pad board "TO FOX THEATER"
    bk6_tpsign5   teleport board "TELEPORT / FOX THEATER"
usage: python build_v6_textures.py"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402
import build_v3_textures as b3  # noqa: E402
from build_v4_textures import launch_sign  # noqa: E402

TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
WAD6 = os.path.join(HERE, "out", "maps", "bklan6.wad")
HI = 4
FOX_CRIMSON = (146, 22, 30)       # Fox Theater's marquee crimson
FOX_GOLD = (248, 212, 108)        # Art Deco marquee gold


def main():
    t = {
        "bk6_lsign6": launch_sign("TO FOX THEATER", FOX_CRIMSON),
        "bk6_tpsign5": b3.dim(
            b3.sign_board(
                (1024, 320),
                FOX_CRIMSON,
                FOX_GOLD,
                [
                    ("TELEPORT", (0.08, 0.38), "arialbd.ttf", FOX_GOLD),
                    ("FOX THEATER", (0.44, 0.90), "arialbd.ttf", (255, 255, 255)),
                ],
            )
        ),
    }
    os.makedirs(os.path.dirname(WAD6), exist_ok=True)
    os.makedirs(TEX, exist_ok=True)
    small = {}
    for nm, im in t.items():
        im.save(os.path.join(TEX, nm + ".png"))
        small[nm] = im.resize(
            (max(16, -(-im.width // HI // 16) * 16), max(16, -(-im.height // HI // 16) * 16)),
            Image.LANCZOS,
        )
    # Include the 4 Daniel meme wall poster textures from BakersfieldQuake/textures/ in bklan6.wad
    for dan_nm in ("dan_4am", "dan_shaaa", "dan_webcam", "dan_ccc"):
        dan_path = os.path.join(TEX, dan_nm + ".png")
        if os.path.exists(dan_path):
            dim = Image.open(dan_path).convert("RGB")
            small[dan_nm] = dim.resize(
                (max(16, -(-dim.width // HI // 16) * 16), max(16, -(-dim.height // HI // 16) * 16)),
                Image.LANCZOS,
            )
    write_wad(WAD6, small)
    print("wrote", WAD6, len(small), "textures:", {k: v.size for k, v in small.items()})


if __name__ == "__main__":
    main()
