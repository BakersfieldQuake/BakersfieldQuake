"""The Bakersfield Sign (the 1949 Union Ave arch, rebuilt over Sillect Ave in 1999), shared by make_bklan.py (geometry)
and build_bklan_textures.py (the band texture, drawn to match the geometry). Feet.

Measured: tower spacing from Google satellite (scale bar), heights and details from the user's photos of 2026-10-30
(the frontal photo at 0 s of 2026-10-30 22-56-37.mp4, the far view at 14 s, a semi trailer and the 30 x 36 in speed
limit sign for scale):
  towers 97 ft apart centre to centre, standing just outside the curbs of a 62 ft wide road
  tower shaft 9.5 ft square (base 10 ft), roof peak 31 ft, eaves 14 ft square at 29.3 ft
  arched pass-through in each face of the base: 4.2 ft wide, impost 7 ft, crown 8.6 ft, tan trim to 9.9 ft
  tan ledge 14.3-16.3 ft, city-seal medallion 6.4 ft across centred at 21.5 ft, tan cap band 26.4-28.9 ft
  arch band 7.5 ft deep, top edge 25.0 ft at the towers rising to 30.6 ft at the crown (level with the tower roofs),
  yellow with BAKERSFIELD in navy on both faces, letters about 4.7 ft tall"""

SPACING = 97.0            # tower centre to centre
HALF = SPACING / 2
SHAFT = 9.5
BASE = 10.0
DEPTH = 1.6               # thickness of the band (along the road)
ZT_END, ZT_CROWN = 25.0, 30.6
ZB_END, ZB_CROWN = 17.5, 23.1
ZMIN, ZMAX = 17.0, 31.0   # the band texture covers this height range over the full tower-centre span
LETTERS = "BAKERSFIELD"
LETTER_H = 4.7
LETTER_SPAN = 0.74        # the letters fill this share of the tower-centre span


def zt(s):
    """top edge height at distance s from the middle of the span"""
    return ZT_END + (ZT_CROWN - ZT_END) * (1 - (s / HALF) ** 2)


def zb(s):
    return ZB_END + (ZB_CROWN - ZB_END) * (1 - (s / HALF) ** 2)
