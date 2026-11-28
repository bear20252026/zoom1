"""Join the kept picture to the model's redraw of it along the quietest path.

After `register.pull_back` the model's picture V lies over the original U to within a couple of
pixels, but the two still disagree wherever the model let something new (a rabbit's ears, the
corner of a desk) reach into the square it was told to keep. A straight cut along the square's
edge would slice those things in half, so instead the cut wanders: inside a band along the edge it
follows the closed path on which U and V differ least (dynamic programming over the band unrolled
into a strip). Outside the path the model's version wins, inside it the original does.

The same matte is then applied to the original at full size (`reconcile`), so that the inner
picture's own rim shows exactly what the outer picture shows there, and the middle half of the outer
picture is, to the pixel, the inner picture at half size.
"""
import numpy as np
from PIL import Image
from scipy import ndimage


def _f(img):
    return np.asarray(img.convert('RGB')).astype(np.float32)


def shift(v_full, v_mid, u_mid, limit=24.0, grid=16):
    """Undo the one thing the model does to tone: it returns the picture it was given a few levels lighter.

    Measured where both versions exist (the kept square): the difference of mean colour over big blocks, the
    median of those, per channel. Applied to the whole of the model's picture as a plain shift, on the
    reasoning that it painted the new part in the same key as it redrew the old. Contrast is deliberately
    not fitted: any fit of contrast has an error, and over a chain of pictures each built on the last a small
    error in contrast compounds into fog or burn (see the record in tone_match).
    """
    a, b = _f(v_mid), _f(u_mid)
    n = a.shape[0] // grid
    blocks = lambda z: z[:n * grid, :n * grid].reshape(grid, n, grid, n, 3).mean(axis=(1, 3))
    d = (blocks(b) - blocks(a)).reshape(-1, 3)
    keep = np.abs(d).mean(axis=1) < max(3 * float(np.median(np.abs(d).mean(axis=1))), 6.0)   # not what it repainted
    off = np.clip(np.median(d[keep], axis=0), -limit, limit)
    out = _f(v_full) + off
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)), [round(float(v), 1) for v in off]


def tone_match(v_full, v_mid, u_mid, origin, lo=0.8, hi=1.25, grid=16):
    """The last small difference at the join: fitted on the kept square, applied in full there, and let go
    of smoothly toward the picture's edge, so that by the edge the tones are the anchored ones again and
    nothing is handed on to the next drawing.

    The fit is deliberately coarse: mean colours of big blocks of the redraw against the same blocks of the
    original (strokes average out of a block, so re-hatching cannot bias it), one gain for all three
    channels, blocks the model repainted left out, and only the outer part of the kept square used.
    """
    a, b = _f(v_mid), _f(u_mid)
    n = a.shape[0] // grid
    blocks = lambda z: z[:n * grid, :n * grid].reshape(grid, n, grid, n, 3).mean(axis=(1, 3))
    x, y = blocks(a), blocks(b)
    c = (grid - 1) / 2.0
    gy, gx = np.mgrid[0:grid, 0:grid]
    outer = (np.maximum(np.abs(gx - c), np.abs(gy - c)) / (grid / 2.0)) > 0.5
    x, y = x[outer], y[outer]
    keep = np.ones(len(x), bool)
    g, o = 1.0, np.zeros(3)
    for _ in range(5):
        xm, ym = x[keep].mean(axis=0), y[keep].mean(axis=0)
        var = ((x[keep] - xm) ** 2).sum()
        if var < 1e-3:
            break
        g = float(np.clip(((x[keep] - xm) * (y[keep] - ym)).sum() / var, lo, hi))
        o = ym - g * xm
        res = np.abs(y - (g * x + o)).mean(axis=1)
        keep = res < max(2.5 * float(np.median(res)), 4.0)
        if keep.sum() < 24:
            keep[:] = True
            break
    full = _f(v_full)
    size = full.shape[0]
    half = a.shape[0] / 2.0
    cx, cy = origin[0] + half - 0.5, origin[1] + half - 0.5
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.maximum(np.abs(xx - cx), np.abs(yy - cy)) / half          # 1 at the square's edge, 2 at the picture's
    t = np.clip((r - 1.0) / 0.9, 0, 1)
    w = (1 - t * t * (3 - 2 * t))[..., None]
    out = full + w * (full * g + o - full)
    report = [round(g, 3)] + [round(float(v), 1) for v in o] + [int(keep.sum()), int(len(keep))]
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)), report


def seam_matte(u_mid, v_mid, band=0.15, dmin=8, pull=0.03, turn=0.004, soft=5.0):
    """Matte over the kept square (same size as u_mid): 1 where the original is used, 0 where the redraw is.

    band: how far in from the edge the cut may wander, as a fraction of the square's side.
    pull: cost per unit of depth (full band = `pull`), so the cut stays near the edge unless it has reason not to.
    """
    n = u_mid.width
    k = 2                                         # work at half size
    m = n // k
    u = _f(u_mid.resize((m, m), Image.BOX))
    v = _f(v_mid.resize((m, m), Image.BOX))
    # disagreement of CONTENT, not of individual pen strokes: the redraw re-hatches everything a pixel or two
    # off, so compare the two pictures a little out of focus, plus the shapes only one of them has
    ub, vb = ndimage.gaussian_filter(u, (4, 4, 0)), ndimage.gaussian_filter(v, (4, 4, 0))
    diff = np.abs(ub - vb).mean(axis=2) / 255.0
    gu = ndimage.gaussian_gradient_magnitude(u.mean(axis=2), 5) / 255.0
    gv = ndimage.gaussian_gradient_magnitude(v.mean(axis=2), 5) / 255.0
    cost_img = ndimage.gaussian_filter(diff, 2) + 3.0 * ndimage.gaussian_filter(np.abs(gu - gv), 3)

    depth_n = int(band * m)
    d0 = max(1, dmin // k)
    N = 4 * m
    c = (m - 1) / 2.0
    i = np.arange(N)
    side = i // m
    frac = (i % m + 0.5) / m
    strip = np.empty((N, depth_n), np.float32)
    for j in range(depth_n):
        r = c - (d0 + j)
        a = -r + 2 * r * frac
        x = np.where(side == 0, c + a, np.where(side == 1, c + r, np.where(side == 2, c - a, c - r)))
        y = np.where(side == 0, c - r, np.where(side == 1, c + a, np.where(side == 2, c + r, c - a)))
        strip[:, j] = ndimage.map_coordinates(cost_img, [y, x], order=1, mode='nearest')
    strip += pull * (np.arange(depth_n, dtype=np.float32) / depth_n)[None, :]

    # cheapest closed path: two laps, keep the middle lap
    reach = 2
    lap = np.concatenate([strip, strip], axis=0)
    acc = np.empty_like(lap)
    back = np.zeros(lap.shape, np.int16)
    acc[0] = lap[0]
    pad = np.full(reach, np.inf, np.float32)
    for t in range(1, len(lap)):
        prev = np.concatenate([pad, acc[t - 1], pad])
        stack = np.stack([prev[s:s + depth_n] + turn * abs(s - reach) for s in range(2 * reach + 1)])
        best = stack.argmin(axis=0)
        acc[t] = lap[t] + stack[best, np.arange(depth_n)]
        back[t] = best - reach
    path = np.empty(len(lap), np.int32)
    path[-1] = int(acc[-1].argmin())
    for t in range(len(lap) - 1, 0, -1):
        path[t - 1] = path[t] + back[t, path[t]]
    path = np.roll(path[N // 2:N // 2 + N], N // 2).astype(np.float32)
    path = ndimage.uniform_filter1d(path, 9, mode='wrap')
    seam_depth = (d0 + path) * k                  # px, at the square's own size

    # rasterise: a pixel belongs to the original when it lies deeper than the path at its place on the lap
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    cn = (n - 1) / 2.0
    dx, dy = xx - cn, yy - cn
    r = np.maximum(np.abs(dx), np.abs(dy))
    depth = cn - r
    rr = np.maximum(r, 1e-3)
    top, right, bottom = (dy <= -np.abs(dx)), (dx >= np.abs(dy)), (dy >= np.abs(dx))
    lapf = np.where(top, (dx / rr + 1) / 2,
                    np.where(right, 1 + (dy / rr + 1) / 2,
                             np.where(bottom, 2 + (-dx / rr + 1) / 2, 3 + (-dy / rr + 1) / 2)))
    idx = np.clip(lapf * m, 0, N - 1e-3)
    i0 = np.floor(idx).astype(np.int32) % N
    i1 = (i0 + 1) % N
    w = idx - np.floor(idx)
    sd = seam_depth[i0] * (1 - w) + seam_depth[i1] * w
    matte = (depth > sd).astype(np.float32)
    matte = ndimage.gaussian_filter(matte, soft)
    matte[depth < 1.0] = 0.0
    stats = {'seam_mean_px': float(seam_depth.mean()), 'seam_max_px': float(seam_depth.max()),
             'cost_on_seam': float(np.mean([strip[t, int(round(p))] for t, p in enumerate(path)])),
             'cost_at_edge': float(strip[:, 0].mean())}
    return matte, stats


def compose(v_full, u_mid, matte, origin):
    """The outer picture: the redraw, with the original set into its middle along the matte."""
    o = _f(v_full)
    x, y = origin
    n = u_mid.width
    a = matte[..., None]
    o[y:y + n, x:x + n] = o[y:y + n, x:x + n] * (1 - a) + _f(u_mid) * a
    return Image.fromarray(np.clip(o + 0.5, 0, 255).astype(np.uint8))


def reconcile(inner_full, v_mid, matte):
    """The inner picture with its rim replaced by the outer picture's version of it (twice enlarged)."""
    size = inner_full.width
    up = _f(v_mid.resize((size, size), Image.BICUBIC))
    m = np.asarray(Image.fromarray((matte * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)).astype(np.float32) / 255.0
    m = m[..., None]
    out = _f(inner_full) * m + up * (1 - m)
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))
