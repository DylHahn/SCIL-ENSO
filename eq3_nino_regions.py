"""
Equatorial 3 — Spatial structure of the warming across the four Niño regions

Monthly SST anomalies in Niño 4 (western–central Pacific), Niño 3.4, Niño 3 and
Niño 1+2 (off Peru and Ecuador), from January of each onset year to June of the
following year. The distribution of warming from west to east distinguishes
eastern-Pacific El Niño events (largest anomalies near South America, e.g.
1997–98) from central-Pacific events. Source: NOAA CPC monthly Niño indices
(OISST v2.1, anomalies relative to 1991–2020).

    python eq3_nino_regions.py
    python eq3_nino_regions.py --refresh
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, join_and, load_nino_regions, save
from enso_equatorial import EVENTS

REGIONS = {
    "Niño 4": "160°E–150°W, 5°S–5°N",
    "Niño 3.4": "170°W–120°W, 5°S–5°N",
    "Niño 3": "150°W–90°W, 5°S–5°N",
    "Niño 1+2": "90°W–80°W, 10°S–0°",
}
# past events: fixed categorical slots (blue, aqua, yellow); the current event uses the El Niño red
PAST_COLORS = {"dark": ["#3987e5", "#199e70", "#c98500"], "light": ["#2a78d6", "#1baf7a", "#eda100"]}
N_MONTHS = 18
# box outlines for the locator map: (lon0, lon1, lat0, lat1) in 0–360 longitude, label side
BOXES = {"Niño 4": (160, 210, -5, 5, "top"), "Niño 3.4": (190, 240, -5, 5, "bottom"),
         "Niño 3": (210, 270, -5, 5, "top"), "Niño 1+2": (270, 280, -10, 0, "bottom")}


def locator_map(fig, rect):
    """Map of the tropical Pacific with the four Niño boxes, matching the panel titles."""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    pc = ccrs.PlateCarree()
    ax = fig.add_axes(rect, projection=ccrs.PlateCarree(central_longitude=180))
    ax.set_extent([115, 292, -22, 17], crs=pc)
    ax.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"], zorder=0)
    ax.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none", zorder=1)
    ax.plot([115, 292], [0, 0], transform=pc, color=COLORS["muted"], lw=0.7, ls=(0, (4, 3)), zorder=2)
    for name, (lo0, lo1, la0, la1, side) in BOXES.items():
        dashed = name == "Niño 3.4"
        ax.plot([lo0, lo1, lo1, lo0, lo0], [la0, la0, la1, la1, la0], transform=pc, zorder=3,
                color=COLORS["text"], lw=1.6, ls=(0, (4, 2)) if dashed else "-")
        y = la1 + 1.2 if side == "top" else la0 - 1.2
        ax.text((lo0 + lo1) / 2, y, name, transform=pc, ha="center", va="bottom" if side == "top" else "top",
                fontsize=11, fontweight="bold", color=COLORS["text"], zorder=4)
    ax.text(118, -20, "Indonesia /\nAustralia", transform=pc, fontsize=9, color=COLORS["text_2"], va="bottom")
    ax.text(289, -20, "South\nAmerica", transform=pc, fontsize=9, color=COLORS["text_2"], va="bottom", ha="right")
    ax.spines["geo"].set_edgecolor(COLORS["grid"])
    return ax


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, nargs="+", default=EVENTS)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "equatorial" / "eq3_nino_regions.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    df = load_nino_regions(args.refresh)
    now, past = args.years[-1], args.years[:-1]
    colors = dict(zip(past, PAST_COLORS[args.theme])) | {now: COLORS["el_nino"]}

    series = {}
    for y in args.years:
        idx = pd.date_range(f"{y}-01-01", periods=N_MONTHS, freq="MS")
        series[y] = df.reindex(idx)
    last = series[now].dropna(how="all").index[-1]
    k_last = int((last.year - now) * 12 + last.month - 1)

    fig = plt.figure(figsize=(13, 9.2))
    locator_map(fig, [0.07, 0.585, 0.91, 0.23])
    axes = []
    for k in range(4):
        axes.append(fig.add_axes([0.07 + k * 0.232, 0.13, 0.215, 0.33], sharey=axes[0] if axes else None))
    for ax in axes[1:]:
        ax.tick_params(labelleft=False)
    x = np.arange(N_MONTHS)
    for ax, (region, box) in zip(axes, REGIONS.items()):
        ax.axhline(0, color=COLORS["text_2"], lw=0.8)
        for y in args.years:
            v = series[y][region].values
            cur = y == now
            ax.plot(x, v, color=colors[y], lw=3.0 if cur else 1.8, zorder=3 if cur else 2,
                    solid_capstyle="round")
            if cur:
                ax.plot(x[k_last], v[k_last], "o", ms=7, color=colors[y], mec=COLORS["surface"], mew=1.5, zorder=4)
                ax.annotate(f"{v[k_last]:+.1f}", (x[k_last], v[k_last]), xytext=(6, 0), textcoords="offset points",
                            va="center", fontsize=11, fontweight="bold", color=COLORS["text"])
        ax.axvline(k_last, color=COLORS["muted"], lw=0.8, ls=(0, (3, 2)))
        ax.set_title(region, fontsize=14.5, loc="left", pad=20)
        ax.text(0, 1.02, box, transform=ax.transAxes, fontsize=9.5, color=COLORS["text_2"], va="bottom")
        ax.set_xticks([0, 3, 6, 9, 12, 15])
        ax.set_xticklabels(["Jan", "Apr", "Jul", "Oct", "Jan", "Apr"], fontsize=10.5)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.set_xlim(0, N_MONTHS - 1)
    axes[0].set_ylabel("SST anomaly (°C)")
    fig.text(0.525, 0.06, "Months from January of the onset year (second “Jan” = following year)",
             ha="center", fontsize=11, color=COLORS["text_2"])
    handles = [plt.Line2D([], [], color=colors[y], lw=3.0 if y == now else 1.8, label=f"{y}–{str(y + 1)[-2:]}")
               for y in args.years]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.065, 0.51), ncol=len(args.years),
               fontsize=11.5, labelcolor=COLORS["text_2"])

    # which past event looks most like this one at the same point in the year (all four regions)?
    cur_vec = series[now].iloc[k_last].values
    dist = {y: float(np.sqrt(np.nanmean((series[y].iloc[k_last].values - cur_vec) ** 2))) for y in past}
    analog = min(dist, key=dist.get)
    east, west = cur_vec[3], cur_vec[0]
    larger = bool(np.all(cur_vec > series[analog].iloc[k_last].values))
    tail = " but larger in every region." if larger else "."
    add_title(fig, "Distribution of sea surface warming across the Niño regions",
              f"Monthly anomalies in four regions, from the western–central Pacific (left) to the coast of Peru and "
              f"Ecuador (right). In {last:%B %Y} the warming\nwas concentrated in the east ({east:+.1f} °C in Niño 1+2 "
              f"versus {west:+.1f} °C in Niño 4), an eastern-Pacific pattern closest to {analog}–{str(analog + 1)[-2:]}"
              + tail)
    add_source(fig, "Data: NOAA Climate Prediction Center monthly Niño indices (OISST v2.1), anomalies relative "
               "to the 1991–2020 climatology.")
    save(fig, args.out,
         alt=f"Line charts of monthly SST anomalies in the Niño 4, 3.4, 3 and 1+2 regions for "
             + join_and(f"{y}–{str(y + 1)[-2:]}" for y in args.years)
             + f". In {last:%B %Y}: " + "; ".join(f"{r} {v:+.1f} °C" for r, v in zip(REGIONS, cur_vec))
             + f". Closest past event at the same stage: {analog}–{str(analog + 1)[-2:]}.")


if __name__ == "__main__":
    main()
