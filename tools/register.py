"""Find where the model put the picture it was asked to keep.

The image model redraws the kept middle faithfully but not in place: it comes back shifted and
slightly stretched. `locate` measures that (patch by patch, coarse then fine) and returns a smooth
map from canvas coordinates to coordinates in the model's output, so the output can be pulled back
until its middle lies exactly under the original.
"""
import numpy as np
from PIL import Image
from scipy import ndimage, signal


def _gray(img):
    return np.asarray(img.convert('L')).astype(np.float32)


def _highpass(a, sigma):
    return a - ndimage.gaussian_filter(a, sigma)


def _ncc(tpl, win):
    """Normalised cross-correlation of tpl (p x p) inside win ((p+2R) x (p+2R)); returns (2R+1)^2 map."""
    p = tpl.shape[0]
    t = tpl - tpl.mean()
    tn = np.sqrt((t * t).sum())
    if tn < 1e-3:
        return None
    num = signal.fftconvolve(win, t[::-1, ::-1], mode='valid')
    ones = np.ones((p, p), np.float32)
    s1 = signal.fftconvolve(win, ones, mode='valid')
    s2 = signal.fftconvolve(win * win, ones, mode='valid')
    den = np.sqrt(np.maximum(s2 - s1 * s1 / (p * p), 1e-6)) * tn
    return num / den


def _peak(c):
    iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
    sy = sx = 0.0
    if 0 < iy < c.shape[0] - 1:
        a, b, d = c[iy - 1, ix], c[iy, ix], c[iy + 1, ix]
        den = a - 2 * b + d
        if abs(den) > 1e-9:
            sy = 0.5 * (a - d) / den
    if 0 < ix < c.shape[1] - 1:
        a, b, d = c[iy, ix - 1], c[iy, ix], c[iy, ix + 1]
        den = a - 2 * b + d
        if abs(den) > 1e-9:
            sx = 0.5 * (a - d) / den
    return iy + float(np.clip(sy, -1, 1)), ix + float(np.clip(sx, -1, 1)), float(c[iy, ix])


def _basis(x, y, order, scale):
    """Polynomial terms of (x, y) up to `order`, coordinates normalised by `scale`."""
    u, v = x / scale, y / scale
    cols = [np.ones_like(u)]
    for n in range(1, order + 1):
        for i in range(n + 1):
            cols.append(u ** (n - i) * v ** i)
    return np.stack(cols, axis=-1)


class Map:
    """canvas (x, y) -> model-output (x, y).

    An affine part that holds everywhere, plus a small polynomial correction that is trusted only
    where it was measured (inside the kept square) and fades to nothing a little way outside it.
    """

    def __init__(self, cx, cy, scale, affine_x, affine_y, order=0, coef_x=None, coef_y=None, limit=14.0):
        self.cx, self.cy, self.scale = cx, cy, scale
        self.affine_x, self.affine_y = affine_x, affine_y
        self.order, self.coef_x, self.coef_y, self.limit = order, coef_x, coef_y, limit

    def __call__(self, x, y):
        x = np.asarray(x, np.float64) - self.cx
        y = np.asarray(y, np.float64) - self.cy
        b1 = _basis(x, y, 1, self.scale)
        with np.errstate(all='ignore'):
            ox, oy = b1 @ self.affine_x, b1 @ self.affine_y
            if self.order > 1:
                half = self.scale / 2.0
                out = np.maximum(np.maximum(np.abs(x), np.abs(y)) - half, 0) / (0.3 * self.scale)
                t = np.clip(1 - out, 0, 1)
                w = t * t * (3 - 2 * t)
                bn = _basis(np.clip(x, -1.3 * half, 1.3 * half), np.clip(y, -1.3 * half, 1.3 * half), self.order, self.scale)
                ox = ox + w * np.clip(bn @ self.coef_x, -self.limit, self.limit)
                oy = oy + w * np.clip(bn @ self.coef_y, -self.limit, self.limit)
        return ox, oy


def _lstsq(b, q, w):
    sw = np.sqrt(w)[:, None]
    with np.errstate(all='ignore'):
        return np.linalg.lstsq(b * sw, q * sw[:, 0], rcond=None)[0]


def _fit(px, py, qx, qy, w, cx, cy, scale, order):
    x, y = px - cx, py - cy
    b1 = _basis(x, y, 1, scale)
    keep = w > 0
    m = None
    res = np.zeros(len(px))
    for _ in range(6):
        ww = w * keep
        ax, ay = _lstsq(b1, qx, ww), _lstsq(b1, qy, ww)
        m = Map(cx, cy, scale, ax, ay)
        if order > 1:
            with np.errstate(all='ignore'):
                rx, ry = qx - b1 @ ax, qy - b1 @ ay
            bn = _basis(x, y, order, scale)
            m = Map(cx, cy, scale, ax, ay, order, _lstsq(bn, rx, ww), _lstsq(bn, ry, ww))
        gx, gy = m(px, py)
        res = np.hypot(gx - qx, gy - qy)
        med = np.median(res[keep]) if keep.any() else 0
        new = (w > 0) & (res < max(3.0 * med, 1.5))
        if new.sum() < 30 or (new == keep).all():
            break
        keep = new
    return m, res, keep


def _match(tpl_img, big_img, pts, p, radius, predict):
    """For each point (canvas coords of a patch centre) find it in big_img near predict(point)."""
    out = []
    H, W = big_img.shape
    for (x, y, tx, ty) in pts:           # (canvas x, canvas y, template x, template y)
        t = tpl_img[int(ty - p // 2):int(ty - p // 2) + p, int(tx - p // 2):int(tx - p // 2) + p]
        if t.shape != (p, p):
            continue
        gx, gy = predict(x, y)
        x0, y0 = int(round(gx)) - p // 2 - radius, int(round(gy)) - p // 2 - radius
        if x0 < 0 or y0 < 0 or x0 + p + 2 * radius > W or y0 + p + 2 * radius > H:
            continue
        c = _ncc(t, big_img[y0:y0 + p + 2 * radius, x0:x0 + p + 2 * radius])
        if c is None:
            continue
        iy, ix, score = _peak(c)
        out.append((x, y, x0 + ix + p / 2.0, y0 + iy + p / 2.0, score))
    return np.array(out, np.float64).reshape(-1, 5)


class Chain:
    """Two maps one after the other: canvas -> (roughly aligned) -> model output."""

    def __init__(self, first, then):
        self.first, self.then = first, then

    def __call__(self, x, y):
        x1, y1 = self.first(x, y)
        return self.then(x1, y1)


def _coarse(inner_small, raw, origin, f, p, radius, grid, predict, floor):
    """Shift-and-stretch estimate from pictures shrunk by f."""
    n = inner_small.width
    ox, oy = origin
    a = _highpass(_gray(inner_small.resize((n // f, n // f), Image.BOX)), 3)
    b = _highpass(_gray(raw.resize((raw.width // f, raw.height // f), Image.BOX)), 3)
    g = np.linspace(p, n // f - p, grid)
    pts = [((ox / f + tx), (oy / f + ty), tx, ty) for ty in g for tx in g]
    m = _match(a, b, pts, p, radius, lambda x, y: tuple(v / f for v in predict(x * f, y * f)))
    if len(m) < 8:
        return None, 0
    good = m[:, 4] > floor
    if good.sum() < 8:
        return None, int(good.sum())
    fit, res, keep = _fit(m[:, 0] * f, m[:, 1] * f, m[:, 2] * f, m[:, 3] * f, np.where(good, m[:, 4] ** 2, 0),
                          ox + n / 2.0, oy + n / 2.0, n, 1)
    return fit, int(keep.sum())


def locate(inner_small, raw, origin, order=3, verbose=True):
    """inner_small: the kept picture as pasted (n x n); raw: the model's output; origin: (x, y) of the paste.

    Returns (map, report). The map takes canvas coordinates to raw coordinates.

    Three looks, each closer: an eighth size over a wide area (the model may have moved the picture a long
    way), a quarter size near that guess, and then full size AFTER undoing that guess, so the fine patches
    are compared at the same scale (a 10% stretch is enough to defeat a patch match on hatching).
    """
    n = inner_small.width
    ox, oy = origin
    cx, cy = ox + n / 2.0, oy + n / 2.0
    ident = lambda x, y: (x, y)
    far, k0 = _coarse(inner_small, raw, origin, 8, 24, min(60, ox // 8 - 2), 9, ident, 0.3)
    near, k1 = _coarse(inner_small, raw, origin, 4, 40, 26 if far else min(64, ox // 4 - 2), 11, far or ident, 0.35)
    if near is None:
        near, k1 = far, k0
    if near is None:
        raise RuntimeError('registration failed: the kept picture was not found in the output')

    # undo the rough map over the square (plus a margin), then measure what is left at full size
    pad = 64
    rough, _ = pull_back(raw, near, n + 2 * pad, (ox - pad, oy - pad))
    a_full = _highpass(_gray(inner_small), 6)
    b_full = _highpass(_gray(rough), 6)
    p = 96
    g = np.linspace(p // 2 + 4, n - p // 2 - 4, 22)
    pts = [(ox + tx, oy + ty, tx, ty) for ty in g for tx in g]
    shift = lambda x, y: (x - (ox - pad), y - (oy - pad))          # canvas -> the rough picture's own pixels
    fine, res, keep, m = None, None, None, None
    for radius, floor in ((30, 0.5), (10, 0.5)):
        guess = (lambda x, y: shift(*fine(x, y))) if fine else shift
        m = _match(a_full, b_full, pts, p, radius, guess)
        if len(m) < 12:
            break
        w = np.where(m[:, 4] > floor, m[:, 4] ** 2, 0)
        if (w > 0).sum() < 12:
            w = np.where(m[:, 4] > 0.3, m[:, 4] ** 2, 0)
        fine, res, keep = _fit(m[:, 0], m[:, 1], m[:, 2] + (ox - pad), m[:, 3] + (oy - pad), w, cx, cy, n, order)
    if fine is None or keep is None or keep.sum() < 12:
        mapping = near
        report = {'matches': k1, 'of': 121, 'rms': -1.0, 'p95': -1.0, 'score': 0.0, 'coarse_only': True}
    else:
        mapping = Chain(fine, near)
        report = {'matches': int(keep.sum()), 'of': int(len(m)),
                  'rms': float(np.sqrt((res[keep] ** 2).mean())), 'p95': float(np.percentile(res[keep], 95)),
                  'score': float(np.median(m[keep, 4]))}
    report['shift'] = (float(near.affine_x[0] - cx), float(near.affine_y[0] - cy))
    report['scale'] = (float(near.affine_x[1] / n), float(near.affine_y[2] / n))
    if verbose:
        print('  register: %(matches)d/%(of)d patches, rms %(rms).2f px (p95 %(p95).2f), median ncc %(score).2f' % report)
        print('            shift (%.1f, %.1f) px, scale (%.4f, %.4f)' % (report['shift'] + report['scale']))
    return mapping, report


def pull_back(raw, mapping, size, window):
    """Resample the model's output into canvas coordinates. window = (x0, y0) of the size x size crop wanted.

    Returns (image, coverage) where coverage is the fraction of the crop the output actually covered.
    """
    x0, y0 = window
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float64)
    sx, sy = mapping(xs + x0, ys + y0)
    a = np.asarray(raw.convert('RGB')).astype(np.float32)
    inside = (sx >= 0) & (sx <= raw.width - 1) & (sy >= 0) & (sy <= raw.height - 1)
    out = np.empty((size, size, 3), np.float32)
    for c in range(3):
        out[..., c] = ndimage.map_coordinates(a[..., c], [sy, sx], order=3, mode='mirror')   # a thin uncovered rim is mirrored, not smeared
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)), float(inside.mean())
