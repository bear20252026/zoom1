#!/usr/bin/env python3
"""The score for the film: thirty-five bars, one for each painting.

    python3 tools/music.py            # video/music.wav
    python3 tools/music.py film       # that, then joined to video/silent.mp4 as video/day-in-day-in.mp4

Played on recorded instruments, all CC0: the VSCO 2 Community Edition orchestra and the Versilian Community
Sample Library, as curated in ~/Film-Studio/library/sounds (set SOUNDS to use another copy). Nothing is
synthesised except the room: a little hall reverb.

The film gives each painting three seconds, so the music is in 6/8 with a three-second bar, and its harmony
changes as the picture does. It follows the day the walk goes through:

    bars  1- 3   night garden, moon gate, orchard      vibraphone and glockenspiel over low strings; the harp wakes
    bars  4- 7   valley to the hill village            harp and a flute
    bars  8-14   the hotel, the terrace, the lake      piano joins; a clarinet takes the tune
    bars 15-23   gardens, villa, hall, library, music room   a slow waltz for cello, piano and harp
                 (the cello's tune ends as the painted pianist, harpist and cellist come into view)
    bars 24-30   glasshouse to the bay at evening      everyone: flute over full strings
    bars 31-35   island, pavilion, studio, the frame   down to vibraphone, harp and low strings again

It ends on the chord it began on, and the film ends on the painting it began on, so both can loop.
"""
import json
import os
import subprocess
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDS = os.environ.get('SOUNDS') or os.path.expanduser('~/Film-Studio/library/sounds')
FFMPEG = os.environ.get('FFMPEG') or 'ffmpeg'
SR = 44100
BAR = 3.0                      # seconds: one painting
E = BAR / 6                    # an eighth note
BARS = 35

# name -> (library id, articulation, gain, release seconds, attack seconds)
ORCHESTRA = {
    'piano': ('vcsl-grand-piano-steinway-b', 'Sus', 0.50, 0.9, 0.0),
    'harp': ('vcsl-concert-harp', 'main', 0.62, 1.4, 0.0),
    'glock': ('vcsl-glockenspiel', 'main', 0.20, 1.5, 0.0),
    'vibes': ('vcsl-vibraphone', 'Soft Mallets', 0.55, 1.8, 0.0),
    'violins': ('vsco-violin-section', 'susVib', 0.30, 0.9, 0.35),
    'violas': ('vsco-viola-section', 'susvib', 0.32, 0.9, 0.35),
    'cellos': ('vsco-cello-section', 'susvib', 0.36, 0.9, 0.30),
    'cello': ('vsco-cello-section', 'susvib', 0.52, 0.45, 0.10),
    'bass': ('vsco-solo-contrabass', 'Pizz', 0.55, 0.8, 0.0),
    'flute': ('vsco-flute', 'susvib', 1.05, 0.30, 0.05),
    'clarinet': ('vsco-clarinet', 'susLong', 0.42, 0.30, 0.06),
}


def read(path):
    sr, a = wavfile.read(path)
    a = a.astype(np.float32) / (np.iinfo(a.dtype).max if a.dtype.kind == 'i' else 1.0)
    if a.ndim == 1:
        a = np.stack([a, a], axis=1)
    if sr != SR:
        a = signal.resample_poly(a, SR, sr, axis=0).astype(np.float32)
    return a[:, :2]


def pitch_of(a):
    """Fundamental of a recorded note, as a MIDI number (autocorrelation of a slice after the attack)."""
    x = a[int(0.12 * SR):int(0.62 * SR)].mean(axis=1)
    if len(x) < SR // 5:
        x = a.mean(axis=1)
    x = x - x.mean()
    spec = np.fft.rfft(x * np.hanning(len(x)), 1 << 16)
    ac = np.fft.irfft(np.abs(spec) ** 2)
    lo, hi = int(SR / 4400), int(SR / 28)
    seg = ac[lo:hi]
    # the FIRST strong peak, not the strongest: a pure tone (a glockenspiel bar) repeats just as well after two
    # or four periods as after one, and taking the biggest peak then names it octaves too low
    peaks = np.flatnonzero((seg[1:-1] > seg[:-2]) & (seg[1:-1] >= seg[2:]) & (seg[1:-1] > 0.8 * seg.max())) + 1
    lag = lo + int(peaks[0] if len(peaks) else np.argmax(seg))
    return 69 + 12 * np.log2(SR / lag / 440.0)


class Instrument:
    def __init__(self, name):
        self.name = name
        ident, art, self.gain, self.release, self.attack = ORCHESTRA[name]
        base = os.path.join(SOUNDS, ident)
        with open(os.path.join(base, 'index.json')) as f:
            rows = [s for s in json.load(f)['samples'] if s.get('articulation') == art and s.get('midi') is not None]
        self.rows = [(s['midi'], s.get('dynamic', 0.5), os.path.join(base, s['file'])) for s in rows]
        self.cache = {}
        # The library's note numbers are read off file names, and the two packs count octaves differently, so
        # listen: measure a few notes and move the whole instrument by whole octaves until names and sound agree.
        mid = sorted(self.rows)[len(self.rows) // 3: len(self.rows) // 3 + 5]
        off = np.median([pitch_of(self.load(p)) - m for m, _, p in mid])
        self.octave = int(round(off / 12.0)) * 12
        self.rows = [(m + self.octave, d, p) for m, d, p in self.rows]

    def load(self, path):
        if path not in self.cache:
            self.cache[path] = read(path)
        return self.cache[path]

    def note(self, midi, dur, vel):
        m, d, path = min(self.rows, key=lambda r: (abs(r[0] - midi), abs(r[1] - vel)))
        a = self.load(path)
        ratio = 2 ** ((midi - m) / 12.0)
        n = int(min(len(a) / ratio, (dur + self.release + 0.05) * SR))
        idx = np.arange(n) * ratio
        i0 = np.minimum(idx.astype(np.int64), len(a) - 2)
        f = (idx - i0)[:, None].astype(np.float32)
        out = a[i0] * (1 - f) + a[i0 + 1] * f
        t = np.arange(n) / SR
        env = np.ones(n, np.float32)
        if self.attack:
            env *= np.clip(t / self.attack, 0, 1) ** 1.5
        rel = np.clip((t - dur) / self.release, 0, 1)
        env *= (1 - rel) ** 2
        env[-64:] *= np.linspace(1, 0, 64)
        return out * env[:, None] * self.gain * (0.35 + 0.65 * vel)


class Mix:
    def __init__(self, seconds):
        self.buf = np.zeros((int((seconds + 6) * SR), 2), np.float32)
        self.band = {}

    def play(self, name, midi, start, dur, vel=0.6, pan=0.0):
        if name not in self.band:
            self.band[name] = Instrument(name)
        a = self.band[name].note(midi, dur, vel)
        i = int(start * SR)
        if i < 0 or i >= len(self.buf):
            return
        a = a[:len(self.buf) - i]
        self.buf[i:i + len(a), 0] += a[:, 0] * min(1.0, 1 - pan)
        self.buf[i:i + len(a), 1] += a[:, 1] * min(1.0, 1 + pan)


# ---- the piece ---------------------------------------------------------------------------------------------------
D, E_, Fs, G, A, B, Cs = 62, 64, 66, 67, 69, 71, 73          # D major, from the D above middle C
CHORDS = {                                                    # name -> (bass, the notes of the chord from low to high)
    'D': (38, [50, 57, 62, 66, 69]), 'D9': (38, [50, 57, 64, 66, 69]), 'D/F#': (42, [54, 57, 62, 66, 69]),
    'A': (45, [52, 57, 61, 64, 69]), 'A/C#': (49, [52, 57, 61, 64, 69]), 'A7sus': (45, [52, 57, 62, 64, 67]),
    'A7': (45, [52, 55, 61, 64, 67]), 'Bm7': (47, [54, 57, 62, 66, 69]), 'Bm': (47, [54, 59, 62, 66, 71]),
    'G': (43, [50, 55, 59, 62, 67]), 'Gmaj7': (43, [50, 54, 59, 62, 66]), 'Em7': (40, [52, 55, 59, 62, 67]),
    'Em9': (40, [52, 55, 59, 62, 66]),
}
HARMONY = ['D9', 'Bm7', 'Gmaj7',                                             # 1-3   night into first light
           'D', 'A/C#', 'Bm7', 'G',                                           # 4-7   valley, village
           'G', 'D/F#', 'Em7', 'A7sus', 'D', 'Bm7', 'Gmaj7',                  # 8-14  hotel, terrace, lake
           'A', 'D', 'G', 'D/F#', 'Em7', 'Bm', 'G', 'A7', 'D',                # 15-23 villa: the waltz
           'Bm7', 'G', 'D', 'A', 'Bm7', 'Gmaj7', 'A7sus',                     # 24-30 glasshouse to the bay
           'Bm7', 'Gmaj7', 'Em9', 'A7sus', 'D9']                              # 31-35 island, studio, the frame
# tunes: bar -> [(midi, length in eighths)], a 0 is a rest
TUNE = {
    'vibes': {1: [(78, 3), (81, 3)], 2: [(74, 3), (83, 3)], 3: [(79, 3), (83, 2), (81, 1)],
              31: [(78, 3), (74, 3)], 32: [(71, 3), (74, 3)], 33: [(78, 3), (76, 3)], 34: [(76, 3), (69, 3)], 35: [(74, 6)]},
    'flute': {4: [(69, 2), (74, 1), (78, 3)], 5: [(76, 2), (73, 1), (69, 3)], 6: [(71, 2), (74, 1), (78, 2), (76, 1)],
              7: [(74, 3), (71, 2), (69, 1)],
              24: [(78, 2), (83, 1), (81, 3)], 25: [(79, 2), (78, 1), (74, 3)], 26: [(81, 3), (78, 2), (74, 1)],
              27: [(76, 2), (73, 1), (76, 3)], 28: [(74, 2), (78, 1), (83, 3)], 29: [(81, 2), (79, 1), (78, 3)],
              30: [(76, 3), (74, 3)]},
    'clarinet': {8: [(67, 2), (71, 1), (74, 3)], 9: [(69, 3), (66, 2), (69, 1)], 10: [(67, 2), (71, 1), (76, 3)],
                 11: [(74, 2), (73, 1), (69, 3)], 12: [(66, 2), (69, 1), (74, 3)], 13: [(78, 2), (74, 1), (71, 3)],
                 14: [(71, 2), (69, 1), (67, 2), (69, 1)]},
    'cello': {15: [(64, 3), (61, 2), (64, 1)], 16: [(66, 3), (69, 3)], 17: [(67, 2), (66, 1), (64, 2), (62, 1)],
              18: [(57, 3), (62, 3)], 19: [(64, 2), (67, 1), (71, 3)], 20: [(69, 2), (66, 1), (62, 3)],
              21: [(59, 2), (62, 1), (67, 3)], 22: [(67, 2), (64, 1), (61, 3)], 23: [(62, 6)]},
}
ARP = [0, 1, 2, 3, 4, 3]                                      # up through the chord and back a step, in eighths


def compose():
    mix = Mix(BARS * BAR)
    for b, name in enumerate(HARMONY, start=1):
        t0 = (b - 1) * BAR
        bass, notes = CHORDS[name]
        waltz, full, night = 15 <= b <= 23, 24 <= b <= 30, b <= 3 or b >= 31
        # strings: a held chord, re-bowed each bar and overlapping the next
        level = 0.22 if b <= 2 else 0.3 if b == 3 else 0.5 if b <= 7 else 0.5 if b <= 14 else 0.5 if b <= 23 else 0.9 if b <= 30 else 0.45 if b <= 33 else 0.32
        mix.play('cellos', bass + 12 if bass < 43 else bass, t0, BAR + 0.5, level, -0.25)
        mix.play('violas', notes[1], t0, BAR + 0.5, level * 0.9, 0.2)
        if b >= 4:
            mix.play('violins', notes[3] + (12 if full else 0), t0, BAR + 0.5, level * (0.9 if full else 0.7), -0.1)
        if full:
            mix.play('violins', notes[2] + 12, t0, BAR + 0.5, level * 0.6, 0.3)
        # harp: the running eighths (it wakes in bar 2, rests under the waltz's piano, and returns)
        if 2 <= b <= 14 or b >= 24:
            soft = 0.38 if b <= 3 else 0.85 if b <= 7 else 0.6 if not night else 0.45
            for i, k in enumerate(ARP):
                mix.play('harp', notes[k] + (12 if b >= 24 and not night else 0), t0 + i * E, E * 2.5, soft * (1.0 if i in (0, 3) else 0.78), 0.3)
        if waltz:                                             # the harp marks the two beats of the bar instead
            for i in (0, 3):
                for k, n in enumerate(notes[1:4]):
                    mix.play('harp', n + 12, t0 + i * E + k * 0.045, E * 2.5, 0.45, 0.3)
        # piano: joins at the hotel; in the waltz it is the left hand and the lilt
        if 8 <= b <= 14 or full:
            for i, k in enumerate(ARP):
                mix.play('piano', notes[(k + 2) % 5] + (0 if k + 2 < 5 else 12), t0 + i * E, E * 2, (0.36 if i else 0.5) * (1.25 if full else 1.0), -0.2)
            mix.play('piano', bass, t0, BAR * 0.9, 0.5, -0.2)
        if waltz:
            mix.play('piano', bass, t0, BAR * 0.9, 0.48, -0.2)
            for i in (1, 2, 4, 5):
                for n in notes[1:4]:
                    mix.play('piano', n, t0 + i * E, E * 0.9, 0.2 if i in (2, 5) else 0.26, -0.2)
            mix.play('piano', bass + 7, t0 + 3 * E, E * 2.5, 0.34, -0.2)
        # the bass, plucked, on the bar and (when everyone is in) on its second beat
        if 8 <= b <= 30:
            mix.play('bass', bass - (12 if bass >= 40 else 0), t0, 1.2, 0.6, 0.0)
            if full:
                mix.play('bass', bass - (12 if bass >= 40 else 0) + 7, t0 + 3 * E, 1.0, 0.45, 0.0)
        # glockenspiel: a few stars at night, and one on each new section
        if night:
            mix.play('glock', notes[4] + 24, t0 + 4 * E, 1.0, 0.3, 0.45)
            if b in (1, 3, 31, 35):
                mix.play('glock', notes[2] + 24, t0 + 1 * E, 1.0, 0.25, -0.45)
        elif b in (4, 8, 15, 24):
            mix.play('glock', notes[2] + 24, t0, 1.2, 0.35, 0.4)
    for name, bars in TUNE.items():
        pan = {'vibes': 0.1, 'flute': 0.15, 'clarinet': -0.15, 'cello': 0.05}[name]
        for b, line in bars.items():
            t = (b - 1) * BAR
            for midi, eighths in line:
                if midi:
                    mix.play(name, midi, t, eighths * E * (0.96 if name != 'vibes' else 1.6), 0.72, pan)
                t += eighths * E
    return mix


def master(buf, seconds):
    # a hall: decaying noise, a touch darker as it dies
    rng = np.random.default_rng(7)
    n = int(2.6 * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-t / 0.55)[:, None]
    ir = signal.lfilter([0.25], [1, -0.75], ir, axis=0)
    ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    wet = np.stack([signal.fftconvolve(buf[:, c], ir[:, c])[:len(buf)] for c in (0, 1)], axis=1)
    out = buf * 0.84 + wet * 0.26
    out = out[:int((seconds + 0.001) * SR)]
    fade = int(1.6 * SR)                                      # the last chord dies away with the last frame
    out[-fade:] *= (np.linspace(1, 0, fade) ** 1.5)[:, None]
    out[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
    out = out / np.abs(out).max() * 1.25
    return np.tanh(out) / np.tanh(1.25) * 0.94                # gentle limiting of the peaks


def main():
    os.makedirs(os.path.join(ROOT, 'video'), exist_ok=True)
    mix = compose()
    for name, ins in sorted(mix.band.items()):
        print('  %-9s %-28s moved %+d octave%s' % (name, ORCHESTRA[name][0], ins.octave // 12, '' if abs(ins.octave) == 12 else 's'))
    out = master(mix.buf, BARS * BAR)
    wav = os.path.join(ROOT, 'video', 'music.wav')
    wavfile.write(wav, SR, (out * 32767).astype(np.int16))
    print('wrote video/music.wav: %.1f s, peak %.2f, rms %.3f' % (len(out) / SR, np.abs(out).max(), np.sqrt((out ** 2).mean())))
    if len(sys.argv) > 1 and sys.argv[1] == 'film':
        import tempfile
        silent, film = os.path.join(ROOT, 'video', 'silent.mp4'), os.path.join(ROOT, 'video', 'day-in-day-in.mp4')
        # two passes at a fixed size: about 75 MB for the lap (a repository will not take a file over 100 MB)
        log = os.path.join(tempfile.mkdtemp(), 'pass')
        video = ['-c:v', 'libx264', '-preset', 'slower', '-b:v', '5500k', '-pix_fmt', 'yuv420p', '-passlogfile', log]
        subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', silent] + video + ['-pass', '1', '-an', '-f', 'null', os.devnull], check=True)
        subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', silent, '-i', wav] + video +
                       ['-pass', '2', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', film], check=True)
        print('wrote video/day-in-day-in.mp4: %.1f MB' % (os.path.getsize(film) / 1e6))


if __name__ == '__main__':
    np.seterr(all='ignore')
    main()
