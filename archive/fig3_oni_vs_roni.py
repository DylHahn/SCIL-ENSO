"""
Figure 3 — "Why NOAA switched to a relative index"

Top: the traditional ONI and the new RONI on the same axis.
Bottom: ONI minus RONI, smoothed, showing how the traditional index has
drifted warmer as the whole tropical ocean warms.

    python fig3_oni_vs_roni.py
    python fig3_oni_vs_roni.py --start 1990
"""
import argparse

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style,
                         load_oni, load_roni, save)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--roni-file")
    ap.add_argument("--oni-file")
    ap.add_argument("--start", type=int, default=1950)
    ap.add_argument("--smooth-years", type=float, default=5, help="running mean for the difference panel")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "fig3_oni_vs_roni.png"))
    args = ap.parse_args()

    apply_style()
    roni, oni = load_roni(args.roni_file, args.refresh), load_oni(args.oni_file, args.refresh)

    both = roni.to_frame("RONI").join(oni.rename("ONI"), how="inner")
    both = both[both.index.year >= args.start]
    diff = (both["ONI"] - both["RONI"])
    diff_smooth = diff.rolling(int(args.smooth_years * 12), center=True, min_periods=12).mean()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8.2), sharex=True,
                                   gridspec_kw=dict(height_ratios=[2.2, 1], hspace=0.12))
    fig.subplots_adjust(top=0.83, bottom=0.09, left=0.08, right=0.88)

    ax1.plot(both.index, both["ONI"], color=COLORS["series_2"], lw=1.6)
    ax1.plot(both.index, both["RONI"], color=COLORS["series_1"], lw=1.6)
    for y in (0.5, -0.5):
        ax1.axhline(y, color=COLORS["muted"], lw=0.9, ls=(0, (4, 3)))
    ax1.axhline(0, color=COLORS["text_2"], lw=0.8)
    ax1.set_ylabel("Index (°C)")
    ax1.yaxis.grid(True)
    ax1.set_axisbelow(True)
    # direct labels at the right end instead of a color-only legend
    last = both.index[-1]
    for col, c, dy in (("ONI", COLORS["series_2"], 10), ("RONI", COLORS["series_1"], -10)):
        ax1.annotate(f"{col}  {both[col].iloc[-1]:+.2f}", (last, both[col].iloc[-1]),
                     xytext=(8, dy), textcoords="offset points", va="center",
                     fontsize=12, fontweight="bold", color=COLORS["text"],
                     annotation_clip=False)
        ax1.plot([], [], color=c, lw=2.5, label={"ONI": "Traditional index (ONI)",
                                                 "RONI": "Relative index (RONI) — official since Feb 2026"}[col])
    ax1.legend(loc="upper left", ncol=2, bbox_to_anchor=(0, 1.08))

    ax2.fill_between(diff.index, 0, diff, color=COLORS["series_2"], alpha=0.18, linewidth=0)
    ax2.plot(diff_smooth.index, diff_smooth, color=COLORS["series_2"], lw=2.2)
    ax2.axhline(0, color=COLORS["text_2"], lw=0.8)
    ax2.set_ylabel("ONI − RONI (°C)")
    ax2.yaxis.grid(True)
    ax2.set_axisbelow(True)
    ax2.text(0.01, 0.92, f"Gap between the two ({args.smooth_years:g}-year average line)",
             transform=ax2.transAxes, va="top", fontsize=12, color=COLORS["text_2"])
    ax2.xaxis.set_major_locator(mdates.YearLocator(10))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    add_title(fig, "Why NOAA switched to a relative El Niño index",
              "The whole tropical ocean is warming, so the old index drifts warmer over time. "
              "The relative index measures how much warmer\nthe Niño 3.4 region is than the "
              "tropics around it — which is what actually drives the weather.")
    add_source(fig, "Data: NOAA Climate Prediction Center, ONI (ERSSTv6) and RONI.")
    save(fig, args.out)


if __name__ == "__main__":
    main()
