"""
Figure 6 — "Watching El Niño travel beneath the surface"

Depth-vs-longitude slices along the equator (2°S–2°N average) for a sequence
of months, built from GODAS: your depth files (data/godas/) plus NOAA's yearly
files for months after them (data/godas_raw/, downloaded automatically).
By default: the latest four even months of the current El Niño year.
Colors are temperature anomalies; the black line is the 20 °C isotherm
(the bottom of the warm layer). A warm blob sliding east over the months is a
Kelvin wave carrying heat toward South America.

    python fig6_equatorial_cross_section.py                     # this year, latest data
    python fig6_equatorial_cross_section.py --dates 1997-01 1997-03 1997-05 1997-07
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import FuncFormatter

from enso_common import (temp_cmap, FIG_DIR, GODAS_DIR, GODAS_RAW_DIR, COLORS, add_source, add_title, apply_style,
                         download_godas_year, godas_equatorial_section, lon_label, save)


def default_dates(year):
    """The latest available month of `year` and the three before it, two months apart."""
    import xarray as xr
    with xr.open_dataset(download_godas_year(year)) as ds:
        last = pd.Timestamp(ds["time"].values[-1])
    return [(last - pd.DateOffset(months=2 * k)).strftime("%Y-%m-01") for k in (3, 2, 1, 0)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=str(GODAS_DIR))
    ap.add_argument("--dates", nargs="+", help="months to show (default: latest 4 of --year)")
    ap.add_argument("--year", type=int, default=2026, help="El Niño year for the default dates")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--lat-band", nargs=2, type=float, default=[-2, 2])
    ap.add_argument("--vmax", type=float, default=10, help="color scale limit (°C)")
    ap.add_argument("--no-isotherm", action="store_true", help="hide the 20 °C line")
    ap.add_argument("--out", default=str(FIG_DIR / "fig6_equatorial_cross_section.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    args.dates = args.dates or default_dates(args.year)
    depths, lons, anoms, temps = godas_equatorial_section(args.data_dir, args.dates,
                                                          lat_band=tuple(args.lat_band))

    n = len(args.dates)
    fig, axes = plt.subplots(n, 1, figsize=(12, 2.35 * n + 2.6), sharex=True)
    axes = np.atleast_1d(axes)
    fig.subplots_adjust(top=1 - 1.45 / (2.35 * n + 2.6), bottom=0.6 / (2.35 * n + 2.6) + 0.05,
                        left=0.09, right=0.86, hspace=0.32)

    step = 1.0
    levels = np.arange(12, 31.01, 0.5)                   # actual temperature, rainbow scale
    cmap, norm = temp_cmap(levels)

    for ax, date, a, t in zip(axes, args.dates, anoms, temps):
        cf = ax.contourf(lons, depths, t, levels=levels, cmap=cmap, norm=norm, extend="both")
        if not args.no_isotherm:
            cs = ax.contour(lons, depths, t, levels=[20], colors="black", linewidths=1.6)
        ax.set_ylim(depths.max(), depths.min())
        ax.set_yticks([t for t in (50, 100, 150, 200) if t <= depths.max()])
        ax.set_ylabel("Depth (m)")
        ax.set_facecolor(COLORS["land"])  # land / missing shows as gray
        ax.text(0.01, 0.94, pd.Timestamp(date).strftime("%B %Y"), transform=ax.transAxes,
                fontsize=14, fontweight="bold", color=COLORS["text"], va="top",
                bbox=dict(facecolor=COLORS["surface"], edgecolor="none", alpha=0.85, pad=3))
        for s in ("left", "bottom"):
            ax.spines[s].set_visible(False)

    axes[-1].xaxis.set_major_formatter(FuncFormatter(lon_label))
    axes[-1].set_xticks([140, 160, 180, 200, 220, 240, 260, 280])
    axes[0].text(0.0, 1.06, "← West (Asia)", transform=axes[0].transAxes, fontsize=11,
                 color=COLORS["text_2"])
    axes[0].text(1.0, 1.06, "East (South America) →", transform=axes[0].transAxes, fontsize=11,
                 color=COLORS["text_2"], ha="right")

    cax = fig.add_axes([0.88, 0.25, 0.018, 0.5])
    cb = fig.colorbar(cf, cax=cax, ticks=np.arange(12, 32, 2))
    cb.outline.set_visible(False)
    cb.set_label("Ocean temperature (°C)", fontsize=12)
    if not args.no_isotherm:
        fig.text(0.875, 0.20, "— 20 °C line:\n   bottom of the\n   warm layer", fontsize=11,
                 va="top", color=COLORS["text"])

    years = {pd.Timestamp(d).year for d in args.dates}
    span = f"{pd.Timestamp(args.dates[0]):%B}–{pd.Timestamp(args.dates[-1]):%B %Y}"
    add_title(fig, f"Equatorial upper-ocean temperature, {span}",
              "Depth–longitude sections, 2°S–2°N, at two-month intervals. As El Niño develops, the warm upper layer "
              "deepens in the east\nand the 20 °C line (the base of the warm layer) flattens, carried by downwelling "
              "Kelvin waves.")
    lat_txt = f"{abs(args.lat_band[0]):g}°S–{abs(args.lat_band[1]):g}°N"
    add_source(fig, f"Data: NCEP GODAS ocean reanalysis, {lat_txt} average; monthly mean temperature."
               "")
    east = (lons >= 180) & (lons <= 280)
    save(fig, args.out,
         alt="Depth-by-longitude slices of the upper 200 m of the equatorial Pacific for "
             + ", ".join(pd.Timestamp(d).strftime("%B %Y") for d in args.dates)
             + ". Average extra warmth, top 200 m from 180° to 80°W: "
             + "; ".join(f"{pd.Timestamp(d):%b %Y} {np.nanmean(a[:, east]):+.1f} °C"
                         for d, a in zip(args.dates, anoms)) + ".")


if __name__ == "__main__":
    main()
