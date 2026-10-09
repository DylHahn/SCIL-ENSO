"""
Animation helpers: render matplotlib frames to an animated WebP (small, plays in every
modern browser as an ordinary <img>) plus a still PNG of the final frame, which is
used as the poster image, for the alt-text workflow and for print.

    frames = AnimationFrames(fig)
    for ...: update the figure; frames.grab()
    frames.save(out_png, alt="...")          # writes out_png and out_png.with_suffix(".webp")
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from enso_common import save


class AnimationFrames:
    def __init__(self, fig, dpi=110):
        self.fig, self.dpi, self.frames, self.durations = fig, dpi, [], []

    def grab(self, duration_ms=120):
        self.fig.set_dpi(self.dpi)
        self.fig.canvas.draw()
        rgba = np.asarray(self.fig.canvas.buffer_rgba())
        self.frames.append(Image.fromarray(rgba[..., :3].copy()))
        self.durations.append(duration_ms)

    def save(self, out_png, alt=None, quality=80):
        out_png = Path(out_png)
        save(self.fig, out_png, alt=alt)                                 # final frame, full resolution
        webp = out_png.with_suffix(".webp")
        self.frames[0].save(webp, save_all=True, append_images=self.frames[1:], duration=self.durations,
                            loop=0, quality=quality, method=4)
        print(f"Saved {webp} ({len(self.frames)} frames, {webp.stat().st_size / 1e6:.1f} MB)")


def interpolate_months(stack, steps):
    """Linear interpolation between consecutive monthly fields (first axis = time).
    Returns (frames, month_index_float) with `steps` frames per month interval."""
    out, pos = [], []
    for k in range(len(stack) - 1):
        for j in range(steps):
            f = j / steps
            out.append((1 - f) * stack[k] + f * stack[k + 1])
            pos.append(k + f)
    out.append(stack[-1])
    pos.append(len(stack) - 1)
    return out, pos
