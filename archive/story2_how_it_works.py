"""
Story 2 — "How El Niño feeds itself"

The physics in four plain-language steps arranged as a loop (the Bjerknes
feedback), with a strip of live numbers underneath showing how hard the loop is
running right now (NOAA CPC monthly Niño indices).

    python story2_how_it_works.py
    python story2_how_it_works.py --theme light
"""
import argparse
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style, fetch_text, load_roni, save,
                         season_words)

STEPS = [
    ("The trade winds ease",
     "Normally, steady winds blow from east to west along the equator and pile warm water up "
     "near Asia and Australia, like wind pushing bathwater to one end of the tub."),
    ("Warm water sloshes back east",
     "When those winds weaken, the piled-up warm water flows back east. Much of it travels "
     "underwater as a slow wave that takes a couple of months to cross the Pacific."),
    ("The eastern Pacific heats up",
     "Normally, cold water rises from the deep near South America and keeps the sea cool. "
     "Now the warm layer on top is so thick that cold water can't reach the surface, so the sea "
     "there warms far above normal."),
    ("Storms follow the warm water",
     "Warm ocean heats the air above it, so storms and heavy rain move toward the central "
     "and eastern Pacific. That shifts air pressure and weakens the trade winds even more."),
]


def latest_sstoi(refresh=False):
    """(month label, Niño 3.4 anomaly, Niño 1+2 anomaly) from CPC's monthly sstoi.indices."""
    rows = [l.split() for l in fetch_text("sstoi", refresh=refresh).splitlines()]
    rows = [r for r in rows if len(r) >= 10 and r[0].isdigit()]
    yr, mon = int(rows[-1][0]), int(rows[-1][1])
    import calendar
    return f"{calendar.month_name[mon]} {yr}", float(rows[-1][9]), float(rows[-1][3])


def card(ax, x, y, w, h, n, title, body):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.025",
                                facecolor=COLORS["surface_2"], edgecolor="none", zorder=2))
    ax.add_patch(Circle((x + 0.04, y + h - 0.045), 0.022, facecolor=COLORS["el_nino"], zorder=3))
    ax.text(x + 0.04, y + h - 0.046, str(n), ha="center", va="center", fontsize=15,
            fontweight="bold", color="white", zorder=4)
    ax.text(x + 0.075, y + h - 0.046, title, ha="left", va="center", fontsize=16,
            fontweight="bold", color=COLORS["text"], zorder=4)
    ax.text(x + 0.025, y + h - 0.085, textwrap.fill(body, 42), ha="left", va="top", fontsize=12.5,
            color=COLORS["text_2"], linespacing=1.45, zorder=4)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "story" / "story2_how_it_works.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    fig = plt.figure(figsize=(13, 9.6))
    # one axes; x runs 0-1 and y is scaled to match, so circles stay round
    rect = [0.03, 0.06, 0.94, 0.80]
    ax = fig.add_axes(rect)
    ymax = rect[3] * 9.6 / (rect[2] * 13)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, ymax)
    ax.axis("off")

    w, h = 0.36, 0.205
    xl, xr = 0.02, 0.62
    yt, yb = ymax - h - 0.005, 0.165
    pos = [(xl, yt), (xr, yt), (xr, yb), (xl, yb)]
    for i, ((x, y), (title, body)) in enumerate(zip(pos, STEPS), 1):
        card(ax, x, y, w, h, i, title, body)

    # clockwise arrows between the cards
    arrow_kw = dict(arrowstyle="-|>,head_length=0.7,head_width=0.4", color=COLORS["el_nino"],
                    lw=3, mutation_scale=18, zorder=5)
    ax.add_patch(FancyArrowPatch((xl + w + 0.01, yt + h / 2), (xr - 0.01, yt + h / 2), **arrow_kw))
    ax.add_patch(FancyArrowPatch((xr + w / 2, yt - 0.01), (xr + w / 2, yb + h + 0.01), **arrow_kw))
    ax.add_patch(FancyArrowPatch((xr - 0.01, yb + h / 2), (xl + w + 0.01, yb + h / 2), **arrow_kw))
    ax.add_patch(FancyArrowPatch((xl + w / 2, yb + h + 0.01), (xl + w / 2, yt - 0.01), **arrow_kw))

    # the middle of the loop
    cy = (yt + yb + h) / 2
    ax.text(0.5, cy + 0.02, "A loop that\nfeeds itself", ha="center", va="bottom", fontsize=17,
            fontweight="bold", color=COLORS["text"], linespacing=1.2)
    ax.text(0.5, cy + 0.0, "Each step makes the next one\nstronger. It winds down once the\n"
            "stored warm water is used up,\nusually by the following spring.",
            ha="center", va="top", fontsize=11.5, color=COLORS["text_2"], linespacing=1.4)

    # "right now" strip with live numbers
    month, n34, n12 = latest_sstoi(args.refresh)
    roni = load_roni(refresh=args.refresh)
    roni_season = roni.attrs["season"][roni.index[-1]]
    sy = 0.0
    ax.text(0.02, sy + 0.115, f"What makes it “super”: the loop is running unusually hard. Right now ({month}):",
            fontsize=13, fontweight="bold", color=COLORS["text"], va="bottom")
    tiles = [(f"{n34:+.1f} °C", "Central Pacific sea surface\n(Niño 3.4 region) vs. normal"),
             (f"{n12:+.1f} °C", "Ocean off Peru & Ecuador\n(Niño 1+2 region) vs. normal"),
             (f"{roni.iloc[-1]:+.1f} °C", f"NOAA's official index:\n{season_words(roni_season)} average, vs.\n"
                                          "the rest of the tropics")]
    for k, (big, small) in enumerate(tiles):
        x = 0.02 + k * 0.33
        ax.add_patch(FancyBboxPatch((x, sy), 0.31, 0.10, boxstyle="round,pad=0,rounding_size=0.02",
                                    facecolor=COLORS["surface_2"], edgecolor="none"))
        col = COLORS["el_nino"]
        ax.text(x + 0.02, sy + 0.05, big, ha="left", va="center", fontsize=24, fontweight="bold", color=col)
        ax.text(x + 0.135, sy + 0.05, small, ha="left", va="center", fontsize=11, color=COLORS["text_2"],
                linespacing=1.35)

    add_title(fig, "How El Niño feeds itself",
              "Wind and ocean push on each other along the equator. Once the loop gets going, "
              "it can grow for months.")
    add_source(fig, f"Live values: NOAA Climate Prediction Center monthly Niño indices ({month}; "
               "anomalies vs. 1991–2020). Explanation after NOAA Climate.gov.")
    save(fig, args.out,
         alt="Diagram of four steps in a loop: 1. the trade winds ease; 2. warm water sloshes back east; "
             "3. the eastern Pacific heats up; 4. storms follow the warm water, which weakens the winds "
             f"further. Below: in {month} the central Pacific was {n34:+.1f} °C and the ocean off Peru and "
             f"Ecuador {n12:+.1f} °C compared with normal.")


if __name__ == "__main__":
    main()
