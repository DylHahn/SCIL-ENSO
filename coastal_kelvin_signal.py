"""
Kelvin waves 5 — The Kelvin-wave signal at one tide gauge on the coast of the Americas

For one tide gauge (chosen with --station, a UHSLC id), from October of the year before the current
El Niño to the latest day: the coastal sea level anomaly (UHSLC fast-delivery daily data, see
enso_tidegauges.py), and the Kelvin-wave signal, the same anomaly minus its 91-day running mean, as
for the equatorial waves in anim_kelvin.py. Dashed lines mark the days the equatorial Kelvin waves
traced in anim_kelvin.py reached 95°W, near South America, numbered as in that figure. The website
shows one version per gauge, with a button for each.

    python coastal_kelvin_signal.py --station 569
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from anim_kelvin import START, kelvin_waves, wave_signal
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save
from enso_tidegauges import STATIONS, alongshore_km, anomalies

NOW = 2026
# the gauges reporting since October 2025, south to north, numbered as in anim_coastal_sea_level.py
GAUGES = [91, 87, 569, 551, 556, 592, 558]


def short(name):
    town, place = name.split(", ")
    abbr = {"California": "CA", "Oregon": "OR", "Washington": "WA"}
    return f"{town}, {abbr.get(place, place)}"


def shade(ax, t, v):
    ax.fill_between(t, 0, v, where=v > 0, color="#e8574a", alpha=0.75, lw=0, interpolate=True)
    ax.fill_between(t, 0, v, where=v < 0, color="#3987e5", alpha=0.75, lw=0, interpolate=True)
    ax.plot(t, v, color=COLORS["text"], lw=1.1)
    ax.axhline(0, color=COLORS["text_2"], lw=0.8)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--station", type=int, default=GAUGES[0], help="UHSLC station id")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "kelvin" / "coastal_kelvin_signal.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    k = [s[0] for s in STATIONS].index(args.station)
    _, name, lat, lon = STATIONS[k]
    km = alongshore_km()[k]
    num = GAUGES.index(args.station) + 1 if args.station in GAUGES else None
    anom, _ = anomalies(refresh=args.refresh)
    s = anom[name]
    sig = wave_signal(s).loc[START:]
    s = s.loc[START:]
    last = s.last_valid_index()
    s, sig = s.loc[:last], sig.loc[:last]
    _, _, waves = kelvin_waves(args.refresh)
    waves = [w for w in waves if w[0] + (w[3] - w[0]) / 2 >= pd.Timestamp(START)]   # as numbered in anim_kelvin.py
    t = s.index

    fig = plt.figure(figsize=(13, 8.6))
    top = fig.add_axes([0.08, 0.52, 0.66, 0.29])
    bot = fig.add_axes([0.08, 0.13, 0.66, 0.32], sharex=top)
    shade(top, t, s.values)
    shade(bot, t, sig.values)
    lim = max(20, np.ceil(np.nanmax(np.abs(s.values)) / 10) * 10)
    top.set_ylim(-lim, lim)
    slim = max(8, np.ceil(np.nanmax(np.abs(sig.values)) / 4) * 4)
    bot.set_ylim(-slim, slim)
    top.set_ylabel("Sea level (cm)")
    bot.set_ylabel("Wave signal (cm)")
    top.set_title("Coastal sea level compared with normal", fontsize=13.5, fontweight="bold", loc="left", pad=8,
                  color=COLORS["text"])
    bot.set_title("Kelvin-wave signal: sea level minus its 91-day average, so each passing wave is a separate peak",
                  fontsize=13.5, fontweight="bold", loc="left", pad=8, color=COLORS["text"])
    for ax in (top, bot):
        ax.yaxis.grid(True, color=COLORS["grid"], lw=0.6)
        ax.set_axisbelow(True)
        ax.set_xlim(pd.Timestamp(START), pd.Timestamp(f"{NOW}-12-31"))
        ax.tick_params(axis="both", labelsize=11)
        for n, w in enumerate(waves, 1):
            ax.axvline(w[3], color=COLORS["text"], lw=1, ls=(0, (4, 3)), alpha=0.7)
            if ax is top:
                ax.text(w[3], lim * 0.96, f" {n}", fontsize=10.5, fontweight="bold", color=COLORS["text"], va="top")
        if last < pd.Timestamp(f"{NOW}-12-31"):
            ax.axvspan(last + pd.Timedelta(days=1), pd.Timestamp(f"{NOW}-12-31"), color=COLORS["surface_2"], lw=0)
    bot.text(last + pd.Timedelta(days=6), 0, f"Data through\n{last:%-d %b %Y}", fontsize=10.5, va="center",
             color=COLORS["text_2"])
    plt.setp(top.get_xticklabels(), visible=False)
    bot.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    bot.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    for tl in top.get_yticklabels() + bot.get_xticklabels() + bot.get_yticklabels():
        tl.set_fontweight("bold")

    # where the gauge is
    pc = ccrs.PlateCarree()
    mx = fig.add_axes([0.765, 0.42, 0.22, 0.39], projection=ccrs.PlateCarree(central_longitude=-100))
    mx.set_extent([-132, -74, -8, 52], crs=pc)
    mx.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"])
    mx.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none")
    mx.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5)
    mx.plot([-132, -74], [0, 0], color=COLORS["muted"], lw=0.7, ls=(0, (4, 3)), transform=pc)
    for g in GAUGES:
        st = STATIONS[[x[0] for x in STATIONS].index(g)]
        mx.plot(st[3], st[2], "o", ms=5, color=COLORS["muted"], transform=pc, zorder=4)
    mx.plot(lon, lat, "o", ms=11, color=COLORS["el_nino"], mec="white", mew=1.4, transform=pc, zorder=5)
    fig.text(0.765, 0.36, f"{f'{num}  ' if num else ''}{name}\n{abs(lat):.1f}°{'N' if lat >= 0 else 'S'}, {abs(lon):.1f}°W\n"
             + (f"about {km:,.0f} km along the coast\nfrom La Libertad, Ecuador" if abs(km) > 1 else "Starting point"),
             fontsize=11, fontweight="bold", color=COLORS["text"], va="top", linespacing=1.4)
    fig.text(0.765, 0.17, "Dashed lines: the days the\nequatorial Kelvin waves of\nFigure 2 reached 95°W,\n"
             "near South America.", fontsize=10.5, color=COLORS["text_2"], va="top", linespacing=1.35)

    add_title(fig, f"The Kelvin-wave signal at {short(name)}, October {NOW - 1} to {last:%B %Y}",
              f"Daily tide-gauge sea level. Over its last 30 days of data, sea level here was {s.iloc[-30:].mean():+.0f} "
              f"cm compared with normal.\nEach peak in the lower panel is a rise in sea level passing the gauge; compare its timing with the "
              "arrival of the equatorial Kelvin waves (dashed lines).")
    add_source(fig, "Data: University of Hawaii Sea Level Center fast-delivery daily tide-gauge data, anomalies from the "
               "station's 1991–2020 seasonal cycle, 10-day means, not corrected for air pressure;\nequatorial Kelvin "
               "waves traced in NOAA blended satellite altimetry (see Figure 2). The signal in the last 45 days uses a shorter "
               "average and may change.")
    save(fig, args.out,
         alt=f"Time series of coastal sea level and its Kelvin-wave signal at {name} from October {NOW - 1} to "
             f"{last:%-d %B %Y}, with the arrival dates of {len(waves)} equatorial Kelvin waves at 95°W. Last 30 days: "
             f"{s.iloc[-30:].mean():+.0f} cm compared with normal.")


if __name__ == "__main__":
    main()
