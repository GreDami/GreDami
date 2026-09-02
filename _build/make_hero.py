#!/usr/bin/env python3
"""
Builds halo-hero.webp — the painted backdrop for the whole hero band.

The watercolour is a 480px square. On the page it sat at the right of the band
with the copy beside it on bare paper; this carries the wall in the painting on
past its own left edge, so the headline has the picture's paper under it instead
of white.

The wash is made out of the painting — slabs of its own wall laid leftwards and
dissolved into one another, at native scale where they meet the painting and at
widening scale as they recede, then blurred and sunk into the page colour by
distance from the join. Nothing is invented, so the palette cannot drift: it is
the same paint, thinning out. The slabs are translated, never mirrored — a
mirror folds the blue batten into a chevron at the join — and they are cut from
the parts of the square that hold neither the bird nor the roof, so the subject
is never repeated behind the copy.

    python3 _build/make_hero.py
"""
import pathlib
import random

from PIL import Image, ImageChops, ImageFilter, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_build" / "src" / "halo1.jpg"
OUT = ROOT / "halo-hero.webp"

PAPER = (250, 250, 248)          # --paper
S = 1100                          # the painting, square, at hero-band height
SEAM = 2460                       # where the painting's own left edge falls
W, H = SEAM + S, S
JOIN = SEAM / W                   # the join, as a fraction of the whole width

random.seed(11)


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


def feather(w, h, edge=0.34):
    """Soft-sided rectangle, so overlapping slabs dissolve instead of butting."""
    return ramp([(0, 0), (edge, 1), (1 - edge, 1), (1, 0)], w, 1).resize(
        (w, h), Image.BILINEAR)


art = Image.open(SRC).convert("RGB").resize((S, S), Image.LANCZOS)
# the three pieces of wall the bird and the roof never reach. The two tall ones
# barely have to be stretched, so they stay as crisp as the painting and can
# meet it at the join; the wide band carries the cream battens and is kept for
# the far end, where everything is a wash anyway.
PALE = art.crop((180, 0, 470, 950))
MOSS = art.crop((790, 0, 1090, 930))
BAND = art.crop((180, 0, S, 470))

# a base coat under the slabs — the wall's own average, taken back towards the
# paper, so no gap between slabs can read as a hole
base = tuple(int(c + (p - c) * 0.3)
             for c, p in zip(ImageStat.Stat(BAND).mean, PAPER))
field = Image.new("RGB", (W, H), base)

# the slabs, walking left from the join: native scale where they meet the
# painting, widening as they recede, each dissolved into the last
x, mag = SEAM, 1.0
while x > -700:
    src = random.choice((PALE, MOSS) if mag < 1.9 else (PALE, MOSS, BAND, BAND))
    w = int(src.width * mag)
    h = int(H * random.uniform(1.04, 1.22))
    slab = src.resize((w, h), Image.LANCZOS)
    if random.random() < 0.5:                      # the battens lean, so let them
        slab = slab.rotate(random.uniform(0.6, 2.6), Image.BICUBIC, fillcolor=base)
    x -= int(w * 0.55)
    field.paste(slab, (x, random.randint(H - h, 0)), feather(w, h))
    mag *= 1.16

# dissolve with distance: as crisp as the painting where it leaves it, a wash by
# the time it reaches the headline
levels = [(72, 0.00), (48, 0.30), (26, 0.54), (13, 0.72), (5, 0.87), (0, 0.96)]
soft = field.filter(ImageFilter.GaussianBlur(levels[0][0]))
for radius, at in levels[1:]:
    step = field.filter(ImageFilter.GaussianBlur(radius)) if radius else field
    soft = Image.composite(step, soft, ramp(
        [(0, 0), (max(0.0, at - 0.12) * JOIN, 0), (min(1.0, at + 0.12) * JOIN, 1), (1, 1)]))

canvas = Image.new("RGB", (W, H), PAPER)
canvas.paste(soft, (0, 0))
# the painting itself, its left edge feathered over the wash so the two washes
# run together instead of butting
canvas.paste(art, (SEAM, 0), ramp([(0, 0), (0.055, 1), (1, 1)], S, H))

# sink it into the page: full paint at the join, a wash under the copy.
# The band crops the left ~38% of this image away, so the far end of the ramp is
# never seen — what the page shows as its own left edge is around 0.38. The early
# steps used to fall to almost nothing there, which was right while the copy
# started at the page gutter and the strip was read as the paper under the
# headline; the copy now stands on the card column further in, and that left the
# strip reading as an empty margin instead. They are lifted so the wall is
# already present at the band's edge. #hero::after was lightened to match: it is
# the paper laid over this, and at its old strength it took back most of what is
# added here.
canvas = Image.composite(
    canvas, Image.new("RGB", (W, H), PAPER),
    ramp([(0.00, 0.30), (0.30, 0.34), (0.48, 0.42), (0.585, 0.50),
          (0.645, 0.63), (0.676, 1.00), (1.00, 1.00)]))

# paper grain, so the thin areas do not band once webp has had them
grain = Image.merge("RGB", [Image.effect_noise((W, H), 7).filter(
    ImageFilter.GaussianBlur(0.5))] * 3)
canvas = Image.blend(canvas, ImageChops.soft_light(canvas, grain), 0.5)

canvas.save(OUT, "WEBP", quality=76, method=6)
print("%s  %dx%d  %.0f KB" % (OUT.name, W, H, OUT.stat().st_size / 1024))

# A phone never sees this at full size: below 640px the band drops the wash to
# 0.3 opacity at 62% height in one corner, so a third of the width carries it
# with nothing to see. Quality goes down with it — what is left is a blur.
SMALL = ROOT / "halo-hero-sm.webp"
sw = W // 3
canvas.resize((sw, H // 3), Image.LANCZOS).save(
    SMALL, "WEBP", quality=62, method=6)
print("%s  %dx%d  %.0f KB" % (SMALL.name, sw, H // 3, SMALL.stat().st_size / 1024))
