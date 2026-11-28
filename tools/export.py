#!/usr/bin/env python3
"""Finish the chain and write what the page loads.

    python3 tools/export.py ring       # close the loop: masters/final/ringNN.png (2304 px, as painted)
    python3 tools/export.py sharpen    # each of those upscaled 2x on fal: masters/final/srNN.png (4608 px, cached)
    python3 tools/export.py            # both of the above if needed, then grade and write art/frames/* and src/story.js
    python3 tools/export.py plain      # no upscale: grade the 2304 px ring and export (quick, for trying things)

Closing the loop. The innermost painting is a studio wall with an empty frame: a blank cream mount a little
larger than the middle half of the picture. The outermost painting, the lake, goes into that middle half and
becomes the picture in the frame, with the rest of the mount showing round it. Nothing has to be blended: a
painting meets its mount at a clean edge. That is just the chain's one rule (the middle half of each painting
is the next one at half size) applied once more, to the last pair.

Sharpening. Every painting is enlarged 2x by a restoration model (SeedVR2). It restores, it does not repaint:
the mean colour of any 36 px block moves by less than half a level, and what little it moves is put back
(`lock_tones`). The rule is then imposed again at the new size, so each painting's middle is the true detail
of the next painting and not an enlargement of a reduction of it.

Grading: see tools/grade.py. It runs last, at full size, so its settings can be changed without paying for the
upscales again.
"""
import json
import os
import sys
import threading
import time

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain  # noqa: E402
import fal  # noqa: E402
import grade  # noqa: E402
import story  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
ROOT = chain.ROOT
S, N, Q = chain.S, chain.N, chain.Q
COUNT = len(story.STEPS)
SR = 'fal-ai/seedvr/upscale/image'
TIERS = (('xl', 4096, 88, 4), ('hi', 2048, 88, 6), ('md', 1024, 86, 6), ('lo', 512, 76, 6))   # name, side, quality, effort


def f32(img):
    return np.asarray(img.convert('RGB')).astype(np.float32)


def img8(a):
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8))


def ring_path(k):
    return os.path.join(chain.FINAL, 'ring%02d.png' % k)


def sr_path(k):
    return os.path.join(chain.FINAL, 'sr%02d.png' % k)


def load_master(k):
    final = os.path.join(chain.FINAL, 'g%02d.png' % k)
    return Image.open(final if os.path.exists(final) else chain.gpath(k)).convert('RGB')


def ramp(n, feather):
    i = np.arange(n, dtype=np.float32)
    d = np.minimum(i, n - 1 - i)
    t = np.clip(np.minimum(d[:, None], d[None, :]) / float(feather), 0, 1)
    return t * t * (3 - 2 * t)


def impose(pics, laps=2, feather=0, ring=True):
    """Middle half of g(k+1) := g(k) at half size, all the way round (g0's middle holds the outermost).

    With a feather, the outer drawing keeps a thin band of its own just inside the square and gives way to
    the inner one over `feather` px, so two separately sharpened versions of the same place meet softly.
    """
    n = len(pics)
    side = pics[0].width
    half, q = side // 2, side // 4
    m = ramp(half, feather)[..., None] if feather else None
    for _ in range(laps):
        for k in range(n if ring else n - 1):
            outer = (k + 1) % n
            small = pics[k].resize((half, half), Image.LANCZOS)
            if m is None:
                o = pics[outer].copy()
                o.paste(small, (q, q))
            else:
                a = np.asarray(pics[outer]).copy()
                mid = a[q:q + half, q:q + half].astype(np.float32)
                a[q:q + half, q:q + half] = np.clip(mid * (1 - m) + np.asarray(small).astype(np.float32) * m + 0.5, 0, 255).astype(np.uint8)
                o = Image.fromarray(a)
            pics[outer] = o


def do_ring():
    missing = [k for k in range(COUNT) if not os.path.exists(chain.gpath(k))]
    if missing:
        raise SystemExit('drawings missing: %s' % missing)
    pics = [load_master(k) for k in range(COUNT)]
    impose(pics)                                                # the last pair closes the loop: g0's frame gets the lake
    os.makedirs(chain.FINAL, exist_ok=True)
    changed = 0
    for k, p in enumerate(pics):
        old = ring_path(k)
        if os.path.exists(old):
            # Unchanged in its own ring? Then keep its file, and with it its upscale. What is in a painting's
            # middle does not count: that is the next painting, and the export sets it in again afterwards.
            was, now = np.asarray(Image.open(old).convert('RGB')).copy(), np.asarray(p).copy()
            was[Q:Q + N, Q:Q + N] = 0
            now[Q:Q + N, Q:Q + N] = 0
            if np.array_equal(was, now):
                continue
        p.save(old)
        changed += 1
    print('ring: %d drawings, %d written' % (COUNT, changed))


def do_sharpen(workers=4):
    todo = [k for k in range(COUNT)
            if not os.path.exists(sr_path(k)) or os.path.getmtime(sr_path(k)) < os.path.getmtime(ring_path(k))]
    print('sharpen: %d to do' % len(todo))
    lock = threading.Lock()
    failed = []

    def work():
        while True:
            with lock:
                if not todo:
                    return
                k = todo.pop(0)
            t0 = time.time()
            try:
                out = fal.run(SR, {'image_url': fal.upload(ring_path(k)), 'upscale_factor': 2, 'upscale_mode': 'factor',
                                   'noise_scale': 0.1, 'output_format': 'png', 'seed': 7},
                              label='sr%02d' % k, log=open(os.devnull, 'w'))
                im = out.get('image') or out['images'][0]
                fal.download(im['url'], sr_path(k) + '.part')
                os.replace(sr_path(k) + '.part', sr_path(k))
                print('  sr%02d %s in %.0fs' % (k, story.STEPS[k][0], time.time() - t0))
            except Exception as err:
                failed.append(k)
                print('  sr%02d FAILED: %s' % (k, str(err)[:200]))
            sys.stdout.flush()

    threads = [threading.Thread(target=work) for _ in range(workers)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    if failed:
        raise SystemExit('sharpen: failed for %s; run again' % failed)


def lock_tones(sr, ring):
    """Put back whatever the upscale moved in broad tone, measured on 8 px blocks of the original."""
    side = sr.width
    n = ring.width // 8
    d = f32(ring.resize((n, n), Image.BOX)) - f32(sr.resize((n, n), Image.BOX))
    d = ndimage.gaussian_filter(d, (1.0, 1.0, 0))
    up = np.stack([np.asarray(Image.fromarray(d[..., c]).resize((side, side), Image.BICUBIC)) for c in range(3)], axis=-1)
    out = np.empty((side, side, 3), np.uint8)
    for y in range(0, side, 512):                                # in strips: these are big
        out[y:y + 512] = np.clip(np.asarray(sr)[y:y + 512].astype(np.float32) + up[y:y + 512] + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def crisp(img):
    """A slight unsharp mask after reducing: reduction and painted edges are both a little soft."""
    return img.filter(ImageFilter.UnsharpMask(radius=1.3, percent=70, threshold=1))


def grade_big(pics):
    g, stats = grade.gains(pics)
    n = len(pics)
    for k in range(n):
        side = pics[k].width
        field = grade.depth_field(side, g[(k - 1) % n], g[k], g[(k + 1) % n])
        a = np.asarray(pics[k])
        out = np.empty_like(a)
        for y in range(0, side, 384):
            out[y:y + 384] = (grade.look(a[y:y + 384].astype(np.float32), field[y:y + 384]) + 0.5).astype(np.uint8)
        pics[k] = Image.fromarray(out)
        print('  graded g%02d %-12s colour %.3f (darks %.2f, lights %.2f) -> gain x%.2f' % (k, story.STEPS[k][0], *stats[k], g[k]))
        sys.stdout.flush()


def do_export(sharp=True, partial=False):
    """partial: export whatever has been painted so far, without closing the loop (for looking at it early)."""
    global COUNT
    t0 = time.time()
    if partial:
        COUNT = len([k for k in range(COUNT) if os.path.exists(chain.gpath(k))])
        pics = [load_master(k) for k in range(COUNT)]
        impose(pics, ring=False)
    elif sharp:
        pics = []
        for k in range(COUNT):
            sr = Image.open(sr_path(k)).convert('RGB')
            pics.append(lock_tones(sr, Image.open(ring_path(k)).convert('RGB')))
        impose(pics, feather=32)
    else:
        pics = [Image.open(ring_path(k)).convert('RGB') for k in range(COUNT)]
    print('loaded %d drawings at %d px (%.0fs)' % (COUNT, pics[0].width, time.time() - t0))
    grade_big(pics)
    impose(pics, feather=32 if sharp and not partial else 0, ring=not partial)
    print('graded (%.0fs)' % (time.time() - t0))

    order = list(range(COUNT - 1, -1, -1))                       # the page shows them outermost first
    for tier, side, quality, effort in TIERS:
        if side > pics[0].width:
            continue
        d = os.path.join(ROOT, 'art', 'frames', tier)
        os.makedirs(d, exist_ok=True)
        for old in os.listdir(d):
            os.remove(os.path.join(d, old))
        for i, k in enumerate(order):
            crisp(pics[k].resize((side, side), Image.LANCZOS)).save(os.path.join(d, '%02d.webp' % i), quality=quality, method=effort)
        size = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)) / 1e6
        print('%s: %d files at %d px, %.1f MB (%.0fs)' % (tier, COUNT, side, size, time.time() - t0))
        sys.stdout.flush()
    # small graded copies in the drawings' own order, for the tools that need to look at them (tools/motion.py)
    d = os.path.join(chain.FINAL, 'graded')
    os.makedirs(d, exist_ok=True)
    for k, p in enumerate(pics):
        p.resize((1536, 1536), Image.LANCZOS).save(os.path.join(d, 'g%02d.jpg' % k), quality=92)

    names = [s[0] for s in story.STEPS]
    with open(os.path.join(ROOT, 'art', 'letters', 'index.json')) as f:
        letters = json.load(f)
    motion = os.path.isdir(os.path.join(ROOT, 'art', 'motion'))
    out = {
        'base': 'art/frames',
        'tiers': [t[0] for t in TIERS if t[1] <= pics[0].width],
        'frames': ['%02d' % i for i in range(COUNT)],
        'names': [names[k] for k in order],
        'motion': 'art/motion' if motion else None,
        'letters': {k: {'w': v['w'], 'h': v['h']} for k, v in letters.items()},
        'start': round(COUNT - 0.42, 2),
    }
    with open(os.path.join(ROOT, 'src', 'story.js'), 'w') as f:
        f.write('// Written by tools/export.py: the drawings in the order of the fall.\n')
        f.write('export const STORY = ' + json.dumps(out, indent=2) + ';\n')
    print('wrote src/story.js (%d drawings)' % COUNT)


if __name__ == '__main__':
    np.seterr(all='ignore')
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if cmd == 'ring':
        do_ring()
    elif cmd == 'sharpen':
        do_sharpen()
    elif cmd == 'plain':                 # no upscale: grade the 2304 px ring and export (quick, for trying a grade)
        do_ring()
        do_export(sharp=False)
    elif cmd == 'partial':               # whatever exists so far, loop not closed
        do_export(sharp=False, partial=True)
    else:
        do_ring()
        do_sharpen()
        do_export()
