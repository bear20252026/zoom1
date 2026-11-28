#!/usr/bin/env python3
"""Where each drawing moves.

    python3 tools/motion.py masks     # find the things (masters/motion/gNN_<what>.png), cached
    python3 tools/motion.py build     # masks -> art/motion/NN.png, one small map per drawing
    python3 tools/motion.py sheet     # masters/motion/sheet.jpg: every map over its drawing, to check by eye

The page animates the paintings with a shader and nothing else (src/zoom.js). What the shader needs to know
is WHERE: which pixels are leaves or washing for the wind to move, which are water, which are cloud or
smoke, which are a flame or a star. PLAN below says what to look for in each drawing; a segmentation model
(SAM 3, by text prompt) finds it; and the answers are packed into a map:

    left half:   red    wind   (leaves, flowers, cloth, feathers)
                 green  water  (ripples and their glints)
                 blue   drift  (clouds, smoke, steam: slow and wide)
    right half:  red    light  (flames and lamps flicker; stars twinkle)

(Two halves side by side and no alpha channel, because a browser may multiply colour by alpha on the way in.)

Stars are found by arithmetic instead: small bright marks with darkness all round them.
"""
import os
import sys
import threading

import numpy as np
from PIL import Image
from scipy import ndimage

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain  # noqa: E402
import fal  # noqa: E402
import story  # noqa: E402

ROOT = chain.ROOT
WORK = os.path.join(chain.MASTERS, 'motion')
OUT = os.path.join(ROOT, 'art', 'motion')
SAM = 'fal-ai/sam-3/image'
SIDE = 512
CHANNEL = {'wind': 0, 'water': 1, 'drift': 2, 'light': 3}

# painting -> [(effect, what to look for, how strongly)]; ('stars',) asks for the star finder
PLAN = {
    'picture': [('light', 'lamp', 0.6)],
    'studio': [('light', 'lamp', 0.6), ('light', 'paper lantern', 0.5), ('wind', 'curtain', 0.4)],
    'doors': [('light', 'lantern', 0.6), ('wind', 'flower', 0.6), ('wind', 'leaves', 0.5)],
    'pavilion': [('light', 'lantern', 0.6), ('drift', 'smoke', 0.9), ('wind', 'tree', 0.5), ('wind', 'flower', 0.6)],
    'island': [('water', 'water', 1.0), ('light', 'lantern', 0.6), ('drift', 'cloud', 0.9), ('wind', 'tree', 0.4)],
    'bay': [('water', 'water', 1.0), ('drift', 'cloud', 1.0), ('drift', 'smoke', 0.9)],
    'street': [('wind', 'flower', 0.7), ('water', 'water', 1.0), ('light', 'lamp', 0.4)],
    'square': [('wind', 'umbrella', 0.4), ('wind', 'tree', 0.6), ('water', 'fountain', 0.8), ('wind', 'balloon', 0.8)],
    'arch': [('wind', 'flower', 0.7), ('wind', 'ivy', 0.6), ('light', 'lamp', 0.5)],
    'courtyard': [('water', 'fountain', 0.8), ('wind', 'tree', 0.6), ('wind', 'laundry', 0.9), ('drift', 'cloud', 1.0)],
    'glass doors': [('wind', 'leaves', 0.5), ('wind', 'flower', 0.5)],
    'glasshouse': [('water', 'pool', 1.0), ('wind', 'palm tree', 0.4)],
    'music door': [('wind', 'flower', 0.4)],
    'music room': [('light', 'chandelier', 0.5), ('wind', 'curtain', 0.5)],
    'library door': [('light', 'lamp', 0.5)],
    'library': [('wind', 'flower', 0.3)],
    'hall door': [('wind', 'flower', 0.4)],
    'hall': [('light', 'chandelier', 0.5), ('wind', 'curtain', 0.4)],
    'front door': [('wind', 'flower', 0.7), ('wind', 'leaves', 0.6)],
    'villa': [('water', 'fountain', 0.8), ('wind', 'tree', 0.6), ('wind', 'flower', 0.6), ('drift', 'cloud', 1.0)],
    'gardens': [('water', 'water', 1.0), ('wind', 'tree', 0.6), ('wind', 'flower', 0.6), ('drift', 'cloud', 1.0)],
    'lake': [('water', 'water', 1.0), ('drift', 'cloud', 1.0), ('drift', 'smoke', 0.9), ('wind', 'flower', 0.8),
             ('wind', 'leaves', 0.7), ('wind', 'tree', 0.5)],
    'terrace': [('wind', 'vine leaves', 0.7), ('wind', 'flower', 0.7), ('wind', 'parasol', 0.4), ('wind', 'tablecloth', 0.5)],
    'window': [('wind', 'curtain', 0.3), ('wind', 'flower', 0.5)],
    'bedroom': [('wind', 'curtain', 0.5)],
    'room door': [('light', 'lamp', 0.5), ('wind', 'palm', 0.3)],
    'landing': [('light', 'chandelier', 0.5), ('wind', 'curtain', 0.4)],
    'hotel door': [('wind', 'awning', 0.5), ('wind', 'flower', 0.7), ('wind', 'tree', 0.5)],
    'village': [('water', 'fountain', 0.8), ('wind', 'tree', 0.5), ('drift', 'cloud', 0.9)],
    'hillside': [('wind', 'tree', 0.5), ('drift', 'cloud', 1.0), ('water', 'stream', 0.9)],
    'viaduct arch': [('water', 'river', 1.0), ('wind', 'reeds', 0.8), ('wind', 'flower', 0.7)],
    'valley': [('water', 'river', 1.0), ('drift', 'cloud', 1.0), ('wind', 'flower', 0.7), ('wind', 'tree', 0.5)],
    'orchard': [('wind', 'blossom', 0.6), ('wind', 'grass', 0.4)],
    'moon gate': [('light', 'lantern', 0.6), ('wind', 'flower', 0.5)],
    'night garden': [('water', 'pond', 1.0), ('light', 'lantern', 0.6), ('light', 'moon', 0.3), ('wind', 'flower', 0.4), ('stars',)],
}
NAMES = [s[0] for s in story.STEPS]


def painted():
    """How many paintings exist so far (the chain is built from g0 outward, so they are consecutive)."""
    n = 0
    while n < len(NAMES) and os.path.exists(chain.gpath(n)):
        n += 1
    return n


def picture(k):
    graded = os.path.join(chain.FINAL, 'graded', 'g%02d.jpg' % k)
    if os.path.exists(graded):
        return Image.open(graded).convert('RGB')
    ring = os.path.join(chain.FINAL, 'ring%02d.png' % k)
    return Image.open(ring if os.path.exists(ring) else chain.gpath(k)).convert('RGB').resize((1536, 1536), Image.LANCZOS)


def mask_path(k, what):
    return os.path.join(WORK, 'g%02d_%s.png' % (k, what.replace(' ', '_')))


def masks(workers=6):
    os.makedirs(WORK, exist_ok=True)
    jobs = [(k, e[1]) for k, name in enumerate(NAMES[:painted()]) for e in PLAN.get(name, []) if len(e) == 3
            and not os.path.exists(mask_path(k, e[1]))]
    print('masks: %d to find' % len(jobs))
    urls, lock = {}, threading.Lock()

    def work():
        while True:
            with lock:
                if not jobs:
                    return
                k, what = jobs.pop(0)
            try:
                with lock:
                    url = urls.get(k)
                if url is None:
                    tmp = os.path.join(WORK, 'g%02d_in.jpg' % k)
                    picture(k).save(tmp, quality=92)
                    url = fal.upload(tmp)
                    with lock:
                        urls[k] = url
                out = fal.run(SAM, {'image_url': url, 'prompt': what, 'apply_mask': False, 'return_multiple_masks': True,
                                    'max_masks': 32, 'output_format': 'png'}, label='sam', log=open(os.devnull, 'w'))
                total = np.zeros((SIDE, SIDE), np.uint8)
                for i, m in enumerate(out.get('masks') or []):
                    tmp = os.path.join(WORK, '_%02d_%s_%d.png' % (k, what.replace(' ', '_'), i))
                    fal.download(m['url'], tmp)
                    total = np.maximum(total, np.asarray(Image.open(tmp).convert('L').resize((SIDE, SIDE), Image.BILINEAR)))
                    os.remove(tmp)
                Image.fromarray(total).save(mask_path(k, what))
                print('  g%02d %-15s %-10s %2d found, %4.1f%% of the drawing' % (k, NAMES[k], what, len(out.get('masks') or []), (total > 127).mean() * 100))
            except Exception as err:
                print('  g%02d %s FAILED: %s' % (k, what, str(err)[:160]))
            sys.stdout.flush()

    threads = [threading.Thread(target=work) for _ in range(workers)]
    [t.start() for t in threads]
    [t.join() for t in threads]


def stars(k):
    """Small bright marks surrounded by darkness."""
    a = np.asarray(picture(k).convert('L').resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255
    near, wide = ndimage.gaussian_filter(a, 9), ndimage.gaussian_filter(a, 26)
    spot = (a - near > 0.25) & (near < 0.4) & (wide < 0.4)
    lab, count = ndimage.label(spot)                             # only specks: not lines, not big bright things
    if count:
        boxes = ndimage.find_objects(lab)
        area = ndimage.sum(spot, lab, index=np.arange(1, count + 1))
        keep = np.zeros(count + 1, bool)
        for i, box in enumerate(boxes):
            h, w = box[0].stop - box[0].start, box[1].stop - box[1].start
            keep[i + 1] = area[i] <= 90 and max(h, w) <= 16 and min(h, w) * 2.5 >= max(h, w)
        spot = keep[lab]
    spot = ndimage.binary_dilation(spot, iterations=2)
    return np.asarray(Image.fromarray((spot * 255).astype(np.uint8)).resize((SIDE, SIDE), Image.BOX)).astype(np.float32) / 255


def one_map(k):
    m = np.zeros((SIDE, SIDE, 4), np.float32)
    plan = sorted(PLAN.get(NAMES[k], []), key=lambda e: e[0] == 'stars')      # stars last: they need the clouds
    for e in plan:
        if e[0] == 'stars':                                      # not on a cloud's bright edge: that is not a star
            sky = 1 - np.clip(ndimage.grey_dilation(m[..., 2], size=(9, 9)) * 3, 0, 1)
            m[..., 3] = np.maximum(m[..., 3], np.clip(stars(k) * 1.6, 0, 1) * sky)
            continue
        effect, what, amount = e
        if not os.path.exists(mask_path(k, what)):
            continue
        a = np.asarray(Image.open(mask_path(k, what))).astype(np.float32) / 255
        if a.mean() > 0.6:                                       # it "found" nearly everything: not an answer
            continue
        if effect == 'light':                                    # the thing itself, and the light it throws round it
            glow = ndimage.gaussian_filter(a, SIDE * 0.035)
            a = np.clip(np.maximum(a, glow / max(float(glow.max()), 1e-3)), 0, 1) * 0.58   # < 0.62: a flame, never a star
        elif effect == 'wind':
            a = ndimage.gaussian_filter(a, 2.0)                  # a leaf moves with a little of what is round it
        else:
            # water and cloud are held still along their edges and move inside them, so that a shoreline, or a
            # tower standing against the sky, is never dragged about by what is next to it
            a = ndimage.gaussian_filter(ndimage.grey_erosion(a, size=(7, 7)), 3.0)
        c = CHANNEL[effect]
        m[..., c] = np.maximum(m[..., c], a * amount)
    return m


def build():
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        os.remove(os.path.join(OUT, old))
    n = painted()
    for k in range(n):
        m = one_map(k)
        i = n - 1 - k                                            # the page counts from the outside in
        b = (np.clip(m, 0, 1) * 255 + 0.5).astype(np.uint8)
        packed = np.zeros((SIDE, SIDE * 2, 3), np.uint8)
        packed[:, :SIDE] = b[..., :3]
        packed[:, SIDE:, 0] = b[..., 3]
        Image.fromarray(packed, 'RGB').save(os.path.join(OUT, '%02d.png' % i), optimize=True)
        cover = [float((m[..., c] > 0.1).mean() * 100) for c in range(4)]
        print('  g%02d %-15s wind %4.1f%%  water %4.1f%%  drift %4.1f%%  light %4.1f%%' % (k, NAMES[k], *cover))
    print('wrote %d maps, %.1f MB' % (n, sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) / 1e6))


def sheet(tile=330, cols=6):
    n = painted()
    rows = (n + cols - 1) // cols
    out = Image.new('RGB', (tile * cols, tile * rows), 'white')
    tint = np.array([[70, 220, 60], [40, 150, 255], [255, 60, 200], [255, 190, 0]], np.float32)   # wind water drift light
    for k in range(n):
        base = np.asarray(picture(k).resize((tile, tile), Image.LANCZOS)).astype(np.float32)
        grey = base.mean(axis=2, keepdims=True) * 0.55 + 90
        full = (np.clip(one_map(k), 0, 1) * 255).astype(np.uint8)
        m = np.stack([np.asarray(Image.fromarray(full[..., c]).resize((tile, tile), Image.BILINEAR)) for c in range(4)], axis=-1).astype(np.float32) / 255
        img = np.repeat(grey, 3, axis=2)
        for c in range(4):
            a = np.clip(m[..., c:c + 1] * 1.3, 0, 1) * 0.75
            img = img * (1 - a) + tint[c] * a
        i = n - 1 - k
        out.paste(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), ((i % cols) * tile, (i // cols) * tile))
    path = os.path.join(WORK, 'sheet.jpg')
    out.save(path, quality=88)
    print('wrote', path, '(order of the fall; green wind, blue water, pink drift, amber light)')


if __name__ == '__main__':
    np.seterr(all='ignore')
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'masks':
        masks()
    elif cmd == 'build':
        build()
    elif cmd == 'sheet':
        sheet()
    else:
        print(__doc__)
