r"""High-Precision 2048x2048 Studio Texture, Emissive Glow, PBR ORM & Glass Painter
for the Pink Exotic Mid-Engine Supercar ("It's not pink") with:
  - Painted Hood Mural: Uploaded portrait + "Say no to drugs." blended seamlessly onto
    the sculpted metallic candy-pink supercar hood inside a custom racing crest
  - Side Livery: Bold "It's not pink" street-racing typography on BOTH Left (+Y) and
    Right (-Y) scissor doors — oriented cleanly left-to-right on BOTH sides!
  - Roof-Mounted PC Streamer Webcam: Dedicated multi-coated optical lens, stereo mic
    grilles, "HD 1080p · LIVE" bezel, glowing status LED, monitor clip & gaffer-taped USB cord
  - Exotic Supercar Details: Y-blade LED headlights, full-width rear LED lightbar,
    2x2 twill carbon fiber, quilted pink/black racing bucket seats, digital cockpit dash,
    mid-mounted V12 engine, forged 10-spoke wheels, and "NOT PINK" vanity plate.
"""
import math
import os
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import ndimage

W_ATLAS = 2048
H_ATLAS = 2048

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REF_JPG = os.path.join(HERE, "out", "pink_supercar", "hood_ref.jpg")

# Master Supercar Coordinates (Quake units, ~42u/m, z=0 exact ground)
CAR_SPEC = dict(
    kind="pink_supercar",
    x0=-96.0,           # Rear diffuser trailing edge
    x1=98.0,            # Front splitter nose tip (194u = 4.62m length)
    hw=43.0,            # Max rear haunch half-width (86u = 2.05m wide)
    hw_waist=39.2,      # Sculpted door waist half-width
    hw_front=41.4,      # Front fender flare half-width
    z_bot=4.6,          # Low supercar splitter/floor clearance
    z_skirt=7.2,        # Carbon side-skirt top
    z_bmp_f=14.8,       # Front hood nose leading edge height
    z_cowl=29.2,        # Base of windshield / rear of hood
    z_belt=31.0,        # Door beltline height
    z_roof=46.2,        # Exotic low-slung roof peak (1.10m!)
    z_deck_rear=34.2,   # Rear tail / taillight deck height
    # Staggered forged wheels (exact z=0 tire contact!)
    wheel_x_f=57.0,
    wheel_y_f=36.0,
    wheel_r_f=13.2,
    wheel_w_f=9.8,
    arch_r_f=15.6,
    wheel_x_r=-55.0,
    wheel_y_r=37.4,
    wheel_r_r=14.4,
    wheel_w_r=12.4,
    arch_r_r=17.0,
    # Hood UV bounds (dedicated distortion-free hood mural projection)
    x_hood_rear=26.5,
    x_hood_front=92.0,
    y_hood_max=28.0,
    # Scissor door bounds (where "It's not pink" lives!)
    x_door_rear=-21.0,
    x_door_front=41.5,
    # Greenhouse & roof
    x_ws_top=-1.5,
    x_roof_rear=-21.0,
    # Roof Webcam anchor
    cam_x=-2.0,
    cam_y=0.0,
    cam_z_base=46.0,
    cam_pivot_z=53.0,
)

# 2048x2048 Atlas Rectangles (px0, py0, px1, py1)
R_SIDE_L      = (16,   16,  1136,  416)   # Left (+Y) driver side: +X on left, -X on right
R_SIDE_R      = (16,  432,  1136,  832)   # Right (-Y) passenger side: -X on left, +X on right
R_HOOD        = (1152, 16,  2032, 1072)   # 880x1056 ultra-crisp hood canvas
R_FRONT       = (16,  848,   656, 1248)   # Front splitter, honeycomb intakes, Y-blade LEDs
R_REAR        = (672, 848,  1136, 1248)   # Rear LED bar, honeycomb grille, NOT PINK plate, diffuser
R_TOP         = (16, 1264,   752, 1664)   # Roof & slotted V12 rear engine deck
R_WEBCAM_F    = (768, 1264, 1344, 1552)   # Webcam front faceplate (mic grilles, bezel, LIVE LED)
R_WEBCAM_LENS = (1360, 1088, 1680, 1408)  # Dedicated optical coated lens objective
R_WHEEL       = (16, 1680,   368, 2032)   # 352x352 10-spoke forged wheel + pink caliper + tire wall
R_TREAD       = (384, 1680,  672, 2032)   # Wide semi-slick performance tire tread
R_CARBON      = (688, 1568,  992, 1856)   # 2x2 twill gloss carbon fiber weave
R_PINK_MET    = (1008, 1568, 1312, 1856)  # Clean metallic hot candy-pink swatch
R_CHROME      = (1328, 1424, 1584, 1680)  # Brushed titanium / mirror chrome
R_TRIM_BLK    = (1600, 1424, 1856, 1680)  # Matte anodized black / rubber / cable trim
R_DUCT_TAPE   = (1872, 1424, 2032, 1680)  # Silver/pink gaffer tape swatch
R_SEAT        = (1328, 1696, 1664, 2032)  # Quilted black & hot-pink racing bucket seat
R_DASH        = (1680, 1696, 2032, 2032)  # Digital supercar dash + LIVE webcam feed screen
R_ENGINE      = (688, 1872, 1312, 2032)   # Mid-mounted V12 pink valve covers & chrome stacks


def clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def uv_in_rect(rect, su, sv, pad=5.0):
    x0, y0, x1, y1 = rect
    px = (x0 + pad) + (x1 - x0 - 2.0 * pad) * clamp01(su)
    py = (y0 + pad) + (y1 - y0 - 2.0 * pad) * clamp01(sv)
    return (round(px / W_ATLAS, 5), round(py / H_ATLAS, 5))


def side_uv(x, z, is_left):
    """Maps world (x, z) to R_SIDE_L or R_SIDE_R such that su=0->1 ALWAYS goes
    viewer-left to viewer-right when looking directly at that side of the car!"""
    tx = clamp01((x - CAR_SPEC["x0"]) / (CAR_SPEC["x1"] - CAR_SPEC["x0"]))
    tz = clamp01((z - CAR_SPEC["z_bot"]) / (CAR_SPEC["z_roof"] - CAR_SPEC["z_bot"]))
    su = (1.0 - tx) if is_left else tx
    rect = R_SIDE_L if is_left else R_SIDE_R
    return uv_in_rect(rect, su, 1.0 - tz, pad=6.0)


def hood_uv(x, y):
    """Maps world (x, y) on the front hood to R_HOOD:
      - Standing in front (+X looking -X):
        viewer left (-Y) -> su=0, viewer right (+Y) -> su=1
        cowl/windshield (x_hood_rear) -> sv=0 (top of head)
        front nose (x_hood_front)     -> sv=1 ('Say no to drugs.')"""
    su = clamp01((y + CAR_SPEC["y_hood_max"]) / (2.0 * CAR_SPEC["y_hood_max"]))
    sv = clamp01((x - CAR_SPEC["x_hood_rear"]) / (CAR_SPEC["x_hood_front"] - CAR_SPEC["x_hood_rear"]))
    return uv_in_rect(R_HOOD, su, sv, pad=8.0)


def front_uv(y, z):
    ty = clamp01((y + CAR_SPEC["hw_front"]) / (2.0 * CAR_SPEC["hw_front"]))
    tz = clamp01((z - 5.2) / (16.6 - 5.2))
    return uv_in_rect(R_FRONT, ty, 1.0 - tz, pad=6.0)


def rear_uv(y, z):
    ty = clamp01((CAR_SPEC["hw"] - y) / (2.0 * CAR_SPEC["hw"]))
    tz = clamp01((z - CAR_SPEC["z_bot"]) / (CAR_SPEC["z_deck_rear"] + 4.0 - CAR_SPEC["z_bot"]))
    return uv_in_rect(R_REAR, ty, 1.0 - tz, pad=6.0)


def top_uv(x, y):
    tx = clamp01((x - CAR_SPEC["x0"]) / (CAR_SPEC["x_hood_rear"] - CAR_SPEC["x0"]))
    ty = clamp01((y + CAR_SPEC["hw"]) / (2.0 * CAR_SPEC["hw"]))
    return uv_in_rect(R_TOP, tx, ty, pad=6.0)


def _load_font(names, size):
    font_dir = r"C:\Windows\Fonts"
    for nm in names:
        p = os.path.join(font_dir, nm)
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _paint_candy_pink_rect(arr, rect, horizon_bias=0.45):
    """Fills a rectangle with rich metallic hot-bubblegum / candy-pearl pink automotive paint."""
    x0, y0, x1, y1 = rect
    h = max(1, y1 - y0)
    w = max(1, x1 - x0)
    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    xx = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]

    # Studio automotive horizon reflection curve: bright pearl-pink top -> luscious hot-pink mid -> deep rose base
    spec_band = np.exp(-((yy - horizon_bias) ** 2) / 0.028)
    top_lift = np.clip(1.0 - yy * 1.4, 0.0, 1.0) ** 1.5
    low_shade = np.clip((yy - 0.62) / 0.38, 0.0, 1.0) ** 1.4

    # Subtle micro-metallic flake sparkle
    rng = np.random.default_rng(1337 + x0 * 7 + y0)
    flake = rng.normal(0.0, 2.2, size=(h, w)).astype(np.float32)
    crown = 6.0 * np.sin(np.pi * xx)

    r = 250.0 + 5.0 * top_lift + 5.0 * spec_band - 26.0 * low_shade + 0.3 * crown + flake
    g = 86.0 + 58.0 * top_lift + 68.0 * spec_band - 34.0 * low_shade + crown + flake * 0.8
    b = 168.0 + 44.0 * top_lift + 48.0 * spec_band - 30.0 * low_shade + 0.7 * crown + flake * 0.9

    sub = np.stack([np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255)], axis=-1).astype(np.uint8)
    arr[y0:y1, x0:x1] = sub


def _paint_carbon_weave(arr, rect, scale=4):
    """2x2 twill carbon fiber weave pattern."""
    x0, y0, x1, y1 = rect
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    phase = ((xx // scale) + (yy // scale)) % 4
    diag = ((xx - yy) // scale) % 2
    val = np.where(phase < 2, 34 + 12 * diag, 20 + 6 * diag).astype(np.float32)
    sheen = 10.0 * np.sin(np.pi * (yy / max(1.0, float(h))))
    c = np.clip(val + sheen, 12, 68).astype(np.uint8)
    arr[y0:y1, x0:x1] = np.stack([c, c + 1, c + 3], axis=-1)


def _paint_hood_mural(atlas_im, orm_arr, ref_jpg_path):
    """Paints the sculpted pink supercar hood in R_HOOD with the uploaded portrait +
    'Say no to drugs.' seamlessly matted & framed inside a custom supercar hood crest."""
    x0, y0, x1, y1 = R_HOOD
    W, H = x1 - x0, y1 - y0  # 880 x 1056

    # 1. Start from rich metallic candy-pink hood base with sculpted outer power-fender creases
    hood_rgba = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    xx = np.linspace(-1.0, 1.0, W, dtype=np.float32)[None, :]

    # V-tapered hood crease lines running from cowl corners toward nose
    crease_pos = 0.78 - 0.14 * yy  # |xx| ~ 0.78 at cowl narrowing to 0.64 near nose
    crease_hi = np.exp(-((np.abs(xx) - crease_pos) ** 2) / 0.0022)
    crease_sh = np.exp(-((np.abs(xx) - (crease_pos + 0.028)) ** 2) / 0.0018)

    # Central airbrushed pearl-rose sunburst halo behind the mural!
    rad = np.hypot(xx * 1.12, (yy - 0.48) * 1.05)
    halo = np.clip(1.0 - rad / 0.78, 0.0, 1.0) ** 1.6
    ang = np.arctan2(yy - 0.46, xx)
    rays = 0.5 + 0.5 * np.cos(ang * 18.0)
    ray_burst = halo * (0.65 + 0.35 * rays)

    r = 248.0 + 7.0 * ray_burst + 10.0 * crease_hi - 34.0 * crease_sh - 10.0 * (yy ** 1.6)
    g = 82.0 + 115.0 * ray_burst + 55.0 * crease_hi - 36.0 * crease_sh + 18.0 * (1.0 - yy)
    b = 165.0 + 72.0 * ray_burst + 40.0 * crease_hi - 32.0 * crease_sh + 12.0 * (1.0 - yy)
    base_rgb = np.stack([np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255)], axis=-1).astype(np.uint8)
    hood_im = Image.fromarray(base_rgb, "RGB").convert("RGBA")

    # 2. Load reference photo (667 x 1024) and cleanly matte out ONLY exterior studio white
    ref = Image.open(ref_jpg_path).convert("RGB")
    ra = np.asarray(ref, dtype=np.float32)
    rh, rw, _ = ra.shape

    dist_w = np.sqrt(((ra - 255.0) ** 2).sum(axis=2))
    cand_bg = dist_w < 30.0
    lbl, num = ndimage.label(cand_bg)
    seeds = {int(lbl[0, 0]), int(lbl[0, rw - 1]), int(lbl[rh - 1, 0])} - {0}
    # Also include enclosed counter hole inside 'a' of 'Say' on bottom-left (x < 130, y > 920)
    for k in range(1, num + 1):
        if k in seeds:
            continue
        ys_k, xs_k = np.nonzero(lbl == k)
        if len(ys_k) > 8 and ys_k.min() > 920 and xs_k.max() < 130:
            seeds.add(k)
    ext_bg = np.isin(lbl, list(seeds))

    # Soft hair/edge anti-aliased alpha ramp near exterior studio white boundary
    dist_to_fg = ndimage.distance_transform_edt(ext_bg)
    dist_to_bg = ndimage.distance_transform_edt(~ext_bg)
    # Unmix white studio backdrop on fine hair boundary (within 5px of exterior white)
    whiteness = 1.0 - np.clip(dist_w / 95.0, 0.0, 1.0)
    alpha = np.where(ext_bg, 0.0, 1.0).astype(np.float32)
    # Protect bottom red/black text (y > 880) from aggressive hair erosion!
    rows_2d = np.arange(rh)[:, None]
    hair_band = (~ext_bg) & (dist_to_bg <= 5.0) & (rows_2d < 880)
    alpha[hair_band] = np.clip((1.0 - whiteness[hair_band]) * 1.18, 0.0, 1.0)
    text_band = (~ext_bg) & (dist_to_bg <= 2.2) & (rows_2d >= 880)
    alpha[text_band] = np.clip(1.0 - 0.85 * whiteness[text_band], 0.0, 1.0)
    alpha = ndimage.gaussian_filter(alpha, sigma=0.55)
    alpha[dist_to_fg > 1.2] = 0.0

    # Decontaminate white spill on hair & shirt-edge boundary pixels
    ra_clean = ra.copy()
    decon = (alpha > 0.01) & (alpha < 0.99) & (dist_to_bg <= 5.5)
    for c_i in range(3):
        ra_clean[..., c_i][decon] = np.clip(
            (ra[..., c_i][decon] - (1.0 - alpha[decon]) * 255.0) / np.maximum(alpha[decon], 0.22),
            0.0, 255.0
        )

    # Scale portrait cleanly to fit generously on the hood (aspect-locked 1:1!)
    # Target height = 870 px (of 1056 px hood length -> covers ~82% of the entire hood!)
    tgt_h = 876
    tgt_w = int(round(rw * (tgt_h / float(rh))))  # ~571 px wide (centered in 880 px!)
    subj_rgba = np.dstack([ra_clean.astype(np.uint8), np.clip(alpha * 255.0, 0, 255).astype(np.uint8)])
    subj_im = Image.fromarray(subj_rgba, "RGBA").resize((tgt_w, tgt_h), Image.Resampling.LANCZOS)

    px_off = (W - tgt_w) // 2
    py_off = 88  # Leaves sleek pink cowl margin at top & nose margin below "Say no to drugs."

    # 3. Build a sleek Supercar Hood Shield / Crest Mask so the right (x=666) & bottom (y=1023)
    #    shirt crop edges sit flush inside a custom racing shield pinstripe (while 100% of his
    #    hair and 100% of "Say no to drugs." remain completely unclipped!)
    crest_mask = Image.new("L", (W, H), 0)
    cd = ImageDraw.Draw(crest_mask)
    cx0, cy0 = px_off - 18, py_off - 16
    cx1, cy1 = px_off + tgt_w, py_off + tgt_h
    # Shield polygon: wide across top & "Say no to drugs." row, beveled race-crest corners
    shield_pts = [
        (cx0 + 36, cy0),
        (cx1 - 24, cy0),
        (cx1, cy0 + 34),
        (cx1, cy1 - 26),
        (cx1 - 28, cy1),
        (cx0 + 28, cy1),
        (cx0, cy1 - 26),
        (cx0, cy0 + 34),
    ]
    cd.polygon(shield_pts, fill=255)

    # Subtle hot-magenta + white pearl inner backdrop inside the shield before compositing portrait
    shield_bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sbd = ImageDraw.Draw(shield_bg)
    sbd.polygon(shield_pts, fill=(255, 145, 202, 115))
    hood_im = Image.alpha_composite(hood_im, shield_bg)

    # Soft drop-shadow behind the subject + text so he pops off the metallic pink hood!
    subj_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    subj_layer.paste(subj_im, (px_off, py_off))
    # Clip subject layer cleanly to shield_pts so right & bottom shirt edges match the shield border!
    subj_alpha = ImageChops.multiply(subj_layer.getchannel("A"), crest_mask)
    subj_layer.putalpha(subj_alpha)

    shadow_a = subj_alpha.filter(ImageFilter.GaussianBlur(radius=9))
    shadow_layer = Image.new("RGBA", (W, H), (72, 8, 42, 0))
    shadow_layer.putalpha(shadow_a.point(lambda p: min(175, int(p * 0.72))))
    hood_im = Image.alpha_composite(hood_im, shadow_layer)
    hood_im = Image.alpha_composite(hood_im, subj_layer)

    # Crisp double racing pinstripe border around the hood crest (gloss black + pearl white + hot magenta)
    hd = ImageDraw.Draw(hood_im)
    hd.line(shield_pts + [shield_pts[0]], fill=(18, 12, 20, 245), width=9, joint="curve")
    hd.line(shield_pts + [shield_pts[0]], fill=(255, 244, 250, 245), width=3, joint="curve")

    # Small supercar nose emblem right near the front tip of the hood (sv ~ 0.965)
    em_cx, em_cy = W // 2, H - 34
    hd.polygon([(em_cx - 18, em_cy - 12), (em_cx + 18, em_cy - 12), (em_cx + 12, em_cy + 12), (em_cx - 12, em_cy + 12)],
               fill=(22, 18, 26, 255), outline=(245, 220, 120, 255), width=2)

    atlas_im.paste(hood_im.convert("RGB"), (x0, y0))
    # Glossy clearcoat ORM over the painted hood (metallic=0.22, roughness=0.18)
    orm_arr[y0:y1, x0:x1] = [255, 46, 56]


def _paint_side_panel(atlas_im, glow_im, orm_arr, rect, is_left):
    """Paints Left (+Y) or Right (-Y) supercar profile with bold 'It's not pink' door livery.
    Remember: su=0..1 ALWAYS runs viewer-left -> viewer-right!"""
    x0, y0, x1, y1 = rect
    W, H = x1 - x0, y1 - y0  # 1120 x 400
    pad = 6.0

    sub_arr = np.zeros((H, W, 3), dtype=np.uint8)
    _paint_candy_pink_rect(sub_arr, (0, 0, W, H), horizon_bias=0.40)
    panel = Image.fromarray(sub_arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(panel)

    def wx_to_px(wx):
        tx = clamp01((wx - CAR_SPEC["x0"]) / (CAR_SPEC["x1"] - CAR_SPEC["x0"]))
        su = (1.0 - tx) if is_left else tx
        return pad + (W - 2.0 * pad) * su

    def wz_to_py(wz):
        tz = clamp01((wz - CAR_SPEC["z_bot"]) / (CAR_SPEC["z_roof"] - CAR_SPEC["z_bot"]))
        return (H - pad) - (H - 2.0 * pad) * tz

    # 1. Lower carbon-fiber aero side skirt band (z <= 7.8)
    py_skirt = int(round(wz_to_py(7.8)))
    carb_strip = np.zeros((H - py_skirt, W, 3), dtype=np.uint8)
    _paint_carbon_weave(carb_strip, (0, 0, W, H - py_skirt), scale=3)
    panel.paste(Image.fromarray(carb_strip, "RGB"), (0, py_skirt))
    # Hot-pink pinstripe along top of carbon side skirt
    d.line([(0, py_skirt), (W, py_skirt)], fill=(255, 225, 242, 255), width=2)
    d.line([(0, py_skirt + 3), (W, py_skirt + 3)], fill=(18, 16, 22, 255), width=2)

    # 2. Sculpted upper door character crease & mid-engine side scoop shadow
    px_door_f = wx_to_px(CAR_SPEC["x_door_front"])
    px_door_r = wx_to_px(CAR_SPEC["x_door_rear"])
    px_d_min, px_d_max = min(px_door_f, px_door_r), max(px_door_f, px_door_r)
    py_belt = wz_to_py(29.8)
    py_low_crease = wz_to_py(11.2)

    # Crisp scissor door shutline
    door_poly = [
        (px_door_f, wz_to_py(29.0)),
        (px_door_r, wz_to_py(30.4)),
        (wx_to_px(CAR_SPEC["x_door_rear"] + 3.0), wz_to_py(8.5)),
        (wx_to_px(CAR_SPEC["x_door_front"] - 2.0), wz_to_py(8.5)),
    ]
    d.line(door_poly + [door_poly[0]], fill=(115, 22, 68, 220), width=3)

    # Flush aerodynamic carbon door handle near rear-top of door
    px_hdl = wx_to_px(CAR_SPEC["x_door_rear"] + 7.5)
    py_hdl = wz_to_py(27.2)
    d.rounded_rectangle([px_hdl - 18, py_hdl - 5, px_hdl + 18, py_hdl + 5], radius=4,
                        fill=(28, 26, 32, 255), outline=(210, 80, 145, 255), width=1)

    # Mid-engine NACA intake shadow recess behind door (x = -22.0 .. -38.0)
    px_in0 = wx_to_px(-22.0)
    px_in1 = wx_to_px(-38.0)
    scoop_pts = [
        (px_in0, wz_to_py(28.8)),
        (px_in1, wz_to_py(30.8)),
        (px_in1, wz_to_py(12.0)),
        (px_in0, wz_to_py(14.5)),
    ]
    d.polygon(scoop_pts, fill=(24, 18, 26, 255), outline=(90, 20, 56, 255))
    # Horizontal pink aero strakes across intake
    for sz in (17.5, 22.0, 26.2):
        d.line([(px_in0, wz_to_py(sz)), (px_in1, wz_to_py(sz))], fill=(255, 88, 168, 255), width=3)

    # Front fender amber/pink LED side-marker lamp (x = +72, z = 13.5)
    px_sm = wx_to_px(71.5)
    py_sm = wz_to_py(13.2)
    d.rounded_rectangle([px_sm - 14, py_sm - 4, px_sm + 14, py_sm + 4], radius=3,
                        fill=(255, 195, 70, 255), outline=(30, 20, 25, 255), width=2)
    gd = ImageDraw.Draw(glow_im)
    gd.rounded_rectangle([x0 + px_sm - 12, y0 + py_sm - 3, x0 + px_sm + 12, y0 + py_sm + 3],
                         radius=2, fill=(255, 175, 50))

    # 3. HERO SIDE LIVERY: "It's not pink" painted boldly across the scissor door!
    #    Guaranteed left-to-right on BOTH sides because su=0..1 is viewer-left..viewer-right!
    txt = "It's not pink"
    door_w = abs(px_d_max - px_d_min)  # ~325 px wide on 1120px side strip!
    door_cx = 0.5 * (px_d_min + px_d_max)
    door_cy = wz_to_py(19.6)

    # Render oversized onto a transparent layer, shear for dynamic supercar speed-italic, & composite!
    txt_w_buf, txt_h_buf = 900, 240
    txt_layer = Image.new("RGBA", (txt_w_buf, txt_h_buf), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    fnt = _load_font(["arialbi.ttf", "impact.ttf", "segoeuib.ttf", "arialbd.ttf"], 108)

    bbox = td.textbbox((0, 0), txt, font=fnt, stroke_width=12)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx0 = (txt_w_buf - tw) // 2 - bbox[0]
    ty0 = (txt_h_buf - th) // 2 - bbox[1]

    # Racing speed stripes flanking/underlining the text
    bar_y = ty0 + th + 10
    td.polygon([(tx0 - 10, bar_y), (tx0 + tw + 18, bar_y), (tx0 + tw + 6, bar_y + 10), (tx0 - 22, bar_y + 10)],
               fill=(18, 14, 22, 235))
    td.polygon([(tx0 - 6, bar_y + 2), (tx0 + tw + 14, bar_y + 2), (tx0 + tw + 6, bar_y + 8), (tx0 - 14, bar_y + 8)],
               fill=(255, 245, 250, 245))

    # Hard offset racing shadow -> thick gloss-black stroke -> pure crisp white lettering!
    td.text((tx0 + 6, ty0 + 7), txt, font=fnt, fill=(95, 8, 55, 225), stroke_width=12, stroke_fill=(95, 8, 55, 225))
    td.text((tx0, ty0), txt, font=fnt, fill=(255, 252, 255, 255), stroke_width=11, stroke_fill=(14, 12, 18, 255))

    # Crop tight & scale cleanly to fit comfortably inside the scissor door (with safe shutline margin!)
    nz = txt_layer.getbbox()
    if nz:
        cropped = txt_layer.crop(nz)
        target_tw = int(round(door_w * 0.88))
        target_th = max(24, int(round(cropped.height * (target_tw / float(cropped.width)))))
        scaled_txt = cropped.resize((target_tw, target_th), Image.Resampling.LANCZOS)
        paste_x = int(round(door_cx - target_tw * 0.5))
        paste_y = int(round(door_cy - target_th * 0.5))
        panel.alpha_composite(scaled_txt, (paste_x, paste_y))

    atlas_im.paste(panel.convert("RGB"), (x0, y0))
    orm_arr[y0:y1, x0:x1] = [255, 48, 58]
    orm_arr[y0 + py_skirt:y1, x0:x1] = [240, 88, 25]


def _paint_front_fascia(atlas_im, glow_im, orm_arr):
    x0, y0, x1, y1 = R_FRONT
    W, H = x1 - x0, y1 - y0  # 640 x 400
    sub = np.zeros((H, W, 3), dtype=np.uint8)
    _paint_candy_pink_rect(sub, (0, 0, W, H), horizon_bias=0.35)
    im = Image.fromarray(sub, "RGB")
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow_im)

    # Lower carbon splitter lip (bottom 18% of front fascia)
    sp_y = int(H * 0.80)
    carb = np.zeros((H - sp_y, W, 3), dtype=np.uint8)
    _paint_carbon_weave(carb, (0, 0, W, H - sp_y), scale=3)
    im.paste(Image.fromarray(carb, "RGB"), (0, sp_y))
    d.line([(0, sp_y), (W, sp_y)], fill=(255, 95, 175), width=4)

    # 3 Exotic Trapezoidal Honeycomb Intakes (Left, Center, Right)
    intakes = [
        [(26, int(H * 0.44)), (195, int(H * 0.50)), (172, int(H * 0.77)), (36, int(H * 0.77))],
        [(218, int(H * 0.54)), (W - 218, int(H * 0.54)), (W - 200, int(H * 0.78)), (200, int(H * 0.78))],
        [(W - 195, int(H * 0.50)), (W - 26, int(H * 0.44)), (W - 36, int(H * 0.77)), (W - 172, int(H * 0.77))],
    ]
    for poly in intakes:
        d.polygon(poly, fill=(16, 16, 20), outline=(42, 38, 46), width=4)
    # Subtle honeycomb mesh dots across intake zone
    for py in range(int(H * 0.45), int(H * 0.78), 10):
        off = 5 if (py // 10) % 2 else 0
        for px in range(32 + off, W - 32, 10):
            if im.getpixel((px, py))[0] < 30:
                d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(32, 32, 38))

    # Razor-sharp Lamborghini-style Y-Blade Crystalline LED Headlights!
    for side in (-1, 1):
        cx = 112 if side < 0 else (W - 112)
        s = -1 if side < 0 else 1
        housing = [
            (cx - s * 86, int(H * 0.14)),
            (cx + s * 78, int(H * 0.25)),
            (cx + s * 62, int(H * 0.40)),
            (cx - s * 74, int(H * 0.33)),
        ]
        d.polygon(housing, fill=(18, 20, 28), outline=(55, 50, 65), width=3)
        # Glowing Y-shaped LED DRL blades inside housing
        p_stem = [(cx - s * 62, int(H * 0.24)), (cx + s * 10, int(H * 0.28))]
        p_up   = [(cx + s * 10, int(H * 0.28)), (cx + s * 64, int(H * 0.26))]
        p_dn   = [(cx + s * 10, int(H * 0.28)), (cx + s * 48, int(H * 0.36))]
        for seg in (p_stem, p_up, p_dn):
            d.line(seg, fill=(245, 250, 255), width=7)
            gseg = [(x0 + a, y0 + b) for a, b in seg]
            gd.line(gseg, fill=(230, 245, 255), width=8)
        # Projector bi-LED jewel
        d.ellipse([cx - s * 28 - 12, int(H * 0.22) - 10, cx - s * 28 + 12, int(H * 0.22) + 10],
                  fill=(210, 238, 255), outline=(255, 255, 255), width=2)
        gd.ellipse([x0 + cx - s * 28 - 10, y0 + int(H * 0.22) - 8, x0 + cx - s * 28 + 10, y0 + int(H * 0.22) + 8],
                   fill=(220, 240, 255))

    atlas_im.paste(im, (x0, y0))
    orm_arr[y0:y1, x0:x1] = [255, 65, 45]


def _paint_rear_fascia(atlas_im, glow_im, orm_arr):
    x0, y0, x1, y1 = R_REAR
    W, H = x1 - x0, y1 - y0  # 464 x 400
    sub = np.zeros((H, W, 3), dtype=np.uint8)
    _paint_candy_pink_rect(sub, (0, 0, W, H), horizon_bias=0.30)
    im = Image.fromarray(sub, "RGB")
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow_im)

    # Full-width dark rear supercar honeycomb grille fascia (y: 16% .. 62%)
    d.rounded_rectangle([18, int(H * 0.15), W - 18, int(H * 0.62)], radius=14,
                        fill=(18, 18, 24), outline=(55, 30, 48), width=3)
    for py in range(int(H * 0.18), int(H * 0.60), 9):
        off = 4 if (py // 9) % 2 else 0
        for px in range(26 + off, W - 26, 9):
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(32, 30, 38))

    # Full-width Supercar LED Lightbar + Hex Taillight Chevrons!
    bar_y = int(H * 0.22)
    d.line([(28, bar_y), (W - 28, bar_y)], fill=(255, 48, 72), width=8)
    gd.line([(x0 + 28, y0 + bar_y), (x0 + W - 28, y0 + bar_y)], fill=(255, 36, 56), width=9)
    for side in (-1, 1):
        base_x = 76 if side < 0 else (W - 76)
        s = 1 if side < 0 else -1
        for k in range(3):
            ox = base_x + s * k * 28
            chev = [(ox - s * 12, bar_y + 6), (ox, bar_y + 22), (ox + s * 12, bar_y + 38)]
            d.line(chev, fill=(255, 70, 85), width=6)
            gd.line([(x0 + a, y0 + b) for a, b in chev], fill=(255, 42, 60), width=7)

    # Lower Carbon Venturi Diffuser (bottom 34%)
    df_y = int(H * 0.66)
    carb = np.zeros((H - df_y, W, 3), dtype=np.uint8)
    _paint_carbon_weave(carb, (0, 0, W, H - df_y), scale=3)
    im.paste(Image.fromarray(carb, "RGB"), (0, df_y))
    d.line([(16, df_y), (W - 16, df_y)], fill=(255, 95, 175), width=3)

    # Vanity License Plate: "NOT PINK" (California style!)
    pw, ph = 136, 68
    px0, py0 = (W - pw) // 2, int(H * 0.34)
    d.rounded_rectangle([px0 - 4, py0 - 4, px0 + pw + 4, py0 + ph + 4], radius=6,
                        fill=(16, 16, 20), outline=(220, 220, 230), width=2)
    d.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=4, fill=(246, 248, 252))
    f_state = _load_font(["arialbi.ttf", "arialbd.ttf"], 13)
    f_plate = _load_font(["impact.ttf", "bahnschrift.ttf", "arialbd.ttf"], 30)
    d.text((px0 + 24, py0 + 3), "CALIFORNIA", font=f_state, fill=(205, 32, 48))
    d.text((px0 + 11, py0 + 21), "NOT PINK", font=f_plate, fill=(22, 44, 118))

    atlas_im.paste(im, (x0, y0))
    orm_arr[y0:y1, x0:x1] = [255, 80, 35]


def _paint_top_roof_and_deck(atlas_im, orm_arr):
    x0, y0, x1, y1 = R_TOP
    W, H = x1 - x0, y1 - y0  # 736 x 400
    sub = np.zeros((H, W, 3), dtype=np.uint8)
    _paint_candy_pink_rect(sub, (0, 0, W, H), horizon_bias=0.50)
    im = Image.fromarray(sub, "RGB")
    d = ImageDraw.Draw(im)

    # Left half of R_TOP corresponds to rear engine deck (x0 .. x_roof_rear)
    deck_w = int(W * 0.58)
    carb = np.zeros((H, deck_w, 3), dtype=np.uint8)
    _paint_carbon_weave(carb, (0, 0, deck_w, H), scale=4)
    # Central carbon spine & louvered rear engine bay surround, keeping outer rear fenders candy pink!
    d.rounded_rectangle([24, int(H * 0.20), deck_w, int(H * 0.80)], radius=18,
                        fill=(26, 26, 32), outline=(140, 35, 88), width=4)
    # Supercar rear engine heat-extractor louver slats
    for lx in range(52, deck_w - 28, 26):
        d.rectangle([lx, int(H * 0.25), lx + 14, int(H * 0.42)], fill=(12, 12, 16), outline=(52, 52, 62))
        d.rectangle([lx, int(H * 0.58), lx + 14, int(H * 0.75)], fill=(12, 12, 16), outline=(52, 52, 62))

    atlas_im.paste(im, (x0, y0))
    orm_arr[y0:y1, x0:x1] = [255, 52, 50]


def _paint_webcam_textures(atlas_im, glow_im, orm_arr):
    """Paints dedicated high-res PC Streamer Webcam front bezel (R_WEBCAM_F)
    and optical multi-coated glass lens objective (R_WEBCAM_LENS)."""
    # 1. R_WEBCAM_F (576 x 288): Front bezel of the webcam
    x0, y0, x1, y1 = R_WEBCAM_F
    W, H = x1 - x0, y1 - y0
    im = Image.new("RGB", (W, H), (28, 30, 36))
    d = ImageDraw.Draw(im)
    gd = ImageDraw.Draw(glow_im)

    # Outer brushed silver / gunmetal pill frame
    d.rounded_rectangle([8, 8, W - 8, H - 8], radius=64, fill=(44, 48, 56), outline=(175, 184, 196), width=6)
    d.rounded_rectangle([20, 20, W - 20, H - 20], radius=54, fill=(22, 24, 30), outline=(76, 82, 94), width=2)

    # Left & Right perforated stereo microphone grilles!
    for mx0, mx1 in [(38, 178), (W - 178, W - 38)]:
        d.rounded_rectangle([mx0, 46, mx1, H - 46], radius=28, fill=(16, 18, 22), outline=(58, 62, 72), width=2)
        for py in range(62, H - 56, 11):
            off = 5 if (py // 11) % 2 else 0
            for px in range(mx0 + 16 + off, mx1 - 12, 11):
                d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(8, 9, 12), outline=(42, 46, 54))

    # Glowing Green/Cyan Streamer Status LED Bars flanking the grilles + "REC ●" jewel LED!
    for lx in (32, W - 32):
        d.line([(lx, 84), (lx, H - 84)], fill=(52, 245, 148), width=6)
        gd.line([(x0 + lx, y0 + 84), (x0 + lx, y0 + H - 84)], fill=(40, 255, 140), width=8)

    led_x, led_y = W // 2 + 96, 62
    d.ellipse([led_x - 10, led_y - 10, led_x + 10, led_y + 10], fill=(70, 255, 120), outline=(220, 255, 230), width=2)
    gd.ellipse([x0 + led_x - 12, y0 + led_y - 12, x0 + led_x + 12, y0 + led_y + 12], fill=(50, 255, 110))

    # Silkscreen webcam branding on bezel
    f_cam = _load_font(["bahnschrift.ttf", "segoeuib.ttf", "arialbd.ttf"], 18)
    f_sub = _load_font(["bahnschrift.ttf", "arialbd.ttf"], 14)
    d.text((W // 2 - 58, 26), "HD 1080p", font=f_cam, fill=(225, 232, 242))
    d.text((W // 2 + 114, 52), "LIVE", font=f_sub, fill=(95, 255, 150))
    d.text((W // 2 - 74, H - 44), "AUTOFOCUS · USB 2.0", font=f_sub, fill=(165, 174, 188))

    atlas_im.paste(im, (x0, y0))
    orm_arr[y0:y1, x0:x1] = [255, 76, 64]

    # 2. R_WEBCAM_LENS (320 x 320): Multi-coated optical glass camera lens
    lx0, ly0, lx1, ly1 = R_WEBCAM_LENS
    LW = lx1 - lx0
    yy, xx = np.mgrid[0:LW, 0:LW].astype(np.float32)
    cx = cy = (LW - 1) * 0.5
    dx, dy = (xx - cx) / (LW * 0.46), (yy - cy) / (LW * 0.46)
    rr = np.hypot(dx, dy)

    lens = np.zeros((LW, LW, 3), dtype=np.float32)
    # Outer silver focus bezel -> dark stepped barrel rings -> sapphire/emerald/magenta coated glass -> black pupil
    in_glass = rr < 0.74
    coat1 = np.exp(-((rr - 0.50) ** 2) / 0.035) * np.clip(0.5 - 0.5 * (dx + dy), 0.0, 1.0)
    coat2 = np.exp(-((rr - 0.34) ** 2) / 0.025) * np.clip(0.5 + 0.5 * (dx + dy), 0.0, 1.0)
    glint1 = np.exp(-(((dx + 0.24) ** 2 + (dy + 0.26) ** 2) / 0.008))
    glint2 = 0.55 * np.exp(-(((dx - 0.20) ** 2 + (dy - 0.22) ** 2) / 0.004))

    lens[..., 0] = np.where(in_glass, 10 + 95 * coat2 + 245 * (glint1 + glint2), 34)
    lens[..., 1] = np.where(in_glass, 18 + 145 * coat1 + 45 * coat2 + 248 * (glint1 + glint2), 36)
    lens[..., 2] = np.where(in_glass, 38 + 215 * coat1 + 165 * coat2 + 255 * (glint1 + glint2), 42)

    # Stepped baffle rings (0.74 .. 0.90) & brushed silver focus ring (0.90 .. 1.0)
    ring_baffle = (rr >= 0.74) & (rr < 0.89)
    ripple = 12.0 * np.sin(rr * 95.0)
    for c_i, base_v in enumerate((24.0, 26.0, 30.0)):
        lens[..., c_i][ring_baffle] = base_v + ripple[ring_baffle]
    silver_ring = rr >= 0.89
    ang = np.arctan2(dy, dx)
    knurl = 18.0 * np.sin(ang * 48.0)
    for c_i, base_v in enumerate((182.0, 188.0, 198.0)):
        lens[..., c_i][silver_ring] = base_v + knurl[silver_ring]

    # Deep center sensor pupil (rr < 0.19)
    pupil = rr < 0.19
    for c_i, pv in enumerate((6.0, 8.0, 16.0)):
        lens[..., c_i][pupil] = pv + 210.0 * glint1[pupil]

    lens_im = Image.fromarray(np.clip(lens, 0, 255).astype(np.uint8), "RGB")
    atlas_im.paste(lens_im, (lx0, ly0))
    # Mirror-smooth glass ORM on lens!
    orm_arr[ly0:ly1, lx0:lx1] = [255, 22, 40]


def _paint_wheel_and_swatches(atlas_im, glow_im, orm_arr):
    # 1. R_WHEEL (352 x 352): 10-Spoke Y-Spoke Forged Alloy Wheel + Pink Brembo Caliper + Tire Sidewall
    x0, y0, x1, y1 = R_WHEEL
    S = x1 - x0  # 352
    im = Image.new("RGB", (S, S), (22, 22, 26))
    d = ImageDraw.Draw(im)
    cx = cy = S // 2
    r_tire = S // 2 - 6
    r_rim = int(r_tire * 0.70)
    r_rotor = int(r_rim * 0.78)

    # Rubber tire sidewall with subtle satin ring + hot-pink pinstripe sidewall lettering!
    d.ellipse([cx - r_tire, cy - r_tire, cx + r_tire, cy + r_tire], fill=(24, 25, 29), outline=(42, 44, 50), width=3)
    d.ellipse([cx - r_rim - 12, cy - r_rim - 12, cx + r_rim + 12, cy + r_rim + 12], outline=(255, 86, 168), width=3)

    # Dark inner wheel barrel + cross-drilled carbon-ceramic brake rotor
    d.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(16, 17, 22), outline=(195, 202, 214), width=5)
    d.ellipse([cx - r_rotor, cy - r_rotor, cx + r_rotor, cy + r_rotor], fill=(96, 100, 108), outline=(65, 68, 76), width=3)
    d.ellipse([cx - int(r_rotor * 0.48), cy - int(r_rotor * 0.48), cx + int(r_rotor * 0.48), cy + int(r_rotor * 0.48)],
              fill=(32, 34, 40))
    # Cross-drilled rotor holes
    for i in range(24):
        a = 2.0 * math.pi * i / 24.0
        for rr in (0.60, 0.74, 0.88):
            hx = cx + math.cos(a + rr * 0.4) * (r_rotor * rr)
            hy = cy + math.sin(a + rr * 0.4) * (r_rotor * rr)
            d.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=(28, 30, 36))

    # Bright Hot-Pink 6-Piston Brake Caliper on right quadrant!
    cal_pts = [
        (cx + int(r_rotor * 0.52), cy - 34),
        (cx + int(r_rotor * 0.96), cy - 28),
        (cx + int(r_rotor * 0.96), cy + 28),
        (cx + int(r_rotor * 0.52), cy + 34),
    ]
    d.polygon(cal_pts, fill=(255, 62, 152), outline=(255, 195, 225), width=2)

    # 5 Forged Y-Spokes (10 outer tips!) in machined titanium/silver
    r_hub = int(r_rim * 0.26)
    for i in range(5):
        a0 = 2.0 * math.pi * i / 5.0
        sx = cx + math.cos(a0) * (r_rim * 0.44)
        sy = cy + math.sin(a0) * (r_rim * 0.44)
        d.line([(cx, cy), (sx, sy)], fill=(205, 212, 224), width=11)
        for branch in (-0.24, 0.24):
            tx = cx + math.cos(a0 + branch) * (r_rim - 3)
            ty = cy + math.sin(a0 + branch) * (r_rim - 3)
            d.line([(sx, sy), (tx, ty)], fill=(214, 220, 232), width=8)

    # Center-lock anodized hot-pink racing hex nut!
    d.ellipse([cx - r_hub, cy - r_hub, cx + r_hub, cy + r_hub], fill=(38, 40, 48), outline=(190, 198, 210), width=3)
    d.regular_polygon((cx, cy, int(r_hub * 0.68)), n_sides=6, fill=(255, 68, 158), outline=(255, 220, 238))
    atlas_im.paste(im, (x0, y0))
    orm_arr[y0:y1, x0:x1] = [255, 110, 140]

    # 2. R_TREAD: Asymmetric semi-slick performance tire tread
    tx0, ty0, tx1, ty1 = R_TREAD
    tw, th = tx1 - tx0, ty1 - ty0
    t_im = Image.new("RGB", (tw, th), (26, 27, 31))
    td = ImageDraw.Draw(t_im)
    for gx in (int(tw * 0.24), int(tw * 0.46), int(tw * 0.72)):
        td.rectangle([gx - 5, 0, gx + 5, th], fill=(12, 13, 16))
    for gy in range(0, th, 22):
        td.line([(8, gy), (int(tw * 0.22), gy + 10)], fill=(14, 15, 18), width=4)
        td.line([(int(tw * 0.75), gy + 10), (tw - 8, gy)], fill=(14, 15, 18), width=4)
    atlas_im.paste(t_im, (tx0, ty0))
    orm_arr[ty0:ty1, tx0:tx1] = [245, 215, 10]

    # Material Swatches: Carbon, Seamless Metallic Candy-Pink, Chrome, Matte Trim, Gaffer Tape
    atlas_arr = np.asarray(atlas_im).copy()
    _paint_carbon_weave(atlas_arr, R_CARBON, scale=4)
    px0, py0, px1, py1 = R_PINK_MET
    rng_p = np.random.default_rng(777)
    ph_s, pw_s = py1 - py0, px1 - px0
    flake_p = rng_p.normal(0.0, 1.6, size=(ph_s, pw_s)).astype(np.float32)
    pink_sw = np.stack([
        np.clip(248.0 + flake_p * 0.7, 0, 255),
        np.clip(92.0 + flake_p * 1.1, 0, 255),
        np.clip(174.0 + flake_p * 0.9, 0, 255),
    ], axis=-1).astype(np.uint8)
    atlas_arr[py0:py1, px0:px1] = pink_sw

    # Brushed Titanium / Chrome
    cx0, cy0, cx1, cy1 = R_CHROME
    yy = np.linspace(0.0, 1.0, cy1 - cy0, dtype=np.float32)[:, None]
    ch_v = np.clip(188.0 + 55.0 * np.sin(np.pi * yy * 2.0), 110, 250).astype(np.uint8)
    atlas_arr[cy0:cy1, cx0:cx1] = np.repeat(np.stack([ch_v, ch_v + 2, np.clip(ch_v + 5, 0, 255)], axis=-1), cx1 - cx0, axis=1)

    # Matte Black Trim / Rubber / USB Cord
    bx0, by0, bx1, by1 = R_TRIM_BLK
    rng = np.random.default_rng(99)
    grain = rng.integers(24, 34, size=(by1 - by0, bx1 - bx0), dtype=np.uint8)
    atlas_arr[by0:by1, bx0:bx1] = np.stack([grain, grain + 1, grain + 3], axis=-1)

    # Gaffer / Hot-Pink Racing Tape holding USB cable to roof!
    dx0, dy0, dx1, dy1 = R_DUCT_TAPE
    tape = np.zeros((dy1 - dy0, dx1 - dx0, 3), dtype=np.uint8)
    tape[:] = [208, 212, 218]
    tape[::3, :, :] = [194, 198, 205]
    tape[:, ::3, :] = [198, 202, 208]
    atlas_arr[dy0:dy1, dx0:dx1] = tape

    atlas_im.paste(Image.fromarray(atlas_arr, "RGB"), (0, 0))
    orm_arr[R_CARBON[1]:R_CARBON[3], R_CARBON[0]:R_CARBON[2]] = [245, 78, 30]
    orm_arr[R_PINK_MET[1]:R_PINK_MET[3], R_PINK_MET[0]:R_PINK_MET[2]] = [255, 46, 56]
    orm_arr[R_CHROME[1]:R_CHROME[3], R_CHROME[0]:R_CHROME[2]] = [255, 32, 235]
    orm_arr[R_TRIM_BLK[1]:R_TRIM_BLK[3], R_TRIM_BLK[0]:R_TRIM_BLK[2]] = [240, 185, 20]
    orm_arr[R_DUCT_TAPE[1]:R_DUCT_TAPE[3], R_DUCT_TAPE[0]:R_DUCT_TAPE[2]] = [245, 115, 60]

    # 4. R_SEAT: Quilted Black & Hot-Pink Supercar Racing Bucket Seat
    sx0, sy0, sx1, sy1 = R_SEAT
    sw, sh = sx1 - sx0, sy1 - sy0
    s_im = Image.new("RGB", (sw, sh), (26, 25, 32))
    sd = ImageDraw.Draw(s_im)
    # Pink outer bolsters + diamond-quilted center insert!
    sd.rectangle([0, 0, 56, sh], fill=(235, 68, 152))
    sd.rectangle([sw - 56, 0, sw, sh], fill=(235, 68, 152))
    for k in range(-sh, sw + sh, 28):
        sd.line([(56, k), (sw - 56, k + (sw - 112))], fill=(240, 78, 160), width=2)
        sd.line([(56, k + (sw - 112)), (sw - 56, k)], fill=(240, 78, 160), width=2)
    f_hr = _load_font(["bahnschrift.ttf", "arialbd.ttf"], 20)
    sd.text((sw // 2 - 48, 34), "NOT PINK", font=f_hr, fill=(255, 110, 185))
    atlas_im.paste(s_im, (sx0, sy0))
    orm_arr[sy0:sy1, sx0:sx1] = [235, 195, 10]

    # 5. R_DASH: Digital Cockpit Dash + "USB WEBCAM: LIVE" Center Display!
    kx0, ky0, kx1, ky1 = R_DASH
    kw, kh = kx1 - kx0, ky1 - ky0
    k_im = Image.new("RGB", (kw, kh), (20, 22, 28))
    kd = ImageDraw.Draw(k_im)
    gd = ImageDraw.Draw(glow_im)
    # Tachometer arc on left
    kd.arc([24, 36, 172, 184], start=140, end=40, fill=(255, 78, 168), width=10)
    gd.arc([kx0 + 24, ky0 + 36, kx0 + 172, ky0 + 184], start=140, end=40, fill=(255, 65, 155), width=8)
    f_spd = _load_font(["impact.ttf", "bahnschrift.ttf"], 34)
    kd.text((68, 86), "199", font=f_spd, fill=(240, 248, 255))
    # Center infotainment screen showing "ROOF CAM LIVE"
    kd.rounded_rectangle([190, 44, kw - 20, 184], radius=10, fill=(14, 28, 38), outline=(90, 100, 118), width=3)
    kd.ellipse([204, 56, 216, 68], fill=(60, 255, 120))
    gd.ellipse([kx0 + 204, ky0 + 56, kx0 + 216, ky0 + 68], fill=(55, 255, 115))
    f_ui = _load_font(["bahnschrift.ttf", "arialbd.ttf"], 15)
    kd.text((222, 54), "ROOF WEBCAM", font=f_ui, fill=(130, 255, 175))
    kd.text((204, 82), "640x480 30fps", font=f_ui, fill=(190, 215, 235))
    kd.text((204, 106), "Say no to drugs.", font=f_ui, fill=(255, 110, 130))
    atlas_im.paste(k_im, (kx0, ky0))
    orm_arr[ky0:ky1, kx0:kx1] = [245, 110, 25]

    # 6. R_ENGINE: 6.5L Mid-Mounted V12 with Anodized Pink Valve Covers & 12 Velocity Stacks
    ex0, ey0, ex1, ey1 = R_ENGINE
    ew, eh = ex1 - ex0, ey1 - ey0
    e_im = Image.new("RGB", (ew, eh), (24, 25, 30))
    ed = ImageDraw.Draw(e_im)
    ed.rounded_rectangle([24, 18, ew - 24, 58], radius=8, fill=(238, 62, 148), outline=(255, 175, 215), width=2)
    ed.rounded_rectangle([24, eh - 58, ew - 24, eh - 18], radius=8, fill=(238, 62, 148), outline=(255, 175, 215), width=2)
    for k in range(6):
        cx_s = 74 + k * 92
        ed.ellipse([cx_s - 18, eh // 2 - 22, cx_s + 18, eh // 2 + 22], fill=(195, 202, 214), outline=(45, 48, 56), width=3)
        ed.ellipse([cx_s - 9, eh // 2 - 11, cx_s + 9, eh // 2 + 11], fill=(18, 20, 26))
    atlas_im.paste(e_im, (ex0, ey0))
    orm_arr[ey0:ey1, ex0:ex1] = [240, 85, 165]


def build_glass_rgba(size=512):
    """512x512 RGBA translucent automotive canopy & V12 deck glass with ceramic frit border
    and subtle iridescent rose-violet solar tint."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / float(size - 1)
    edge = np.minimum(np.minimum(xx, 1.0 - xx), np.minimum(yy, 1.0 - yy))
    frit = edge < 0.055
    sheen = np.exp(-((yy - 0.34) ** 2) / 0.04)

    r = np.where(frit, 16.0, 42.0 + 55.0 * sheen)
    g = np.where(frit, 16.0, 38.0 + 42.0 * sheen)
    b = np.where(frit, 20.0, 58.0 + 68.0 * sheen)
    a = np.where(frit, 238.0, 118.0 + 28.0 * sheen)
    rgba = np.stack([r, g, b, a], axis=-1).clip(0, 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def generate_all_textures(out_dir, progs_dir, ref_jpg_path=DEFAULT_REF_JPG, dp_gain=0.68):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(progs_dir, exist_ok=True)

    # Base gutter color = candy pink so UV mipmaps never bleed black along body seams!
    atlas_im = Image.new("RGB", (W_ATLAS, H_ATLAS), (236, 78, 158))
    glow_im = Image.new("RGB", (W_ATLAS, H_ATLAS), (0, 0, 0))
    # glTF ORM convention: R = Occlusion (255), G = Roughness (0..255), B = Metallic (0..255)
    orm_arr = np.zeros((H_ATLAS, W_ATLAS, 3), dtype=np.uint8)
    orm_arr[:] = [255, 64, 48]

    _paint_hood_mural(atlas_im, orm_arr, ref_jpg_path)
    _paint_side_panel(atlas_im, glow_im, orm_arr, R_SIDE_L, is_left=True)
    _paint_side_panel(atlas_im, glow_im, orm_arr, R_SIDE_R, is_left=False)
    _paint_front_fascia(atlas_im, glow_im, orm_arr)
    _paint_rear_fascia(atlas_im, glow_im, orm_arr)
    _paint_top_roof_and_deck(atlas_im, orm_arr)
    _paint_webcam_textures(atlas_im, glow_im, orm_arr)
    _paint_wheel_and_swatches(atlas_im, glow_im, orm_arr)

    orm_im = Image.fromarray(orm_arr, "RGB")
    glass_im = build_glass_rgba(512)

    # Soft bloom halo on emissive glow map
    glow_blur = glow_im.filter(ImageFilter.GaussianBlur(radius=4))
    glow_final = ImageChops.lighter(glow_im, glow_blur)

    p_atlas = os.path.join(out_dir, "pink_supercar_atlas_2k.png")
    p_glow = os.path.join(out_dir, "pink_supercar_glow_2k.png")
    p_orm = os.path.join(out_dir, "pink_supercar_orm_2k.png")
    p_glass = os.path.join(out_dir, "pink_supercar_glass.png")

    atlas_im.save(p_atlas, "PNG", optimize=True)
    glow_final.save(p_glow, "PNG", optimize=True)
    orm_im.save(p_orm, "PNG", optimize=True)
    glass_im.save(p_glass, "PNG", optimize=True)

    # DarkPlaces tone-mapped 1024x1024 textures in progs/
    dp_arr = (np.asarray(atlas_im, dtype=np.float32) * dp_gain).clip(0, 255).astype(np.uint8)
    dp_im = Image.fromarray(dp_arr, "RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
    dp_glow = glow_final.resize((1024, 1024), Image.Resampling.LANCZOS)

    dp_im.save(os.path.join(progs_dir, "pink_supercar_tex.png"), "PNG", optimize=True)
    dp_glow.save(os.path.join(progs_dir, "pink_supercar_tex_glow.png"), "PNG", optimize=True)
    glass_im.save(os.path.join(progs_dir, "pink_supercar_glass.png"), "PNG", optimize=True)

    return dict(
        atlas=atlas_im,
        glow=glow_final,
        orm=orm_im,
        glass=glass_im,
        atlas_path=p_atlas,
        glow_path=p_glow,
        orm_path=p_orm,
        glass_path=p_glass,
    )


if __name__ == "__main__":
    mod_dir = os.path.abspath(os.path.join(HERE, "..", ".."))
    generate_all_textures(
        os.path.join(HERE, "out", "pink_supercar"),
        os.path.join(mod_dir, "progs"),
    )
    print("Generated pink_supercar 2K texture suite successfully!")
