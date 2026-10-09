"""
Animation 2 — Equatorial subsurface temperature anomalies, 2026 and 1997, month by month

Depth–longitude sections of GODAS temperature anomalies (2°S–2°N, 5–205 m,
relative to 1991–2020) from January to the latest available month of the
current year, with the same months of 1997 below. The black line is the 20 °C
isotherm (the base of the warm upper layer). Frames are interpolated between
months for smooth playback.

    python anim2_subsurface.py
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import FuncFormatter

from enso_anim import AnimationFrames, interpolate_months
from enso_common import (FIG_DIR, GODAS_DIR, COLORS, add_source, add_title, apply_style, download_godas_year,
                         godas_equatorial_section, lon_label)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--compare", type=int, default=1997)
    ap.add_argument("--steps", type=int, default=6)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim2_subsurface.png"))
    args = ap.parse_args()

    import xarray as xr
    apply_style(args.theme)
    with xr.open_dataset(download_godas_year(args.year, args.refresh)) as ds:
        months = list(pd.to_datetime(ds["time"].values))
    dates = [m.strftime("%Y-%m-%d") for m in months] + [f"{args.compare}-{m.month:02d}-01" for m in months]
    depths, lons, anoms, temps = godas_equatorial_section(GODAS_DIR, dates)
    n = len(months)
    stacks = {args.year: (anoms[:n], temps[:n]), args.compare: (anoms[n:], temps[n:])}

    fig = plt.figure(figsize=(13, 8.4))
    levels = np.arange(-10.5, 11, 1.0)
    cmap = plt.get_cmap("RdBu_r", len(levels) - 1)
    norm = BoundaryNorm(levels, cmap.N)
    axes, meshes, labels, iso = {}, {}, {}, {}
    for k, y in enumerate((args.year, args.compare)):
        ax = fig.add_axes([0.08, 0.53 - k * 0.345, 0.88, 0.255])
        meshes[y] = ax.pcolormesh(lons, depths, stacks[y][0][0], cmap=cmap, norm=norm, shading="gouraud")
        ax.set_ylim(depths.max(), depths.min())
        ax.set_yticks([50, 100, 150, 200])
        ax.set_ylabel("Depth (m)")
        ax.set_facecolor(COLORS["land"])
        ax.xaxis.set_major_formatter(FuncFormatter(lon_label))
        ax.set_xticks([140, 160, 180, 200, 220, 240, 260, 280])
        cur = y == args.year
        ax.set_title(str(y), fontsize=16, fontweight="bold", loc="left", pad=6,
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        labels[y] = ax.text(0.99, 1.02, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=15,
                            fontweight="bold", color=COLORS["text"])
        for sp in ax.spines.values():
            sp.set_visible(cur)
            sp.set_edgecolor(COLORS["el_nino"])
            sp.set_linewidth(2)
        axes[y] = ax
    axes[args.year].text(0.0, 1.16, "← West (Asia)", transform=axes[args.year].transAxes, fontsize=11,
                         color=COLORS["text_2"])
    axes[args.year].text(1.0, 1.16, "East (South America) →", transform=axes[args.year].transAxes, fontsize=11,
                         color=COLORS["text_2"], ha="right")
    cax = fig.add_axes([0.28, 0.095, 0.44, 0.018])
    cb = fig.colorbar(meshes[args.year], cax=cax, orientation="horizontal", ticks=np.arange(-10, 11, 2),
                      extend="both")
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("Temperature anomaly (°C), 2°S–2°N, relative to 1991–2020 · black line: 20 °C isotherm",
                 fontsize=11, color=COLORS["text_2"])
    add_title(fig, f"Equatorial subsurface temperature anomalies, January–{months[-1]:%B}: {args.year} and "
                   f"{args.compare}",
              "Warm anomalies build below the surface and move east along the thermocline as Kelvin waves. In "
              f"{args.year} the subsurface\nwarm pool grows larger and warmer than in {args.compare} at the same "
              "point in the year.")
    add_source(fig, "Data: NCEP GODAS ocean reanalysis (NOAA), monthly; frames interpolated between months for "
               "display.")

    frames = AnimationFrames(fig)
    seqs = {y: (interpolate_months(stacks[y][0], args.steps), interpolate_months(stacks[y][1], args.steps)[0])
            for y in stacks}
    for i, pos in enumerate(seqs[args.year][0][1]):
        k = int(round(pos))
        for y in stacks:
            meshes[y].set_array(seqs[y][0][0][i].ravel())
            labels[y].set_text(f"{calendar.month_name[months[k].month]} {y}")
            if y in iso:
                iso[y].remove()
            iso[y] = axes[y].contour(lons, depths, seqs[y][1][i], levels=[20], colors="black", linewidths=1.5)
        frames.grab(700 if abs(pos - round(pos)) < 1e-9 else 90)
    frames.durations[-1] = 2500
    east = lons >= 180
    now = float(np.nanmean(stacks[args.year][0][-1][:, east]))
    then = float(np.nanmean(stacks[args.compare][0][-1][:, east]))
    frames.save(args.out,
                alt=f"Animated depth–longitude sections of equatorial Pacific temperature anomalies from January to "
                    f"{months[-1]:%B} for {args.year} and {args.compare}. In {months[-1]:%B}, the mean anomaly over "
                    f"5–205 m east of 180° was {now:+.1f} °C in {args.year} and {then:+.1f} °C in {args.compare}.")


if __name__ == "__main__":
    main()
