"""
Animation 1 — Tropical Pacific sea surface temperature, month by month: 2026, 2023, the past very
strong El Niños (2015, 1997, 1982), 2023 and normal

Monthly mean sea surface temperature from NOAA OISST v2.1 (0.25°) from January to
the latest available month of the current year, for the current year (top), the
same months of each past very strong El Niño and the 1991–2020 normal (bottom),
in the classic rainbow colour scale used for El Niño maps (here "turbo", a
perceptually improved rainbow). The black line marks the 28 °C isotherm, the
edge of the warm pool that drives tropical rainfall. Frames are interpolated
between months for smooth playback.

    python anim_sst.py
    python anim_sst.py --compare 1997 2015
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from enso_anim import (EVENT_MONTHS, AnimationFrames, event_months, event_name, hold_last, interpolate_months,
                       month_label)
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, join_and
from enso_marine import PACIFIC, pacific_monthly, pacific_normals


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--compare", type=int, nargs="+", default=[2023, 2015, 1997, 1982],
                    help="past onset years to show (OISST begins in September 1981)")
    ap.add_argument("--steps", type=int, default=2, help="interpolated frames per month")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_sst.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    # each El Niño from January of its first year to December of the next; the current event holds
    # at its latest month
    cur = pacific_monthly(event_months(args.year), args.refresh)
    lon, lat = cur["lon"].values, cur["lat"].values
    rows = [(event_name(args.year), *hold_last(cur.values), args.year)]
    for y in args.compare:
        comp = pacific_monthly(event_months(y))
        rows.append((event_name(y), *hold_last(comp.values), y))
    normals = pacific_normals()
    rows.append(("Normal (1991–2020)", normals.sel(month=[m.month for m in event_months(2000)]).values,
                 EVENT_MONTHS, None))
    have_now = rows[0][2]
    latest = event_months(args.year)[have_now - 1]

    from scipy.ndimage import gaussian_filter

    def smooth(a):
        """Lightly smoothed copy used only for the 28 °C contour (the colours show the full-resolution data)."""
        filled = np.where(np.isfinite(a), a, np.nanmean(a))
        return gaussian_filter(filled, 2.5)

    # fixed sizes in inches so the layout works for any number of rows
    top_in, row_in, map_in, bottom_in = 1.75, 3.05, 2.6, 1.45
    H = top_in + row_in * len(rows) + bottom_in
    fig = plt.figure(figsize=(13, H))
    proj = ccrs.PlateCarree(central_longitude=200)
    pc = ccrs.PlateCarree()
    levels = np.arange(18, 32.01, 0.5)
    cmap = plt.get_cmap("turbo", len(levels) + 1)          # +2 for the below/above extensions
    norm = BoundaryNorm(levels, cmap.N, extend="both")
    meshes, labels, axes = [], [], []
    for k, (name, stack, _, _) in enumerate(rows):
        ax = fig.add_axes([0.06, 1 - (top_in + row_in * k + map_in) / H, 0.90, map_in / H], projection=proj)
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
    cax = fig.add_axes([0.25, 0.82 / H, 0.5, 0.17 / H])
    cb = fig.colorbar(meshes[0], cax=cax, orientation="horizontal", ticks=np.arange(18, 33, 2))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("Monthly mean sea surface temperature (°C) · black line: 28 °C, the edge of the warm pool",
                 fontsize=11, color=COLORS["text_2"])
    add_title(fig, f"Sea surface temperature: {event_name(args.year)} compared "
                   f"with {join_and(event_name(y) for y in args.compare)}",
              "Each El Niño runs from January of its first year to December of the next; the "
              f"{event_name(args.year)} panel holds at the latest month.\nDuring El Niño the warm pool (red) spreads "
              "east and the cool tongue off South America weakens. The value at right of each panel is the Niño 3.4 "
              "average.")
    add_source(fig, "Data: NOAA OISST v2.1 monthly mean (0.25°), via NOAA PSL; normal = 1991–2020 monthly mean. "
               "Frames are interpolated between months for display.")

    box = lambda a: float(np.nanmean(a[(lat >= -5) & (lat <= 5)][:, (lon >= 190) & (lon <= 240)]))
    frames = AnimationFrames(fig, dpi=110)
    seqs = [interpolate_months(stack, args.steps) for _, stack, _, _ in rows]
    iso = [None] * len(rows)
    for i, pos in enumerate(seqs[0][1]):
        k = int(round(pos))
        for r, (name, _, have, year) in enumerate(rows):
            field = seqs[r][0][i]
            meshes[r].set_array(field.ravel())
            month = month_label(year, k, have) if year else calendar.month_name[k % 12 + 1]
            labels[r].set_text(f"{month}  ·  Niño 3.4 {box(field):.1f} °C")
            if iso[r] is not None:
                iso[r].remove()
            iso[r] = axes[r].contour(lon, lat, smooth(field), levels=[28], colors="black", linewidths=1.0,
                                     transform=pc, zorder=2.5)
        frames.grab(600 if abs(pos - round(pos)) < 1e-9 else 90)
    frames.durations[-1] = 3000
    frames.save(args.out, quality=86,
                alt=f"Animated maps of tropical Pacific sea surface temperature from January of each El Niño's first "
                    f"year to December of the next, for {event_name(args.year)} (to {latest:%B %Y}), "
                    f"{join_and(event_name(y) for y in args.compare)} and the 1991–2020 normal. In {latest:%B} of the "
                    f"first year, the Niño 3.4 region averaged "
                    + ", ".join(f"{box(st[have_now - 1]):.1f} °C in {nm}" for nm, st, _, _ in rows[:-1])
                    + f", and {box(rows[-1][1][have_now - 1]):.1f} °C normally.")


if __name__ == "__main__":
    main()
