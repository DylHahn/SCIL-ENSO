"""
SoCal 6 — How summer heat has increased in Southern California since 1895

Top: maps of the change in June–September mean daily maximum and minimum
temperature, 1996–2025 minus 1951–1980 (NOAA nClimGrid, ~5 km).
Bottom: regional summer anomalies for every year since 1895, shown as
"warming stripes" (one stripe per summer) and as a time series with a
10-year running mean; summers preceding a strong El Niño winter are marked.

    python socal_warming_since_1895.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, Normalize

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save
from enso_nclimgrid import LAT, LON, socal_months, summer_months
from enso_socal import winter_roni

START = 1895
EARLY, LATE = (1951, 1980), (1996, 2025)
NORMAL = (1991, 2020)
CITIES = {"Los Angeles": (-118.24, 34.05), "San Diego": (-117.16, 32.72), "Riverside": (-117.40, 33.95),
          "Palm Springs": (-116.55, 33.83), "Santa Barbara": (-119.70, 34.42)}


def regional(da):
    w = np.cos(np.deg2rad(da["lat"]))
    s = da.weighted(w).mean(("lat", "lon")).to_series()
    counts = s.groupby(s.index.year).count()
    summ = s.groupby(s.index.year).mean()[counts == 4]          # complete summers only
    return summ - summ.loc[NORMAL[0]:NORMAL[1]].mean()


def change_map(da):
    yr = da["time"].dt.year
    late = da.sel(time=(yr >= LATE[0]) & (yr <= LATE[1])).mean("time")
    early = da.sel(time=(yr >= EARLY[0]) & (yr <= EARLY[1])).mean("time")
    return late - early


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "socal_warming_since_1895.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    data = {v: socal_months(v, summer_months(range(START, args.year + 1)), args.refresh) for v in ("tmax", "tmin")}
    series = {v: regional(d) for v, d in data.items()}
    changes = {v: change_map(d) for v, d in data.items()}

    fig = plt.figure(figsize=(13, 11.2))
    pc = ccrs.PlateCarree()

    # --- change maps ----------------------------------------------------------------------
    levels = np.arange(-0.25, 2.76, 0.25)
    cmap = plt.get_cmap("Reds", len(levels) + 1)
    norm = BoundaryNorm(levels, cmap.N, extend="both")
    names = {"tmax": "Daytime highs", "tmin": "Overnight lows"}
    for k, v in enumerate(("tmax", "tmin")):
        ax = fig.add_axes([0.03 + k * 0.49, 0.585, 0.46, 0.235], projection=pc)
        ax.set_extent([LON[0], LON[1], LAT[0], LAT[1]], crs=pc)
        ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor=COLORS["land"], edgecolor="none", zorder=0)
        ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor=COLORS["ocean"], zorder=0)
        m = changes[v]
        cf = ax.contourf(m["lon"], m["lat"], m.values, levels=levels, cmap=cmap, norm=norm, extend="both",
                         transform=pc, zorder=1)
        ax.add_feature(cfeature.LAKES.with_scale("10m"), facecolor=COLORS["ocean"], edgecolor="none", zorder=1.5)
        ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor=COLORS["text_2"], linewidth=0.6,
                       facecolor="none", zorder=2)
        ax.add_feature(cfeature.COASTLINE.with_scale("50m"), edgecolor=COLORS["text_2"], linewidth=0.6, zorder=2)
        for city, (lon, lat) in CITIES.items():
            ax.plot(lon, lat, "o", ms=4.5, color="black", mec="white", mew=1, transform=pc, zorder=4)
            ax.text(lon + 0.07, lat + 0.07, city, transform=pc, fontsize=9, color="black", zorder=4,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=0.8))
        s = series[v]
        delta = s.loc[LATE[0]:LATE[1]].mean() - s.loc[EARLY[0]:EARLY[1]].mean()
        ax.set_title(f"{names[v]}: change since {EARLY[0]}–{EARLY[1]}", fontsize=14.5, loc="left", pad=24,
                     color=COLORS["text"])
        ax.text(0, 1.015, f"Regional mean {delta:+.1f} °C ({LATE[0]}–{LATE[1]} vs. {EARLY[0]}–{EARLY[1]})",
                transform=ax.transAxes, fontsize=11, color=COLORS["text_2"], va="bottom")
    cax = fig.add_axes([0.28, 0.54, 0.44, 0.013])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=np.arange(0, 2.76, 0.5))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10, length=0)
    cb.set_label("Change in June–September mean temperature (°C)", fontsize=10.5, color=COLORS["text_2"])

    # --- warming stripes ----------------------------------------------------------------------
    stripe_norm = Normalize(-2.0, 2.0)
    stripe_cmap = plt.get_cmap("RdBu_r")
    for r, v in enumerate(("tmax", "tmin")):
        sx = fig.add_axes([0.13, 0.425 - r * 0.045, 0.84, 0.035])
        s = series[v]
        sx.bar(s.index, 1, width=1.0, color=stripe_cmap(stripe_norm(s.values)), lw=0)
        sx.set_xlim(START - 0.5, args.year + 0.5)
        sx.set_ylim(0, 1)
        sx.axis("off")
        sx.text(-0.005, 0.5, names[v], transform=sx.transAxes, ha="right", va="center", fontsize=10.5,
                color=COLORS["text_2"])
    fig.text(0.13, 0.468, "One stripe per summer, blue = cooler, red = warmer than 1991–2020", fontsize=11,
             color=COLORS["text_2"])

    # --- time series ----------------------------------------------------------------------------
    tx = fig.add_axes([0.13, 0.075, 0.84, 0.245])
    djf = winter_roni(args.refresh)
    cols = {"tmax": COLORS["heat"], "tmin": COLORS["el_nino"]}
    for v in ("tmax", "tmin"):
        s = series[v]
        tx.plot(s.index, s.values, color=cols[v], lw=0.9, alpha=0.45)
        roll = s.reindex(range(s.index.min(), s.index.max() + 1)).rolling(10, center=True, min_periods=7).mean()
        tx.plot(roll.index, roll.values, color=cols[v], lw=2.6, label=f"{names[v]} (10-year mean)")
    onset = [y for y in series["tmin"].index if djf.get(y + 1, 0) >= 1.5]
    tx.scatter(onset, series["tmin"].reindex(onset), s=26, color=COLORS["text"], zorder=4,
               label="Overnight lows, summers preceding a strong El Niño winter")
    if args.year in series["tmin"].index:
        tx.annotate(f"{args.year}", (args.year, series["tmin"][args.year]), xytext=(-4, 6),
                    textcoords="offset points", ha="right", fontsize=10.5, fontweight="bold", color=COLORS["text"])
    tx.axhline(0, color=COLORS["text_2"], lw=0.8)
    tx.set_xlim(START - 1, args.year + 1)
    tx.set_ylabel("Anomaly vs. 1991–2020 (°C)")
    tx.yaxis.grid(True)
    tx.set_axisbelow(True)
    tx.legend(loc="upper left", fontsize=10.5, labelcolor=COLORS["text_2"], ncol=3)
    tx.set_ylim(None, max(series["tmax"].max(), series["tmin"].max()) + 0.9)

    rank = lambda v: int((series[v] > series[v].get(args.year, np.inf)).sum()) + 1
    trend = {v: np.polyfit(series[v].loc[1950:].index, series[v].loc[1950:].values, 1)[0] * 10 for v in series}
    hottest = series["tmax"].sort_values(ascending=False).head(5).index
    add_title(fig, f"Summer heat in Southern California has increased since {START}",
              f"June–September overnight lows have warmed by about {trend['tmin']:.1f} °C per decade since 1950 and "
              f"daytime highs by {trend['tmax']:.1f} °C per decade. The five hottest\nsummers on record all occurred "
              f"in {min(hottest)}–{max(hottest)}; {args.year} ranks {rank('tmin')}"
              f"{'th' if rank('tmin') > 3 else ['st', 'nd', 'rd'][rank('tmin') - 1]} warmest for overnight lows.")
    add_source(fig, "Data: NOAA NCEI nClimGrid monthly (~5 km), June–September mean daily maximum and minimum "
               f"temperature, {LAT[0]:.1f}–{LAT[1]:.1f}°N, {abs(LON[1]):.1f}–{abs(LON[0]):.1f}°W; El Niño winters "
               "from NOAA CPC RONI.")
    save(fig, args.out,
         alt=f"Maps and time series of Southern California summer temperature since {START}. Change from "
             f"{EARLY[0]}–{EARLY[1]} to {LATE[0]}–{LATE[1]}: daytime highs "
             f"{series['tmax'].loc[LATE[0]:LATE[1]].mean() - series['tmax'].loc[EARLY[0]:EARLY[1]].mean():+.1f} °C, "
             f"overnight lows "
             f"{series['tmin'].loc[LATE[0]:LATE[1]].mean() - series['tmin'].loc[EARLY[0]:EARLY[1]].mean():+.1f} °C. "
             f"Five hottest summers: {', '.join(str(y) for y in sorted(hottest))}.")


if __name__ == "__main__":
    main()
