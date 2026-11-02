"""NetSend PC: the sending-loop screen as a Windows 98 "Messenger Service" dialog (owner's review 2026-10-31 16:03,
8:54-9:17: "the screen needs to say Sending NET SEND ... it should look like a Windows 98 screen").
Rewrites progs/netsend_s_l00..l15.png (the 16 frames of the progs/netsend_scr_loop animmap, 512x256). The old green
DOS frames are kept in out/netsend_orig_screens. Baked at DIM of full brightness: the game shows model textures ~2.5x.
usage: python build_netsend_win98.py"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROGS = os.path.join(HERE, "..", "..", "progs")
DIM = 0.5
F = "C:/Windows/Fonts/"
title_f = ImageFont.truetype(F + "tahomabd.ttf", 17)
body_f = ImageFont.truetype(F + "tahoma.ttf", 17)
big_f = ImageFont.truetype(F + "tahomabd.ttf", 22)
small_f = ImageFont.truetype(F + "tahoma.ttf", 13)


def c(r, g, b):
    return (int(r * DIM), int(g * DIM), int(b * DIM))


TEAL, GREY, WHITE, DARK, BLACK = c(0, 128, 128), c(192, 192, 192), c(255, 255, 255), c(128, 128, 128), (0, 0, 0)
NAVY, BLUE2 = c(0, 0, 128), c(16, 132, 208)


def bevel(d, x0, y0, x1, y1, raised=True):
    a, b = (WHITE, DARK) if raised else (DARK, WHITE)
    d.line([(x0, y1), (x0, y0), (x1, y0)], fill=a, width=2)
    d.line([(x0, y1), (x1, y1), (x1, y0)], fill=b, width=2)


def frame(k):
    im = Image.new("RGB", (512, 256), TEAL)
    d = ImageDraw.Draw(im)
    # taskbar
    d.rectangle([0, 230, 511, 255], fill=GREY)
    d.line([(0, 231), (511, 231)], fill=WHITE)
    d.rectangle([4, 234, 70, 252], fill=GREY)
    bevel(d, 4, 234, 70, 252)
    d.text((12, 235), "Start", font=title_f, fill=BLACK)
    d.text((452, 237), "4:20 PM", font=small_f, fill=BLACK)
    # the dialog
    x0, y0, x1, y1 = 40, 18, 472, 218
    d.rectangle([x0, y0, x1, y1], fill=GREY)
    bevel(d, x0, y0, x1, y1)
    for i in range(x1 - x0 - 8):                                   # Win98 gradient title bar
        t = i / (x1 - x0 - 8)
        col = tuple(int(NAVY[j] * (1 - t) + BLUE2[j] * t) for j in range(3))
        d.line([(x0 + 4 + i, y0 + 4), (x0 + 4 + i, y0 + 26)], fill=col)
    d.text((x0 + 10, y0 + 5), "Messenger Service", font=title_f, fill=WHITE)
    bx = x1 - 26
    d.rectangle([bx, y0 + 7, bx + 18, y0 + 23], fill=GREY)
    bevel(d, bx, y0 + 7, bx + 18, y0 + 23)
    d.text((bx + 5, y0 + 5), "x", font=title_f, fill=BLACK)
    dots = "." * (1 + (k // 2) % 3)
    d.text((x0 + 22, y0 + 40), "Sending NET SEND" + dots, font=big_f, fill=BLACK)
    d.text((x0 + 22, y0 + 76), "To: *  (everyone on LAB_NET)", font=body_f, fill=BLACK)
    d.text((x0 + 22, y0 + 100), "Message: WHERE'S THE DISK?", font=body_f, fill=BLACK)
    # progress bar: Win98 blocks
    px0, py0, px1, py1 = x0 + 22, y0 + 132, x1 - 22, y0 + 154
    d.rectangle([px0, py0, px1, py1], fill=WHITE)
    bevel(d, px0, py0, px1, py1, raised=False)
    n = int((k + 1) / 16 * 26)
    for b in range(n):
        bx0 = px0 + 4 + b * 14
        if bx0 + 10 > px1 - 3:
            break
        d.rectangle([bx0, py0 + 4, bx0 + 10, py1 - 4], fill=NAVY)
    # OK button
    ox = (x0 + x1) // 2 - 40
    d.rectangle([ox, y0 + 164, ox + 80, y0 + 190], fill=GREY)
    bevel(d, ox, y0 + 164, ox + 80, y0 + 190)
    d.rectangle([ox - 2, y0 + 162, ox + 82, y0 + 192], outline=BLACK)
    d.text((ox + 29, y0 + 167), "OK", font=body_f, fill=BLACK)
    return im


for k in range(16):
    frame(k).save(os.path.join(PROGS, "netsend_s_l%02d.png" % k))
print("wrote 16 Win98 NET SEND frames")
