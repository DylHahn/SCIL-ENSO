"""
Kelvin waves 3 — Coastal sea level from Ecuador to Washington

Daily tide-gauge sea level anomalies (UHSLC fast-delivery data; see enso_tidegauges.py) at stations
along the Pacific coast of the Americas, from Peru and Ecuador to Neah Bay, Washington (at the
entrance to the strait leading to Seattle), from October of the year before each El Niño to January
after its first year, for 2026/2027, 2023/2024, 2015/2016 and 1997/1998. When an equatorial Kelvin
wave reaches South America, part of it travels poleward along the coast as a coastal-trapped wave,
raising sea level at each station in turn; coastal sea level also responds to local winds and air
pressure, especially north of Mexico. Several Mexican gauges have stopped reporting, so the
coverage differs between events.

    python coastal_sea_level.py
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

from enso_common import CLEAN, FIG_DIR, COLORS, add_source, add_title, apply_style, join_and, save
from enso_tidegauges import STATIONS, anomalies

NOW = 2026
EVENTS = [NOW, 2023, 2015, 1997]
SHOW = ["La Libertad, Ecuador", "San Diego, California", "Neah Bay, Washington"]


def window(y):
    return pd.Timestamp(f"{y - 1}-10-01"), pd.Timestamp(f"{y + 1}-01-31")


def short(name):
    town, place = name.split(", ")
    abbr = {"California": "CA", "Oregon": "OR", "Washington": "WA"}
    return f"{town}, {abbr.get(place, place)}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "kelvin" / "coastal_sea_level.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    anom, short_base = anomalies(refresh=args.refresh)
    latest = anom.dropna(how="all").index[-1]
    # stations with data in at least one of the periods shown, south to north, one row each
    used = [s for s in STATIONS if any(anom.loc[window(y)[0]:window(y)[1], s[1]].notna().sum() >= 60
                                       for y in EVENTS)]
    row = {s[1]: k for k, s in enumerate(used)}

    levels = np.arange(-30, 30.1, 5)
    cmap = ListedColormap(plt.get_cmap("RdBu_r")(np.linspace(0.04, 0.96, len(levels) + 1)))
    norm = BoundaryNorm(levels, cmap.N, extend="both")

    fig = plt.figure(figsize=(13, 11))
    # map of the stations
    pc = ccrs.PlateCarree()
    mx = fig.add_axes([0.01, 0.12, 0.25, 0.7], projection=ccrs.PlateCarree(central_longitude=-100))
    mx.set_extent([-136, -74, -8, 52], crs=pc)
    mx.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"])
    mx.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none")
    mx.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5)
    mx.plot([-132, -74], [0, 0], color=COLORS["muted"], lw=0.7, ls=(0, (4, 3)), transform=pc)
    placed = []
    for k, (_, name, lat, lon) in enumerate(used, 1):
        mx.plot(lon, lat, "o", ms=6, color=COLORS["el_nino"], mec=COLORS["surface"], mew=0.8, transform=pc, zorder=5)
        ly = lat
        while any(abs(ly - p) < 2.6 for p in placed):          # keep the numbers apart
            ly += 1.0
        placed.append(ly)
        mx.text(lon - 2.2, ly, str(k), transform=pc, ha="right", va="center", fontsize=10.5, fontweight="bold",
                color=COLORS["text"], zorder=6)
    mx.set_title("Tide gauges", fontsize=13, loc="left", pad=6)

    panels = []
    for k, y in enumerate(EVENTS):
        r, c = divmod(k, 2)
        ax = fig.add_axes([0.42 + c * 0.29, 0.555 - r * 0.385, 0.265, 0.3])
        start, end = window(y)
        w = anom.loc[start:end]
        have = [s for s in used if w[s[1]].notna().sum() >= 60]
        t = pd.date_range(start, end + pd.Timedelta(days=1))
        for _, name, _, _ in have:
            v = w[name].reindex(t[:-1]).values
            mesh = ax.pcolormesh(t, [row[name] - 0.42, row[name] + 0.42], v[None, :], cmap=cmap, norm=norm,
                                 rasterized=True)
        ax.set_xlim(start, end)
        ax.set_ylim(-0.6, len(used) - 0.4)
        ax.set_facecolor(COLORS["surface_2"])
        ticks = pd.date_range(start, end, freq="MS")[::3]
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{calendar.month_abbr[m.month]}\n{m.year}" if m.month in (1, 10) else
                            calendar.month_abbr[m.month] for m in ticks], fontsize=9.5)
        names = [s[1] for s in used]
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels([f"{short(n)}  {k}" for k, n in enumerate(names, 1)] if c == 0 else [], fontsize=9)
        for lbl, n in zip(ax.get_yticklabels(), names):
            if n not in {s[1] for s in have}:
                lbl.set_alpha(0.35)
        onset = pd.Timestamp(f"{y}-01-01")
        ax.axvline(onset, color=COLORS["text"], lw=0.8, ls=(0, (4, 3)))
        cur = y == NOW
        ax.set_title(f"{y}/{y + 1}", fontsize=14, fontweight="bold", loc="left", pad=6,
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        for sp in ax.spines.values():
            sp.set_visible(cur)
            sp.set_edgecolor(COLORS["el_nino"])
            sp.set_linewidth(2)
        if cur and latest < end:
            ax.axvspan(latest + pd.Timedelta(days=1), end, color=COLORS["surface_2"], zorder=3)
            ax.text(latest + (end - latest) / 2, np.mean(ax.get_ylim()), f"Data through\n{latest:%-d %b %Y}",
                    ha="center", va="center", fontsize=10, color=COLORS["text_2"], zorder=4, rotation=90)
        panels.append(ax)
    fig.text(0.02, 0.1, "Rows run from south (bottom) to north (top);\nthe numbers match the map.", fontsize=10.5,
             color=COLORS["text_2"])
    cax = fig.add_axes([0.46, 0.09, 0.45, 0.016])
    cb = fig.colorbar(mesh, cax=cax, orientation="horizontal", ticks=np.arange(-30, 31, 10))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("Coastal sea level compared with normal (cm), 10-day means", fontsize=11, color=COLORS["text_2"])

    # latest full month at three stations, against the same month of 1997
    m = (latest + pd.Timedelta(days=1)).replace(day=1) - pd.DateOffset(months=1)
    mon = anom.loc[f"{m:%Y-%m}"].mean()
    then = anom.loc[f"1997-{m.month:02d}"].mean()
    add_title(fig, "Coastal sea level from Ecuador to Washington during four El Niño events",
              f"Daily tide-gauge sea level compared with normal, 10-day means. {m:%B %Y}: "
              + join_and(f"{mon[n]:+.0f} cm at {short(n).split(',')[0]}" for n in SHOW if np.isfinite(mon[n])) + ".")
    add_source(fig, "Data: University of Hawaii Sea Level Center fast-delivery daily tide-gauge data; anomalies from "
               "each station's 1991–2020 seasonal cycle" + (" (whole record for " + join_and(
                   short(n).split(",")[0] for n in sorted(short_base & {u[1] for u in used})) + ")"
                   if short_base & {u[1] for u in used} else "") + ", not corrected for air pressure.")
    save(fig, args.out,
         alt="Time–distance diagrams of coastal sea level anomalies at tide gauges from Peru to Washington for the "
             "El Niños of " + join_and(f"{y}/{y + 1}" for y in EVENTS) + f". In {m:%B %Y}: "
             + join_and(f"{short(n)} {mon[n]:+.0f} cm" for n in SHOW if np.isfinite(mon[n])) + f"; in {m:%B} 1997: "
             + join_and(f"{short(n)} {then[n]:+.0f} cm" for n in SHOW if np.isfinite(then[n])) + ".")


if __name__ == "__main__":
    main()
