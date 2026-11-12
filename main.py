"""Lab 3: basic raster algorithms. Run:  python3 main.py

Pixel (x, y) with integer coordinates = a grid cell whose CENTER is the point (x, y).
Grid lines lie at half-integers (x +- 0.5), axes pass through the centers of cells x = 0 / y = 0.
"""
import math
import time
import tkinter as tk
from tkinter import ttk

import raster

COLORS = {
    "Step-by-step": (230, 126, 34),
    "DDA": (39, 174, 96),
    "Bresenham line": (41, 98, 255),
    "Bresenham circle": (142, 68, 173),
    "Castle-Pitteway (bonus)": (192, 57, 43),
    "Wu antialiased line (bonus)": (20, 20, 20),
}


def hex_color(rgb, intensity=1.0):
    """Blend the color with white: intensity 1 = full color, 0 = white."""
    return "#%02x%02x%02x" % tuple(round(255 - intensity * (255 - c)) for c in rgb)


def measure(func, args):
    """Average time of one call (without the text log), in microseconds."""
    runs, start = 0, time.perf_counter()
    while time.perf_counter() - start < 0.1:   # repeat for ~0.1 s for a stable average
        func(*args, log=False)
        runs += 1
    return (time.perf_counter() - start) / runs * 1e6


class App:
    def __init__(self, root):
        self.root = root
        self.shapes = []          # drawn shapes: (algorithm name, args, pixels)
        self.cell = 24            # cell size in screen pixels = zoom
        self.offset = [0, 0]      # pan offset in screen pixels
        self.drag_from = None

        # ---------- left panel ----------
        panel = tk.Frame(root, padx=10, pady=10)
        panel.pack(side="left", fill="y")

        tk.Label(panel, text="Algorithm").pack(anchor="w")
        self.algo = ttk.Combobox(panel, state="readonly", width=26, values=list(raster.ALGORITHMS))
        self.algo.current(2)
        self.algo.pack(anchor="w")
        self.algo.bind("<<ComboboxSelected>>", lambda e: self.update_fields())

        fields = tk.Frame(panel, pady=8)
        fields.pack(anchor="w")
        self.vars, self.entries = {}, {}
        for i, (name, default) in enumerate([("x0", -8), ("y0", -3), ("x1", 10), ("y1", 5), ("R", 8)]):
            tk.Label(fields, text=name, width=3).grid(row=i, column=0)
            var = tk.IntVar(value=default)
            entry = tk.Spinbox(fields, from_=-1000, to=1000, textvariable=var, width=7)
            entry.grid(row=i, column=1, pady=1)
            self.vars[name], self.entries[name] = var, entry
        self.hint = tk.Label(panel, fg="gray40", justify="left")
        self.hint.pack(anchor="w")

        buttons = tk.Frame(panel, pady=6)
        buttons.pack(anchor="w")
        tk.Button(buttons, text="Draw", command=self.draw_shape).pack(side="left")
        tk.Button(buttons, text="Clear", command=self.clear).pack(side="left")
        tk.Button(buttons, text="Benchmark", command=self.benchmark).pack(side="left")

        self.show_ideal = tk.BooleanVar(value=True)
        tk.Checkbutton(panel, text="Show ideal line / circle", variable=self.show_ideal,
                       command=self.redraw).pack(anchor="w")

        tk.Label(panel, text="Scale (cell size, px)").pack(anchor="w", pady=(8, 0))
        self.scale = ttk.Scale(panel, from_=3, to=60, length=220)
        self.scale.set(self.cell)
        self.scale.config(command=lambda v: self.set_cell(float(v)))
        self.scale.pack(anchor="w")
        tk.Label(panel, text="Mouse wheel: zoom.  Drag: move.", fg="gray40").pack(anchor="w")

        tk.Label(panel, text="Calculations", font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(10, 0))
        self.log = tk.Text(panel, width=46, height=24, font="TkFixedFont", wrap="none")
        self.log.pack(fill="y", expand=True)

        # ---------- canvas ----------
        self.canvas = tk.Canvas(root, bg="white", width=800, height=650, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<MouseWheel>", self.wheel)                    # macOS / Windows
        self.canvas.bind("<Button-4>", lambda e: self.zoom(1.1))       # Linux
        self.canvas.bind("<Button-5>", lambda e: self.zoom(1 / 1.1))

        self.update_fields()
        self.draw_shape()

    # ---------- coordinates ----------

    def to_screen(self, x, y):
        """Grid point (x, y) -> canvas pixel. Y axis goes up, origin at the canvas center."""
        cx = self.canvas.winfo_width() / 2 + self.offset[0]
        cy = self.canvas.winfo_height() / 2 + self.offset[1]
        return cx + x * self.cell, cy - y * self.cell

    def to_grid(self, sx, sy):
        cx = self.canvas.winfo_width() / 2 + self.offset[0]
        cy = self.canvas.winfo_height() / 2 + self.offset[1]
        return (sx - cx) / self.cell, (cy - sy) / self.cell

    # ---------- controls ----------

    def update_fields(self):
        circle = self.algo.get() == "Bresenham circle"
        for name in ("x1", "y1"):
            self.entries[name].config(state="disabled" if circle else "normal")
        self.entries["R"].config(state="normal" if circle else "disabled")
        self.hint.config(text="circle: center (x0, y0), radius R" if circle
                         else "segment from (x0, y0) to (x1, y1)")

    def args(self):
        v = {k: var.get() for k, var in self.vars.items()}
        if self.algo.get() == "Bresenham circle":
            return v["x0"], v["y0"], abs(v["R"])
        return v["x0"], v["y0"], v["x1"], v["y1"]

    def draw_shape(self):
        try:
            args = self.args()
        except tk.TclError:
            return
        name = self.algo.get()
        func = raster.ALGORITHMS[name]
        pixels, lines = func(*args)
        t = measure(func, args)
        self.shapes.append((name, args, pixels))

        self.log.delete("1.0", "end")
        self.log.insert("end", f"{name} {args}\n")
        self.log.insert("end", f"time: {t:.2f} us per call, {len(pixels)} pixels "
                               f"({t / len(pixels):.3f} us per pixel)\n\n")
        self.log.insert("end", "\n".join(lines))
        self.redraw()

    def clear(self):
        self.shapes.clear()
        self.log.delete("1.0", "end")
        self.redraw()

    def benchmark(self):
        """Time every algorithm on the same long line / big circle."""
        tests = [("line (0,0)-(1000,377)", (0, 0, 1000, 377)),
                 ("line (0,0)-(100,37)", (0, 0, 100, 37))]
        self.log.delete("1.0", "end")
        self.log.insert("end", "Average time of one call, us (us per pixel)\n\n")
        for title, args in tests:
            self.log.insert("end", title + "\n")
            for name, func in raster.ALGORITHMS.items():
                if name == "Bresenham circle":
                    continue
                t = measure(func, args)
                n = len(func(*args, log=False)[0])
                self.log.insert("end", f"  {name:28} {t:9.1f} ({t / n:.3f})\n")
            self.log.insert("end", "\n")
        for r in (100, 500):
            t = measure(raster.bresenham_circle, (0, 0, r))
            n = len(raster.bresenham_circle(0, 0, r, log=False)[0])
            self.log.insert("end", f"circle R = {r}: {t:9.1f} us ({t / n:.3f} per pixel)\n")

    def set_cell(self, size):
        self.cell = max(3.0, min(60.0, size))
        self.redraw()

    def zoom(self, factor):
        self.scale.set(self.cell * factor)    # scale callback redraws

    def wheel(self, event):
        self.zoom(1.1 if event.delta > 0 else 1 / 1.1)

    def start_drag(self, event):
        self.drag_from = (event.x, event.y)

    def drag(self, event):
        self.offset[0] += event.x - self.drag_from[0]
        self.offset[1] += event.y - self.drag_from[1]
        self.drag_from = (event.x, event.y)
        self.redraw()

    # ---------- drawing ----------

    def redraw(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        (gx0, gy1), (gx1, gy0) = self.to_grid(0, 0), self.to_grid(w, h)
        xs = range(math.floor(gx0) - 1, math.ceil(gx1) + 2)
        ys = range(math.floor(gy0) - 1, math.ceil(gy1) + 2)

        # pixels (cells)
        half = self.cell / 2
        for name, args, pixels in self.shapes:
            for p in pixels:
                x, y = p[0], p[1]
                intensity = p[2] if len(p) == 3 else 1.0
                sx, sy = self.to_screen(x, y)
                c.create_rectangle(sx - half, sy - half, sx + half, sy + half,
                                   fill=hex_color(COLORS[name], intensity), outline="")

        # grid lines between cells (at half-integers)
        if self.cell >= 6:
            for x in xs:
                sx = self.to_screen(x - 0.5, 0)[0]
                c.create_line(sx, 0, sx, h, fill="#dddddd")
            for y in ys:
                sy = self.to_screen(0, y - 0.5)[1]
                c.create_line(0, sy, w, sy, fill="#dddddd")

        # axes through the centers of cells x = 0 and y = 0
        ox, oy = self.to_screen(0, 0)
        c.create_line(0, oy, w, oy, fill="black", width=2, arrow="last")
        c.create_line(ox, h, ox, 0, fill="black", width=2, arrow="last")
        c.create_text(w - 12, oy - 12, text="X", font=("Helvetica", 12, "bold"))
        c.create_text(ox + 12, 12, text="Y", font=("Helvetica", 12, "bold"))

        # labels: every n-th cell, so that labels are at least ~30 px apart
        n = next(s for s in (1, 2, 5, 10, 20, 50, 100, 200, 500) if s * self.cell >= 30)
        for x in xs:
            if x % n == 0 and x != 0:
                sx = self.to_screen(x, 0)[0]
                c.create_line(sx, oy - 4, sx, oy + 4)
                c.create_text(sx, oy + 14, text=str(x), font=("Helvetica", 10))
        for y in ys:
            if y % n == 0 and y != 0:
                sy = self.to_screen(0, y)[1]
                c.create_line(ox - 4, sy, ox + 4, sy)
                c.create_text(ox - 8, sy, text=str(y), anchor="e", font=("Helvetica", 10))
        c.create_text(ox - 8, oy + 14, text="0", anchor="e", font=("Helvetica", 10))

        # ideal (mathematical) shapes through the cell centers
        if self.show_ideal.get():
            for name, args, _ in self.shapes:
                if name == "Bresenham circle":
                    xc, yc, r = args
                    (x0, y0), (x1, y1) = self.to_screen(xc - r, yc + r), self.to_screen(xc + r, yc - r)
                    c.create_oval(x0, y0, x1, y1, outline="red")
                else:
                    c.create_line(*self.to_screen(*args[:2]), *self.to_screen(*args[2:]), fill="red")

        # legend
        used = list(dict.fromkeys(name for name, _, _ in self.shapes))
        for i, name in enumerate(used):
            c.create_rectangle(10, 10 + i * 20, 24, 24 + i * 20, fill=hex_color(COLORS[name]), outline="")
            c.create_text(30, 17 + i * 20, text=name, anchor="w", font=("Helvetica", 11))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Lab 3: basic raster algorithms")
    App(root)
    root.mainloop()
