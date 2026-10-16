"""
Archived: the three-step cartoon of how a Kelvin wave works, which used to head the Kelvin wave
animation (anim_kelvin.py). Run on its own to draw it as a still image:

    PYTHONPATH=. python archive/kelvin_schematic.py
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

from enso_common import FIG_DIR, COLORS, apply_style, save


def schematic(fig, rect):
    """Three cartoon cross-sections of the equatorial Pacific, west (left) to east (right)."""
    steps = [
        ("1  A burst of westerly wind", "Winds reverse for a few days in the western\nPacific and push warm water east."),
        ("2  A pulse travels east", "A bulge of warm water moves east beneath the\nsurface at 2.5–3 m/s (roughly 250 km a day)."),
        ("3  It reaches South America", "One to two months later it deepens the warm\nlayer in the east and warms the surface."),
    ]
    x, y, w, h = rect
    warm, cold, land = "#e8574a", "#1c5cab", "#3a3936"
    for k, (title, text) in enumerate(steps):
        ax = fig.add_axes([x + k * w / 3 + 0.008, y, w / 3 - 0.016, h])
        ax.set_xlim(0, 10); ax.set_ylim(-4.0, 4.6); ax.axis("off")
        bump = [2.0, 5.2, 8.2][k]
        xs = np.linspace(0.4, 9.6, 200)
        z = -1.6 + 0.11 * (xs - 0.4) - 0.9 * np.exp(-((xs - bump) / 0.9) ** 2)   # base of the warm layer
        ax.add_patch(Rectangle((0.4, -3.2), 9.2, 3.2, color=cold, zorder=1))
        ax.add_patch(Polygon(np.column_stack([np.r_[xs, xs[::-1]], np.r_[z, np.zeros_like(xs)]]), color=warm,
                             zorder=2))
        ax.plot(xs, z, color="white", lw=1, ls=(0, (3, 2)), zorder=3)
        ax.add_patch(Rectangle((0, -3.2), 0.4, 3.6, color=land, zorder=4))
        ax.add_patch(Polygon([[9.6, -3.2], [9.6, 0.6], [9.8, 1.4], [10, 1.0], [10, -3.2]], color=land, zorder=4))
        if k == 0:
            ax.add_patch(FancyArrowPatch((0.9, 1.0), (4.4, 1.0), arrowstyle="-|>", mutation_scale=14, lw=2.2,
                                         color=COLORS["text"]))
            ax.text(2.65, 1.25, "westerly winds", ha="center", fontsize=9, color=COLORS["text"])
        else:
            ax.add_patch(FancyArrowPatch((bump - 1.7, -1.1), (bump + 0.9, -1.1), arrowstyle="-|>",
                                         mutation_scale=12, lw=1.8, color="white", zorder=5))
            ax.plot(xs, 0.25 * np.exp(-((xs - bump) / 0.9) ** 2), color="#9ec5f4", lw=1.6, zorder=5)
            ax.text(bump - 0.3, 0.45, "sea level rises", ha="center" if k == 1 else "right", fontsize=8.5,
                    color="#9ec5f4")
        if k == 2:
            ax.add_patch(Rectangle((7.2, -0.2), 2.4, 0.2, color="#ffb000", zorder=6))
            ax.text(7.0, -0.55, "surface warms", ha="right", fontsize=8.5, color="#ffd27a", zorder=6)
        ax.text(0.0, 4.5, title, fontsize=12, fontweight="bold", color=COLORS["text"], va="top")
        ax.text(0.0, 3.55, text, fontsize=9.5, color=COLORS["text_2"], va="top", linespacing=1.3)
        ax.text(0.5, -3.65, "West (Asia)", fontsize=8, color=COLORS["muted"])
        ax.text(9.5, -3.65, "East (S. America)", fontsize=8, color=COLORS["muted"], ha="right")


if __name__ == "__main__":
    apply_style("dark")
    fig = plt.figure(figsize=(13, 3.2))
    schematic(fig, (0.03, 0.02, 0.94, 0.95))
    save(fig, FIG_DIR / "archive" / "kelvin_schematic.png", alt="Three-step cartoon of a Kelvin wave.")
