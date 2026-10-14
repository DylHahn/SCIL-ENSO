"""
Animation 2 — Equatorial upper-ocean temperature, month by month: 2026, the past very strong
El Niños (2015, 1997, 1982) and normal

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

from enso_anim import AnimationFrames, interpolate_months
from enso_common import (FIG_DIR, GODAS_DIR, COLORS, add_source, add_title, apply_style, download_godas_year,
                         godas_equatorial_section, join_and, lon_label)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--compare", type=int, nargs="+", default=[2015, 1997, 1982],
                    help="past onset years to show (GODAS begins in 1980)")
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_upper_ocean.png"))
    args = ap.parse_args()

    import xarray as xr
    apply_style(args.theme)
    with xr.open_dataset(download_godas_year(args.year, args.refresh)) as ds:
        months = list(pd.to_datetime(ds["time"].values))
    dates = [m.strftime("%Y-%m-%d") for m in months] + [f"{y}-{m.month:02d}-01" for y in args.compare
                                                          for m in months]
    depths, lons, anoms, temps = godas_equatorial_section(GODAS_DIR, dates)
    n = len(months)
    from scipy.ndimage import zoom

    def fine(a, z=4):
        """Resample a (depth, lon) section 4× in each direction (linear) for crisp display of the 1° grid."""
        return zoom(np.where(np.isfinite(a), a, np.nanmean(a)), z, order=1)

    lons_f = np.linspace(lons.min(), lons.max(), len(lons) * 4)
    depths_f = np.linspace(depths.min(), depths.max(), len(depths) * 4)
    normal = temps[:n] - anoms[:n]                      # 1991–2020 monthly normal = temperature − anomaly
    names = [str(args.year)] + [str(y) for y in args.compare]
    rows = ([(nm, temps[i * n:(i + 1) * n]) for i, nm in enumerate(names)] + [("Normal (1991–2020)", normal)])
    row_anoms = [anoms[i * n:(i + 1) * n] for i in range(len(names))] + [np.zeros_like(normal)]
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
    add_title(fig, f"Equatorial Pacific upper-ocean temperature, Jan–{months[-1]:%b}: {args.year} compared "
                   f"with {join_and(str(y) for y in args.compare)}",
              "Normally the warm layer is thick in the west and thin in the east, where cold water lies close to the "
              "surface. During El Niño\nthe warm layer deepens in the east and the 20 °C line flattens. The value at right of each panel is the "
              "upper-200 m anomaly, 180°–80°W.")
    add_source(fig, "Data: NCEP GODAS ocean reanalysis (NOAA), monthly, 1° × 10 m, resampled for display; normal = "
               "1991–2020. Frames are interpolated between months.")

    frames = AnimationFrames(fig, dpi=115)
    seqs = [interpolate_months(stack, args.steps) for _, stack in rows]
    for i, pos in enumerate(seqs[0][1]):
        k = int(round(pos))
        for r, (name, _) in enumerate(rows):
            field = seqs[r][0][i]
            meshes[r].set_array(fine(field).ravel())
            year = name if r < len(rows) - 1 else ""
            month = f"{calendar.month_name[months[k].month]} {year}".strip()
            if r < len(rows) - 1:
                a = (1 - (pos - int(pos))) * row_anoms[r][int(pos)] + (pos - int(pos)) * row_anoms[r][min(int(pos) + 1, n - 1)]
                month += f"  ·  upper 200 m {float(np.nanmean(a[:, east])):+.1f} °C"
            labels[r].set_text(month)
            if iso[r] is not None:
                iso[r].remove()
            iso[r] = axes[r].contour(lons, depths, field, levels=[20], colors="black", linewidths=1.6)
        frames.grab(800 if abs(pos - round(pos)) < 1e-9 else 90)
    frames.durations[-1] = 3000
    last = [float(np.nanmean(a[-1][:, east])) for a in row_anoms[:-1]]
    frames.save(args.out, quality=86,
                alt=f"Animated depth–longitude sections of equatorial Pacific ocean temperature from January to "
                    f"{months[-1]:%B} for {join_and(names)} and the 1991–2020 normal. In {months[-1]:%B}, the "
                    f"upper 200 m east of 180° departed from normal by "
                    + join_and(f"{v:+.1f} °C in {nm}" for nm, v in zip(names, last)) + ".")


if __name__ == "__main__":
    main()
