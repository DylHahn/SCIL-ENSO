"""
Compare 2 — "At the surface: this year vs. past super El Niños"

Sea and land surface temperature differences from normal across the tropical
Pacific in the same month of each big El Niño year (default: the latest month
of data). Uses NOAAGlobalTemp, the dataset on iCHARM's front page.

Each map is labelled with two numbers: the Niño 3.4 box, and the average over
the whole tropics (20°S–20°N). Their gap is what NOAA's relative index tracks,
and it shows how much of today's warmth is El Niño versus a warmer ocean overall.

    python compare2_surface.py
    python compare2_surface.py --month 7
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from enso_common import (FIG_DIR, COLORS, NINO_BOXES, add_source, add_title, apply_style, save)
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
    ap.add_argument("--out", default=str(FIG_DIR / "compare" / "compare2_surface.png"))
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

    proj = ccrs.PlateCarree(central_longitude=190)
    fig = plt.figure(figsize=(13, 8.0))
    levels = np.arange(-3.25, 3.5, 0.5)
    cmap = plt.get_cmap("RdBu_r", len(levels) - 1)
    norm = BoundaryNorm(levels, cmap.N)
    n34 = NINO_BOXES["Niño 3.4"]
    stats = []
    for k, y in enumerate(args.years):
        r, c = divmod(k, 2)
        ax = fig.add_axes([0.02 + c * 0.49, 0.53 - r * 0.34, 0.47, 0.25], projection=proj)
        field = (mon.sel(time=f"{y}-{month:02d}").squeeze("time") - normal)
        field = field.interp(lat=np.arange(-39.5, 40, 1.0), lon=np.arange(0.5, 360, 1.0))
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
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=np.arange(-3, 3.5, 1))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=11, length=0)
    cb.set_label("Warmer (red) or cooler (blue) than the 1991–2020 normal for that month, °C   ·   "
                 "black box: Niño 3.4", fontsize=11.5, color=COLORS["text_2"])

    cur, past = stats[-1], stats[:-1]
    rel = {y: a - b for y, a, b in stats}            # Niño 3.4 minus the tropics: NOAA's relative view
    best_past = max(past, key=lambda p: p[1])
    if cur[1] > best_past[1]:
        headline = f"At the surface, {now} is already warmer than past super El Niños at this point"
    else:
        headline = f"At the surface, {now} is keeping pace with past super El Niños"
    rel_past = ", ".join(f"{y} {rel[y]:+.1f}" for y, _, _ in past)
    add_title(fig, headline,
              f"Tropical Pacific in {calendar.month_name[month]} of each super El Niño year. The Niño 3.4 box is "
              f"{cur[1]:+.1f} °C, but the whole tropics are also {cur[2]:+.1f} °C,\nwarmer than in any past event. "
              f"Measured against the tropics, as NOAA now does, it's {rel[now]:+.1f} °C ({rel_past}), "
              f"and still growing.")
    add_source(fig, "Data: NOAAGlobalTemp v6 monthly surface temperature (NOAA NCEI), 5° grid, smoothed for "
               "display; differences from the 1991–2020 monthly normal.")
    save(fig, args.out,
         alt=f"Four maps of tropical Pacific surface temperature in {calendar.month_name[month]} of "
             + ", ".join(str(y) for y in args.years) + ". " + "; ".join(
                 f"{y}: Niño 3.4 {a:+.1f} °C, whole tropics {b:+.1f} °C" for y, a, b in stats) + ".")


if __name__ == "__main__":
    main()
