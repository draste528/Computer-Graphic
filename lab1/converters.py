"""Color model conversions.

All values are floats:
    R, G, B, C, M, Y, K, S, V     -> range [0, 1]
    H (hue)                       -> degrees in range [0, 360)
"""


def rgb_to_rgb(r, g, b):
    return r, g, b


# ---------------- CMYK ----------------

def rgb_to_cmyk(r, g, b):
    k = 1 - max(r, g, b)          # black = how far the brightest channel is from 1
    if k == 1:                    # pure black: C, M, Y are undefined -> 0
        return 0.0, 0.0, 0.0, 1.0
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return c, m, y, k


def cmyk_to_rgb(c, m, y, k):
    r = (1 - c) * (1 - k)
    g = (1 - m) * (1 - k)
    b = (1 - y) * (1 - k)
    return r, g, b


# ---------------- helpers for HSV ----------------

def _hue(r, g, b):
    """Hue in degrees."""
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:                    # gray: hue is undefined -> 0
        return 0.0
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60


def _from_chroma(h, c, m):
    """Build RGB from hue, chroma C and the lightness offset m."""
    h6 = (h % 360) / 60           # sector 0..5 on the color wheel
    x = c * (1 - abs(h6 % 2 - 1))  # second largest component
    sectors = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)]
    r, g, b = sectors[int(h6) % 6]
    return r + m, g + m, b + m


# ---------------- HSV ----------------

def rgb_to_hsv(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx
    s = 0.0 if mx == 0 else (mx - mn) / mx
    return _hue(r, g, b), s, v


def hsv_to_rgb(h, s, v):
    c = v * s                     # chroma
    return _from_chroma(h, c, v - c)

