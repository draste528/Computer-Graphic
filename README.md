# Lab 3 — Basic raster algorithms

Step-by-step, DDA, Bresenham line, Bresenham circle
(+ bonus: Castle-Pitteway, Wu's antialiased line).

## Run

```bash
python3 main.py      # GUI, only the standard library (tkinter)
python3 bench.py     # time measurement for the report
```

On macOS with Homebrew Python: `brew install python-tk@3.14` if `import tkinter` fails.

## Files

| File | What it does |
|------|--------------|
| `raster.py` | all algorithms; each returns the pixels and a log of intermediate calculations |
| `main.py` | GUI: grid, axes, labels, zoom, drawing, calculation log, timing |
| `bench.py` | measures the time of every algorithm on long lines and big circles |

## How to use

* Choose an algorithm, enter `(x0, y0)`–`(x1, y1)` (circle: center `(x0, y0)` and `R`), press **Draw**.
  Shapes stay on the canvas until **Clear**, so algorithms can be compared on top of each other.
* The **Calculations** panel shows every step of the algorithm and the time of one call.
* **Scale** slider or mouse wheel = zoom (cell size 3–60 px), drag with the mouse = move.
* Red line = the ideal (mathematical) line / circle, for comparison with the pixels.
* **Benchmark** times all algorithms on the same long lines.

## Integer coordinates and the grid

A pixel with integer coordinates `(x, y)` is a square grid cell whose **center** is the
point `(x, y)`. Cell borders (the light grid lines) lie at `x ± 0.5`, `y ± 0.5`.
The axes pass through the centers of the cells `x = 0` and `y = 0`, the Y axis points up.
So a pixel is chosen by rounding the ideal coordinate to the nearest integer:
`y = 2.4 → pixel 2`, `y = 2.6 → pixel 3`, and the error of any pixel is at most 0.5 cell.

Screen mapping: `sx = cx + x · cell`, `sy = cy − y · cell` (`cx, cy` = canvas center + pan offset).

## Algorithms

Line from `(x0, y0)` to `(x1, y1)`, `dx = x1 − x0`, `dy = y1 − y0`.

| Algorithm | Idea | Per pixel |
|-----------|------|-----------|
| Step-by-step | `y = y0 + k (x − x0)`, `k = dy/dx`, step along the longer axis | 1 float multiply + add + round |
| DDA | `L = max(|dx|, |dy|)`, `x += dx/L`, `y += dy/L` | 2 float adds + 2 rounds |
| Bresenham line | integer error `err = dx − dy`; `e2 = 2·err`: if `e2 > −dy` step x, `err −= dy`; if `e2 < dx` step y, `err += dx` | integer add / compare |
| Bresenham circle | 1/8 of the circle, `d = 3 − 2R`; `d < 0`: `d += 4x + 6`; else `d += 4(x − y) + 10`, `y −= 1`; mirror ×8 | integer, 8 pixels per step |
| Castle-Pitteway | Euclid's algorithm on `(dx − dy, dy)` builds the word of moves `s` (straight) / `d` (diagonal) | string building, no arithmetic per pixel |
| Wu | 2 cells per step, brightness = `1 − distance` to the ideal line | float + 2 pixels |

Step-by-step steps along the longer axis, otherwise a steep line would have gaps.

### Worked example: Bresenham, (0, 0) → (8, 3)

`dx = 8, dy = 3, err0 = dx − dy = 5`

| pixel | 2·err | step | new err |
|-------|-------|------|---------|
| (0,0) | 10 | x | 2 |
| (1,0) | 4 | x+y | 7 |
| (2,1) | 14 | x | 4 |
| (3,1) | 8 | x | 1 |
| (4,1) | 2 | x+y | 6 |
| (5,2) | 12 | x | 3 |
| (6,2) | 6 | x+y | 8 |
| (7,3) | 16 | x | 5 |
| (8,3) | end | | |

Ideal `y = 3x/8`: 0, 0.375, 0.75, 1.125, 1.5, 1.875, 2.25, 2.625, 3 → rounded 0, 0, 1, 1, 1|2, 2, 2, 3, 3. Same pixels.

## Time (MacBook Air M5, Python 3.10, `bench.py`)

| Line (0,0)–(10000,3770), 10001 pixels | time, ms | ns / pixel |
|----|----|----|
| Step-by-step | 0.88 | 88 |
| DDA | 1.18 | 118 |
| Bresenham | 0.96 | 96 |
| Castle-Pitteway | 0.81 | 81 |
| Wu (2 cells per step) | 1.78 | 89 |
| Bresenham circle R = 1000 (5656 pixels) | 1.16 | 205 |

All line algorithms are O(L), L = number of pixels. In Python an integer operation costs the same
as a float one, so Bresenham is not faster here; in C / hardware it is the fastest, because it uses
only integer addition and comparison.
