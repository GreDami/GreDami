#!/usr/bin/env python3
"""
Builds halo-band.webp — the wide plate the hero band carries edge to edge.

The picture is already about the band's shape: 2:1, the bird on his roof at
the right and open wall to the left of him, where the copy goes. But a screen
can be a good deal wider than 2:1, and `cover` on the picture alone would then
have to scale it by the width — the bird blown up, and the roof he stands on,
the one thing that says what he is, cropped off the foot of the band.

So the plate is the picture with the wall's facets carried on to its left,
taken from the canvas facets.py builds. Up to five times as wide as it is
tall, `cover` fits it by its height: the picture is shown whole and at the
right, and all a wider screen adds is more wall. Nothing in it is enlarged.

The picture fills nine tenths of the plate's height, not all of it, and the
rest is carried-on wall above it. At full height this bird stands larger in
the band than the drawing before him did, and his roof reaches further along
the foot of it, into the proof line under the buttons at the narrow end of
the wide layout. At nine tenths both are where the drawing had them — his
width and the foot of the roof each within a hundredth of a band-height — and
the copy's widths, which were set against the drawing, still hold.

    python3 _build/make_band.py
"""
import pathlib

from facets import TOP, EDGE, H, SH, SW, canvas

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "halo-band.webp"

ABOVE = round(SH / 0.9) - SH      # rows of carried-on wall over the picture

# the plate stops at the picture's own right edge, where `right` anchors it:
# the strip carried on past that edge is for the tall frame only
band = canvas().crop((0, TOP - ABOVE, EDGE, H))
band.save(OUT, "WEBP", quality=82, method=6)
print("%s  %dx%d  %.0f KB  (picture %d of %d, %d rows of wall over it)"
      % (OUT.name, band.width, band.height, OUT.stat().st_size / 1024, SW, EDGE, ABOVE))
