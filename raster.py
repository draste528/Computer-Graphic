"""Basic raster algorithms.

Every function returns (pixels, log):
    pixels - list of (x, y) integer cells, or (x, y, intensity) for Wu's algorithm
    log    - list of text lines with the intermediate calculations

Pass log=False to skip the text log (used for time measurement).
"""
import math


def rnd(v):
    """Round half up (Python's round() rounds 0.5 to even, which looks inconsistent)."""
    return math.floor(v + 0.5)


# ---------------- 1. Step-by-step algorithm ----------------

def step_by_step(x0, y0, x1, y1, log=True):
    """Use the line equation y = y0 + k (x - x0) directly, one step along the longer axis."""
    dx, dy = x1 - x0, y1 - y0
    pixels, lines = [], []
    if dx == 0 and dy == 0:
        return [(x0, y0)], ["single point"]
    if abs(dx) >= abs(dy):                       # gentle line: step along x
        k = dy / dx
        if log:
            lines.append(f"k = dy/dx = {dy}/{dx} = {k:.4f};  y = {y0} + k*(x - {x0})")
        step = 1 if dx > 0 else -1
        for x in range(x0, x1 + step, step):
            y = y0 + k * (x - x0)
            pixels.append((x, rnd(y)))
            if log:
                lines.append(f"x = {x:4}  y = {y:8.3f}  -> ({x}, {rnd(y)})")
    else:                                        # steep line: step along y
        k = dx / dy
        if log:
            lines.append(f"1/k = dx/dy = {dx}/{dy} = {k:.4f};  x = {x0} + (y - {y0})/k")
        step = 1 if dy > 0 else -1
        for y in range(y0, y1 + step, step):
            x = x0 + k * (y - y0)
            pixels.append((rnd(x), y))
            if log:
                lines.append(f"y = {y:4}  x = {x:8.3f}  -> ({rnd(x)}, {y})")
    return pixels, lines


# ---------------- 2. DDA (digital differential analyzer) ----------------

def dda(x0, y0, x1, y1, log=True):
    """Increments instead of multiplication: x += dx/L, y += dy/L, L = max(|dx|, |dy|)."""
    dx, dy = x1 - x0, y1 - y0
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return [(x0, y0)], ["single point"]
    x_inc, y_inc = dx / steps, dy / steps
    x, y = float(x0), float(y0)
    pixels = []
    lines = [f"L = max(|dx|, |dy|) = {steps};  x_inc = {dx}/{steps} = {x_inc:.4f};  "
             f"y_inc = {dy}/{steps} = {y_inc:.4f}"] if log else []
    for i in range(steps + 1):
        pixels.append((rnd(x), rnd(y)))
        if log:
            lines.append(f"i = {i:3}  x = {x:8.3f}  y = {y:8.3f}  -> ({rnd(x)}, {rnd(y)})")
        x += x_inc
        y += y_inc
    return pixels, lines


# ---------------- 3. Bresenham line ----------------

def bresenham_line(x0, y0, x1, y1, log=True):
    """Integer-only. err = dx - dy tracks (scaled by 2) the distance to the ideal line."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 >= x0 else -1
    sy = 1 if y1 >= y0 else -1
    err = dx - dy
    x, y = x0, y0
    pixels = []
    lines = [f"dx = {dx}, dy = {dy}, sx = {sx}, sy = {sy}, err0 = dx - dy = {err}"] if log else []
    while True:
        pixels.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        moves = []
        if e2 > -dy:            # error allows a step in x
            err -= dy
            x += sx
            moves.append("x")
        if e2 < dx:             # error allows a step in y
            err += dx
            y += sy
            moves.append("y")
        if log:
            lines.append(f"({pixels[-1][0]}, {pixels[-1][1]})  2err = {e2:4}  "
                         f"step {'+'.join(moves):3} -> err = {err}")
    return pixels, lines


# ---------------- 4. Bresenham circle ----------------

def bresenham_circle(xc, yc, r, log=True):
    """Compute 1/8 of the circle (x from 0 to y), mirror it to the other 7 octants.

    Decision d = 3 - 2r chooses between (x+1, y) and (x+1, y-1):
        d < 0  -> keep y,  d += 4x + 6
        d >= 0 -> y -= 1,  d += 4(x - y) + 10
    """
    x, y, d = 0, r, 3 - 2 * r
    pixels = set()
    lines = [f"x = 0, y = R = {r}, d0 = 3 - 2R = {d}"] if log else []
    while x <= y:
        for px, py in ((x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)):
            pixels.add((xc + px, yc + py))
        if log:
            lines.append(f"({x:3}, {y:3})  d = {d:5}  -> "
                         + ("d < 0: keep y" if d < 0 else "d >= 0: y - 1"))
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1
    return sorted(pixels), lines


# ---------------- bonus: Castle-Pitteway ----------------

def castle_pitteway(x0, y0, x1, y1, log=True):
    """Builds the line as a word of moves: s = straight step, d = diagonal step.

    For 0 <= dy <= dx (first octant):
        x = dx - dy, y = dy, m1 = "s", m2 = "d"
        while x != y:
            if x > y: x -= y; m2 = m1 + reverse(m2)
            else:     y -= x; m1 = m2 + reverse(m1)
        result = (m2 + reverse(m1)) repeated x times
    It is Euclid's algorithm on (dx - dy, dy). Other octants: mirror / swap axes.
    """
    dx, dy = x1 - x0, y1 - y0
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    a, b = abs(dx), abs(dy)
    swap = b > a                       # steep line: work with swapped axes
    if swap:
        a, b = b, a
    lines = [f"|dx| = {a}, |dy| = {b} (axes swapped: {swap})"] if log else []
    if b == 0:
        word = "s" * a
    elif a == b:
        word = "d" * a
    else:
        x, y, m1, m2 = a - b, b, "s", "d"
        while x != y:
            if x > y:
                x -= y
                m2 = m1 + m2[::-1]
            else:
                y -= x
                m1 = m2 + m1[::-1]
            if log:
                lines.append(f"x = {x:3}, y = {y:3}, m1 = {m1}, m2 = {m2}")
        word = (m2 + m1[::-1]) * x
    if log:
        lines.append(f"moves: {word}")
    # turn the word into pixels
    u, v = 0, 0
    pixels = [(x0, y0)]
    for m in word:
        u += 1
        if m == "d":
            v += 1
        px, py = (v, u) if swap else (u, v)
        pixels.append((x0 + sx * px, y0 + sy * py))
    return pixels, lines


# ---------------- bonus: Wu's antialiased line ----------------

def wu_line(x0, y0, x1, y1, log=True):
    """Each step paints the 2 cells closest to the ideal line.

    Intensity of a cell = 1 - its distance to the line, so the line looks smooth.
    """
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:                                    # work as if the line were gentle
        x0, y0, x1, y1 = y0, x0, y1, x1
    if x0 > x1:
        x0, x1, y0, y1 = x1, x0, y1, y0
    dx, dy = x1 - x0, y1 - y0
    k = dy / dx if dx else 0.0
    pixels = []
    lines = [f"k = {k:.4f}"] if log else []
    for x in range(x0, x1 + 1):
        y = y0 + k * (x - x0)
        y_int = math.floor(y)
        frac = y - y_int                         # distance to the lower cell
        for cy, c in ((y_int, 1 - frac), (y_int + 1, frac)):
            if c > 0:
                pixels.append((cy, x, c) if steep else (x, cy, c))
        if log:
            lines.append(f"x = {x:4}  y = {y:7.3f}  -> {y_int}: {1 - frac:.2f}, "
                         f"{y_int + 1}: {frac:.2f}")
    return pixels, lines


ALGORITHMS = {
    "Step-by-step": step_by_step,
    "DDA": dda,
    "Bresenham line": bresenham_line,
    "Bresenham circle": bresenham_circle,
    "Castle-Pitteway (bonus)": castle_pitteway,
    "Wu antialiased line (bonus)": wu_line,
}
