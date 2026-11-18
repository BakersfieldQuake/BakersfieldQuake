"""Builds zz_gunframes.pk3: the animated gun models' frames packed into atlases, so a map load opens 47 textures
instead of 882.

    python -I source/mm_tools/build_gunframe_atlas_pk3.py <path to bakersfield.pk3> [output pk3]

Why: every map precaches six animated gun models whose skins are one PNG per frame (v_milky 248, v_pickle 120,
v_dookie 114, v_greenjar 112, v_robhead_drone 112 plus 112 drone heads, and the pickle world model 64). Load time scales with the number of texture files, because the engine probes ~40 optional
companion files (_norm, _glow, _pants... as .tga/.png/.jpg) for every one of them (docs/audit-2026-11-18-performance.md).

What it does, all read from bakersfield.pk3 (nothing in the base pack or the QuakeC changes):
  1. Follows each model's progs/<model>.md3_<n>.skin files to the texture (= shader) names, in skin order.
  2. Finds the scripts/*.shader files that define those shaders and the image each one maps.
  3. Packs each (model, surface) frame set into atlases of at most 2048x2048 (see ATLAS_MAX).
  4. Rewrites those shader files with every keyword kept as it was; only the image line changes, from
     "clampmap progs/mvm_a_00" to "clampmap progs/gunatlas/mvm_3" plus a "tcMod transform" that maps the card's
     0..1 texture coordinates onto that frame's cell. Sets drawn without mipmaps gain "nomipmaps" (see SETS).
     The overlay's scripts/<same name>.shader replaces the base file: the engine lists each shader file name once
     and loads it from the highest-priority pack, and ignores a second definition of a shader name.
  5. Checks every atlas cell against its source frame, pixel for pixel, and writes a reproducible pk3.

Layout decisions (from the Zircon source, model_shared_q3shader_loop.c.h and gl_textures.c):
  - ATLAS_MAX = 2048: shader textures without "nopicmip" are capped by gl_max_size, whose default is 2048 and which
    the mod does not raise; a 4096 atlas would be halved. Keeping picmip (no "nopicmip") keeps gl_picmip /
    gl_picmip_other working on the guns exactly as before.
  - The view-model frames have opaque pixels on their edges (arms leaving the frame) and are drawn with clampmap.
    Their gutter therefore repeats each frame's edge pixels (GUTTER px on every side), which reproduces
    clamp-to-edge filtering exactly; where a frame's edge is transparent, so is its gutter.
  - The pickle world model is seen at a distance and keeps its mipmaps. Its frames are 512x512 with at least 5 px
    of transparent margin, so they sit gutter-free on a 512 grid in 2048x2048 atlases: every mip level of a cell
    stays aligned to its own texels.

Reproducible: PNGs are written by the pinned Pillow at a fixed compression level; zip entries are sorted, dated
1980-01-01, with fixed attributes; PNGs stored, shaders deflated at level 9.
"""
import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

ATLAS_MAX = 2048
GUTTER = 2
ATLAS_DIR = "progs/gunatlas"
SCRIPT_NAME = "source/mm_tools/build_gunframe_atlas_pk3.py"

# model -> (mipmapped, gutter px). View models are drawn without mipmaps; the world-model pickle keeps them.
# v_robhead, v_robhead_baseball and v_robhead_wizard (112 frames each) are left out: the QuakeC never precaches them
# (only v_robhead_drone), so no map loads their frames and packing them would only add 35.6 MB to the download.
SETS = {
    "v_milky": (False, GUTTER),
    "v_pickle": (False, GUTTER),
    "v_dookie": (False, GUTTER),
    "v_greenjar": (False, GUTTER),
    "v_robhead_drone": (False, GUTTER),
    "pickle": (True, 0),
}

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
PNG_LEVEL = 9


def skin_textures(z, model):
    """{surface: [texture names in skin order]} from progs/<model>.md3_<n>.skin."""
    pat = re.compile(r"progs/%s\.md3_(\d+)\.skin" % re.escape(model))
    skins = sorted(((int(m.group(1)), n) for n in z.namelist() for m in [pat.fullmatch(n)] if m))
    assert skins and [i for i, _ in skins] == list(range(len(skins))), f"{model}: skins not numbered 0..n-1"
    out = {}
    for _, name in skins:
        for line in z.read(name).decode("latin-1").splitlines():
            if "," in line:
                surf, tex = (s.strip() for s in line.split(",", 1))
                lst = out.setdefault(surf, [])
                if tex not in lst:
                    lst.append(tex)
    return out


BLOCK = re.compile(r"^([^\s{}/][^\s{}]*)[ \t]*\r?\n\{.*?^\}[ \t]*\r?\n?", re.M | re.S)
MAPLINE = re.compile(r"^([ \t]*)(map|clampmap)[ \t]+(\S+)[ \t]*$", re.M | re.I)


def shader_blocks(text):
    return {m.group(1): m for m in BLOCK.finditer(text)}


def load_rgba(z, names_lower, tex):
    for ext in (".tga", ".png", ".jpg"):     # the engine's own lookup order
        real = names_lower.get((tex + ext).lower())
        if real:
            im = Image.open(io.BytesIO(z.read(real)))
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            return np.asarray(im).copy()
    raise SystemExit(f"no image for {tex}")


def plan_atlases(n, w, h, gutter, mip):
    pw, ph = w + 2 * gutter, h + 2 * gutter
    cols, rows = ATLAS_MAX // pw, ATLAS_MAX // ph
    assert cols >= 1 and rows >= 1, (w, h)
    count = -(-n // (cols * rows))                  # fewest atlases that hold the set
    per = cols * -(-(-(-n // count)) // cols)        # then spread the frames evenly: whole rows, fewer empty cells
    sizes = []
    left = n
    for _ in range(count):
        k = min(per, left)
        left -= k
        aw = cols * pw if k >= cols else k * pw
        ah = -(-k // cols) * ph
        if mip:   # mipmapped atlases stay power-of-two so every level keeps the cell grid aligned
            aw = ah = ATLAS_MAX
            assert ATLAS_MAX % pw == 0 and ATLAS_MAX % ph == 0 and pw & (pw - 1) == 0 and ph & (ph - 1) == 0
        sizes.append((k, aw, ah))
    return cols, pw, ph, sizes


def pack_set(prefix, frames, gutter, mip):
    """frames: list of (tex, rgba). Returns ([(atlas name, png bytes, (w, h))], {tex: (atlas, transform)})."""
    h, w = frames[0][1].shape[:2]
    for tex, a in frames:
        assert a.shape[:2] == (h, w), f"{tex}: {a.shape[:2]} differs from {(h, w)}"
    if mip:
        for tex, a in frames:   # gutter-free cells: the frame's own border must be transparent
            al = a[..., 3]
            assert not (al[:4].any() or al[-4:].any() or al[:, :4].any() or al[:, -4:].any()), \
                f"{tex}: a mipmapped set needs a 4 px transparent margin"
    cols, pw, ph, sizes = plan_atlases(len(frames), w, h, gutter, mip)
    atlases, xform = [], {}
    i = 0
    for ai, (k, aw, ah) in enumerate(sizes):
        name = f"{ATLAS_DIR}/{prefix}_{ai}"
        atlas = np.zeros((ah, aw, 4), np.uint8)
        for j in range(k):
            tex, a = frames[i + j]
            cx, cy = (j % cols) * pw, (j // cols) * ph
            cell = np.pad(a, ((gutter, gutter), (gutter, gutter), (0, 0)), mode="edge") if gutter else a
            atlas[cy:cy + ph, cx:cx + pw] = cell
            x0, y0 = cx + gutter, cy + gutter
            xform[tex] = (name, (w / aw, h / ah, x0 / aw, y0 / ah), (x0, y0, w, h))
        buf = io.BytesIO()
        Image.fromarray(atlas, "RGBA").save(buf, format="PNG", compress_level=PNG_LEVEL)
        atlases.append((name, buf.getvalue(), atlas))
        i += k
    return atlases, xform


def rewrite_shader(text, xform_by_shader, mip_by_shader):
    """Swap the image line of every frame shader for atlas + tcMod transform; keep everything else verbatim."""
    blocks = shader_blocks(text)
    out, pos, done = [], 0, set()
    for name, m in sorted(blocks.items(), key=lambda kv: kv[1].start()):
        out.append(text[pos:m.start()])
        block = m.group(0)
        if name in xform_by_shader:
            atlas, (sx, sy, ox, oy), _ = xform_by_shader[name]
            maps = list(MAPLINE.finditer(block))
            assert len(maps) == 1, f"{name}: expected one map/clampmap line"
            ind, kw, _img = maps[0].groups()
            new = f"{ind}{kw} {atlas}\n{ind}tcMod transform {sx:.8f} 0 0 {sy:.8f} {ox:.8f} {oy:.8f}"
            block = block[:maps[0].start()] + new + block[maps[0].end():]
            if not mip_by_shader[name] and not re.search(r"^\s*nomipmaps\s*$", block, re.M | re.I):
                block = block.replace("{\n", "{\n\tnomipmaps\n", 1)
            done.add(name)
        out.append(block)
        pos = m.end()
    out.append(text[pos:])
    missing = set(xform_by_shader) - done
    assert not missing, f"shaders not found in file: {sorted(missing)[:5]}"
    body = "".join(out)
    first, _, rest = body.partition("\n")
    if first.startswith("//"):
        body = f"// written by {SCRIPT_NAME} (frames packed into {ATLAS_DIR}/); " \
               f"original {first[2:].strip()}\n{rest}"
    return body


def verify(z, names_lower, atlases, xform):
    pixels = {name: arr for name, _png, arr in atlases}
    for name, png, _arr in atlases:   # the PNG round-trips to the same pixels
        back = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
        assert np.array_equal(back, pixels[name]), name
    for tex, (atlas, (sx, sy, ox, oy), (x0, y0, w, h)) in xform.items():
        a = pixels[atlas]
        ah, aw = a.shape[:2]
        assert abs(ox * aw - x0) < 1e-6 and abs(sx * aw - w) < 1e-6 and abs(oy * ah - y0) < 1e-6 and abs(sy * ah - h) < 1e-6
        assert np.array_equal(a[y0:y0 + h, x0:x0 + w], load_rgba(z, names_lower, tex)), f"{tex}: cell differs"


def write_pk3(out_path, entries):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".pk3.tmp")
    with zipfile.ZipFile(tmp, "w") as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            info.create_system = 3
            if name.endswith(".png"):
                info.compress_type = zipfile.ZIP_STORED
                zf.writestr(info, entries[name])
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, entries[name], compresslevel=9)
    tmp.replace(out_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("base_pk3", type=Path)
    ap.add_argument("out_pk3", type=Path, nargs="?")
    args = ap.parse_args()
    out_pk3 = args.out_pk3 or args.base_pk3.with_name("zz_gunframes.pk3")

    z = zipfile.ZipFile(args.base_pk3)
    names_lower = {n.lower(): n for n in z.namelist()}
    shader_files = sorted(n for n in z.namelist() if n.startswith("scripts/") and n.endswith(".shader"))
    shader_text = {n: z.read(n).decode("latin-1") for n in shader_files}
    defined = {}
    for n in shader_files:
        for sname, m in shader_blocks(shader_text[n]).items():
            defined.setdefault(sname, (n, m.group(0)))

    entries, xform_all, mip_by_shader, files_touched = {}, {}, {}, set()
    total_frames = 0
    for model, (mip, gutter) in SETS.items():
        for surf, texs in skin_textures(z, model).items():
            frames = []
            for tex in texs:
                assert tex in defined, f"{model}/{surf}: no shader {tex}"
                sfile, block = defined[tex]
                maps = MAPLINE.findall(block)
                assert len(maps) == 1, f"{tex}: expected one map/clampmap line"
                frames.append((maps[0][2], load_rgba(z, names_lower, maps[0][2]), tex))
                files_touched.add(sfile)
            prefix = model if surf == "card" else f"{model}_{surf}"
            atlases, xf = pack_set(prefix, [(img, a) for img, a, _ in frames], gutter, mip)
            verify(z, names_lower, atlases, xf)
            for img, _a, tex in frames:
                xform_all[tex] = xf[img]
                mip_by_shader[tex] = mip
            for name, png, arr in atlases:
                entries[name + ".png"] = png
            total_frames += len(frames)
            print(f"{model:20s} {surf:5s} {len(frames):4d} frames {frames[0][1].shape[1]}x{frames[0][1].shape[0]}"
                  f" -> {len(atlases)} atlases " + " ".join(f"{a.shape[1]}x{a.shape[0]}" for _, _, a in atlases))

    for sfile in sorted(files_touched):
        mine = {s: x for s, x in xform_all.items() if defined[s][0] == sfile}
        entries[sfile] = rewrite_shader(shader_text[sfile], mine, mip_by_shader).encode("latin-1")

    write_pk3(out_pk3, entries)
    pngs = sum(1 for e in entries if e.endswith(".png"))
    print(f"{total_frames} frames -> {pngs} atlases, {len(files_touched)} shader files; "
          f"wrote {out_pk3} ({out_pk3.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
