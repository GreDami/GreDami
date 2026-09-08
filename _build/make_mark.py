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
a saturated ochre wall, a stone coping he is perched on, and a bird painted in
cobalt with a green frame over his eyes. So there are two keys rather than one,
because the bird and the coping are unlike the wall in different ways:

    the bird   is cool — blue over red on the body, green over red on the
               frames — everywhere he is not nearly black, and the near-black
               is his ink outline, which nothing on that wall comes close to.
               Cool or dark, then, against a wall that is neither.
    the coping is neither cool nor warm: grey, and the only grey in the
               picture. The wall reads about -170 on blue-minus-red and the
               cream mouldings under the cap about -90, so a band either side
               of zero takes the cap and leaves the building it belongs to.

Neither key throws away the drawn line-work of the building on its own — those
edges are as dark as the bird's outline and score just as high. That is dealt
with by geometry rather than colour: each piece is one connected run of pixels
and the stray edges are others, so only the largest run is kept.

Two things then have to be put back that the keys are too strict about. The
first is the pale specular light on the bird's shoulder and breast, which is
near-white and so scores as though it were wall; left alone it punches holes
that are invisible on paper and show as violet freckles the moment the mark
goes on the footer. The second is the reverse, and must not be put back: the
wall genuinely does show through the gap under the brow bar. Both are enclosed
pockets, so what separates them is what colour they are — a pocket of ochre is
the wall seen through the drawing and stays open, a pocket of anything else is
paint and is filled.

    the bird   crown to tail, ending where the coping crosses in front of him
    the coping the corner he is standing on, cut to a little either side of
               him — a ledge, not the building

One picture, and every file below is that picture at a different size. The
icons used to be a second framing — the head alone, cropped under the beak —
because a whole bird at sixteen pixels is four pixels of head and the glasses
go with it. That is still true and it is still the cost: at 16 the green is
two pixels and what is left is a blue bird on a bar. It buys the thing that
matters more, which is that the tab, the home screen and the nav all carry the
same mark, and at 32 — which is what a tab strip actually asks for on any
screen worth having — the glasses are back and it reads.

Four files, because the places an icon lands do not agree on what to do with a
transparent corner:

    mark.webp             alpha kept — the stylesheet's mark
    favicon.png/.ico      alpha kept — a tab strip is any colour
    apple-touch-icon.png  on page colour, opaque — iOS lays transparency on
                          black and rounds corners itself
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
# The corner of the coping he is standing on. The cap runs the length of the
# roof and turns out of frame at both ends; this is the part of it that is a
# base for a bird — a little wider than he is on the left, where his breast
# overhangs, and stopped on the right before the arm plunges out of the
# picture. Any more and the mark is a building with a bird on it.
LEDGE = (416, 984, 830, 1180)

PAGE = (250, 250, 251)           # --paper, what the opaque icons stand on

NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
CROSS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def bird_score(rgb):
    """How far a pixel is from anything on the wall behind the bird.

    Blue over red carries the body, green over red the frames, and the last
    term carries the ink outline — which is neutral, and so scores nothing on
    hue, but is darker than any plaster or shadow on the wall behind it.
    """
    r, g, b = rgb
    lum = (r * 299 + g * 587 + b * 114) / 1000
    return (b - r) + (g - r) * 0.35 + max(0.0, 60 - lum) * 1.5


def stone_score(rgb):
    """The same, for the coping: grey, and nothing else up there is.

    Warm is the wall and the cream mouldings; cool is the bird, whose body
    crosses this crop and must not be dragged into it. What is left in the
    middle is the cap and its drawn edges.
    """
    r, g, b = rgb
    lum = (r * 299 + g * 587 + b * 114) / 1000
    if lum > 178:
        return -100.0
    return min(35 - abs(b - r), 40 + (g - r)) * 2.0


def largest_run(solid, w, h):
    """The biggest connected run of `solid` pixels — the subject, not the
    building's line-work around it."""
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
                for dx, dy in CROSS:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and solid[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            if len(run) > len(best):
                best = run
    return best


def close_pockets(keep, src, w, h):
    """Fill the enclosed gaps that are paint rather than wall.

    A pocket the key left open is either light the key was too strict about —
    the specular on the shoulder, the glare on a lens — or it is a genuine
    hole in the drawing with the ochre wall behind it. Ochre is the whole
    difference, so that is what is measured.
    """
    outside = [[False] * w for _ in range(h)]
    queue = deque()
    border = ([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
              + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
    for x, y in border:
        if not keep[y][x] and not outside[y][x]:
            outside[y][x] = True
            queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for dx, dy in CROSS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not keep[ny][nx] and not outside[ny][nx]:
                outside[ny][nx] = True
                queue.append((nx, ny))

    seen = [[False] * w for _ in range(h)]
    for sy in range(h):
        for sx in range(w):
            if keep[sy][sx] or outside[sy][sx] or seen[sy][sx]:
                continue
            queue = deque([(sx, sy)])
            seen[sy][sx] = True
            pocket = []
            while queue:
                x, y = queue.popleft()
                pocket.append((x, y))
                for dx, dy in CROSS:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < w and 0 <= ny < h and not keep[ny][nx]
                            and not outside[ny][nx] and not seen[ny][nx]):
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            ochre = sum(1 for p in pocket if src[p][0] - src[p][2] > 60)
            if ochre * 4 < len(pocket):
                for x, y in pocket:
                    keep[y][x] = True


def key(im, score, hi, lo=8.0):
    """Lift one piece of the picture off the wall behind it."""
    w, h = im.size
    src = im.load()
    sc = [[score(src[x, y]) for x in range(w)] for y in range(h)]
    solid = [[sc[y][x] >= hi for x in range(w)] for y in range(h)]

    keep = [[False] * w for _ in range(h)]
    for x, y in largest_run(solid, w, h):
        keep[y][x] = True
    close_pockets(keep, src, w, h)

    out = Image.new("RGBA", (w, h))
    dst = out.load()
    span = hi - lo
    for y in range(h):
        for x in range(w):
            if keep[y][x]:
                dst[x, y] = src[x, y] + (255,)
                continue
            # One ring of half-lit pixels around him, and no more: anything
            # not touching the subject is wall, however it scored.
            edge = [(x + dx, y + dy) for dx, dy in NEIGHBOURS
                    if 0 <= x + dx < w and 0 <= y + dy < h and keep[y + dy][x + dx]]
            if not edge:
                dst[x, y] = (0, 0, 0, 0)
                continue
            t = min(1.0, max(0.0, (sc[y][x] - lo) / span))
            a = t * t * (3 - 2 * t)
            if a <= 0.004:
                dst[x, y] = (0, 0, 0, 0)
                continue
            # These pixels are part subject and part ochre wall. Left as they
            # are they ring him in warm light, which is exactly what shows up
            # the moment the mark is put on the dark footer — so the fringe is
            # given the colour of what it touches and only its opacity is
            # allowed to fall away.
            mix = [sum(c) // len(edge) for c in zip(*(src[p] for p in edge))]
            dst[x, y] = tuple(mix) + (int(round(a * 255)),)
    return out


def cut(box, score, hi):
    return key(Image.open(SRC).convert("RGB").crop(box), score, hi)


def perched():
    """The bird on his ledge, back in the positions the plate has them in."""
    bird = cut(BIRD, bird_score, 46.0)
    ledge = cut(LEDGE, stone_score, 30.0)
    x0, y0 = min(BIRD[0], LEDGE[0]), min(BIRD[1], LEDGE[1])
    out = Image.new("RGBA", (max(BIRD[2], LEDGE[2]) - x0, max(BIRD[3], LEDGE[3]) - y0))
    out.alpha_composite(ledge, (LEDGE[0] - x0, LEDGE[1] - y0))
    out.alpha_composite(bird, (BIRD[0] - x0, BIRD[1] - y0))
    return out.crop(out.getbbox())


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


mark = perched()

written = []


def save(name, im, **kw):
    path = ROOT / name
    im.save(path, **kw)
    written.append((name, im.size, path.stat().st_size))


# the mark: bird and ledge at their own proportions, no square to fit. The nav
# shows them 34px tall and the footer 44, so 288 covers a 3x screen with room
# over
save("mark.webp", down(mark, 288), format="WEBP", quality=90, method=6,
     exact=True)

save("favicon.png", square(mark, 192, 0.98), format="PNG", optimize=True)

# The .ico is what a tab strip actually reads, and it holds three pictures
# rather than one. Handed a single image and a list of sizes, Pillow makes the
# small frames by shrinking the large one — so 16 and 32 came out of a 48-pixel
# square that had already lost most of the drawing, and the glasses with it.
# Each frame is cut from the full-resolution mark instead, resampled once and
# sharpened for the size it is going to be seen at. They are also given the
# whole square: at 16 pixels a margin costs a pixel off the bird, and the
# portrait shape leaves air down both sides regardless.
ico = ROOT / "favicon.ico"
frames = {n: square(mark, n) for n in (48, 32, 16)}
frames[48].save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)],
                append_images=[frames[32], frames[16]])
written.append(("favicon.ico", (48, 48), ico.stat().st_size))

# home screen: opaque, and held off the edges — iOS rounds the corners itself
# and a mark touching them loses its beak on one side and its ledge on the other
save("apple-touch-icon.png", square(mark, 180, 0.84, PAGE),
     format="PNG", optimize=True)
# Android maskable: everything that matters inside the middle 80%
save("icon-maskable.webp", square(mark, 512, 0.63, PAGE),
     format="WEBP", quality=88, method=6)

for name, size, nbytes in written:
    print("%-22s %4dx%-4d %6.1f KB" % (name, size[0], size[1], nbytes / 1024))
