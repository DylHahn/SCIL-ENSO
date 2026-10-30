"""
Animation 8 — Sea level across the tropical Pacific as a 3D landscape, day by day

Daily satellite sea level anomaly over 12°S–12°N, 145°E–82°W (NOAA blended altimetry, 1°),
relative to the 2017–2024 seasonal cycle with a 5-day running mean, drawn as a surface whose height
is the anomaly (greatly exaggerated). Kelvin waves appear as ridges on the equator travelling east;
over the event the eastern Pacific rises as warm water piles up against South America.

    python anim_sealevel_3d.py
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from enso_anim import AnimationFrames
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style
from enso_sealevel import band_anomalies, daily_band

NOW = 2026
LON = (145, 278)
LAT = (-12, 12)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--every", type=int, default=4, help="days per animation frame")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_sealevel_3d.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    anom = band_anomalies(daily_band(f"{NOW - 1}-07-01", refresh=args.refresh))
    anom = anom.sel(longitude=slice(*LON), latitude=slice(*LAT)).dropna("time", how="all")
    lat, lon = anom["latitude"].values, anom["longitude"].values
    dates = [__import__("pandas").Timestamp(t) for t in anom["time"].values]
    X, Y = np.meshgrid(lon, lat)
    from interactive_3d_data import for_display
    vals = for_display(anom.values, coast=1, sigma=1.2)            # light spatial smoothing for display, cm

    levels = np.arange(-30, 30.1, 5)
    cmap = plt.get_cmap("RdBu_r", len(levels) + 1)
    norm = BoundaryNorm(levels, cmap.N, extend="both")

    box = (3.2, 0.85, 0.8)
    exag = (box[2] / 0.90) / (box[0] / ((LON[1] - LON[0]) * 111.32e3))     # z spans 90 cm; x spans the basin
    fig = plt.figure(figsize=(13, 8.2))
    ax = fig.add_axes([-0.08, 0.04, 1.14, 0.86], projection="3d")
    ax.set_box_aspect(box, zoom=1.45)
    ax.computed_zorder = False
    ax.set_facecolor("none")
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.set_pane_color((0, 0, 0, 0))
        a._axinfo["grid"]["color"] = COLORS["grid"]
    ax.tick_params(colors=COLORS["text_2"], labelsize=8.5, pad=0)
    ax.set_xlim(*LON); ax.set_ylim(lat.min(), lat.max()); ax.set_zlim(-30, 60)
    ax.set_xticks([160, 180, 220, 260]); ax.set_xticklabels(["160°E", "180°", "140°W", "100°W"])
    ax.set_yticks([-10, 0, 10]); ax.set_yticklabels(["10°S", "0°", "10°N"])
    ax.set_zticks([-20, 0, 20, 40]); ax.set_zticklabels(["−20 cm", "0", "+20", "+40"])
    ax.view_init(elev=30, azim=-64)

    cax = fig.add_axes([0.3, 0.075, 0.4, 0.016])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal",
                      ticks=levels[::2], extend="both")
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10, length=0)
    cb.set_label("Sea level anomaly (cm): height and colour", fontsize=10.5, color=COLORS["text_2"])
    stamp = fig.text(0.04, 0.80, "", fontsize=17, fontweight="bold", color=COLORS["text"])
    fig.text(0.04, 0.765, "Ridges along the equator moving east (left to right) are Kelvin waves;\n"
             "the eastern Pacific rises as warm water piles up against South America.",
             fontsize=11, color=COLORS["text_2"], va="top", linespacing=1.35)
    add_title(fig, "Sea level across the tropical Pacific in 3D",
              "Daily satellite sea level height (SSH) compared with normal. Height exaggerated about "
              f"{exag / 1e6:.0f} million times.")
    add_source(fig, "Data: NOAA blended satellite altimetry (daily, sampled at 1°, 12°S–12°N), anomalies relative to the "
               "2017–2024 seasonal cycle, 5-day running mean, lightly smoothed. South America is at the right.")

    frames = AnimationFrames(fig, dpi=105)
    surf = None
    idx = list(range(0, len(dates), args.every))
    if idx[-1] != len(dates) - 1:
        idx.append(len(dates) - 1)
    for i in idx:
        z = np.clip(vals[i], -30, 60)
        colors = cmap(norm(np.nan_to_num(vals[i])))
        colors[..., 3] = np.where(np.isfinite(vals[i]), 1.0, 0.0)
        if surf is not None:
            surf.remove()
        surf = ax.plot_surface(X, Y, np.where(np.isfinite(z), z, np.nan), facecolors=colors, rstride=1, cstride=1,
                               linewidth=0, antialiased=False, shade=True)
        stamp.set_text(f"{dates[i]:%-d %B %Y}")
        frames.grab(75)
    frames.durations[-1] = 4000
    east = lon >= 230
    eq = np.abs(lat) <= 2
    first, last = [round(float(np.nanmean(vals[k][eq][:, east]))) + 0 for k in (0, -1)]
    frames.save(args.out, quality=84,
                alt=f"Animated 3D landscape of sea level across the tropical Pacific from {dates[0]:%B %Y} to "
                    f"{dates[-1]:%-d %B %Y}. Ridges travel east along the equator as Kelvin waves, and sea level on "
                    f"the equator east of 130°W rises from {first:+.0f} cm to {last:+.0f} cm.")


if __name__ == "__main__":
    main()
