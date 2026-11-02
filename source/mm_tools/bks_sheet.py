"""Contact sheet of screenshots: python bks_sheet.py out.jpg cols w img1 img2 ..."""
import sys
from PIL import Image, ImageDraw
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ims = [(p, Image.open(p).convert("RGB")) for p in sys.argv[4:]]
h = int(w * ims[0][1].height / ims[0][1].width)
rows = (len(ims) + cols - 1) // cols
sh = Image.new("RGB", (cols * w, rows * h))
for i, (p, im) in enumerate(ims):
    t = im.resize((w, h))
    ImageDraw.Draw(t).text((4, 4), p.split("/")[-1], fill=(255, 255, 0))
    sh.paste(t, ((i % cols) * w, (i // cols) * h))
sh.save(out, quality=85)
