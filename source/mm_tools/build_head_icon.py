"""JohnWave grenade icon.  Isolates the suit guy's head from the front reference photo and wraps it in a Quake-style
pineapple grenade shell with a fuse cap, safety lever and pull ring.

python3 -E -P build_head_icon.py [outdir]     (default: BakersfieldQuake/source/mm_tools/out/icon)
writes johnwave_head.png (cutout), johnwave_grenade.png (transparent), johnwave_grenade_tile.png, johnwave_sizes.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "icon")
os.makedirs(OUT, exist_ok=True)
REF = os.path.join(HERE, "out", "chars", "ref", "suit_front.jpg")

N = 1024            # final icon size
SS = 2              # supersampling for the drawn parts
W = N * SS


# ---------------------------------------------------------------- head cutout
def head_cutout():
    im = Image.open(REF).convert("RGB")
    x0, y0, x1, y1 = 420, 20, 730, 345
    a = np.asarray(im, np.float32)
    # background: grey gradient, estimate per row from the left/right margins
    bg = np.concatenate([a[:, 0:90], a[:, -90:]], axis=1).mean(axis=1)           # (H,3)
    diff = np.abs(a - bg[:, None, :]).max(axis=2)
    luma = a @ np.array([0.299, 0.587, 0.114], np.float32)
    ys = np.arange(a.shape[0])[:, None]
    m = diff > 26
    m &= (ys < 268) | (luma < 88)                          # below the cheeks only the dark beard stays
    m &= (ys < 322)
    m[:, :x0] = False
    m[:, x1:] = False
    m[:y0] = False
    m = ndi.binary_closing(m, iterations=3)
    m = ndi.binary_fill_holes(m)
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(sizes)))
    m = ndi.binary_opening(m, iterations=2)
    # tidy the cut under the beard with a smooth curve
    mf = ndi.gaussian_filter(m.astype(np.float32), 1.3)
    alpha = np.clip((mf - 0.56) * 4 + 0.5, 0, 1)
    rgba = np.dstack([a, alpha * 255]).astype(np.uint8)
    ys_, xs_ = np.where(alpha > 0.02)
    box = (xs_.min() - 4, ys_.min() - 4, xs_.max() + 5, ys_.max() + 5)
    return Image.fromarray(rgba, "RGBA").crop(box)


# ---------------------------------------------------------------- drawing helpers
def lin(h, w, c0, c1, vertical=True):
    t = np.linspace(0, 1, h if vertical else w, dtype=np.float32)
    t = t[:, None] if vertical else t[None, :]
    c0, c1 = np.array(c0, np.float32), np.array(c1, np.float32)
    g = c0 * (1 - t[..., None]) + c1 * t[..., None]
    return np.broadcast_to(g, (h, w, 3)).copy()


def cyl(w, h, dark, mid, light, hi=0.35):
    """horizontal cylinder shading (light from the upper left)"""
    x = np.linspace(0, 1, w, dtype=np.float32)
    prof = np.where(x < hi, dark + (light - dark) * (x / hi) if False else 0, 0)
    out = np.zeros((h, w, 3), np.float32)
    d, m, l = (np.array(c, np.float32) for c in (dark, mid, light))
    for i, t in enumerate(x):
        if t < hi:
            u = t / hi
            c = d * (1 - u) + l * u
        else:
            u = (t - hi) / (1 - hi)
            c = l * (1 - u) + d * u
            c = c * 0.75 + m * 0.25
        out[:, i] = c
    return out


def paste_shape(canvas, shape_mask, color_arr, offset=(0, 0)):
    """composite an (h,w,3) colour array through an L mask onto an RGBA canvas at offset"""
    ox, oy = offset
    h, w = shape_mask.size[1], shape_mask.size[0]
    layer = Image.fromarray(np.dstack([color_arr, np.full((h, w), 255, np.uint8)]).astype(np.uint8), "RGBA")
    layer.putalpha(shape_mask)
    canvas.alpha_composite(layer, (ox, oy))


def rrect_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def outline(canvas, mask_full, color, px):
    """dark outline around a full-canvas mask"""
    big = mask_full.filter(ImageFilter.MaxFilter(2 * px + 1))
    ring = ImageChops.subtract(big, mask_full)
    layer = Image.new("RGBA", canvas.size, color + (255,))
    layer.putalpha(ring)
    canvas.alpha_composite(layer)


def shadow(canvas, mask_full, off, blur, alpha):
    s = mask_full.filter(ImageFilter.GaussianBlur(blur))
    s = s.point(lambda v: int(v * alpha))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 255))
    layer.putalpha(ImageChops.offset(s, off[0], off[1]))
    canvas.alpha_composite(layer)


def full_mask(draw_fn):
    m = Image.new("L", (W, W), 0)
    draw_fn(ImageDraw.Draw(m))
    return m


# ---------------------------------------------------------------- the icon
def build():
    head = head_cutout()
    head.save(os.path.join(OUT, "johnwave_head.png"))

    # head placement (final-pixel units, then * SS)
    HEAD_H = 500
    sc = HEAD_H / head.height
    hw, hh = int(head.width * sc * SS), int(head.height * sc * SS)
    head_big = head.resize((hw, hh), Image.LANCZOS)
    hx, hy = (W - hw) // 2, int(335 * SS)

    canvas = Image.new("RGBA", (W, W), (0, 0, 0, 0))

    # --- pineapple shell: the head silhouette grown into a fat egg
    hm = Image.new("L", (W, W), 0)
    hm.paste(head_big.getchannel("A"), (hx, hy))
    sh = np.asarray(hm, np.float32) / 255
    egg = ndi.gaussian_filter(ndi.maximum_filter(sh, size=int(112 * SS)), 40 * SS) > 0.5
    egg = ndi.binary_dilation(egg, iterations=1)
    # push the egg's bottom into a rounder grenade belly
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float32)
    cx, cy = W / 2, hy + hh * 0.52
    ell = (((xx - cx) / (hw * 0.60)) ** 2 + ((yy - cy) / (hh * 0.64)) ** 2) < 1
    shell = ndi.gaussian_filter((egg | ell).astype(np.float32), 6 * SS) > 0.5
    shell_m = Image.fromarray((shell * 255).astype(np.uint8), "L")

    # shading: distance from the edge -> bevel, plus a diagonal pineapple grid
    dist = ndi.distance_transform_edt(shell)
    bev = np.clip(dist / (46 * SS), 0, 1) ** 0.6
    base = np.array([74, 86, 40], np.float32)                 # olive drab
    light = np.array([138, 152, 74], np.float32)
    col = base[None, None] + (light - base)[None, None] * bev[..., None]
    # lighting from upper left
    lit = np.clip(1.15 - 0.55 * ((xx - W * 0.35) / W) - 0.5 * ((yy - W * 0.25) / W), 0.55, 1.2)
    col = col * lit[..., None]
    # diamond grooves
    P = 78 * SS
    u = (xx + yy) % P
    v = (xx - yy) % P
    gr = np.minimum(np.minimum(u, P - u), np.minimum(v, P - v))
    groove = np.clip(1 - gr / (5.5 * SS), 0, 1)
    col = col * (1 - 0.55 * groove[..., None])
    hi_ = np.clip(1 - np.abs(gr - 9 * SS) / (3.2 * SS), 0, 1) * 0.16
    col = col + hi_[..., None] * 255 * (lit[..., None] - 0.4)
    shell_layer = Image.fromarray(np.dstack([np.clip(col, 0, 255), np.full((W, W), 255)]).astype(np.uint8), "RGBA")
    shell_layer.putalpha(shell_m)

    shadow(canvas, shell_m, (0, 26 * SS), 22 * SS, 0.55)
    outline(canvas, shell_m, (22, 28, 12), 6 * SS)
    canvas.alpha_composite(shell_layer)

    # --- head on the shell: soft contact shadow then the cutout
    ha = Image.new("L", (W, W), 0)
    ha.paste(head_big.getchannel("A"), (hx, hy))
    shadow(canvas, ha, (6 * SS, 12 * SS), 10 * SS, 0.65)
    outline(canvas, ha, (30, 34, 16), 3 * SS)
    canvas.alpha_composite(head_big, (hx, hy), )

    # --- fuse assembly on top of the shell
    top = int(min(np.where(shell.any(axis=1))[0]))
    cxs = W // 2
    steel_d, steel_m, steel_l = (40, 44, 48), (110, 116, 120), (214, 220, 224)
    brass_d, brass_m, brass_l = (96, 62, 18), (176, 126, 40), (248, 214, 120)

    def put(cx_, y_, w_, h_, r_, arrs, ol=(14, 16, 18)):
        wm, hm_ = int(w_ * SS), int(h_ * SS)
        m = rrect_mask(wm, hm_, int(r_ * SS))
        x_, yb = int(cx_ * SS - wm / 2), int(y_ * SS)
        full = Image.new("L", (W, W), 0)
        full.paste(m, (x_, yb))
        shadow(canvas, full, (0, 6 * SS), 5 * SS, 0.5)
        outline(canvas, full, ol, 3 * SS)
        paste_shape(canvas, m, arrs(wm, hm_), (x_, yb))

    ft = top // SS                                              # shell top in final px
    # lever (spoon): from the fuse, bending over the right shoulder of the shell
    lev = Image.new("L", (W, W), 0)
    ld = ImageDraw.Draw(lev)
    pts = [(cxs / SS + 40, ft - 56), (cxs / SS + 120, ft - 50), (cxs / SS + 192, ft + 0), (cxs / SS + 236, ft + 100),
           (cxs / SS + 256, ft + 230), (cxs / SS + 258, ft + 330)]
    # smooth the polyline
    sm = []
    for i in range(len(pts) - 1):
        for t in np.linspace(0, 1, 24, endpoint=False):
            a_, b_ = np.array(pts[i]), np.array(pts[i + 1])
            sm.append(tuple((a_ * (1 - t) + b_ * t) * SS))
    sm.append(tuple(np.array(pts[-1]) * SS))
    for p in sm:
        r = 30 * SS
        ld.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=255)
    shadow(canvas, lev, (8 * SS, 12 * SS), 9 * SS, 0.6)
    outline(canvas, lev, (14, 16, 18), 4 * SS)
    # steel shading across the lever, light along its upper-left edge
    lev_arr = lin(W, W, steel_l, steel_d, vertical=False)
    lev_arr = lev_arr * 0.0 + lin(W, W, (150, 156, 160), (58, 62, 66), vertical=False)
    stripe = ndi.gaussian_filter(np.asarray(lev, np.float32) / 255, 18 * SS)
    ridge = np.clip((stripe - 0.35) * 2.2, 0, 1)
    lev_arr = lev_arr * (0.7 + 0.5 * ridge[..., None])
    paste_shape(canvas, lev, np.clip(lev_arr, 0, 255))
    # lever rivet
    rv = ImageDraw.Draw(canvas)
    p0 = (cxs / SS + 40, ft - 56)

    # collar + body of the fuse
    put(cxs / SS, ft - 46, 258, 64, 14, lambda w, h: cyl(w, h, steel_d, steel_m, steel_l, 0.3))
    put(cxs / SS, ft - 130, 188, 100, 20, lambda w, h: cyl(w, h, brass_d, brass_m, brass_l, 0.28))
    put(cxs / SS, ft - 160, 130, 44, 18, lambda w, h: cyl(w, h, steel_d, steel_m, steel_l, 0.3))
    # fuse groove lines on the brass
    d = ImageDraw.Draw(canvas)
    for k in range(3):
        yv = int((ft - 112 + k * 24) * SS)
        d.line((int((cxs / SS - 92) * SS), yv, int((cxs / SS + 92) * SS), yv), fill=(70, 44, 10, 150), width=2 * SS)

    # pull ring + pin through the fuse
    ring_c = (cxs / SS - 168, ft - 98)
    pin = Image.new("L", (W, W), 0)
    pd = ImageDraw.Draw(pin)
    pd.rounded_rectangle(((ring_c[0] + 40) * SS, (ring_c[1] - 9) * SS, (cxs / SS + 20) * SS, (ring_c[1] + 9) * SS),
                         9 * SS, fill=255)
    ring = Image.new("L", (W, W), 0)
    rd = ImageDraw.Draw(ring)
    R, T = 64, 17
    rd.ellipse(((ring_c[0] - R) * SS, (ring_c[1] - R * 0.92) * SS, (ring_c[0] + R) * SS, (ring_c[1] + R * 0.92) * SS),
               fill=255)
    rd.ellipse(((ring_c[0] - R + T) * SS, (ring_c[1] - R * 0.92 + T) * SS, (ring_c[0] + R - T) * SS,
                (ring_c[1] + R * 0.92 - T) * SS), fill=0)
    both = ImageChops.lighter(pin, ring)
    shadow(canvas, both, (6 * SS, 10 * SS), 6 * SS, 0.6)
    outline(canvas, both, (14, 16, 18), 3 * SS)
    ra = lin(W, W, (236, 240, 244), (90, 96, 102), vertical=True)
    paste_shape(canvas, both, ra)

    return canvas.resize((N, N), Image.LANCZOS)


def tile(icon):
    t = np.zeros((N, N, 3), np.float32)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    r = np.sqrt(((xx - N / 2) / (N * 0.62)) ** 2 + ((yy - N * 0.62) / (N * 0.62)) ** 2)
    glow = np.clip(1 - r, 0, 1) ** 1.8
    base = np.array([26, 24, 22], np.float32)
    warm = np.array([150, 70, 22], np.float32)
    t = base + warm * glow[..., None] * 0.85
    t *= (1 - 0.25 * (yy / N))[..., None]
    img = Image.fromarray(np.clip(t, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # a little scale-down so the sticker sits inside the tile
    ic = icon.resize((int(N * 0.9), int(N * 0.9)), Image.LANCZOS)
    img.alpha_composite(ic, ((N - ic.width) // 2, int(N * 0.06)))
    m = rrect_mask(N, N, 180)
    img.putalpha(m)
    return img


def main():
    icon = build()
    icon.save(os.path.join(OUT, "johnwave_grenade.png"))
    t = tile(icon)
    t.save(os.path.join(OUT, "johnwave_grenade_tile.png"))
    # legibility strip: the icon at game-ish sizes on dark and light grounds
    sizes = [256, 128, 64, 32]
    sheet = Image.new("RGB", (sum(sizes) + 40 * (len(sizes) + 1), 256 + 80), (40, 40, 44))
    x = 40
    for s in sizes:
        sheet.paste(t.resize((s, s), Image.LANCZOS), (x, 40), t.resize((s, s), Image.LANCZOS))
        x += s + 40
    sheet.save(os.path.join(OUT, "johnwave_sizes.png"))
    print("wrote icons to", OUT)


if __name__ == "__main__":
    main()
