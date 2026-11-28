"""The grade: one light pass so that seventeen paintings read as one.

The paintings come from the model already rich, and each was painted with the same style guide in front of
it, so there is little to do. What is left is what any set of pictures painted at different sittings needs
before it is hung together:

  * evening out: a painting whose colour came out weaker or stronger than its neighbours' is brought part
    of the way toward the chain's middle. The amount changes smoothly with depth, from each painting's inner
    edge to its outer one, so the correction itself has no seams;
  * one look for all of them: a slight S-curve so darks sit down and lights lift, and a little more colour
    where colour is weak, leaving strong colour alone (so nothing turns to candy).
  * a signature: the paintings were painted in a palette borrowed from another painter, and `ours` turns it a
    few degrees so that it is ours: indigo in the darks, jade for celadon, apricot for dusty pink.

Everything is done in OKLab, where "lighter" and "more colourful" mean what they look like.
"""
import numpy as np
from PIL import Image

EVEN = 0.5            # how far each painting's colour strength is moved toward the chain's median (0 none, 1 all)
EVEN_LIMIT = (0.92, 1.22)
CONTRAST = 0.07       # depth of the S-curve
VIBRANCE = 0.10       # extra chroma for weak colours, fading out for strong ones
OURS = 1.0            # strength of the signature turn of the palette (0 = as painted)


def _lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _enc(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255.0


def to_oklab(rgb):
    r = _lin(rgb)
    l = 0.4122214708 * r[..., 0] + 0.5363325363 * r[..., 1] + 0.0514459929 * r[..., 2]
    m = 0.2119034982 * r[..., 0] + 0.6806995451 * r[..., 1] + 0.1073969566 * r[..., 2]
    s = 0.0883024619 * r[..., 0] + 0.2817188376 * r[..., 1] + 0.6299787005 * r[..., 2]
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], axis=-1)


def from_oklab(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return _enc(np.stack([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                          -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                          -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s], axis=-1))


def ring_mask(n):
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    return (np.maximum(np.abs(xx - c), np.abs(yy - c)) / (n / 2.0)) > 0.5


def strength(img):
    """How colourful a painting's own ring is: mean OKLab chroma, and its 3rd and 97th lightness percentiles."""
    lab = to_oklab(np.asarray(img.convert('RGB').resize((256, 256), Image.BOX)).astype(np.float32))[ring_mask(256)]
    return float(np.hypot(lab[:, 1], lab[:, 2]).mean()), float(np.percentile(lab[:, 0], 3)), float(np.percentile(lab[:, 0], 97))


def gains(pics):
    """One colour gain per painting, and the measurements they came from."""
    stats = [strength(p) for p in pics]
    mid = float(np.median([s[0] for s in stats]))
    return [float(np.clip((mid / max(s[0], 1e-4)) ** EVEN, *EVEN_LIMIT)) for s in stats], stats


def depth_field(n, inner, own, outer):
    """A painting's gain at every pixel: its neighbours' at its inner and outer edges, its own between."""
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.maximum(np.abs(xx - c), np.abs(yy - c)) / (n / 2.0)
    t = np.clip(np.log2(np.maximum(r, 0.5) / 0.5), 0, 1)        # 0 at the middle square's edge, 1 at the frame's
    a, b = (inner + own) / 2.0, (own + outer) / 2.0
    return np.where(t < 0.5, a + (own - a) * (t / 0.5), own + (b - own) * ((t - 0.5) / 0.5)).astype(np.float32)


def _sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _near(h, centre, width):
    """Weight for hues (degrees) near `centre`."""
    d = np.degrees(np.angle(np.exp(1j * np.radians(h - centre))))
    return np.exp(-(d / width) ** 2)


def ours(L, a, b, k=OURS):
    """A small, fixed turn of the palette that makes the set ours (the same for every pixel of every painting).

      * the darks lean toward ballpoint indigo instead of brown-black
      * the celadon and sage greens turn a little toward jade
      * the dusty pinks and peaches warm toward apricot, and carry a little more colour
      * the lights are a shade more buttery
    """
    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a))
    green = _near(h, 150, 34)
    pink = _near(h, 22, 34)
    h = h + k * (11 * green + 7 * pink)
    C = C * (1 + k * (0.05 + 0.10 * pink + 0.04 * green))
    hr = np.radians(h)
    a, b = C * np.cos(hr), C * np.sin(hr)
    dark = (1 - _sm(0.16, 0.50, L)) * k
    a = a * (1 - 0.30 * dark) + 0.004 * dark          # indigo: a touch of red, a good deal of blue
    b = b * (1 - 0.30 * dark) - 0.030 * dark
    light = _sm(0.80, 0.96, L) * k
    b = b + 0.008 * light
    return L, a, b


def look(rgb, gain, contrast=CONTRAST, vibrance=VIBRANCE, signature=OURS):
    """rgb: float array (..., 3) 0..255; gain: scalar or array matching rgb[..., 0]."""
    lab = to_oklab(rgb)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    L = L - contrast * np.sin(2 * np.pi * np.clip(L, 0, 1)) / (2 * np.pi)
    chroma = np.hypot(a, b)
    lift = 1 + ((np.asarray(gain) - 1) + vibrance) * np.exp(-((chroma / 0.2) ** 2))   # weak colours take it, strong ones do not
    a, b = a * lift, b * lift
    if signature:
        L, a, b = ours(L, a, b, signature)
    return np.clip(from_oklab(np.stack([L, a, b], axis=-1)), 0, 255)
