"""
SoCal 2 — "Summer heat in Southern California, 1950 to now"

For four stations, each summer's (Jun–Sep) count of warm nights (low ≥ 65 °F)
and hot days (high ≥ 90 °F) since 1950. Summers when a strong El Niño was
building (like this one) are shown in red; the current summer is highlighted
with its rank. The grey line is the 10-year running average.

What the data shows: warm nights have increased almost everywhere, and El Niño
summers sit on top of that trend; El Niño alone is not a reliable heat signal
for SoCal summers, so this graphic says so rather than implying one.

    python socal2_heat.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save
from enso_socal import STATIONS, STATION_NOTES, load_station, winter_roni

WARM_NIGHT_C = (65 - 32) / 1.8      # 65 °F
HOT_DAY_C = (90 - 32) / 1.8         # 90 °F
MONTHS = [6, 7, 8, 9]


def summer_counts(daily, start):
    s = daily.loc[str(start):]
    s = s[s.index.month.isin(MONTHS)]
    yr = s.index.year
    ok_n = s["TMIN"].groupby(yr).count() >= 110          # of 122 days
    ok_d = s["TMAX"].groupby(yr).count() >= 110
    nights = (s["TMIN"] >= WARM_NIGHT_C).groupby(yr).sum()[ok_n]
    days = (s["TMAX"] >= HOT_DAY_C).groupby(yr).sum()[ok_d]
    return nights, days


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def most_phrase(rank):
    return "the most" if rank == 1 else f"the {ordinal(rank)}-most"


def shade_gaps(ax, years, start, end, min_len=5):
    """Grey band + label over runs of >= min_len missing summers, so gaps read as gaps."""
    missing = [y for y in range(start, end + 1) if y not in set(years)]
    runs, run = [], []
    for y in missing:
        if run and y != run[-1] + 1:
            runs.append(run); run = []
        run.append(y)
    if run:
        runs.append(run)
    for r in runs:
        if len(r) >= min_len:
            ax.axvspan(r[0] - 0.5, r[-1] + 0.5, color=COLORS["grid"], alpha=0.6, lw=0)
            ax.text((r[0] + r[-1]) / 2, 0.5, "no data", transform=ax.get_xaxis_transform(), ha="center",
                    va="center", fontsize=10, color=COLORS["text_2"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026, help="summer to highlight")
    ap.add_argument("--start", type=int, default=1950)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "socal2_heat.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    djf = winter_roni(args.refresh)
    strong_building = {y for y in range(args.start, args.year + 1) if djf.get(y + 1, 0) >= 1.5}
    strong_building.discard(args.year)

    fig = plt.figure(figsize=(13, 9.6))
    rows = [("Warm nights (low ≥ 65 °F)", 0), ("Hot days (high ≥ 90 °F)", 1)]
    notes = []
    for k, (name, sid) in enumerate(STATIONS.items()):
        nights, days = summer_counts(load_station(sid, args.refresh), args.start)
        for label, r in rows:
            series = nights if r == 0 else days
            ax = fig.add_axes([0.06 + k * 0.237, 0.50 - r * 0.38, 0.205, 0.28])
            colors = [COLORS["el_nino"] if y == args.year else
                      (COLORS["el_nino_soft"] if y in strong_building else COLORS["neutral"]) for y in series.index]
            ax.bar(series.index, series.values, width=0.85, color=colors, lw=0)
            shade_gaps(ax, series.index, args.start, args.year)
            roll = series.reindex(range(series.index.min(), series.index.max() + 1)).rolling(
                10, center=True, min_periods=6).mean()
            ax.plot(roll.index, roll.values, color=COLORS["text"], lw=1.4, alpha=0.8)
            ax.set_xlim(args.start - 1, args.year + 1)
            ax.set_xticks([1960, 1980, 2000, 2020])
            ax.tick_params(labelsize=10)
            ax.yaxis.grid(True)
            ax.set_axisbelow(True)
            ax.set_ylim(0, max(series.max() * 1.22, 5))
            if args.year in series.index:
                v = int(series[args.year])
                rank = int((series > v).sum()) + 1
                gappy = len(series) < 0.8 * (args.year - args.start + 1)
                of = f"{len(series)} summers with data" if gappy else str(len(series))
                ax.annotate(f"{args.year}: {v}\n({ordinal(rank)} of {of})", (args.year, v),
                            xytext=(-4, 4), textcoords="offset points", ha="right", va="bottom", fontsize=10,
                            fontweight="bold", color=COLORS["text"],
                            bbox=dict(facecolor=COLORS["surface"], edgecolor="none", alpha=0.75, pad=1.5))
                if r == 0:
                    typical = series.loc[1991:2020].mean()
                    notes.append((name, v, rank, len(series), typical))
            if r == 0:
                ax.set_title(f"{name}", fontsize=13.5, loc="left", pad=22)
                ax.text(0, 1.03, STATION_NOTES[name], transform=ax.transAxes, fontsize=9.5,
                        color=COLORS["text_2"], va="bottom")
            if k == 0:
                ax.set_ylabel(label + "\nper summer (Jun–Sep)", fontsize=11)

    fig.legend(handles=[Patch(color=COLORS["el_nino"], label=f"Summer {args.year}"),
                        Patch(color=COLORS["el_nino_soft"], label="Earlier summers with a strong El Niño building"),
                        Patch(color=COLORS["neutral"], label="Other summers")],
               loc="lower left", bbox_to_anchor=(0.055, 0.845), ncol=3, fontsize=11.5, labelcolor=COLORS["text_2"])

    best = max(notes, key=lambda n: n[1] / max(n[4], 1))
    add_title(fig, f"Summer {args.year} brought some of Southern California's warmest nights on record",
              f"{best[0]} had {best[1]} warm nights, {most_phrase(best[2])} since {args.start}, against about "
              f"{best[4]:.0f} in a typical recent summer. Warm nights have been rising for decades;\nwarm ocean "
              "water near the coast, common while a strong El Niño builds, adds to it. Hot nights matter for "
              "health because bodies can't cool down.")
    add_source(fig, f"Data: NOAA NCEI GHCN-Daily station records, Jun–Sep {args.start}–{args.year}; summers with "
               "large data gaps left out. Line: 10-year running average. El Niño strength: NOAA CPC RONI.")
    save(fig, args.out,
         alt=f"Bar charts of warm nights and hot days each summer since {args.start} at Los Angeles, San Diego, "
             f"the Inland Empire and Santa Barbara. Summer {args.year}: " + "; ".join(
                 f"{n} {v} warm nights ({ordinal(rk)} of {t}, typical {ty:.0f})" for n, v, rk, t, ty in notes) + ".")


if __name__ == "__main__":
    main()
