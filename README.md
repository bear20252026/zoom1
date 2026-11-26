# Day In, Day In

A painting with no bottom: an endless walk into one painted world, round one whole day. You begin in a
walled garden in the last of the night, white flowers under a full moon; step through a moon gate into an
orchard in blossom at first light, and down into a valley at dawn where a painter stands at an easel; go under
a viaduct and up to a hill village, into a small hotel, through a bedroom and out onto its terrace above a
lake; cross the gardens to a villa and go through its hall, library and music room, out through a glasshouse
into a courtyard, across a market square and down a harbour street to the bay in the evening; over the water
to an island at dusk, and into the painter's studio at night. On the studio wall, in a frame, hangs the night
garden you began in.

Thirty-five paintings, each one the far distance of the one before it. Everything in them is still: a
painting cannot move, so nothing is caught in the middle of moving.

**See it:** <https://kevintngo.github.io/zoom1/> · **the film:** [`video/day-in-day-in.mp4`](video/day-in-day-in.mp4)
(one lap, 1:45, square, with a score played on recorded CC0 instruments).

## Run it

Any static file server, from this folder:

```sh
python3 -m http.server 7813
```

then open <http://localhost:7813>. No build step and no dependencies: plain ES modules and WebGL 2.

Scroll, drag or press ↑ ↓ to walk in or back out; left alone it drifts slowly inward. Space rests, `f` is full
screen. With *reduce motion* set, nothing moves until you move it. The page has no sound, and no writing after
the title card.

## How it works

| where | what |
| --- | --- |
| `index.html`, `src/style.css` | the page: one canvas, and a title card on torn paper that lifts away |
| `src/app.js` | the loop: input, the speed of the walk, the clock |
| `src/zoom.js` | the walk: the ring of paintings, drawn as a stack of three (each half the size of the one under it), streamed in sharp as you approach; and the movement inside them |
| `src/paper.js` | the last pass: a restrained sharpen, then the tooth of the paper over everything |
| `src/gl.js` | small WebGL helpers and the noise the shaders share |
| `src/story.js` | written by `tools/export.py`: the paintings in order |
| `art/frames/{xl,hi,md,lo}/` | the paintings at 4096, 2048, 1024 and 512 px (the page picks by screen size) |
| `art/motion/` | one small map per painting: where it has wind, water, drifting cloud and light |
| `art/letters/`, `art/ui/` | the title's brush lettering (alpha masks) and the torn paper |
| `video/day-in-day-in.mp4` | the film: one lap of the walk with its score |
| `tools/` | everything that made the art, the film and the music (see below) |
| `masters/` | the full-size originals and every intermediate: several gigabytes, kept out of the repository and not needed to run the page |

**The walk.** Position is a real number of paintings. At position `k + f` the screen shows painting `k`
enlarged `2^f`, with `k+1` at half that size over its middle and `k+2` at a quarter. Because the middle half
of every painting *is* the next painting, nothing changes on screen when `k` ticks over.

**Why it reads as one place.** Every step in the chain is one of two kinds: the same scene widening (the
villa, then the villa in its garden, then the garden on its hillside), or a step back through an opening (a
door, an arch, the gap between two rows of houses) so that the picture so far becomes the view through it.
Nothing is ever "revealed to be inside" something else, except once: the night garden is the picture on the
studio wall, which is what closes the loop.

**The paintings move, in code only.** A fragment shader displaces and brightens the painting where its motion
map says to: leaves and flowers in the wind; ripples and glints on water; a slow drift in clouds and
smoke; a flicker in lamps and lanterns. It takes one displaced sample of the painting, never a blend of two,
so nothing is softened by moving, and movement is held to zero where two paintings overlap, so the joins stay
exact. The maps were made once, offline, by a segmentation model asked for "water", "tree", "lantern" and so on.

## How the paintings were made

All of the art is from GPT Image 2.6 Sunburst on fal (`openai/gpt-image-2.6/sunburst/text-to-image` and
`…/edit`), built from the inside out by `tools/chain.py`:

1. A style guide (`masters/card.png`: swatches and nine small studies) and `g0`, the studio wall with an empty
   frame, are painted from prompts.
2. For each next painting, the previous one is set at half size in the middle of a blank 2880 px sheet and
   the model is asked to paint what surrounds it, with the style guide beside it as a second image so that
   every step is held to the same colour and brushwork (`tools/story.py` holds the prompts: the story).
3. The model never returns the middle where it was put: it comes back shifted and stretched by a few per
   cent. `tools/register.py` finds it (patch matching at three scales) and the result is pulled back until
   it lies exactly under the original.
4. `tools/stitch.py` takes off the few levels of brightness the model adds, matches what is left at the join,
   and cuts the two together along the closed path where they agree best, so that anything the model let
   reach into the kept square is kept whole. The inner painting's rim is then replaced by the outer
   painting's version of it, which makes the middle half of the outer one exactly the inner one at half size.
5. `tools/export.py` closes the loop (the night garden goes into the studio's empty frame), has every painting
   enlarged 2x by a restoration model (SeedVR2 on fal), grades the set lightly so it hangs together
   (`tools/grade.py`), and writes the four sizes.
6. `tools/motion.py` asks a segmentation model (SAM 3 on fal) where the moving things are and writes the maps.

The look starts from a debt to the painter Yukiko Noritake, above all in colour: large calm areas of ivory,
celadon, sage, dusty rose and pale peach; masses of very deep forest green and brown-black; aqua water; and
pure red kept as an accent (a sail, a flower, the painter's coat). Also opaque paint with no outlines, foliage
as bold patterned masses, buildings seen frontally like stage sets, and tiny lively figures. The prompts
describe those qualities; they do not name her or describe any of her pictures. The grade then turns that
palette a few degrees to make it ours (`OURS` in `tools/grade.py`): indigo in the darks, a little toward jade
in the greens, apricot in the pinks. (A first, brighter attempt in
hot coral and teal is kept in `masters/_v2_bright/`.)

**Sharpness.** The outermost painting on screen is enlarged by up to 2x as you walk in, so the page takes
the 4096 px set for any window over about 1100 device pixels wide (phones and small tablets stop at 2048), and
shows 1024 px versions, loaded in the background, wherever a sharp one has not arrived yet. Each painting is
sharpened in the shader in proportion to how far it is enlarged, never past the lightest or darkest of the
neighbouring texels, so edges firm up without halos.

## The film

`video/day-in-day-in.mp4` is one whole lap at three seconds a painting, 1080 x 1080, with nothing written on
it. It begins and ends on the night garden filling the frame, so it loops.

- **Picture.** Nothing is screen-recorded. With `?capture=1080&record=1` the page renders one exact frame at a
  time, at a stated depth and animation time, and posts the pixels to `tools/video.py`, which pipes them into
  ffmpeg.
- **Music.** `tools/music.py` is the score and the player: thirty-five bars of 6/8, one three-second bar to a
  painting, so the harmony changes as the picture does. Vibraphone and glockenspiel for the night garden, harp
  and flute for the valley, a clarinet over piano at the hotel, a slow waltz for cello, piano and harp through
  the villa (the cello's tune ends as the painted pianist, harpist and cellist come into view), full strings
  down to the bay, and vibraphone again for the studio. Every note is a recording: the VSCO 2 Community Edition
  orchestra and the Versilian Community Sample Library, both CC0. Only the hall reverb is made in code.

```sh
python3 tools/video.py                    # serves the site on :7841 and waits for frames
#   then open http://localhost:7841/?capture=1080&record=1 in a browser -> video/silent.mp4
python3 tools/music.py film               # video/music.wav, then video/day-in-day-in.mp4
```

### Making it again

Needs `FAL_KEY` in the environment and Python 3 with Pillow, NumPy and SciPy.

```sh
python3 tools/chain.py card               # the style guide
python3 tools/chain.py seed -n 2          # two candidates for the studio wall; keep one with: chain.py accept 0 1
python3 tools/chain.py run 1 34           # the other thirty-four, each around the last (about two minutes each)
python3 tools/chain.py step 8 -n 2        # or one step with candidates to choose from, then: chain.py accept 8 1
python3 tools/export.py ring              # close the loop
python3 tools/motion.py masks && python3 tools/motion.py build
python3 tools/export.py                   # upscale, grade, write art/frames and src/story.js
python3 tools/lettering.py make && python3 tools/lettering.py cut
python3 tools/extras.py make && python3 tools/extras.py cut
```

Redoing step `K` from scratch means redoing every step after it, since each is painted around the one before.
But one painting can be repainted on its own: `python3 tools/chain.py repaint K` keeps the picture in its
middle and a band along its outer edge and paints only what lies between (the model holds both sides in place
to within a pixel or two), and `chain.py redo K+1` then takes the new painting into the next one's middle. Changing only
how the pieces are joined does not: `tools/rejoin.sh` joins the whole chain again from the model outputs on
disk in under a minute, and `python3 tools/qa.py` prints, per painting, how busy the picture is along each cut
compared with beside it (about 1 or less means the cut cannot be seen) and the tones of each ring (to catch a
chain that is fading or burning). `python3 tools/motion.py sheet` shows every motion map over its painting.
