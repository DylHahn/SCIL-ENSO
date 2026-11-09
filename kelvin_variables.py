"""
Kelvin waves 5 — The 2026 Kelvin waves seen in four variables

From October of the year before the current El Niño to the latest day, along the equator with time running left
to right: the Kelvin-wave signal (anomaly minus its 91-day running mean) in satellite sea level, in the depth of
the 20 °C isotherm, in sea surface temperature and in zonal wind, the last three from the TAO/TRITON buoys
(see enso_tao.py). The dashed lines are the Kelvin waves traced in satellite sea level (anim_kelvin.py), from
150°E to 95°W, numbered as in that figure.

    python kelvin_variables.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import FuncFormatter

from anim_kelvin import START, X0, X1, kelvin_waves
from enso_common import FIG_DIR, COLORS, add_note, add_source, add_title, apply_style, lon_label, save
from enso_tao import LONS, anomalies, infill_across, wave_signal

NOW = 2026
PANELS = [("ssh", "Satellite sea level", "cm", 12, 2), ("d20", "Warm-layer depth (20 °C isotherm), buoys", "m", 32, 4),
          ("sst", "Sea surface temperature, buoys", "°C", 1.6, 0.2), ("wind", "East–west wind, buoys", "m/s", 4.8, 0.6)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "kelvin" / "kelvin_variables.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    _, ssh, waves = kelvin_waves(args.refresh)
    waves = [w for w in waves if w[0] + (w[3] - w[0]) / 2 >= pd.Timestamp(START)]
    ssh = ssh.loc[START:]
    H = 11.2
    fig = plt.figure(figsize=(13, H))
    L, W = 0.08, 0.82
    ends = []
    for k, (key, name, unit, top, step) in enumerate(PANELS):
        ax = fig.add_axes([L, (0.9 + (len(PANELS) - 1 - k) * 2.32) / H, W, 1.95 / H])
        if key == "ssh":
            lons, f = np.array(ssh.columns, float), ssh
        else:
            f = infill_across(wave_signal(anomalies(key, args.refresh))).loc[START:]
            lons = np.array(LONS, float)
        f = f.dropna(how="all")
        ends.append(f.index[-1])
        levels = np.arange(-top, top + step / 2, step)
        cmap = ListedColormap(plt.get_cmap("RdBu_r")(np.linspace(0.04, 0.96, len(levels) + 1)))
        cf = ax.contourf(mdates.date2num(f.index), lons, f.values.T, levels=levels, cmap=cmap,
                         norm=BoundaryNorm(levels, cmap.N, extend="both"), extend="both")
        ax.set_ylim(165, 265)
        ax.set_xlim(pd.Timestamp(START), max(ssh.index[-1], f.index[-1]))
        ax.set_facecolor(COLORS["surface_2"])
        ax.yaxis.set_major_formatter(FuncFormatter(lon_label))
        ax.set_yticks([165, 190, 220, 250, 265])
        ax.tick_params(axis="both", labelsize=10.5)
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 3, 5, 7, 9, 11]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y") if k == len(PANELS) - 1 else FuncFormatter(lambda *_: ""))
        ax.set_ylabel("Longitude\n(west → east)", fontsize=10.5)
        ax.set_title(name, fontsize=14, fontweight="bold", loc="left", pad=5, color=COLORS["text"])
        for n, w in enumerate(waves, 1):
            ax.plot([w[0], w[3]], [X0, X1], color="black", lw=1.5, alpha=0.3)
            ax.plot([w[0], w[3]], [X0, X1], color="white", lw=0.8, ls=(0, (6, 4)), alpha=0.85)
            if k == 0:
                ax.text(w[0] + (w[3] - w[0]) * 0.3, X0 + (X1 - X0) * 0.3 + 5, str(n), fontsize=11, fontweight="bold",
                        color="white", ha="center", bbox=dict(boxstyle="round,pad=0.15", fc="black", ec="none", alpha=0.7))
        cax = fig.add_axes([L + W + 0.012, (0.9 + (len(PANELS) - 1 - k) * 2.32) / H, 0.012, 1.95 / H])
        cb = fig.colorbar(cf, cax=cax, ticks=levels[::2 if k != 2 else 4])
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=9.5, length=0)
        cb.set_label(unit, fontsize=11, fontweight="bold", color=COLORS["text"])

    add_note("Time runs left to right and longitude runs up the page. Dashed lines are the Kelvin waves traced in "
             "satellite sea level, numbered as in Figure 2.")
    add_title(fig, f"Kelvin waves in four variables, October {NOW - 1} to {max(ends):%B %Y}",
              "Kelvin-wave signal along the equator: each variable minus its own 91-day average. Red: above; blue: below.")
    add_source(fig, "Data: NOAA blended satellite altimetry (0.25°, daily, 1°S–1°N, via NOAA CoastWatch ERDDAP); TAO/TRITON "
               "moored buoys (NOAA PMEL, via NOAA CoastWatch ERDDAP), daily,\nat 8 moorings on the equator 10–15° apart, "
               "anomalies from each mooring's 1991–2020 seasonal cycle, 5-day means. Gaps up to 10 days and single "
               "missing moorings are interpolated.")
    save(fig, args.out,
         alt=f"Longitude–time diagrams along the equator from {START[:7]} to {max(ends):%B %Y} of the Kelvin-wave signal in "
             "satellite sea level, the depth of the 20 °C isotherm, sea surface temperature and zonal wind, with the "
             f"{len(waves)} Kelvin waves traced in satellite sea level overlaid.")


if __name__ == "__main__":
    main()
