"""
Figure 2 — "El Niño and La Niña since 1950"

Bars of NOAA's Relative Oceanic Niño Index (RONI), colored red for El Niño
(>= +0.5 °C), blue for La Niña (<= -0.5 °C) and gray for neutral. The biggest
events are labelled automatically and the latest value is called out.

    python fig2_roni_timeline.py                 # downloads RONI from NOAA CPC
    python fig2_roni_timeline.py --file RONI.ascii.txt
    python fig2_roni_timeline.py --start 1980 --label-top 6
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style, 
                         load_roni, phase_color, save)


def biggest_events(s, n, min_gap_months=24, min_abs=1.5):
    """Indices of the n largest |peaks| separated by at least min_gap_months."""
    picked = []
    for t in s.abs().sort_values(ascending=False).index:
        if abs(s[t]) < min_abs or len(picked) >= n:
            break
        if all(abs((t - p).days) > min_gap_months * 30 for p in picked):
            picked.append(t)
    return picked


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="local copy of RONI.ascii.txt")
    ap.add_argument("--start", type=int, default=1950)
    ap.add_argument("--label-top", type=int, default=8, help="how many big events to label")
    ap.add_argument("--refresh", action="store_true", help="re-download even if cached")
    ap.add_argument("--out", default=str(FIG_DIR / "fig2_roni_timeline.png"))
    args = ap.parse_args()

    apply_style()
    s = load_roni(args.file, args.refresh)
    s = s[s.index.year >= args.start]

    fig, ax = plt.subplots(figsize=(14, 6.4))
    fig.subplots_adjust(top=0.78, bottom=0.10, left=0.07, right=0.90)

    colors = [phase_color(v) for v in s.values]
    ax.bar(s.index, s.values, width=31, color=colors, linewidth=0)
    for y in (0.5, -0.5):
        ax.axhline(y, color=COLORS["muted"], lw=0.9, ls=(0, (4, 3)))
    ax.axhline(0, color=COLORS["text_2"], lw=0.8)

    lim = max(2.8, np.ceil(s.abs().max() * 2) / 2 + 0.3)
    ax.set_ylim(-lim, lim)
    ax.set_xlim(s.index[0], s.index[-1] + np.timedelta64(400, "D"))
    ax.set_ylabel("Temperature difference from normal (°C)")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(mdates.YearLocator(10 if len(s) > 400 else 5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # threshold labels on the right edge
    trans = ax.get_yaxis_transform()
    ax.text(1.005, 0.5, "+0.5  El Niño\nthreshold", transform=trans, va="center",
            fontsize=10, color=COLORS["text_2"])
    ax.text(1.005, -0.5, "−0.5  La Niña\nthreshold", transform=trans, va="center",
            fontsize=10, color=COLORS["text_2"])

    # label the biggest events with their winter, e.g. "1997–98"
    for t in biggest_events(s, args.label_top):
        v = s[t]
        yr = t.year if t.month >= 6 else t.year - 1
        txt = f"{yr}–{str(yr + 1)[-2:]}"
        ax.annotate(txt, (t, v), xytext=(0, 6 if v > 0 else -6), textcoords="offset points",
                    ha="center", va="bottom" if v > 0 else "top", fontsize=11,
                    color=COLORS["text"])

    # latest value callout
    t_last, v_last = s.index[-1], s.iloc[-1]
    season = s.attrs.get("season", {}).get(t_last, t_last.strftime("%b"))
    phase = "El Niño" if v_last >= 0.5 else ("La Niña" if v_last <= -0.5 else "neutral")
    ax.annotate(f"Latest ({season} {t_last.year}): {v_last:+.2f} °C, {phase}",
                (t_last, v_last), xytext=(0.99, 1.03), textcoords="axes fraction",
                ha="right", va="bottom", fontsize=12, fontweight="bold",
                color=COLORS["text"],
                arrowprops=dict(arrowstyle="-", color=COLORS["text_2"], lw=1,
                                connectionstyle="angle,angleA=0,angleB=90,rad=0"))

    handles = [Patch(color=COLORS["el_nino"], label="El Niño (warm)"),
               Patch(color=COLORS["neutral"], label="Neutral"),
               Patch(color=COLORS["la_nina"], label="La Niña (cool)")]
    # sits above the axes so it can never cover an event label
    ax.legend(handles=handles, loc="lower left", ncol=3, bbox_to_anchor=(0, 1.0))

    add_title(fig, "El Niño and La Niña since %d" % s.index[0].year,
              "Each bar is a 3-month average of Pacific temperature in the Niño 3.4 region, compared with "
              "the rest of the tropics\n(NOAA's Relative Oceanic Niño Index). Red = El Niño, blue = La Niña.")
    add_source(fig, "Data: NOAA Climate Prediction Center, Relative Oceanic Niño Index (RONI).")
    save(fig, args.out)


if __name__ == "__main__":
    main()
