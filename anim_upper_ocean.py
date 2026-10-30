"""
Animation 2 — Equatorial upper-ocean temperature, month by month: 2026, the past very strong
El Niños (2015, 1997, 1982), 2023 and normal

Depth–longitude sections of GODAS ocean temperature (2°S–2°N, 5–205 m) from
January to the latest available month of the current year, for the current year,
the same months of each past very strong El Niño and the 1991–2020 normal, in the same rainbow scale as
animation 1. The black line is the 20 °C
isotherm (the base of the warm upper layer). Frames are interpolated between
months for smooth playback.

    python anim_upper_ocean.py
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import FuncFormatter

from enso_anim import (EVENT_MONTHS, AnimationFrames, event_months, event_name, hold_last, interpolate_months,
                       month_label)
from enso_common import (FIG_DIR, GODAS_DIR, COLORS, add_source, add_title, apply_style, download_godas_year,
                         godas_equatorial_section, join_and, lon_label)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--compare", type=int, nargs="+", default=[2023, 2015, 1997, 1982],
                    help="past onset years to show (GODAS begins in 1980)")
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_upper_ocean.png"))
    args = ap.parse_args()

    import xarray as xr
    apply_style(args.theme)
    with xr.open_dataset(download_godas_year(args.year, args.refresh)) as ds:
        months = list(pd.to_datetime(ds["time"].values))           # months of the current event with data
    n = len(months)
    # each El Niño from January of its first year to December of the next
    dates = [m.strftime("%Y-%m-%d") for m in months] + [m.strftime("%Y-%m-%d") for y in args.compare
                                                          for m in event_months(y)]
    depths, lons, anoms, temps = godas_equatorial_section(GODAS_DIR, dates)
    from scipy.ndimage import zoom

    def fine(a, z=4):
        """Resample a (depth, lon) section 4× in each direction (linear) for crisp display of the 1° grid."""
        return zoom(np.where(np.isfinite(a), a, np.nanmean(a)), z, order=1)

    lons_f = np.linspace(lons.min(), lons.max(), len(lons) * 4)
    depths_f = np.linspace(depths.min(), depths.max(), len(depths) * 4)
    years = [args.year] + list(args.compare)
    names = [event_name(y) for y in years]
    parts = [(temps[:n], anoms[:n])] + [(temps[n + i * EVENT_MONTHS:n + (i + 1) * EVENT_MONTHS],
                                          anoms[n + i * EVENT_MONTHS:n + (i + 1) * EVENT_MONTHS])
                                         for i in range(len(args.compare))]
    normal = parts[1][0] - parts[1][1]                  # 1991–2020 monthly normal = temperature − anomaly (24 months)
    rows, row_anoms, haves = [], [], []
    for nm, (t, a) in zip(names, parts):
        tp, have = hold_last(t)
        rows.append((nm, tp)); row_anoms.append(hold_last(a)[0]); haves.append(have)
    rows.append(("Normal (1991–2020)", normal)); row_anoms.append(np.zeros_like(normal)); haves.append(EVENT_MONTHS)
    latest = months[-1]
    N = EVENT_MONTHS
    east = (lons >= 180) & (lons <= 280)

    # fixed sizes in inches so the layout works for any number of rows
    top_in, row_in, sec_in, bottom_in = 1.95, 2.5, 2.0, 1.4
    H = top_in + row_in * len(rows) + bottom_in
    fig = plt.figure(figsize=(13, H))
    levels = np.arange(12, 31.01, 0.5)
    cmap = plt.get_cmap("turbo", len(levels) + 1)
    norm = BoundaryNorm(levels, cmap.N, extend="both")
    axes, meshes, labels, iso = [], [], [], [None] * len(rows)
    for k, (name, stack) in enumerate(rows):
        ax = fig.add_axes([0.08, 1 - (top_in + row_in * k + sec_in) / H, 0.88, sec_in / H])
        meshes.append(ax.pcolormesh(lons_f, depths_f, fine(stack[0]), cmap=cmap, norm=norm, shading="nearest",
                                    rasterized=True))
        ax.set_ylim(depths.max(), depths.min())
        ax.set_yticks([50, 100, 150, 200])
        ax.set_ylabel("Depth (m)")
        ax.set_facecolor("black")
        ax.xaxis.set_major_formatter(FuncFormatter(lon_label))
        ax.set_xticks([140, 160, 180, 200, 220, 240, 260, 280])
        if k < len(rows) - 1:
            ax.set_xticklabels([])
        cur = k == 0
        ax.set_title(name, fontsize=15, fontweight="bold", loc="left", pad=6,
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        labels.append(ax.text(0.99, 1.03, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=14,
                              fontweight="bold", color=COLORS["text"]))
        for sp in ax.spines.values():
            sp.set_visible(cur)
            sp.set_edgecolor(COLORS["el_nino"])
            sp.set_linewidth(2)
        axes.append(ax)
    axes[0].text(0.0, 1.25, "← West (Asia)", transform=axes[0].transAxes, fontsize=11, color=COLORS["text_2"])
    axes[0].text(1.0, 1.25, "East (South America) →", transform=axes[0].transAxes, fontsize=11,
                 color=COLORS["text_2"], ha="right")
    cax = fig.add_axes([0.28, 0.8 / H, 0.44, 0.16 / H])
    cb = fig.colorbar(meshes[0], cax=cax, orientation="horizontal", ticks=np.arange(12, 31, 2))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("Ocean temperature (°C), 2°S–2°N · black line: 20 °C isotherm (base of the warm layer)",
                 fontsize=11, color=COLORS["text_2"])
    add_title(fig, f"Upper-ocean temperature along the equator: {event_name(args.year)} and past strong events",
              "Monthly, January of each event's first year to December of the next. Right of each panel: upper-200 m "
              "anomaly, 180°–80°W.")
    add_source(fig, "Data: NCEP GODAS ocean reanalysis (NOAA), monthly, 1° × 10 m, resampled for display; normal = "
               "1991–2020. Frames are interpolated between months.")

    frames = AnimationFrames(fig, dpi=115)
    seqs = [interpolate_months(stack, args.steps) for _, stack in rows]
    for i, pos in enumerate(seqs[0][1]):
        k = int(round(pos))
        for r, (name, _) in enumerate(rows):
            field = seqs[r][0][i]
            meshes[r].set_array(fine(field).ravel())
            month = (month_label(years[r], k, haves[r]) if r < len(rows) - 1 else calendar.month_name[k % 12 + 1])
            if r < len(rows) - 1:
                a = (1 - (pos - int(pos))) * row_anoms[r][int(pos)] + (pos - int(pos)) * row_anoms[r][min(int(pos) + 1, N - 1)]
                month += f"  ·  upper 200 m {float(np.nanmean(a[:, east])):+.1f} °C"
            labels[r].set_text(month)
            if iso[r] is not None:
                iso[r].remove()
            iso[r] = axes[r].contour(lons, depths, field, levels=[20], colors="black", linewidths=1.6)
        frames.grab(600 if abs(pos - round(pos)) < 1e-9 else 90)
    frames.durations[-1] = 3000
    last = [float(np.nanmean(a[n - 1][:, east])) for a in row_anoms[:-1]]
    frames.save(args.out, quality=86,
                alt=f"Animated depth–longitude sections of equatorial Pacific ocean temperature from January of each El "
                    f"Niño's first year to December of the next, for {join_and(names)} (the current event to "
                    f"{latest:%B %Y}) and the 1991–2020 normal. In {latest:%B} of the first year, the "
                    f"upper 200 m east of 180° departed from normal by "
                    + join_and(f"{v:+.1f} °C in {nm}" for nm, v in zip(names, last)) + ".")


if __name__ == "__main__":
    main()
