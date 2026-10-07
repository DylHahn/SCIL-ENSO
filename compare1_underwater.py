"""
Compare 1 — "Underwater, this El Niño is in a league of its own"

The same month in each of the big El Niños (default: the latest month of GODAS
data for this year), as depth-by-longitude slices along the equator. Colours are
temperature differences from the 1991–2020 normal; the line is the 20 °C
isotherm. Each panel's headline number is the average extra warmth in the top
~200 m of the central and eastern Pacific (180°–80°W): the heat that feeds the
surface.

GODAS is the same ocean reanalysis iCHARM hosts.

    python compare1_underwater.py
    python compare1_underwater.py --month 7 --years 1982 1997 2015 2026
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from enso_common import (FIG_DIR, GODAS_DIR, GODAS_RAW_DIR, COLORS, add_source, add_title, apply_style,
                         download_godas_year, godas_equatorial_section, lon_label, save)
from matplotlib.ticker import FuncFormatter

EAST = (180, 280)   # longitudes for the headline number


def latest_month(year):
    import xarray as xr
    p = GODAS_RAW_DIR / f"pottmp.{year}.nc"
    with xr.open_dataset(p) as ds:
        return int(pd.Timestamp(ds["time"].values[-1]).month)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, nargs="+", default=[1982, 1997, 2015, 2026],
                    help="El Niño years to compare (the year the event grew); the last one is highlighted")
    ap.add_argument("--month", type=int, help="calendar month to compare (default: latest available)")
    ap.add_argument("--vmax", type=float, default=10)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true", help="re-download this year's GODAS file")
    ap.add_argument("--out", default=str(FIG_DIR / "compare" / "compare1_underwater.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    now = args.years[-1]
    download_godas_year(now, args.refresh)
    month = args.month or latest_month(now)
    dates = [f"{y}-{month:02d}-01" for y in args.years]
    depths, lons, anoms, temps = godas_equatorial_section(GODAS_DIR, dates)
    east = (lons >= EAST[0]) & (lons <= EAST[1])
    heat = [float(np.nanmean(a[:, east])) for a in anoms]

    n = len(args.years)
    h = 2.25 * n + 3.2
    fig, axes = plt.subplots(n, 1, figsize=(13, h), sharex=True)
    fig.subplots_adjust(top=1 - 1.55 / h, bottom=1.45 / h, left=0.08, right=0.85, hspace=0.30)

    step = 1.0
    levels = np.arange(-args.vmax - step / 2, args.vmax + step, step)
    cmap = plt.get_cmap("RdBu_r", len(levels) - 1)
    norm = BoundaryNorm(levels, cmap.N)
    for ax, y, a, t, q in zip(axes, args.years, anoms, temps, heat):
        cf = ax.contourf(lons, depths, a, levels=levels, cmap=cmap, norm=norm, extend="both")
        ax.contour(lons, depths, t, levels=[20], colors="black", linewidths=1.5)
        ax.set_ylim(depths.max(), depths.min())
        ax.set_yticks([50, 100, 150, 200])
        ax.set_ylabel("Depth (m)", fontsize=11)
        ax.set_facecolor(COLORS["land"])
        cur = y == now
        ax.text(0.01, 0.92, f"{calendar.month_name[month]} {y}", transform=ax.transAxes, fontsize=14,
                fontweight="bold", color="#111111", va="top",
                bbox=dict(facecolor="white", edgecolor=COLORS["el_nino"] if cur else "none",
                          linewidth=2, alpha=0.9, pad=3))
        # headline number to the right of each slice
        ax.text(1.015, 0.5, f"{q:+.1f} °C", transform=ax.transAxes, va="center", fontsize=22,
                fontweight="bold", color=COLORS["el_nino"] if cur else COLORS["text_2"])
        for s in ("left", "bottom"):
            ax.spines[s].set_visible(False)
    axes[0].text(1.015, 1.03, "Extra warmth,\ntop 200 m,\n180°–80°W", transform=axes[0].transAxes,
                 fontsize=10.5, color=COLORS["text_2"], va="bottom")
    axes[-1].xaxis.set_major_formatter(FuncFormatter(lon_label))
    axes[-1].set_xticks([140, 160, 180, 200, 220, 240, 260, 280])
    axes[0].text(0.0, 1.06, "← West (Asia)", transform=axes[0].transAxes, fontsize=11, color=COLORS["text_2"])
    axes[0].text(1.0, 1.06, "East (South America) →", transform=axes[0].transAxes, fontsize=11,
                 color=COLORS["text_2"], ha="right")

    cax = fig.add_axes([0.3, 0.72 / h, 0.4, 0.13 / h])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=np.arange(-args.vmax, args.vmax + 1, 2))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("Warmer (red) or cooler (blue) than normal, °C   ·   black line: 20 °C, the bottom of the "
                 "warm layer", fontsize=11, color=COLORS["text_2"])

    past = max(heat[:-1])
    ratio = heat[-1] / past if past > 0 else np.nan
    add_title(fig, f"Underwater, {now}'s El Niño carries far more heat than past giants did",
              f"Slices of the top 200 m of the Pacific along the equator, each in {calendar.month_name[month]} of "
              f"a super El Niño year. This year's warm\nlayer holds about {ratio:.1f} times the extra warmth of the "
              f"biggest past one at the same point in the year, and it keeps feeding the surface for months.")
    add_source(fig, "Data: NCEP GODAS ocean reanalysis (NOAA), 2°S–2°N average; differences from the 1991–2020 "
               "monthly normal.")
    save(fig, args.out,
         alt=f"Depth-by-longitude slices of the equatorial Pacific in {calendar.month_name[month]} of "
             + ", ".join(str(y) for y in args.years) + ". Average extra warmth in the top 200 m from 180° to "
             "80°W: " + "; ".join(f"{y}: {q:+.1f} °C" for y, q in zip(args.years, heat)) + ".")


if __name__ == "__main__":
    main()
