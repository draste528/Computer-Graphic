"""Image processing algorithms (variant 6).

1. Point (element-wise) operations + linear contrast stretching.
2. Global thresholding: iterative method and Otsu's method.

Images are numpy arrays of uint8 (0..255): shape (H, W) for gray, (H, W, 3) for RGB.
Every algorithm is written by hand with numpy; no ready-made library functions.
"""
import numpy as np


def to_gray(img):
    """RGB -> gray with the standard luminance weights (ITU-R BT.601)."""
    if img.ndim == 2:
        return img
    gray = 0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]
    return np.round(gray).astype(np.uint8)


def histogram(gray):
    """Number of pixels for every brightness level 0..255."""
    return np.bincount(gray.ravel(), minlength=256)


def _clip(values):
    """Float values -> valid uint8 image."""
    return np.clip(np.round(values), 0, 255).astype(np.uint8)


# ---------------- point operations: g(x, y) = T(f(x, y)) ----------------

def negative(img):
    return 255 - img


def brightness(img, c):
    """g = f + c"""
    return _clip(img.astype(float) + c)


def contrast(img, k):
    """g = 128 + k * (f - 128): k > 1 increases contrast, k < 1 decreases it."""
    return _clip(128 + k * (img.astype(float) - 128))


def gamma(img, g):
    """Power law: s = 255 * (f / 255) ^ gamma. gamma < 1 brightens dark areas."""
    return _clip(255 * (img / 255.0) ** g)


def log_transform(img):
    """s = c * log(1 + f), c chosen so that 255 -> 255. Expands dark levels."""
    c = 255 / np.log(256)
    return _clip(c * np.log1p(img.astype(float)))


def linear_stretch(img, clip_percent=0.0):
    """Linear contrast stretching: [low, high] -> [0, 255].

    low / high are the min / max brightness, optionally ignoring `clip_percent` %
    of the darkest and of the brightest pixels (so a few outliers do not block it).
    The same low / high are used for all color channels, so colors keep their hue.
    """
    low, high = np.percentile(img, [clip_percent, 100 - clip_percent])
    if high <= low:  # flat image: nothing to stretch
        return img.copy(), low, high
    return _clip((img.astype(float) - low) * 255 / (high - low)), low, high


# ---------------- global thresholding ----------------

def threshold(gray, t):
    """Binary image: white (255) where brightness > t, black (0) otherwise."""
    return np.where(gray > t, 255, 0).astype(np.uint8)


def iterative_threshold(gray, eps=0.5):
    """Basic global thresholding (iterative, Gonzalez & Woods).

    1. Start with T = mean brightness.
    2. Split pixels into G1 (> T) and G2 (<= T), find their means m1 and m2.
    3. New T = (m1 + m2) / 2. Repeat until T changes by less than eps.
    Returns (T, number of iterations).
    """
    hist = histogram(gray).astype(float)
    levels = np.arange(256)
    t = (hist * levels).sum() / hist.sum()
    for iteration in range(1, 256):
        low, high = levels <= t, levels > t
        m2 = (hist[low] * levels[low]).sum() / max(hist[low].sum(), 1)
        m1 = (hist[high] * levels[high]).sum() / max(hist[high].sum(), 1)
        new_t = (m1 + m2) / 2
        if abs(new_t - t) < eps:
            return new_t, iteration
        t = new_t
    return t, iteration


def otsu_threshold(gray):
    """Otsu's method: choose T that maximizes the between-class variance

        sigma_B^2(T) = P1 * P2 * (m1 - m2)^2

    where P1, P2 are class probabilities and m1, m2 are class means.
    Returns (T, separability eta = sigma_B^2 / sigma_total^2, in 0..1).
    """
    p = histogram(gray) / gray.size           # probability of each level
    levels = np.arange(256)
    p1 = np.cumsum(p)                         # P1(k): probability of class "<= k"
    m = np.cumsum(p * levels)                 # cumulative mean up to k
    mg = m[-1]                                # global mean
    with np.errstate(divide="ignore", invalid="ignore"):
        sigma_b = (mg * p1 - m) ** 2 / (p1 * (1 - p1))
    sigma_b = np.nan_to_num(sigma_b)          # p1 = 0 or 1 -> one class is empty
    best = sigma_b.max()
    t = levels[sigma_b == best].mean()        # several maxima -> take their middle
    sigma_g = (p * (levels - mg) ** 2).sum()  # total variance
    eta = best / sigma_g if sigma_g > 0 else 0.0
    return t, eta
