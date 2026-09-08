#!/usr/bin/env python3
"""
Builds the company mark and the whole icon set out of the hero illustration.

The mark used to be a second bird — a watercolour pigeon in green aviators,
painted on cream paper, kept in _build/src/mark.png. It was a good drawing and
it was not this bird: beside the hero plate the site now leads with, the nav
carried a paler, softer, differently drawn animal, and a visitor had to be told
they were the same character. So the mark is cut from the hero itself. There is
one bird on this site and every place it appears it is the same one.

Lifting him off that plate is a different problem from lifting him off paper.
There is no sheet to flatten here and no lighting to correct; what there is, is
a saturated ochre wall, a grey cornice he is perched on, and a bird painted in
cobalt with a green frame over his eyes. Wall and cornice are warm — red above
blue, every one of them, from the brightest render on the plaster to the shaded
underside of the eave. The bird is cool everywhere he is not nearly black, and
the near-black is his ink outline, which nothing in the building comes close
to. So the key measures both: how cool a pixel is, and how dark. That separates
him from the building in one pass and keeps the outline that makes the drawing
read.

What it does not do on its own is throw away the building's own line-work — the
drawn edges of the cornice are as dark as his outline and score just as high.
Those are dealt with by geometry rather than colour: the bird is one connected
run of pixels and the cornice edges are others, so only the largest run is
kept. That also settles the awkward part of the picture, which is that the roof
crosses in front of his tail. Below the roof line he is simply not there, and
the silhouette that comes out ends where the building starts — a bird sitting
down, which is the shape he has in the illustration.

Two framings come out of the plate, because 16 pixels and 28 pixels do not want
the same picture:

    the bird   crown to tail, bounded underneath by the roof he is standing
               on. A whole animal. This is the mark.
    the head   cropped close under the beak. At favicon sizes the bird's head
               is four pixels of the height and the glasses vanish with it;
               this throws away the body to keep the part that is recognisable.

and four files, because the places an icon lands do not agree on what to do
with a transparent corner:

    mark.webp             the bird, alpha kept — the stylesheet's mark
    favicon.png/.ico      the head, alpha kept — a tab strip is any colour
    apple-touch-icon.png  the head on page colour, opaque — iOS lays
                          transparency on black and rounds corners itself
    icon-maskable.webp    the same, pulled into Android's 80% safe circle

Small sizes are sharpened after the resample: the glasses are the whole
recognition down there and they need their edge back.

    python3 _build/make_mark.py
"""
import pathlib
from collections import deque

from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_build" / "src" / "halo3.png"

# The bird entire, from the top of the frames to the tip of the tail, plus a
# few pixels of wall on every side so the key has somewhere to start.
BIRD = (392, 606, 848, 1140)
# The head, squared, for the sizes the body cannot survive. Cut under the beak
# and just past the far temple: at 32 pixels this is two green lenses and a
# blue head, which is as much as an icon that size can say.
HEAD = (404, 618, 620, 834)

PAGE = (250, 250, 251)           # --paper, what the opaque icons stand on

# Below LO a pixel is the building; above HI it is the bird. Bare plaster sits
# around -170 and the shaded cornice around -90, so the gap either side of this
# pair is wide — these are not delicate numbers.
LO, HI = 8.0, 46.0


def coolness(rgb):
    """How far a pixel is from anything in the building.

    Blue over red carries the body, green over red the frames, and the last
    term carries the ink outline — which is neutral, and so scores nothing on
    hue, but is darker than any plaster or shadow on the wall behind it.
    """
    r, g, b = rgb
    lum = (r * 299 + g * 587 + b * 114) / 1000
    return (b - r) + (g - r) * 0.35 + max(0.0, 60 - lum) * 1.5


def largest_run(solid, w, h):
    """The biggest connected run of `solid` pixels — the bird, not the roof."""
    seen = [[False] * w for _ in range(h)]
    best = []
    for sy in range(h):
        for sx in range(w):
            if not solid[sy][sx] or seen[sy][sx]:
                continue
            queue = deque([(sx, sy)])
            seen[sy][sx] = True
            run = []
            while queue:
                x, y = queue.popleft()
                run.append((x, y))
                for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    if 0 <= nx < w and 0 <= ny < h and solid[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            if len(run) > len(best):
                best = run
    return best


NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def key(im):
    """Lift the bird off the building."""
    w, h = im.size
    src = im.load()
    sc = [[coolness(src[x, y]) for x in range(w)] for y in range(h)]
    solid = [[sc[y][x] >= HI for x in range(w)] for y in range(h)]

    keep = [[False] * w for _ in range(h)]
    for x, y in largest_run(solid, w, h):
        keep[y][x] = True

    out = Image.new("RGBA", (w, h))
    dst = out.load()
    span = HI - LO
    for y in range(h):
        for x in range(w):
            if keep[y][x]:
                dst[x, y] = src[x, y] + (255,)
                continue
            # One ring of half-lit pixels around him, and no more: anything
            # not touching the bird is wall, however it scored.
            edge = [(x+dx, y+dy) for dx, dy in NEIGHBOURS
                    if 0 <= x+dx < w and 0 <= y+dy < h and keep[y+dy][x+dx]]
            if not edge:
                dst[x, y] = (0, 0, 0, 0)
                continue
            t = min(1.0, max(0.0, (sc[y][x] - LO) / span))
            a = t * t * (3 - 2 * t)
            if a <= 0.004:
                dst[x, y] = (0, 0, 0, 0)
                continue
            # These pixels are part bird and part ochre wall. Left as they are
            # they ring him in warm light, which is exactly what shows up the
            # moment the mark is put on the dark footer — so the fringe is
            # given the colour of the bird it touches and only its opacity is
            # allowed to fall away.
            mix = [sum(c) // len(edge) for c in zip(*(src[p] for p in edge))]
            dst[x, y] = tuple(mix) + (int(round(a * 255)),)
    return out


def prepare(box):
    """Crop, lift him off the building, then trim back to the paint."""
    art = key(Image.open(SRC).convert("RGB").crop(box))
    return art.crop(art.getbbox())


def down(im, size, sharpen=True):
    """Resample to fit a `size` box, then give the edges back what it took."""
    w, h = im.size
    scale = size / max(w, h)
    out = im.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                    Image.LANCZOS)
    if sharpen:
        out = out.filter(ImageFilter.UnsharpMask(
            radius=max(0.6, size / 220), percent=int(150 - size / 12), threshold=2))
    return out


def square(im, size, inset=1.0, ground=None):
    """Centre him on a square, at `inset` of its width. Alpha unless grounded."""
    canvas = Image.new("RGBA", (size, size),
                       (ground or (0, 0, 0)) + (255 if ground else 0,))
    art = down(im, round(size * inset))
    canvas.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
    return canvas.convert("RGB") if ground else canvas


bird = prepare(BIRD)
head = prepare(HEAD)

written = []


def save(name, im, **kw):
    path = ROOT / name
    im.save(path, **kw)
    written.append((name, im.size, path.stat().st_size))


# the mark: the bird at his own proportions, no square to fit. The nav shows
# him 29px tall and the footer 38, so 288 covers a 3x screen with room over
save("mark.webp", down(bird, 288), format="WEBP", quality=90, method=6,
     exact=True)

save("favicon.png", square(head, 192, 0.98), format="PNG", optimize=True)
ico = ROOT / "favicon.ico"
square(head, 48, 0.98).save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
written.append(("favicon.ico", (48, 48), ico.stat().st_size))

# home screen: opaque, and held off the edges — iOS rounds the corners itself
# and a bird touching them loses his beak to the mask
save("apple-touch-icon.png", square(head, 180, 0.84, PAGE),
     format="PNG", optimize=True)
# Android maskable: everything that matters inside the middle 80%
save("icon-maskable.webp", square(head, 512, 0.63, PAGE),
     format="WEBP", quality=88, method=6)

for name, size, nbytes in written:
    print("%-22s %4dx%-4d %6.1f KB" % (name, size[0], size[1], nbytes / 1024))
