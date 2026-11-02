"""Build mystery_box_monster_vote.html (self-contained) from mbox_vote_template.html + the vote_thumbs PNGs.
Run: python build_mbox_vote.py      (needs PIL; run make_vote_thumbs.py first if the thumbs are missing)
"""
import base64
import io
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM = os.path.dirname(HERE)
MOD = os.path.dirname(os.path.dirname(MM))
THUMBS = os.path.join(MM, "out", "mystery_box", "vote_thumbs")
OUT = os.path.join(MOD, "mystery_box_monster_vote.html")

# (id, kind, name, thumb file)  -- ids are fixed by the game code (mb_pool)
ROSTER = [
    (1, "3D", "Mega Man Contraption", "01_megaman_contraption.png"),
    (2, "3D", "Suit Rider on Bar & Wheels", "02_suit_rider.png"),
    (3, "3D", "Exotic Pink Supercar", "03_pink_supercar.png"),
    (4, "3D", "Squat Rider on Bar & Wheels", "04_squat_rider.png"),
    (5, "3D", "NetSend 90s CRT PC", "05_netsend_pc.png"),
    (6, "3D", "Golden West Casino Horse", "06_gw_horse.png"),
    (7, "3D", "Big-Ears Head", "07_bigears_head.png"),
    (8, "3D", "Larry's Warehouse Forklift", "08_forklift.png"),
    (9, "2D", "Wheelman", "09_wheelman.png"),
    (10, "2D", "JessKart Racer", "10_jesskart.png"),
    (11, "2D", "Kyle the Scissor Man", "11_kyle_scissors.png"),
    (12, "2D", "Earhead", "12_earhead.png"),
    (13, "2D", "Pickle Surprise", "13_pickle_surprise.png"),
    (14, "2D", "Friend Rob", "14_friend_rob.png"),
    (15, "2D", "John Wave Hand", "15_john_wave_hand.png"),
    (16, "2D", "Wheelman Rolling", "16_wheelman_rolling.png"),
]


def data_uri(path):
    im = Image.open(path).convert("RGBA")
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=86, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main():
    roster = [dict(id=i, kind=k, name=n, img=data_uri(os.path.join(THUMBS, f))) for i, k, n, f in ROSTER]
    tpl = open(os.path.join(HERE, "mbox_vote_template.html"), encoding="utf-8").read()
    marker = "/*ROSTER_JSON*/[]"
    assert marker in tpl
    blob = json.dumps(roster, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace(marker, blob)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(OUT, "%.2f MB" % (os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
