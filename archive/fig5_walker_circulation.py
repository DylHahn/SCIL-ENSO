"""
Figure 5 — "What changes in the Pacific during El Niño and La Niña"

A hand-drawn-style schematic (no data needed): three panels showing the
equatorial Pacific in La Niña, neutral and El Niño conditions. Each panel shows
  * where the warm water sits and how deep the warm layer (thermocline) is
  * the trade winds at the surface
  * where air rises (storm clouds, rain) and sinks (dry, clear skies)

    python fig5_walker_circulation.py
    python fig5_walker_circulation.py --layout vertical
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle, Circle

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save

X0, X1 = 0.0, 10.0          # west (Asia/Australia) -> east (South America)
OCEAN_BOTTOM = -3.2
AIR_TOP = 5.4

SCENARIOS = {
    "La Niña": dict(
        therm=(-2.6, -0.25),        # thermocline depth at west/east edges (deep -> very shallow)
        warm_extent=4.2,            # how far east the warmest surface water reaches
        cells=[dict(rise=1.6, sink=8.6, strength=1.6)],
        note="Stronger trade winds push warm water west.\nHeavy rain over Indonesia; "
             "drier in Peru.",
        color=COLORS["la_nina"],
    ),
    "Neutral": dict(
        therm=(-2.3, -0.7),
        warm_extent=5.2,
        cells=[dict(rise=2.4, sink=8.6, strength=1.0)],
        note="Normal trade winds blow east → west.\nWarm water and rain stay in the "
             "western Pacific.",
        color=COLORS["text_2"],
    ),
    "El Niño": dict(
        therm=(-1.7, -1.3),
        warm_extent=9.2,
        cells=[dict(rise=5.6, sink=9.1, strength=0.8),
               dict(rise=5.6, sink=1.3, strength=0.8)],
        note="Trade winds weaken or reverse; warm water\nspreads east. Rain moves to the "
             "central Pacific.",
        color=COLORS["el_nino"],
    ),
}


def arrow(ax, p, q, width, color, z=6):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=f"-|>,head_length={0.35 + 0.1 * width},"
                                 f"head_width={0.18 + 0.06 * width}",
                                 lw=1.2 + 1.6 * width, color=color, zorder=z,
                                 shrinkA=0, shrinkB=0, mutation_scale=18))


def cloud(ax, x, y, scale=1.0):
    for dx, dy, r in [(-0.55, 0, 0.42), (0, 0.22, 0.55), (0.55, 0.02, 0.45), (0.2, -0.12, 0.4),
                      (-0.25, -0.12, 0.38)]:
        ax.add_patch(Circle((x + dx * scale, y + dy * scale), r * scale, facecolor="#8f8e89",
                            edgecolor="none", zorder=7))
    for k in range(-2, 3):
        ax.plot([x + 0.28 * k * scale, x + 0.28 * k * scale - 0.12],
                [y - 0.55 * scale, y - 1.25 * scale], color="#5d8fcf", lw=1.6, zorder=6)


def sun(ax, x, y):
    ax.add_patch(Circle((x, y), 0.32, facecolor="#eda100", edgecolor="none", zorder=7))
    for ang in np.linspace(0, 2 * np.pi, 9)[:-1]:
        ax.plot([x + 0.45 * np.cos(ang), x + 0.65 * np.cos(ang)],
                [y + 0.45 * np.sin(ang), y + 0.65 * np.sin(ang)], color="#eda100", lw=1.8, zorder=7)


def draw_panel(ax, name, sc):
    ax.set_xlim(X0 - 0.9, X1 + 0.9)
    ax.set_ylim(OCEAN_BOTTOM - 1.6, AIR_TOP + 1.0)
    ax.set_aspect("equal")
    ax.axis("off")

    # sky
    ax.add_patch(Rectangle((X0, 0), X1 - X0, AIR_TOP, facecolor="#f4f8fc", edgecolor="none", zorder=0))
    # deep cool ocean
    ax.add_patch(Rectangle((X0, OCEAN_BOTTOM), X1 - X0, -OCEAN_BOTTOM, facecolor=COLORS["ocean_cool"],
                           edgecolor="none", zorder=1))
    # warm layer above the thermocline, with the warmest water as far east as warm_extent
    tw, te = sc["therm"]
    xs = np.linspace(X0, X1, 60)
    therm = tw + (te - tw) * (xs - X0) / (X1 - X0)
    ax.add_patch(Polygon(np.c_[np.r_[xs, xs[::-1]], np.r_[therm, np.zeros_like(xs)]],
                         facecolor=COLORS["ocean_warm"], edgecolor="none", zorder=2))
    hot = xs <= sc["warm_extent"]
    ax.add_patch(Polygon(np.c_[np.r_[xs[hot], xs[hot][::-1]],
                               np.r_[np.maximum(therm[hot], -0.55), np.zeros(hot.sum())]],
                         facecolor="#e0603f", edgecolor="none", zorder=3))
    ax.plot(xs, therm, color="#7a3b2a", lw=1.6, ls=(0, (5, 3)), zorder=4)
    ax.text(X0 + 0.2, tw - 0.12, "thermocline", ha="left", va="top", fontsize=9.5,
            color="#7a3b2a", zorder=5)
    ax.text(X0 + 0.15, -0.3, "warm\nwater", ha="left", va="top", fontsize=10, color="#5c1d10",
            fontweight="bold", zorder=5)

    # land on both sides
    ax.add_patch(Rectangle((X0 - 0.9, OCEAN_BOTTOM), 0.9, -OCEAN_BOTTOM + 0.5, facecolor="#cfccc2",
                           edgecolor="none", zorder=5))
    ax.add_patch(Rectangle((X1, OCEAN_BOTTOM), 0.9, -OCEAN_BOTTOM + 0.9, facecolor="#cfccc2",
                           edgecolor="none", zorder=5))
    ax.text(X0 - 0.45, 0.75, "Indonesia /\nAustralia", ha="center", va="bottom", fontsize=9.5,
            color=COLORS["text_2"])
    ax.text(X1 + 0.45, 1.15, "South\nAmerica", ha="center", va="bottom", fontsize=9.5,
            color=COLORS["text_2"])

    # air circulation cells
    aloft, low = 4.0, 0.55
    for cell in sc["cells"]:
        r, s, w = cell["rise"], cell["sink"], cell["strength"]
        col = "#3d3c39"
        arrow(ax, (r, 1.6), (r, aloft - 0.25), w, col)                         # rising
        arrow(ax, (r + np.sign(s - r) * 0.3, aloft), (s - np.sign(s - r) * 0.3, aloft), w, col)  # aloft
        arrow(ax, (s, aloft - 0.25), (s, low + 0.35), w, col)                  # sinking
        arrow(ax, (s - np.sign(s - r) * 0.3, low), (r + np.sign(s - r) * 1.0, low), w,
              "#1c5cab", z=8)                                                    # surface wind
        sun(ax, s, aloft + 0.85) if abs(s - r) > 2 else None
    rise = sc["cells"][0]["rise"]
    cloud(ax, rise, aloft + 0.55, 1.0)

    ax.text(X0 - 0.9, AIR_TOP + 0.95, name, ha="left", va="top", fontsize=17, fontweight="bold",
            color=sc["color"])
    ax.text(X0 - 0.9, OCEAN_BOTTOM - 0.25, sc["note"], ha="left", va="top", fontsize=11,
            color=COLORS["text"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layout", choices=["horizontal", "vertical"], default="horizontal")
    ap.add_argument("--out", default=str(FIG_DIR / "fig5_walker_circulation.png"))
    args = ap.parse_args()

    apply_style()
    if args.layout == "horizontal":
        fig, axes = plt.subplots(1, 3, figsize=(18, 6.0))
        fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.06, wspace=0.06)
    else:
        fig, axes = plt.subplots(3, 1, figsize=(9, 17))
        fig.subplots_adjust(left=0.04, right=0.96, top=0.92, bottom=0.04, hspace=0.25)

    for ax, (name, sc) in zip(axes, SCENARIOS.items()):
        draw_panel(ax, name, sc)

    add_title(fig, "What changes in the Pacific during La Niña and El Niño",
              "Looking along the equator from the side. Arrows show air rising over warm water "
              "(storms) and sinking where it is dry. Blue arrows are the surface trade winds.")
    add_source(fig, "Schematic, not to scale. Concept: NOAA Climate.gov ENSO explainers.")
    save(fig, args.out)


if __name__ == "__main__":
    main()
