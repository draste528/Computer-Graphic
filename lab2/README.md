# Lab 2 — Image processing (variant 6)

Variant 6 = **point (element-wise) operations + linear contrast stretching** and
**global thresholding (2 methods, compared): iterative method and Otsu's method**.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

`tkinter` is part of Python (on macOS with Homebrew: `brew install python-tk@3.14`).
`numpy` is used for array math, `Pillow` only to read / write / show image files.
All algorithms are implemented by hand in `processing.py`.

## Files

| File | What it does |
|------|--------------|
| `processing.py` | all algorithms (point operations, stretching, histogram, thresholds) |
| `main.py` | GUI: choose an image and an operation, see original / result and both histograms |
| `images/` | test image set |
| `make_test_images.py` | script that generated `images/` (needs `scikit-image`, only for rebuilding) |

## How to use

1. Pick a test image (or `Open...` any file).
2. Pick an operation. If it has a parameter, move the slider — the result updates live.
3. Threshold lines are drawn on the histogram of the original image.
4. `Threshold: compare Otsu vs iterative` shows both results side by side:
   left = Otsu (red line), right = iterative (blue line).

---

## 1. Point operations

A point operation computes every output pixel only from the same input pixel:
`g(x, y) = T(f(x, y))`. Neighbours do not matter, so it changes brightness and contrast,
but cannot remove noise or sharpen. Values are clipped to `[0, 255]`.
For color images the same `T` is applied to R, G and B.

| Operation | Formula | Effect |
|-----------|---------|--------|
| Negative | `g = 255 - f` | inverts brightness; dark details become easier to see |
| Brightness | `g = f + c` | shifts the histogram left/right; contrast stays the same |
| Contrast | `g = 128 + k (f - 128)` | `k > 1` spreads levels from the middle, `k < 1` squeezes them |
| Gamma (power law) | `g = 255 (f / 255)^γ` | `γ < 1` brightens dark areas, `γ > 1` darkens bright areas |
| Logarithm | `g = c log(1 + f)`, `c = 255 / log 256` | strongly expands dark levels, compresses bright ones |

## 2. Linear contrast stretching

A low-contrast image uses only a narrow range `[low, high]` of the 256 levels.
Linear stretching maps this range onto the full range:

```
g = (f - low) * 255 / (high - low)
```

* `low`, `high` = min and max brightness of the image.
* Problem: a few very dark / very bright pixels (noise) make `low = 0`, `high = 255`, so nothing
  changes. Solution: the **clip %** parameter ignores that percent of the darkest and the brightest
  pixels (`low` / `high` become percentiles). Pixels outside are clipped to 0 / 255.
* For color images one `low` / `high` is used for all channels, so colors keep their hue.
* Unlike the contrast operation, the coefficients are chosen automatically from the image.

## 3. Global thresholding

Thresholding turns a gray image into a binary one: `g = 255 if f > T else 0`.
Global = one `T` for the whole image. Both methods find `T` from the histogram.

### Iterative method (basic global thresholding)

1. `T` = mean brightness of the image.
2. Split pixels into `G1` (`f > T`) and `G2` (`f <= T`), compute their means `m1`, `m2`.
3. `T = (m1 + m2) / 2`.
4. Repeat 2–3 until `T` changes by less than 0.5.

Simple and fast (2–15 iterations here). It moves from the start point to the **nearest**
stable `T`, so the result depends on where it starts.

### Otsu's method

For every possible `T = 0..255` compute the **between-class variance**

```
σB²(T) = P1 · P2 · (m1 − m2)²
```

`P1`, `P2` = fraction of pixels in each class, `m1`, `m2` = class means. Choose the `T` with the
largest `σB²`: classes are as far apart as possible. Everything is computed from cumulative
sums of the histogram, so it is one pass over 256 levels.
**Separability** `η = σB² / σ²` (0..1) shows how well the histogram splits into two classes.

Otsu checks **all** thresholds and takes the **global** best. A useful fact: at Otsu's optimum
`T` is also close to `(m1 + m2) / 2`, so on a normal two-class image both methods give almost
the same `T`. They differ when the histogram has a tiny class or more than two classes.

---

## Test images

| Image | Problem | What to show | Result |
|-------|---------|--------------|--------|
| `1_low_contrast.png` | levels only in `[90, 150]` | Linear stretching, clip 0 % | full range, histogram spread over 0..255 |
| `2_low_contrast_outliers.png` | low contrast + 0.4 % black/white noise pixels | Linear stretching: clip 0 % vs 1 % | 0 %: `[0, 255]`, **no change**; 1 %: `[100, 145]`, contrast restored |
| `3_dark.png` | too dark color photo | Gamma γ ≈ 0.3–0.4, Logarithm | shadows become visible; log over-brightens |
| `4_washed_out.png` | faded colors, range `[140, 230]` | Linear stretching; Gamma γ > 1 | stretching restores contrast and colors |
| `5_moon.png` | natural low-contrast photo | Linear stretching with clip 1–2 % | craters become visible |
| `6_coins.png` | clear two-peak histogram | Compare thresholds | Otsu T = 107, iterative T = 107 — **both good** |
| `7_stars.png` | tiny bright stars (≈ 1 % of pixels) on a noisy dark sky | Compare thresholds | **Otsu wins**: T ≈ 88, clean stars. Iterative: T ≈ 26, half of the sky noise becomes white |
| `8_frame_objects.png` | bright objects on a gray table, dark frame around the photo | Compare thresholds | **Iterative wins**: T ≈ 174, objects separated. Otsu: T ≈ 89, only the frame is separated |
| `9_uneven_light_text.png` | text with uneven lighting | Compare thresholds | **both fail**: one global T cannot fit dark and light parts — needs local thresholding |

### Why each method wins

* **Stars (Otsu better).** The mean brightness is almost the sky brightness. The iterative method
  starts there; the class "above T" is mostly sky noise, so `(m1 + m2) / 2` stays inside the sky
  peak — it gets stuck in a local solution. Otsu checks every T and finds the real gap between sky
  and stars.
* **Frame (iterative better).** The histogram has three peaks: frame (dark, 11 %), table (gray),
  objects (bright). Otsu maximizes `σB²` globally, and the biggest variance split is
  "very dark frame vs everything else" — correct by its criterion, useless for finding the
  objects. The iterative method starts at the mean (between table and objects) and converges to
  the nearest gap, which is exactly table vs objects.
* **Coins (equal).** Two clear classes of similar size → both criteria lead to the same gap.
* **Uneven light (both bad).** The limitation of any global method.

## Conclusions

1. Point operations change only the brightness scale. Gamma and log fix dark images,
   negative helps to see dark details, brightness/contrast are manual adjustments.
2. Linear contrast stretching automatically uses the full range `0..255`; clipping a small
   percent of extreme pixels is necessary, otherwise single noisy pixels block the stretching.
3. Otsu is more robust: it checks all thresholds, does not depend on a start point and gives a
   quality measure (separability). Good choice by default.
4. The iterative method is simpler and finds the gap nearest to the mean brightness; it can
   be better when the histogram has several classes and the needed gap is near the mean,
   but it can get stuck when one class is tiny.
5. With uneven lighting no global threshold works — local methods are needed.
