# Lab 1 — Color models (CMYK – RGB – HSV, even variant)

## Run

```bash
python3 main.py
```

Only the standard library is needed (`tkinter`). On macOS with Homebrew Python:
`brew install python-tk@3.14` (match your Python version) if `import tkinter` fails.

## UI

- Top: color squares (white by default). Click a square to select it (black frame).
  `+ square` / `- square` add or remove squares.
- Bottom: editors for the selected square. Every model can be set in three ways:
  1. exact value in the number field (type it or use the arrows),
  2. slider for smooth changes,
  3. `Palette...` button — system color picker.
- `HEX` field: type `#rrggbb` and press Enter.
- Changing any component recalculates the other two models immediately.

## Files

- `converters.py` — conversion formulas (RGB <-> CMYK, RGB <-> HSV).
- `main.py` — the interface.

## Ranges

| Model | Components | Range |
|-------|------------|-------|
| CMYK  | C, M, Y, K | 0–100 % |
| RGB   | R, G, B    | 0–255 |
| HSV   | H / S, V   | 0–360° / 0–100 % |

Internally the color is stored as RGB floats in [0, 1], so no precision is lost
between conversions; the model being edited is not rewritten from rounded values.
