#!/usr/bin/env python3
"""
Builds halo-band.webp — the wide plate the hero band carries edge to edge.

halo-art.webp is the drawing as it was drawn: tall, 3:4, and right for a phone,
where the band is read down the page. A screen-wide band is the opposite shape,
and `cover` on a 3:4 picture stretched across 2.4:1 blows the bird up to the
full height of the band and crops away the cornice he is standing on — the one
thing that says what he is. There is no crop of that file that works there.

So this writes a second plate in the band's own proportions, with the picture
kept at its own scale on the right and the wall carried on to the left edge.
The extension is not invented: every part of it comes out of the drawing.

  · The picture loses its left quarter first — the shutter, the downpipe and
    the pilaster beside them. Those are vertical edges, and an edge cannot be
    continued sideways; what is left at the cut is plain wall, which can.

  · The cornice is a moulding, so it is a straight extrusion: repeating the
    cross-section at the cut along the line's own slope continues it exactly.
    The slope was measured off the drawn edge (-0.5045), and at that angle it
    runs out of the bottom of the plate about 300px to the left. Everything
    further left is wall all the way down.

  · The wall is one clean piece of plaster from above the bird, opened out
    across the whole extension. Opened out rather than tiled: a repeat at this
    size is the first thing the eye finds, and nothing here repeats. It reads
    as the same wall nearer the eye, which is what it would be.

  · Its light is not its own. The low frequencies are replaced by those of the
    cross-section carried leftwards, so the tone at every height is the tone
    the drawing has at that height, and the join is a change of texture with
    no change of colour across it.

    python3 _build/make_band.py
"""
import pathlib

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC  = ROOT / "_build" / "src" / "halo3.png"
OUT  = ROOT / "halo-band.webp"

# The cut has to land on plain wall. At 185 it cleared the downpipe but not the
# shadow beside it, and a dark column carried leftwards puts a dark bar down the
# join — the one place in the plate that must not have a line in it.
CUT            = 300          # px off the left of the source: shutter, pipe, pilaster
BAND_W, BAND_H = 2400, 1200   # the band's own proportions, near 2:1
SEAM           = 240          # how far the picture is blended into the wall
CORNICE_SLOPE  = 0.5045       # rows the cornice falls for every column to the left
CORNICE_AT_185 = 1049.0       # where it met the wall when the cut was there
TONE_R         = 420          # everything slower than this is taken from the drawing

src = Image.open(SRC).convert("RGB")
pic = src.crop((CUT, 0, src.width, src.height))
SCALE = BAND_H / src.height
pic = pic.resize((round(pic.width * SCALE), BAND_H), Image.LANCZOS)
PW  = pic.width
EXT = BAND_W - PW
# The wall is built wider than the gap it fills. The picture is faded into it
# over SEAM px, and a fade needs something underneath it for its whole length —
# built to EXT exactly, the first frames of the crossfade had bare plate under
# them and the join came out as a black line down the band.
EW  = EXT + SEAM
# the same drawn line, read at wherever the cut now falls
CORNICE_Y = CORNICE_AT_185 - CORNICE_SLOPE * SCALE * (CUT - 185)

# ── the cut's own cross-section, carried leftwards down the cornice's slope ──
PAD  = int(CORNICE_SLOPE * EXT) + 8
col  = pic.crop((0, 0, 5, BAND_H)).resize((1, BAND_H), Image.LANCZOS)
tall = Image.new("RGB", (1, BAND_H + PAD))
tall.paste(col.crop((0, 0, 1, 1)).resize((1, PAD)), (0, 0))   # wall carried on up
tall.paste(col, (0, PAD))
carried = tall.resize((EW, BAND_H + PAD), Image.NEAREST).transform(
    (EW, BAND_H), Image.AFFINE,
    (1, 0, 0, CORNICE_SLOPE, 1, PAD - CORNICE_SLOPE * EXT), Image.BILINEAR)

# ── the plaster: one piece of wall from above the bird, opened out, and put
#    back on the drawing's own light ──
patch = pic.crop((20, 0, PW, 470))
ref   = pic.crop((0, 0, 150, 880))                 # the wall right at the join
mr, mp = ImageStat.Stat(ref).mean, ImageStat.Stat(patch).mean
patch = patch.point([min(255, round(v * mr[c] / mp[c]))
                     for c in range(3) for v in range(256)])
opened = patch.resize((EW, BAND_H), Image.LANCZOS) \
              .filter(ImageFilter.UnsharpMask(3, 55, 3))
wall = ImageChops.add(
    ImageChops.subtract(opened, opened.filter(ImageFilter.GaussianBlur(TONE_R)), 1, 128),
    carried.filter(ImageFilter.GaussianBlur(TONE_R)), 1, -128)

# the plaster is the wall's; the cornice keeps the drawn mouldings underneath it
above = Image.new("L", (EW, BAND_H), 0)
ImageDraw.Draw(above).polygon(
    [(0, 0), (EW, 0), (EW, CORNICE_Y - CORNICE_SLOPE * SEAM - 30),
     (0, CORNICE_Y + CORNICE_SLOPE * EXT - 30)], fill=255)
ext = Image.composite(wall, carried, above.filter(ImageFilter.GaussianBlur(10)))

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
