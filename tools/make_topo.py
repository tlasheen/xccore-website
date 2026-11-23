#!/usr/bin/env python3
"""Writes assets/img/topo.svg: faint topographic contour lines, a seamless
tile for section backgrounds (standard-library Python only).

  python tools/make_topo.py
"""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = H = 600


def height(x, y):
    """A smooth, tileable surface: a few hills from periodic sines."""
    t = 2 * math.pi
    return (math.sin(t * x / W) * math.cos(t * y / H)
            + 0.6 * math.sin(t * 2 * (x + y) / W + 1.3)
            + 0.45 * math.cos(t * 3 * x / W - 0.7) * math.sin(t * 2 * y / H + 0.4))


def contours(levels, step=12):
    """Line segments of each level by marching squares over the tile."""
    n = W // step
    vals = [[height(i * step, j * step) for i in range(n + 1)] for j in range(n + 1)]
    paths = []
    for lv in levels:
        segs = []
        for j in range(n):
            for i in range(n):
                c = [vals[j][i], vals[j][i + 1], vals[j + 1][i + 1], vals[j + 1][i]]
                pts = [(i * step, j * step), ((i + 1) * step, j * step),
                       ((i + 1) * step, (j + 1) * step), (i * step, (j + 1) * step)]
                cross = []
                for k in range(4):
                    a, b = c[k], c[(k + 1) % 4]
                    if (a - lv) * (b - lv) < 0:
                        f = (lv - a) / (b - a)
                        (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % 4]
                        cross.append((x0 + f * (x1 - x0), y0 + f * (y1 - y0)))
                if len(cross) >= 2:
                    segs.append((cross[0], cross[1]))
                if len(cross) == 4:
                    segs.append((cross[2], cross[3]))
        paths.append("".join("M%.0f %.0fL%.0f %.0f" % (a[0], a[1], b[0], b[1]) for a, b in segs))
    return paths


def main():
    levels = [v / 3 for v in range(-5, 6)]
    paths = contours(levels)
    body = "".join('<path d="%s"/>' % p for p in paths)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">'
           '<g fill="none" stroke="#0e2a47" stroke-opacity="0.09" stroke-width="1.1" '
           'stroke-linecap="round">%s</g></svg>\n' % (W, H, W, H, body))
    out = os.path.join(ROOT, "assets", "img", "topo.svg")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    print("%s: %d bytes" % (out, len(svg)))


if __name__ == "__main__":
    main()
