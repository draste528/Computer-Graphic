"""Generates the test image set in images/ (already generated, run only to rebuild).

Needs: pip install scikit-image   (only for the sample photos)
"""
from pathlib import Path

import numpy as np
from PIL import Image
from skimage import data

OUT = Path(__file__).parent / "images"
rng = np.random.default_rng(42)


def save(name, img):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / name)


def discs(shape, count, r_min, r_max):
    """Boolean mask with `count` random filled circles."""
    h, w = shape
    yy, xx = np.mgrid[:h, :w]
    mask = np.zeros(shape, bool)
    for _ in range(count):
        r = rng.uniform(r_min, r_max)
        cy, cx = rng.uniform(r, h - r), rng.uniform(r, w - r)
        mask |= (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r
    return mask


def main():
    OUT.mkdir(exist_ok=True)
    camera = data.camera().astype(float)
    astro = data.astronaut().astype(float)

    # ---- point operations / linear contrast stretching ----
    # 1. Low contrast: brightness squeezed into [90, 150]
    save("1_low_contrast.png", 90 + camera * 60 / 255)
    # 2. Low contrast + a few black/white outlier pixels: plain min-max stretch fails
    img = 100 + camera * 50 / 255
    noise = rng.random(img.shape)
    img[noise < 0.002] = 0
    img[noise > 0.998] = 255
    save("2_low_contrast_outliers.png", img)
    # 3. Too dark color photo (fix: gamma < 1 or log)
    save("3_dark.png", 255 * (astro / 255) ** 3)
    # 4. Washed-out (faded) color photo: range [140, 230]
    save("4_washed_out.png", 140 + astro * 90 / 255)
    # 5. Natural low-contrast photo
    save("5_moon.png", data.moon())

    # ---- global thresholding ----
    # 6. Clear bimodal histogram: both methods work
    save("6_coins.png", data.coins())

    # 7. Tiny bright stars (~1 % of pixels) on a noisy dark sky: Otsu wins.
    #    The iterative method starts at the mean (= sky) and gets stuck there.
    h, w = 400, 600
    sky = rng.normal(25, 10, (h, w))
    stars = discs((h, w), 60, 1.5, 3.5)
    sky[stars] = rng.normal(150, 25, stars.sum())
    save("7_stars.png", sky)

    # 8. Bright objects on a gray table + dark frame around the photo: iterative wins.
    #    Otsu's global optimum separates the dark frame from everything else.
    img = rng.normal(150, 6, (h, w))
    objects = discs((h, w), 22, 30, 45)
    img[objects] = rng.normal(220, 6, objects.sum())
    border = 14
    frame = np.ones((h, w), bool)
    frame[border:-border, border:-border] = False
    img[frame] = rng.normal(25, 8, frame.sum())
    save("8_frame_objects.png", img)

    # 9. Text with uneven lighting: no single global threshold works (needs local methods)
    page = data.page()
    save("9_uneven_light_text.png", page)


if __name__ == "__main__":
    main()
