"""
Animation 5 — The tropical Pacific in 3D: a normal year and 2026, month by month

Two rotating 3D blocks of the tropical Pacific (15°S–15°N, 135°E–85°W) from NCEP GODAS. The
semi-transparent top surface is the temperature at 5 m; the lower surface is the depth of the
20 °C isotherm, the base of the warm upper layer. In a normal year the warm layer is thick in the
west and thin in the east; in 2026 it has flattened and deepened toward South America. Months run
from January of the onset year to the latest GODAS month while the camera turns slowly.
Depth is greatly exaggerated.

    python anim_3d.py
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from anim_warm_water import d20, load_temps, monthly_normal
from interactive_3d_data import for_display
from enso_anim import AnimationFrames, event_months, event_name, interpolate_months
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style

NOW = 2026
LAT_STEP, LON_STEP = 2, 2
LAT, LON = (-15, 15), (135, 275)       # away from the Maritime Continent and Central America


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--steps", type=int, default=3, help="interpolated frames per month")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_3d.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    span = event_months(NOW)                       # January of the onset year to the latest month
    temps, months, lat, lon, depths = load_temps(span, args.refresh)
    normal = monthly_normal([m.month for m in months])
    la = np.flatnonzero((lat >= LAT[0]) & (lat <= LAT[1]))[::LAT_STEP]
    lo = np.flatnonzero((lon >= LON[0]) & (lon <= LON[1]))[::LON_STEP]
    pick = lambda a: a[:, la][:, :, lo]
    lat, lon = lat[la], lon[lo]
    rows = [("Normal (1991–2020)", normal), (event_name(NOW), temps)]
    fields = [(pick(for_display(t[:, 0])), pick(for_display(d20(t, depths)))) for _, t in rows]
    X, Y = np.meshgrid(lon, lat)
    width_m = (lon.max() - lon.min()) * 111e3
    box = (3.0, 0.75, 0.9)
    zmin = -240
    exag = (box[2] / -zmin) / (box[0] / width_m)

    sst_levels, d20_levels = np.arange(18, 32.01, 0.5), np.arange(0, 220.01, 10)
    sst_cmap = plt.get_cmap("turbo", len(sst_levels) + 1)
    d20_cmap = plt.get_cmap("turbo", len(d20_levels) + 1)
    sst_norm = BoundaryNorm(sst_levels, sst_cmap.N, extend="both")
    d20_norm = BoundaryNorm(d20_levels, d20_cmap.N, extend="both")

    fig = plt.figure(figsize=(13, 7.6))
    axes, labels = [], []
    for k, (name, _) in enumerate(rows):
        ax = fig.add_axes([-0.03 + k * 0.485, 0.14, 0.52, 0.68], projection="3d")
        ax.set_box_aspect(box, zoom=1.22)
        ax.computed_zorder = False                 # draw the warm-layer base first, then the surface
        ax.set_facecolor("none")
        for a in (ax.xaxis, ax.yaxis, ax.zaxis):
            a.set_pane_color((0, 0, 0, 0))
            a._axinfo["grid"]["color"] = COLORS["grid"]
            a.label.set_color(COLORS["text_2"])
        ax.tick_params(colors=COLORS["text_2"], labelsize=8, pad=0)
        ax.set_xlim(lon.min(), lon.max()); ax.set_ylim(lat.min(), lat.max()); ax.set_zlim(zmin, 0)
        ax.set_xticks([140, 180, 220, 260])
        ax.set_xticklabels(["140°E", "180°", "140°W", "100°W"])
        ax.set_yticks([-15, 0, 15])
        ax.set_yticklabels(["15°S", "0°", "15°N"])
        ax.set_zticks([0, -100, -200])
        ax.set_zticklabels(["0 m", "100 m", "200 m"])
        cur = k == 1
        labels.append(fig.text(0.04 + k * 0.5, 0.80, "", fontsize=15, fontweight="bold",
                               color=COLORS["el_nino"] if cur else COLORS["text"]))
        axes.append(ax)

    def surf(ax, z, c, cmap, norm, alpha):
        colors = cmap(norm(np.where(np.isfinite(c), c, np.nan)))
        colors[..., 3] = np.where(np.isfinite(c), alpha, 0)
        return ax.plot_surface(X, Y, np.where(np.isfinite(z), z, np.nan), facecolors=colors, rstride=1, cstride=1,
                               linewidth=0, antialiased=False, shade=False)

    for k, (cmap, norm, ticks, text) in enumerate([
            (sst_cmap, sst_norm, np.arange(18, 33, 2), "Temperature at 5 m (°C): top surface"),
            (d20_cmap, d20_norm, np.arange(0, 221, 40), "Depth of the 20 °C isotherm (m): lower surface")]):
        cax = fig.add_axes([0.1 + k * 0.45, 0.10, 0.35, 0.018])
        sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
        cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=ticks, extend="both")
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=10, length=0)
        cb.set_label(text, fontsize=10.5, color=COLORS["text_2"])
    add_title(fig, f"The tropical Pacific in 3D: the warm upper layer in a normal year and in {event_name(NOW)}",
              "The lower surface is the base of the warm layer (20 °C). Normally it is deep in the west and rises "
              "toward South America;\nduring El Niño warm water spreads east and the layer flattens. Depth is "
              f"exaggerated about {round(exag, -3):,.0f} times.")
    add_source(fig, "Data: NCEP GODAS ocean reanalysis (NOAA), monthly, 15°S–15°N, sampled every ⅔° latitude × 2° "
               "longitude and lightly smoothed; coastal cells omitted; normal from the 1991–2020 mean temperature.")

    seqs = [(interpolate_months(s, args.steps), interpolate_months(z, args.steps)) for s, z in fields]
    pos_all = seqs[0][0][1]
    frames = AnimationFrames(fig, dpi=110)
    drawn = [[], []]
    n = len(pos_all)
    for i, pos in enumerate(pos_all):
        kk = int(round(pos))
        azim = -78 + 36 * i / max(n - 1, 1)
        for k, ax in enumerate(axes):
            for art in drawn[k]:
                art.remove()
            s, z = seqs[k][0][0][i], seqs[k][1][0][i]
            drawn[k] = [surf(ax, -z, z, d20_cmap, d20_norm, 1.0), surf(ax, np.zeros_like(s), s, sst_cmap, sst_norm, 0.6)]
            ax.view_init(elev=18, azim=azim)
            m = months[kk]
            labels[k].set_text(f"{rows[k][0]} · {calendar.month_name[m.month]}" if k == 0
                               else f"{calendar.month_name[m.month]} {m.year}")
        frames.grab(700 if abs(pos - round(pos)) < 1e-9 else 90)
    frames.durations[-1] = 3500
    east = (lon >= 230)
    eq = np.abs(lat) <= 2
    zz = [float(np.nanmean(z[-1][eq][:, east])) for _, z in fields]
    frames.save(args.out, quality=85,
                alt=f"Rotating 3D animation of the tropical Pacific comparing a normal year with 2026 from "
                    f"{months[0]:%B %Y} to {months[-1]:%B %Y}. In {months[-1]:%B}, the base of the warm layer on the "
                    f"equator east of 130°W lay at about {zz[1]:.0f} m in 2026, against {zz[0]:.0f} m normally.")


if __name__ == "__main__":
    main()
