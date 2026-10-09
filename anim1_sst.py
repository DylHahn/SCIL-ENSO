"""
Animation 1 — Tropical Pacific sea surface temperature, month by month: 2026, 1997 and normal

Monthly mean sea surface temperature from NOAA OISST v2.1 (0.25°) from January to
the latest available month of the current year, for the current year (top), the
same months of 1997 (middle) and the 1991–2020 normal for each month (bottom),
in the classic rainbow colour scale used for El Niño maps (here "turbo", a
perceptually improved rainbow). The black line marks the 28 °C isotherm, the
edge of the warm pool that drives tropical rainfall. Frames are interpolated
between months for smooth playback.

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
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style
from enso_marine import PACIFIC, pacific_monthly, pacific_normals


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--compare", type=int, default=1997)
    ap.add_argument("--steps", type=int, default=4, help="interpolated frames per month")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim1_sst.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    # months of the current year that exist in the file (probe up to December)
    probe = [pd.Timestamp(args.year, m, 1) for m in range(1, 13)]
    cur = pacific_monthly(probe, args.refresh)
    months = list(pd.to_datetime(cur["time"].values))
    comp = pacific_monthly([pd.Timestamp(args.compare, m.month, 1) for m in months])
    normals = pacific_normals()
    rows = [(str(args.year), cur.values), (str(args.compare), comp.values),
            ("Normal (1991–2020)", normals.sel(month=[m.month for m in months]).values)]
    lon, lat = cur["lon"].values, cur["lat"].values

    from scipy.ndimage import gaussian_filter

    def smooth(a):
        """Lightly smoothed copy used only for the 28 °C contour (the colours show the full-resolution data)."""
        filled = np.where(np.isfinite(a), a, np.nanmean(a))
        return gaussian_filter(filled, 2.5)

    fig = plt.figure(figsize=(13, 12.0))
    proj = ccrs.PlateCarree(central_longitude=200)
    pc = ccrs.PlateCarree()
    levels = np.arange(18, 32.01, 0.5)
    cmap = plt.get_cmap("turbo", len(levels) + 1)          # +2 for the below/above extensions
    norm = BoundaryNorm(levels, cmap.N, extend="both")
    meshes, labels, axes = [], [], []
    for k, (name, stack) in enumerate(rows):
        ax = fig.add_axes([0.06, 0.642 - k * 0.254, 0.90, 0.2167], projection=proj)
        ax.set_extent([PACIFIC["lon"][0], PACIFIC["lon"][1], -20, 20], crs=pc)
        meshes.append(ax.pcolormesh(lon, lat, stack[0], cmap=cmap, norm=norm, transform=pc, shading="nearest",
                                    rasterized=True, zorder=1))
        ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="black", edgecolor="none", zorder=2)
        ax.plot([100, 300], [0, 0], transform=pc, color="black", lw=0.8, zorder=3)
        is_cur = k == 0
        ax.set_title(name, fontsize=15, fontweight="bold", loc="left", pad=6,
                     color=COLORS["el_nino"] if is_cur else COLORS["text"])
        labels.append(ax.text(0.99, 1.03, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=14,
                              fontweight="bold", color=COLORS["text"]))
        gl = ax.gridlines(crs=pc, draw_labels=dict(left="y", bottom="x" if k == len(rows) - 1 else False),
                          xlocs=[120, 140, 160, 180, -160, -140, -120, -100, -80], ylocs=[-20, -10, 0, 10, 20],
                          linewidth=0, color="none")
        gl.xlabel_style = gl.ylabel_style = dict(size=10, color=COLORS["text_2"])
        ax.spines["geo"].set_edgecolor(COLORS["el_nino"] if is_cur else COLORS["grid"])
        ax.spines["geo"].set_linewidth(2 if is_cur else 0.8)
        axes.append(ax)
    cax = fig.add_axes([0.25, 0.068, 0.5, 0.014])
    cb = fig.colorbar(meshes[0], cax=cax, orientation="horizontal", ticks=np.arange(18, 33, 2))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("Monthly mean sea surface temperature (°C) · black line: 28 °C, the edge of the warm pool",
                 fontsize=11, color=COLORS["text_2"])
    add_title(fig, f"Tropical Pacific sea surface temperature, January–{months[-1]:%B}: {args.year}, "
                   f"{args.compare} and normal",
              "Normally the warmest water (red) is pooled in the western Pacific and cool water rises along the "
              "equator off South America.\nDuring El Niño the warm pool spreads east and the cool tongue weakens; "
              "compare each year with the normal panel below.")
    add_source(fig, "Data: NOAA OISST v2.1 monthly mean (0.25°), via NOAA PSL; normal = 1991–2020 monthly mean. "
               "Frames are interpolated between months for display.")

    frames = AnimationFrames(fig, dpi=115)
    seqs = [interpolate_months(stack, args.steps) for _, stack in rows]
    iso = [None] * len(rows)
    for i, pos in enumerate(seqs[0][1]):
        k = int(round(pos))
        for r, (name, _) in enumerate(rows):
            field = seqs[r][0][i]
            meshes[r].set_array(field.ravel())
            year = name if r < 2 else ""
            labels[r].set_text(f"{calendar.month_name[months[k].month]} {year}".strip())
            if iso[r] is not None:
                iso[r].remove()
            iso[r] = axes[r].contour(lon, lat, smooth(field), levels=[28], colors="black", linewidths=1.0,
                                     transform=pc, zorder=2.5)
        frames.grab(800 if abs(pos - round(pos)) < 1e-9 else 90)
    frames.durations[-1] = 3000
    box = lambda a: float(np.nanmean(a[(lat >= -5) & (lat <= 5)][:, (lon >= 190) & (lon <= 240)]))
    frames.save(args.out, quality=86,
                alt=f"Animated maps of tropical Pacific sea surface temperature from January to {months[-1]:%B} for "
                    f"{args.year}, {args.compare} and the 1991–2020 normal. In {months[-1]:%B}, the Niño 3.4 region "
                    f"averaged {box(rows[0][1][-1]):.1f} °C in {args.year}, {box(rows[1][1][-1]):.1f} °C in "
                    f"{args.compare} and {box(rows[2][1][-1]):.1f} °C normally.")


if __name__ == "__main__":
    main()
