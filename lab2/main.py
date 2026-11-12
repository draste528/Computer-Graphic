"""Lab 2 (variant 6): point operations + linear contrast stretching, global thresholding.

Run:  python3 main.py
"""
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

import numpy as np
from PIL import Image, ImageTk

import processing as p

IMAGES_DIR = Path(__file__).parent / "images"
VIEW_W, VIEW_H = 480, 360   # max size of a shown image, px
HIST_H = 110                # histogram height, px
OTSU_COLOR, ITER_COLOR = "#d62728", "#1f77b4"


# ---------------- operations ----------------
# Each operation: f(img, value) -> (result image, info text, [(threshold, color), ...])

def op_stretch(img, clip):
    res, low, high = p.linear_stretch(img, clip)
    return res, f"[{low:.0f}, {high:.0f}] -> [0, 255]", []


def op_manual(img, t):
    return p.threshold(p.to_gray(img), t), f"T = {t:.0f}", [(t, "black")]


def op_iterative(img, _):
    t, n = p.iterative_threshold(p.to_gray(img))
    return p.threshold(p.to_gray(img), t), f"Iterative: T = {t:.1f} ({n} iterations)", [(t, ITER_COLOR)]


def op_otsu(img, _):
    t, eta = p.otsu_threshold(p.to_gray(img))
    return p.threshold(p.to_gray(img), t), f"Otsu: T = {t:.1f} (separability = {eta:.2f})", [(t, OTSU_COLOR)]


def op_compare(img, _):
    """Otsu (left) and iterative (right) results side by side."""
    gray = p.to_gray(img)
    t_otsu, eta = p.otsu_threshold(gray)
    t_iter, n = p.iterative_threshold(gray)
    gap = np.full((gray.shape[0], 10), 128, np.uint8)
    res = np.hstack([p.threshold(gray, t_otsu), gap, p.threshold(gray, t_iter)])
    info = (f"Left - Otsu: T = {t_otsu:.1f} (separability = {eta:.2f})   |   "
            f"Right - Iterative: T = {t_iter:.1f} ({n} iterations)")
    return res, info, [(t_otsu, OTSU_COLOR), (t_iter, ITER_COLOR)]


# name -> (parameter (label, min, max, default, step) or None, function)
OPERATIONS = {
    "Negative:  g = 255 - f": (None, lambda img, v: (p.negative(img), "", [])),
    "Brightness:  g = f + c": (("c", -128, 128, 50, 1), lambda img, v: (p.brightness(img, v), "", [])),
    "Contrast:  g = 128 + k(f - 128)": (("k", 0.1, 3, 1.5, 0.1), lambda img, v: (p.contrast(img, v), "", [])),
    "Gamma:  g = 255 (f/255)^γ": (("γ", 0.1, 5, 0.5, 0.05), lambda img, v: (p.gamma(img, v), "", [])),
    "Logarithm:  g = c log(1 + f)": (None, lambda img, v: (p.log_transform(img), "", [])),
    "Linear contrast stretching": (("clip %", 0, 5, 0, 0.1), op_stretch),
    "Threshold: manual": (("T", 0, 255, 128, 1), op_manual),
    "Threshold: iterative": (None, op_iterative),
    "Threshold: Otsu": (None, op_otsu),
    "Threshold: compare Otsu vs iterative": (None, op_compare),
}


class App:
    def __init__(self, root):
        self.root = root
        self.original = None   # numpy image
        self.result = None

        # --- toolbar ---
        bar = tk.Frame(root)
        bar.pack(fill="x", padx=10, pady=8)
        tk.Label(bar, text="Test image:").pack(side="left")
        self.image_box = ttk.Combobox(bar, state="readonly", width=26,
                                      values=sorted(f.name for f in IMAGES_DIR.glob("*.png")))
        self.image_box.pack(side="left")
        self.image_box.bind("<<ComboboxSelected>>",
                            lambda e: self.load(IMAGES_DIR / self.image_box.get()))
        tk.Button(bar, text="Open...", command=self.open_file).pack(side="left", padx=4)
        tk.Button(bar, text="Save result...", command=self.save_file).pack(side="left")

        ops = tk.Frame(root)
        ops.pack(fill="x", padx=10)
        tk.Label(ops, text="Operation:").pack(side="left")
        self.op_box = ttk.Combobox(ops, state="readonly", width=36, values=list(OPERATIONS))
        self.op_box.current(0)
        self.op_box.pack(side="left")
        self.op_box.bind("<<ComboboxSelected>>", lambda e: self.on_operation())
        self.param_label = tk.Label(ops, width=12, anchor="e")
        self.param_label.pack(side="left")
        self.param = tk.DoubleVar()
        self.slider = ttk.Scale(ops, variable=self.param, length=260,
                                command=lambda v: self.apply())
        self.slider.pack(side="left", padx=4)

        self.info = tk.Label(root, anchor="w", font=("Helvetica", 13))
        self.info.pack(fill="x", padx=10, pady=4)

        # --- two panels: original and result, each = image + histogram ---
        panels = tk.Frame(root)
        panels.pack(padx=10, pady=(0, 10))
        self.views, self.hists = [], []
        for col, title in enumerate(["Original", "Result"]):
            tk.Label(panels, text=title, font=("Helvetica", 14, "bold")).grid(row=0, column=col)
            view = tk.Label(panels, bg="#cccccc")
            view.grid(row=1, column=col, padx=5)
            hist = tk.Canvas(panels, width=VIEW_W, height=HIST_H, bg="white", highlightthickness=0)
            hist.grid(row=2, column=col, padx=5, pady=5)
            self.views.append(view)
            self.hists.append(hist)

        if self.image_box["values"]:
            self.image_box.current(0)
            self.load(IMAGES_DIR / self.image_box.get())
        self.on_operation()

    # ---------- files ----------

    def load(self, path):
        img = Image.open(path)
        img = img.convert("L" if img.mode in ("1", "L", "LA", "I", "I;16") else "RGB")
        self.original = np.array(img)
        self.show(0, self.original, [])
        self.apply()

    def open_file(self):
        path = filedialog.askopenfilename(initialdir=IMAGES_DIR, filetypes=[
            ("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("All files", "*")])
        if path:
            self.image_box.set("")
            self.load(path)

    def save_file(self):
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png")])
        if path:
            Image.fromarray(self.result).save(path)

    # ---------- processing ----------

    def on_operation(self):
        """Show / hide the slider for the chosen operation and set its default."""
        param, _ = OPERATIONS[self.op_box.get()]
        if param:
            label, lo, hi, default, _ = param
            self.param_label.config(text=label)
            self.slider.config(from_=lo, to=hi)
            self.param.set(default)
            self.slider.state(["!disabled"])
        else:
            self.param_label.config(text="")
            self.slider.state(["disabled"])
        self.apply()

    def apply(self):
        if self.original is None:
            return
        param, func = OPERATIONS[self.op_box.get()]
        value = None
        if param:
            step = param[4]
            value = round(self.param.get() / step) * step   # snap slider to its step
            self.param_label.config(text=f"{param[0]} = {value:g}")
        self.result, text, thresholds = func(self.original, value)
        self.info.config(text=text)
        self.show(0, self.original, thresholds)   # threshold lines go on the source histogram
        self.show(1, self.result, [])

    # ---------- drawing ----------

    def show(self, i, img, thresholds):
        """Show image `img` in panel i with its histogram and threshold lines."""
        pil = Image.fromarray(img)
        pil.thumbnail((VIEW_W, VIEW_H))
        photo = ImageTk.PhotoImage(pil)
        self.views[i].config(image=photo, width=VIEW_W, height=VIEW_H)
        self.views[i].image = photo   # keep a reference, otherwise Tk shows nothing

        c = self.hists[i]
        c.delete("all")
        hist = p.histogram(p.to_gray(img))
        top = max(hist.max(), 1)
        bar_w = VIEW_W / 256
        for level, count in enumerate(hist):
            x = level * bar_w
            c.create_rectangle(x, HIST_H, x + bar_w, HIST_H - count / top * (HIST_H - 5),
                               fill="gray30", outline="")
        for k, (t, color) in enumerate(thresholds):
            x = (t + 0.5) * bar_w
            c.create_line(x, 0, x, HIST_H, fill=color, width=2)
            c.create_text(x + 3, 3 + 15 * k, text=f"T={t:.0f}", fill=color, anchor="nw")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Lab 2: point operations, contrast stretching, global thresholding")
    App(root)
    root.mainloop()
