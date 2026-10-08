"""
SoCal 1 — "Do El Niño winters bring rain to Southern California?"

Top: every Los Angeles rainy season (Oct–Sep) since 1951 as a percent of normal,
coloured by that winter's El Niño / La Niña strength (NOAA RONI, Dec–Feb).
Bottom: the same for four SoCal stations, grouped by category, with how often
each kind of winter was wetter than normal.

    python socal1_rain.py
    python socal1_rain.py --refresh       # re-download the station records
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save
from enso_socal import (CATEGORIES, RAIN_NOTES, RAIN_STATIONS, categorize, category_colors, load_station, season_so_far,
                        water_year_totals, winter_roni)

START = 1951
NORMAL = (1991, 2020)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, default=2027, help="season (water year end) to mark as 'this winter'")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "socal1_rain.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    cols = category_colors()
    djf = winter_roni(args.refresh)

    data = {}
    for name, sid in RAIN_STATIONS.items():
        daily = load_station(sid, args.refresh)
        tot = water_year_totals(daily)
        tot = tot[(tot.index >= START) & (tot.index < args.season)]
        pct = 100 * tot / tot.loc[NORMAL[0]:NORMAL[1]].mean()
        cats = pd.Series({y: categorize(djf.get(y, np.nan)) for y in pct.index})
        data[name] = (pct, cats, daily)

    fig = plt.figure(figsize=(13, 10.6))
    top = fig.add_axes([0.07, 0.50, 0.90, 0.32])
    pct, cats, daily = data["Los Angeles"]
    top.bar(pct.index, pct.values, width=0.78, color=[cols.get(c, COLORS["neutral"]) for c in cats], lw=0)
    top.axhline(100, color=COLORS["text_2"], lw=1, ls=(0, (4, 3)))
    top.text(START - 0.6, 103, "normal", fontsize=10.5, color=COLORS["text_2"], va="bottom")
    for y in pct.index[cats.values == "Strong El Niño"]:
        top.annotate(f"{y - 1}–{str(y)[-2:]}", (y, pct[y]), xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=10, color=COLORS["text"])
    # this winter hasn't happened yet: a label, not a bar
    top.text(args.season, 8, f"{args.season - 1}–{str(args.season)[-2:]}\n?", ha="center", va="bottom",
             fontsize=10.5, fontweight="bold", color=COLORS["el_nino"])
    top.set_xlim(START - 1, args.season + 2)
    top.set_ylabel("Rain vs. normal (%)")
    top.yaxis.grid(True)
    top.set_axisbelow(True)
    top.set_title(f"Los Angeles (Downtown/USC): water-year precipitation, {START}–{args.season - 1}",
                  fontsize=14, loc="left")
    fig.legend(handles=[Patch(color=cols[c], label=c.replace("\n", " ")) for c, _, _ in CATEGORIES],
               loc="lower left", bbox_to_anchor=(0.065, 0.855), ncol=4, fontsize=11.5,
               labelcolor=COLORS["text_2"], title="ENSO phase (Dec–Feb RONI):",
               title_fontsize=11.5, alignment="left")

    # four stations: one dot per season, grouped by category
    rng = np.random.default_rng(1)
    short = {"La Niña": "La Niña", "Neutral": "Neutral", "Weak–moderate\nEl Niño": "Weak–mod.\nEl Niño",
             "Strong El Niño": "Strong\nEl Niño"}
    summary = []
    for k, (name, (pct, cats, _)) in enumerate(data.items()):
        ax = fig.add_axes([0.07 + k * 0.232, 0.135, 0.20, 0.25])
        for j, (c, _, _) in enumerate(CATEGORIES):
            v = pct[cats == c].values
            if not len(v):
                continue
            x = j + rng.uniform(-0.18, 0.18, len(v))
            ax.scatter(x, v, s=22, color=cols[c], edgecolor=COLORS["surface"], linewidth=0.6, zorder=3)
            ax.plot([j - 0.28, j + 0.28], [np.median(v)] * 2, color=COLORS["text"], lw=2, zorder=4)
            wet = int((v > 100).sum())
            strong = c == "Strong El Niño"
            ax.text(j, -0.04, f"{short[c]}\n{wet}/{len(v)} above", transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=9.5, linespacing=1.2,
                    color=COLORS["text"] if strong else COLORS["text_2"], fontweight="bold" if strong else "normal")
            if c == "Strong El Niño":
                summary.append((name, wet, len(v), float(np.median(v))))
        ax.axhline(100, color=COLORS["text_2"], lw=1, ls=(0, (4, 3)), zorder=1)
        ax.set_xticks([])
        ax.set_xlim(-0.6, len(CATEGORIES) - 0.4)
        ax.set_ylim(0, 300)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        if k:
            ax.set_yticklabels([])
        else:
            ax.set_ylabel("Rain vs. normal (%)")
        ax.set_title(name, fontsize=13.5, loc="left", pad=20)
        ax.text(0, 1.02, RAIN_NOTES[name], transform=ax.transAxes, fontsize=9.5, color=COLORS["text_2"],
                va="bottom")
    fig.text(0.07, 0.035, "Each dot is one water year (Oct–Sep); horizontal bars are medians. "
             "“6/7 above” = 6 of 7 seasons in that category had above-normal precipitation.", fontsize=10.5, color=COLORS["text_2"])

    la = next(s for s in summary if s[0] == "Los Angeles")
    sd = next(s for s in summary if s[0] == "San Diego")
    add_title(fig, "Southern California water-year precipitation by ENSO phase, 1951–present",
              f"Strong El Niño winters have favoured above-normal precipitation: {la[1]} of {la[2]} in Los Angeles "
              f"(median {la[3]:.0f}% of normal) and {sd[1]} of {sd[2]} in San Diego.\nThe relationship is "
              "probabilistic: the very strong 2015–16 event produced roughly half of normal precipitation in "
              "Los Angeles.")
    add_source(fig, f"Data: NOAA NCEI GHCN-Daily station records (rain season Oct–Sep, normal = "
               f"{NORMAL[0]}–{NORMAL[1]}); El Niño strength: NOAA CPC RONI, Dec–Feb. Seasons with large data gaps left out.")
    save(fig, args.out,
         alt="Bar chart of every Los Angeles rainy season since 1951 as a percent of normal, coloured by El Niño "
             "or La Niña strength, and dot plots for Los Angeles, San Diego, the Inland Empire and Santa Barbara. "
             + "; ".join(f"{n}: {w} of {t} strong El Niño seasons wetter than normal, median {m:.0f}%"
                         for n, w, t, m in summary) + ".")


if __name__ == "__main__":
    main()
