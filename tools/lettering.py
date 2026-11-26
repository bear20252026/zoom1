#!/usr/bin/env python3
"""The lettering: a sheet of brush lettering from the image model, cut into lines.

    python3 tools/lettering.py make       # ask for the sheets (masters/letters/sheet_*.png)
    python3 tools/lettering.py cut        # slice them into art/letters/*.png (white ink on transparent)

Each sheet is one line of writing per row with wide gaps, so rows can be found by how much ink each
pixel row holds. The pieces are saved as alpha only; the page colours them with CSS masks.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fal  # noqa: E402

ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'masters', 'letters')
OUT = os.path.join(ROOT, 'art', 'letters')

HAND = (
    "A sheet of pure white paper with brush lettering on it and nothing else. The lettering is painted with a "
    "round brush in opaque deep bottle-green gouache: warm, confident, slightly quirky upright letters, the hand of "
    "a painter titling a picture book, separate letters (not joined-up script), lower case with capitals where "
    "shown, strokes that swell and taper a little with the pressure of the brush, even in size. Write EXACTLY the "
    "following lines, one line per row, in this order, each on a single row, left aligned, all the same size, with "
    "very wide empty gaps between the rows (at least twice the height of the lettering). Spell every word exactly "
    "as given and add nothing else: no numbering, no bullets, no underlines, no ruled lines, no decorations, no "
    "border, no paper texture, no shadow. The background is flat pure white.\n\nThe lines:\n"
)

# One sheet: the title card is the only writing on the page.
SHEETS = {
    'title': {'size': (2048, 1536), 'rows': [
        ('title', 'Day In, Day In'),
        ('sub', 'a painting with no bottom'),
        ('hint_scroll', 'scroll to walk in'),
    ]},
}


def make(only=None):
    os.makedirs(SRC, exist_ok=True)
    for name, sh in SHEETS.items():
        if only and name not in only:
            continue
        lines = '\n'.join('%d. %s' % (i + 1, t) for i, (_, t) in enumerate(sh['rows']))
        prompt = HAND + lines + '\n\n(The numbers before the lines are only for you; do not write them.)' + sh.get('note', '')
        w, h = sh['size']
        base = {'prompt': prompt, 'image_size': {'width': w, 'height': h}, 'quality': 'high', 'num_images': 1,
                'output_format': 'png', 'background': 'opaque'}
        path = os.path.join(SRC, 'sheet_%s.png' % name)
        out = fal.run(fal.T2I, base, label='letters ' + name)
        fal.download(out['images'][0]['url'], path)
        print('wrote', path)


def ink(img):
    """How much ink at each pixel, 0..1 (blue pen on white)."""
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255.0
    white = np.percentile(a.reshape(-1, 3), 90, axis=0)
    dark = 1.0 - np.min(a / np.maximum(white, 1e-3), axis=2)
    return np.clip((dark - 0.08) / 0.55, 0, 1)


def runs(profile, thresh, gap):
    """Stretches of a 1-D ink profile above thresh, merging gaps shorter than `gap`."""
    on = profile > thresh
    out, start, last = [], None, None
    for i, v in enumerate(on):
        if v:
            if start is None:
                start = i
            elif i - last > gap:
                out.append((start, last + 1))
                start = i
            last = i
    if start is not None:
        out.append((start, last + 1))
    return out


def save_alpha(a, path, pad=14):
    ys, xs = np.where(a > 0.1)
    if len(xs) == 0:
        raise RuntimeError('empty piece ' + path)
    y0, y1, x0, x1 = max(ys.min() - pad, 0), min(ys.max() + pad, a.shape[0]), max(xs.min() - pad, 0), min(xs.max() + pad, a.shape[1])
    cut = (np.clip(a[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8)
    rgba = np.dstack([np.full_like(cut, 255)] * 3 + [cut])
    Image.fromarray(rgba, 'RGBA').save(path, optimize=True)
    return cut.shape[1], cut.shape[0]


def cut():
    os.makedirs(OUT, exist_ok=True)
    index = {}
    for name, sh in SHEETS.items():
        path = os.path.join(SRC, 'sheet_%s.png' % name)
        if not os.path.exists(path):
            print('missing', path)
            continue
        a = ink(Image.open(path))
        rows = runs(ndimage.uniform_filter1d(a.sum(axis=1), 5), 2.5, int(a.shape[0] * 0.012))
        rows = [r for r in rows if r[1] - r[0] > a.shape[0] * 0.012]
        want = sh['rows']
        status = 'ok' if len(rows) == len(want) else 'MISMATCH (found %d rows, wanted %d)' % (len(rows), len(want))
        print('%s: %s' % (name, status))
        for (key, text), (y0, y1) in zip(want, rows):
            if key is None:
                continue
            band = a[max(y0 - 10, 0):y1 + 10]
            if key == 'digits':
                cols = runs(ndimage.uniform_filter1d(band.sum(axis=0), 3), 1.0, int(a.shape[1] * 0.012))
                cols = [c for c in cols if c[1] - c[0] > 6]
                print('   digits: found %d' % len(cols))
                for d, (x0, x1) in enumerate(cols[:10]):
                    w, h = save_alpha(band[:, max(x0 - 6, 0):x1 + 6], os.path.join(OUT, 'd%d.png' % d), pad=8)
                    index['d%d' % d] = {'w': w, 'h': h}
            else:
                w, h = save_alpha(band, os.path.join(OUT, key + '.png'))
                index[key] = {'w': w, 'h': h, 'text': text}
    with open(os.path.join(OUT, 'index.json'), 'w') as f:
        json.dump(index, f, indent=1)
    print('wrote', len(index), 'pieces')


if __name__ == '__main__':
    np.seterr(all='ignore')
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'make':
        make(sys.argv[2:] or None)
    elif cmd == 'cut':
        cut()
    else:
        print(__doc__)
