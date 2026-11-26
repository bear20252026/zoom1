#!/usr/bin/env python3
"""The scraps of paper the words are written on.

    python3 tools/extras.py make     # ask the image model (masters/extras/*.png, transparent)
    python3 tools/extras.py cut      # trim to the paper and save art/ui/*.webp
"""
import os
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fal  # noqa: E402

ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'masters', 'extras')
OUT = os.path.join(ROOT, 'art', 'ui')

COMMON = (
    " The paper is warm cream cold-press drawing paper with a visible soft tooth, torn by hand from a larger sheet: "
    "deckled, feathery, slightly uneven torn edges on all four sides. It lies perfectly flat and is seen straight from "
    "above, evenly lit. Nothing is written or drawn on it; it is blank. No shadow, no tape, no pins, no other objects. "
    "The background around the paper is completely transparent."
)
ITEMS = {
    'strip': ((2400, 800),
              "One long, narrow strip of paper, running horizontally and spanning almost the full width of the image, "
              "about one seventh as tall as it is wide, centred, with empty space above and below it." + COMMON),
    'card': ((2048, 1280),
             "One torn piece of paper, a rough rectangle a little wider than it is tall (about three to two), filling most "
             "of the image, centred." + COMMON),
}


def make(only=None):
    os.makedirs(SRC, exist_ok=True)
    for name, ((w, h), prompt) in ITEMS.items():
        if only and name not in only:
            continue
        out = fal.run(fal.T2I, {'prompt': prompt, 'image_size': {'width': w, 'height': h}, 'quality': 'high',
                                'num_images': 1, 'output_format': 'png', 'background': 'transparent'},
                      label='extra ' + name)
        fal.download(out['images'][0]['url'], os.path.join(SRC, name + '.png'))
        print('wrote', name)


def cut():
    os.makedirs(OUT, exist_ok=True)
    for name in ITEMS:
        path = os.path.join(SRC, name + '.png')
        if not os.path.exists(path):
            print('missing', path)
            continue
        im = Image.open(path).convert('RGBA')
        a = np.asarray(im)[..., 3]
        ys, xs = np.where(a > 24)
        if len(xs) == 0:
            print(name, 'has no alpha; skipped')
            continue
        im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        scale = 1400 / im.width
        im = im.resize((1400, max(1, round(im.height * scale))), Image.LANCZOS)
        im.save(os.path.join(OUT, 'scrap_%s.webp' % name), quality=86, method=6)
        print(name, im.size, 'opaque share %.2f' % (np.asarray(im)[..., 3] > 200).mean())


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'make':
        make(sys.argv[2:] or None)
    elif cmd == 'cut':
        cut()
    else:
        print(__doc__)
