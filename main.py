"""Lab 1 - color models CMYK - RGB - HSV. Run:  python3 main.py"""
import tkinter as tk
from tkinter import colorchooser, ttk

import converters as cv

# model -> (components [(name, max shown value, factor)], from_rgb, to_rgb)
# shown value = internal value * factor  (internal: 0..1, hue: 0..360)
MODELS = {
    "CMYK": ([("C", 100, 100), ("M", 100, 100), ("Y", 100, 100), ("K", 100, 100)],
             cv.rgb_to_cmyk, cv.cmyk_to_rgb),
    "RGB":  ([("R", 255, 255), ("G", 255, 255), ("B", 255, 255)], cv.rgb_to_rgb, cv.rgb_to_rgb),
    "HSV":  ([("H", 360, 1), ("S", 100, 100), ("V", 100, 100)], cv.rgb_to_hsv, cv.hsv_to_rgb),
}

SQUARE = 140   # square size, px
GAP = 30       # gap between squares, px
FRAME = 8      # selection frame offset, px


def to_hex(rgb):
    return "#%02x%02x%02x" % tuple(round(c * 255) for c in rgb)


class App:
    def __init__(self, root):
        self.root = root
        self.colors = [(1.0, 1.0, 1.0), (1.0, 1.0, 1.0)]  # RGB in [0, 1] for every square
        self.selected = 0
        self.boxes = []        # square bounding boxes for click detection
        self.updating = False  # blocks callbacks while we update widgets ourselves
        self.vars = {}         # model -> list of IntVar (one per component)

        # --- top half: squares ---
        self.canvas = tk.Canvas(root, height=280, bg="#d9d9d9", highlightthickness=0)
        self.canvas.pack(fill="x")
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<Button-1>", self.on_click)

        bar = tk.Frame(root)
        bar.pack(pady=8)
        tk.Button(bar, text="+ square", command=self.add_square).pack(side="left")
        tk.Button(bar, text="- square", command=self.remove_square).pack(side="left")
        tk.Label(bar, text="HEX").pack(side="left", padx=(16, 4))
        self.hex_var = tk.StringVar()
        hex_entry = tk.Entry(bar, textvariable=self.hex_var, width=9)
        hex_entry.pack(side="left")
        hex_entry.bind("<Return>", self.on_hex)

        # --- bottom half: editors, one block per model ---
        editors = tk.Frame(root)
        editors.pack(fill="x", padx=16, pady=(0, 16))
        editors.columnconfigure(1, weight=1)
        row = 0
        for model in MODELS:
            tk.Label(editors, text=model, font=("Helvetica", 14, "bold")).grid(
                row=row, column=0, columnspan=2, sticky="w", pady=(10, 0))
            tk.Button(editors, text="Palette...", command=self.pick_from_palette).grid(
                row=row, column=2, pady=(10, 0))
            row += 1
            self.vars[model] = []
            for name, mx, _ in MODELS[model][0]:
                var = tk.IntVar()
                tk.Label(editors, text=name, width=2).grid(row=row, column=0)
                # ttk.Scale = native macOS slider with a round knob; it returns floats -> round
                ttk.Scale(editors, from_=0, to=mx, orient="horizontal", variable=var,
                          command=lambda v, var=var: var.set(round(float(v)))
                          ).grid(row=row, column=1, sticky="we", padx=4)
                tk.Spinbox(editors, from_=0, to=mx, textvariable=var, width=5).grid(row=row, column=2)
                var.trace_add("write", lambda *_, m=model: self.on_change(m))
                self.vars[model].append(var)
                row += 1

        self.show_color()

    # ---------- squares ----------

    def draw(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        n = len(self.colors)
        size = max(10, min(SQUARE, (w - GAP * (n + 1)) / n))
        x = (w - (n * size + (n - 1) * GAP)) / 2
        y = (h - size) / 2
        self.boxes = []
        for i, rgb in enumerate(self.colors):
            box = (x, y, x + size, y + size)
            c.create_rectangle(*box, fill=to_hex(rgb), outline="#888888")
            if i == self.selected:
                c.create_rectangle(x - FRAME, y - FRAME, x + size + FRAME, y + size + FRAME,
                                   outline="black", width=3)
            self.boxes.append(box)
            x += size + GAP

    def on_click(self, event):
        for i, (x1, y1, x2, y2) in enumerate(self.boxes):
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.selected = i
                self.show_color()

    def add_square(self):
        self.colors.append((1.0, 1.0, 1.0))
        self.selected = len(self.colors) - 1
        self.show_color()

    def remove_square(self):
        if len(self.colors) > 1:
            self.colors.pop(self.selected)
            self.selected = min(self.selected, len(self.colors) - 1)
            self.show_color()

    # ---------- editing ----------

    def show_color(self, skip=None):
        """Write the selected color into every model except `skip` (the one being edited)."""
        rgb = self.colors[self.selected]
        self.updating = True
        for model, vars_ in self.vars.items():
            if model == skip:
                continue
            values = MODELS[model][1](*rgb)
            for var, value, (_, _, factor) in zip(vars_, values, MODELS[model][0]):
                var.set(round(value * factor))
        self.hex_var.set(to_hex(rgb))
        self.updating = False
        self.draw()

    def on_change(self, model):
        """Called when any slider / field of `model` changes."""
        if self.updating:
            return
        values = []
        for var, (_, mx, factor) in zip(self.vars[model], MODELS[model][0]):
            try:
                v = var.get()
            except tk.TclError:   # field is empty or not a number while typing
                return
            if not 0 <= v <= mx:  # keep the value inside its range
                v = min(max(v, 0), mx)
                self.updating = True
                var.set(v)
                self.updating = False
            values.append(v / factor)
        self.colors[self.selected] = MODELS[model][2](*values)
        self.show_color(skip=model)

    def pick_from_palette(self):
        rgb, _ = colorchooser.askcolor(to_hex(self.colors[self.selected]), parent=self.root)
        if rgb:
            self.colors[self.selected] = tuple(c / 255 for c in rgb)
            self.show_color()

    def on_hex(self, _event):
        text = self.hex_var.get().strip().lstrip("#")
        try:
            if len(text) != 6:
                raise ValueError
            self.colors[self.selected] = tuple(int(text[i:i + 2], 16) / 255 for i in (0, 2, 4))
        except ValueError:
            pass  # invalid input -> just restore the current value
        self.show_color()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Color models: CMYK - RGB - HSV")
    root.geometry("720x820")
    App(root)
    root.mainloop()
