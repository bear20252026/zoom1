"""Day In, Day In: the story, as prompts.

One walk through one painted world, round one whole day. You begin in a walled garden in the last of the
night, white flowers under a full moon; step through a moon gate into an orchard in blossom at first light,
and down into a valley at dawn where a painter stands at an easel; go under a viaduct and up to a hill
village, into a small hotel, through a bedroom and out onto its terrace above a lake; cross the gardens to a
villa and go through its hall, library and music room, out through a glasshouse into a courtyard, across a
market square and down a harbour street to the bay in the evening; over the water to an island at dusk, and
into the painter's studio at night. On the studio wall, in a frame, hangs the night garden you began in.

Everything in it is still. A painting cannot move, so nothing in these is caught in the middle of moving: no
washing on a line, no train in steam, nobody running.

The picture is built from the INSIDE OUT. g0 is the innermost painting (the studio wall with its frame); every
later step shrinks the picture so far to half size, sets it in the middle of a fresh sheet and paints what
lies around it. Each step is one of two kinds, and that is what makes the walk feel continuous:

    wider     the same scene, more of it: nothing is revealed, the view just opens out
    doorway   we step back through an opening (a door, an arch, the gap between two rows of houses) and the
              picture so far becomes the view through it

The outermost painting, the night garden, is the picture in the frame of the innermost, so the walk never ends.

The look is ours, with a debt to the painter Yukiko Noritake, above all in colour: large calm areas of ivory,
celadon, sage, dusty rose and pale peach; masses of very deep forest green and brown-black; aqua water; and
pure red kept as an accent. Also opaque paint with no outlines, foliage as bold patterned masses, buildings
seen frontally like stage sets, and tiny lively figures. None of her pictures or compositions is described.
"""

MEDIUM = (
    "Medium and style: an original painting in opaque gouache and acrylic on smooth paper. There are no outlines "
    "anywhere: every form is a flat, clean-edged shape of opaque matte paint, modelled with only two or three "
    "closely related tones laid in soft, slightly streaky brushstrokes. Perspective is simplified and a little "
    "flattened, like a stage set; buildings are seen frontally. The picture is composed of large calm areas of a "
    "single colour that give it air, with detail gathered in a few places rather than spread everywhere. Plants are "
    "designed as bold patterned masses: scalloped tree crowns, fans of palm, dark columns of cypress, each leaf a "
    "single brushstroke; flowers are large soft blooms. A few tiny, simply painted figures and animals (some "
    "strokes each, no facial features) give scale and life.\n"
    "Colour is the heart of it, and it is restrained and elegant, never loud. Large calm areas of warm ivory and "
    "cream; soft celadon, sage and mint green; dusty rose, salmon and pale peach; pale powder blue. Set against "
    "them, masses of very deep forest green and a dark chocolate brown that is nearly black. Water is clear aqua "
    "and turquoise with white brushstrokes. Sunlit walls are warm peach-orange or ochre. Pure vermilion red is the "
    "one bright accent and is used sparingly: a sail, a flower, an awning, a coat. Mid-tones are slightly milky and "
    "matte. No hot magenta or fuchsia, no saturated sunset pink, no neon, no candy colours, no acid green, nothing "
    "grey or muddy; and not washed out either: the darks are truly dark and the red is truly red.\n"
    "No black outlines, no ink lines, no hatching, no photographic realism, no 3D render, no airbrushed gradients. "
    "No text, letters, numbers, signature, logo or border anywhere."
)

CARD = (
    "A painter's sample board: one sheet showing a way of painting, to be used as a style and colour guide. Across "
    "the top, a row of sixteen flat square swatches of opaque matte paint, in this order: ivory, warm cream, pale "
    "peach, dusty rose, salmon, peach-orange, ochre, vermilion red, mint, celadon, sage, fresh leaf green, very "
    "deep forest green, aqua, powder blue, chocolate brown-black. Below them, nine small separate studies arranged "
    "in a neat three-by-three grid on the ivory ground, each painted in that way and in those colours: an "
    "umbrella pine and a cypress in deep forest green against a calm cream sky; aqua water with white "
    "brushstrokes and one red-sailed boat; a peach-orange wall with sage shutters; large pale pink, cream and red "
    "blooms against a chocolate brown-black ground; a celadon wall with a dark brown shelf and a cream vase; a "
    "lemon tree in a terracotta pot against ivory; tiny figures, one in a red coat, with a white dog on a cream "
    "path; hills in flat layers of powder blue and sage under a pale peach sky; a floor of cream and celadon "
    "chequers.\n\n"
)

GUIDE = (
    " The second image is NOT part of the painting and nothing it shows may appear in the result: it is only a guide "
    "to the way of painting (flat opaque shapes, no outlines, the brushwork, large calm areas) and to the colours: "
    "use its palette and its restraint."
)

EXTEND = (
    "The first image is an unfinished painting. The finished square in the middle is one part of a much larger "
    "painting; the plain blank area around it has not been painted yet. Complete the painting by filling the whole "
    "blank surrounding area, right up to all four edges of the image. Do not change, move or repaint the central "
    "square: it must stay exactly where it is, in the exact centre of the image, the same size, not shifted up, down "
    "or sideways and not enlarged, even if that means things in the new area run off the edge of the image. Every "
    "shape, colour and brushstroke that reaches the edge of the central square must carry on outward without any "
    "break, border, outline, gap or change of style, so that nobody could tell where the old part ends and the new "
    "part begins: there must be no visible square. The new area is painted by the same hand, in the same light and "
    "in the same colours as the middle." + GUIDE + "\n\nWhat the newly painted surrounding area shows: "
)

SEED = (
    "A painting of one wall of a painter's studio at night, seen straight on, lit by a warm lamp. Exactly in the "
    "centre of the image hangs one large SQUARE picture frame. Inside the frame there is no picture yet: only a "
    "perfectly blank, flat, even, warm ivory mount board with no marks, no shading, no texture and no shadow on it. "
    "The blank ivory square is big: it covers the central three fifths of the image's width and of its height, and "
    "it is perfectly square, upright and centred. Nothing overlaps it. The frame around it is a fairly narrow "
    "moulding of ochre gold with a simple carved leaf pattern. Around the frame, filling the rest of the image to "
    "its edges: the wall, painted a dark chocolate brown that is nearly black, with a pattern of large leaves in "
    "very deep forest green; at the left a tall monstera plant in a dusty-rose pot; at the right a dark wooden "
    "shelf with jars of brushes and pots of paint in cream, celadon, powder blue and one red; along the bottom the "
    "edge of a dark work table with a vase of big pale pink, cream and red blooms, a palette with dabs of colour "
    "and a sleeping ginger cat; at the upper right a brass lamp throwing a soft pool of cream light across the "
    "wall.\n\n"
)

WIDER = "This step only widens the view: it is the same scene, the same place and the same light, with more of it now in sight. "
BACK = "In this step we have stepped back through an opening, and the picture so far becomes the view through it. "
OPENING = (
    " The opening is large and exactly centred: its inner edge lies just outside the central square on every side "
    "(the opening is about three fifths as wide and as tall as the image), so the whole central square is seen "
    "through it and nothing covers any of it."
)
WALKER = " Somewhere in the new area, small: the painter, a little figure in a red coat, with a small white dog."

# (name, kind, what the surrounding ring shows). Generation order: g1 surrounds g0, g2 surrounds g1, ...
STEPS = [
    ("picture", "seed", None),

    ("studio", "wider", WIDER +
     "The central square is part of the far wall of a painter's studio at night; now the whole room is in view, "
     "with the framed picture hanging in the middle of the far wall. Above: the ceiling with a dark beam, a round "
     "cream paper lantern and trailing plants in hanging pots. At the left: a tall window with long dusty-rose "
     "curtains and deep blue-green night outside, and in front of it an easel holding a blank canvas. At the "
     "right: dark shelves with jars, bottles, rolled papers, a cactus in a pot and a blue-and-white vase. Below: "
     "the work table continues, and in front of it a floor of pale terracotta tiles with a cream rug bordered in "
     "red, a small white dog asleep on the rug, a red coat thrown over a chair, a stool, and canvases stacked "
     "with their blank backs showing. The walls stay a calm dark chocolate brown-black with deep forest-green "
     "leaves; lamplight falls in soft cream pools. Palette: chocolate brown-black, forest green, cream, dusty "
     "rose, celadon, and the red coat as the one accent."),

    ("doors", "doorway", BACK +
     "We now stand outside on a veranda at dusk and see the lamplit studio through its wide-open glass double "
     "doors." + OPENING + " Around the opening: the two door leaves, glazed and painted sage green, folded back "
     "to the left and right; a fanlight above; the outside wall of the little house, a large calm area of pale "
     "peach-pink stucco in soft evening shade, with a climbing rose bearing a few red blooms on one side and "
     "white jasmine on the other; two hanging lanterns glowing cream; in front, the veranda floor of chequered "
     "cream and celadon tiles with warm light spilling across it from the doorway; a lemon tree in a terracotta "
     "pot on each side, a watering can, a pair of slippers. Palette: pale peach wall, sage doors, cream light, "
     "forest-green leaves, celadon tiles, a few reds."),

    ("pavilion", "wider", WIDER +
     "The whole little house is in view: a one-storey garden pavilion with a hipped terracotta roof, a round attic "
     "window and a chimney with a thread of smoke, its open doors in the middle of its front. It stands in a "
     "clearing among tall umbrella pines and cypress painted as dense masses of very deep forest green; a few "
     "tall pale-pink foxgloves and powder-blue agapanthus grow by the walls; a string of small cream lanterns "
     "hangs between the trees; a path of ivory stepping stones leads from the doors down to the bottom edge of "
     "the image across a lawn of fresh leaf green; a white heron stands in the grass. Above the roof the evening "
     "sky is one large calm area: pale peach low down, rising through cream to powder blue, almost empty, with "
     "one star and a thin crescent moon." + WALKER + " Palette: deep forest-green trees, pale peach and "
     "powder-blue sky, peach walls, leaf-green lawn, cream lantern points."),

    ("island", "wider", WIDER +
     "The clearing turns out to be on a small island, now seen whole from across the water in the evening, the "
     "pavilion among its pines in the middle. Round it runs the island's shore of pale rocks with pines leaning "
     "out over the water; at the bottom centre a little wooden jetty with a lantern on a pole and a moored "
     "rowing boat painted red; all around, the still lake as one large calm area of celadon and aqua with white "
     "horizontal brushstrokes and soft reflections, a few lily pads and two white swans; far to the left and "
     "right, hills in flat layers of sage and powder blue; above, the calm evening sky, pale peach at the horizon "
     "rising to powder blue, with two long dusty-rose clouds." + WALKER + " Palette: celadon and aqua water, "
     "pale peach and powder-blue sky, forest-green island, cream rocks, one red boat."),

    ("bay", "wider", WIDER +
     "The island is small in the middle of a wide bay in the evening. Beyond it, mountains in flat layers of "
     "powder blue and sage; a huge calm sky, a broad field of pale peach and cream with a few long dusty-rose "
     "clouds; three red-sailed fishing boats and a small white steamer trailing smoke; on the left a headland "
     "with a white chapel and dark cypress; on the right the end of a harbour wall with a small beacon. The water "
     "is aqua and celadon with white brushstrokes. Along the bottom of the image, nearest us, the edge of a "
     "harbour quay in cream stone: bollards, coiled ropes, nets, a crate of oranges, two cats, and moored boats "
     "painted red and sage. A few gulls." + WALKER + " Palette: pale peach and cream sky, aqua water, powder-blue "
     "mountains, cream stone, vermilion sails as the accent."),

    ("street", "doorway", BACK +
     "We are now part of the way up a steep, narrow street in a harbour town, and the bay is the view at the "
     "bottom of the street, seen between the houses." + OPENING + " The opening here is the gap between the two "
     "rows of houses, with the street's own steps below it and the calm evening sky above it. Around it: tall "
     "narrow houses on both sides, their walls large calm areas of ivory, pale peach and dusty rose, with sage "
     "and powder-blue shutters, a few balconies with red geraniums, a wrought-iron lamp on a bracket, and one "
     "awning striped red and cream without any lettering. Nothing hangs across the street: no washing lines, no "
     "cloth, no bunting; above the view there is only the sky between the roofs, pale peach and cream, with one "
     "long dusty-rose cloud. Below the view, wide cream stone steps going down, two cafe tables with tiny seated "
     "people, a fruit stall, a sleeping dog; a spray of dusty-pink bougainvillea on one wall; one side of the "
     "street in warm evening light, the other in soft blue-grey shade. Everything is still." + WALKER +
     " Palette: ivory, pale peach and dusty rose walls, sage and powder-blue shutters, cream steps, red accents."),

    ("square", "wider", WIDER +
     "The street opens off a market square, which is now in view all round it, the mouth of the street in the "
     "middle of the far side. In the square: market stalls under cream and red-striped umbrellas, piled with "
     "fruit, flowers and fish; a round stone fountain; cafe terraces with tiny people; on the left a white church "
     "front with a bell tower; plane trees with scalloped crowns of deep forest green; pigeons; a child with a red "
     "balloon. The houses round the square are large calm areas of ivory, pale peach and dusty rose under "
     "terracotta roofs; the paving is cream; long soft shadows in blue-grey; above the roofs the calm evening sky, "
     "cream and pale peach." + WALKER + " Palette: ivory and peach houses, cream paving, forest-green trees, "
     "terracotta roofs, red umbrellas and balloon."),

    ("arch", "doorway", BACK +
     "We have stepped back through a stone archway, and the square is seen through it: a tall round-topped arch "
     "in a thick wall." + OPENING + " Around the arch: the wall of a shady arcade, a large calm area of ivory "
     "plaster with a painted frieze of sage leaves; a wrought-iron lamp above the arch; a little dark ivy; on "
     "each side a big terracotta pot of oleander with pale pink and red flowers; in front a floor of patterned "
     "tiles in celadon, cream and a little red; a bicycle leaning on the wall; a cat. Cool, soft reflected light. "
     "Palette: ivory, sage, celadon, terracotta, forest green, a little red."),

    ("courtyard", "wider", WIDER +
     "The whole courtyard is in view: a square cloister with two storeys of arcades, round arches on slender "
     "columns, on every side, in ivory and pale peach; the arch we looked through is the middle one on the far "
     "side. Nearer us, in the middle of the courtyard, a round fountain with a celadon tiled basin and goldfish; "
     "four orange trees in big pots, their crowns deep forest green with orange fruit; the floor of celadon and "
     "cream tiles; two small tables with people drinking, a waiter, a peacock, pigeons; on the upper gallery, "
     "potted plants and a line of white washing; above, a square of calm powder-blue sky with two cream clouds, "
     "edged by terracotta roof tiles." + WALKER + " Palette: ivory and pale peach arcades, celadon tiles, forest "
     "green, orange fruit, powder-blue sky."),

    ("glass doors", "doorway", BACK +
     "We have stepped back inside a great glasshouse, and the courtyard is seen through its tall open doors of "
     "white-painted iron and glass." + OPENING + " Around the doors: the glasshouse wall of slender white columns "
     "and arched panes; huge palms, banana leaves, tree ferns and monsteras crowding in from both sides and from "
     "above, each leaf one bold flat shape, in greens from very deep forest green to sage and mint; a hanging "
     "basket trailing red flowers; a path of chequered cream and celadon tiles leading to the doors; two wicker "
     "chairs; a red parrot on a perch; a gardener with a watering can. Soft, pale green light. Palette: forest "
     "green, sage, mint and celadon, white ironwork, cream tiles, red as the accent."),

    ("glasshouse", "wider", WIDER +
     "The whole inside of the great glasshouse is in view, under its arched glass roof and central dome of white "
     "iron ribs, the open doors small in the middle of the far end. Tall palms reach the roof; a long rectangular "
     "pool of aqua water with white water lilies, round lily pads and a few red fish runs down the middle toward "
     "us, with a chequered cream and celadon path on each side; stone urns, a white heron, a bench; a few tiny "
     "people strolling; pale sunlight slanting through the roof and falling in soft stripes." + WALKER +
     " Palette: every green from mint to deep forest green, white ribs, aqua pool, cream paths, red fish."),

    ("music door", "doorway", BACK +
     "We have stepped back through a tall doorway into a music room, and the glasshouse is seen through the open "
     "double doors at the far end of the room." + OPENING + " Around the doorway: the room's far wall, a large "
     "calm area of dusty rose with ivory panelling and an ivory door case; on the left a grand piano in chocolate "
     "brown-black with its lid up and a pianist playing; on the right a golden harp and a sage-green sofa; a tall "
     "cream vase of flowers on each side of the door; a floor of honey-ochre parquet with a cream carpet bordered "
     "in red; a small dog asleep under the piano. Soft daylight. Palette: dusty rose walls, ivory, chocolate "
     "brown-black piano, sage, ochre floor, a red border."),

    ("music room", "wider", WIDER +
     "The whole music room is in view: tall mirrors in ochre-gold frames, a chandelier, long powder-blue curtains "
     "at tall windows on the left letting in pale daylight, framed pictures that show only abstract shapes of "
     "colour, a cello player beside the piano, two tiny couples dancing, a row of small gilt chairs along the "
     "wall, an ivory ceiling with a painted garland, the ochre parquet running toward us." + WALKER + " Palette: "
     "dusty rose and ivory, powder-blue curtains, ochre gold, chocolate brown, small reds."),

    ("library door", "doorway", BACK +
     "We have stepped back through a doorway into a library, and the music room is seen through the open doors at "
     "the far end of it." + OPENING + " Around the doorway: a wall of tall bookcases in dark chocolate brown, "
     "filled with books whose spines are dusty rose, sage, cream, powder blue and a few red (plain spines, no "
     "lettering); a rolling ladder; a globe on a stand; a deep red armchair with someone reading in it; a brass "
     "reading lamp; a table with open atlases; a ginger cat asleep on a pile of books; a sage-green carpet. "
     "Quiet, warm light. Palette: chocolate brown bookcases, the soft colours of the spines, sage carpet, the red "
     "armchair as the accent."),

    ("library", "wider", WIDER +
     "The whole library is in view, two storeys high: a gallery with an iron railing runs round it above, reached "
     "by a spiral staircase; more bookcases above; a round skylight in an ivory ceiling letting down a soft shaft "
     "of light; a long table with maps and a vase of flowers; marble busts; a child at the top of the ladder; a "
     "white dog on the carpet." + WALKER + " Palette: chocolate brown, ivory, sage, dusty rose, cream light."),

    ("hall door", "doorway", BACK +
     "We have stepped back through a tall doorway into the entrance hall of the villa, and the library is seen "
     "through the open double doors at the far end of the hall." + OPENING + " Around the doorway: the hall's far "
     "wall, a large calm area of soft celadon green with ivory pilasters and a carved ivory door case; on each "
     "side a tall blue-and-white vase holding enormous pale pink, cream and red blooms; to the far left and "
     "right, the first steps of two curving staircases with dark chocolate-brown banisters; in front a chequered "
     "floor in chocolate brown-black and cream, with a vermilion red carpet running toward us from the doorway; "
     "a console table with a bowl of lemons; a white greyhound lying on the floor. Soft daylight. Palette: "
     "celadon walls, ivory stone, chocolate brown and cream floor, the red carpet as the accent."),

    ("hall", "wider", WIDER +
     "The whole grand entrance hall is in view: the two staircases curve up on the left and right to a balcony "
     "gallery that crosses above the doorway, their banisters dark chocolate brown and their steps carpeted in "
     "red; a large ochre-gold chandelier hangs in the middle; tall windows with long dusty-rose curtains; framed "
     "pictures on the celadon walls that show only abstract shapes of colour; an ivory ceiling painted with a few "
     "flowers; the chequered floor and the red carpet running toward us. Tiny figures: a maid carrying flowers, "
     "two children sliding down a banister, a cat on the stairs. Morning light comes from behind us and lays "
     "soft shadows." + WALKER + " Palette: celadon and ivory, chocolate brown, dusty rose, ochre gold, red "
     "carpet."),

    ("front door", "doorway", BACK +
     "We have stepped back outside, and the hall is seen through the villa's wide-open front door." + OPENING +
     " Around the doorway: the front of the villa seen close, a large calm area of warm peach-orange stucco; an "
     "ivory stone door surround with a fanlight; the two door leaves, painted very deep forest green, folded "
     "back; white jasmine hanging over the door; a tall window with sage louvred shutters on each side; below, "
     "wide ivory steps coming down toward us, with a lemon tree in a pot on each side and two urns of red "
     "geraniums; a bicycle, a gardener's straw hat, a sleeping dog. Bright late-morning sun, with soft shadows "
     "in blue-grey. Palette: peach-orange wall, ivory stone, forest-green doors, sage shutters, lemon, red "
     "geraniums."),

    ("villa", "wider", WIDER +
     "The whole front of the villa is in view: three storeys in peach-orange with rows of sage-shuttered "
     "windows, a balcony above the door, a balustrade with urns along the roof line, a terracotta tile roof. In "
     "front of it a formal garden: ivory gravel paths, low clipped hedges in patterns, a round fountain, lemon "
     "trees in pots, and two beds of pale pink and red flowers. On both sides, columns of cypress and broad "
     "umbrella pines in very deep forest green. Tiny figures: children with a hoop, a couple under a parasol. "
     "Behind the roof, hills in powder blue and a calm cream morning sky." + WALKER + " Palette: peach-orange "
     "villa, deep forest green, ivory gravel, leaf-green hedges, cream sky, small reds."),

    ("gardens", "wider", WIDER +
     "The villa stands on a hillside, and its gardens come down toward us in terraces to the shore of a lake: "
     "ivory balustraded terraces, flights of steps, a long pergola, olive groves in sage and orange groves in "
     "deep green, a few cascades of pale pink flowers, a round aqua pool with a fountain and two white swans; at "
     "the bottom a stone landing stage with red-and-cream striped mooring poles and small boats, and the aqua "
     "water of the lake along the bottom edge of the image. To the left and right, wooded hills in forest green "
     "and sage with a pale village and a bell tower; mountains in powder blue behind; a calm cream and pale peach "
     "morning sky." + WALKER + " Palette: forest green and sage, ivory stone, peach-orange villa, aqua water, "
     "cream sky, a few reds."),

    ("lake", "wider", WIDER +
     "The villa and its gardens are small on the far shore of a wide lake in the morning. The lake stretches "
     "toward us as one large calm area of aqua and celadon, with white horizontal brushstrokes of reflection; "
     "three red-sailed boats and a white steamer trailing a little smoke, and a line of white birds flying low "
     "over the water; nobody is swimming. Mountains in flat layers of powder blue and sage with touches of snow; "
     "a huge calm morning sky of cream and pale peach with a few soft dusty-rose clouds. The near shore frames "
     "the view along the bottom and up both sides: big leaves in very deep forest green and enormous soft "
     "flowers in pale pink, cream and red, the trunks and crowns of two umbrella pines, and an ivory stone "
     "balustrade where the painter in the red coat leans with the small white dog beside him, seen from behind, "
     "watching the red-sailed boats. Palette: aqua and celadon water, cream and peach sky, powder-blue "
     "mountains, deep forest-green foreground, vermilion sails and coat."),

    ("terrace", "wider", WIDER +
     "The balustrade belongs to the terrace of a small hillside hotel, and the terrace is now in view all round "
     "the lake: a floor of cream and celadon tiles; round tables with ivory cloths laid for breakfast; one big "
     "red parasol; a waiter with a tray; a few guests; overhead, along the top of the image, a pergola hung with "
     "vine leaves and bunches of grapes; terracotta pots of red geraniums and small lemon trees along the edges; "
     "a white cat on a chair; stone steps going down on the left and right. Fresh morning light. Palette: cream "
     "and celadon tiles, ivory cloths, forest-green vine, terracotta, the red parasol."),

    ("window", "doorway", BACK +
     "We have stepped back into a hotel bedroom, and the terrace and the lake are seen through its tall open "
     "French windows." + OPENING + " Around the opening: sage-green louvred shutters folded back on the left and "
     "right, long ivory curtains hanging straight and perfectly still at each side, and the wall, a large calm area of pale peach with "
     "a faint leaf pattern; at one side a small table with a coffee pot, a cup, a bowl of peaches and a vase with "
     "one red flower; a chair with a straw hat on it; a floor of honey-ochre boards with a long bright shape of "
     "sunlight; one white cat asleep in the sun. Nothing is moving: no cloth lifts or billows. Palette: pale peach wall, sage shutters, ivory curtains, ochre "
     "floor, one red flower."),

    ("bedroom", "wider", WIDER +
     "The whole bedroom is in view: on the left a brass bed with a dusty-rose quilt and white pillows, an open "
     "suitcase on it with a paintbox and a sketchbook; on the right a wardrobe with a mirror and a washstand "
     "with a jug and basin; framed pictures that show only abstract shapes of colour; a cream rug bordered in "
     "red; a lamp; a pair of shoes; the ochre floorboards running toward us. Calm morning light. Palette: pale "
     "peach walls, dusty rose, ivory, brass ochre, chocolate brown furniture, small reds."),

    ("room door", "doorway", BACK +
     "We have stepped back out into the hotel corridor, and the bedroom is seen through its open door." +
     OPENING + " Around the doorway: the corridor wall, a large calm area of ivory above a sage-green dado; a "
     "dark chocolate-brown door frame and the door leaf standing open; a vermilion red carpet runner along the "
     "floor; a brass wall lamp; a maid with a trolley of white linen; a pair of shoes left outside the door; a "
     "potted palm. No numbers or lettering anywhere. Palette: ivory and sage, chocolate brown, brass, the red "
     "runner."),

    ("landing", "wider", WIDER +
     "The corridor is the upper landing of the hotel's stair hall, now in view: a staircase with a dark banister "
     "going down on the left and right, a tall window with powder-blue curtains, a chandelier, potted palms, and "
     "at the bottom of the image the hall below with a porter carrying two suitcases, a guest with a hat box, and "
     "a white dog on the stairs. Soft daylight. Palette: ivory, sage, chocolate brown, powder blue, red carpet."),

    ("hotel door", "doorway", BACK +
     "We have stepped back outside into a village street, and the stair hall is seen through the hotel's open "
     "front door." + OPENING + " Around the doorway: the front of the small hotel, a large calm area of pale "
     "peach stucco; an awning striped red and cream over the door, without lettering; sage shutters; window "
     "boxes of red geraniums; a bay tree in a pot on each side of the door; a bench; a bicycle; a porter with a "
     "trolley of suitcases; a cat; ivory cobbles in front. Early morning light with long soft blue-grey shadows. "
     "Palette: pale peach wall, sage, ivory cobbles, forest-green bay trees, the red awning."),

    ("village", "wider", WIDER +
     "The whole small hotel is in view in its village street on a hill: neighbouring houses in ivory and dusty "
     "rose under terracotta roofs; a bakery with loaves in its window; a small fountain; a chapel with a bell; "
     "steps climbing between the houses; a cat asleep on a wall; behind the roofs, steep slopes with terraced "
     "vineyards and dark cypress; above, a calm early-morning sky of cream." + WALKER + " Palette: ivory, dusty "
     "rose and pale peach houses, terracotta, sage vineyards, forest-green cypress, cream sky."),

    ("hillside", "wider", WIDER +
     "The village is small on a steep hillside among terraces of vines and olive groves in sage; a road zigzags "
     "up to it, empty but for a small red cart standing by a gate; a shepherd resting with white sheep; columns of dark cypress; a stone bridge over a "
     "stream at the bottom; behind, mountains in flat layers of powder blue with the first sun on their snow; a "
     "huge calm dawn sky of cream and pale peach. Palette: sage and forest green, ivory village, powder-blue "
     "mountains, cream and peach sky, one red cart."),

    ("viaduct arch", "doorway", BACK +
     "We have stepped back down the valley, and the hillside is seen through one tall arch of a stone railway "
     "viaduct." + OPENING + " The opening here is the arch: round-topped, with the viaduct's ivory stone piers "
     "to the left and right of it and its curve above. Around and below it: a river running under the arch "
     "toward us, aqua with white brushstrokes; reeds; a white heron; a fisherman on the bank; pale pink wild "
     "flowers; a small red rowing boat pulled up on the shingle. Everything is still. Cool morning shade under the arch, "
     "sunlight beyond. Palette: ivory stone, aqua river, forest green and sage banks, one red boat."),

    ("valley", "wider", WIDER +
     "The whole viaduct is in view, crossing a wide, quiet valley on many tall arches at dawn; nothing is "
     "crossing it. The river winds toward us through meadows of fresh leaf green dotted with red poppies; "
     "haystacks; a few white cows lying down; wooded slopes in very deep forest green on both sides; mountains "
     "in powder blue behind; a huge calm dawn sky of cream and pale peach with one long dusty-rose cloud. In the "
     "meadow in the foreground at the bottom, seen from behind: the painter in the red coat standing at an "
     "easel, painting this very view, with the small white dog sitting beside him. Palette: leaf-green meadows, "
     "forest-green woods, aqua river, ivory viaduct, cream and peach sky, the red poppies and coat."),

    ("orchard", "wider", WIDER +
     "The meadow lies at the edge of an old orchard in full blossom, which is now in view all round the valley: "
     "fruit trees on the left and right and their branches across the top of the image, their crowns soft "
     "clouds of cream and pale pink blossom on dark chocolate-brown trunks, framing the view; under them long "
     "grass of fresh leaf green with daisies; a row of white beehives; a wooden ladder leaning in a tree; a "
     "wicker basket; two white geese asleep in the grass; a few fallen petals. The same calm dawn sky shows "
     "between the branches, with a pale full moon still up at one side. Everything is still. Palette: cream "
     "and pale pink blossom, chocolate-brown trunks, leaf green, cream and peach sky."),

    ("moon gate", "doorway", BACK +
     "We have stepped back through a moon gate, a perfectly round opening in a garden wall, and the orchard is "
     "seen through it. The round opening is large and exactly centred: it is about three quarters as wide as "
     "the image, so that the whole central square lies inside the circle and nothing covers any of it. This "
     "side of the wall is still in the last of the night: the wall is one large calm area of deep slate "
     "blue-green shadow, with white climbing roses and jasmine showing pale against it; two round paper "
     "lanterns still lit, cream; in front, a path of ivory stepping stones leading to the gate between dark "
     "beds of white lilies and pale foxgloves; a white cat sitting on top of the wall. Palette: deep slate "
     "blue-green and forest-green shadow, cream and white flowers, cream lantern light; the dawn only through "
     "the gate."),

    ("night garden", "wider", WIDER +
     "The whole walled garden is in view in the last of the night, the wall with its moon gate in the middle of "
     "the far side and the dawn showing only through the gate. Above the wall the sky is one large calm area of "
     "deep night blue-green, with a big cream full moon, a few stars, and the dark crowns of cypress and "
     "umbrella pines against it. In the garden: a still, round pond in the foreground holding the moon's "
     "reflection; great white flowers glowing against chocolate brown-black and very deep forest-green leaves "
     "(magnolias, lilies, white roses, moonflowers), with a few pale pink peonies; a white peacock standing at "
     "the edge of the pond; a stone bench where the painter in the red coat sits, the small white dog asleep at "
     "his feet; a few lit paper lanterns; fireflies as small cream dots. Nothing moves. Palette: chocolate "
     "brown-black and deep forest green, deep night blue-green sky, cream moon and white flowers, pale pink, "
     "and the red coat as the one accent."),
]
