#!/usr/bin/env python3
"""
Builds halo-art.webp — the picture that stands beside the hero copy.

There is almost nothing to do here, and that is the point. The version of this
script that came before it was long: the source then was a photographed
watercolour sheet, and to put a sheet of white paper on a white page you have
to flatten the light it was shot under, set its white point on --paper and fall
its four edges away to nothing, or the drawing sits in a grey rectangle. This
source is a born-digital illustration — saturated, opaque, full-bleed to its
own corners, with no paper in it and no lighting to correct. Every one of those
steps would now be damage.

So the picture is passed through as it was drawn. It is only resized, to about
twice the width it is ever displayed at, and encoded. Nothing is cropped here
either: the hero decides how much of the picture it shows, and it decides that
differently on a phone and on a wide display, so the file has to hold all of
it.

    python3 _build/make_art.py
"""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_build" / "src" / "halo3.png"
OUT = ROOT / "halo-art.webp"

# The picture is the hero band now rather than a card in a column, and the band
# gives it up to 880 CSS px on a wide screen — so 940 was barely 1x there and
# short of it on a retina display. It is written at the source's own width,
# which is as much as there is.
WIDTH = 1086

art = Image.open(SRC).convert("RGB")
if art.width > WIDTH:
    art = art.resize((WIDTH, round(art.height * WIDTH / art.width)), Image.LANCZOS)
art.save(OUT, "WEBP", quality=82, method=6)
print("%s  %dx%d  %.0f KB  (aspect %s)"
      % (OUT.name, art.width, art.height, OUT.stat().st_size / 1024,
         "%d / %d" % (art.width, art.height)))
