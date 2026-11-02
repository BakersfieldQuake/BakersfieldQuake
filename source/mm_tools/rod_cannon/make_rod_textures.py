"""Procedural studio-grade texture synthesis for the Quake 'CHROME-ROD CONTRAPTION BAZOOKA' (`rod_cannon`):

Faithfully captures every material of the uploaded two-wheel stainless-steel contraption video
blown up to absurd Quake bazooka scale, calibrated for BOTH full-range PBR (WebGL2 / GLB / Blender)
AND DarkPlaces HDR lighting (`progs/rod_*.png` + `scripts/rodcannon.shader`) + Vanilla Quake `.mdl`:

  1. `rod_chrome.png` (1024x1024):
       - u:[0.02..0.48], v:[0.02..0.98] : Mirror-Polished 304 Stainless-Steel Tube & Bullet-Dome Breech
       - u:[0.52..0.98], v:[0.02..0.24] : Drawn Solid Stainless-Steel Axle Bar
       - u:[0.52..0.98], v:[0.26..0.48] : CNC-Machined / TIG-Welded Center T-Sleeve Collar & Seam Ring
       - u:[0.52..0.98], v:[0.50..0.74] : Matte-Satin Black Delrin / Rubber Muzzle Collar Bushing
       - u:[0.52..0.98], v:[0.76..0.98] : Deep Hollow Smoothbore Dark Gunmetal-Charcoal Pipe Interior
  2. `rod_wheel.png`  (1024x1024):
       - u:[0.02..0.98], v:[0.02..0.48] : Pneumatic 4.10/3.50-4 Hand-Truck Black Rubber Tire w/ 6 Ribs & Sidewall Molding
       - u:[0.02..0.48], v:[0.52..0.98] : Glossy White Stamped-Steel Concave Dish Rim w/ 4 Oval Holes & 6203-2RS Bearing
       - u:[0.52..0.74], v:[0.52..0.74] : Black Rubber Schrader Valve Stem & Brass/Black Cap
       - u:[0.76..0.98], v:[0.52..0.74] : Stainless Hex Nyloc Axle Locknut & Flat Washer
  3. `rod_hand.png`   (512x512):
       - Quake Ranger distressed brown leather combat glove, steel knuckle plate & riveted Ranger bracer
  4. `rod_fx.png`     (512x512 RGBA):
       - Cartoon Starburst Cannon Blast, Supersonic Smoke/Shockwave Ring, Burnout Tire-Screech Sparks & Smoke Puff!
  5. `rod_env.png`    (256x256):
       - Subtle DarkPlaces `tcGen environment` studio softbox chrome reflection map for live gleaming steel!
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Canonical UV rectangles shared with geometry builder (u0, v0, u1, v1) in [0..1] top-down UV space
UV_CHROME_TUBE   = (0.02, 0.02, 0.48, 0.98)
UV_CHROME_AXLE   = (0.52, 0.02, 0.98, 0.24)
UV_CHROME_COLLAR = (0.52, 0.26, 0.98, 0.48)
UV_BLACK_CAP     = (0.52, 0.50, 0.98, 0.74)
UV_DARK_BORE     = (0.52, 0.76, 0.98, 0.98)

UV_TIRE_TREAD    = (0.02, 0.02, 0.98, 0.48)
UV_WHITE_RIM     = (0.02, 0.52, 0.48, 0.98)
UV_VALVE_STEM    = (0.54, 0.54, 0.72, 0.72)
UV_HEX_NUT       = (0.76, 0.54, 0.96, 0.72)

UV_FX_STARBURST  = (0.02, 0.02, 0.48, 0.48)
UV_FX_SHOCKRING  = (0.52, 0.02, 0.98, 0.48)
UV_FX_SPARKS     = (0.02, 0.52, 0.48, 0.98)
UV_FX_SMOKE      = (0.52, 0.52, 0.98, 0.98)


def _font(size, prefer=("ariblk.ttf", "impact.ttf", "tahomabd.ttf", "arialbd.ttf", "consolab.ttf")):
    for nm in prefer:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _fbm(h, w, seed=77, octaves=(4, 8, 16, 32, 64)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tw = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh = max(2, h // freq)
        gw = max(2, w // freq)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        im = Image.fromarray(g, mode="F").resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, dtype=np.float32) * amp
        tw += amp
    return acc / max(tw, 1e-6)


def _draw_rivet(draw, cx, cy, r):
    draw.ellipse((cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2), fill=(26, 20, 14))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(172, 152, 118))
    draw.arc((cx - r, cy - r, cx + r, cy + r), 195, 345, fill=(242, 226, 195), width=2)
    draw.arc((cx - r, cy - r, cx + r, cy + r), 15, 165, fill=(68, 54, 38), width=2)


def build_chrome_texture(out_dir):
    """1024x1024 Mirror-Polished 304 Stainless Steel, Machined T-Collar, Black Delrin Muzzle Cap & Bore."""
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    nf = _fbm(H, W, seed=101, octaves=(2, 4, 8, 16))

    # --- 1. Left Half [0..1024, 0..512]: Mirror-Polished Studio 304 Stainless-Steel Cylinder ---
    # Exact 2*pi periodicity across u in [0.02..0.48] so cylindrical lathe wrap is 100% seamless!
    # Note: phi = pi + tu * 2*pi -> tu = 0.50 is +Z top, tu = 0.25/0.75 are +/-Y flanks, tu = 0/1 is -Z bottom!
    tu = (np.arange(512, dtype=np.float32)[None, :] / 512.0 * 0.50 - 0.02) / 0.46
    phi = np.pi + tu * (2.0 * np.pi)
    v = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]

    # Studio softbox reflection profile matching the bright white studio video:
    # Crisp bright key-light band at top-left, secondary studio softbox on right flank, dark horizon line, warm floor bounce!
    cz = np.cos(phi)   # +1 at top (+Z), -1 at bottom (-Z)
    sy = np.sin(phi)   # +1 at inner-left (+Y), -1 at outer-right (-Y)

    sky_grad = 0.66 + 0.20 * np.clip(cz, -1.0, 1.0)
    softbox_top = 0.34 * np.exp(-((cz - 0.82) ** 2 + (sy - 0.36) ** 2) / 0.095)
    softbox_side = 0.24 * np.exp(-((cz - 0.35) ** 2 + (sy + 0.78) ** 2) / 0.110)
    horizon_dark = 0.30 * np.exp(-((cz + 0.14) ** 2) / 0.028)
    floor_bounce = 0.18 * np.exp(-((cz + 0.86) ** 2) / 0.090)
    micro_lathe = 0.012 * np.sin(v * 640.0) + 0.014 * nf[:, :512]

    lum = np.clip(sky_grad + softbox_top + softbox_side - horizon_dark + floor_bounce + micro_lathe, 0.22, 1.06)
    arr[:, :512, 0] = np.clip(lum * 234.0, 0, 255)
    arr[:, :512, 1] = np.clip(lum * 239.0, 0, 255)
    arr[:, :512, 2] = np.clip(lum * 247.0 + 3.0, 0, 255)

    # --- 2. Right Band 1 [y=0..256, x=512..1024]: Drawn Solid Stainless-Steel Axle Bar (`UV_CHROME_AXLE`) ---
    tu_r = (np.arange(512, dtype=np.float32)[None, :] / 512.0 * 0.50 + 0.50 - 0.52) / 0.46
    phi_r = np.pi + tu_r * (2.0 * np.pi)
    cz_r = np.cos(phi_r)
    vr1 = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    axle_lum = np.clip(
        0.68 + 0.26 * cz_r + 0.18 * np.exp(-((cz_r - 0.88) ** 2) / 0.05)
        - 0.24 * np.exp(-((cz_r + 0.18) ** 2) / 0.03) + 0.015 * np.sin(vr1 * 420.0),
        0.24, 1.05,
    )
    arr[0:256, 512:, 0] = np.clip(axle_lum * 232.0, 0, 255)
    arr[0:256, 512:, 1] = np.clip(axle_lum * 237.0, 0, 255)
    arr[0:256, 512:, 2] = np.clip(axle_lum * 246.0, 0, 255)

    # --- 3. Right Band 2 [y=256..512, x=512..1024]: Machined T-Sleeve Collar & Seam Groove (`UV_CHROME_COLLAR`) ---
    vr2 = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    bevel = np.maximum(0.0, np.sin(np.clip(vr2, 0.0, 1.0) * np.pi)) ** 0.35
    weld_lip = np.exp(-((vr2 - 0.08) ** 2) / 0.0018) + np.exp(-((vr2 - 0.92) ** 2) / 0.0018)
    seam_chan = np.exp(-((vr2 - 0.50) ** 2) / 0.0035)
    col_lum = np.clip(
        (0.62 + 0.25 * cz_r + 0.16 * np.exp(-((cz_r - 0.80) ** 2) / 0.06))
        * (0.56 + 0.46 * bevel) * (1.0 - 0.32 * seam_chan) + 0.10 * weld_lip,
        0.18, 1.05,
    )
    arr[256:512, 512:, 0] = np.clip(col_lum * 228.0, 0, 255)
    arr[256:512, 512:, 1] = np.clip(col_lum * 234.0, 0, 255)
    arr[256:512, 512:, 2] = np.clip(col_lum * 244.0, 0, 255)

    # --- 4. Right Band 3 [y=512..768, x=512..1024]: Matte-Satin Black Delrin / Rubber Muzzle Collar (`UV_BLACK_CAP`) ---
    vr3 = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    lip_spec = 0.22 * np.exp(-((vr3 - 0.72) ** 2) / 0.015) * (0.55 + 0.45 * np.maximum(0.0, cz_r))
    cap_lum = np.clip(0.11 + 0.06 * np.maximum(0.0, cz_r) + lip_spec + 0.018 * nf[512:768, 512:], 0.05, 0.44)
    arr[512:768, 512:, 0] = np.clip(cap_lum * 235.0, 8, 120)
    arr[512:768, 512:, 1] = np.clip(cap_lum * 240.0, 8, 124)
    arr[512:768, 512:, 2] = np.clip(cap_lum * 248.0, 10, 132)

    # --- 5. Right Band 4 [y=768..1024, x=512..1024]: Deep Smoothbore Dark Pipe Interior (`UV_DARK_BORE`) ---
    vr4 = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    # v=0 is mouth rim (subtle steel gleam), v=1 is deep pitch-black bore interior!
    depth_fade = np.exp(-vr4 * 3.8)
    bore_lum = np.clip((0.03 + 0.28 * depth_fade * (0.6 + 0.4 * np.cos(phi_r * 2.0))) + 0.01 * nf[768:, 512:], 0.015, 0.38)
    arr[768:, 512:, 0] = np.clip(bore_lum * 220.0, 3, 96)
    arr[768:, 512:, 1] = np.clip(bore_lum * 228.0, 3, 100)
    arr[768:, 512:, 2] = np.clip(bore_lum * 240.0, 4, 108)

    path = os.path.join(out_dir, "rod_chrome.png")
    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)
    return path


def build_wheel_texture(out_dir):
    """1024x1024 Pneumatic 6-Rib Black Rubber Hand-Truck Tire + Glossy White 4-Hole Steel Rim & 6203 Bearing."""
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    nf = _fbm(H, W, seed=202, octaves=(4, 8, 16, 32, 64))

    # --- 1. Top Half [y=0..512, x=0..1024]: Pneumatic Ribbed Black Rubber Tire (`UV_TIRE_TREAD`) ---
    # u wraps 360 deg around tire circumference; v goes inner-bead (0) -> outer-sidewall -> crown (0.5) -> inner-sidewall -> inner-bead (1)
    tu = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
    tv = np.linspace(0.0, 1.0, 512, dtype=np.float32)[:, None]
    theta = tu * 2.0 * np.pi

    # Crown zone centered at tv = 0.50: 6 crisp circumferential sawtooth/ribbed pneumatic tread grooves!
    in_crown = np.clip(1.0 - np.abs(tv - 0.50) / 0.20, 0.0, 1.0)
    rib_wave = np.cos((tv - 0.50) / 0.20 * 6.0 * np.pi)
    groove = np.exp(-(np.sin((tv - 0.50) / 0.20 * 3.0 * np.pi) ** 2) / 0.045) * (np.abs(tv - 0.50) < 0.19)
    # Transverse micro-sipes around the circumference (48 lugs) so tire rotation is visibly crisp!
    lugs = (0.5 + 0.5 * np.cos(theta * 48.0)) * in_crown

    sidewall_bulge = np.maximum(0.0, np.sin(np.clip(tv, 0.0, 1.0) * np.pi)) ** 0.55
    mold_ring_1 = np.exp(-((np.abs(tv - 0.50) - 0.22) ** 2) / 0.00025)
    mold_ring_2 = np.exp(-((np.abs(tv - 0.50) - 0.34) ** 2) / 0.00025)

    rub = (
        0.135
        + 0.075 * sidewall_bulge
        + 0.038 * in_crown * rib_wave
        + 0.032 * lugs
        - 0.095 * groove
        + 0.035 * (mold_ring_1 + mold_ring_2)
        + 0.022 * nf[:512, :]
    )
    rub = np.clip(rub, 0.035, 0.34)
    arr[:512, :, 0] = rub * 238.0
    arr[:512, :, 1] = rub * 242.0
    arr[:512, :, 2] = rub * 248.0

    # --- 2. Bottom-Left Quadrant [y=512..1024, x=0..512]: Glossy White 4-Hole Stamped Steel Dish Rim (`UV_WHITE_RIM`) ---
    # Render at 2x supersampling (1024x1024) for ultra-clean circular stamping holes, rolled lip, and 6203-2RS bearing!
    RW = RH = 1024
    yy, xx = np.mgrid[0:RH, 0:RW].astype(np.float32)
    dx = (xx - 512.0) / 470.0
    dy = (yy - 512.0) / 470.0
    rr = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)

    # Glossy white powder-coated stamped steel concave dish shading:
    # Outer rolled lip at rr in [0.86..1.0], concave dish bowl in [0.30..0.86], raised bearing boss in [0.22..0.30]
    light_dir = -0.55 * dx - 0.72 * dy  # top-left studio highlight
    lip_bump = np.exp(-((rr - 0.92) ** 2) / 0.0022)
    dish_groove = np.exp(-((rr - 0.82) ** 2) / 0.0028)
    boss_ring = np.exp(-((rr - 0.27) ** 2) / 0.0014)

    white_lum = (
        0.88
        + 0.08 * light_dir
        + 0.09 * lip_bump
        - 0.16 * dish_groove
        + 0.06 * boss_ring
        - 0.06 * np.clip((0.82 - rr) / 0.55, 0.0, 1.0) ** 1.4
    )
    white_lum = np.clip(white_lum, 0.45, 1.02)
    rim_rgb = np.zeros((RH, RW, 3), dtype=np.float32)
    rim_rgb[..., 0] = np.clip(white_lum * 244.0, 0, 255)
    rim_rgb[..., 1] = np.clip(white_lum * 247.0, 0, 255)
    rim_rgb[..., 2] = np.clip(white_lum * 252.0, 0, 255)

    # 4 Stamped Oval Dish Holes at 45, 135, 225, 315 degrees (matching video frame 00:03 & 00:04!)
    for h_deg in (45.0, 135.0, 225.0, 315.0):
        ha = math.radians(h_deg)
        ca, sa = math.cos(ha), math.sin(ha)
        hx, hy = 0.54 * ca, 0.54 * sa
        # Local radial & tangential coordinates around hole center
        rx_l = (dx - hx) * ca + (dy - hy) * sa
        ry_l = -(dx - hx) * sa + (dy - hy) * ca
        oval_d = np.sqrt((rx_l / 0.082) ** 2 + (ry_l / 0.132) ** 2)
        bevel_ring = np.exp(-((oval_d - 1.06) ** 2) / 0.045)
        hole_mask = np.clip((1.0 - oval_d) * 14.0, 0.0, 1.0)
        # Stamped white steel rollover bevel around each oval cutout, dark recessed shadow inside!
        rim_rgb += bevel_ring[:, :, None] * np.array([18.0, 18.0, 20.0], dtype=np.float32)
        dark_hole = np.array([28.0, 31.0, 36.0], dtype=np.float32)[None, None, :]
        rim_rgb = rim_rgb * (1.0 - hole_mask[:, :, None]) + dark_hole * hole_mask[:, :, None]

    # Central Sealed Ball Bearing (`6203-2RS`, rr <= 0.25):
    #   [0.20..0.25]: Pressed steel outer bearing race
    #   [0.12..0.20]: Matte black/charcoal rubber dust seal ring (`6203-2RS`)
    #   [0.07..0.12]: Bright polished chrome inner bearing race
    #   [0.00..0.07]: Stainless axle shaft center!
    in_outer_race = np.clip((0.255 - rr) * 45.0, 0.0, 1.0) * np.clip((rr - 0.195) * 45.0, 0.0, 1.0)
    in_seal = np.clip((0.200 - rr) * 50.0, 0.0, 1.0) * np.clip((rr - 0.118) * 50.0, 0.0, 1.0)
    in_inner_race = np.clip((0.122 - rr) * 55.0, 0.0, 1.0) * np.clip((rr - 0.068) * 55.0, 0.0, 1.0)
    in_shaft = np.clip((0.072 - rr) * 60.0, 0.0, 1.0)

    steel_sh = 175.0 + 58.0 * np.cos(ang * 2.0 - 0.8)
    outer_col = np.stack([steel_sh * 0.96, steel_sh * 0.99, steel_sh * 1.04], axis=-1)
    seal_col = np.broadcast_to(np.array([34.0, 37.0, 42.0], dtype=np.float32), (RH, RW, 3))
    inner_sh = 205.0 + 48.0 * np.cos(ang * 2.0 + 0.5)
    inner_col = np.stack([inner_sh * 0.97, inner_sh * 1.00, inner_sh * 1.04], axis=-1)
    shaft_sh = 155.0 + 45.0 * light_dir
    shaft_col = np.stack([shaft_sh * 0.96, shaft_sh * 0.98, shaft_sh * 1.02], axis=-1)

    for msk, col in ((in_outer_race, outer_col), (in_seal, seal_col), (in_inner_race, inner_col), (in_shaft, shaft_col)):
        rim_rgb = rim_rgb * (1.0 - msk[:, :, None]) + col * msk[:, :, None]

    rim_im = Image.fromarray(np.clip(rim_rgb, 0, 255).astype(np.uint8), mode="RGB").resize((512, 512), Image.LANCZOS)
    arr[512:, :512, :] = np.asarray(rim_im, dtype=np.float32)

    # --- 3. Bottom-Right Quadrant [y=512..1024, x=512..1024]: Schrader Valve Stem (`UV_VALVE_STEM`) & Hex Locknut (`UV_HEX_NUT`) ---
    # Valve stem [x=512..756, y=512..768]: black rubber stem + brass tip ring + black plastic dust cap
    vv = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    vu = np.linspace(0.0, 1.0, 244, dtype=np.float32)[None, :]
    brass_band = (vv > 0.62) & (vv < 0.78)
    sh_v = 0.65 + 0.35 * np.sin(vu * np.pi)
    v_rgb = np.zeros((256, 244, 3), dtype=np.float32)
    v_rgb[..., 0] = np.where(brass_band, 215.0 * sh_v, 36.0 * sh_v)
    v_rgb[..., 1] = np.where(brass_band, 178.0 * sh_v, 38.0 * sh_v)
    v_rgb[..., 2] = np.where(brass_band, 68.0 * sh_v,  42.0 * sh_v)
    arr[512:768, 512:756, :] = v_rgb

    # Stainless Hex Nyloc Locknut [x=756..1024, y=512..768]
    nu = np.linspace(0.0, 1.0, 268, dtype=np.float32)[None, :]
    nv_y = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    facet = 0.68 + 0.28 * np.cos(nu * 6.0 * np.pi)
    nyloc_blue = (nv_y > 0.74) & (nv_y < 0.90)
    n_rgb = np.zeros((256, 268, 3), dtype=np.float32)
    n_rgb[..., 0] = np.where(nyloc_blue, 55.0 * facet, 222.0 * facet)
    n_rgb[..., 1] = np.where(nyloc_blue, 118.0 * facet, 228.0 * facet)
    n_rgb[..., 2] = np.where(nyloc_blue, 205.0 * facet, 238.0 * facet)
    arr[512:768, 756:1024, :] = n_rgb

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    d = ImageDraw.Draw(im)
    # Subtle hilarious molded rubber sidewall lettering along both tire sidewalls!
    f_tire = _font(18, prefer=("ariblk.ttf", "arialbd.ttf"))
    for tx, txt in ((68, "4.10/3.50-4 PNEUMATIC"), (395, "NOT FOR CANNON USE"), (715, "MAX 300 PSI · BAKERSFIELD")):
        d.text((tx, 84), txt, fill=(58, 60, 64), font=f_tire)
        d.text((tx + 1, 85), txt, fill=(22, 24, 26), font=f_tire)
        d.text((tx, 396), txt, fill=(58, 60, 64), font=f_tire)

    path = os.path.join(out_dir, "rod_wheel.png")
    im.save(path, "PNG", optimize=True)
    return path


def build_hand_texture(out_dir):
    """512x512 Classic Quake Ranger Combat Glove matching `mmw_geometry.build_articulated_ranger_hand` UVs:
      - `UV_LEATHER = (0.04, 0.04, 0.46, 0.46)` [y:0..256,   x:0..256]   : Warm distressed brown leather dorsal glove
      - `UV_PALM    = (0.54, 0.04, 0.96, 0.46)` [y:0..256,   x:256..512] : Darker grippy suede palm & curled fingers
      - `UV_CUFF    = (0.02, 0.53, 0.48, 0.97)` [y:256..512, x:0..256]   : Riveted Ranger bronze-brown forearm gauntlet
      - `UV_KNUCKLE = (0.53, 0.53, 0.97, 0.73)` [y:256..384, x:256..512] : Brushed gunmetal-bronze knuckle armor plate
      - `UV_SLEEVE  = (0.53, 0.77, 0.97, 0.98)` [y:384..512, x:256..512] : Dark olive-brown padded combat sleeve
    """
    W = H = 512
    arr = np.zeros((H, W, 3), dtype=np.float32)
    nf = _fbm(H, W, seed=303, octaves=(4, 8, 16, 32, 64))

    # Top-left [0..256, 0..256]: Classic Quake Ranger warm brown leather glove (`UV_LEATHER`)
    grain_l = 74.0 + 20.0 * nf[:256, :256]
    arr[:256, :256, 0] = np.clip(grain_l * 1.22, 30, 148)
    arr[:256, :256, 1] = np.clip(grain_l * 0.82, 20, 102)
    arr[:256, :256, 2] = np.clip(grain_l * 0.54, 12, 68)

    # Top-right [0..256, 256..512]: Darker reinforced grip leather for palm & fingers (`UV_PALM`)
    grain_p = 58.0 + 18.0 * nf[:256, 256:]
    arr[:256, 256:, 0] = np.clip(grain_p * 1.18, 24, 124)
    arr[:256, 256:, 1] = np.clip(grain_p * 0.80, 16, 86)
    arr[:256, 256:, 2] = np.clip(grain_p * 0.54, 10, 58)

    # Bottom-left [256..512, 0..256]: Quake Ranger bronze-brown armored gauntlet cuff (`UV_CUFF`)
    u = np.linspace(0.0, 1.0, 256, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    bracer = 98.0 + 34.0 * np.cos((u - 0.5) * 2.0 * np.pi) + 10.0 * np.sin(v * 20.0) + 10.0 * nf[256:, :256]
    arr[256:, :256, 0] = np.clip(bracer * 1.22, 34, 198)
    arr[256:, :256, 1] = np.clip(bracer * 0.90, 24, 152)
    arr[256:, :256, 2] = np.clip(bracer * 0.56, 14, 98)

    # Bottom-right upper [256..384, 256..512]: Brushed gunmetal-bronze knuckle guard (`UV_KNUCKLE`)
    plate = 136.0 + 42.0 * np.sin(u * math.pi) + 10.0 * nf[256:384, 256:]
    arr[256:384, 256:, 0] = np.clip(plate * 1.04, 42, 224)
    arr[256:384, 256:, 1] = np.clip(plate * 0.96, 38, 210)
    arr[256:384, 256:, 2] = np.clip(plate * 0.84, 34, 192)

    # Bottom-right lower [384..512, 256..512]: Ranger dark olive-tan combat sleeve (`UV_SLEEVE`)
    vs = np.linspace(0.0, 1.0, 128, dtype=np.float32)[:, None]
    sleeve = 68.0 + 18.0 * np.cos((u - 0.5) * 2.0 * np.pi) + 6.0 * np.sin(vs * 28.0) + 10.0 * nf[384:, 256:]
    arr[384:, 256:, 0] = np.clip(sleeve * 1.12, 24, 128)
    arr[384:, 256:, 1] = np.clip(sleeve * 0.94, 20, 108)
    arr[384:, 256:, 2] = np.clip(sleeve * 0.62, 14, 76)

    im = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    d = ImageDraw.Draw(im)
    # Brass cuff trim band & rivets on `UV_CUFF` [x:0..256, y:256..512]
    d.rectangle((14, 282, 242, 298), fill=(184, 138, 58))
    d.rectangle((14, 474, 242, 488), fill=(156, 114, 46))
    for rx in (44, 102, 158, 212):
        _draw_rivet(d, rx, 324, 8)
        _draw_rivet(d, rx, 444, 8)
    # Knuckle plate rivets on `UV_KNUCKLE` [x:256..512, y:256..384]
    for rx in (296, 356, 416, 474):
        _draw_rivet(d, rx, 320, 7)
    path = os.path.join(out_dir, "rod_hand.png")
    im.save(path, "PNG", optimize=True)
    return path


def build_fx_texture(out_dir):
    """512x512 RGBA additive FX atlas: Cannon Starburst Blast, Cartoon Smoke/Shock-Ring, Burnout Sparks & Smoke."""
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    nf = _fbm(H, W, seed=505, octaves=(4, 8, 16, 32))

    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    dx, dy = (xx - 128.0) / 128.0, (yy - 128.0) / 128.0
    r = np.sqrt(dx * dx + dy * dy) + 1e-6
    ang = np.arctan2(dy, dx)

    # --- Q1 [0..256, 0..256]: Cartoon Cannon Fiery-Gold & White-Hot Starburst Flash ---
    rays = 0.50 + 0.50 * np.cos(ang * 10.0 + 0.30 * nf[:256, :256])
    burst = np.clip(np.maximum(0.0, 1.0 - r / (0.56 + 0.42 * rays)) ** 1.30, 0.0, 1.0)
    core_hot = np.exp(-(r * r) / 0.14)
    a1 = np.clip(burst + core_hot, 0.0, 1.0)
    rgba[:256, :256, 0] = np.clip((1.00 * burst + 1.00 * core_hot) * 255.0, 0, 255)
    rgba[:256, :256, 1] = np.clip((0.76 * burst + 0.98 * core_hot) * 255.0, 0, 255)
    rgba[:256, :256, 2] = np.clip((0.28 * burst + 0.94 * core_hot) * 255.0, 0, 255)
    rgba[:256, :256, 3] = a1 * 255.0

    # --- Q2 [0..256, 256..512]: Puffy Cartoon Cannon Smoke-Ring / Shockwave Donut ---
    wobble_r = r + 0.035 * nf[:256, 256:]
    ring = np.exp(-((wobble_r - 0.70) ** 2) / 0.015) * np.clip(1.0 - np.maximum(0.0, r - 0.95) * 16.0, 0.0, 1.0)
    inner_glow = 0.30 * np.exp(-((wobble_r - 0.46) ** 2) / 0.022)
    a2 = np.clip(ring + inner_glow, 0.0, 1.0)
    rgba[:256, 256:, 0] = np.clip(a2 * 248.0, 0, 255)
    rgba[:256, 256:, 1] = np.clip(a2 * 242.0, 0, 255)
    rgba[:256, 256:, 2] = np.clip(a2 * 228.0, 0, 255)
    rgba[:256, 256:, 3] = a2 * 255.0

    # --- Q3 [256..512, 0..256]: Tire-Burnout Friction Sparks & Overpressure Streaks ---
    ux = xx / 256.0
    uy = (yy - 128.0) / 128.0
    s1 = np.exp(-((uy - 0.18 * np.sin(ux * 14.0)) ** 2) / 0.008) * np.sin(np.clip(ux, 0.0, 1.0) * np.pi)
    s2 = np.exp(-((uy + 0.22 * np.cos(ux * 11.0)) ** 2) / 0.006) * np.sin(np.clip(ux, 0.0, 1.0) * np.pi)
    sp = np.clip(s1 + s2, 0.0, 1.0)
    rgba[256:, :256, 0] = np.clip(sp * 255.0, 0, 255)
    rgba[256:, :256, 1] = np.clip(sp * 205.0, 0, 255)
    rgba[256:, :256, 2] = np.clip(sp * 95.0, 0, 255)
    rgba[256:, :256, 3] = np.clip(sp * 255.0, 0, 255)

    # --- Q4 [256..512, 256..512]: White Tire-Burnout / Muzzle-Vent Smoke Puff ---
    cloud = np.clip((np.maximum(0.0, 1.0 - r) ** 1.35) * (0.70 + 0.30 * nf[256:, 256:]), 0.0, 1.0)
    rgba[256:, 256:, 0] = cloud * 232.0
    rgba[256:, 256:, 1] = cloud * 234.0
    rgba[256:, 256:, 2] = cloud * 238.0
    rgba[256:, 256:, 3] = cloud * 220.0

    path = os.path.join(out_dir, "rod_fx.png")
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA").save(path, "PNG", optimize=True)
    return path


def build_env_texture(out_dir):
    """256x256 DarkPlaces `tcGen environment` studio chrome specular map (kept subtle so chrome gleams without blowout)."""
    S = 256
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    nx = (xx - 128.0) / 128.0
    ny = (yy - 128.0) / 128.0
    band1 = np.exp(-((ny + 0.38 - 0.18 * nx) ** 2) / 0.022)
    band2 = 0.55 * np.exp(-((ny - 0.28 + 0.12 * nx) ** 2) / 0.035)
    spot = 0.65 * np.exp(-((nx + 0.32) ** 2 + (ny + 0.42) ** 2) / 0.055)
    val = np.clip(0.08 + 0.72 * band1 + 0.45 * band2 + spot, 0.0, 1.0)
    rgb = np.stack([val * 235.0, val * 244.0, val * 255.0], axis=-1)
    path = os.path.join(out_dir, "rod_env.png")
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)
    return path


def build_all_textures(stage_tex_dir, progs_dir):
    os.makedirs(stage_tex_dir, exist_ok=True)
    os.makedirs(progs_dir, exist_ok=True)

    paths = {
        "chrome": build_chrome_texture(stage_tex_dir),
        "wheel":  build_wheel_texture(stage_tex_dir),
        "hand":   build_hand_texture(stage_tex_dir),
        "fx":     build_fx_texture(stage_tex_dir),
        "env":    build_env_texture(stage_tex_dir),
    }

    # Deploy DarkPlaces HDR-calibrated textures into `progs/` (DarkPlaces renders ~2.2-2.5x bright!)
    for key, gain in (("chrome", 0.64), ("wheel", 0.54), ("hand", 0.52)):
        arr = np.asarray(Image.open(paths[key]).convert("RGB"), dtype=np.float32)
        Image.fromarray(np.clip(arr * gain, 0, 255).astype(np.uint8), mode="RGB").save(
            os.path.join(progs_dir, f"rod_{key}.png"), "PNG", optimize=True
        )

    # DarkPlaces per-pixel specular `_gloss` map for `progs/rod_chrome_gloss.png` (gleaming steel, satin black cap, matte bore)
    ch_arr = np.asarray(Image.open(paths["chrome"]).convert("RGB"), dtype=np.float32)
    gloss = np.clip(ch_arr * 0.42, 0, 128)
    gloss[512:768, 512:, :] *= 0.35  # satin black Delrin muzzle collar
    gloss[768:, 512:, :] = 0.0       # non-reflective hollow bore interior
    Image.fromarray(gloss.astype(np.uint8), mode="RGB").save(
        os.path.join(progs_dir, "rod_chrome_gloss.png"), "PNG", optimize=True
    )
    env_old = os.path.join(progs_dir, "rod_env.png")
    if os.path.exists(env_old):
        os.remove(env_old)

    fx_rgba = np.asarray(Image.open(paths["fx"]).convert("RGBA"), dtype=np.float32)
    fx_premul = fx_rgba[..., :3] * (fx_rgba[..., 3:4] / 255.0) * 0.76
    Image.fromarray(np.clip(fx_premul, 0, 255).astype(np.uint8), mode="RGB").save(
        os.path.join(progs_dir, "rod_fx.png"), "PNG", optimize=True
    )

    # Unified 2:1 classic Quake `.mdl` single-skin atlas (1024x512 hires `_0.tga` + 512x256 embedded `IDPO` v6 skin):
    #   [u: 0.00..0.375, v: 0.0..1.0] -> rod_chrome (384x512)
    #   [u: 0.375..0.75, v: 0.0..1.0] -> rod_wheel  (384x512)
    #   [u: 0.75..1.00,  v: 0.0..0.5] -> rod_hand   (256x256)
    #   [u: 0.75..1.00,  v: 0.5..1.0] -> rod_fx     (256x256, fullbright-eligible!)
    atlas_hi = Image.new("RGB", (1024, 512), (16, 18, 22))
    atlas_hi.paste(Image.open(paths["chrome"]).convert("RGB").resize((384, 512), Image.LANCZOS), (0, 0))
    atlas_hi.paste(Image.open(paths["wheel"]).convert("RGB").resize((384, 512), Image.LANCZOS), (384, 0))
    atlas_hi.paste(Image.open(paths["hand"]).convert("RGB").resize((256, 256), Image.LANCZOS), (768, 0))
    fx_rgb_hi = Image.fromarray(np.clip(fx_rgba[..., :3] * (fx_rgba[..., 3:4] / 255.0), 0, 255).astype(np.uint8), mode="RGB")
    atlas_hi.paste(fx_rgb_hi.resize((256, 256), Image.LANCZOS), (768, 256))

    paths["mdl_atlas_hi"] = os.path.join(stage_tex_dir, "rod_mdl_atlas_1024x512.png")
    atlas_hi.save(paths["mdl_atlas_hi"], "PNG", optimize=True)

    atlas_lo = atlas_hi.resize((512, 256), Image.LANCZOS)
    paths["mdl_atlas_lo"] = os.path.join(stage_tex_dir, "rod_mdl_atlas_512x256.png")
    atlas_lo.save(paths["mdl_atlas_lo"], "PNG", optimize=True)

    return paths
