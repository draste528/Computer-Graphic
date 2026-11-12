"""Time measurement for the report: python3 bench.py"""
import platform
import timeit

import raster

TESTS = [
    ("line (0,0)-(100,37)", (0, 0, 100, 37)),
    ("line (0,0)-(1000,377)", (0, 0, 1000, 377)),
    ("line (0,0)-(10000,3770)", (0, 0, 10000, 3770)),
]


def best_time(func, args, number=200):
    """Best of 5 series, microseconds per call (best = least disturbed by other processes)."""
    total = min(timeit.repeat(lambda: func(*args, log=False), number=number, repeat=5))
    return total / number * 1e6


if __name__ == "__main__":
    print(platform.platform(), platform.processor(), "Python", platform.python_version())
    for title, args in TESTS:
        print(f"\n{title}")
        for name, func in raster.ALGORITHMS.items():
            if name == "Bresenham circle":
                continue
            n = len(func(*args, log=False)[0])
            t = best_time(func, args, number=max(2, 20000 // n))
            print(f"  {name:28} {t:10.1f} us   {t / n * 1000:7.1f} ns/pixel")
    print()
    for r in (10, 100, 1000):
        n = len(raster.bresenham_circle(0, 0, r, log=False)[0])
        t = best_time(raster.bresenham_circle, (0, 0, r), number=max(2, 20000 // n))
        print(f"circle R = {r:<5} {t:10.1f} us   {t / n * 1000:7.1f} ns/pixel")
