#!/usr/bin/env python3
"""Look for trouble in the chain without looking at every pixel.

    python3 tools/qa.py            # a table: one row per drawing

For each drawing it reports
  * how hard the picture changes ALONG the cut where the inner drawing was set in, compared with how hard it
    changes a little to either side of the cut. About 1.0 means the cut is no busier than its surroundings,
    which is what an invisible join looks like to arithmetic. Well above 1 is worth looking at by eye.
  * the tones of its outer ring (darks, spread, saturation), to catch a chain that is slowly fading or
    burning from one drawing to the next.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain  # noqa: E402
import story  # noqa: E402

S, N, Q = chain.S, chain.N, chain.Q


def seam_score(k):
    mattes = sorted(glob.glob(os.path.join(chain.WORK, 'g%02d_c*_matte.png' % k)), key=os.path.getmtime)
    if not mattes:
        return None
    matte = np.asarray(Image.open(mattes[-1]).convert('L')).astype(np.float32) / 255
    img = np.asarray(Image.open(chain.gpath(k)).convert('L')).astype(np.float32)[Q:Q + N, Q:Q + N]
    grad = ndimage.gaussian_gradient_magnitude(img, 1.5)
    inside = matte > 0.5
    edge = inside ^ ndimage.binary_erosion(inside, iterations=3)
    on = ndimage.binary_dilation(edge, iterations=4)
    # the same band slid 14 px inward and 14 px outward (where that is still inside the square)
    inner = ndimage.binary_erosion(inside, iterations=18) ^ ndimage.binary_erosion(inside, iterations=26)
    outer = ndimage.binary_dilation(inside, iterations=22) ^ ndimage.binary_dilation(inside, iterations=14)
    ref = [grad[b].mean() for b in (inner, outer) if b.sum() > 500]
    if not ref or on.sum() < 500:
        return None
    return float(grad[on].mean() / np.mean(ref))


def ring_tones(k):
    a = np.asarray(Image.open(chain.gpath(k)).convert('RGB').resize((384, 384), Image.BOX)).astype(np.float32)
    n = a.shape[0]
    ring = np.ones((n, n), bool)
    ring[n // 4:n // 4 + n // 2, n // 4:n // 4 + n // 2] = False
    r = a[ring]
    lum = r[:, 0] * 0.299 + r[:, 1] * 0.587 + r[:, 2] * 0.114
    return float(np.percentile(lum, 3)), float(lum.std()), float((r.max(axis=1) - r.min(axis=1)).mean())


def main():
    print('  g  name             cut/nearby   darks(p3)  spread  saturation')
    for k, (name, _kind, _ring) in enumerate(story.STEPS):
        if not os.path.exists(chain.gpath(k)):
            continue
        s = seam_score(k) if k else None
        d, sp, sat = ring_tones(k)
        flag = '  <-- look' if s and s > 1.2 else ''
        print(' %2d  %-15s  %s      %6.1f   %6.1f   %6.1f%s' % (k, name, ' %.2f ' % s if s else '  -   ', d, sp, sat, flag))


if __name__ == '__main__':
    main()
