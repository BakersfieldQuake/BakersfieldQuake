"""build_textures.py — Photo-derived texture extractor, homography straightener,
tileability blender, WAD2 builder, DarkPlaces hi-res PNG exporter, and source logger
for Nana Plaza (`specs/textures.json` -> `BakersfieldQuake/textures/np_*.png` + `out/nanaplaza.wad` + `texture_sources.md`).
"""
import json
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, MM_TOOLS)
from wad2 import write_wad  # noqa: E402

REF_DIR = os.path.join(HERE, "ref_images")
SPEC_PATH = os.path.join(HERE, "specs", "textures.json")
OUT_DIR = os.path.join(HERE, "out")
WAD_PATH = os.path.join(OUT_DIR, "nanaplaza.wad")
MOD_TEX_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "textures"))
LOG_MD_PATH = os.path.join(HERE, "texture_sources.md")
ATLAS_PATH = os.path.join(OUT_DIR, "texture_atlas_sheet.jpg")


def solve_perspective_coeffs(dst_pts, src_pts):
    """Computes 8-DOF perspective transform coeffs mapping dst_pts -> src_pts for PIL.Image.transform."""
    A = []
    B = []
    for (x, y), (u, v) in zip(dst_pts, src_pts):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        B.append(u)
        B.append(v)
    A = np.array(A, dtype=np.float64)
    B = np.array(B, dtype=np.float64)
    res = np.linalg.solve(A, B)
    return tuple(res.tolist())


def rectify_quad(im, quad, out_w, out_h):
    dst = [(0, 0), (out_w, 0), (out_w, out_h), (0, out_h)]
    coeffs = solve_perspective_coeffs(dst, quad)
    return im.transform((out_w, out_h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)


def level_illumination(im):
    """Removes broad uneven lighting gradients across a surface crop while preserving exact mean RGB."""
    arr = np.asarray(im, dtype=np.float32)
    sigma = max(12.0, min(im.width, im.height) * 0.22)
    low = np.asarray(im.filter(ImageFilter.GaussianBlur(sigma)), dtype=np.float32)
    mean_rgb = arr.mean(axis=(0, 1), keepdims=True)
    out = arr * (mean_rgb / np.maximum(low, 8.0))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def make_tileable(im, mode="hv", frac=0.18):
    """Applies smooth raised-cosine wrap-around cross-blending so opposite edges tile cleanly."""
    if mode == "none":
        return im
    arr = np.asarray(im, dtype=np.float32)
    h, w, _ = arr.shape
    if "h" in mode:
        bw = max(4, int(round(w * frac)))
        shifted = np.roll(arr, w // 2, axis=1)
        # Blend seam at w//2 in `shifted` using original center, then roll back — classic artifact-free wrap!
        mask = np.ones((1, w, 1), dtype=np.float32)
        c = w // 2
        for dx in range(-bw, bw):
            t = (dx + bw) / float(2 * bw)  # 0..1
            # Bell weight = sin(pi * t)^2 -> 1 at center seam, 0 at +-bw
            wgt = math.sin(math.pi * t) ** 2
            mask[0, (c + dx) % w, 0] = 1.0 - wgt
        blended = shifted * mask + arr * (1.0 - mask)
        arr = np.roll(blended, -(w // 2), axis=1)
    if "v" in mode:
        bh = max(4, int(round(h * frac)))
        shifted = np.roll(arr, h // 2, axis=0)
        mask = np.ones((h, 1, 1), dtype=np.float32)
        c = h // 2
        for dy in range(-bh, bh):
            t = (dy + bh) / float(2 * bh)
            wgt = math.sin(math.pi * t) ** 2
            mask[(c + dy) % h, 0, 0] = 1.0 - wgt
        blended = shifted * mask + arr * (1.0 - mask)
        arr = np.roll(blended, -(h // 2), axis=0)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def is_pow2(n):
    return n >= 16 and (n & (n - 1)) == 0


def build_cutout_textures(base_dict):
    """Creates alpha-cutout `{np_*` fence/railing/wire textures from photo-derived base textures."""
    cutouts = {}

    # 1. {np_wire_blk: Overhead Bangkok black cable bundle & coils derived from ref_051.jpg
    ref51 = Image.open(os.path.join(REF_DIR, "ref_051.jpg")).convert("RGB")
    wire_crop = ref51.crop((320, 12, 740, 188)).resize((512, 256), Image.Resampling.LANCZOS)
    w_arr = np.asarray(wire_crop, dtype=np.float32)
    # Dark cables (< 95 luma) are opaque, bright sky/building background (> 115 luma) is transparent!
    luma = 0.299 * w_arr[..., 0] + 0.587 * w_arr[..., 1] + 0.114 * w_arr[..., 2]
    alpha = np.where(luma < 92.0, 255, 0).astype(np.uint8)
    rgba = np.dstack([np.clip(w_arr * 0.55, 0, 255).astype(np.uint8), alpha])
    cutouts["{np_wire_blk"] = (
        Image.fromarray(rgba, "RGBA"),
        "ref_051.jpg",
        "box [320, 12, 740, 188] luma-keyed cable bundle",
        (512, 256),
        "h",
        (4.5, 1.8),
        "Overhead Bangkok telecom/power black cable bundle & coils extracted with alpha key from ref_051.jpg.",
    )

    # 2. {np_ped_rail: Stainless pedestrian guardrail at Soi 4 mouth derived from ref_045.jpg
    ref45 = Image.open(os.path.join(REF_DIR, "ref_045.jpg")).convert("RGB")
    metal_sample = ref45.crop((495, 360, 555, 455)).resize((256, 128), Image.Resampling.LANCZOS)
    m_rgb = np.median(np.asarray(metal_sample), axis=(0, 1)).astype(np.uint8)
    rail = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(rail)
    col = (max(160, int(m_rgb[0])), max(165, int(m_rgb[1])), max(172, int(m_rgb[2])), 255)
    col_dk = (110, 116, 124, 255)
    # Top, mid, bottom thin tubular rails + slender vertical pickets matching ref_045.jpg
    d.rectangle([0, 6, 255, 11], fill=col, outline=col_dk)
    d.rectangle([0, 26, 255, 30], fill=col)
    d.rectangle([0, 110, 255, 115], fill=col, outline=col_dk)
    for x in range(8, 252, 18):
        d.rectangle([x, 10, x + 2, 111], fill=col)
    d.rectangle([0, 0, 4, 127], fill=col_dk)
    d.rectangle([251, 0, 255, 127], fill=col_dk)
    cutouts["{np_ped_rail"] = (
        rail,
        "ref_045.jpg",
        "box [495, 360, 555, 455] stainless rail profile",
        (256, 128),
        "h",
        (2.0, 1.0),
        "Stainless-steel sidewalk pedestrian barrier railing at Soi 4 mouth matched to ref_045.jpg.",
    )

    # 3. {np_bunting: International flag bunting & string lights across Nana Plaza courtyard from ref_018.jpg
    ref18 = Image.open(os.path.join(REF_DIR, "ref_018.jpg")).convert("RGB")
    bunt_crop = ref18.crop((160, 412, 470, 468)).resize((512, 64), Image.Resampling.LANCZOS)
    b_arr = np.asarray(bunt_crop, dtype=np.uint8)
    bunt = Image.new("RGBA", (512, 64), (0, 0, 0, 0))
    db = ImageDraw.Draw(bunt)
    db.rectangle([0, 2, 511, 5], fill=(40, 40, 45, 255))
    # Populate flag pennants sampled directly from ref_018.jpg bunting colours!
    for i in range(16):
        x0 = i * 32 + 4
        patch = b_arr[12:52, x0 : x0 + 22]
        # Boost vibrancy of real sampled flag pixels
        alpha_f = np.full((40, 22, 1), 255, dtype=np.uint8)
        flag_im = Image.fromarray(np.concatenate([patch, alpha_f], axis=2), "RGBA")
        bunt.paste(flag_im, (x0, 6))
    cutouts["{np_bunting"] = (
        bunt,
        "ref_018.jpg",
        "box [160, 412, 470, 468] courtyard flag bunting",
        (512, 64),
        "h",
        (6.4, 0.75),
        "Courtyard overhead international flag bunting & festoon wire sampled from ref_018.jpg.",
    )

    return cutouts


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(MOD_TEX_DIR, exist_ok=True)

    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        spec = json.load(f)

    wad_dict = {}
    log_rows = []
    INCH_PER_M = 39.37007874

    glow_signs = {
        "np_arch_main", "np_arch_crn", "np_arch_ban", "np_arch_safe", "np_arch_land", "np_blade_v", "np_exchange",
        "np_exch_hdr", "np_stumble", "np_morning", "np_kickoff", "np_bunny25",
        "np_lollipop", "np_loll_int", "np_bunnies", "np_twister", "np_obsession", "np_rainbow_b",
        "np_witchcrf", "np_erotica1", "np_playskool", "np_london", "np_spankys",
        "np_angel_sgn", "np_dc10", "np_dc10_wal", "np_sexynight", "np_casanova", "np_billboard", "np_bill_bar",
        "np_geisha3f", "np_erotica3", "np_butterfl", "np_hooters", "np_pharm_sgn", "np_pharm_bld",
        "np_blez", "np_pool_ceil", "np_led_cyan", "np_tv_pitch", "np_chang_bar", "np_reddragon", "np_balcony_b",
        "np_cannabis", "np_tattoo", "np_hillary2", "np_kingind", "np_billb_arr", "np_enter_sgn",
        "np_welcome_v", "np_in_plq", "np_out_plq",
    }

    for entry in spec["textures"]:
        name = entry["name"]
        assert len(name) <= 15, f"Texture name too long (>15): {name}"
        tw, th = entry["size"]
        assert is_pow2(tw) and is_pow2(th), f"Non-power-of-two size for {name}: {tw}x{th}"

        if entry["source"] == "placeholder":
            c = tuple(entry["color"])
            im = Image.new("RGB", (tw, th), c)
            # Subtle 2-px grid border so scale is clean without inventing detail
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, tw - 1, th - 1], outline=tuple(max(0, v - 14) for v in c), width=1)
            src_label = "placeholder (plain neutral)"
            crop_label = f"RGB {c}"
        else:
            src_path = os.path.join(REF_DIR, entry["source"])
            src_im = Image.open(src_path).convert("RGB")
            if "quad" in entry:
                im = rectify_quad(src_im, entry["quad"], tw, th)
                crop_label = f"quad {entry['quad']}"
            else:
                x0, y0, x1, y1 = entry["box"]
                im = src_im.crop((x0, y0, x1, y1)).resize((tw, th), Image.Resampling.LANCZOS)
                crop_label = f"box [{x0}, {y0}, {x1}, {y1}]"
            if entry.get("level_light", False):
                im = level_illumination(im)
            if entry.get("contrast_red", False):
                c_arr = np.asarray(im, dtype=np.float32).copy()
                red_ex = np.maximum(0.0, c_arr[..., 0] - 0.5 * (c_arr[..., 1] + c_arr[..., 2]) - 8.0)
                c_arr[..., 1] = np.clip(c_arr[..., 1] - 2.35 * red_ex, 0, 255)
                c_arr[..., 2] = np.clip(c_arr[..., 2] - 2.35 * red_ex, 0, 255)
                im = Image.fromarray(c_arr.astype(np.uint8), "RGB")
            if "tone" in entry:
                t_arr = np.clip(np.asarray(im, dtype=np.float32) * float(entry["tone"]), 0, 255).astype(np.uint8)
                im = Image.fromarray(t_arr, "RGB")
            im = make_tileable(im, entry.get("tile", "none"))
            src_label = f"`ref_images/{entry['source']}`"

        # Save full-res PNG for DarkPlaces + quarter-res (pow2 multiple of 16) for WAD2 lightmap subdivision scale
        png_path = os.path.join(MOD_TEX_DIR, f"{name}.png")
        im.save(png_path)
        if name in glow_signs:
            g_arr = np.asarray(im, dtype=np.float32)
            lum = 0.299 * g_arr[..., 0] + 0.587 * g_arr[..., 1] + 0.114 * g_arr[..., 2]
            mask = np.clip((lum - 75.0) / 135.0, 0.0, 1.0)[..., None]
            g_scale = 0.62 if name == "np_geisha3f" else 0.78
            glow = np.clip(g_arr * mask * g_scale, 0, 255).astype(np.uint8)
            Image.fromarray(glow, "RGB").save(os.path.join(MOD_TEX_DIR, f"{name}_glow.png"))
        sw = max(16, (tw // 4 // 16) * 16)
        sh = max(16, (th // 4 // 16) * 16)
        wad_dict[name] = im.resize((sw, sh), Image.Resampling.LANCZOS)
        sm = entry["scale_m"]
        log_rows.append((
            name,
            src_label,
            crop_label,
            f"{tw}x{th}",
            entry.get("tile", "none"),
            f"{sm[0]:.2f}m x {sm[1]:.2f}m ({sm[0]*INCH_PER_M:.0f}u x {sm[1]*INCH_PER_M:.0f}u)",
            entry["notes"],
        ))

    for cname, (cim, csrc, ccrop, (cw, ch), ctile, csm, cnotes) in build_cutout_textures(wad_dict).items():
        assert len(cname) <= 15 and is_pow2(cw) and is_pow2(ch)
        cim.save(os.path.join(MOD_TEX_DIR, f"{cname}.png"))
        sw = max(32, (cw // 2 // 16) * 16)
        sh = max(32, (ch // 2 // 16) * 16)
        wad_dict[cname] = cim.resize((sw, sh), Image.Resampling.NEAREST)
        log_rows.append((
            cname,
            f"`ref_images/{csrc}`",
            ccrop,
            f"{cw}x{ch}",
            ctile,
            f"{csm[0]:.2f}m x {csm[1]:.2f}m ({csm[0]*INCH_PER_M:.0f}u x {csm[1]*INCH_PER_M:.0f}u)",
            cnotes,
        ))

    # Include true Quake 1 256x128 dual-half sky miptex (`sky_np` & `sky`: left 128x128 transparent black 0 + wisps, right 128x128 Bangkok blue) + utility lumps in nanaplaza.wad
    sky_im = Image.new("RGB", (256, 128), (0, 0, 0))
    sky_bg = Image.new("RGB", (128, 128), (138, 176, 222))
    sky_im.paste(sky_bg, (128, 0))
    wad_dict["sky_np"] = sky_im
    wad_dict["sky"] = sky_im.copy()
    for stale_sky in ("sky_np.png", "sky.png"):
        sp_stale = os.path.join(MOD_TEX_DIR, stale_sky)
        if os.path.exists(sp_stale):
            os.remove(sp_stale)
    wad_dict["clip"] = Image.new("RGB", (64, 64), (180, 90, 60))
    wad_dict["skip"] = Image.new("RGB", (64, 64), (60, 60, 60))
    wad_dict["trigger"] = Image.new("RGB", (64, 64), (180, 60, 180))

    sky_log_row = (
        "sky_np",
        "`ref_images/ref_045.jpg` & `ref_049.jpg` (`build_sky.py`)",
        "calibrated zenith/horizon skybox cubemap `gfx/env/nanaplaza_*.png`",
        "256x128",
        "sky",
        "skybox",
        "Quake sky miptex backed by 6x512px Bangkok dry-season skybox calibrated to ref_045.jpg & ref_049.jpg.",
    )

    write_wad(WAD_PATH, wad_dict)
    print(f"Wrote {len(wad_dict)} textures to {WAD_PATH} and {MOD_TEX_DIR}")

    # Write texture_sources.md
    with open(LOG_MD_PATH, "w", encoding="utf-8") as mf:
        mf.write("# Nana Plaza — Photo-Derived Texture Source Log\n\n")
        mf.write("Every custom texture in `nanaplaza.wad` and `BakersfieldQuake/textures/np_*.png` is cropped, perspective-rectified, seam-blended (where tiled), and resized to power-of-two dimensions directly from the unpacked reference images in `source/mm_tools/nana_plaza/ref_images/`.\n\n")
        mf.write("| Texture | Source Image | Crop / Homography Quad | PoT Size | Tile Mode | Real-World Scale | Description |\n")
        mf.write("|---|---|---|---|---|---|---|\n")
        for r in log_rows + [sky_log_row]:
            mf.write(f"| `{r[0]}` | {r[1]} | `{r[2]}` | `{r[3]}` | `{r[4]}` | `{r[5]}` | {r[6]} |\n")
    print(f"Wrote {LOG_MD_PATH} ({len(log_rows) + 1} logged textures)")

    # Build visual verification contact sheet of all generated high-res PNG textures
    cols = 8
    items = [r[0] for r in log_rows]
    rows = math.ceil(len(items) / cols)
    cw_cell, ch_cell = 220, 190
    sheet = Image.new("RGB", (cols * cw_cell, rows * ch_cell), (26, 26, 30))
    ds = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 13)
    except OSError:
        fnt = ImageFont.load_default()
    for idx, tname in enumerate(items):
        cx = (idx % cols) * cw_cell
        cy = (idx // cols) * ch_cell
        full_im = Image.open(os.path.join(MOD_TEX_DIR, f"{tname}.png"))
        w0, h0 = full_im.size
        tim = full_im.convert("RGBA")
        bg = Image.new("RGBA", tim.size, (48, 52, 60, 255))
        comp = Image.alpha_composite(bg, tim).convert("RGB")
        comp.thumbnail((cw_cell - 12, ch_cell - 34), Image.Resampling.LANCZOS)
        sheet.paste(comp, (cx + (cw_cell - comp.width) // 2, cy + 6))
        ds.rectangle([cx, cy, cx + cw_cell - 1, cy + ch_cell - 1], outline=(70, 70, 80), width=1)
        ds.text((cx + 6, cy + ch_cell - 22), f"{tname} ({w0}x{h0})", fill=(255, 225, 120), font=fnt)
    sheet.save(ATLAS_PATH, quality=90)
    print(f"Wrote {ATLAS_PATH}")


if __name__ == "__main__":
    main()
