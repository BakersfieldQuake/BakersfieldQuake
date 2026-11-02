"""Builds megaman.ico from a Blender render of the gun (flood-fills the grey backdrop, puts it on a blue tile)."""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
bg = im.getpixel((5, 5))
mask = Image.new("L", im.size, 255)  # 255 = keep
work = im.copy()
for seed in [(2, 2), (im.width - 3, 2), (2, im.height - 3), (im.width - 3, im.height - 3)]:
    ImageDraw.floodfill(work, seed, (255, 0, 255), thresh=28)
px = work.load()
m = Image.new("L", im.size, 255)
mp = m.load()
for y in range(im.height):
    for x in range(im.width):
        if px[x, y] == (255, 0, 255):
            mp[x, y] = 0
m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1))
obj = im.copy(); obj.putalpha(m)
bbox = m.point(lambda v: 255 if v > 40 else 0).getbbox()
obj = obj.crop(bbox)
S = 1024
tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
grad = Image.new("RGB", (S, S))
gp = grad.load()
for y in range(S):
    t = y / S
    c = (int(30 + 20 * t), int(120 - 40 * t), int(235 - 60 * t))  # Mega Man blue
    for x in range(S):
        gp[x, y] = c
rm = Image.new("L", (S, S), 0)
ImageDraw.Draw(rm).rounded_rectangle((0, 0, S - 1, S - 1), radius=190, fill=255)
tile.paste(grad, (0, 0), rm)
k = 0.80 * S / max(obj.size)
obj = obj.resize((int(obj.width * k), int(obj.height * k)), Image.LANCZOS)
shadow = Image.new("RGBA", obj.size, (0, 0, 0, 0))
shadow.putalpha(obj.getchannel("A").point(lambda v: int(v * 0.45)))
shadow = shadow.filter(ImageFilter.GaussianBlur(14))
pos = ((S - obj.width) // 2, (S - obj.height) // 2)
tile.alpha_composite(shadow, (pos[0] + 8, pos[1] + 16))
tile.alpha_composite(obj, pos)
tile.save(out, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
tile.resize((512, 512), Image.LANCZOS).save(out.replace(".ico", "_preview.png"))
