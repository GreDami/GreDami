#!/usr/bin/env python3
"""
Builds halo-art.webp — the picture as it stands in the narrow arrangement.

From 1040px down the hero stops reading across: the bird stands at the head of
the band beside the headline, in a 3:4 frame the stylesheet lifts by a third
of its own height and runs off the right edge (site.css, "narrow"), and the
same file thrown out of focus is the field around him. Every number there was
set by where the bird stood in that frame in the drawing before this one —
glasses to tail across 37.6-75.3% of its width, head to foot across 43-77% of
its height — so the frame is cut to put him in the same place, and none of
those numbers has to move.

He is squarer than the drawn bird was, so the frame is matched across, where
it matters: his glasses on the same line, which is what keeps him clear of the
headline, and his tail a little further in, at 74%. The stylesheet runs the
frame off the right edge by a share of the screen's width, and on a short
landscape tablet that share came to a quarter of the frame — which the drawn
bird's tail was already touching. Up and down he is centred where the drawn
bird was.

The frame is taken at the picture's own scale, which makes it 762 x 1016. The
picture is 2:1 with the bird high and far right in it, so the frame reaches a
little way above the picture's top edge and past its right edge, into the wall
and the roof facets.py carries on there.

    python3 _build/make_art.py
"""
import pathlib

from facets import LEFT, TOP, canvas

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "halo-art.webp"

# the frame in picture px; he is x 1346-1624, y 320-626 in the picture
FRAME = (1060, -140, 1822, 876)

x0, y0, x1, y1 = FRAME
art = canvas().crop((LEFT + x0, TOP + y0, LEFT + x1, TOP + y1))
art.save(OUT, "WEBP", quality=82, method=6)
print("%s  %dx%d  %.0f KB  (aspect %d / %d)"
      % (OUT.name, art.width, art.height, OUT.stat().st_size / 1024, art.width, art.height))
