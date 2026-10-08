"""
Story 4 — "El Niños push the whole planet to new heat records"

Yearly global surface temperature (NOAA NCEI) since 1950. Years that set a new
record right after a strong El Niño winter are highlighted, and the current
year-to-date value is shown separately so it is not mistaken for a full year.

"El Niño winter" = Dec–Feb RONI at or above --threshold (default +1.0, moderate or stronger).

    python story4_global_heat.py
    python story4_global_heat.py --theme light --start 1970
"""
import argparse

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style, load_global_temp,
                         load_roni, save)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=int, default=1950)
    ap.add_argument("--threshold", type=float, default=1.0,
                    help="Dec–Feb RONI that counts as an El Niño winter (1.0 = moderate or stronger)")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "story" / "story4_global_heat.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    temp = load_global_temp(args.refresh)
    temp = temp[temp.index >= args.start]
    ytd = load_global_temp(args.refresh, ytd=True)
    roni = load_roni(refresh=args.refresh)

    # Dec–Feb RONI is stored on January: an El Niño "of winter 1997–98" sits on Jan 1998
    djf = pd.Series({t.year: v for t, v in roni.items() if t.month == 1})
    after_strong = {y for y in temp.index if djf.get(y, 0) >= args.threshold}
    full = load_global_temp(args.refresh)
    record = {y for y in temp.index if full[y] > full[full.index < y].max()}
    highlight = sorted(after_strong & record)

    fig, ax = plt.subplots(figsize=(13, 7.4))
    fig.subplots_adjust(top=0.82, bottom=0.10, left=0.07, right=0.97)

    colors = [COLORS["heat"] if y in highlight else COLORS["neutral"] for y in temp.index]
    ax.bar(temp.index, temp.values, width=0.72, color=colors, linewidth=0)
    for y in highlight:
        ax.annotate(str(y), (y, temp[y]), xytext=(0, 6), textcoords="offset points", ha="center",
                    va="bottom", fontsize=11, fontweight="bold", color=COLORS["text"])

    # this year so far, hatched so it reads as unfinished
    this_year = int(ytd.index[-1])
    if this_year > temp.index[-1]:
        ax.bar([this_year], [ytd.iloc[-1]], width=0.72, facecolor="none", edgecolor=COLORS["heat"],
               hatch="////", linewidth=1.2)
        rank = int((ytd > ytd.iloc[-1]).sum()) + 1
        ax.annotate(f"{this_year} so far (Jan–Aug): #{rank} on record", (this_year, ytd.iloc[-1]),
                    xytext=(-14, 62), textcoords="offset points", ha="right", va="center", fontsize=11.5,
                    color=COLORS["text"],
                    arrowprops=dict(arrowstyle="-", color=COLORS["text_2"], lw=1, shrinkA=4, shrinkB=3,
                                    relpos=(1, 0.5), connectionstyle="angle,angleA=0,angleB=90,rad=0"))

    ax.axhline(0, color=COLORS["text_2"], lw=0.8)
    ax.set_xlim(args.start - 1, this_year + 1)
    top = max(temp.max(), ytd.iloc[-1])
    ax.set_ylim(min(0, temp.min()) - 0.05, top + 0.42)
    ax.set_ylabel("Warmer than the 20th-century average (°C)")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.legend(handles=[Patch(color=COLORS["heat"], label="Record year coinciding with an El Niño winter"),
                       Patch(color=COLORS["neutral"], label="Other years")],
              loc="upper left", fontsize=12, labelcolor=COLORS["text_2"])

    add_title(fig, "Global mean surface temperature anomalies and El Niño, 1950–present",
              "Annual global land and ocean temperature relative to the 1901–2000 mean. El Niño releases heat "
              "from the tropical Pacific to the\natmosphere, adding to the long-term warming trend; most recent "
              "record years, including 1998, 2016 and 2024, coincided with El Niño events.")
    add_source(fig, "Data: NOAA NCEI global land & ocean surface temperature (vs. 1901–2000); "
               "El Niño strength from NOAA CPC RONI (Dec–Feb).")
    names = ", ".join(str(y) for y in highlight)
    save(fig, args.out,
         alt=f"Bar chart of global temperature each year since {args.start}, rising over time. "
             f"Highlighted record years that came with an El Niño winter: {names}. {this_year} so far is "
             f"{ytd.iloc[-1]:+.2f} °C above the 20th-century average.")


if __name__ == "__main__":
    main()
