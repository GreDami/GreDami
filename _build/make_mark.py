#!/usr/bin/env python3
"""
Builds the company mark and the whole icon set out of the painting.

The source is the original watercolour — a pigeon in green aviators, painted on
cream paper. The bird is lifted off that sheet and stands free: no disc, no
plate, no rectangle of cream sitting in the nav bar. What makes that possible
is that the paper and the paint disagree about more than brightness. The lit
side of the breast is as pale as the sheet, so a threshold on lightness alone
punches holes in the bird — but the sheet is warm (blue below red) and every
part of the bird is cool (blue above red), and no amount of light closes that
gap. The key measures both, and then only removes what is *connected to the
edge of the frame*, so a pale patch surrounded by paint can never be mistaken
for background however close to cream it reads.

Edge pixels are part paper and part paint. Those get their alpha from how far
they have travelled from cream, and their colour back-computed out of the mix,
so the fringe is the bird's own colour at low opacity rather than cream — which
is what stops a cream halo appearing the moment the mark is put on the dark
footer.

Two framings come out of the sheet, because 16 pixels and 28 pixels do not want
the same picture:

    the bust   head, breast and the wash trailing off below it. A whole
               silhouette, ending where the paint ends. This is the mark.
    the head   cropped close under the beak. At favicon sizes the bust's head
               is four pixels of the height and the glasses vanish with it;
               this throws away the body to keep the part that is recognisable.

and four files, because the places an icon lands do not agree on what to do
with a transparent corner:

    mark.webp             the bust, alpha kept — the stylesheet's mark
    favicon.png/.ico      the head, alpha kept — a tab strip is any colour
    apple-touch-icon.png  the head on page colour, opaque — iOS lays
                          transparency on black and rounds corners itself
    icon-maskable.webp    the same, pulled into Android's 80% safe circle

Small sizes are sharpened after the resample. A watercolour reduced to sixteen
pixels goes to mush otherwise: the glasses are the whole recognition at that
size and they need their edge back.

    python3 _build/make_mark.py
"""
import pathlib

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_build" / "src" / "mark.png"

# The bird entire, from the crown to where the breast wash gives out. The box
# is the paint's own extent plus a few pixels of air, because the alpha channel
# is the edge now — anything more is empty rows the mark has to carry around.
BUST = (150, 305, 675, 925)
# The head, squared, for the sizes the bust cannot survive.
HEAD = (215, 255, 745, 785)

# The painting has him facing right. Turned to face left he reads as the more
# alert of the two — the beak leads rather than trailing the wordmark — and that
# is the way round the mark is wanted. It cuts against the usual rule for a
# lockup, that a subject should look into the words beside it and not off the
# edge of the page; if that ever starts to grate, the answer is to move the mark
# to the right of the wordmark rather than to flip him back. Nothing in the
# drawing is handed — no lettering, no writing hand — so the flip costs nothing.
MIRROR = True

PAPER = (238, 233, 223)          # the sheet, measured off its own margin
PAGE = (250, 250, 251)           # --paper, what the opaque icons stand on
# Grain on the bare sheet reaches about 22 of the distance below; paint starts
# well above it. Between the two the pixel is a mixture and is treated as one.
KEY_LO, KEY_HI = 26, 58


def distance(rgb):
    """How far a pixel is from bare paper.

    Per-channel difference catches anything darker or more saturated; the last
    term is the warm/cool split, which is what separates the pale breast from
    the sheet it is painted on when the two are the same brightness.
    """
    r, g, b = rgb
    return max(abs(r - PAPER[0]), abs(g - PAPER[1]), abs(b - PAPER[2]),
               abs((b - r) - (PAPER[2] - PAPER[0])))


def key(im):
    """Lift the bird off the sheet."""
    w, h = im.size
    src = im.load()

    # every pixel that could be paper or part-paper, as a field the fill can
    # run through
    field = Image.new("L", (w, h))
    fld = field.load()
    for y in range(h):
        for x in range(w):
            fld[x, y] = 255 if distance(src[x, y]) < KEY_HI else 0
    # Only paper that reaches the frame is background. Anything cream-coloured
    # and walled in by paint — the glare on the lens, the light off the crown —
    # is part of the bird and stays.
    ImageDraw.floodfill(field, (0, 0), 128, border=None, thresh=0)
    for corner in ((w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if fld[corner] == 255:
            ImageDraw.floodfill(field, corner, 128, border=None, thresh=0)

    out = Image.new("RGBA", (w, h))
    dst = out.load()
    span = KEY_HI - KEY_LO
    for y in range(h):
        for x in range(w):
            rgb = src[x, y]
            if fld[x, y] != 128:
                dst[x, y] = rgb + (255,)
                continue
            t = min(1.0, max(0.0, (distance(rgb) - KEY_LO) / span))
            a = t * t * (3 - 2 * t)
            if a <= 0.004:
                dst[x, y] = (0, 0, 0, 0)
                continue
            # undo the mix with the sheet, so the fringe carries the bird's
            # colour and not a pale wash of cream
            dst[x, y] = tuple(
                min(255, max(0, int(round(p + (c - p) / max(a, 0.16)))))
                for c, p in zip(rgb, PAPER)) + (int(round(a * 255)),)
    return out


def prepare(box):
    """Crop, turn him round, lift him off the paper, then trim to the paint."""
    art = Image.open(SRC).convert("RGB").crop(box)
    if MIRROR:
        art = ImageOps.mirror(art)
    art = ImageEnhance.Color(art).enhance(1.10)
    art = ImageEnhance.Contrast(art).enhance(1.06)
    art = key(art.resize([v * 2 for v in art.size], Image.LANCZOS))
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
    canvas = Image.new("RGBA", (size, size), (ground or (0, 0, 0)) + (255 if ground else 0,))
    art = down(im, round(size * inset))
    canvas.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
    return canvas.convert("RGB") if ground else canvas


bust = prepare(BUST)
head = prepare(HEAD)

written = []


def save(name, im, **kw):
    path = ROOT / name
    im.save(path, **kw)
    written.append((name, im.size, path.stat().st_size))


# the mark: the bust at its own proportions, no square to fit. The nav shows it
# 28px tall and the footer 34, so 288 covers a 3x screen with room over
save("mark.webp", down(bust, 288), format="WEBP", quality=90, method=6,
     exact=True)

save("favicon.png", square(head, 192, 0.96), format="PNG", optimize=True)
ico = ROOT / "favicon.ico"
square(head, 48, 0.96).save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
written.append(("favicon.ico", (48, 48), ico.stat().st_size))

# home screen: opaque, and held off the edges — iOS rounds the corners itself
# and a bird touching them loses his beak to the mask
save("apple-touch-icon.png", square(head, 180, 0.82, PAGE),
     format="PNG", optimize=True)
# Android maskable: everything that matters inside the middle 80%
save("icon-maskable.webp", square(head, 512, 0.62, PAGE),
     format="WEBP", quality=88, method=6)

for name, size, nbytes in written:
    print("%-22s %4dx%-4d %6.1f KB" % (name, size[0], size[1], nbytes / 1024))
