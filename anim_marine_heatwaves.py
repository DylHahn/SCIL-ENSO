"""
Animation — Marine heatwaves along the Pacific coast of the Americas in 2026

Daily marine heatwave category (Hobday et al. 2016, 2018) from NOAA OISST v2.1 over 25°S–45°N,
150°W–70°W, from January of the current year to the latest day, with the share of two coastal
regions in each category:
  Southern California and northern Baja California, 30–35°N, 125°W to the coast;
  Ecuador and Peru (the Niño 1+2 region), 10°S–0°, 90°W–80°W.
See enso_mhw.py for the definitions. Frames every two days.

    python anim_marine_heatwaves.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch, Rectangle

from enso_anim import AnimationFrames
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, join_and
from enso_mhw import CAT_COLORS, CATEGORIES, heatwaves

REGIONS = {
    "Southern California and northern Baja": dict(lat=(30, 35), lon=(-125, -114)),
    "Ecuador and Peru (Niño 1+2)": dict(lat=(-10, 0), lon=(-90, -80)),
}
CALM = "#c9d3de"                           # ocean with no heatwave: light, so every category stands out


def shares(cat, box):
    """(time, 4) percentage of the box's ocean area in each category."""
    sub = cat.sel(lat=slice(*box["lat"]), lon=slice(*box["lon"]))
    w = np.cos(np.deg2rad(sub["lat"])) * sub.isel(time=0).notnull()
    tot = float(w.sum())
    return np.stack([((sub == k) * w).sum(("lat", "lon")).values / tot * 100 for k in range(1, 5)], axis=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--step", type=int, default=2, help="days between frames")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "anim_marine_heatwaves.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    anom, cat = heatwaves(f"{args.year}-01-01", refresh=args.refresh)
    times = pd.DatetimeIndex(cat["time"].values)
    latest = times[-1]
    sh = {name: shares(cat, box) for name, box in REGIONS.items()}

    fig = plt.figure(figsize=(13, 9.6))
    pc = ccrs.PlateCarree()
    ax = fig.add_axes([0.065, 0.1, 0.47, 0.72], projection=pc)
    ax.set_extent([-150, -70, -25, 45], crs=pc)
    ax.set_facecolor(CALM)
    cmap = ListedColormap([CALM] + CAT_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, 5), cmap.N)
    lon, lat = cat["lon"].values, cat["lat"].values
    mesh = ax.pcolormesh(lon, lat, cat.values[0], cmap=cmap, norm=norm, shading="nearest", transform=pc,
                         rasterized=True, zorder=1)
    ax.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none", zorder=2)
    ax.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5, zorder=3)
    ax.add_feature(cfeature.BORDERS, edgecolor=COLORS["muted"], linewidth=0.4, zorder=3)
    ax.plot([-150, -70], [0, 0], color="#555", lw=0.8, ls=(0, (4, 3)), transform=pc, zorder=3)
    ax.text(-149, 0.8, "equator", fontsize=10, color="#333", transform=pc, zorder=4)
    for k, (name, box) in enumerate(REGIONS.items()):
        (la0, la1), (lo0, lo1) = box["lat"], box["lon"]
        ax.add_patch(Rectangle((lo0, la0), lo1 - lo0, la1 - la0, fill=False, ec="black", lw=1.6, transform=pc,
                               zorder=4))
        ax.text(lo0 - 0.8, (la0 + la1) / 2, "AB"[k], ha="right", va="center", fontsize=13, fontweight="bold",
                color="black", transform=pc, zorder=4)
    gl = ax.gridlines(draw_labels=True, color=COLORS["grid"], lw=0.4, alpha=0.6,
                      xlocs=[-150, -130, -110, -90, -70], ylocs=[-20, 0, 20, 40])
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = dict(color=COLORS["text_2"], fontsize=10)
    date = ax.text(0.02, 0.97, "", transform=ax.transAxes, fontsize=17, fontweight="bold", color="black",
                   va="top", zorder=5, bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=4))

    # progression in each coastal region, revealed as the animation advances
    cursors, covers = [], []
    END = mdates.date2num(pd.Timestamp(f"{args.year}-12-31"))
    for k, (name, s) in enumerate(sh.items()):
        bx = fig.add_axes([0.6, 0.53 - k * 0.4, 0.37, 0.27])
        bx.set_facecolor(CALM)
        bx.stackplot(times, s.T, colors=CAT_COLORS, lw=0)
        bx.set_xlim(times[0], pd.Timestamp(f"{args.year}-12-31"))
        bx.set_ylim(0, 100)
        bx.set_yticks([0, 50, 100])
        bx.set_ylabel("% of area")
        months = pd.date_range(times[0], f"{args.year}-12-01", freq="MS")
        bx.set_xticks(months)
        bx.set_xticklabels([m.strftime("%b")[0] if m.month != 1 else f"Jan\n{m.year}" for m in months], fontsize=10)
        bx.set_title(f"{'AB'[k]}  {name}", fontsize=13, loc="left", pad=6)
        cover = Rectangle((mdates.date2num(times[0]), 0), END - mdates.date2num(times[0]), 100,
                          color=COLORS["surface_2"], lw=0, zorder=3)
        bx.add_patch(cover)
        covers.append(cover)
        cursors.append(bx.axvline(times[0], color="black", lw=1.2, zorder=4))
    fig.text(0.6, 0.835, "Share of each coastal region in a marine heatwave, by category", fontsize=12.5,
             color=COLORS["text"])
    fig.legend(handles=[Patch(color=CALM, label="No heatwave")]
               + [Patch(color=c, label=n) for c, n in zip(CAT_COLORS, CATEGORIES)],
               loc="lower left", bbox_to_anchor=(0.02, 0.83), ncol=5, fontsize=11, frameon=False,
               labelcolor=COLORS["text"], handlelength=1.4, columnspacing=1.2)

    now = {n: s[-1] for n, s in sh.items()}
    worst = {n: CATEGORIES[int(np.flatnonzero(s[-1] > 0)[-1])] if s[-1].sum() > 0 else "none" for n, s in sh.items()}
    add_title(fig, f"Marine heatwaves along the Pacific coast of the Americas, {args.year}",
              "Daily marine heatwave category, I Moderate to IV Extreme (Hobday et al. 2018). " + f"On {latest:%-d %B}: "
              + "; ".join(f"{n.split(' (')[0]} {now[n].sum():.0f}% in a heatwave" for n in REGIONS) + ".")
    add_source(fig, "Data: NOAA OISST v2.1 daily sea surface temperature (0.25°, shown every 1°), via NOAA PSL. "
               "Heatwave: above the 1991–2020 day-of-year 90th percentile for ≥ 5 days (Hobday et al. 2016).")

    frames = AnimationFrames(fig, dpi=100)
    idx = list(range(0, len(times), args.step))
    if idx[-1] != len(times) - 1:
        idx.append(len(times) - 1)
    for i in idx:
        mesh.set_array(cat.values[i].ravel())
        date.set_text(f"{times[i]:%-d %B %Y}")
        for cov, cur in zip(covers, cursors):
            x = mdates.date2num(pd.Timestamp(times[i]) + pd.Timedelta(hours=12))
            cov.set_x(x)
            cov.set_width(END - x)
            cur.set_xdata([x, x])
        frames.grab(90 if times[i].day > 2 else 400)
    frames.durations[-1] = 4000
    frames.save(args.out, quality=82,
                alt=f"Animated map of marine heatwave categories from {times[0]:%B %Y} to {latest:%-d %B %Y} over the "
                    "eastern Pacific from 25°S to 45°N, with charts of the share of two coastal regions in each "
                    f"category. On {latest:%-d %B %Y}: " + join_and(
                        f"{n} {now[n].sum():.0f}% in a heatwave, at most {worst[n]}" for n in REGIONS) + ".")


if __name__ == "__main__":
    main()
