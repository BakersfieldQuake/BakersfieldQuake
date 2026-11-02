"""Textures for make_bklan_v5.py (bklan4: Golden West Casino added, the accuracy pass of 2026-10-31 night). bk5_* only,
written to BakersfieldQuake/textures (full size) and out/maps/bklan5.wad (quarter size, for qbsp's names and sizes).
    bk5_lsign5    launch pad board "TO GOLDEN WEST CASINO"
    bk5_tpsign4   teleport board "TELEPORT: GOLDEN WEST CASINO"
    bk5_bsign     the Bakersfield Sign's band with the letters standing plumb (the real ones do; bk_bsign leaned them)
    bk5_white     bright white stucco for the 118/120 front and the Manning St ranch houses (same size as bk_stucco)
    bk5_fascia    white smooth fascia with faint seams (same size as bk_fascia)
    bk5_ortiz     the lime ORTIZ Auto Body banner on the fascia
    bk5_cblogo    the round monogram on B45's E 21st face
    bk5_ambsign   AMBERTON PARK monument sign
    bk5_clubview  CLUB VIEW DR street blade (as bk3_manning)
usage: python build_v5_textures.py"""
import inspect
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402
import build_v3_textures as b3  # noqa: E402
_argv = sys.argv
sys.argv = [_argv[0], os.path.join(HERE, "ref_sources", "bklan_wmv_frames"), os.path.join(HERE, "ref_sources", "streetview_gallery1")]
import build_bklan_textures as b1  # noqa: E402  (reads its frame / gallery dirs from argv at import; only ref_v2 is used here)
sys.argv = _argv
from build_v4_textures import launch_sign  # noqa: E402

TEX = os.path.normpath(os.path.join(HERE, "..", "..", "textures"))
WAD5 = os.path.join(HERE, "out", "maps", "bklan5.wad")
HI = 4
CASINO = (96, 24, 118)            # the casino's purple


def sign_band_plumb(size):
    """build_bklan_textures.sign_band with the per-letter rotation taken out: the glyphs stand upright, only their
    baseline follows the arc (ref_v2/0.jpg, 14.jpg)."""
    src = inspect.getsource(b1.sign_band).replace("ang = math.degrees(math.atan(slope))", "ang = 0.0")
    src = src.replace("def sign_band(", "def _sign_band_plumb(")
    ns = dict(vars(b1))
    exec(src, ns)
    return ns["_sign_band_plumb"](size)


def white_stucco(size, base=(224, 218, 206)):
    im = Image.new("RGB", (size[0] * HI, size[1] * HI), base)
    return b3.noise(im, 7, seed=11)


def white_fascia(size):
    im = Image.new("RGB", (size[0] * HI, size[1] * HI), (228, 224, 214))
    d = ImageDraw.Draw(im)
    for x in range(0, size[0] * HI, 128 * HI // 4):
        d.line([(x, 0), (x, size[1] * HI)], fill=(206, 202, 192), width=2)
    return b3.noise(im, 4, seed=12)


def cb_logo():
    S = 512
    im = Image.new("RGB", (S, S), (150, 150, 148))
    d = ImageDraw.Draw(im)
    d.ellipse([16, 16, S - 17, S - 17], fill=(240, 240, 238), outline=(26, 40, 96), width=22)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/ariali.ttf", 300)
        fs = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 56)
    except OSError:
        f = fs = ImageFont.load_default()
    d.text((S / 2, S / 2 - 30), "CB", font=f, fill=(26, 40, 96), anchor="mm")
    d.text((S / 2, S - 92), "BODYWORKS", font=fs, fill=(26, 40, 96), anchor="mm")
    return b3.dim(im, 0.9)


def main():
    t = {"bk5_lsign5": launch_sign("TO GOLDEN WEST CASINO", CASINO),
         "bk5_tpsign4": b3.dim(b3.sign_board((1024, 320), CASINO, (240, 240, 235),
                                             [("TELEPORT", (0.08, 0.38), "arialbd.ttf", (255, 230, 120)),
                                              ("GOLDEN WEST CASINO", (0.44, 0.9), "arialbd.ttf", (255, 255, 255))])),
         "bk5_bsign": sign_band_plumb((512, 80)),
         "bk5_white": white_stucco((128, 128)),
         "bk5_fascia": white_fascia((128, 32)),
         "bk5_ortiz": b3.dim(b3.sign_board((512, 256), (118, 196, 40), (90, 150, 30),
                                           [("ORTIZ", (0.06, 0.52), "arialbd.ttf", (240, 120, 20)),
                                            ("Auto Body", (0.52, 0.80), "arialbd.ttf", (250, 230, 40)),
                                            ("(661) 555-0120", (0.80, 0.95), "arialbd.ttf", (30, 30, 30))]), 0.9),
         "bk5_cblogo": cb_logo(),
         "bk5_ambsign": b3.dim(b3.sign_board((512, 192), (186, 166, 126), (110, 80, 50),
                                             [("AMBERTON PARK", (0.14, 0.62), "arialbd.ttf", (70, 45, 25)),
                                              ("CITY OF BAKERSFIELD", (0.64, 0.88), "arialbd.ttf", (90, 65, 40))]), 0.9),
         "bk5_clubview": b3.dim(b3.sign_board((1024, 192), (14, 98, 52), (240, 240, 240),
                                              [("CLUB VIEW DR", (0.08, 0.88), "arialbd.ttf", (255, 255, 255))]), 0.9)}
    os.makedirs(os.path.dirname(WAD5), exist_ok=True)
    small = {}
    for nm, im in t.items():
        im.save(os.path.join(TEX, nm + ".png"))
        small[nm] = im.resize((max(16, -(-im.width // HI // 16) * 16), max(16, -(-im.height // HI // 16) * 16)), Image.LANCZOS)
    write_wad(WAD5, small)
    print("wrote", WAD5, len(small), "textures:", {k: v.size for k, v in small.items()})


if __name__ == "__main__":
    main()
