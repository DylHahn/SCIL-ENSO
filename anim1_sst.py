"""
Animation 1 — Tropical Pacific sea surface temperature anomalies, 2026 and 1997, month by month

Monthly ERSST v5 anomalies (relative to 1991–2020) from January to the latest
available month of the current year, shown for the current year (top) and the
same months of 1997 (bottom). Frames are linearly interpolated between months
for smooth playback; the month label shows which month (or transition) is shown.

Writes an animated WebP and a PNG of the final frame.

    python anim1_sst.py
    python anim1_sst.py --compare 2015
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from enso_anim import AnimationFrames, interpolate_months
from enso_common import FIG_DIR, COLORS, NINO_BOXES, add_source, add_title, apply_style
from enso_stats import load_gridded

LAT, LON = (-25, 25), (110, 290)


def anomalies(sst):
    sub = sst.sel(lat=slice(LAT[0] - 2, LAT[1] + 2), lon=slice(LON[0] - 2, LON[1] + 2))
    clim = sub.sel(time=slice("1991", "2020")).groupby("time.month").mean("time")
    anom = sub.groupby("time.month") - clim
    # fill coastal/land cells from their ocean neighbours so interpolation leaves no gaps (land is drawn on top)
    anom = anom.ffill("lon").bfill("lon").ffill("lat").bfill("lat")
    return anom.interp(lat=np.arange(LAT[0], LAT[1] + 0.5, 1.0), lon=np.arange(LON[0], LON[1] + 0.5, 1.0))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--compare", type=int, default=1997)
    ap.add_argument("--steps", type=int, default=6, help="interpolated frames per month")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim1_sst.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    anom = anomalies(load_gridded("sst", args.refresh))
    times = pd.to_datetime(anom["time"].values)
    months = [t for t in times if t.year == args.year]
    n = len(months)
    stacks = {y: np.array([anom.sel(time=f"{y}-{m.month:02d}-01").values for m in months])
              for y in (args.year, args.compare)}

    fig = plt.figure(figsize=(13, 8.6))
    proj = ccrs.PlateCarree(central_longitude=200)
    pc = ccrs.PlateCarree()
    levels = np.arange(-4.5, 4.75, 0.5)
    cmap = plt.get_cmap("RdBu_r", len(levels) - 1)
    norm = BoundaryNorm(levels, cmap.N)
    lon, lat = anom["lon"].values, anom["lat"].values
    meshes, labels = {}, {}
    for k, y in enumerate((args.year, args.compare)):
        ax = fig.add_axes([0.03, 0.50 - k * 0.355, 0.94, 0.30], projection=proj)
        ax.set_extent([LON[0], LON[1], LAT[0], LAT[1]], crs=pc)
        meshes[y] = ax.pcolormesh(lon, lat, stacks[y][0], cmap=cmap, norm=norm, transform=pc, shading="gouraud",
                                  zorder=1)
        ax.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none", zorder=2)
        ax.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5, zorder=3)
        b = NINO_BOXES["Niño 3.4"]
        ax.plot([b["lon"][0], b["lon"][1], b["lon"][1], b["lon"][0], b["lon"][0]],
                [b["lat"][0], b["lat"][0], b["lat"][1], b["lat"][1], b["lat"][0]], transform=pc,
                color="black", lw=1.2, zorder=4)
        cur = y == args.year
        ax.set_title(str(y), fontsize=16, fontweight="bold", loc="left", pad=6,
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        labels[y] = ax.text(0.99, 1.02, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=15,
                            fontweight="bold", color=COLORS["text"])
        ax.spines["geo"].set_edgecolor(COLORS["el_nino"] if cur else COLORS["grid"])
        ax.spines["geo"].set_linewidth(2 if cur else 0.8)
    cax = fig.add_axes([0.28, 0.10, 0.44, 0.018])
    cb = fig.colorbar(meshes[args.year], cax=cax, orientation="horizontal", ticks=np.arange(-4, 4.5, 1),
                      extend="both")
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("Sea surface temperature anomaly (°C) relative to 1991–2020 · black box: Niño 3.4", fontsize=11,
                 color=COLORS["text_2"])
    add_title(fig, f"Tropical Pacific sea surface temperature anomalies, January–{months[-1]:%B}: "
                   f"{args.year} and {args.compare}",
              f"Monthly anomalies from NOAA ERSST v5. In both years warm water spreads east along the equator; in "
              f"{args.year} the warming\nis broader and stronger, and the wider tropical ocean is warmer than in "
              f"{args.compare}.")
    add_source(fig, "Data: NOAA ERSST v5 monthly (2°, shown at 1°); anomalies relative to 1991–2020. Frames are "
               "interpolated between months for display.")

    frames = AnimationFrames(fig)
    seqs = {y: interpolate_months(stacks[y], args.steps) for y in stacks}
    for i, pos in enumerate(seqs[args.year][1]):
        k = int(round(pos))
        for y in stacks:
            meshes[y].set_array(seqs[y][0][i].ravel())
            labels[y].set_text(f"{calendar.month_name[months[k].month]} {y}")
        exact = abs(pos - round(pos)) < 1e-9
        frames.grab(700 if exact else 90)                       # pause briefly on each actual month
    frames.durations[-1] = 2500                                 # hold the last month before looping
    east = anom["lon"].values >= 190
    nino_now = float(anom.sel(time=months[-1], lat=slice(-5, 5), lon=slice(190, 240)).mean())
    nino_then = float(anom.sel(time=f"{args.compare}-{months[-1].month:02d}-01", lat=slice(-5, 5),
                               lon=slice(190, 240)).mean())
    frames.save(args.out,
                alt=f"Animated maps of tropical Pacific sea surface temperature anomalies, January to "
                    f"{months[-1]:%B}, for {args.year} and {args.compare}. In {months[-1]:%B} the Niño 3.4 region "
                    f"was {nino_now:+.1f} °C in {args.year} and {nino_then:+.1f} °C in {args.compare}.")


if __name__ == "__main__":
    main()
