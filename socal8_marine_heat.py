"""
SoCal 8 — Marine heat in the Southern California Bight (NOAA OISST v2.1, daily)

(a) Cumulative marine heatwave days through the year, every year since 1982,
    with 1997, 2015 and the current year highlighted.
(b) Daily sea surface temperature anomaly (7-day mean) for the same years.
(c) Marine heatwave days per year, coloured by the ENSO phase of the following
    winter (i.e. whether an El Niño was developing that year).
Marine heatwave: SST above the day-of-year 90th percentile (1991–2020) for at
least five consecutive days (Hobday et al., 2016).

    python socal8_marine_heat.py
    python socal8_marine_heat.py --refresh      # re-fetch the current year
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save
from enso_marine import BOX, CLIM, anomalies_and_mhw, bight_sst, doy_index
from enso_socal import CATEGORIES, categorize, category_colors, winter_roni

HIGHLIGHT = {1997: "#199e70", 2015: "#c98500"}
MONTH_STARTS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "socal8_marine_heat.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    sst = bight_sst(args.refresh, current_year=args.year)
    anom, mhw = anomalies_and_mhw(sst)
    last = sst.index.max()
    last_doy = int(doy_index(pd.DatetimeIndex([last]))[0])

    fig = plt.figure(figsize=(13, 10.0))
    ax_a = fig.add_axes([0.06, 0.47, 0.42, 0.32])
    ax_b = fig.add_axes([0.56, 0.47, 0.42, 0.32])
    ax_c = fig.add_axes([0.06, 0.08, 0.92, 0.26])

    to_date = {}
    for y in sorted(set(sst.index.year)):
        m = mhw.loc[str(y)]
        x = doy_index(m.index)
        cum = m.cumsum().values
        to_date[y] = int(cum[x <= last_doy][-1]) if (x <= last_doy).any() else 0
        a = anom.loc[str(y)].rolling(7, center=True, min_periods=4).mean()
        if y == args.year:
            style = dict(color=COLORS["el_nino"], lw=3.0, zorder=5)
        elif y in HIGHLIGHT:
            style = dict(color=HIGHLIGHT[y], lw=2.0, zorder=4)
        else:
            style = dict(color=COLORS["neutral"], lw=0.8, alpha=0.45, zorder=1)
        ax_a.plot(x, cum, **style)
        if y == args.year or y in HIGHLIGHT:
            ax_b.plot(doy_index(a.index), a.values, **style)
    ax_a.annotate(f"{to_date[args.year]} days", (last_doy, to_date[args.year]), xytext=(6, 0),
                  textcoords="offset points", va="center", fontsize=11, fontweight="bold", color=COLORS["text"])
    clim_b = anom.loc[str(CLIM[0]):str(CLIM[1])]
    for ax in (ax_a, ax_b):
        ax.set_xticks(MONTH_STARTS)
        ax.set_xticklabels(MONTH_LABELS, fontsize=10)
        ax.set_xlim(1, 366)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.axvline(last_doy, color=COLORS["muted"], lw=0.8, ls=(0, (3, 2)))
    ax_a.set_title("(a) Cumulative marine heatwave days", fontsize=13.5, loc="left", pad=8)
    ax_a.set_ylabel("Days")
    ax_b.axhline(0, color=COLORS["text_2"], lw=0.8)
    ax_b.set_title("(b) Daily SST anomaly (7-day mean)", fontsize=13.5, loc="left", pad=8)
    ax_b.set_ylabel("°C vs. 1991–2020")
    handles = [Line2D([], [], color=COLORS["el_nino"], lw=3, label=str(args.year))] + \
              [Line2D([], [], color=c, lw=2, label=str(y)) for y, c in HIGHLIGHT.items()] + \
              [Line2D([], [], color=COLORS["neutral"], lw=1, label="Other years since 1982")]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.055, 0.815), ncol=4, fontsize=11,
               labelcolor=COLORS["text_2"])

    # (c) heatwave days per year, coloured by the ENSO phase of the following winter
    days = mhw.groupby(mhw.index.year).sum()
    djf = winter_roni(args.refresh)
    cols = category_colors()
    cats = [categorize(djf.get(y + 1, np.nan)) for y in days.index]
    colors = [cols.get(c, COLORS["neutral"]) for c in cats]
    ax_c.bar(days.index, days.values, width=0.8, color=colors, lw=0)
    if args.year in days.index:
        # the coming winter is not observed yet; NOAA expects a strong El Niño, so mark it as such, hatched
        ax_c.bar([args.year], [days[args.year]], width=0.8, color=cols["Strong El Niño"], hatch="///",
                 edgecolor=COLORS["surface"], lw=0)
        ax_c.annotate(f"{args.year} to {last:%-d %b}\n(El Niño developing)", (args.year, days[args.year]), xytext=(-8, 0),
                      textcoords="offset points", ha="right", va="center", fontsize=10.5, fontweight="bold",
                      color=COLORS["text"])
    ax_c.set_xlim(days.index.min() - 1, days.index.max() + 1)
    ax_c.set_ylabel("Days per year")
    ax_c.yaxis.grid(True)
    ax_c.set_axisbelow(True)
    ax_c.set_title("(c) Marine heatwave days per year, coloured by the ENSO phase of the following winter",
                   fontsize=13.5, loc="left", pad=8)
    ax_c.legend(handles=[Patch(color=cols[c], label=c.replace("\n", " ")) for c, _, _ in CATEGORIES],
                loc="upper left", ncol=4, fontsize=10, labelcolor=COLORS["text_2"])
    ax_c.set_ylim(0, days.max() * 1.18)

    prev = max((y for y in to_date if y != args.year), key=lambda y: to_date[y])
    record = to_date[args.year] > to_date[prev]
    lead = (f"By {last:%-d %B}, {args.year} had accumulated {to_date[args.year]} marine heatwave days, "
            + (f"the most on record for this date (previous: {to_date[prev]} in {prev})."
               if record else f"second only to {prev} ({to_date[prev]}) for this date."))
    add_title(fig, "Marine heat in the Southern California Bight",
              lead + "\nWarm coastal water raises overnight temperatures and humidity on land and stresses kelp "
              "forests and fisheries.")
    add_source(fig, f"Data: NOAA OISST v2.1 daily (0.25°) via NOAA CoastWatch ERDDAP, area mean "
               f"{BOX['lat'][0]}–{BOX['lat'][1]}°N, {abs(BOX['lon'][1])}–{abs(BOX['lon'][0])}°W. Marine heatwave: "
               f"> 90th percentile of {CLIM[0]}–{CLIM[1]} for ≥ 5 days (Hobday et al. 2016).")
    save(fig, args.out,
         alt=f"Marine heatwave days and sea surface temperature anomalies in the Southern California Bight since "
             f"1982. By {last:%-d %B} {args.year}: {to_date[args.year]} heatwave days; same date in 1997: "
             f"{to_date.get(1997, 0)}, 2015: {to_date.get(2015, 0)}. Recent 30-day mean anomaly "
             f"{anom.loc[last - pd.Timedelta(days=30):].mean():+.1f} °C.")


if __name__ == "__main__":
    main()
