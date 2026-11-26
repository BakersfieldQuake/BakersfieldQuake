"""Frame tools for the THE DISK viewmodel: optical-flow in-betweens and pose-to-pose morphs on keyed RGBA frames.
OpenCV + NumPy only."""
import cv2
import numpy as np


def _gray(rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    comp = rgba[..., :3].astype(np.float32) * a + 128.0 * (1.0 - a)
    return cv2.cvtColor(comp.astype(np.uint8), cv2.COLOR_RGB2GRAY)


def _premul(rgba):
    f = rgba.astype(np.float32)
    return np.dstack([f[..., :3] * (f[..., 3:4] / 255.0), f[..., 3:4]])


def _unpremul(pm, sharpen=True):
    alpha = np.clip(pm[..., 3], 0.0, 255.0)
    rgb = np.clip(pm[..., :3] / np.maximum(alpha[..., None] / 255.0, 1e-4), 0.0, 255.0)
    if sharpen:
        # keep silhouettes crisp: a warped blend must not split into two faint ghosts
        a = np.clip((alpha - 96.0) * (255.0 / 64.0), 0.0, 255.0)
        alpha = np.where(alpha > 250, alpha, np.minimum(alpha * 1.15, a + alpha * 0.25))
    a8 = np.clip(np.round(alpha), 0, 255).astype(np.uint8)
    c8 = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    c8[a8 == 0] = 0
    return np.dstack([c8, a8])


def flow_interp(rgba0, rgba1, t, sharpen=True):
    """Frame between rgba0 (t=0) and rgba1 (t=1), symmetric Farneback flow, premultiplied warps."""
    if t <= 1e-4:
        return rgba0.copy()
    if t >= 1.0 - 1e-4:
        return rgba1.copy()
    g0, g1 = _gray(rgba0), _gray(rgba1)
    f01 = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 5, 25, 4, 7, 1.5, 0)
    f10 = cv2.calcOpticalFlowFarneback(g1, g0, None, 0.5, 5, 25, 4, 7, 1.5, 0)
    h, w = g0.shape
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    vx = 0.5 * (f01[..., 0] - f10[..., 0])
    vy = 0.5 * (f01[..., 1] - f10[..., 1])
    mvx = cv2.remap(vx, gx - (t - 0.5) * vx, gy - (t - 0.5) * vy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mvy = cv2.remap(vy, gx - (t - 0.5) * vx, gy - (t - 0.5) * vy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    p0, p1 = _premul(rgba0), _premul(rgba1)
    w0 = cv2.remap(p0, gx - t * mvx, gy - t * mvy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    w1 = cv2.remap(p1, gx + (1 - t) * mvx, gy + (1 - t) * mvy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return _unpremul((1.0 - t) * w0 + t * w1, sharpen)


def _affine_between(a, b):
    """2x3 affine taking frame a's silhouette onto frame b's (ECC on blurred alpha, at quarter size)."""
    s = 0.25
    aa = cv2.GaussianBlur(cv2.resize(a[..., 3], None, fx=s, fy=s, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0, (0, 0), 2.0)
    bb = cv2.GaussianBlur(cv2.resize(b[..., 3], None, fx=s, fy=s, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0, (0, 0), 2.0)
    # start from the centroid shift
    ma, mb = cv2.moments(aa), cv2.moments(bb)
    warp = np.eye(2, 3, dtype=np.float32)
    if ma["m00"] > 1 and mb["m00"] > 1:
        warp[0, 2] = mb["m10"] / mb["m00"] - ma["m10"] / ma["m00"]
        warp[1, 2] = mb["m01"] / mb["m00"] - ma["m01"] / ma["m00"]
    try:
        # findTransformECC(template, input): warp maps template coords onto input coords. We want a -> b, so b is
        # the template... keep it simple and solve b <- a, then invert.
        _, wm = cv2.findTransformECC(bb, aa, cv2.invertAffineTransform(warp), cv2.MOTION_AFFINE,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), None, 5)
        warp = cv2.invertAffineTransform(wm)
    except cv2.error:
        pass
    warp[:, 2] /= s
    return warp


def _lerp_affine(m, t):
    eye = np.eye(2, 3, dtype=np.float32)
    return eye + (m - eye) * t


def morph(a, b, n, ease=True):
    """n in-between frames carrying pose a onto pose b (exclusive of both ends): a global affine glide plus flow for
    the rest, so a hand that has drifted bigger/higher settles back instead of cross-fading."""
    h, w = a.shape[:2]
    m = _affine_between(a, b)
    minv = cv2.invertAffineTransform(m)
    out = []
    for k in range(1, n + 1):
        t = k / (n + 1.0)
        if ease:
            t = t * t * (3 - 2 * t)
        wa = cv2.warpAffine(_premul(a), _lerp_affine(m, t), (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        wb = cv2.warpAffine(_premul(b), _lerp_affine(minv, 1.0 - t), (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        out.append(flow_interp(_unpremul(wa, False), _unpremul(wb, False), t))
    return out


def resample(frames, positions):
    """frames: list of RGBA (index = source frame order); positions: float indices into it."""
    out = []
    n = len(frames)
    for p in positions:
        p = float(np.clip(p, 0.0, n - 1))
        i0 = int(np.floor(p))
        i1 = min(i0 + 1, n - 1)
        out.append(flow_interp(frames[i0], frames[i1], p - i0) if p - i0 > 1e-3 else frames[i0].copy())
    return out


def ease_positions(a, b, n, power_in=1.0, power_out=1.0):
    """n positions from a to b (inclusive). power_in > 1: slow start; power_out > 1: slow end."""
    u = np.linspace(0.0, 1.0, n)
    if power_in != 1.0 or power_out != 1.0:
        # blend of ease-in and ease-out curves
        ein = u ** power_in
        eout = 1.0 - (1.0 - u) ** power_out
        u = ein * (1.0 - u) + eout * u
    return a + (b - a) * u


def motion_blur(rgba, dx, dy, taps=5):
    """Linear motion blur along (dx, dy) pixels, premultiplied (for synthetic whips)."""
    pm = _premul(rgba)
    acc = np.zeros_like(pm)
    h, w = rgba.shape[:2]
    for k in range(taps):
        f = (k / (taps - 1.0)) - 0.5
        mtx = np.float32([[1, 0, dx * f], [0, 1, dy * f]])
        acc += cv2.warpAffine(pm, mtx, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return _unpremul(acc / taps, False)


def smear(a, b, n):
    """n in-betweens from pose a to pose b for poses too different for optical flow (flow would double-expose):
    both frames glide along the affine between them with a directional motion blur that peaks mid-way, and swap
    over the middle third, the way a hand-drawn smear frame hides a pose change."""
    h, w = a.shape[:2]
    m = _affine_between(a, b)
    minv = cv2.invertAffineTransform(m)
    ma, mb = cv2.moments(a[..., 3].astype(np.float32)), cv2.moments(b[..., 3].astype(np.float32))
    if ma["m00"] > 1 and mb["m00"] > 1:
        dx = mb["m10"] / mb["m00"] - ma["m10"] / ma["m00"]
        dy = mb["m01"] / mb["m00"] - ma["m01"] / ma["m00"]
    else:
        dx = dy = 0.0
    dist = max(30.0, float(np.hypot(dx, dy)))
    ux, uy = (dx / dist, dy / dist) if np.hypot(dx, dy) > 1 else (0.6, -0.8)
    out = []
    for k in range(1, n + 1):
        t = k / (n + 1.0)
        te = t * t * (3 - 2 * t)
        wa = cv2.warpAffine(_premul(a), _lerp_affine(m, te), (w, h), flags=cv2.INTER_LINEAR)
        wb = cv2.warpAffine(_premul(b), _lerp_affine(minv, 1.0 - te), (w, h), flags=cv2.INTER_LINEAR)
        mix = float(np.clip((t - 0.40) / 0.20, 0.0, 1.0))
        mix = mix * mix * (3 - 2 * mix)
        pm = (1.0 - mix) * wa + mix * wb
        blur = (0.55 * dist / (n + 1.0)) * (0.35 + np.sin(np.pi * t))
        taps = 7
        acc = np.zeros_like(pm)
        for j in range(taps):
            f = (j / (taps - 1.0) - 0.5) * blur
            acc += cv2.warpAffine(pm, np.float32([[1, 0, ux * f], [0, 1, uy * f]]), (w, h), flags=cv2.INTER_LINEAR)
        out.append(_unpremul(acc / taps, False))
    return out


def whip(a, n, dx, dy, rot, pivot):
    """n synthetic follow-through frames: frame a flung by (dx, dy) px and rot degrees (cv2 sense: + is
    counter-clockwise) about pivot, fast first then easing, with motion blur matched to each frame's travel."""
    h, w = a.shape[:2]
    pm = _premul(a)
    out = []
    prev = None
    for k in range(1, n + 1):
        u = k / float(n)
        e = 1.0 - (1.0 - u) ** 2.2
        acc = np.zeros_like(pm)
        taps = 7
        e0 = 1.0 - (1.0 - (k - 1) / float(n)) ** 2.2
        for j in range(taps):
            ee = e0 + (e - e0) * j / (taps - 1.0)
            mtx = cv2.getRotationMatrix2D(pivot, rot * ee, 1.0)
            mtx[0, 2] += dx * ee
            mtx[1, 2] += dy * ee
            acc += cv2.warpAffine(pm, mtx, (w, h), flags=cv2.INTER_LINEAR)
        out.append(_unpremul(acc / taps, False))
    return out
