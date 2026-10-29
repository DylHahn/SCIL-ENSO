"""
Kelvin waves 4 — Animation: coastal sea level from Peru to Washington, day by day

Daily tide-gauge sea level anomalies (UHSLC fast-delivery data; see enso_tidegauges.py) along the
Pacific coast of the Americas, from October of the year before the current El Niño to the latest
day, in the style of anim_kelvin.py: the top panel shows sea level at every gauge on the day shown,
from south (left) to north (right); the bottom panel builds up day by day, with time running down,
so a wave travelling north along the coast is a streak slanting down to the right. The map colours
each gauge by its sea level on the day shown.

    python anim_coastal_sea_level.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

from enso_anim import AnimationFrames
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, join_and
from enso_tidegauges import STATIONS, anomalies

NOW = 2026
START = f"{NOW - 1}-10-01"            # first day shown, as in anim_kelvin.py
SHOW = ["La Libertad, Ecuador", "San Diego, California", "Neah Bay, Washington"]


def short(name):
    town, place = name.split(", ")
    abbr = {"California": "CA", "Oregon": "OR", "Washington": "WA"}
    return f"{town}, {abbr.get(place, place)}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--every", type=int, default=2, help="days per animation frame")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "kelvin" / "anim_coastal_sea_level.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    anom, short_base = anomalies(refresh=args.refresh)
    anom = anom.loc[START:]
    anom = anom.loc[:anom.dropna(how="all").index[-1]]
    used = [s for s in STATIONS if anom[s[1]].notna().sum() >= 60]          # gauges reporting in this period
    names = [s[1] for s in used]
    a = anom[names]
    dates = a.index
    x = np.arange(len(names))

    levels = np.arange(-30, 30.1, 5)
    cmap = ListedColormap(plt.get_cmap("RdBu_r")(np.linspace(0.04, 0.96, len(levels) + 1)))
    norm = BoundaryNorm(levels, cmap.N, extend="both")

    H = 11.9
    fig = plt.figure(figsize=(13, H))
    W = 0.6
    HOV = (1.1, 6.1)                                              # bottom panel: bottom and height, inches
    prof = fig.add_axes([0.085, 1 - 3.35 / H, W, 1.6 / H])
    hov = fig.add_axes([0.085, HOV[0] / H, W, HOV[1] / H])

    def station_axis(ax):
        ax.set_xlim(-0.5, len(names) - 0.5)
        ax.set_xticks(x)
        ax.set_xticklabels([str(k) for k in x + 1])
        ax.tick_params(axis="both", labelsize=11)
        for t in ax.get_xticklabels() + ax.get_yticklabels():
            t.set_fontweight("bold")
        ax.set_xlabel("Tide gauge, from south (Peru) to north (Washington); numbers as on the map", fontsize=12,
                      fontweight="bold", color=COLORS["text"])

    # bottom: sea level at each gauge, revealed day by day
    data = np.ma.masked_invalid(a.values)
    mesh = hov.pcolormesh(np.arange(len(names) + 1) - 0.5, dates, np.ma.array(data, mask=True)[:-1], cmap=cmap,
                          norm=norm, shading="flat", rasterized=True)
    hov.set_facecolor(COLORS["surface_2"])
    hov.set_ylim(dates[-1] + pd.Timedelta(days=2), dates[0])
    station_axis(hov)
    hov.yaxis.set_major_locator(mdates.MonthLocator())
    hov.yaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    for t in hov.get_yticklabels():
        t.set_fontweight("bold")
    hov.set_ylabel("Date (time runs down)", fontsize=12, fontweight="bold", color=COLORS["text"])
    hov.set_title("Coastal sea level day by day: a streak slanting down to the right is a wave moving north",
                  fontsize=13.5, fontweight="bold", loc="left", pad=8, color=COLORS["text"])
    now_line = hov.axhline(dates[0], color="white", lw=1.2, alpha=0.9)
    cax = fig.add_axes([0.085 + W + 0.012, HOV[0] / H, 0.012, HOV[1] / H])
    cb = fig.colorbar(mesh, cax=cax, ticks=levels[::2])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    for t in cb.ax.get_yticklabels():
        t.set_fontweight("bold")
    cb.set_label("Coastal sea level compared with normal (cm), 10-day means", fontsize=11, fontweight="bold",
                 color=COLORS["text"])

    # top: sea level at every gauge on the day shown
    prof.axhline(0, color=COLORS["text_2"], lw=0.8)
    top = float(np.nanmax(a.values))
    prof.set_ylim(-20, max(30, np.ceil(top / 10) * 10 + 5))
    prof.yaxis.grid(True, color=COLORS["grid"], lw=0.6)
    prof.set_ylabel("Sea level (cm)", fontsize=12, fontweight="bold", color=COLORS["text"])
    station_axis(prof)
    prof.set_xlabel("Tide gauge, south → north", fontsize=12, fontweight="bold", color=COLORS["text"])
    prof_title = prof.set_title("", fontsize=13.5, fontweight="bold", loc="left", pad=8, color=COLORS["text"])
    line, = prof.plot([], [], color=COLORS["text"], lw=1.5, marker="o", ms=4)
    fills = []

    # right: map of the gauges, coloured by the day's sea level
    pc = ccrs.PlateCarree()
    lx = 0.085 + W + 0.085
    top_tab = H - (HOV[0] + HOV[1])
    mx = fig.add_axes([lx, 1 - (top_tab + 3.6) / H, 1 - lx - 0.01, 3.6 / H],
                      projection=ccrs.PlateCarree(central_longitude=-100))
    mx.set_extent([-132, -74, -8, 52], crs=pc)
    mx.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"])
    mx.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none")
    mx.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5)
    mx.plot([-132, -74], [0, 0], color=COLORS["muted"], lw=0.7, ls=(0, (4, 3)), transform=pc)
    dots = mx.scatter([s[3] for s in used], [s[2] for s in used], c=np.zeros(len(used)), cmap=cmap, norm=norm,
                      s=70, edgecolors="black", linewidths=0.8, transform=pc, zorder=5)
    placed = []
    for k, (_, name, lat, lon) in enumerate(used, 1):
        ly = lat
        while any(abs(ly - p) < 2.6 for p in placed):                # keep the numbers apart
            ly += 1.0
        placed.append(ly)
        mx.text(lon - 2.4, ly, str(k), transform=pc, ha="right", va="center", fontsize=10.5, fontweight="bold",
                color=COLORS["text"], zorder=6)
    mx.set_title("Tide gauges", fontsize=14, fontweight="bold", loc="left", pad=6, color=COLORS["text"])
    fig.text(lx, 1 - (top_tab + 3.85) / H, "\n".join(f"{k:>2}  {short(n)}" for k, n in enumerate(names, 1)),
             fontsize=10.5, fontweight="bold", color=COLORS["text_2"], va="top", linespacing=1.35)

    mon = a.iloc[-30:].mean()
    add_title(fig, f"Coastal sea level from Peru to Washington during the {NOW}/{NOW + 1} El Niño",
              "When a Kelvin wave reaches South America, part of it turns north along the coast and raises sea level "
              "at each tide gauge in turn.\nOver the last 30 days of data: "
              + join_and(f"{mon[n]:+.0f} cm at {short(n).split(',')[0]}" for n in SHOW if n in mon and np.isfinite(mon[n]))
              + " compared with normal.")
    add_source(fig, "Data: University of Hawaii Sea Level Center fast-delivery daily tide-gauge data; anomalies from "
               "each station's 1991–2020 seasonal cycle" + (" (whole record for " + join_and(
                   short(n).split(",")[0] for n in sorted(short_base & set(names))) + ")"
                   if short_base & set(names) else "") + ", 10-day means, not corrected for air pressure.")

    frames = AnimationFrames(fig, dpi=105)
    idx = list(range(0, len(dates), args.every))
    if idx[-1] != len(dates) - 1:
        idx.append(len(dates) - 1)
    for i in idx:
        d = dates[i]
        shown = np.ma.array(data, mask=np.ma.getmaskarray(data) | (np.arange(len(dates)) > i)[:, None])
        mesh.set_array(shown[:-1].ravel())
        now_line.set_ydata([d, d])
        v = a.values[i]
        line.set_data(x, v)
        for f in fills:
            f.remove()
        fills = [prof.fill_between(x, 0, v, where=v > 0, color="#e8574a", alpha=0.7, lw=0, interpolate=True),
                 prof.fill_between(x, 0, v, where=v < 0, color="#3987e5", alpha=0.7, lw=0, interpolate=True)]
        prof_title.set_text(f"Sea level along the coast, {d:%-d %B %Y}")
        dots.set_array(np.ma.masked_invalid(v))
        frames.grab(70)
    frames.durations[-1] = 4500
    frames.save(args.out, quality=85,
                alt=f"Animated chart of coastal sea level at {len(names)} tide gauges from Peru to Washington, from "
                    f"{dates[0]:%B %Y} to {dates[-1]:%-d %B %Y}. Over the last 30 days of data: "
                    + join_and(f"{short(n)} {mon[n]:+.0f} cm" for n in SHOW if n in mon and np.isfinite(mon[n]))
                    + " compared with normal.")


if __name__ == "__main__":
    main()
