#!/usr/bin/env python3
"""Build the chain of nested drawings, from the inside out.

    python3 tools/chain.py card               # the style and colour guide shown to every step
    python3 tools/chain.py seed [-n 2]        # g0: the studio wall and its empty frame (text to image)
    python3 tools/chain.py step K [-n 1]      # gK: shrink g(K-1) to half, draw what surrounds it
    python3 tools/chain.py accept K I         # keep candidate I of step K as gK
    python3 tools/chain.py run A B            # steps A..B in a row, keeping candidate 0 of each
    python3 tools/chain.py redo K [-n 1]      # the join of step K again from the model output on disk
    python3 tools/chain.py repaint K          # paint K's own ring again (new prompt), keeping both neighbours; then redo K+1

How one step goes:
  1. g(K-1) at half size (1152 px) is set in the middle of a 2880 px sheet; the model draws around it.
  2. The model never returns the middle where it was put (it comes back moved and stretched a few
     per cent), so `register` finds it and the output is pulled back until it lies under the original.
  3. The few levels of lightness the model adds are taken off again, what is left is matched at the join,
     and `stitch` cuts the two together along the path where they agree best. That is gK, 2304 px, with
     g(K-1) in its middle half.
  4. g(K-1)'s own rim is replaced by gK's version of it (`reconcile`), so the two say the same thing
     wherever both can be seen. That finished g(K-1) goes to masters/final/.
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fal  # noqa: E402
import register  # noqa: E402
import stitch  # noqa: E402
import story  # noqa: E402

ROOT = os.path.dirname(HERE)
MASTERS = os.path.join(ROOT, 'masters')
WORK = os.path.join(MASTERS, 'work')
FINAL = os.path.join(MASTERS, 'final')
S = 2304             # side of every master (the sheet's middle 80%: the model drifts, so it needs the slack)
SHEET = 2880         # side of the sheet the model draws on (the most it allows)
N = S // 2           # the kept picture, as the model sees it
O = (SHEET - N) // 2  # where it sits on the sheet
WIN = (SHEET - S) // 2  # the master is this window of the sheet
SINK = 100           # px: new steps set the kept picture this much below centre (the model slides it up by about that)
Q = S // 4           # where the kept picture sits in the master
PAPER = (244, 238, 224)


def gpath(k):
    return os.path.join(MASTERS, 'g%02d.png' % k)


def cand(k, i, tag=''):
    return os.path.join(WORK, 'g%02d_c%d%s.png' % (k, i, ('_' + tag) if tag else ''))


def preview(img, path, side=1100):
    img.resize((side, side), Image.LANCZOS).convert('RGB').save(path, quality=88)


def card_path():
    return os.path.join(MASTERS, 'card.png')


def do_card():
    """The style and colour guide every later step is shown."""
    os.makedirs(MASTERS, exist_ok=True)
    out = fal.run(fal.T2I, {'prompt': story.CARD + story.MEDIUM, 'image_size': {'width': 1536, 'height': 1536},
                            'quality': 'high', 'num_images': 1, 'output_format': 'png', 'background': 'opaque'}, label='card')
    fal.download(out['images'][0]['url'], card_path())
    print('wrote', card_path())


def blank_box(img):
    """The blank mount in the seed: bounding box of the flat area that holds the picture's centre."""
    from scipy import ndimage
    a = np.asarray(img.convert('RGB')).astype(np.float32)
    h, w = a.shape[:2]
    mid = np.median(a[h // 2 - 60:h // 2 + 60, w // 2 - 60:w // 2 + 60].reshape(-1, 3), axis=0)
    flat = np.abs(a - mid).max(axis=2) < 16
    lab, _ = ndimage.label(flat)
    box = ndimage.find_objects((lab == lab[h // 2, w // 2]).astype(np.uint8))[0]
    return box[1].start, box[0].start, box[1].stop, box[0].stop


def do_seed(n, quality, recut=False):
    os.makedirs(WORK, exist_ok=True)
    big = 2560
    if not recut:
        out = fal.run(fal.T2I, {
            'prompt': story.SEED + story.MEDIUM,
            'image_size': {'width': big, 'height': big},
            'quality': quality, 'num_images': n, 'output_format': 'png', 'background': 'opaque',
        }, label='g00 seed')
        for i, im in enumerate(out['images']):
            fal.download(im['url'], cand(0, i, 'raw'))
    for i in range(n):
        if not os.path.exists(cand(0, i, 'raw')):
            continue
        img = Image.open(cand(0, i, 'raw')).convert('RGB')
        if img.size != (big, big):
            img = img.resize((big, big), Image.LANCZOS)
        x0, y0, x1, y1 = blank_box(img)
        # cut the master as a square window about the blank mount's centre, as large as fits in the painting
        # and no larger than leaves the mount a margin round the middle half (where the picture will go)
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        w = min(2 * min(cx, cy, big - cx, big - cy), min(x1 - x0, y1 - y0) / 0.55, S)
        left, top = int(round(cx - w / 2.0)), int(round(cy - w / 2.0))
        w = int(w)
        img = img.crop((left, top, left + w, top + w)).resize((S, S), Image.LANCZOS)
        img.save(cand(0, i))
        preview(img, cand(0, i, 'view').replace('.png', '.jpg'))
        fx0, fy0, fx1, fy1 = [(v - o) / float(w) for v, o in ((x0, left), (y0, top), (x1, left), (y1, top))]
        room = min(0.25 - fx0, 0.25 - fy0, fx1 - 0.75, fy1 - 0.75)
        print('g00 c%d: window %d px of %d; blank mount spans x %.3f-%.3f, y %.3f-%.3f of the master; margin round the picture %.3f %s'
              % (i, w, big, fx0, fx1, fy0, fy1, room, '' if room > 0.012 else '  <-- too small'))
    if n == 1:
        shutil.copyfile(cand(0, 0), gpath(0))


def join(k, i, inner, small):
    """Model output on disk -> the candidate master, the reconciled inner picture, and a log line."""
    name = story.STEPS[k][0]
    raw = Image.open(cand(k, i, 'raw')).convert('RGB')
    size = raw.size
    if raw.size != (SHEET, SHEET):
        raw = raw.resize((SHEET, SHEET), Image.LANCZOS)
    pulled = cand(k, i, 'pulled')            # the output brought back into register: slow to find, so it is kept
    meta = pulled.replace('.png', '.json')
    if os.path.exists(pulled) and os.path.exists(meta) and os.path.getmtime(pulled) > os.path.getmtime(cand(k, i, 'raw')):
        v = Image.open(pulled).convert('RGB')
        with open(meta) as f:
            saved = json.load(f)
        rep, cover = saved['register'], saved['coverage']
    else:
        sink = sheet_sink(k)
        mapping, rep = register.locate(small, raw, (O, O + sink), order=3)
        v, cover = register.pull_back(raw, mapping, S, (WIN, WIN + sink))
        v.save(pulled)
        with open(meta, 'w') as f:
            json.dump({'register': rep, 'coverage': cover}, f)
    v, anchored = stitch.shift(v, v.crop((Q, Q, Q + N, Q + N)), small)
    v, gains = stitch.tone_match(v, v.crop((Q, Q, Q + N, Q + N)), small, (Q, Q))
    v_mid = v.crop((Q, Q, Q + N, Q + N))
    matte, seam = stitch.seam_matte(small, v_mid)
    inner_done = stitch.reconcile(inner, v_mid, matte)
    outer = v.copy()
    outer.paste(inner_done.resize((N, N), Image.LANCZOS), (Q, Q))   # the rule, to the pixel
    outer.save(cand(k, i))
    inner_done.save(cand(k, i, 'inner'))
    Image.fromarray((matte * 255).astype(np.uint8)).save(cand(k, i, 'matte'))
    preview(outer, cand(k, i, 'view').replace('.png', '.jpg'))
    log = {'step': k, 'name': name, 'candidate': i, 'returned': list(size), 'coverage': round(cover, 4),
           'register': rep, 'shift': anchored, 'tone': gains, 'seam': seam}
    with open(cand(k, i, 'log').replace('.png', '.json'), 'w') as f:
        json.dump(log, f, indent=1)
    flag = '' if cover > 0.975 else '   <-- the output did not cover the whole master'
    print('g%02d %s c%d: coverage %.4f, moved (%.0f, %.0f) px x%.3f, tone shift %s, seam %.0f px in (max %.0f), cost %.3f%s'
          % (k, name, i, cover, rep['shift'][0], rep['shift'][1], rep['scale'][0], anchored,
             seam['seam_mean_px'], seam['seam_max_px'], seam['cost_on_seam'], flag))
    sys.stdout.flush()
    return cover


def sheet_sink(k):
    """How far below centre the kept picture was set on step k's sheet (0 for steps made before that was done)."""
    path = os.path.join(WORK, 'g%02d_sheet.json' % k)
    if os.path.exists(path):
        with open(path) as f:
            return int(json.load(f).get('sink', 0))
    return 0


def request(k, n, quality, extra=''):
    """Ask the model to draw around g(k-1); returns the URLs of what came back."""
    name, kind, ring = story.STEPS[k]
    prompt = story.EXTEND + ring + (' ' + extra if extra else '') + '\n\n' + story.MEDIUM
    out = fal.run(fal.EDIT, {
        'prompt': prompt,
        'image_urls': [fal.upload(os.path.join(WORK, 'g%02d_sheet.png' % k)), fal.upload(card_path())],
        'mask_url': fal.upload(os.path.join(WORK, 'g%02d_mask.png' % k)),
        'image_size': {'width': SHEET, 'height': SHEET},
        'quality': quality, 'num_images': n, 'output_format': 'png', 'background': 'opaque',
    }, label='g%02d %s' % (k, name))
    return [im['url'] for im in out['images']]


def do_step(k, n, quality, extra='', only_join=False, tries=3):
    os.makedirs(WORK, exist_ok=True)
    inner = Image.open(gpath(k - 1)).convert('RGB')
    small = inner.resize((N, N), Image.LANCZOS)
    if only_join:
        for i in range(n):
            if os.path.exists(cand(k, i, 'raw')):
                join(k, i, inner, small)
        if n == 1:
            accept(k, 0)
        return
    sheet = Image.new('RGB', (SHEET, SHEET), PAPER)
    sheet.paste(small, (O, O + SINK))
    mask = Image.new('L', (SHEET, SHEET), 255)
    mask.paste(0, (O, O + SINK, O + N, O + SINK + N))
    sheet.save(os.path.join(WORK, 'g%02d_sheet.png' % k))
    mask.save(os.path.join(WORK, 'g%02d_mask.png' % k))
    with open(os.path.join(WORK, 'g%02d_sheet.json' % k), 'w') as f:
        json.dump({'sink': SINK}, f)
    for old in os.listdir(WORK):                 # anything cached from an earlier try at this step is stale now
        if old.startswith('g%02d_c' % k) and ('_pulled' in old):
            os.remove(os.path.join(WORK, old))
    if n > 1:                                   # several candidates to choose between by eye
        for i, url in enumerate(request(k, n, quality, extra)):
            fal.download(url, cand(k, i, 'raw'))
            join(k, i, inner, small)
        return
    # one at a time, asking again when the model slid the kept picture so far that the master is not covered
    best, best_cover = None, -1.0
    for i in range(tries):
        fal.download(request(k, 1, quality, extra)[0], cand(k, i, 'raw'))
        try:
            cover = join(k, i, inner, small)
        except Exception as err:               # the kept picture could not be found in what came back
            print('g%02d attempt %d: %s' % (k, i, err))
            continue
        if cover > best_cover:
            best, best_cover = i, cover
        if cover >= 0.975:
            break
        print('g%02d attempt %d covered only %.3f of the master; asking again' % (k, i, cover))
    if best is None:
        raise SystemExit('g%02d: no usable drawing after %d tries' % (k, tries))
    accept(k, best)


REPAINT = (
    "The first image is a painting with one part missing: the plain blank band between the finished square in the "
    "middle and the finished strip that runs round all four edges. Paint the blank band, and only that. Do not "
    "change, move or repaint the central square or the strip round the edges: they must stay exactly where they "
    "are. What you paint must join both of them without any break, border, gap or change of style, every shape, "
    "colour and brushstroke carrying across, so that nobody could tell which part was painted last. In particular "
    "the central square must not look like a picture set into the painting: whatever reaches its edge (sky, water, "
    "ground, trees, walls) carries straight on outward into the band in the same colour and at the same height, "
    "until it meets the things described below; there must be no visible square." + story.GUIDE +
    "\n\nWhat the band shows: "
)


def do_repaint(k, ring, quality='high', band=0.11):
    """Paint painting k's own ring again, with a new description, keeping what it joins on BOTH sides: the
    picture in its middle, and a band along its outer edge (which is what painting k+1 was painted around).
    Afterwards run `redo k+1` so that the next painting takes the new one into its middle."""
    backup = os.path.join(WORK, 'g%02d_before_repaint.png' % k)
    old = Image.open(backup if os.path.exists(backup) else gpath(k)).convert('RGB')   # always from the original
    inner = Image.open(gpath(k - 1)).convert('RGB')
    small = inner.resize((N, N), Image.LANCZOS)
    b = int(band * S / 2)
    sheet = old.copy()
    sheet.paste(PAPER, (b, b, S - b, S - b))
    sheet.paste(small, (Q, Q))
    mask = Image.new('L', (S, S), 0)
    mask.paste(255, (b, b, S - b, S - b))
    mask.paste(0, (Q, Q, Q + N, Q + N))
    spath, mpath = os.path.join(WORK, 'g%02d_resheet.png' % k), os.path.join(WORK, 'g%02d_remask.png' % k)
    sheet.save(spath)
    mask.save(mpath)
    out = fal.run(fal.EDIT, {
        'prompt': REPAINT + ring + '\n\n' + story.MEDIUM,
        'image_urls': [fal.upload(spath), fal.upload(card_path())], 'mask_url': fal.upload(mpath),
        'image_size': {'width': S, 'height': S}, 'quality': quality, 'num_images': 1,
        'output_format': 'png', 'background': 'opaque'}, label='g%02d again' % k)
    raw_path = os.path.join(WORK, 'g%02d_repaint_raw.png' % k)
    fal.download(out['images'][0]['url'], raw_path)
    raw = Image.open(raw_path).convert('RGB')
    if raw.size != (S, S):
        raw = raw.resize((S, S), Image.LANCZOS)
    mapping, rep = register.locate(small, raw, (Q, Q), order=3)
    v, cover = register.pull_back(raw, mapping, S, (0, 0))
    v, shifted = stitch.shift(v, v.crop((Q, Q, Q + N, Q + N)), small)
    # outside: give way to the old painting across the kept band (where both show the same thing)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    edge = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy))
    t = np.clip((edge - (b - 56)) / 48.0, 0, 1)
    w = (t * t * (3 - 2 * t))[..., None]
    a = np.asarray(old).astype(np.float32) * (1 - w) + np.asarray(v).astype(np.float32) * w
    outer = Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8))
    # inside: the same join as any step
    v_mid = v.crop((Q, Q, Q + N, Q + N))
    matte, seam = stitch.seam_matte(small, v_mid)
    inner_done = stitch.reconcile(inner, v_mid, matte)
    outer.paste(inner_done.resize((N, N), Image.LANCZOS), (Q, Q))
    if not os.path.exists(backup):                 # keep the first original, however many times this is run
        shutil.copyfile(gpath(k), backup)
    outer.save(gpath(k))
    os.makedirs(FINAL, exist_ok=True)
    inner_done.save(os.path.join(FINAL, 'g%02d.png' % (k - 1)))
    preview(outer, os.path.join(WORK, 'g%02d_repaint_view.jpg' % k))
    print('g%02d repainted: moved (%.0f, %.0f) px x%.3f, tone shift %s, seam %.0f px in'
          % (k, rep['shift'][0], rep['shift'][1], rep['scale'][0], shifted, seam['seam_mean_px']))


def accept(k, i):
    os.makedirs(FINAL, exist_ok=True)
    shutil.copyfile(cand(k, i), gpath(k))
    if k > 0:
        shutil.copyfile(cand(k, i, 'inner'), os.path.join(FINAL, 'g%02d.png' % (k - 1)))
    print('g%02d <- candidate %d' % (k, i))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('card')
    p = sub.add_parser('seed'); p.add_argument('-n', type=int, default=1); p.add_argument('--quality', default='high')
    p.add_argument('--recut', action='store_true')
    for c in ('step', 'redo'):
        p = sub.add_parser(c); p.add_argument('k', type=int); p.add_argument('-n', type=int, default=1)
        p.add_argument('--quality', default='high'); p.add_argument('--extra', default='')
    p = sub.add_parser('accept'); p.add_argument('k', type=int); p.add_argument('i', type=int)
    p = sub.add_parser('repaint'); p.add_argument('k', type=int)
    p = sub.add_parser('run'); p.add_argument('a', type=int); p.add_argument('b', type=int); p.add_argument('--quality', default='high')
    a = ap.parse_args()
    np.seterr(all='ignore')
    if a.cmd == 'card':
        do_card()
    elif a.cmd == 'seed':
        do_seed(a.n, a.quality, a.recut)
    elif a.cmd == 'step':
        do_step(a.k, a.n, a.quality, a.extra)
    elif a.cmd == 'redo':
        do_step(a.k, a.n, a.quality, only_join=True)
    elif a.cmd == 'repaint':
        do_repaint(a.k, story.STEPS[a.k][2])
    elif a.cmd == 'accept':
        accept(a.k, a.i)
    elif a.cmd == 'run':
        for k in range(a.a, a.b + 1):
            do_step(k, 1, a.quality)


if __name__ == '__main__':
    main()
