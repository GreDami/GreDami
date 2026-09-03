#!/usr/bin/env python3
"""
Builds halo-hero.webp — the painted backdrop for the whole hero band.

The source is a pen-and-wash sheet: two birds on the cornices of an ochre
palazzo, drawn on the left of the paper with the right two-thirds left bare.
That bare paper is the whole idea here. The old backdrop had to invent a wall
to put behind the headline, because its painting was a full-bleed square with
no room in it; this one arrives with the room already in it. So the band is not
a picture with a wash bolted onto its side — it is one sheet of paper, the
drawing held at the right end of it and the copy standing on the same sheet.

What is built, therefore, is mostly paper:

  * the sheet itself — the drawing's own blank corner, tiled out to the full
    band with its grain and its unevenness intact, so the paper under the
    headline is the paper the drawing is on and not a flat fill;
  * a haze — the drawing blurred past recognition and stretched sideways, laid
    just to the left of the join and gone within a third of the width, so the
    ochre does not stop dead at the drawing's edge;
  * the drawing, every edge but its right one dissolved into that haze —
    the right runs off the band.

Nothing is mirrored and nothing is invented: the palette cannot drift, because
every pixel here comes off the one sheet. The result is light enough that the
copy sits on it without a veil having to be dragged back over the top — the
previous backdrop needed one, and it was what made the band look muddy.

    python3 _build/make_hero.py
"""
import pathlib
import random

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_build" / "src" / "halo3.jpg"
OUT = ROOT / "halo-hero.webp"
SMALL = ROOT / "halo-hero-sm.webp"

PAPER = (250, 250, 248)           # --paper

# the scan carries a dark deckle on three sides; this is the sheet inside it
TRIM = (2, 26, 882, 1182)
# the bare corner of that sheet — grain, no drawing
BARE = (545, 30, 875, 640)

W, H = 3200, 1100                 # the band, at hero-band height
ART_H = 0.90                      # the drawing, as a multiple of band height
BLEED_R = 30                      # how far it runs off the right edge
HAZE = 0.62                       # the haze at the join, before it dies off
HAZE_END = 0.52                   # where it has died out, as a fraction of W

random.seed(7)


def ramp(points, w=W, h=H):
    """An L mask from (x fraction, value 0..1) control points, smoothstepped."""
    row = Image.new("L", (w, 1))
    px = row.load()
    pts = sorted(points)
    for x in range(w):
        t = x / (w - 1)
        v = pts[0][1] if t <= pts[0][0] else pts[-1][1]
        for (x0, v0), (x1, v1) in zip(pts, pts[1:]):
            if x0 <= t <= x1:
                u = 0.0 if x1 == x0 else (t - x0) / (x1 - x0)
                u = u * u * (3 - 2 * u)
                v = v0 + (v1 - v0) * u
                break
        px[x, 0] = int(round(255 * v))
    return row.resize((w, h), Image.BILINEAR)


def feather(w, h, edge=0.3):
    """Soft-sided rectangle, so overlapping patches dissolve instead of butting."""
    return ramp([(0, 0), (edge, 1), (1 - edge, 1), (1, 0)], w, 1).resize(
        (w, h), Image.BILINEAR)


def edges(w, h, left, cap):
    """The drawing's own outline, dissolved: `left` of the width fading in at
    the join, `cap` of the height fading in at top and bottom. The right side
    is not touched — it runs off the band. Without this the sheet is a rectangle
    of slightly different paper sitting on the page, and at any scale small
    enough to be quiet the band's own top and bottom fades no longer cover its
    corners: you see the join as a line rather than as weather."""
    side = ramp([(0, 0), (left, 1), (1, 1)], w, h)
    # the same ramp stood on end: built along h, then turned a quarter turn
    ends = ramp([(0, 0), (cap, 1), (1 - cap, 1), (1, 0)], h, 1).transpose(
        Image.ROTATE_90).resize((w, h), Image.BILINEAR)
    return ImageChops.multiply(side, ends)


sheet = Image.open(SRC).convert("RGB").crop(TRIM)
aw = int(round(H * ART_H * sheet.width / sheet.height))
ah = int(round(H * ART_H))
art = sheet.resize((aw, ah), Image.LANCZOS)
ax = W - aw + BLEED_R             # the join: the drawing's own left edge
JOIN = ax / W

# ── the sheet ────────────────────────────────────────────────────────────────
# The bare corner, laid over the band in overlapping patches at a few sizes and
# never at the same offset twice, so the grain reads as paper rather than as a
# repeat. It is a light, low-contrast crop to begin with; pulled back towards
# the page colour it is barely there, which is the point — you should read it
# as paper, not as texture.
bare = sheet.crop(BARE)
base = tuple(int(c + (p - c) * 0.82)
             for c, p in zip(ImageStat.Stat(bare).mean, PAPER))
field = Image.new("RGB", (W, H), base)
for mag in (2.6, 1.7, 1.1):
    w = int(bare.width * mag)
    h = int(bare.height * mag)
    patch = bare.resize((w, h), Image.LANCZOS)
    mask = feather(w, h)
    x = -random.randint(0, w // 3)
    while x < W:
        field.paste(patch, (x, random.randint(-h // 3, H - h * 2 // 3)), mask)
        x += int(w * 0.62)
field = Image.blend(field, Image.new("RGB", (W, H), base), 0.35)

# ── the haze ─────────────────────────────────────────────────────────────────
# The drawing itself, blurred until nothing in it can be named and stretched
# sideways so even its rhythm is gone, carried leftwards off the join. All that
# should survive is the warmth: ochre leaving the drawing instead of stopping
# at it.
#
# Blurring alone does not give you that. The drawing is ochre wash over grey
# ink, and a wide blur averages the two into a flat grey — which then spread
# across the middle of the band as a smudge that was neither paper nor picture.
# So the blur is lifted most of the way to the paper first, which takes the ink
# out of it, and only then is the colour brought back up: what is left is the
# wash's own hue at paper's own lightness. Desaturating instead — which is what
# this did — keeps the grey and throws away the one thing worth carrying.
haze = art.filter(ImageFilter.GaussianBlur(int(aw * 0.16)))
haze = Image.blend(haze, Image.new("RGB", haze.size, base), 0.62)
haze = ImageEnhance.Color(haze).enhance(1.9)
hw = int(aw * 2.9)
haze = haze.resize((hw, H), Image.LANCZOS)
veil = Image.new("RGB", (W, H), base)
# run it off the right edge rather than ending it under the drawing: the
# drawing's own edges are dissolved, so anything laid behind them that stops
# in mid-air shows through the dissolve as a straight line
veil.paste(haze, (W - hw, 0))
# how much of the haze is let through: nothing at the far end, HAZE at the join
field = Image.composite(veil, field, ramp(
    [(0.0, 0.0), (HAZE_END, 0.0), (JOIN, HAZE), (1.0, HAZE)]))

# ── the drawing ──────────────────────────────────────────────────────────────
# The sheet was photographed cool, and the field is mixed from a crop of it
# that has been walked towards the page colour — so the two papers do not match,
# and an unmatched paper shows up as a seam however soft the feather is. The
# drawing is put on the field's white point before it is laid down: its own bare
# corner is measured and the gain that takes it there is applied to the whole
# drawing, which moves the paper and leaves the ink where it is.
kx, ky = aw / sheet.width, ah / sheet.height
corner = art.crop((int(BARE[0] * kx), int(BARE[1] * ky),
                   int(BARE[2] * kx), int(BARE[3] * ky)))
lift = [f / a for f, a in zip(base, ImageStat.Stat(corner).mean)]
art = Image.merge("RGB", [ch.point(lambda v, g=g: min(255, int(v * g)))
                          for ch, g in zip(art.split(), lift)])

canvas = Image.new("RGB", (W, H), PAPER)
canvas.paste(field, (0, 0))
canvas.paste(art, (ax, (H - ah) // 2), edges(aw, ah, 0.17, 0.11))

# Sink the band into the page colour, and at the far left sink it all the way.
# This used to hold a little of the field everywhere, on the theory that the
# headline should stand on the drawing's paper — but the drawing's paper is a
# scan, three or four points below --paper and faintly olive, and a hero that
# sits that far under the sections below it does not read as paper. It reads as
# dirty. So the left two-thirds are now the page's own paper exactly, and the
# sheet arrives late: nothing until the copy has ended, then quickly.
canvas = Image.composite(
    canvas, Image.new("RGB", (W, H), PAPER),
    ramp([(0.00, 0.00), (0.46, 0.00), (0.62, 0.12), (0.72, 0.38),
          (JOIN, 0.80), (0.86, 1.00), (1.00, 1.00)]))

# paper grain, so the thin areas do not band once webp has had them
grain = Image.merge("RGB", [Image.effect_noise((W, H), 6).filter(
    ImageFilter.GaussianBlur(0.5))] * 3)
canvas = Image.blend(canvas, ImageChops.soft_light(canvas, grain), 0.5)

canvas.save(OUT, "WEBP", quality=78, method=6)
print("%s  %dx%d  %.0f KB" % (OUT.name, W, H, OUT.stat().st_size / 1024))

# A phone never sees this at full size: below 640px the band drops the drawing
# into one corner at low opacity, so a third of the width carries it with
# nothing to see. Quality goes down with it — what is left is a blur.
canvas.resize((W // 3, H // 3), Image.LANCZOS).save(
    SMALL, "WEBP", quality=64, method=6)
print("%s  %dx%d  %.0f KB" % (SMALL.name, W // 3, H // 3,
                              SMALL.stat().st_size / 1024))
