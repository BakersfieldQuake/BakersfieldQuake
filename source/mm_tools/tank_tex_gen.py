"""Procedural & original photogrammetry texture + DarkPlaces shader synthesis
for the Pure-Original Mega Man Tank (2 big wheels + straight cross-axle + silver bar):
  - progs/mmt_orig.png / mmt_orig_burn.png          (1024x1024 original photogrammetry atlas from PK3 mm_debris_tex.png)
  - progs/mmt_chrome_bar.png / mmt_chrome_burn.png   (1024x1024 mirror-chrome bar, TIG T-collar, stainless axle, rubber cap, nut, pin)
  - progs/mmt_wheel.png / mmt_wheel_burn.png         (1024x1024 5-ribbed tire tread, molded sidewall, smooth off-white stamped dish rim)
  - progs/mmt_fx.png                                 (512x512 RGBA rocket exhaust plume, launch ring, chrome glint)
  - scripts/mm_tank.shader
"""
import io
import math
import os
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# UV rects in mmt_chrome_bar.png
UV_CHROME_BAR   = (0.02, 0.02, 0.48, 0.48)
UV_STAINLESS    = (0.52, 0.02, 0.98, 0.48)
UV_RUBBER_CAP   = (0.02, 0.52, 0.48, 0.98)
UV_HEX_ZINC     = (0.52, 0.52, 0.73, 0.73)
UV_COTTER_YEL   = (0.77, 0.52, 0.98, 0.73)
UV_VALVE_BLK    = (0.52, 0.77, 0.73, 0.98)
UV_VALVE_BRASS  = (0.77, 0.77, 0.98, 0.98)

# UV rects in mmt_wheel.png
UV_WHEEL_TREAD  = (0.01, 0.01, 0.49, 0.49)
UV_WHEEL_SIDE   = (0.51, 0.01, 0.99, 0.49)
UV_WHEEL_RIM    = (0.01, 0.51, 0.49, 0.99)
UV_WHEEL_IRIM   = (0.51, 0.51, 0.99, 0.99)

# UV rects in mmt_fx.png
UV_FX_PLUME     = (0.02, 0.02, 0.48, 0.48)
UV_FX_RING      = (0.52, 0.02, 0.98, 0.48)
UV_FX_GLINT     = (0.02, 0.52, 0.48, 0.98)
UV_FX_SPARK     = (0.52, 0.52, 0.98, 0.98)


def _font(size, bold=True):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fbm(h, w, seed=42, octaves=(4, 8, 16, 32, 64)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tw = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh = max(2, h // freq)
        gw = max(2, w // freq)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(g, mode="F").resize((w, h), Image.Resampling.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tw += amp
    return acc / max(tw, 1e-6)


def _make_subtle_soot(arr_rgb, seed=99):
    """Subtle smoky soot darkening for <40% HP _1.skin (no bright orange neon)."""
    h, w = arr_rgb.shape[:2]
    nc = _fbm(h, w, seed=seed, octaves=(4, 8, 16, 32))
    soot = np.clip(0.46 + 0.34 * nc, 0.24, 0.82)[..., None]
    out = arr_rgb.astype(np.float32) * soot * np.array([0.92, 0.86, 0.80], dtype=np.float32)
    return np.clip(out, 4, 150).astype(np.uint8)


def build_orig_textures(mod_dir, progs_dir):
    pk3_path = os.path.join(mod_dir, "bakersfield.pk3")
    with zipfile.ZipFile(pk3_path) as z:
        raw = z.read("progs/mm_debris_tex.png")
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    arr_f = np.asarray(im, dtype=np.float32) / 255.0
    # Calibrate down for Zircon r_hdr_scenebrightness 1.45 + r_minlight 3 so V1 matches the dark-rubber/steel toy
    arr = np.clip(np.round(arr_f * 0.78 * 255.0), 0, 255).astype(np.uint8)
    p_orig = os.path.join(progs_dir, "mmt_orig.png")
    Image.fromarray(arr, mode="RGB").save(p_orig, "PNG", optimize=True)
    p_burn = os.path.join(progs_dir, "mmt_orig_burn.png")
    Image.fromarray(_make_subtle_soot(arr, seed=91), mode="RGB").save(p_burn, "PNG", optimize=True)
    return p_orig, p_burn


def build_chrome_bar_textures(progs_dir):
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    nf = _fbm(H, W, seed=201, octaves=(2, 4, 8, 16, 32))

    # Q1: Liquid-Mirror Polished Chrome Silver Bar
    u = np.linspace(0.0, 2.0 * math.pi, 512, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, 512, dtype=np.float32)[:, None]
    refl = (
        0.62
        + 0.24 * np.cos(u - 0.85)
        + 0.15 * np.cos(2.0 * u + 0.42)
        + 0.08 * np.sin(3.0 * u - 0.25)
        - 0.16 * np.exp(-((u - 3.55) ** 2) / 0.14)
        + 0.25 * np.exp(-((u - 1.52) ** 2) / 0.065)
    )
    lathe = 0.012 * np.sin(v * 340.0)
    weld_ao = 1.0 - 0.16 * np.exp(-((v - 0.46) ** 2) / 0.0020)
    c_val = np.clip((refl + lathe + 0.015 * nf[:512, :512]) * weld_ao, 0.14, 1.0)
    arr[:512, :512, 0] = c_val * 240.0
    arr[:512, :512, 1] = c_val * 246.0
    arr[:512, :512, 2] = np.clip(c_val * 254.0 + 4.0, 0, 255)

    # Q2: Brushed Stainless Axle & TIG Weld T-Collar
    steel = 0.58 + 0.20 * np.cos(u - 0.65) + 0.10 * np.cos(2.0 * u) + 0.028 * nf[:512, 512:]
    steel += 0.018 * np.sin(v * 380.0)
    tint_straw = np.exp(-((v - 0.84) ** 2) / 0.0032)
    tint_blue = np.exp(-((v - 0.90) ** 2) / 0.0018)
    bead_rip = 1.0 + 0.12 * np.sin(u * 24.0) * np.exp(-((v - 0.95) ** 2) / 0.0022)
    s_r = steel * 218.0 + tint_straw * 36.0 - tint_blue * 20.0
    s_g = steel * 222.0 + tint_straw * 15.0 - tint_blue * 8.0
    s_b = steel * 232.0 - tint_straw * 22.0 + tint_blue * 32.0
    arr[:512, 512:, 0] = np.clip(s_r * bead_rip, 24, 255)
    arr[:512, 512:, 1] = np.clip(s_g * bead_rip, 24, 255)
    arr[:512, 512:, 2] = np.clip(s_b * bead_rip, 26, 255)

    # Q3: Matte Ribbed Charcoal Rubber Rear Cap
    vr = np.linspace(0.0, 1.0, 512, dtype=np.float32)[:, None]
    ribs = 0.5 + 0.5 * np.cos(vr * 2.0 * math.pi * 8.0)
    rub = 40.0 + 16.0 * ribs + 4.5 * nf[512:, :512]
    arr[512:, :512, 0] = np.clip(rub * 0.95, 14, 92)
    arr[512:, :512, 1] = np.clip(rub * 0.98, 14, 96)
    arr[512:, :512, 2] = np.clip(rub * 1.05, 16, 106)

    # Q4: Hardware Sub-Swatches (Zinc hex, Yellow cotter pin, Valve rubber, Brass)
    zn = 188.0 + 14.0 * nf[512:768, 512:768]
    arr[512:768, 512:768, 0] = np.clip(zn * 0.97, 30, 240)
    arr[512:768, 512:768, 1] = np.clip(zn * 1.00, 30, 245)
    arr[512:768, 512:768, 2] = np.clip(zn * 1.05, 34, 252)

    yp = 1.0 + 0.06 * nf[512:768, 768:]
    arr[512:768, 768:, 0] = np.clip(248.0 * yp, 0, 255)
    arr[512:768, 768:, 1] = np.clip(204.0 * yp, 0, 255)
    arr[512:768, 768:, 2] = np.clip(36.0 * yp, 0, 255)

    vb = 32.0 + 5.0 * nf[768:, 512:768]
    arr[768:, 512:768, 0] = vb
    arr[768:, 512:768, 1] = vb + 1.0
    arr[768:, 512:768, 2] = vb + 4.0

    v_th = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    br = (0.86 + 0.14 * np.sin(v_th * 128.0)) * (1.0 + 0.05 * nf[768:, 768:])
    arr[768:, 768:, 0] = np.clip(226.0 * br, 0, 255)
    arr[768:, 768:, 1] = np.clip(182.0 * br, 0, 255)
    arr[768:, 768:, 2] = np.clip(76.0 * br, 0, 255)

    # Calibrate chrome/steel albedo for Zircon overbright lighting (matching mmw_chrome_axle.png ~0.45x)
    u8 = np.clip(arr * 0.45, 0, 255).astype(np.uint8)
    p_norm = os.path.join(progs_dir, "mmt_chrome_bar.png")
    Image.fromarray(u8, mode="RGB").save(p_norm, "PNG", optimize=True)
    p_burn = os.path.join(progs_dir, "mmt_chrome_burn.png")
    Image.fromarray(_make_subtle_soot(u8, seed=92), mode="RGB").save(p_burn, "PNG", optimize=True)
    return p_norm, p_burn


def build_wheel_textures(progs_dir):
    """1024x1024 clean original-style Mega Man wheel atlas (smooth concave white steel dish rim, zero cutouts)."""
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    grain = _fbm(H, W, seed=303, octaves=(2, 4, 8, 16, 32))

    # Q1: 5-Ribbed Tire Tread
    ux = np.linspace(0.0, 1.0, 512, dtype=np.float32)[None, :]
    vy = np.linspace(0.0, 2.0 * math.pi, 512, dtype=np.float32)[:, None]
    groove_mask = np.zeros_like(ux)
    for gc in (0.20, 0.39, 0.61, 0.80):
        groove_mask += np.exp(-((ux - gc) ** 2) / (2.0 * 0.022 ** 2))
    groove_mask = np.clip(groove_mask, 0.0, 1.0)
    sipes = 0.22 * (np.sin(vy * 26.0) > 0.42).astype(np.float32) * (1.0 - groove_mask)
    shoulder = 1.0 - 0.20 * ((2.0 * ux - 1.0) ** 4)
    base_rub = (74.0 - 38.0 * groove_mask - 12.0 * sipes) * shoulder + 5.5 * grain[:512, :512]
    dust = 10.0 * (1.0 - groove_mask) * (0.55 + 0.45 * np.sin(vy * 4.0 + 0.6))
    tread_c = np.clip(base_rub + dust, 18.0, 145.0)
    arr[:512, :512, 0] = tread_c * 0.97
    arr[:512, :512, 1] = tread_c * 0.99
    arr[:512, :512, 2] = tread_c * 1.04

    # Q2: Polar Molded Rubber Sidewall
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    rx = (xx - 255.5) / 245.0
    ry = (yy - 255.5) / 245.0
    rr = np.sqrt(rx * rx + ry * ry)
    ang = np.arctan2(ry, rx)

    sw = 62.0 + 13.0 * np.exp(-((rr - 0.78) ** 2) / 0.009)
    sw += 13.0 * np.exp(-((rr - 0.61) ** 2) / 0.0003) - 9.0 * np.exp(-((rr - 0.625) ** 2) / 0.0003)
    sw += 10.0 * np.exp(-((rr - 0.89) ** 2) / 0.0003) - 7.0 * np.exp(-((rr - 0.903) ** 2) / 0.0003)
    sw_ribs = 9.0 * (np.cos(ang * 8.0) > 0.80).astype(np.float32) * np.exp(-((rr - 0.75) ** 2) / 0.014)
    sw = sw + sw_ribs - 16.0 * np.exp(-((rr - 0.56) ** 2) / 0.0008) + 4.5 * grain[:512, 512:]
    arr[:512, 512:, 0] = np.clip(sw * 0.97, 18, 120)
    arr[:512, 512:, 1] = np.clip(sw * 0.99, 18, 122)
    arr[:512, 512:, 2] = np.clip(sw * 1.05, 20, 128)

    # Q3: Smooth Concave Off-White Stamped Steel Outer Rim (matching original megaman.png!)
    rim = np.full((512, 512), 230.0, dtype=np.float32)
    rim += 20.0 * np.exp(-((rr - 0.93) ** 2) / 0.0012)
    rim -= 32.0 * np.exp(-((rr - 0.83) ** 2) / 0.0022)
    rim -= 18.0 * np.exp(-((rr - 0.52) ** 2) / 0.055)
    rim += 14.0 * (rx * -0.55 + ry * -0.55) * np.clip(1.0 - np.abs(rr - 0.55), 0.0, 1.0)
    # 4 subtle stamped weld/rivet dimples (no big black cutouts)
    for k in range(4):
        ba = math.radians(k * 90.0 + 45.0)
        bdx = rx - 0.34 * math.cos(ba)
        bdy = ry - 0.34 * math.sin(ba)
        rim -= 26.0 * np.exp(-(bdx * bdx + bdy * bdy) / 0.0011)
    rim -= 26.0 * np.exp(-((rr - 0.26) ** 2) / 0.0009)
    rim += 10.0 * (rr < 0.24).astype(np.float32)
    va = math.radians(-35.0)
    vdx = rx - 0.66 * math.cos(va)
    vdy = ry - 0.66 * math.sin(va)
    rim -= 95.0 * np.exp(-(vdx * vdx + vdy * vdy) / 0.0016)
    rim += 2.4 * grain[512:, :512]
    arr[512:, :512, 0] = np.clip(rim * 0.985, 22, 253)
    arr[512:, :512, 1] = np.clip(rim * 0.995, 22, 254)
    arr[512:, :512, 2] = np.clip(rim * 1.015, 25, 255)

    # Q4: Inner White Steel Rim w/ Sealed Bearing Hub
    irim = np.full((512, 512), 222.0, dtype=np.float32)
    irim += 18.0 * np.exp(-((rr - 0.92) ** 2) / 0.0015) - 26.0 * np.exp(-((rr - 0.82) ** 2) / 0.0025)
    seal_mask = (rr >= 0.155) & (rr <= 0.255)
    outer_race = (rr > 0.255) & (rr <= 0.315)
    inner_bore = rr < 0.095
    irim = np.where(outer_race, 185.0 + 32.0 * np.cos(ang * 2.0), irim)
    irim = np.where(seal_mask, 42.0 + 8.0 * np.sin(ang * 6.0), irim)
    irim = np.where(inner_bore, 30.0, irim)
    irim += 2.6 * grain[512:, 512:]
    arr[512:, 512:, 0] = np.clip(irim * 0.985, 18, 252)
    arr[512:, 512:, 1] = np.clip(irim * 0.995, 18, 254)
    arr[512:, 512:, 2] = np.clip(irim * 1.015, 20, 255)

    # Calibrate wheel rim & rubber albedo for Zircon overbright lighting (matching mmw_wheel.png ~0.42x)
    u8 = np.clip(arr * 0.42, 0, 255).astype(np.uint8)
    p_norm = os.path.join(progs_dir, "mmt_wheel.png")
    Image.fromarray(u8, mode="RGB").save(p_norm, "PNG", optimize=True)
    p_burn = os.path.join(progs_dir, "mmt_wheel_burn.png")
    Image.fromarray(_make_subtle_soot(u8, seed=93), mode="RGB").save(p_burn, "PNG", optimize=True)
    return p_norm, p_burn


def build_fx_texture(out_path):
    """512x512 RGBA additive FX atlas (rocket fire plume, launch shockwave ring, chrome star glint)."""
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    nx = (xx - 127.5) / 120.0
    ny = (yy - 127.5) / 120.0
    rr = np.sqrt(nx * nx + ny * ny)
    ang = np.arctan2(ny, nx)

    plume_u = xx / 255.0
    flame = np.exp(-((ny * 1.15) ** 2) / (0.12 + 0.24 * plume_u)) * np.clip(1.0 - plume_u * 0.72, 0.0, 1.0)
    flame *= (0.78 + 0.22 * np.sin(plume_u * 26.0 + ny * 9.0))
    rgba[:256, :256, 0] = np.clip(255.0 * flame * 1.25, 0, 255)
    rgba[:256, :256, 1] = np.clip(195.0 * (flame ** 1.3), 0, 255)
    rgba[:256, :256, 2] = np.clip(90.0 * (flame ** 2.2), 0, 255)
    rgba[:256, :256, 3] = np.clip(255.0 * flame, 0, 255)

    ring = np.exp(-((rr - 0.70) ** 2) / 0.018) * (0.75 + 0.25 * np.cos(ang * 10.0))
    core = np.exp(-(rr * rr) / 0.12)
    a2 = np.clip(ring + 0.55 * core, 0.0, 1.0)
    rgba[:256, 256:, 0] = 255.0 * a2
    rgba[:256, 256:, 1] = 210.0 * ring + 245.0 * core
    rgba[:256, 256:, 2] = 95.0 * ring + 210.0 * core
    rgba[:256, 256:, 3] = 255.0 * a2

    ray_main = np.exp(-(nx * nx) / 0.0045) * np.exp(-(ny * ny) / 0.28) + np.exp(-(ny * ny) / 0.0045) * np.exp(-(nx * nx) / 0.28)
    dx1 = (nx + ny) * 0.7071
    dy1 = (nx - ny) * 0.7071
    ray_diag = 0.65 * (np.exp(-(dx1 * dx1) / 0.005) * np.exp(-(dy1 * dy1) / 0.14) + np.exp(-(dy1 * dy1) / 0.005) * np.exp(-(dx1 * dx1) / 0.14))
    halo = 0.52 * np.exp(-(rr * rr) / 0.045)
    glint = np.clip(ray_main + ray_diag + halo, 0.0, 1.0)
    rgba[256:, :256, 0] = 255.0 * glint
    rgba[256:, :256, 1] = 250.0 * glint
    rgba[256:, :256, 2] = np.clip(225.0 * glint + 30.0 * ray_main, 0, 255)
    rgba[256:, :256, 3] = 255.0 * glint

    sp_rays = 0.6 + 0.4 * np.cos(ang * 12.0)
    sp = np.exp(-(rr * rr) / 0.15) * sp_rays
    rgba[256:, 256:, 0] = 255.0 * sp
    rgba[256:, 256:, 1] = 215.0 * sp
    rgba[256:, 256:, 2] = 110.0 * sp
    rgba[256:, 256:, 3] = 255.0 * np.clip(sp, 0.0, 1.0)

    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA").save(out_path, "PNG", optimize=True)
    return out_path


def build_aim_beam_texture(out_path):
    """64x32 soft-edged laser beam strip for the tank trajectory aiming line."""
    W, H = 64, 32
    yy, _ = np.mgrid[0:H, 0:W].astype(np.float32)
    v = np.abs((yy + 0.5) / H - 0.5) * 2.0
    core = np.exp(-(v * v) / 0.08)
    halo = 0.45 * np.exp(-(v * v) / 0.36) * np.clip(1.0 - v, 0.0, 1.0)
    val = np.clip(core + halo, 0.0, 1.0)
    rgb = np.repeat((val * 255.0)[..., None], 3, axis=2)
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


SHADER_TEXT = """// written by mm_tools/build_tank_models.py

progs/mmt_orig
{
\tcull none
\t{
\t\tmap progs/mmt_orig
\t\trgbGen lightingDiffuse
\t}
}

progs/mmt_orig_burn
{
\tcull none
\t{
\t\tmap progs/mmt_orig_burn
\t\trgbGen lightingDiffuse
\t}
}

progs/mmt_chrome_bar
{
\tcull none
\t{
\t\tmap progs/mmt_chrome_bar
\t\trgbGen lightingDiffuse
\t}
}

progs/mmt_chrome_burn
{
\tcull none
\t{
\t\tmap progs/mmt_chrome_burn
\t\trgbGen lightingDiffuse
\t}
}

progs/mmt_wheel
{
\tcull none
\t{
\t\tmap progs/mmt_wheel
\t\trgbGen lightingDiffuse
\t}
}

progs/mmt_wheel_burn
{
\tcull none
\t{
\t\tmap progs/mmt_wheel_burn
\t\trgbGen lightingDiffuse
\t}
}

progs/mmt_fx
{
\tcull none
\t{
\t\tmap progs/mmt_fx
\t\tblendfunc add
\t\trgbGen const ( 0.30 0.30 0.30 )
\t}
}

progs/mmt_aim_beam
{
\tcull none
\t{
\t\tmap progs/mmt_aim_beam
\t\tblendfunc add
\t\trgbGen vertex
\t}
}
"""


def ensure_tank_textures_and_shader(mod_dir):
    progs_dir = os.path.join(mod_dir, "progs")
    scripts_dir = os.path.join(mod_dir, "scripts")
    os.makedirs(progs_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)

    # Remove obsolete chassis/glow PNGs if present
    for old_fn in ("mmt_chassis.png", "mmt_chassis_burn.png", "mmt_glow.png"):
        old_p = os.path.join(progs_dir, old_fn)
        if os.path.exists(old_p):
            os.remove(old_p)

    p_orig, p_orig_burn = build_orig_textures(mod_dir, progs_dir)
    p_chrome, p_chrome_burn = build_chrome_bar_textures(progs_dir)
    p_wheel, p_wheel_burn = build_wheel_textures(progs_dir)
    p_fx = build_fx_texture(os.path.join(progs_dir, "mmt_fx.png"))
    p_beam = build_aim_beam_texture(os.path.join(progs_dir, "mmt_aim_beam.png"))

    shader_path = os.path.join(scripts_dir, "mm_tank.shader")
    with open(shader_path, "w", encoding="ascii", newline="\n") as f:
        f.write(SHADER_TEXT)

    return dict(
        orig=p_orig,
        orig_burn=p_orig_burn,
        chrome_bar=p_chrome,
        chrome_burn=p_chrome_burn,
        wheel=p_wheel,
        wheel_burn=p_wheel_burn,
        fx=p_fx,
        aim_beam=p_beam,
        shader=shader_path,
    )
