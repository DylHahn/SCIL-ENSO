"""
SoCal 4 — Summer temperature anomaly maps and regional ranking (NOAA nClimGrid)

Top: maps of June–September mean daily maximum and minimum temperature for the
selected summer, relative to the 1991–2020 normal, across Southern California
(~5 km grid). Bottom: the regional-mean overnight-low anomaly for every summer
since 1950, with summers preceding a strong El Niño winter marked.

    python socal4_heatmap.py
    python socal4_heatmap.py --year 2015      # any past summer
    python socal4_heatmap.py --refresh        # re-read the SoCal window from NCEI
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.patches import Patch

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save
from enso_nclimgrid import LAT, LON, socal_months, summer_months
from enso_socal import winter_roni

CITIES = {"Los Angeles": (-118.24, 34.05), "San Diego": (-117.16, 32.72), "Riverside": (-117.40, 33.95),
          "Palm Springs": (-116.55, 33.83), "Santa Barbara": (-119.70, 34.42)}
NORMAL = (1991, 2020)


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def summer_anomalies(var, years, target, refresh):
    da = socal_months(var, summer_months(years), refresh)
    yr = da["time"].dt.year
    normal = da.sel(time=(yr >= NORMAL[0]) & (yr <= NORMAL[1])).groupby("time.month").mean()
    target_map = (da.sel(time=yr == target).groupby("time.month").mean() - normal).mean("month")
    w = np.cos(np.deg2rad(da["lat"]))
    reg = da.weighted(w).mean(("lat", "lon")).to_series()
    summer = reg.groupby(reg.index.year).mean()
    return target_map, summer - summer.loc[NORMAL[0]:NORMAL[1]].mean()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--start", type=int, default=1950)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "socal4_heatmap.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    years = range(args.start, max(args.year, 2026) + 1)
    maps, series = {}, {}
    for var in ("tmax", "tmin"):
        maps[var], series[var] = summer_anomalies(var, years, args.year, args.refresh)

    fig = plt.figure(figsize=(13, 9.8))
    pc = ccrs.PlateCarree()
    levels = np.arange(-3.25, 3.5, 0.5)
    cmap = plt.get_cmap("RdBu_r", len(levels) - 1)
    norm = BoundaryNorm(levels, cmap.N)
    titles = {"tmax": "Daytime highs", "tmin": "Overnight lows"}
    for k, var in enumerate(("tmax", "tmin")):
        ax = fig.add_axes([0.03 + k * 0.49, 0.515, 0.46, 0.27], projection=pc)
        ax.set_extent([LON[0], LON[1], LAT[0], LAT[1]], crs=pc)
        ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor=COLORS["land"], edgecolor="none", zorder=0)
        ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor=COLORS["ocean"], zorder=0)
        m = maps[var]
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
        reg = series[var][args.year]
        rank = int((series[var] > reg).sum()) + 1
        ax.set_title(f"{titles[var]}, Jun–Sep {args.year}", fontsize=15, loc="left", pad=24, color=COLORS["text"])
        ax.text(0, 1.015, f"Regional mean {reg:+.1f} °C · {ordinal(rank)} warmest of {len(series[var])} summers",
                transform=ax.transAxes, fontsize=11, color=COLORS["text_2"], va="bottom")
    cax = fig.add_axes([0.28, 0.455, 0.44, 0.015])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=np.arange(-3, 3.5, 1))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10, length=0)
    cb.set_label("Temperature anomaly (°C) relative to the 1991–2020 Jun–Sep normal", fontsize=10.5,
                 color=COLORS["text_2"])

    # regional overnight-low anomaly, every summer
    djf = winter_roni(args.refresh)
    s = series["tmin"]
    onset = {y for y in s.index if djf.get(y + 1, 0) >= 1.5 and y != args.year}
    bx = fig.add_axes([0.07, 0.075, 0.90, 0.25])
    colors = [COLORS["el_nino"] if y == args.year else COLORS["el_nino_soft"] if y in onset else COLORS["neutral"]
              for y in s.index]
    bx.bar(s.index, s.values, width=0.8, color=colors, lw=0)
    bx.axhline(0, color=COLORS["text_2"], lw=0.8)
    bx.set_xlim(s.index.min() - 1, s.index.max() + 1)
    bx.set_ylim(s.min() - 0.2, s.max() + 0.7)          # headroom for the label above the latest bar
    bx.set_ylabel("Anomaly (°C)")
    bx.yaxis.grid(True)
    bx.set_axisbelow(True)
    bx.set_title("Southern California mean overnight low, Jun–Sep, every summer since 1950", fontsize=13,
                 loc="left", pad=8)
    bx.annotate(f"{args.year}: {s[args.year]:+.1f} °C", (args.year, s[args.year]), xytext=(-6, 2),
                textcoords="offset points", ha="right", va="bottom", fontsize=10.5, fontweight="bold",
                color=COLORS["text"])
    bx.legend(handles=[Patch(color=COLORS["el_nino"], label=f"{args.year}"),
                       Patch(color=COLORS["el_nino_soft"], label="Summers preceding a strong El Niño winter"),
                       Patch(color=COLORS["neutral"], label="Other summers")],
              loc="upper left", fontsize=10.5, ncol=3, labelcolor=COLORS["text_2"])

    rmax = int((series["tmax"] > series["tmax"][args.year]).sum()) + 1
    rmin = int((series["tmin"] > s[args.year]).sum()) + 1
    add_title(fig, f"Summer {args.year} temperatures in Southern California relative to 1991–2020",
              f"June–September mean overnight lows were {s[args.year]:+.1f} °C above normal across the region, the "
              f"{ordinal(rmin)} warmest since {args.start}; daytime highs were {series['tmax'][args.year]:+.1f} °C "
              f"({ordinal(rmax)}).\nMost earlier summers preceding strong El Niño winters were near or below normal; "
              "recent warmth reflects the long-term warming trend as well as ENSO.")
    add_source(fig, f"Data: NOAA NCEI nClimGrid monthly (~5 km), mean daily maximum and minimum temperature; "
               f"region {LAT[0]:.1f}–{LAT[1]:.1f}°N, {abs(LON[1]):.1f}–{abs(LON[0]):.1f}°W (land only).")
    save(fig, args.out,
         alt=f"Maps of Southern California June–September {args.year} temperature anomalies relative to "
             f"1991–2020: daytime highs {series['tmax'][args.year]:+.1f} °C ({ordinal(rmax)} warmest since "
             f"{args.start}), overnight lows {s[args.year]:+.1f} °C ({ordinal(rmin)} warmest). Bar chart of the "
             "regional overnight-low anomaly for every summer since 1950.")


if __name__ == "__main__":
    main()
