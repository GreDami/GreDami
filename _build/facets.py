"""
The low-poly hero picture, with its facets carried on past its edges.

halo4.png is a low-poly render, 1777 x 885: the bird on his roof at the right
and open yellow wall to the left of him. Both hero plates need picture the
picture does not have — the wide band more wall to the left, on a screen wider
than 2:1, and the tall frame a little more above the bird and to the right of
him — so make_band.py and make_art.py both cut their plate out of the one
canvas built here, with the picture laid in along its foot untouched. The two
plates therefore agree facet for facet.

The new facets are cut the way the picture's are: a Delaunay mesh over
scattered points, each face one flat colour, and every colour is the picture's
own wall, its pixels in order of lightness, so the palette cannot drift.
Nothing starts at the frame. Each edge of the picture that runs into it is
measured there and carried straight on, and the face between two such edges
keeps its colour until those edges meet or a new edge closes it — so the frame
is not a row of vertices, and no facet it cuts changes colour at it. The pole
behind the bird carries on too, narrowing the way the perspective already
narrows it until it closes to a point. New faces are drawn four times over and
brought down with the filter that made the picture's own edges, so old and new
edges are equally crisp.
"""
import math
import pathlib
import random

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_build" / "src" / "halo4.png"

SW, SH = 1777, 885          # the picture
LEFT, TOP = 3150, 180       # facets carried on to its left, and above it
RIGHT = 60                  # ...and a strip to its right, for the tall frame
EDGE = LEFT + SW            # the picture's right edge on the canvas
W, H = EDGE + RIGHT, TOP + SH
GAP = 200                   # spacing of new vertices: the picture's own facet size
SS = 4                      # new faces are drawn this many times over, then reduced
TILE = 256
SEED = 5                    # the wall is the same wall on every build


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def diff(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def runs(line):
    """The faces one edge of the frame cuts through, as [start, end, colour].
    A face ends where the colour steps, at the middle of the step."""
    n = len(line)
    # the step is read across one pixel either side: faces can meet the frame
    # only a few pixels apart, where a wider reading would run them together
    step = [diff(line[max(i - 1, 0)], line[min(i + 1, n - 1)]) >= 8 for i in range(n)]
    cuts, i = [0.0], 0
    while i < n:
        if step[i]:
            j = i
            while j < n and step[j]:
                j += 1
            cuts.append((i + j) / 2)
            i = j
        else:
            i += 1
    cuts.append(float(n))
    out = []
    for a, b in zip(cuts, cuts[1:]):
        inner = sorted(line[int(a) + 3:int(b) - 3] or line[int(a):int(b) + 1], key=lum)
        out.append([a, b, inner[len(inner) // 2]])
    return out


def edge_line(px, at, a, b, inward, reach=22):
    """The picture's edge between colours a and b where it meets the frame at
    `at` (picture px), as a point and a unit direction pointing out of the
    picture. The pixels that sit between the two colours are gathered near
    the frame and their main axis taken."""
    cx, cy = at
    near = []
    for y in range(max(0, int(cy - reach)), min(SH, int(cy + reach) + 1)):
        for x in range(max(0, int(cx - reach)), min(SW, int(cx + reach) + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 > reach * reach:
                continue
            ring = [px[x + dx, y + dy] for dx in (-2, 0, 2) for dy in (-2, 0, 2)
                    if 0 <= x + dx < SW and 0 <= y + dy < SH]
            if min(diff(c, a) for c in ring) <= 5 and min(diff(c, b) for c in ring) <= 5:
                near.append((x + 0.5, y + 0.5))
    # too little of the edge to read — two faces meeting at a vertex on the
    # frame itself — and it leaves the frame square
    if len(near) < 8:
        return (cx, cy), (-inward[0], -inward[1])
    mx = sum(p[0] for p in near) / len(near)
    my = sum(p[1] for p in near) / len(near)
    sxx = sum((p[0] - mx) ** 2 for p in near)
    syy = sum((p[1] - my) ** 2 for p in near)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in near)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(ang), math.sin(ang)
    if ux * -inward[0] + uy * -inward[1] < 0:
        ux, uy = -ux, -uy
    # an edge that only grazes the frame is held to a shallow angle, so it
    # still leaves the frame instead of running along it
    out = ux * -inward[0] + uy * -inward[1]
    if out < 0.26:
        side = (ux - out * -inward[0], uy - out * -inward[1])
        k = math.hypot(*side) or 1.0
        ux = 0.26 * -inward[0] + 0.966 * side[0] / k
        uy = 0.26 * -inward[1] + 0.966 * side[1] / k
    return (mx, my), (ux, uy)


def meet(p, u, q, v):
    """Where two rays p + s*u and q + t*v cross, as (s, t); None if parallel."""
    den = u[0] * v[1] - u[1] * v[0]
    if abs(den) < 1e-9:
        return None
    dx, dy = q[0] - p[0], q[1] - p[1]
    return (dx * v[1] - dy * v[0]) / den, (dx * u[1] - dy * u[0]) / den


def seam(px, rng, line, fold, inward, origin, pole=None):
    """Carry the picture's faces across one edge of the frame.

    `line` is the row or column of the frame's edge, `fold` turns a distance
    along it into a canvas point, `inward` points into the picture and
    `origin` places picture px on the canvas. `pole` is the pole's run on
    this edge and the heading of its far side. Returns the new faces as
    (polygon, colour, run) and the vertices their edges end on."""
    rs = runs(line)
    ox, oy = origin
    k, up = pole if pole else (None, None)
    crossings = []
    for i, ((a0, a1, ca), (b0, b1, cb)) in enumerate(zip(rs, rs[1:])):
        # the pole is not part of the wall. The face left of it is taken to
        # run on under it as far as its far side, and the pole itself is
        # carried on separately, over the top
        if k and i == k - 1:
            continue
        base = fold(a1)
        at = (base[0] - ox, base[1] - oy)
        if i == k:
            # the far side of the pole: the face left of it closes along the
            # same line the pole's own side is drawn on
            u = up
        else:
            p, u = edge_line(px, at, ca, cb, inward)
            # a line that misses the point where the faces meet on the frame
            # has been read off some other edge nearby, and is not used
            if abs((at[0] - p[0]) * u[1] - (at[1] - p[1]) * u[0]) > 3:
                u = (-inward[0], -inward[1])
        # the edge leaves from where the colour steps on the frame itself,
        # which is read to the pixel; the fitted line only gives it a heading.
        # How far out it runs is drawn widely, so the faces that close the
        # edges do not line up into a second frame a step outside the first.
        depth = rng.uniform(0.3, 1.35) * GAP
        out = abs(u[0] * inward[0] + u[1] * inward[1])
        crossings.append({"c": base, "u": u, "d": min(depth / out, 2 * GAP)})
    if k:
        rs[k - 1][1] = rs[k][1]
        del rs[k]
    # an edge ends at the nearer of its own length and where it meets a
    # neighbour, so two edges that close a face close it at one vertex
    for i, e in enumerate(crossings):
        for j in (i - 1, i + 1):
            if 0 <= j < len(crossings):
                f = crossings[j]
                m = meet(e["c"], e["u"], f["c"], f["u"])
                if m and m[0] > 0 and m[1] > 0 and m[0] < e["d"]:
                    e["d"] = m[0]
    for e in crossings:
        e["v"] = (e["c"][0] + e["d"] * e["u"][0], e["c"][1] + e["d"] * e["u"][1])
    faces = []
    for i, (a0, a1, colour) in enumerate(rs):
        poly = []
        if i == 0:
            poly += [fold(a0)]
        else:
            e = crossings[i - 1]
            poly += [e["c"], e["v"]]
        if i == len(rs) - 1:
            poly += [fold(a1)]
        else:
            e = crossings[i]
            poly += [e["v"], e["c"]]
        faces.append((poly, colour, (a0, a1)))
    return faces, [e["v"] for e in crossings]


def pole_sides(px):
    """The two straight sides of the pole's dark face as x = a + b*y in
    picture px: each leaves the frame where the colour steps on it, at the
    lean fitted over the rows above the bird."""
    top = runs([px[x, 0] for x in range(SW)])
    k = min(range(len(top)), key=lambda i: lum(top[i][2]))
    dark = top[k][2]
    rows, lefts, rights = [], [], []
    mid = (top[k][0] + top[k][1]) / 2
    for y in range(0, 141):
        xs = [x for x in range(int(mid) - 40, int(mid) + 40) if diff(px[x, y], dark) <= 14]
        if not xs:
            continue
        # sub-pixel sides: a blended pixel at either end counts by how far
        # it has gone over to the dark
        x0, x1 = min(xs), max(xs)

        def share(x):
            c = px[x, y]
            out = px[x - 3, y] if x < x0 else px[x + 3, y]
            return max(0.0, min(1.0, (lum(out) - lum(c)) / max(1.0, lum(out) - lum(dark))))

        rows.append(y + 0.5)
        lefts.append(x0 - share(x0 - 1))
        rights.append(x1 + 1 + share(x1 + 1))
        mid = (x0 + x1) / 2

    def lean(ys, xs):
        my, mx = sum(ys) / len(ys), sum(xs) / len(xs)
        return sum((y - my) * (x - mx) for y, x in zip(ys, xs)) / sum((y - my) ** 2 for y in ys)

    return k, dark, (top[k][0], lean(rows, lefts)), (top[k][1], lean(rows, rights))


def delaunay(points):
    """Bowyer–Watson. The mesh as triples of indices into points."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    span = 20 * max(max(xs) - min(xs), max(ys) - min(ys))
    mx, my = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    pts = list(points) + [(mx - span, my - span), (mx + span, my - span), (mx, my + span)]
    n = len(points)

    def circle(t):
        (ax, ay), (bx, by), (cx, cy) = pts[t[0]], pts[t[1]], pts[t[2]]
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        a2, b2, c2 = ax * ax + ay * ay, bx * bx + by * by, cx * cx + cy * cy
        ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
        uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
        return ux, uy, (ax - ux) ** 2 + (ay - uy) ** 2

    mesh = {(n, n + 1, n + 2): circle((n, n + 1, n + 2))}
    for i in range(n):
        x, y = pts[i]
        bad = [t for t, (ux, uy, rr) in mesh.items() if (x - ux) ** 2 + (y - uy) ** 2 < rr]
        rim = {}
        for t in bad:
            del mesh[t]
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                k = (min(a, b), max(a, b))
                rim[k] = rim.get(k, 0) + 1
        for (a, b), c in rim.items():
            if c == 1:
                mesh[(a, b, i)] = circle((a, b, i))
    return [t for t in mesh if max(t) < n]


def inside(p, poly):
    x, y = p
    hit = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def canvas():
    """The picture on a W x H canvas — its top-left corner at (LEFT, TOP),
    its foot on the canvas's foot — with its facets carried on over the rest."""
    art = Image.open(SRC).convert("RGB")
    assert art.size == (SW, SH), art.size
    px = art.load()
    rng = random.Random(SEED)

    # the wall's own paint: the open facets left of the roof, pixel by pixel,
    # in order of lightness. Pixels on an edge are left out so no blend is
    # picked.
    paints = sorted((px[x, y] for y in range(3, SH - 3, 3) for x in range(3, 860, 3)
                     if max(diff(px[x, y], px[x + dx, y + dy])
                            for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3))) <= 4),
                    key=lum)

    def paint(t):
        return paints[min(len(paints) - 1, max(0, int(t * len(paints))))]

    # ── the frame's three cut edges, carried on ──
    pole_k, pole_dark, (la, lb), (ra, rb) = pole_sides(px)
    left_faces, left_ends = seam(px, rng, [px[0, y] for y in range(SH)],
                                 lambda s: (LEFT, TOP + s), (1, 0), (LEFT, TOP))
    top_faces, top_ends = seam(px, rng, [px[x, 0] for x in range(SW)],
                               lambda s: (LEFT + s, TOP), (0, 1), (LEFT, TOP),
                               pole=(pole_k, (-rb / math.hypot(rb, 1), -1 / math.hypot(rb, 1))))
    # the right edge runs down through the roof as well as the wall; the roof
    # is flat faces too, so it carries on the same way
    right_faces, right_ends = seam(px, rng, [px[SW - 1, y] for y in range(SH)],
                                   lambda s: (EDGE, TOP + s), (-1, 0), (LEFT, TOP))

    # the corners above the picture: the face each one is in is cut by two
    # edges of the frame, and its two halves close on one vertex off the corner
    corner = (LEFT - 0.55 * GAP, TOP - 0.55 * GAP)
    left_faces[0][0].insert(1, corner)
    top_faces[0][0].insert(1, corner)
    corner_r = (EDGE + 0.55 * GAP, TOP - 0.55 * GAP)
    top_faces[-1][0].insert(-1, corner_r)
    right_faces[0][0].insert(1, corner_r)
    # the feet of the two side edges run off the canvas, as the picture's
    # faces do
    for faces, x in ((left_faces, LEFT), (right_faces, EDGE)):
        foot = faces[-1][0]
        foot[-1:-1] = [(foot[-2][0], H + 0.5 * GAP), (x, H + 0.5 * GAP)]
    band = left_faces + top_faces + right_faces

    # ── the rest of the field ──
    pts, room = [], []
    for v in left_ends + top_ends + right_ends + [corner, corner_r]:
        # two edges that close one face end on the same vertex; it goes in once
        if all(abs(v[0] - q[0]) + abs(v[1] - q[1]) > 1 for q in pts):
            pts.append(v)
            room.append(0.8 * GAP)
    # a ring just outside the canvas, so the mesh covers it to the edge
    for x in range(-GAP, W + GAP, GAP):
        pts.append((x + rng.uniform(-0.3, 0.3) * GAP, -0.4 * GAP + rng.uniform(-0.1, 0.1) * GAP))
        room.append(GAP)
    for y in range(0, H + GAP, GAP):
        pts.append((-0.4 * GAP + rng.uniform(-0.1, 0.1) * GAP, y + rng.uniform(-0.3, 0.3) * GAP))
        room.append(GAP)
    for x in range(0, LEFT - GAP // 2, GAP):
        pts.append((x + rng.uniform(-0.3, 0.3) * GAP, H + 0.4 * GAP + rng.uniform(-0.1, 0.1) * GAP))
        room.append(GAP)
    misses = 0
    while misses < 6000:
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if x > LEFT - 0.3 * GAP and y > TOP - 0.3 * GAP:
            misses += 1
            continue
        r = GAP * rng.uniform(0.7, 1.5)
        if (any((x - qx) ** 2 + (y - qy) ** 2 < ((r + qr) / 2) ** 2
                for (qx, qy), qr in zip(pts, room))
                or any(inside((x, y), f[0]) for f in band)):
            misses += 1
            continue
        pts.append((x, y))
        room.append(r)
        misses = 0

    # lightness drifts across the field in broad swells, and each face is
    # nudged off it, the way the picture's own faces sit
    swell = Image.new("L", (9, 3))
    swell.putdata([rng.randint(0, 255) for _ in range(9 * 3)])
    swell = swell.resize((W, H), Image.BICUBIC)

    field = []
    for t in delaunay(pts):
        tri = [pts[i] for i in t]
        cx, cy = sum(p[0] for p in tri) / 3, sum(p[1] for p in tri) / 3
        if LEFT < cx < EDGE and cy > TOP:
            continue
        s = swell.getpixel((min(W - 1, max(0, int(cx))), min(H - 1, max(0, int(cy))))) / 255
        field.append((tri, paint(0.5 + 0.4 * (s - 0.5) + rng.uniform(-0.3, 0.3))))

    # each carried-on face also reaches a little way in under the picture, so
    # the reducing filter finds the same colour on both sides of the frame
    under = []
    for poly, colour, (a0, a1) in left_faces:
        under.append(([(LEFT, TOP + a0), (LEFT + 8, TOP + a0),
                       (LEFT + 8, TOP + a1), (LEFT, TOP + a1)], colour))
    for poly, colour, (a0, a1) in top_faces:
        under.append(([(LEFT + a0, TOP), (LEFT + a1, TOP),
                       (LEFT + a1, TOP + 8), (LEFT + a0, TOP + 8)], colour))
    for poly, colour, (a0, a1) in right_faces:
        under.append(([(EDGE - 8, TOP + a0), (EDGE, TOP + a0),
                       (EDGE, TOP + a1), (EDGE - 8, TOP + a1)], colour))

    # the pole, from a little under the frame up to where its sides meet
    apex_y = (ra - la) / (lb - rb)
    spire = [(LEFT + la + lb * 8, TOP + 8), (LEFT + ra + rb * 8, TOP + 8),
             (LEFT + la + lb * apex_y, TOP + apex_y)]

    shapes = field + [(p, c) for p, c, _ in band] + under + [(spire, pole_dark)]
    boxes = [(min(p[0] for p in s), min(p[1] for p in s),
              max(p[0] for p in s), max(p[1] for p in s)) for s, _ in shapes]

    out = Image.new("RGB", (W, H), paint(0.5))
    m = 6       # the reducing filter reaches this far past a tile's edge
    for ty in range(0, H, TILE):
        for tx in range(0, W, TILE):
            tw, th = min(TILE, W - tx), min(TILE, H - ty)
            if tx >= LEFT + m and ty >= TOP + m and tx + tw <= EDGE - m:
                continue
            x0, y0 = tx - m, ty - m
            x1, y1 = tx + tw + m, ty + th + m
            tile = Image.new("RGB", ((x1 - x0) * SS, (y1 - y0) * SS), paint(0.5))
            draw = ImageDraw.Draw(tile)
            for (poly, colour), (bx0, by0, bx1, by1) in zip(shapes, boxes):
                if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
                    continue
                draw.polygon([((x - x0) * SS, (y - y0) * SS) for x, y in poly], fill=colour)
            tile = tile.resize((x1 - x0, y1 - y0), Image.LANCZOS)
            out.paste(tile.crop((m, m, m + tw, m + th)), (tx, ty))

    out.paste(art, (LEFT, TOP))
    return out
