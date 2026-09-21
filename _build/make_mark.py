#!/usr/bin/env python3
"""
Builds the company mark and the whole icon set out of the hero picture.

The mark used to be a second bird — a watercolour pigeon in green aviators,
painted on cream paper, kept in _build/src/mark.png. It was a good drawing and
it was not this bird: beside the hero plate the site now leads with, the nav
carried a paler, softer, differently drawn animal, and a visitor had to be told
they were the same character. So the mark is cut from the hero itself. There is
one bird on this site and every place it appears it is the same one.

The picture is low-poly — every face one flat colour, no brush and no line —
and what the bird has to be lifted off is a yellow wall, the grey gutter along
the ridge he is perched on, and the cream faces of the building under it. So
there are two keys rather than one, because the bird and the gutter are unlike
the wall in different ways:

    the bird   is cool — blue over red on the body, green over red on the
               frames — everywhere he is not nearly black, and the near-black
               is the glass in his frames, which nothing on that wall comes
               close to. Cool or dark, then, against a wall that is neither.
    the gutter is neither cool nor warm: grey, and the only grey in the
               picture. The wall reads about -170 on blue-minus-red and the
               cream faces of the building -55 to -80, while even the gutter
               face the light falls on stays within 30 of zero, so a band
               either side of zero takes the gutter and leaves the building it
               belongs to. The light face is also as bright as the cream, so
               warmth decides it and not lightness.

Each piece is then one connected run of pixels, and anything else either key
happens to catch is another run, so only the largest is kept.

Enclosed pockets the keys leave open are either paint they were too strict
about — the one-pixel line where two faces of the gutter meet at the ridge —
or the wall genuinely showing through, as it does between his breast and the
gutter. Ochre is the whole difference, so that is what is measured: a pocket of
ochre stays open, a pocket of anything else is paint and is filled.

    the bird   crown to tail, standing on the gutter
    the gutter the ridge he is standing on, cut straight down at the ends of
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

And a fifth, halo-mark.svg, the vector build.py squares off into Safari's
pinned-tab icon. A picture made of flat straight-edged faces traces cleanly,
so it is not drawn again by hand: each piece's outline is traced off this same
cut and kept to its corners, and the two are one shape.

    python3 _build/make_mark.py
"""
import math
import pathlib
from collections import deque

from PIL import Image, ImageFilter, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_build" / "src" / "halo4.png"

# The bird entire, from the top of the frames to the tip of the tail, plus a
# few pixels of wall on every side so the key has somewhere to start.
BIRD = (1338, 312, 1632, 634)
# The ridge he is standing on. The gutter runs down both arms of the roof and
# out of the picture; this is the part of it that is a base for a bird, cut
# straight down at the far edge of his glasses and the tip of his tail. That
# makes the mark as wide as he is and no wider, which is the shape the nav and
# the footer set aside for it. Any more and it is a roof with a bird on it.
LEDGE = (1346, 540, 1624, 704)

PAGE = (250, 250, 251)           # --paper, what the opaque icons stand on

NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
CROSS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def bird_score(rgb):
    """How far a pixel is from anything on the wall behind the bird.

    Blue over red carries the body, green over red the frames, and the last
    term carries the glass — which is barely coloured, and so scores little on
    hue, but is darker than any face of the wall behind it.
    """
    r, g, b = rgb
    lum = (r * 299 + g * 587 + b * 114) / 1000
    return (b - r) + (g - r) * 0.35 + max(0.0, 60 - lum) * 1.5


def stone_score(rgb):
    """The same, for the gutter: grey, and nothing else down there is.

    Warm is the wall and the cream faces of the building; cool is the bird,
    whose tail crosses this crop and must not be dragged into it. What is left
    in the middle is the gutter, the face in the light included — which is
    why the band is 45 wide and only near-white is ruled out on lightness.
    """
    r, g, b = rgb
    lum = (r * 299 + g * 587 + b * 114) / 1000
    if lum > 212:
        return -100.0
    return min(45 - abs(b - r), 40 + (g - r)) * 2.0


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

    A pocket the key left open is either paint the key was too strict about —
    a one-pixel line where two faces meet — or it is a genuine gap in the
    picture with the ochre wall behind it. Ochre is the whole difference, so
    that is what is measured.
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
    """The bird on his ledge, back in the positions the plate has them in —
    and the two pieces apart, on the same canvas, for the tracing."""
    bird = cut(BIRD, bird_score, 46.0)
    ledge = cut(LEDGE, stone_score, 30.0)
    x0, y0 = min(BIRD[0], LEDGE[0]), min(BIRD[1], LEDGE[1])
    size = (max(BIRD[2], LEDGE[2]) - x0, max(BIRD[3], LEDGE[3]) - y0)
    pieces = []
    for im, box in ((ledge, LEDGE), (bird, BIRD)):
        layer = Image.new("RGBA", size)
        layer.alpha_composite(im, (box[0] - x0, box[1] - y0))
        pieces.append(layer)
    out = Image.alpha_composite(*pieces)
    box = out.getbbox()
    return out.crop(box), [piece.crop(box) for piece in pieces]


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


RING = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))


def walk(solid, w, h, start):
    """The edge of the run `start` is the top-left pixel of, clockwise, as
    the pixels along it (Moore-neighbour tracing)."""
    def on(x, y):
        return 0 <= x < w and 0 <= y < h and solid[y * w + x]

    c, b = start, (start[0] - 1, start[1])
    ring, first = [], None
    while True:
        i = RING.index((b[0] - c[0], b[1] - c[1]))
        prev = b
        for k in range(1, 9):
            dx, dy = RING[(i + k) % 8]
            n = (c[0] + dx, c[1] + dy)
            if on(*n):
                c, b = n, prev
                break
            prev = n
        else:
            return [start]
        if (c, b) == first:
            return ring
        if first is None:
            first = (c, b)
        ring.append(c)


def corners(pts, eps):
    """A closed outline kept to its corners: every point within `eps` of the
    straight run between the points either side of it goes (Douglas-Peucker,
    worked from a stack so a long edge cannot run out the recursion)."""
    n = len(pts)
    far = max(range(n), key=lambda j: (pts[j][0] - pts[0][0]) ** 2
              + (pts[j][1] - pts[0][1]) ** 2)
    keep = {0, far}
    todo = [(0, far), (far, n)]
    while todo:
        a, z = todo.pop()
        if z - a < 2:
            continue
        (x0, y0), (x1, y1) = pts[a], pts[z % n]
        dx, dy = x1 - x0, y1 - y0
        span = math.hypot(dx, dy) or 1e-9
        worst, at = -1.0, a
        for j in range(a + 1, z):
            d = abs((pts[j][0] - x0) * dy - (pts[j][1] - y0) * dx) / span
            if d > worst:
                worst, at = d, j
        if worst > eps:
            keep.add(at)
            todo += [(a, at), (at, z)]
    return [pts[j] for j in sorted(keep)]


def outlines(matte, least=60, k=4):
    """Every separate piece of a matte as a closed polygon in the matte's own
    pixels, largest first. The matte is enlarged k times and read at half, so
    the outline runs between pixels where the edge in the picture really runs;
    then it is kept to its corners — anything within a pixel of a straight run
    goes, which is the key's own wobble — and for a figure made of
    straight-edged faces the corners are what it is."""
    w, h = matte.width * k, matte.height * k
    solid = bytearray(v >= 128 for v in
                      matte.resize((w, h), Image.BILINEAR).getdata())
    seen = bytearray(w * h)
    found = []
    for i in range(w * h):
        if not solid[i] or seen[i]:
            continue
        seen[i] = 1
        queue, area = deque([i]), 0
        while queue:
            j = queue.popleft()
            area += 1
            x, y = j % w, j // w
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                m = ny * w + nx
                if 0 <= nx < w and 0 <= ny < h and solid[m] and not seen[m]:
                    seen[m] = 1
                    queue.append(m)
        if area < least * k * k:
            continue
        edge = walk(solid, w, h, (i % w, i // w))
        found.append((area, corners([((x + 0.5) / k, (y + 0.5) / k) for x, y in edge], 1.0)))
    return [poly for _, poly in sorted(found, key=lambda f: -f[0])]


def tones(im, matte, *at):
    """The colours a piece has at given lightnesses, from its own solid
    pixels: 0 is its darkest, 1 its lightest."""
    px = [c for c, a in zip(im.convert("RGB").getdata(), matte.getdata()) if a >= 250]
    px.sort(key=lambda c: c[0] * 299 + c[1] * 587 + c[2] * 114)
    return ["#%02X%02X%02X" % px[min(len(px) - 1, int(t * len(px)))] for t in at]


def vector(ledge, bird):
    """halo-mark.svg: the same cut, in outline. The four fills and the
    classes on their stops are the ones build.py already lightens for a dark
    tab strip."""
    # the glasses are the part of him that is greener than it is blue; the
    # rims run 150 and up in green, the glass under 110 reflections and all
    frames = Image.new("L", bird.size)
    glass = Image.new("L", bird.size)
    for i, (r, g, b, a) in enumerate(bird.getdata()):
        if a >= 128 and g > b and g - r > 25:
            xy = (i % bird.width, i // bird.width)
            frames.putpixel(xy, 255)
            if g < 125:
                glass.putpixel(xy, 255)
    nothing = Image.new("L", bird.size)
    body = Image.composite(bird.getchannel("A"), nothing, ImageOps.invert(frames))
    rims = Image.composite(frames, nothing, ImageOps.invert(glass))
    hb = tones(bird, body, 0.85, 0.45, 0.08)
    gf = tones(bird, rims, 0.8, 0.2)
    gl = tones(bird, glass, 0.85, 0.1)
    st = tones(ledge, ledge.getchannel("A"), 0.9, 0.4, 0.05)

    def path(poly):
        return "M " + " L ".join("%.1f %.1f" % p for p in poly) + " Z"

    w, h = bird.size
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="GreDami">' % (w, h),
        '  <!-- written by _build/make_mark.py, traced off the same cut as mark.webp -->',
        '  <defs>',
        '    <!-- the body: lit from the top left, as he is in the picture -->',
        '    <linearGradient id="hb" x1="0.15" y1="0" x2="0.85" y2="1">',
        '      <stop class="s0" offset="0" stop-color="%s"/>' % hb[0],
        '      <stop class="s1" offset="0.5" stop-color="%s"/>' % hb[1],
        '      <stop class="s2" offset="1" stop-color="%s"/>' % hb[2],
        '    </linearGradient>',
        '    <linearGradient id="gf" x1="0.1" y1="0" x2="0.7" y2="1">',
        '      <stop class="s3" offset="0" stop-color="%s"/>' % gf[0],
        '      <stop class="s4" offset="1" stop-color="%s"/>' % gf[1],
        '    </linearGradient>',
        '    <linearGradient id="gl" x1="0.2" y1="0" x2="0.6" y2="1">',
        '      <stop offset="0" stop-color="%s"/>' % gl[0],
        '      <stop offset="1" stop-color="%s"/>' % gl[1],
        '    </linearGradient>',
        '    <!-- the gutter: the light along its top face, slate down its front -->',
        '    <linearGradient id="st" x1="0" y1="0" x2="0.25" y2="1">',
        '      <stop class="s5" offset="0" stop-color="%s"/>' % st[0],
        '      <stop class="s6" offset="0.5" stop-color="%s"/>' % st[1],
        '      <stop class="s7" offset="1" stop-color="%s"/>' % st[2],
        '    </linearGradient>',
        '  </defs>',
        '  <!-- the ledge first and the bird over it, as the picture has them; its',
        '       stroke closes the hair between his outline and the top of the gutter -->',
        '  <path d="%s" fill="url(#st)" stroke="url(#st)" stroke-width="1.2" stroke-linejoin="round"/>'
        % path(outlines(ledge.getchannel("A"))[0]),
        '  <path d="%s" fill="url(#hb)"/>' % path(outlines(bird.getchannel("A"))[0]),
        '  <path d="%s" fill="url(#gf)"/>' % path(outlines(frames)[0]),
    ]
    for lens in outlines(glass, least=20)[:2]:
        lines.append('  <path d="%s" fill="url(#gl)"/>' % path(lens))
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


mark, (ledge_piece, bird_piece) = perched()

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

svg = ROOT / "halo-mark.svg"
svg.write_text(vector(ledge_piece, bird_piece), encoding="utf-8")
written.append(("halo-mark.svg", ledge_piece.size, svg.stat().st_size))

for name, size, nbytes in written:
    print("%-22s %4dx%-4d %6.1f KB" % (name, size[0], size[1], nbytes / 1024))
