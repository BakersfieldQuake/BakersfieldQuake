"""Writes a Quake WAD2 of miptex lumps from PIL images (palette from id1/pak0.pak, 4 mip levels, fullbright colours left out)."""
import struct
from PIL import Image

PAK = "G:/Quake/Combat/id1/pak0.pak"


def quake_palette():
    with open(PAK, "rb") as f:
        _, dofs, dlen = struct.unpack("<4sii", f.read(12))
        f.seek(dofs)
        for _ in range(dlen // 64):
            name, pos, size = struct.unpack("<56sii", f.read(64))
            if name.split(b"\0")[0] == b"gfx/palette.lmp":
                f.seek(pos)
                return list(f.read(size))
    raise IOError("no gfx/palette.lmp in " + PAK)


def _pal_image(pal):
    im = Image.new("P", (1, 1))
    lit = pal[:224 * 3]                           # 224..255 glow in the dark: never pick them
    im.putpalette(lit + lit[:3] * (256 - 224))
    return im


def miptex(name, img, palimg):
    w, h = img.size
    data = b""
    for m in range(4):
        sz = (max(1, w >> m), max(1, h >> m))
        q = img.convert("RGB").resize(sz, Image.LANCZOS).quantize(palette=palimg, dither=Image.Dither.NONE)
        px = bytearray(q.tobytes())
        if name.startswith("{") and img.mode == "RGBA":     # fence textures: index 255 is see-through
            a = img.getchannel("A").resize(sz, Image.NEAREST).tobytes()
            for i, v in enumerate(a):
                if v < 128:
                    px[i] = 255
        data += bytes(px)
    ofs, o = [], 40
    for m in range(4):
        ofs.append(o)
        o += max(1, w >> m) * max(1, h >> m)
    return struct.pack("<16s2I4I", name.encode()[:15], w, h, *ofs) + data


def write_wad(path, textures):
    """textures: dict name -> PIL image (sizes multiples of 16)."""
    palimg = _pal_image(quake_palette())
    lumps = [(n, miptex(n, im, palimg)) for n, im in textures.items()]
    body, dirs, pos = b"", b"", 12
    for n, data in lumps:
        dirs += struct.pack("<3i2bh16s", pos, len(data), len(data), 0x44, 0, 0, n.encode()[:15])
        body += data
        pos += len(data)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sii", b"WAD2", len(lumps), pos) + body + dirs)
