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

from enso_common import CLEAN, make_readable, save


class AnimationFrames:
    def __init__(self, fig, dpi=110):
        self.fig, self.dpi, self.frames, self.durations = fig, dpi, [], []
        self.boxes = []                                    # content extents, for the clean export's crop

    def _content_box(self):
        """(left, top, right, bottom) pixels of everything drawn, plus a small margin."""
        bb = self.fig.get_tightbbox(self.fig.canvas.get_renderer())
        h = self.fig.get_figheight() * self.dpi
        m = 0.15 * self.dpi
        return (max(bb.x0 * self.dpi - m, 0), max(h - bb.y1 * self.dpi - m, 0),
                min(bb.x1 * self.dpi + m, self.fig.get_figwidth() * self.dpi), min(h - bb.y0 * self.dpi + m, h))

    def grab(self, duration_ms=120):
        if not self.frames:
            make_readable(self.fig)                            # same text style as the still images
        self.fig.set_dpi(self.dpi)
        self.fig.canvas.draw()
        rgba = np.asarray(self.fig.canvas.buffer_rgba())
        self.frames.append(Image.fromarray(rgba[..., :3].copy()))
        self.durations.append(duration_ms)
        if CLEAN and len(self.frames) in (1, 2) or CLEAN and len(self.frames) % 25 == 0:
            self.boxes.append(self._content_box())

    def save(self, out_png, alt=None, quality=80):
        out_png = Path(out_png)
        frames = self.frames
        if CLEAN:                                          # crop every frame to the content of all frames
            self.boxes.append(self._content_box())
            box = [int(round(f(v[i] for v in self.boxes))) for i, f in enumerate((min, min, max, max))]
            box[2] -= (box[2] - box[0]) % 2                # even size, required by H.264 video
            box[3] -= (box[3] - box[1]) % 2
            frames = [f.crop(box) for f in frames]
        save(self.fig, out_png, alt=alt)                                 # final frame, full resolution
        webp = out_png.with_suffix(".webp")
        frames[0].save(webp, save_all=True, append_images=frames[1:], duration=self.durations,
                       loop=0, quality=quality, method=4)
        print(f"Saved {webp} ({len(frames)} frames, {webp.stat().st_size / 1e6:.1f} MB)")
        if CLEAN:
            self.save_video(out_png.with_suffix(".mp4"), frames)

    def save_video(self, path, frames, fps=25):
        """MP4 (H.264) at a constant frame rate: each frame is repeated to match its duration."""
        import imageio_ffmpeg
        w, h = frames[0].size
        writer = imageio_ffmpeg.write_frames(str(path), (w, h), fps=fps, quality=8, macro_block_size=2)
        writer.send(None)
        for f, d in zip(frames, self.durations):
            data = np.asarray(f, dtype=np.uint8).tobytes()
            for _ in range(max(1, round(d / 1000 * fps))):
                writer.send(data)
        writer.close()
        print(f"Saved {path} ({path.stat().st_size / 1e6:.1f} MB)")


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


# ---------------------------------------------------------------------------------------------
# Event calendars: every El Niño is shown from January of its onset year to December of the next
# ---------------------------------------------------------------------------------------------
EVENT_MONTHS = 24


def event_name(year):
    """'2015/2016' style name for the El Niño that began in `year`."""
    return f"{year}/{year + 1}"


def event_months(year, n=EVENT_MONTHS):
    """Month-start dates from January of `year` to December of the following year."""
    import pandas as pd
    return list(pd.date_range(f"{year}-01-01", periods=n, freq="MS"))


def hold_last(stack, n=EVENT_MONTHS):
    """Pad a (time, ...) stack to `n` months by repeating its last month, for an event still in
    progress. Returns (padded stack, number of months with data)."""
    stack = np.asarray(stack)
    have = len(stack)
    if have >= n:
        return stack[:n], n
    return np.concatenate([stack, np.repeat(stack[-1:], n - have, axis=0)]), have


def month_label(year, k, have=None):
    """'March 2016' for month k of the event that began in `year`; once k passes the months with
    data (an event in progress), the latest month is shown with '(latest data)'."""
    import calendar
    if have is not None and k >= have:
        k, tail = have - 1, " (latest data)"
    else:
        tail = ""
    return f"{calendar.month_name[k % 12 + 1]} {year + k // 12}{tail}"
