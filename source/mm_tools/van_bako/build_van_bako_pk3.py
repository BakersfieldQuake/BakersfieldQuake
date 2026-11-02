"""Builds zz_bakovan.pk3: the stock ProMaster van texture with Rob's van front (van_front_bako.png) pasted in.

python -I build_van_bako_pk3.py <path to bakersfield.pk3> [output pk3]

Reads the stock progs/veh_van_tex.png and progs/veh_van_tex_glow.png out of bakersfield.pk3, scales
van_front_bako.png into the front-fascia panel (x 1024-1521, y 43-497 of the 2048x2048 atlas), matches its white
paint to the atlas white (about 147, the atlas is dimmed for DarkPlaces), and moves the two headlight glow blobs
onto the new headlights. Writes both PNGs into a small pk3 (default: zz_bakovan.pk3 next to bakersfield.pk3).
The zz_ name sorts after bakersfield.pk3, so DarkPlaces loads it later and its files win; delete it to undo.
"""
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
FRONT_ART = HERE / "van_front_bako.png"
X0, Y0, W, H = 1024, 43, 497, 454              # front panel in veh_van_tex.png
ATLAS_WHITE = 147.0                            # mean of the stock white paint
HEADLIGHTS_UV = ((160 / 1312, 300 / 1199), (1180 / 1312, 300 / 1199))  # headlight centres in van_front_bako.png
GLOW_BLOB = (1075, 150, 1115, 190)             # one stock headlight glow blob, reused for both lights


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src_pk3 = Path(sys.argv[1])
    out_pk3 = Path(sys.argv[2]) if len(sys.argv) > 2 else src_pk3.with_name("zz_bakovan.pk3")
    with zipfile.ZipFile(src_pk3) as z:
        tex = Image.open(io.BytesIO(z.read("progs/veh_van_tex.png"))).convert("RGB")
        glow = Image.open(io.BytesIO(z.read("progs/veh_van_tex_glow.png"))).convert("RGB")

    front = np.asarray(Image.open(FRONT_ART).convert("RGB").resize((W, H), Image.LANCZOS)).astype(float)
    hood = front[int(H * 0.05):int(H * 0.15), int(W * 0.3):int(W * 0.7)].reshape(-1, 3).mean()
    front = np.clip(front * (ATLAS_WHITE / hood), 0, 255).astype(np.uint8)
    tex.paste(Image.fromarray(front), (X0, Y0))

    blob = glow.crop(GLOW_BLOB)
    glow.paste((0, 0, 0), (X0, Y0, X0 + W, Y0 + H))
    for u, v in HEADLIGHTS_UV:
        glow.paste(blob, (X0 + int(u * W) - blob.width // 2, Y0 + int(v * H) - blob.height // 2))

    with zipfile.ZipFile(out_pk3, "w", zipfile.ZIP_STORED) as z:   # PNGs are already compressed
        for name, im in (("progs/veh_van_tex.png", tex), ("progs/veh_van_tex_glow.png", glow)):
            buf = io.BytesIO()
            im.save(buf, "PNG")
            z.writestr(name, buf.getvalue())
            print(f"wrote {name} -> {out_pk3}")


if __name__ == "__main__":
    main()
