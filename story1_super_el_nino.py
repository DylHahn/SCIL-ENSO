"""
Story 1 — "Is this a Super El Niño?"

The 2026 El Niño month by month (NOAA's official RONI index), NOAA's forecast
range for the coming seasons, and the biggest past El Niños for comparison,
all on one strength scale (weak / moderate / strong / very strong).

    python story1_super_el_nino.py                 # dark theme for icharm.sdsu.edu
    python story1_super_el_nino.py --theme light
    python story1_super_el_nino.py --refresh       # pull NOAA's latest monthly update
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style, load_cpc_outlook,
                         load_cpc_strengths, load_roni, save, season_words)

PAST_EVENTS = [1972, 1982, 1997, 2015]        # the "super" El Niños before 2026 (year the event began)
STRENGTHS = [(0.5, "Weak"), (1.0, "Moderate"), (1.5, "Strong"), (2.0, "Very strong\n(“super”)")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026, help="year the current El Niño began")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true", help="re-download NOAA data")
    ap.add_argument("--out", default=str(FIG_DIR / "story" / "story1_super_el_nino.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    roni = load_roni(refresh=args.refresh)
    outlook = load_cpc_outlook(args.refresh)
    strengths = load_cpc_strengths(args.refresh)

    y0 = args.year
    start, end = pd.Timestamp(f"{y0}-01-01"), pd.Timestamp(f"{y0 + 1}-06-01")
    now = roni[start:end]

    fig, ax = plt.subplots(figsize=(13, 7.6))
    fig.subplots_adjust(top=0.84, bottom=0.10, left=0.07, right=0.84)

    # strength scale: faint threshold lines, labels on the right, only "super" territory shaded
    edges = [s for s, _ in STRENGTHS] + [3.0]
    for (lo, label), hi in zip(STRENGTHS, edges[1:]):
        ax.axhline(lo, color=COLORS["muted"], lw=0.8, ls=(0, (4, 3)), alpha=0.7)
        ax.text(1.01, (lo + hi) / 2, label, transform=ax.get_yaxis_transform(),
                va="center", fontsize=12, color=COLORS["text_2"])
    ax.axhspan(2.0, 3.6, color=COLORS["el_nino"], alpha=0.08, lw=0)
    ax.axhline(0, color=COLORS["text_2"], lw=0.8)

    # past giants, shifted onto this event's calendar
    record_val, record_lbl = -np.inf, ""
    for yr in PAST_EVENTS:
        seg = roni[f"{yr}-01":f"{yr + 1}-06"]
        x = seg.index + pd.DateOffset(years=y0 - yr)
        ax.plot(x, seg.values, color=COLORS["muted"], lw=1.6, alpha=0.9)
        lbl = f"{yr}–{str(yr + 1)[-2:]}"
        if seg.max() > record_val:
            record_val, record_lbl = seg.max(), lbl

    # NOAA forecast: 90% and 50% ranges plus the middle estimate, joined to the last observation
    fc = outlook[outlook.index > now.index[-1]]
    join = pd.DataFrame({c: [now.iloc[-1]] for c in fc.columns if c.startswith("p")}, index=[now.index[-1]])
    fc = pd.concat([join, fc[join.columns]])
    ax.fill_between(fc.index, fc["p5"], fc["p95"], color=COLORS["el_nino"], alpha=0.18, lw=0)
    ax.fill_between(fc.index, fc["p25"], fc["p75"], color=COLORS["el_nino"], alpha=0.35, lw=0)
    ax.plot(fc.index, fc["p50"], color=COLORS["el_nino"], lw=2.4, ls=(0, (4, 3)))

    # this year, observed
    ax.plot(now.index, now.values, color=COLORS["el_nino"], lw=3.4, solid_capstyle="round")
    ax.plot(now.index[-1], now.iloc[-1], "o", ms=10, color=COLORS["el_nino"],
            mec=COLORS["surface"], mew=2, zorder=5)
    season = season_words(roni.attrs["season"][now.index[-1]])
    ax.annotate(f"Now ({season} {now.index[-1].year})\n{now.iloc[-1]:+.1f} °C",
                (now.index[-1], now.iloc[-1]), xytext=(-14, 4), textcoords="offset points",
                ha="right", va="bottom", fontsize=13, fontweight="bold", color=COLORS["text"])

    peak = fc["p50"].idxmax()
    ax.annotate(f"NOAA forecast\nmiddle estimate {fc['p50'].max():+.1f} °C",
                (peak, fc["p50"].max()), xytext=(70, 4), textcoords="offset points",
                fontsize=12, color=COLORS["text"], va="center",
                arrowprops=dict(arrowstyle="-", color=COLORS["text_2"], lw=1))
    ax.axhline(record_val, color=COLORS["text_2"], lw=1, ls=(0, (1, 2)))
    ax.text(start + pd.Timedelta(days=10), record_val + 0.05,
            f"Strongest on record so far: {record_val:+.1f} °C ({record_lbl})",
            fontsize=11, color=COLORS["text_2"], va="bottom")

    ax.set_xlim(start, end)
    ax.set_ylim(-1.2, 3.4)
    ax.set_ylabel("Ocean temperature vs. normal (°C)")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))

    handles = [Line2D([], [], color=COLORS["el_nino"], lw=3.4, label=f"{y0} so far"),
               Line2D([], [], color=COLORS["el_nino"], lw=2.4, ls=(0, (4, 3)), label="NOAA forecast"),
               Patch(color=COLORS["el_nino"], alpha=0.35, label="Likely range"),
               Line2D([], [], color=COLORS["muted"], lw=1.6, label="Past super El Niños: 1972, 1982, 1997, 2015")]
    ax.legend(handles=handles, loc="lower right", ncol=2, fontsize=11.5, labelcolor=COLORS["text_2"],
              bbox_to_anchor=(1.0, 0.0))

    vs = strengths["en_vstrong"]
    add_title(fig, f"{y0} is shaping up to be a Super El Niño",
              f"NOAA ({outlook.attrs['issued']} outlook): {vs.max():.0f}% chance of a “very strong” El Niño by "
              f"{season_words(strengths.loc[vs.idxmax(), 'season'])}, with a real chance it beats every\nEl Niño since records "
              f"began in 1950. Gray lines show the four biggest past events on the same calendar.")
    add_source(fig, "Data: NOAA Climate Prediction Center — Relative Oceanic Niño Index (RONI) and official "
               "RONI outlook. Values are 3-month averages, plotted on the middle month.")
    save(fig, args.out,
         alt=f"Line chart of El Niño strength from January {y0} to June {y0 + 1}. {y0} rose from "
             f"{now.iloc[0]:+.1f} °C in January to {now.iloc[-1]:+.1f} °C now; NOAA's forecast peaks near "
             f"{fc['p50'].max():+.1f} °C, above the record of {record_val:+.1f} °C set in {record_lbl}.")


if __name__ == "__main__":
    main()
