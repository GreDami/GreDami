#!/usr/bin/env python3
"""
Builds halo-band.webp — the wide plate the hero band carries edge to edge.

halo-art.webp is the drawing as it was drawn: tall, 3:4, and right for a phone,
where the band is read down the page. A screen-wide band is the opposite shape,
and `cover` on a 3:4 picture stretched across 2:1 blows the bird up to the full
height of the band and crops away the cornice he is standing on — the one thing
that says what he is. No crop of that file works there.

So this writes a second plate in the band's own proportions, with the picture
kept at its own scale on the right and the wall carried on to the left edge.
The extension is not invented: every part of it is cut from the drawing, and at
the drawing's own resolution — the plate is as tall as the source, so nothing
anywhere in it is enlarged.

  · The picture loses its left quarter first — the shutter, the downpipe and
    the pilaster beside them. Those are vertical edges, and an edge cannot be
    continued sideways; what is left at the cut is plain wall, which can. The
    cut has to clear the shadow beside the pilaster too: at 185 it cleared the
    pipe but not the shadow, and a dark column carried leftwards puts a dark
    bar down the join, which is the one place that must not have a line in it.

  · The cornice is a moulding, so it is a straight extrusion: repeating the
    cross-section at the cut along the line's own slope continues it exactly.
    The slope was measured off the drawn edge (-0.5045 rows per column, by
    least squares over its first 220px), and at that angle it runs out of the
    bottom of the plate a few hundred px to the left. Everything further left
    is wall all the way down.

  · The wall is cloned, not stretched. An earlier plate opened one clean piece
    of plaster out across the whole extension, and enlarging it 2.4x cost the
    drawing its grain: the join read as a change of focus. Here the wall is
    laid in from four clean regions of the drawing at their own size, in soft
    irregular patches, flipped and nudged in scale so nothing repeats where the
    eye can catch it. Sharp on both sides of the join, because it is the same
    plaster at the same size on both sides.

  · Its light is not its own. Everything slower than TONE_R is thrown away and
    replaced by the light of the cross-section carried leftwards, so the tone
    at every height is the tone the drawing has at that height, and the join is
    a change of texture with no change of colour across it.

    python3 _build/make_band.py
"""
import pathlib
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC  = ROOT / "_build" / "src" / "halo3.png"
OUT  = ROOT / "halo-band.webp"

CUT            = 300          # px off the left of the source: shutter, pipe, pilaster
BAND_W         = 2900         # the band's own proportions, near 2:1...
SEAM           = 200          # how far the picture is blended into the wall
CORNICE_SLOPE  = 0.5045       # rows the cornice falls for every column to the left
CORNICE_AT_185 = 1049.0       # where it met the wall when the cut was at 185, at 1200 tall
TONE_R         = 240          # everything slower than this is taken from the drawing
PATCHES        = 105          # how many pieces of plaster the wall is laid in with
CALM           = 15           # broad stretches where the plaster is left alone
SEED           = 7            # the wall is the same wall on every build

src = Image.open(SRC).convert("RGB")
BAND_H = src.height           # ...and the source's own height, so nothing is enlarged
pic = src.crop((CUT, 0, src.width, src.height))
PW  = pic.width
EXT = BAND_W - PW
# The wall is built wider than the gap it fills: the picture is faded into it
# over SEAM px, and a fade needs something under it for its whole length.
EW  = EXT + SEAM
CORNICE_Y = (CORNICE_AT_185 * BAND_H / 1200.0) - CORNICE_SLOPE * (CUT - 185)

# ── the cut's own cross-section, carried leftwards down the cornice's slope ──
PAD = int(CORNICE_SLOPE * EXT) + 8
col = pic.crop((0, 0, 6, BAND_H)).resize((1, BAND_H), Image.LANCZOS)


def carry(column):
    """one column of the drawing, repeated to the left and falling at the
    cornice's own slope"""
    t = Image.new("RGB", (1, BAND_H + PAD))
    t.paste(column.crop((0, 0, 1, 1)).resize((1, PAD)), (0, 0))   # wall carried on up
    t.paste(column, (0, PAD))
    return t.resize((EW, BAND_H + PAD), Image.NEAREST).transform(
        (EW, BAND_H), Image.AFFINE,
        (1, 0, 0, CORNICE_SLOPE, 1, PAD - CORNICE_SLOPE * EXT), Image.BILINEAR)


# Carried sharp, the cross-section continues the cornice exactly — which is
# right, because a moulding is a straight extrusion. It is wrong for everything
# above the cornice: the cut happens to fall through a big patch of bare
# plaster, and a patch is not an extrusion, so carrying it sideways drew a pale
# diagonal band across the whole wall. Above the cornice only the light is
# taken, with the patches smoothed out of it first.
carried = carry(col)
flat = col.copy()
# Cut well clear of the cornice, and on an average of sixty rows rather than
# one: taken from the row that meets the moulding, the fill picked up the
# shadow sitting in that corner and smeared it up the wall as a grey cloud.
edge = int(CORNICE_Y) - 150
fill = tuple(round(v) for v in ImageStat.Stat(col.crop((0, edge - 60, 1, edge))).mean)
flat.paste(Image.new("RGB", (1, BAND_H - edge), fill), (0, edge))
light = carry(flat.filter(ImageFilter.GaussianBlur(130)))

# ── the plaster: clean wall out of the drawing, laid in at its own size ──
# Boxes in source coordinates that hold wall and nothing else — no pipe, no
# pilaster, no glasses, no bird, and above the cornice at every column in them.
# All of them sit above the glasses, which are the highest thing that is not
# wall. The one box tried below them caught the bird's cast shadow and printed
# grey clouds along the cornice.
POOL = [(320, 20, 560, 580), (640, 20, 1060, 580), (660, 20, 900, 560)]
rng = random.Random(SEED)
wall = light.copy()
for _ in range(PATCHES):
    px0, py0, px1, py1 = POOL[rng.randrange(len(POOL))]
    w = rng.randint(200, min(420, px1 - px0))
    h = rng.randint(200, min(420, py1 - py0))
    x = rng.randint(px0, px1 - w)
    y = rng.randint(py0, py1 - h)
    piece = src.crop((x, y, x + w, y + h))
    if rng.random() < 0.5: piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
    if rng.random() < 0.5: piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
    k = rng.uniform(0.88, 1.16)          # never far from 1:1, only enough to break a repeat
    piece = piece.resize((round(w * k), round(h * k)), Image.LANCZOS)
    pw, ph = piece.size
    blob = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(blob).rounded_rectangle(
        [pw * 0.16, ph * 0.16, pw * 0.84, ph * 0.84], radius=min(pw, ph) * 0.3, fill=255)
    blob = blob.filter(ImageFilter.GaussianBlur(min(pw, ph) * 0.11))
    wall.paste(piece, (rng.randint(-pw // 3, EW - pw + pw // 3),
                       rng.randint(-ph // 3, BAND_H - ph + ph // 3)), blob)

# Laid in evenly the plaster comes out as camouflage — peeling at the same rate
# everywhere, which no wall does. This is where it has come off and where it has
# not: broad soft stretches, and between them the wall is left nearly plain.
calm = Image.new("L", (EW, BAND_H), 0)
dc = ImageDraw.Draw(calm)
for _ in range(CALM):
    cx, cy = rng.randint(0, EW), rng.randint(0, BAND_H)
    rx, ry = rng.randint(260, 620), rng.randint(240, 560)
    dc.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
calm = calm.filter(ImageFilter.GaussianBlur(190))
wall = Image.composite(wall, ImageChops.blend(light, wall, 0.34), calm)

# the plaster keeps its grain; the light under it is the drawing's
wall = ImageChops.add(
    ImageChops.subtract(wall, wall.filter(ImageFilter.GaussianBlur(TONE_R)), 1, 128),
    light.filter(ImageFilter.GaussianBlur(TONE_R)), 1, -128)
# and its overall cast is set by the wall the join actually meets
ref = pic.crop((0, 0, 150, round(BAND_H * 0.73)))
mr = ImageStat.Stat(ref).mean
mw = ImageStat.Stat(wall.crop((EW - 400, 0, EW, round(BAND_H * 0.6)))).mean
wall = wall.point([min(255, round(v * mr[c] / mw[c]))
                   for c in range(3) for v in range(256)])

# the plaster is the wall's; the cornice keeps the drawn mouldings underneath it
above = Image.new("L", (EW, BAND_H), 0)
ImageDraw.Draw(above).polygon(
    [(0, 0), (EW, 0), (EW, CORNICE_Y - CORNICE_SLOPE * SEAM - 34),
     (0, CORNICE_Y + CORNICE_SLOPE * EXT - 34)], fill=255)
ext = Image.composite(wall, carried, above.filter(ImageFilter.GaussianBlur(12)))

band = Image.new("RGB", (BAND_W, BAND_H))
band.paste(ext, (0, 0))
join = Image.new("L", (PW, BAND_H), 255)
d = ImageDraw.Draw(join)
for i in range(SEAM):
    d.line([(i, 0), (i, BAND_H)], fill=round(255 * (i / SEAM) ** 0.9))
band.paste(pic, (EXT, 0), join)

band.save(OUT, "WEBP", quality=80, method=6)
print("%s  %dx%d  %.0f KB  (picture %d of %d)"
      % (OUT.name, band.width, band.height, OUT.stat().st_size / 1024, PW, BAND_W))
