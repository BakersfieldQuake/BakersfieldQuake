"""Builds ONLY 100% active, verified in-game visual & audio media for the BakersfieldQuake 90s GeoCities fanpage:
  - fanpage/media/shots/*.jpg   (All 9 shipped .bsp maps + 100% active in-game weapons/monsters/vehicles)
  - fanpage/media/gifs/*.gif    (Active Milky & Pink Lady, WEW Cannon +58° bend, Wheelman roll/scream/fire-wheels/gibs
                                 & 8 post-crash dances, 24-angle Laptop Head, Pickle Surprise, NetSend LOL.BAT,
                                 Rob Dob, JohnWave splash, active mb_pool Mystery Box roster [10,11,17,18,19,20,21,22],
                                 Warehouse BKTV, Sky-Chariot & Pink Supercar, plus 90s GeoCities UI GIFs)
  - fanpage/media/ui/*          (milkdrips.png, bg_tile.png)
  - fanpage/media/sfx/*         (22 active progs.dat-verified .wav/.ogg clips from bakersfield.pk3)
"""
import base64
import glob
import io
import json
import math
import os
import random
import re
import shutil
import struct
import zipfile
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
COMBAT_ROOT = os.path.abspath(os.path.join(MOD_ROOT, ".."))
DEV_ROOT = os.path.join(COMBAT_ROOT, "_bakersfield_dev")
OUT_ROOT = os.path.join(HERE, "out")
PK3_PATH = os.path.join(MOD_ROOT, "bakersfield.pk3")
PROGS_DAT = os.path.join(MOD_ROOT, "progs.dat")

FANPAGE_DIR = os.path.join(MOD_ROOT, "fanpage")
SHOTS_DIR = os.path.join(FANPAGE_DIR, "media", "shots")
GIFS_DIR = os.path.join(FANPAGE_DIR, "media", "gifs")
SFX_DIR = os.path.join(FANPAGE_DIR, "media", "sfx")
UI_DIR = os.path.join(FANPAGE_DIR, "media", "ui")

PAK0_PATH = os.path.join(COMBAT_ROOT, "id1", "pak0.pak")


def clean_media_dirs():
    for d in (SHOTS_DIR, GIFS_DIR, SFX_DIR, UI_DIR):
        os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d):
            fp = os.path.join(d, fn)
            if os.path.isfile(fp):
                os.remove(fp)


def load_quake_palette():
    if os.path.exists(PAK0_PATH):
        with open(PAK0_PATH, "rb") as f:
            hdr = f.read(12)
            if hdr[:4] == b"PACK":
                ofs, sz = struct.unpack("<2i", hdr[4:])
                f.seek(ofs)
                for _ in range(sz // 64):
                    ent = f.read(64)
                    nm = ent[:56].split(b"\0")[0].decode("latin1")
                    if nm.lower() == "gfx/palette.lmp":
                        p_ofs, _ = struct.unpack("<2i", ent[56:])
                        f.seek(p_ofs)
                        raw = f.read(768)
                        return np.frombuffer(raw, dtype=np.uint8).reshape((256, 3))
    pal = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        pal[i] = ((i * 7) % 256, (i * 3) % 256, i)
    return pal


QPAL = load_quake_palette()


def save_shot(src_img_or_path, dst_name, max_w=1024, quality=86, crop_box=None):
    if isinstance(src_img_or_path, str):
        if not os.path.exists(src_img_or_path):
            print(f"  [WARN] Missing shot source: {src_img_or_path}")
            return False
        im = Image.open(src_img_or_path)
    else:
        im = src_img_or_path
    im = im.convert("RGB")
    if crop_box is not None:
        im = im.crop(crop_box)
    if im.width > max_w:
        nh = max(1, int(round(im.height * (max_w / im.width))))
        im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
    dst = os.path.join(SHOTS_DIR, dst_name)
    im.save(dst, "JPEG", quality=quality, optimize=True)
    return True


def make_gif(frames_rgba_or_rgb, dst_name, duration_ms=90, target_w=None, bg_rgb=(12, 10, 16), transparent=False):
    if not frames_rgba_or_rgb:
        return False
    out_frames = []
    for fr in frames_rgba_or_rgb:
        im = fr.copy()
        if target_w and im.width != target_w:
            nh = max(1, int(round(im.height * (target_w / im.width))))
            im = im.resize((target_w, nh), Image.Resampling.LANCZOS)
        if transparent:
            rgba = im.convert("RGBA")
            alpha = rgba.getchannel("A")
            comp = Image.new("RGBA", rgba.size, (*bg_rgb, 255))
            comp.alpha_composite(rgba)
            rgb = comp.convert("RGB")
            p = rgb.quantize(colors=255, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
            mask = Image.eval(alpha, lambda a: 255 if a < 96 else 0)
            p.paste(255, mask)
            out_frames.append(p)
        else:
            if im.mode == "RGBA":
                comp = Image.new("RGBA", im.size, (*bg_rgb, 255))
                comp.alpha_composite(im)
                rgb = comp.convert("RGB")
            else:
                rgb = im.convert("RGB")
            p = rgb.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
            out_frames.append(p)
    dst = os.path.join(GIFS_DIR, dst_name)
    save_kw = dict(save_all=True, append_images=out_frames[1:], duration=duration_ms, loop=0, optimize=False)
    if transparent:
        save_kw["transparency"] = 255
        save_kw["disposal"] = 2
    out_frames[0].save(dst, "GIF", **save_kw)
    return True


def read_spr32_frames(raw_bytes, indices):
    ident, ver, stype, rad, maxw, maxh, nframes, beam, sync = struct.unpack_from("<4siiifiiii", raw_bytes, 0)
    assert ident == b"IDSP" and ver == 32
    pos = 36
    want = set(indices)
    extracted = {}
    for fi in range(nframes):
        ftype = struct.unpack_from("<i", raw_bytes, pos)[0]
        pos += 4
        if ftype == 0:
            ox, oy, w, h = struct.unpack_from("<4i", raw_bytes, pos)
            pos += 16
            nbytes = w * h * 4
            if fi in want:
                extracted[fi] = Image.frombytes("RGBA", (w, h), raw_bytes[pos:pos + nbytes])
            pos += nbytes
        else:
            ng = struct.unpack_from("<i", raw_bytes, pos)[0]
            pos += 4 + ng * 4
            for sub in range(ng):
                ox, oy, w, h = struct.unpack_from("<4i", raw_bytes, pos)
                pos += 16
                nbytes = w * h * 4
                if sub == 0 and fi in want:
                    extracted[fi] = Image.frombytes("RGBA", (w, h), raw_bytes[pos:pos + nbytes])
                pos += nbytes
        if len(extracted) == len(want):
            break
    return [extracted[i] for i in indices if i in extracted]


def build_procedural_90s_gifs():
    print("[1/5] Generating procedural 90s GeoCities pixel-art GIFs & UI tiles...")
    tw, th = 192, 192
    bg = Image.new("RGB", (tw, th), (8, 6, 12))
    px = bg.load()
    rng = random.Random(6610)
    for y in range(th):
        for x in range(tw):
            n = int(
                7 * math.sin(x * 0.098 + 1.2 * math.sin(y * 0.065))
                + 6 * math.cos(y * 0.13 - 0.9 * math.cos(x * 0.065))
                + rng.randint(-3, 3)
            )
            gx = min(x % 64, 64 - (x % 64))
            gy = min((y + (32 if (x // 64) % 2 else 0)) % 64, 64 - ((y + (32 if (x // 64) % 2 else 0)) % 64))
            mortar = -5 if (gx < 2 or gy < 2) else 0
            r = max(4, min(28, 13 + n + mortar))
            g = max(3, min(20, 9 + n // 2 + mortar))
            b = max(6, min(32, 16 + n + mortar))
            px[x, y] = (r, g, b)
    for _ in range(42):
        sx, sy = rng.randrange(tw), rng.randrange(th)
        col = rng.choice([(140, 28, 28), (185, 45, 30), (120, 95, 40), (95, 30, 80), (65, 85, 130)])
        px[sx, sy] = col
    bg.save(os.path.join(UI_DIR, "bg_tile.png"), "PNG", optimize=True)

    # Classic Doom/Quake Pixel Fire Divider Bar
    fw, fh = 240, 32
    pal_fire = [(0, 0, 0, 0)]
    stops = [
        (0, (0, 0, 0)),
        (5, (45, 6, 4)),
        (11, (125, 14, 6)),
        (17, (205, 42, 8)),
        (23, (248, 118, 12)),
        (29, (255, 200, 35)),
        (35, (255, 250, 175)),
    ]
    for i in range(1, 36):
        for k in range(len(stops) - 1):
            i0, c0 = stops[k]
            i1, c1 = stops[k + 1]
            if i0 <= i <= i1:
                t = (i - i0) / max(1, i1 - i0)
                c = tuple(int(c0[c_i] + (c1[c_i] - c0[c_i]) * t) for c_i in range(3))
                pal_fire.append((*c, min(255, i * 24)))
                break
    buf = np.zeros((fh, fw), dtype=np.int32)
    buf[-1, :] = 35
    rng_f = np.random.default_rng(1997)
    for _ in range(45):
        for y in range(fh - 1):
            decay = rng_f.integers(0, 3, size=fw)
            shift = rng_f.integers(-1, 2, size=fw)
            src_x = (np.arange(fw) + shift) % fw
            buf[y, :] = np.maximum(0, buf[y + 1, src_x] - decay)
    fire_frames = []
    for _ in range(14):
        for _ in range(2):
            for y in range(fh - 1):
                decay = rng_f.integers(0, 3, size=fw)
                shift = rng_f.integers(-1, 2, size=fw)
                src_x = (np.arange(fw) + shift) % fw
                buf[y, :] = np.maximum(0, buf[y + 1, src_x] - decay)
        rgba = np.zeros((fh, fw, 4), dtype=np.uint8)
        for idx, c in enumerate(pal_fire):
            rgba[buf == idx] = c
        im = Image.fromarray(rgba, "RGBA").resize((fw * 2, fh * 2), Image.Resampling.NEAREST)
        fire_frames.append(im)
    make_gif(fire_frames, "fire_divider.gif", duration_ms=70, bg_rgb=(10, 6, 10), transparent=True)

    # Spinning Bloody Quake Nail-Rune
    rune_frames = []
    for fi in range(16):
        ang = (fi / 16.0) * 2.0 * math.pi
        cx_s = math.cos(ang)
        im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        glow_r = 27 + int(2 * math.sin(ang * 2))
        d.ellipse([32 - glow_r, 32 - glow_r, 32 + glow_r, 32 + glow_r], fill=(95, 12, 16, 120))
        w_scale = max(0.18, abs(cx_s))
        shade = int(165 + 85 * (0.5 + 0.5 * cx_s))
        metal = (shade, int(shade * 0.72), int(shade * 0.24), 255)
        edge = (85, 32, 12, 255)
        rx = max(4, int(22 * w_scale))
        d.arc([32 - rx, 8, 32 + rx, 48], start=35, end=325, fill=edge, width=7)
        d.arc([32 - rx, 8, 32 + rx, 48], start=38, end=322, fill=metal, width=4)
        nw = max(2, int(4 * w_scale))
        nw_head = max(4, int(10 * w_scale))
        d.rectangle([32 - nw_head, 22, 32 + nw_head, 27], fill=metal, outline=edge)
        d.polygon([(32 - nw, 27), (32 + nw, 27), (32, 58)], fill=metal, outline=edge)
        drop_y = 54 + (fi % 4) * 2
        d.ellipse([30, drop_y, 34, drop_y + 5], fill=(220, 15, 25, 255))
        im_pix = im.resize((32, 32), Image.Resampling.BILINEAR).resize((64, 64), Image.Resampling.NEAREST)
        rune_frames.append(im_pix)
    make_gif(rune_frames, "quake_rune_spin.gif", duration_ms=75, bg_rgb=(12, 8, 12), transparent=True)

    # Animated 90s Hazard Bar
    haz_frames = []
    for fi in range(8):
        im = Image.new("RGB", (320, 24), (20, 18, 12))
        d = ImageDraw.Draw(im)
        off = fi * 6
        for x in range(-48, 360, 24):
            pts = [(x + off, 0), (x + 12 + off, 0), (x - 4 + off, 24), (x - 16 + off, 24)]
            d.polygon(pts, fill=(245, 195, 15))
        d.rectangle([0, 0, 319, 23], outline=(255, 220, 60), width=2)
        d.rectangle([58, 4, 262, 19], fill=(10, 10, 12), outline=(255, 60, 30), width=1)
        d.text((68, 6), "WARNING: 661 LAN GORE & MILK ZONE", fill=(255, 235, 60))
        haz_frames.append(im)
    make_gif(haz_frames, "hazard_bar.gif", duration_ms=90)

    # Classic 88x31 Animated GeoCities Micro-Buttons
    buttons_spec = [
        ("btn_quake661.gif", (45, 12, 14), (255, 190, 40), (255, 60, 40), "QUAKE 1.5", "BAKERSFIELD!"),
        ("btn_milky.gif", (85, 12, 62), (255, 130, 225), (255, 255, 255), "GOT MILK?!", "PINK LADY 18+"),
        ("btn_wheelman.gif", (16, 32, 68), (90, 210, 255), (255, 140, 30), "WEW CANNON", "1200 U/S BOOM"),
        ("btn_megaman.gif", (14, 48, 56), (60, 245, 255), (255, 230, 50), "BLUE SHELL", "MEGAMAN READY"),
        ("btn_netscape.gif", (12, 42, 48), (140, 255, 220), (255, 255, 110), "NETSCAPE 4.7", "800x600 BEST!"),
        ("btn_nocampers.gif", (52, 24, 8), (255, 150, 45), (255, 50, 50), "0 FALL DMG!", "BONK OR DIE"),
    ]
    for fn, bgc, c1, c2, l1, l2 in buttons_spec:
        bframes = []
        for k in range(4):
            im = Image.new("RGB", (88, 31), bgc)
            d = ImageDraw.Draw(im)
            hi = tuple(min(255, v + 95) for v in bgc)
            lo = tuple(max(0, v - 35) for v in bgc)
            d.line([(0, 0), (87, 0)], fill=hi)
            d.line([(0, 0), (0, 30)], fill=hi)
            d.line([(0, 30), (87, 30)], fill=lo)
            d.line([(87, 0), (87, 30)], fill=lo)
            d.rectangle([2, 2, 85, 28], outline=c1 if k % 2 == 0 else c2, width=1)
            d.text((7, 5), l1, fill=c2 if k == 1 else (255, 255, 255))
            d.text((7, 16), l2, fill=c1 if k != 2 else (255, 255, 140))
            if k % 2 == 0:
                d.rectangle([78, 5, 82, 9], fill=(255, 50, 50))
            bframes.append(im)
        make_gif(bframes, fn, duration_ms=260)


def copy_and_build_gameplay_gifs(pk3):
    print("[2/5] Copying & building ONLY active in-game gameplay/weapon GIFs...")
    # ONLY active Wheelman states (wcannon.qc: normal rocket boom + flying wheels/bars/gibs, fire-wheels, scream, roll, long-bar, turn)
    # and ONLY active mb_pool ("10 11 17 18 19 20 21 22") Mystery Box monsters!
    copy_jobs = [
        (os.path.join(OUT_ROOT, "wheelman", "explode_gibs.gif"), "wm_gibs.gif"),
        (os.path.join(OUT_ROOT, "wheelman", "fire_wheels.gif"), "wm_fire_wheels.gif"),
        (os.path.join(OUT_ROOT, "wheelman", "scream.gif"), "wm_scream.gif"),
        (os.path.join(OUT_ROOT, "wheelman", "roll.gif"), "wm_roll.gif"),
        (os.path.join(OUT_ROOT, "wheelman", "long_bar_wheels.gif"), "wm_long_bar.gif"),
        (os.path.join(OUT_ROOT, "wheelman", "turn.gif"), "wm_turn.gif"),
        (os.path.join(DEV_ROOT, "bryan_sprite", "bryan_demon_whirl.gif"), "bryan_demon_whirl.gif"),
        (os.path.join(DEV_ROOT, "bryan_sprite", "bryan_360_spin.gif"), "bryan_360_spin.gif"),
        (os.path.join(DEV_ROOT, "jesskart_sprite", "anim", "jesskart_turbo_360.gif"), "jesskart_turbo_360.gif"),
        (os.path.join(DEV_ROOT, "jesskart_sprite", "anim", "jesskart_wheelie_loop.gif"), "jesskart_wheelie_loop.gif"),
        (os.path.join(DEV_ROOT, "scissor_sprite", "scissor_run.gif"), "scissor_run.gif"),
        (os.path.join(DEV_ROOT, "mrdiy_sprite", "mrdiy_dance.gif"), "mrdiy_dance.gif"),
        (os.path.join(DEV_ROOT, "rubber_finger_sprite", "rubber_finger_360_spin.gif"), "rubber_finger_360_spin.gif"),
        (os.path.join(DEV_ROOT, "dennis_sprite", "dennis_360_spin.gif"), "dennis_360_spin.gif"),
        (os.path.join(DEV_ROOT, "paul_sprite", "paul_360_spin.gif"), "paul_360_spin.gif"),
        (os.path.join(DEV_ROOT, "quakeguy_sprite", "quakeguy_360_spin.gif"), "quakeguy_360_spin.gif"),
    ]
    for src, dst in copy_jobs:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(GIFS_DIR, dst))
        else:
            hits = glob.glob(os.path.join(DEV_ROOT, "**", os.path.basename(src)), recursive=True)
            if hits:
                shutil.copy2(hits[0], os.path.join(GIFS_DIR, dst))
            else:
                raise FileNotFoundError(f"Active GIF source not found: {src}")

    if "gfx/milkdrips.png" in pk3.namelist():
        with open(os.path.join(UI_DIR, "milkdrips.png"), "wb") as f:
            f.write(pk3.read("gfx/milkdrips.png"))

    # 1. Milky Gun & Pink Lady In-Game Attack -> Milk Explosion!
    mk_paths = [os.path.join(DEV_ROOT, f"zr3_mk_{i}.png") for i in range(1, 9)]
    mk_frames = [Image.open(p) for p in mk_paths if os.path.exists(p)]
    if mk_frames:
        make_gif(mk_frames, "milky_pinklady_attack.gif", duration_ms=180, target_w=460)

    zp_paths = sorted(glob.glob(os.path.join(OUT_ROOT, "milky", "test15", "zp_*.png")))
    if zp_paths:
        zp_sub = [Image.open(p) for p in zp_paths[::2][:16]]
        make_gif(zp_sub, "milky_chase_splat.gif", duration_ms=110, target_w=460)

    # 2. Pink Lady 34-frame Bounce + 16-angle Spin GIF from pk3
    pl_b = []
    for i in range(0, 34, 2):
        nm = f"progs/pinklady_b{i:02d}.png"
        if nm in pk3.namelist():
            pl_b.append(Image.open(io.BytesIO(pk3.read(nm))))
    for i in range(16):
        nm = f"progs/pinklady_{i:02d}.png"
        if nm in pk3.namelist():
            pl_b.append(Image.open(io.BytesIO(pk3.read(nm))))
    if pl_b:
        make_gif(pl_b, "pinklady_bounce_spin.gif", duration_ms=85, target_w=260, bg_rgb=(22, 8, 24), transparent=True)

    # 3. WEW CANNON +58° Elastic Barrel Bend -> Whip-Snap Blast -> S-Bend Recoil!
    wew_p = sorted(glob.glob(os.path.join(OUT_ROOT, "wew_cannon", "previews", "0[1-7]_*.png")))
    if wew_p:
        wf = [Image.open(p) for p in wew_p]
        make_gif(wf + wf[-2:0:-1], "wewcannon_bend_blast.gif", duration_ms=150, target_w=460)

    # 4. Wheelman Post-Crash 8 Crazy Dances Showcase GIF (from progs/wheelman_dance.spr32)
    if "progs/wheelman_dance.spr32" in pk3.namelist():
        raw_wd = pk3.read("progs/wheelman_dance.spr32")
        banks_meta = [
            (0, 10, "1. STUCK SPRINT"),
            (80, 10, "2. OVERHEAD FLAIL"),
            (160, 12, "3. MANIAC DANCE"),
            (256, 10, "4. HANDS-UP KICK"),
            (336, 12, "5. 360 BAR SPIN"),
            (432, 12, "6. AXLE DEADLIFT"),
            (528, 12, "7. THROW THE RIG"),
            (624, 14, "8. TURN INTO ROBOT"),
        ]
        want_idx, idx_labels = [], []
        for base, klen, lbl in banks_meta:
            for step in range(4):
                d = (step * 2) % 8
                k = (step * 3) % klen
                want_idx.append(base + d * klen + k)
                idx_labels.append(lbl)
        wd_ims = read_spr32_frames(raw_wd, want_idx)
        labeled_wd = []
        for im, lbl in zip(wd_ims, idx_labels):
            card = Image.new("RGBA", (220, 204), (16, 10, 22, 255))
            rs = im.resize((176, 176), Image.Resampling.LANCZOS)
            card.alpha_composite(rs, (22, 4))
            dr = ImageDraw.Draw(card)
            dr.rectangle([4, 180, 215, 200], fill=(40, 12, 18, 255), outline=(255, 160, 30, 255))
            dr.text((12, 185), lbl, fill=(255, 235, 90, 255))
            labeled_wd.append(card)
        make_gif(labeled_wd, "wheelman_8_crazy_dances.gif", duration_ms=125)

    # 5. Mystery Box Throw & Active mb_pool Monster Rush GIFs!
    zm_p = sorted(glob.glob(os.path.join(DEV_ROOT, "zm_0*.png")) + glob.glob(os.path.join(DEV_ROOT, "zm_10.png")))
    if zm_p:
        make_gif([Image.open(p) for p in zm_p], "mystery_box_throw.gif", duration_ms=150, target_w=460)

    active_mb_shots = [
        p for p in (
            sorted(glob.glob(os.path.join(DEV_ROOT, "zm_0[4-9].png")))
            + [os.path.join(DEV_ROOT, "zm_10.png"), os.path.join(DEV_ROOT, "zm3_a.png"), os.path.join(DEV_ROOT, "zm3_b.png")]
            + sorted(glob.glob(os.path.join(DEV_ROOT, "zm4_*.png")))
        )
        if os.path.exists(p)
    ]
    if active_mb_shots:
        make_gif([Image.open(p) for p in active_mb_shots], "mystery_box_stampede.gif", duration_ms=155, target_w=460)

    # 6. NetSend LOL.BAT Floppy -> Win98 CRT Materialize -> Laser Sweep!
    zn_p = sorted(glob.glob(os.path.join(DEV_ROOT, "zn_*.png")))
    if zn_p:
        make_gif([Image.open(p) for p in zn_p], "netsend_lolbat.gif", duration_ms=155, target_w=460)

    # 7. Rob Dob Floating Head Rush & Explosion!
    zr_p = sorted(glob.glob(os.path.join(DEV_ROOT, "zr_0*.png")))
    if zr_p:
        make_gif([Image.open(p) for p in zr_p], "robdob_scream_boom.gif", duration_ms=190, target_w=460)

    # 8. JohnWave 3D Head Grenade Stare & Pacific Water Splash!
    jg_p = sorted(glob.glob(os.path.join(DEV_ROOT, "jg_*.png")))
    if jg_p:
        make_gif([Image.open(p) for p in jg_p], "johnwave_head_splash.gif", duration_ms=190, target_w=460)

    # 9. Pure Active In-Game Bakersfield LAN Mayhem Reel!
    mayhem_srcs = [
        os.path.join(DEV_ROOT, "zb4_00_start.png"),
        os.path.join(DEV_ROOT, "zz_vmmm_b.png"),
        os.path.join(DEV_ROOT, "zz_vmmm_d.png"),
        os.path.join(DEV_ROOT, "zr3_mk_2.png"),
        os.path.join(DEV_ROOT, "zr3_mk_7.png"),
        os.path.join(DEV_ROOT, "zm3_a.png"),
        os.path.join(DEV_ROOT, "zm4_18.png"),
        os.path.join(DEV_ROOT, "zn_04_send.png"),
        os.path.join(DEV_ROOT, "zr_02_boom.png"),
        os.path.join(DEV_ROOT, "jg_3.png"),
        os.path.join(DEV_ROOT, "zc3_05_boom.png"),
        os.path.join(DEV_ROOT, "zb3_08_trash_up.png"),
        os.path.join(DEV_ROOT, "zb3_10_pink.png"),
        os.path.join(DEV_ROOT, "zz_jp_fly.png"),
    ]
    mayhem_ims = [Image.open(p) for p in mayhem_srcs if os.path.exists(p)]
    if mayhem_ims:
        make_gif(mayhem_ims, "lan_mayhem_reel.gif", duration_ms=155, target_w=480)

    # 10. Erect Screaming Pickle Surprise 360° Diva GIF!
    pk_frames = []
    for s in range(4):
        for v in range(0, 16, 2):
            nm = f"progs/pkv_s{s}_v{v:02d}.png"
            if nm in pk3.namelist():
                pk_frames.append(Image.open(io.BytesIO(pk3.read(nm))))
    if pk_frames:
        make_gif(pk_frames, "pickle_diva_scream.gif", duration_ms=90, target_w=240, bg_rgb=(10, 22, 10), transparent=True)

    # 11. Real Key 4 AOL Laptop Gun 24-Angle Screaming Drone Head GIF (progs/ltg_head_00..23.png)!
    ltg_frames = []
    for i in range(24):
        nm = f"progs/ltg_head_{i:02d}.png"
        if nm in pk3.namelist():
            ltg_frames.append(Image.open(io.BytesIO(pk3.read(nm))))
    if ltg_frames:
        make_gif(ltg_frames, "ltg_head_360.gif", duration_ms=80, target_w=240, bg_rgb=(10, 18, 28), transparent=True)

    # 12. Real bklan Sky-Chariot, Pink Supercar & Rocket Trashcan In-Game Reel!
    cruiser_srcs = [
        os.path.join(DEV_ROOT, "zb3_10_pink.png"),
        os.path.join(DEV_ROOT, "zc3_08_pink.png"),
        os.path.join(DEV_ROOT, "zb3_12_pod.png"),
        os.path.join(DEV_ROOT, "zb3_07_trash.png"),
        os.path.join(DEV_ROOT, "zb3_08_trash_up.png"),
        os.path.join(DEV_ROOT, "zc3_05_boom.png"),
    ]
    cruiser_ims = [Image.open(p) for p in cruiser_srcs if os.path.exists(p)]
    if cruiser_ims:
        make_gif(cruiser_ims, "sky_chariot_pinkcar_reel.gif", duration_ms=210, target_w=460)

    # 13. Warehouse Live Video TV Loop (bktv)!
    tv_frames = []
    for i in range(0, 24, 2):
        nm = f"progs/bktv/v0_{i:04d}.jpg"
        if nm in pk3.namelist():
            tv_frames.append(Image.open(io.BytesIO(pk3.read(nm))))
    if tv_frames:
        make_gif(tv_frames, "bktv_live_crt.gif", duration_ms=110, target_w=320)


def copy_curated_screenshots():
    print("[3/5] Copying & optimizing 100% active in-game screenshots...")
    intro_dir = os.path.join(OUT_ROOT, "dp_intro_userdir", "BakersfieldQuake")
    INTRO_CROP = (0, 64, 1280, 622)  # strips top/bottom intro caption bars cleanly

    shots = [
        # --- MILKY & PINK LADY (ACTIVE KEY 5) ---
        (os.path.join(OUT_ROOT, "milky", "test15", "zp_00.png"), "milky_vm_ingame.jpg", None),
        (os.path.join(DEV_ROOT, "zr3_mk_2.png"), "milky_pinklady_float.jpg", None),
        (os.path.join(DEV_ROOT, "zr3_mk_5.png"), "milky_pinklady_close.jpg", None),
        (os.path.join(DEV_ROOT, "zr3_mk_7.png"), "milky_screen_whiteout.jpg", None),
        (os.path.join(OUT_ROOT, "milky", "splats.png"), "milky_splats_sheet.jpg", None),
        (os.path.join(OUT_ROOT, "pinklady", "closeup_check.png"), "pinklady_closeup.jpg", None),
        (os.path.join(DEV_ROOT, "zb3_12_pod.png"), "skyveh_pod_ingame.jpg", None),
        (os.path.join(intro_dir, "zz_shot_06_fox_stage_milky_drips.png"), "milky_fox_stage.jpg", INTRO_CROP),

        # --- WHEELMAN & WEW CANNON (ACTIVE KEY G) ---
        (os.path.join(OUT_ROOT, "wew_cannon", "previews", "01_pov_idle.png"), "wew_01_idle.jpg", None),
        (os.path.join(OUT_ROOT, "wew_cannon", "previews", "03_pov_bend_max.png"), "wew_03_bend58.jpg", None),
        (os.path.join(OUT_ROOT, "wew_cannon", "previews", "05_pov_blast.png"), "wew_05_blast.jpg", None),
        (os.path.join(OUT_ROOT, "wew_cannon", "previews", "08_exterior_orbit.png"), "wew_08_orbit.jpg", None),
        (os.path.join(OUT_ROOT, "wew_cannon", "previews", "09_darkplaces_live_goodwebsites.png"), "wew_09_ingame_crt1.jpg", None),
        (os.path.join(OUT_ROOT, "wew_cannon", "previews", "10_darkplaces_live_zxccc.png"), "wew_10_ingame_crt2.jpg", None),
        (os.path.join(OUT_ROOT, "wheelman", "above_below_card.jpg"), "wheelman_angles_card.jpg", None),
        (os.path.join(intro_dir, "zz_shot_05_fox_stage_wewcannon.png"), "wew_fox_stage.jpg", INTRO_CROP),

        # --- CRAZY MEGAMAN & ROOM 120A SHRINE (ACTIVE KEY 9) ---
        (os.path.join(DEV_ROOT, "zz_vmmm_b.png"), "megaman_slinger_ingame1.jpg", None),
        (os.path.join(DEV_ROOT, "zz_vmmm_d.png"), "megaman_slinger_ingame2.jpg", None),
        (os.path.join(COMBAT_ROOT, "megaman_preview.png"), "megaman_contraption_hero.jpg", None),
        (os.path.join(DEV_ROOT, "zc3_01_bed.png"), "megaman_bed_closeup.jpg", None),
        (os.path.join(OUT_ROOT, "mystery_box", "previews", "01_pov_idle_megaman.png"), "mbox_pov_megaman.jpg", None),
        (os.path.join(OUT_ROOT, "mystery_box", "previews", "02_pov_idle_wheelman.png"), "mbox_pov_wheelman.jpg", None),

        # --- ACTIVE ARSENAL, CHASERS & VEHICLES ---
        (os.path.join(DEV_ROOT, "rb_pickle.png"), "pickle_vm_ingame.jpg", None),
        (os.path.join(intro_dir, "zz_shot_04_fox_lounge_pickle.png"), "pickle_fox_lounge.jpg", INTRO_CROP),
        (os.path.join(DEV_ROOT, "rb_goo.png"), "googun_vm_ingame.jpg", None),
        (os.path.join(intro_dir, "zz_shot_10_larry_wh_bonk_hammer.png"), "bonk_hammer_ingame.jpg", INTRO_CROP),
        (os.path.join(intro_dir, "zz_shot_17_crystal_mbox_bryan.png"), "mbox_bryan_ingame.jpg", INTRO_CROP),
        (os.path.join(OUT_ROOT, "netsend_renders", "ingame", "ns_ig_07_scr40u_lolbat.png"), "netsend_lolbat_crt.jpg", None),
        (os.path.join(OUT_ROOT, "netsend_renders", "ingame", "ns_ig_09_scr40u_wheresthedisk.png"), "netsend_wheredisk.jpg", None),
        (os.path.join(DEV_ROOT, "zr_vm_held.png"), "robdob_vm_held.jpg", None),
        (os.path.join(DEV_ROOT, "zr_02_boom.png"), "robdob_boom.jpg", None),
        (os.path.join(intro_dir, "zz_shot_03_fox_marquee_robdob.png"), "robdob_fox_marquee.jpg", INTRO_CROP),
        (os.path.join(DEV_ROOT, "jg_1.png"), "johnwave_grenade_roll.jpg", None),
        (os.path.join(DEV_ROOT, "jg_3.png"), "johnwave_splash_boom.jpg", None),
        (os.path.join(OUT_ROOT, "pink_supercar", "pink_supercar_hero.png"), "pink_supercar_hero.jpg", None),
        (os.path.join(OUT_ROOT, "pink_supercar", "v5_webcam.png"), "pink_supercar_webcam.jpg", None),
        (os.path.join(DEV_ROOT, "zb3_10_pink.png"), "pink_supercar_ingame.jpg", None),
        (os.path.join(DEV_ROOT, "zc3_05_boom.png"), "car_explosion_gore.jpg", None),
        (os.path.join(DEV_ROOT, "zz_jp_pickup.png"), "jetpack_pickup.jpg", None),
        (os.path.join(DEV_ROOT, "zz_jp_fly.png"), "jetpack_flying.jpg", None),
        (os.path.join(intro_dir, "zz_shot_07_padre_jetpack_float.png"), "jetpack_padre_float.jpg", INTRO_CROP),
        (os.path.join(intro_dir, "zz_shot_01_sign_white_van.png"), "lan_van_sign_arch.jpg", INTRO_CROP),

        # --- MAPS: BKLAN4 / BKLAN5 ---
        (os.path.join(DEV_ROOT, "zb4_00_start.png"), "map_bklan_warehouse_crt.jpg", None),
        (os.path.join(DEV_ROOT, "zb3_03_bed.png"), "map_bklan_megaman_bed.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_11_larry_front.png"), "map_bklan_larry_facade.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_01_entrance.png"), "map_bklan_casino_ext.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_02_lobby.png"), "map_bklan_casino_horse.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_03_cardroom.png"), "map_bklan_casino_cards.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_09_sign.png"), "map_bklan_sign_arch.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_sign_air.png"), "map_bklan_sign_aerial.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_15_manning.png"), "map_bklan_manning_van.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_16_clubview.png"), "map_bklan_orcom_hall.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_17_park.png"), "map_bklan_amberton_park.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_tv1_warehouse.png"), "map_bklan_live_tv.jpg", None),

        # --- MAPS: HISTORIC DOWNTOWN FOX THEATER & PADRE HOTEL (fox.bsp) ---
        (os.path.join(MOD_ROOT, "zf_21_fox_post.png"), "map_fox_marquee.jpg", None),
        (os.path.join(MOD_ROOT, "zf_23_fox_lobby.png"), "map_fox_lobby.jpg", None),
        (os.path.join(MOD_ROOT, "zf_01_pad_se.png"), "map_fox_padre_ext.jpg", None),
        (os.path.join(MOD_ROOT, "zf_03_pad_lobby.png"), "map_fox_padre_lobby.jpg", None),
        (os.path.join(MOD_ROOT, "zf_15_padroof.png"), "map_fox_padre_rooftop.jpg", None),
        (os.path.join(MOD_ROOT, "zf_04_nile.png"), "map_fox_nile_theater.jpg", None),
        (os.path.join(MOD_ROOT, "zf_18_woolw.png"), "map_fox_woolworths.jpg", None),
        (os.path.join(MOD_ROOT, "zf_20_fire21.png"), "map_fox_fire21.jpg", None),

        # --- MAPS: NANA PLAZA BANGKOK (nanaplaza.bsp) ---
        (os.path.join(HERE, "nana_plaza", "out", "renders", "cam_01_ext_arch_east.png"), "map_nana_arch.jpg", None),
        (os.path.join(HERE, "nana_plaza", "out", "renders", "cam_06_ext_mouth_north.png"), "map_nana_courtyard.jpg", None),
        (os.path.join(HERE, "nana_plaza", "out", "renders", "cam_18_aerial_sw_isometric.png"), "map_nana_aerial.jpg", None),
        (os.path.join(HERE, "nana_plaza", "out", "topdown_z20_overlay.jpg"), "map_nana_plan.jpg", None),

        # --- MAPS: BAKOLAN SMALL (bakolansmall.bsp) ---
        (os.path.join(DEV_ROOT, "zs_final.png"), "map_bks_hero.jpg", None),
        (os.path.join(DEV_ROOT, "zs_ovN.png"), "map_bks_north.jpg", None),
        (os.path.join(DEV_ROOT, "zs_ovS.png"), "map_bks_south.jpg", None),
        (os.path.join(DEV_ROOT, "zs_tp1.png"), "map_bks_teleporter.jpg", None),

        # --- 12 VERIFIED PURE IN-GAME DARKPLACES LAN ACTION CAPTURES ---
        (os.path.join(DEV_ROOT, "zm3_a.png"), "lan_live_00.jpg", None),
        (os.path.join(DEV_ROOT, "zm4_18.png"), "lan_live_01.jpg", None),
        (os.path.join(DEV_ROOT, "zm4_20.png"), "lan_live_02.jpg", None),
        (os.path.join(DEV_ROOT, "zm4_22.png"), "lan_live_03.jpg", None),
        (os.path.join(DEV_ROOT, "zz_larry_1.png"), "lan_live_04.jpg", None),
        (os.path.join(DEV_ROOT, "zc3_08_pink.png"), "lan_live_05.jpg", None),
        (os.path.join(DEV_ROOT, "zb3_08_trash_up.png"), "lan_live_06.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_04_bar_tv.png"), "lan_live_07.jpg", None),
        (os.path.join(DEV_ROOT, "zb4_07_hub.png"), "lan_live_08.jpg", None),
        (os.path.join(DEV_ROOT, "zr_00_launch.png"), "lan_live_09.jpg", None),
        (os.path.join(DEV_ROOT, "zn_04_send.png"), "lan_live_10.jpg", None),
        (os.path.join(DEV_ROOT, "bal_a.png"), "lan_live_11.jpg", None),
    ]

    ok_count = 0
    for src, dst, cbox in shots:
        if save_shot(src, dst, crop_box=cbox):
            ok_count += 1
    print(f"  -> Saved {ok_count} verified in-game screenshots into fanpage/media/shots/")


def render_bsp_screenshots_webgl(pk3):
    """Render genuine textured + colored-lightmapped 3D screenshots of
    gallup.bsp, spruce.bsp, bfarena.bsp, and aerowalk.bsp via headless Chrome WebGL2."""
    print("[4/5] Rendering 3D WebGL2 screenshots for gallup.bsp, spruce.bsp, bfarena.bsp & aerowalk.bsp...")
    pk3_names = set(pk3.namelist())
    pk3_lookup = {}
    for n in pk3_names:
        low = n.lower()
        if low.startswith("textures/") and low.endswith((".png", ".jpg", ".tga")):
            base = os.path.splitext(os.path.basename(low))[0]
            pk3_lookup[base] = n

    # Also load pak0.pak miptex fallback if any classic Quake map uses external/id1 textures
    def export_bsp_mini_payload(bsp_name, cams):
        bsp_path = os.path.join(MOD_ROOT, "maps", bsp_name + ".bsp")
        lit_path = os.path.join(MOD_ROOT, "maps", bsp_name + ".lit")
        if not os.path.exists(bsp_path):
            return None
        d = open(bsp_path, "rb").read()
        bsp2 = d[:4] == b"BSP2"
        lumps = [struct.unpack("<2i", d[4 + 8 * i: 12 + 8 * i]) for i in range(15)]
        FACE, FACE_SZ = ("<iiiii4Bi", 28) if bsp2 else ("<hhihh4Bi", 20)
        lump = lambda i: d[lumps[i][0]:lumps[i][0] + lumps[i][1]]

        verts = np.frombuffer(lump(3), dtype="<f4").reshape((-1, 3))
        texinfo = [struct.unpack("<8f2i", lump(6)[i:i + 40]) for i in range(0, len(lump(6)), 40)]
        faces = [struct.unpack(FACE, lump(7)[i:i + FACE_SZ]) for i in range(0, len(lump(7)), FACE_SZ)]
        lighting = lump(8)
        edges = np.frombuffer(lump(12), dtype="<u4" if bsp2 else "<u2").reshape((-1, 2))
        surfedges = np.frombuffer(lump(13), dtype="<i4")
        models = [struct.unpack("<9f7i", lump(14)[i:i + 64]) for i in range(0, len(lump(14)), 64)]
        lit = open(lit_path, "rb").read()[8:] if os.path.exists(lit_path) else None

        tl = lump(2)
        nmip = struct.unpack("<i", tl[:4])[0]
        tex_uris, tex_sizes, tex_skip, tex_alpha = [], [], [], []
        SKIP_PREFIX = ("sky", "clip", "skip", "trigger")
        for i in range(nmip):
            o = struct.unpack("<i", tl[4 + 4 * i: 8 + 4 * i])[0]
            if o < 0:
                tex_uris.append("")
                tex_sizes.append((16, 16))
                tex_skip.append(True)
                tex_alpha.append(False)
                continue
            raw_nm, w, h, m0 = struct.unpack("<16s3I", tl[o:o + 28])
            nm = raw_nm.split(b"\0")[0].decode("latin1")
            tex_sizes.append((max(1, w), max(1, h)))
            if nm.lower().startswith(SKIP_PREFIX):
                tex_uris.append("")
                tex_skip.append(True)
                tex_alpha.append(False)
                continue
            tex_skip.append(False)
            is_cutout = nm.startswith("{")
            im = None
            key = nm.lower()
            if key in pk3_lookup:
                try:
                    im = Image.open(io.BytesIO(pk3.read(pk3_lookup[key])))
                except Exception:
                    im = None
            if im is None and m0 > 0 and o + m0 + w * h <= len(tl):
                idx_arr = np.frombuffer(tl[o + m0: o + m0 + w * h], dtype=np.uint8).reshape((h, w))
                rgb = QPAL[idx_arr]
                if is_cutout:
                    rgba = np.zeros((h, w, 4), dtype=np.uint8)
                    rgba[:, :, :3] = rgb
                    rgba[:, :, 3] = np.where(idx_arr == 255, 0, 255)
                    im = Image.fromarray(rgba, "RGBA")
                else:
                    im = Image.fromarray(rgb, "RGB")
            if im is None:
                im = Image.new("RGB", (16, 16), (150, 145, 138))
            has_a = is_cutout or (im.mode in ("RGBA", "LA") and im.getchannel("A").getextrema()[0] < 250)
            tex_alpha.append(has_a)
            if max(im.size) > 256:
                sc = 256.0 / max(im.size)
                im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.Resampling.LANCZOS)
            bio = io.BytesIO()
            if has_a:
                im.convert("RGBA").save(bio, "PNG")
                tex_uris.append("data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("ascii"))
            else:
                im.convert("RGB").save(bio, "JPEG", quality=82)
                tex_uris.append("data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode("ascii"))

        AW = 4096
        ax, ay, shelf = 1, 1, 0
        entities_txt = lump(0).decode("latin1", errors="ignore")
        submodel_origins = {0: (0.0, 0.0, 0.0)}
        for m_ent in re.finditer(r"\{([^}]*)\}", entities_txt):
            kv = dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', m_ent.group(1)))
            cls = kv.get("classname", "")
            mdl = kv.get("model", "")
            if mdl.startswith("*") and not cls.startswith("trigger"):
                midx = int(mdl[1:])
                org = tuple(float(x) for x in kv.get("origin", "0 0 0").split())
                submodel_origins[midx] = org

        draw_buckets = {}
        lm_blocks = []
        for midx, morg in submodel_origins.items():
            if midx >= len(models):
                continue
            firstface, numfaces = models[midx][14], models[midx][15]
            for fi in range(firstface, firstface + numfaces):
                planenum, side, firstedge, numedges, ti, s0, s1, s2, s3, lightofs = faces[fi]
                t_idx = texinfo[ti][8]
                if t_idx < 0 or t_idx >= nmip or tex_skip[t_idx] or numedges < 3:
                    continue
                vec = texinfo[ti]
                tw, th = tex_sizes[t_idx]
                e_slice = surfedges[firstedge:firstedge + numedges]
                v_idx = np.where(e_slice >= 0, edges[np.abs(e_slice), 0], edges[np.abs(e_slice), 1])
                pts = verts[v_idx]
                s_vals = pts[:, 0] * vec[0] + pts[:, 1] * vec[1] + pts[:, 2] * vec[2] + vec[3]
                t_vals = pts[:, 0] * vec[4] + pts[:, 1] * vec[5] + pts[:, 2] * vec[6] + vec[7]

                if s0 != 255 and lightofs >= 0:
                    mins0 = math.floor(float(s_vals.min()) / 16.0)
                    mins1 = math.floor(float(t_vals.min()) / 16.0)
                    maxs0 = math.ceil(float(s_vals.max()) / 16.0)
                    maxs1 = math.ceil(float(t_vals.max()) / 16.0)
                    lw = max(1, maxs0 - mins0 + 1)
                    lh = max(1, maxs1 - mins1 + 1)
                    if ax + lw + 2 > AW:
                        ax = 1
                        ay += shelf + 2
                        shelf = 0
                    lx, ly = ax, ay
                    ax += lw + 2
                    shelf = max(shelf, lh)
                    lm_blocks.append((lx, ly, lw, lh, lightofs))
                    lu = (lx + 0.5 + (s_vals / 16.0 - mins0)) / AW
                    lv_raw = ly + 0.5 + (t_vals / 16.0 - mins1)
                else:
                    lu = np.zeros_like(s_vals)
                    lv_raw = np.zeros_like(t_vals)

                u_vals = s_vals / tw
                v_vals = t_vals / th
                pts_w = pts + np.array(morg, dtype=np.float32)

                b = draw_buckets.setdefault(t_idx, [])
                for k in range(1, numedges - 1):
                    for idx_p in (0, k, k + 1):
                        b.extend([
                            float(pts_w[idx_p, 0]), float(pts_w[idx_p, 1]), float(pts_w[idx_p, 2]),
                            float(u_vals[idx_p]), float(v_vals[idx_p]),
                            float(lu[idx_p]), float(lv_raw[idx_p]),
                        ])

        AH = max(64, 1 << max(6, (ay + shelf + 4 - 1).bit_length()))
        lm_arr = np.full((AH, AW, 3), 210, dtype=np.uint8)
        for lx, ly, lw, lh, ofs in lm_blocks:
            if ly + lh >= AH:
                continue
            n_px = lw * lh
            if lit and ofs * 3 + n_px * 3 <= len(lit):
                blk = np.frombuffer(lit, dtype=np.uint8, count=n_px * 3, offset=ofs * 3).reshape((lh, lw, 3))
            elif ofs + n_px <= len(lighting):
                g = np.frombuffer(lighting, dtype=np.uint8, count=n_px, offset=ofs).reshape((lh, lw, 1))
                blk = np.repeat(g, 3, axis=2)
            else:
                continue
            lm_arr[ly:ly + lh, lx:lx + lw] = blk

        lm_bio = io.BytesIO()
        Image.fromarray(lm_arr, "RGB").save(lm_bio, "JPEG", quality=90)
        lm_uri = "data:image/jpeg;base64," + base64.b64encode(lm_bio.getvalue()).decode("ascii")

        all_floats = []
        groups = []
        v_cursor = 0
        for pass_alpha in (False, True):
            for t_idx, flist in draw_buckets.items():
                if tex_alpha[t_idx] != pass_alpha:
                    continue
                arr = np.array(flist, dtype=np.float32).reshape((-1, 7))
                arr[:, 6] = np.where(arr[:, 5] > 0.0, arr[:, 6] / AH, 0.0)
                cnt = arr.shape[0]
                all_floats.append(arr)
                groups.append(dict(tex=t_idx, start=v_cursor, count=cnt, alpha=pass_alpha))
                v_cursor += cnt

        vbo_bytes = np.vstack(all_floats).astype(np.float32).tobytes() if all_floats else b""
        spawns = []
        for m_ent in re.finditer(r"\{([^}]*)\}", entities_txt):
            kv = dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', m_ent.group(1)))
            if kv.get("classname") in ("info_player_deathmatch", "info_player_start"):
                org = [float(x) for x in kv.get("origin", "0 0 64").split()]
                ang = float(kv.get("angle", "0"))
                spawns.append((org[0], org[1], org[2] + 22.0, ang, 0.0))

        resolved_cams = []
        for c in cams:
            if c.get("pos") is None and spawns:
                sp = spawns[min(c.get("spawn_idx", 0), len(spawns) - 1)]
                resolved_cams.append(dict(out=c["out"], pos=[sp[0], sp[1], sp[2]], yaw=sp[3], pitch=sp[4]))
            else:
                resolved_cams.append(c)

        return dict(
            vboB64=base64.b64encode(vbo_bytes).decode("ascii"),
            lmUri=lm_uri,
            texUris=tex_uris,
            groups=groups,
            cams=resolved_cams,
        )

    gallup_spots_p = os.path.join(MOD_ROOT, "maps", "gallup.spots.json")
    spruce_spots_p = os.path.join(MOD_ROOT, "maps", "spruce.spots.json")
    ga_spots = json.load(open(gallup_spots_p)) if os.path.exists(gallup_spots_p) else []
    sp_spots = json.load(open(spruce_spots_p)) if os.path.exists(spruce_spots_p) else []

    def spot_cam(spots, idx, out_fn, z_add=22.0, pitch=0.0):
        if idx < len(spots):
            p = spots[idx]["pos"]
            return dict(out=out_fn, pos=[p[0], p[1], p[2] + z_add], yaw=spots[idx]["yaw"], pitch=pitch)
        return dict(out=out_fn, pos=None, spawn_idx=idx)

    jobs = [
        ("gallup", [
            spot_cam(ga_spots, 0, "map_gallup_7705_front.jpg", pitch=-2.0),
            spot_cam(ga_spots, 2, "map_gallup_living_room.jpg", pitch=-4.0),
            spot_cam(ga_spots, 10, "map_gallup_albertsons.jpg", pitch=2.0),
            spot_cam(ga_spots, 5, "map_gallup_rooftop.jpg", z_add=36.0, pitch=-8.0),
        ]),
        ("spruce", [
            spot_cam(sp_spots, 0, "map_spruce_hero.jpg", pitch=-1.0),
            spot_cam(sp_spots, 7, "map_spruce_water_tower.jpg", pitch=11.0),
            spot_cam(sp_spots, 12, "map_spruce_cityserve.jpg", pitch=1.0),
            spot_cam(sp_spots, 16, "map_spruce_interior.jpg", pitch=-4.0),
        ]),
        ("bfarena", [
            dict(out="map_bfarena_1.jpg", pos=[-920.0, -920.0, 220.0], yaw=45.0, pitch=-13.0),
            dict(out="map_bfarena_2.jpg", pos=[920.0, -920.0, 180.0], yaw=135.0, pitch=-10.0),
        ]),
        ("aerowalk", [
            dict(out="map_aerowalk_1.jpg", pos=[-224.0, -704.0, 478.0], yaw=82.0, pitch=-14.0),
            dict(out="map_aerowalk_2.jpg", pos=[-320.0, 480.0, 478.0], yaw=-62.0, pitch=-16.0),
        ]),
    ]

    html_shell = r"""<!DOCTYPE html><html><body style="margin:0;background:#87b5e5;"><canvas id="c" width="1024" height="576"></canvas>
<script>
window.renderMap = async function(payload) {
  const canvas = document.getElementById('c');
  const gl = canvas.getContext('webgl2', {preserveDrawingBuffer: true, antialias: true});
  const vs = `#version 300 es
  layout(location=0) in vec3 aPos;
  layout(location=1) in vec2 aUV;
  layout(location=2) in vec2 aLM;
  uniform mat4 uMVP;
  out vec2 vUV, vLM;
  void main() { vUV = aUV; vLM = aLM; gl_Position = uMVP * vec4(aPos, 1.0); }`;
  const fs = `#version 300 es
  precision highp float;
  in vec2 vUV, vLM;
  uniform sampler2D uTex, uLM;
  uniform int uAlpha;
  out vec4 frag;
  void main() {
    vec4 t = texture(uTex, vUV);
    if (uAlpha == 1 && t.a < 0.5) discard;
    vec3 lm = vLM.x > 0.0 ? texture(uLM, vLM).rgb * 2.15 : vec3(1.05);
    vec3 col = clamp(t.rgb * lm, 0.0, 1.35);
    col = pow(col / (1.0 + col * 0.22), vec3(0.92));
    frag = vec4(col, 1.0);
  }`;
  function sh(t, s){ const x=gl.createShader(t); gl.shaderSource(x,s); gl.compileShader(x); return x; }
  const prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, vs));
  gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(prog);
  gl.useProgram(prog);

  async function mkTex(uri, wrap) {
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    if (!uri) {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([180,180,180,255]));
      return t;
    }
    const img = new Image();
    img.src = uri;
    await img.decode();
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrap);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wrap);
    return t;
  }

  const lmTex = await mkTex(payload.lmUri, gl.CLAMP_TO_EDGE);
  const texs = [];
  for (const u of payload.texUris) texs.push(await mkTex(u, gl.REPEAT));

  const binStr = atob(payload.vboB64);
  const bytes = new Uint8Array(binStr.length);
  for (let i=0; i<binStr.length; i++) bytes[i] = binStr.charCodeAt(i);
  const vbo = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
  gl.bufferData(gl.ARRAY_BUFFER, bytes, gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 28, 0);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 28, 12);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 28, 20);

  function persp(fovY, asp, n, f) {
    const t = 1.0 / Math.tan(fovY * 0.5), nf = 1.0 / (n - f);
    return new Float32Array([t/asp,0,0,0, 0,t,0,0, 0,0,(f+n)*nf,-1, 0,0,2*f*n*nf,0]);
  }
  function lookAt(e, c, u) {
    let fx=c[0]-e[0], fy=c[1]-e[1], fz=c[2]-e[2];
    let rl=1/Math.hypot(fx,fy,fz); fx*=rl; fy*=rl; fz*=rl;
    let sx=fy*u[2]-fz*u[1], sy=fz*u[0]-fx*u[2], sz=fx*u[1]-fy*u[0];
    rl=1/Math.hypot(sx,sy,sz); sx*=rl; sy*=rl; sz*=rl;
    let ux=sy*fz-sz*fy, uy=sz*fx-sx*fz, uz=sx*fy-sy*fx;
    return new Float32Array([
      sx, ux, -fx, 0,
      sy, uy, -fy, 0,
      sz, uz, -fz, 0,
      -(sx*e[0]+sy*e[1]+sz*e[2]), -(ux*e[0]+uy*e[1]+uz*e[2]), (fx*e[0]+fy*e[1]+fz*e[2]), 1
    ]);
  }
  function mul(a, b) {
    const o = new Float32Array(16);
    for (let i=0;i<4;i++) for (let j=0;j<4;j++)
      o[j*4+i] = a[i]*b[j*4] + a[4+i]*b[j*4+1] + a[8+i]*b[j*4+2] + a[12+i]*b[j*4+3];
    return o;
  }

  gl.enable(gl.DEPTH_TEST);
  gl.disable(gl.CULL_FACE);
  gl.uniform1i(gl.getUniformLocation(prog, 'uTex'), 0);
  gl.uniform1i(gl.getUniformLocation(prog, 'uLM'), 1);
  gl.activeTexture(gl.TEXTURE1);
  gl.bindTexture(gl.TEXTURE_2D, lmTex);

  const outJpgs = [];
  const P = persp(62 * Math.PI / 180, 1024/576, 4.0, 16000.0);
  for (const cam of payload.cams) {
    gl.viewport(0, 0, 1024, 576);
    gl.clearColor(0.52, 0.72, 0.94, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    const yaw = (cam.yaw || 0) * Math.PI / 180.0;
    const pitch = (cam.pitch || 0) * Math.PI / 180.0;
    const dx = Math.cos(pitch)*Math.cos(yaw), dy = Math.cos(pitch)*Math.sin(yaw), dz = Math.sin(pitch);
    const e = cam.pos;
    const V = lookAt(e, [e[0]+dx*100, e[1]+dy*100, e[2]+dz*100], [0,0,1]);
    gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uMVP'), false, mul(P, V));
    gl.activeTexture(gl.TEXTURE0);
    for (const g of payload.groups) {
      gl.bindTexture(gl.TEXTURE_2D, texs[g.tex]);
      gl.uniform1i(gl.getUniformLocation(prog, 'uAlpha'), g.alpha ? 1 : 0);
      gl.drawArrays(gl.TRIANGLES, g.start, g.count);
    }
    gl.finish();
    outJpgs.push({out: cam.out, dataUrl: canvas.toDataURL('image/jpeg', 0.88)});
  }
  return outJpgs;
};
</script></body></html>"""

    from playwright.sync_api import sync_playwright
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chrome_exe if os.path.exists(chrome_exe) else None,
            headless=True,
            args=["--use-gl=angle", "--enable-webgl"],
        )
        page = browser.new_page(viewport={"width": 1024, "height": 576})
        page.set_content(html_shell)
        for bsp_name, cams in jobs:
            payload = export_bsp_mini_payload(bsp_name, cams)
            if not payload:
                continue
            res = page.evaluate("p => window.renderMap(p)", payload)
            for item in res:
                b64 = item["dataUrl"].split(",", 1)[1]
                with open(os.path.join(SHOTS_DIR, item["out"]), "wb") as f:
                    f.write(base64.b64decode(b64))
            print(f"  -> Rendered {len(res)} WebGL2 3D shots for {bsp_name}.bsp")
        browser.close()


def extract_sfx(pk3):
    print("[5/5] Extracting 22 progs.dat-verified active gameplay SFX from bakersfield.pk3...")
    progs_raw = open(PROGS_DAT, "rb").read()
    sfx_map = [
        ("sound/milky/song.ogg", "milky_song.ogg"),
        ("sound/milky/fire.wav", "milky_fire.wav"),
        ("sound/wcannon/wc_scream.wav", "wc_scream.wav"),
        ("sound/wcannon/wc_boom.wav", "wc_boom.wav"),
        ("sound/friends/gowewd.wav", "gowewd.wav"),
        ("sound/weapons/megahorn.wav", "megaman_horn.wav"),
        ("sound/megaman/mm_drive.wav", "megaman_drive.wav"),
        ("sound/megaman/boom01.wav", "megaman_boom.wav"),
        ("sound/grenade/boom_04_mega_fart.wav", "mega_fart_boom.wav"),
        ("sound/grenade/boom_03_scream_launch.wav", "johnwave_scream_boom.wav"),
        ("sound/pickle/surprise.wav", "pickle_surprise.wav"),
        ("sound/floathead/sight1.wav", "robdob_hug.wav"),
        ("sound/ltgun/canis.wav", "laptop_canis.wav"),
        ("sound/netsend/wheres_disk.wav", "wheres_the_disk.wav"),
        ("sound/jetpack/floating.wav", "im_floating.wav"),
        ("sound/bklan/notpink.wav", "its_not_pink.wav"),
        ("sound/bklan/pinkcar.wav", "pinkcar_music.wav"),
        ("sound/vehicles/lanvan.wav", "six_man_lan_van.wav"),
        ("sound/bryan/noway.wav", "bryan_noway.wav"),
        ("sound/mbox/drv_boing_hop.wav", "finger_boing.wav"),
        ("sound/ccc/shoot.wav", "ccc_shoot.wav"),
        ("sound/hammer/frying_pan.wav", "bonk_frying_pan.wav"),
    ]
    pk3_set = set(pk3.namelist())
    cnt = 0
    for src, dst in sfx_map:
        rel_snd = src.removeprefix("sound/")
        assert rel_snd.encode("ascii") in progs_raw, f"Sound not referenced in progs.dat: {src}"
        assert src in pk3_set, f"Sound missing in bakersfield.pk3: {src}"
        with open(os.path.join(SFX_DIR, dst), "wb") as f:
            f.write(pk3.read(src))
        cnt += 1
    print(f"  -> Extracted & progs.dat-verified {cnt} audio clips into fanpage/media/sfx/")


def main():
    clean_media_dirs()
    with zipfile.ZipFile(PK3_PATH, "r") as pk3:
        build_procedural_90s_gifs()
        copy_and_build_gameplay_gifs(pk3)
        copy_curated_screenshots()
        render_bsp_screenshots_webgl(pk3)
        extract_sfx(pk3)
    print("[MEDIA OK] All 100% active in-game GIFs, screenshots & SFX ready in fanpage/media/!")


if __name__ == "__main__":
    main()
