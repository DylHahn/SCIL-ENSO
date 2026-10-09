"""
SoCal 7 — Southern California winter precipitation during strong El Niño events (NOAA nClimGrid)

November–March precipitation (~5 km grid) for every winter whose Dec–Feb RONI
reached the strong threshold (≥ +1.5 °C), compared with the 1991–2020 normal:
  left:   average across those winters, as a percent of normal
  right:  how many of those winters were wetter than normal at each location
Bottom: regional November–March total for every winter since 1951, coloured by
ENSO phase.

    python socal_precip_el_nino_winters.py
    python socal_precip_el_nino_winters.py --threshold 1.0     # moderate-or-stronger
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save
from enso_nclimgrid import LAT, LON, socal_months
from enso_socal import CATEGORIES, categorize, category_colors, winter_roni

START, END = 1951, 2026
NORMAL = (1991, 2020)
CITIES = {"Los Angeles": (-118.24, 34.05), "San Diego": (-117.16, 32.72), "Riverside": (-117.40, 33.95),
          "Palm Springs": (-116.55, 33.83), "Santa Barbara": (-119.70, 34.42)}
BROWN_GREEN = ["#8c510a", "#bf812d", "#dfc27d", "#f2e8cf", "#c7eae5", "#80cdc1", "#35978f", "#01665e"]


def winter_totals(refresh):
    """(water year, lat, lon) Nov–Mar precipitation totals in mm."""
    months = [pd.Timestamp(year=y - (m >= 11), month=m, day=1) for y in range(START, END + 1) for m in (11, 12, 1, 2, 3)]
    da = socal_months("prcp", months, refresh)
    wy = da["time"].dt.year + (da["time"].dt.month >= 11)
    counts = da["time"].groupby(wy.rename("wy")).count()
    tot = da.groupby(wy.rename("wy")).sum("time")
    return tot.sel(wy=counts["wy"][counts == 5])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threshold", type=float, default=1.5, help="Dec–Feb RONI for a winter to count")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "socal_precip_el_nino_winters.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    tot = winter_totals(args.refresh)
    normal = tot.sel(wy=slice(*NORMAL)).mean("wy")
    djf = winter_roni(args.refresh)
    years = [int(y) for y in tot["wy"].values if djf.get(int(y), -9) >= args.threshold]
    ev = tot.sel(wy=years)
    pct = (100 * ev.mean("wy") / normal).where(normal > 20)
    wetter = (ev > normal).sum("wy").where(normal > 20).astype(float)
    n = len(years)

    fig = plt.figure(figsize=(13, 10.2))
    pc = ccrs.PlateCarree()

    def base(rect):
        ax = fig.add_axes(rect, projection=pc)
        ax.set_extent([LON[0], LON[1], LAT[0], LAT[1]], crs=pc)
        ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor=COLORS["land"], edgecolor="none", zorder=0)
        ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor=COLORS["ocean"], zorder=0)
        return ax

    def finish(ax):
        ax.add_feature(cfeature.LAKES.with_scale("10m"), facecolor=COLORS["ocean"], edgecolor="none", zorder=1.5)
        ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor=COLORS["text_2"], linewidth=0.6,
                       facecolor="none", zorder=2)
        ax.add_feature(cfeature.COASTLINE.with_scale("50m"), edgecolor=COLORS["text_2"], linewidth=0.6, zorder=2)
        for city, (lon, lat) in CITIES.items():
            ax.plot(lon, lat, "o", ms=4.5, color="black", mec="white", mew=1, transform=pc, zorder=4)
            ax.text(lon + 0.07, lat + 0.07, city, transform=pc, fontsize=9, color="black", zorder=4,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=0.8))

    # percent of normal
    ax = base([0.03, 0.56, 0.46, 0.25])
    levels = [0, 50, 75, 90, 110, 125, 150, 200, 300]
    cmap = ListedColormap(BROWN_GREEN)
    norm = BoundaryNorm(levels, cmap.N)
    cf = ax.contourf(pct["lon"], pct["lat"], pct.values, levels=levels, cmap=cmap, norm=norm, extend="max",
                     transform=pc, zorder=1)
    finish(ax)
    w = np.cos(np.deg2rad(pct["lat"]))
    reg_pct = float((ev.mean("wy") * w).sum() / (normal * w).sum() * 100)
    ax.set_title("Average precipitation, % of normal", fontsize=14.5, loc="left", pad=24, color=COLORS["text"])
    ax.text(0, 1.015, f"Regional mean {reg_pct:.0f}% of the 1991–2020 normal", transform=ax.transAxes,
            fontsize=11, color=COLORS["text_2"], va="bottom")
    cax = fig.add_axes([0.06, 0.515, 0.40, 0.013])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=levels[:-1])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=9.5, length=0)
    cb.set_label("Nov–Mar precipitation, % of normal", fontsize=10.5, color=COLORS["text_2"])

    # how many winters were wetter
    ax = base([0.52, 0.56, 0.46, 0.25])
    lv = np.arange(-0.5, n + 1)
    cmap2 = ListedColormap([BROWN_GREEN[int(round(i * 7 / n))] for i in range(n + 1)])
    cf2 = ax.contourf(wetter["lon"], wetter["lat"], wetter.values, levels=lv, cmap=cmap2,
                      norm=BoundaryNorm(lv, cmap2.N), transform=pc, zorder=1)
    finish(ax)
    reg_wet = int(((ev * w).sum(("lat", "lon")) > (normal * w).sum(("lat", "lon"))).sum())
    ax.set_title(f"Winters wetter than normal (of {n})", fontsize=14.5, loc="left", pad=24, color=COLORS["text"])
    ax.text(0, 1.015, f"Region as a whole: {reg_wet} of {n} winters wetter than normal", transform=ax.transAxes,
            fontsize=11, color=COLORS["text_2"], va="bottom")
    cax = fig.add_axes([0.55, 0.515, 0.40, 0.013])
    cb = fig.colorbar(cf2, cax=cax, orientation="horizontal", ticks=range(n + 1))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=9.5, length=0)
    cb.set_label("Number of strong El Niño winters with above-normal precipitation", fontsize=10.5,
                 color=COLORS["text_2"])

    # regional series, every winter
    reg = ((tot * w).sum(("lat", "lon")) / (normal * w).sum(("lat", "lon")) * 100).to_series()
    cols = category_colors()
    bx = fig.add_axes([0.07, 0.08, 0.90, 0.30])
    cats = [categorize(djf.get(int(y), np.nan)) for y in reg.index]
    bx.bar(reg.index, reg.values, width=0.8, color=[cols.get(c, COLORS["neutral"]) for c in cats], lw=0)
    bx.axhline(100, color=COLORS["text_2"], lw=1, ls=(0, (4, 3)))
    for y in years:
        bx.annotate(f"{y - 1}–{str(y)[-2:]}", (y, reg[y]), xytext=(0, 3), textcoords="offset points", ha="center",
                    va="bottom", fontsize=9, color=COLORS["text"])
    bx.set_xlim(START - 1, END + 1)
    bx.set_ylim(0, reg.max() * 1.15)
    bx.set_ylabel("% of normal")
    bx.yaxis.grid(True)
    bx.set_axisbelow(True)
    bx.set_title("Southern California Nov–Mar precipitation, every winter since 1951 (regional mean)",
                 fontsize=13, loc="left", pad=8)
    bx.legend(handles=[Patch(color=cols[c], label=c.replace("\n", " ")) for c, _, _ in CATEGORIES],
              loc="upper right", ncol=4, fontsize=10, labelcolor=COLORS["text_2"])

    driest = min(years, key=lambda y: reg[y])
    add_title(fig, "Southern California winter precipitation during strong El Niño events",
              f"November–March precipitation in the {n} winters since 1951 with a strong El Niño (RONI ≥ "
              f"+{args.threshold:.1f} °C) averaged {reg_pct:.0f}% of normal; {reg_wet} of {n} were\nwetter than "
              f"normal region-wide. Outcomes vary widely between events: {driest - 1}–{str(driest)[-2:]} received "
              f"{reg[driest]:.0f}% of normal.")
    add_source(fig, "Data: NOAA NCEI nClimGrid monthly precipitation (~5 km), Nov–Mar totals; normal = "
               f"{NORMAL[0]}–{NORMAL[1]}; El Niño strength from NOAA CPC RONI (Dec–Feb). Very dry areas left blank.")
    save(fig, args.out,
         alt=f"Maps of Southern California November–March precipitation during {n} strong El Niño winters "
             f"({', '.join(f'{y - 1}–{str(y)[-2:]}' for y in years)}): regional mean {reg_pct:.0f}% of normal, "
             f"{reg_wet} of {n} winters wetter than normal. Bar chart of every winter since 1951 coloured by ENSO "
             "phase.")


if __name__ == "__main__":
    main()
