"""
Compare 2 — "At the surface: this year vs. past super El Niños"

Sea and land surface temperature differences from normal across the tropical
Pacific in the same month of each big El Niño year (default: the latest month
of data). Uses NOAAGlobalTemp, the dataset on iCHARM's front page.

Each map is labelled with two numbers: the Niño 3.4 box, and the average over
the whole tropics (20°S–20°N). Their gap is what NOAA's relative index tracks,
and it shows how much of today's warmth is El Niño versus a warmer ocean overall.

    python surface_comparison.py
    python surface_comparison.py --month 7
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from enso_common import (temp_cmap, FIG_DIR, COLORS, NINO_BOXES, add_source, add_title, apply_style, save)
from enso_stats import load_gridded


def box_mean(da, lat, lon):
    sub = da.sel(lat=slice(*lat), lon=slice(*lon))
    return float(sub.weighted(np.cos(np.deg2rad(sub["lat"]))).mean(("lat", "lon")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, nargs="+", default=[1982, 1997, 2015, 2026],
                    help="El Niño years to compare; the last one is highlighted")
    ap.add_argument("--month", type=int, help="calendar month (default: latest available)")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "compare" / "surface_comparison.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.util import add_cyclic_point

    apply_style(args.theme)
    temp = load_gridded("temp", args.refresh)
    month = args.month or int(pd.Timestamp(temp["time"].values[-1]).month)
    mon = temp.where(temp["time.month"] == month, drop=True)
    normal = mon.sel(time=slice("1991", "2020")).mean("time")
    now = args.years[-1]
    sst = load_gridded("sst", args.refresh)                 # actual SST for the maps (ERSST v5)

    proj = ccrs.PlateCarree(central_longitude=190)
    fig = plt.figure(figsize=(13, 8.0))
    levels = np.arange(18, 31.01, 0.5)
    cmap, norm = temp_cmap(levels)
    n34 = NINO_BOXES["Niño 3.4"]
    stats = []
    for k, y in enumerate(args.years):
        r, c = divmod(k, 2)
        ax = fig.add_axes([0.02 + c * 0.49, 0.53 - r * 0.34, 0.47, 0.25], projection=proj)
        field = sst.sel(time=f"{y}-{month:02d}").squeeze("time")
        field = field.ffill("lon").bfill("lon").interp(lat=np.arange(-39.5, 40, 1.0), lon=np.arange(0.5, 360, 1.0))
        data, lon = add_cyclic_point(field.values, coord=field["lon"].values)
        cf = ax.contourf(lon, field["lat"].values, data, levels=levels, cmap=cmap, norm=norm, extend="both",
                         transform=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none", zorder=2)
        ax.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5, zorder=3)
        ax.set_extent([100, 290, -30, 30], crs=ccrs.PlateCarree())
        (la0, la1), (lo0, lo1) = n34["lat"], n34["lon"]
        ax.plot([lo0, lo1, lo1, lo0, lo0], [la0, la0, la1, la1, la0], color="black", lw=1.4,
                transform=ccrs.PlateCarree(), zorder=4)
        raw = mon.sel(time=f"{y}-{month:02d}").squeeze("time") - normal
        v34 = box_mean(raw, n34["lat"], n34["lon"])
        vtrop = box_mean(raw, (-20, 20), (0, 360))
        stats.append((y, v34, vtrop))
        cur = y == now
        ax.spines["geo"].set_edgecolor(COLORS["el_nino"] if cur else COLORS["grid"])
        ax.spines["geo"].set_linewidth(2.5 if cur else 0.8)
        ax.text(0.0, 1.04, f"{calendar.month_name[month]} {y}", transform=ax.transAxes, fontsize=15,
                fontweight="bold", color=COLORS["el_nino"] if cur else COLORS["text"], va="bottom")
        ax.text(1.0, 1.04, f"Niño 3.4 box {v34:+.1f} °C · whole tropics {vtrop:+.1f} °C",
                transform=ax.transAxes, fontsize=11, color=COLORS["text"] if cur else COLORS["text_2"],
                va="bottom", ha="right")

    cax = fig.add_axes([0.25, 0.095, 0.5, 0.02])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=np.arange(18, 32, 2))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=11, length=0)
    cb.set_label("Sea surface temperature (°C), ERSST v5   ·   "
                 "black box: Niño 3.4", fontsize=11.5, color=COLORS["text_2"])

    cur, past = stats[-1], stats[:-1]
    rel = {y: a - b for y, a, b in stats}            # Niño 3.4 minus the tropics: NOAA's relative view
    headline = f"Tropical Pacific sea surface temperature in {calendar.month_name[month]}: {now} and past very strong events"
    rel_past = ", ".join(f"{y} {rel[y]:+.1f}" for y, _, _ in past)
    add_title(fig, headline,
              f"Niño 3.4 anomaly {cur[1]:+.1f} °C, the highest of the four years at this stage. The tropical mean "
              f"(20°S–20°N) is also {cur[2]:+.1f} °C, above any previous event, so relative to\nthe tropics, the "
              f"basis of NOAA's RONI, the anomaly is {rel[now]:+.1f} °C ({rel_past}).")
    add_source(fig, "Maps: NOAA ERSST v5 monthly sea surface temperature (2°, smoothed for display). Anomaly values: "
               "NOAAGlobalTemp v6 relative to the 1991–2020 monthly normal.")
    save(fig, args.out,
         alt=f"Four maps of tropical Pacific surface temperature in {calendar.month_name[month]} of "
             + ", ".join(str(y) for y in args.years) + ". " + "; ".join(
                 f"{y}: Niño 3.4 {a:+.1f} °C, whole tropics {b:+.1f} °C" for y, a, b in stats) + ".")


if __name__ == "__main__":
    main()
