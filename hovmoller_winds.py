"""
Equatorial 7 — Westerly wind bursts along the equator (Hovmöller)

Daily anomalies of the east–west (zonal) surface wind at 10 m, averaged over 5°S–5°N from 120°E
to 80°W, from October of the year before each El Niño to January after its first year, for the
current event, 2023/2024, 2015/2016 and 1997/1998 (the satellite record begins in 1987, so
1982/1983 is not shown). Positive (red) anomalies are winds blowing more toward the east than
normal: they weaken the trade winds, and short, strong episodes ("westerly wind bursts") push warm
water east as Kelvin waves. Source: NOAA NCEI Blended Sea Winds v2; anomalies relative to the
1991–2020 monthly climatology; 5-day running means for display.

Bursts are counted as episodes of daily anomalies of +5 m/s or more, averaged over at least 10° of
longitude, lasting at least 3 days (separate if more than 3 days apart).

    python hovmoller_winds.py
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import FuncFormatter

from enso_common import CLEAN, FIG_DIR, COLORS, add_source, add_title, apply_style, join_and, lon_label, save
from enso_equatorial import LON_RANGE, _map_strip
from enso_winds import daily_anomaly

NOW = 2026
EVENTS = [NOW, 2023, 2015, 1997]
BURST = dict(threshold=5.0, width=10.0, days=3, gap=3)


def window(y):
    return pd.Timestamp(f"{y - 1}-10-01"), pd.Timestamp(f"{y + 1}-01-31")


def bursts(anom, until):
    """Number of westerly wind bursts in `anom` (time, lon) up to `until` (see the module notes)."""
    a = anom.sel(time=slice(None, until))
    t = pd.DatetimeIndex(a["time"].values)
    a = a.reindex(time=pd.date_range(t[0], t[-1]))                 # missing days are not bursts
    lon = a["lon"].values
    step = float(np.diff(lon).mean())
    k = max(int(round(BURST["width"] / step)), 1)
    vals = a.values
    smooth = np.stack([np.convolve(r, np.ones(k) / k, mode="valid") for r in np.nan_to_num(vals)])
    hit = (smooth >= BURST["threshold"]).any(axis=1)
    runs, start = [], None                               # (first, last) day index of each spell
    for i, h in enumerate(list(hit) + [False]):
        if h and start is None:
            start = i
        elif not h and start is not None:
            runs.append((start, i - 1))
            start = None
    merged = []
    for r in runs:                                       # spells close together are one burst
        if merged and r[0] - merged[-1][1] - 1 <= BURST["gap"]:
            merged[-1] = (merged[-1][0], r[1])
        else:
            merged.append(r)
    return sum(1 for r0, r1 in merged if r1 - r0 + 1 >= BURST["days"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "equatorial" / "hovmoller_winds.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    fields = {y: daily_anomaly(*window(y), refresh=args.refresh and y == NOW) for y in EVENTS}
    latest = pd.Timestamp(fields[NOW]["time"].values[-1])
    # bursts from October of the year before to the same calendar day as the latest data
    t = pd.DatetimeIndex(fields[NOW]["time"].values)
    missing = len(pd.date_range(t[0], t[-1]).difference(t))         # days absent from NCEI's record
    counts = {y: bursts(fields[y], pd.Timestamp(year=y, month=latest.month, day=latest.day)) for y in EVENTS}

    levels = np.arange(-8, 8.01, 1)
    base = plt.get_cmap("RdBu_r")
    cmap = ListedColormap(base(np.linspace(0.04, 0.96, len(levels) + 1)))
    norm = BoundaryNorm(levels, cmap.N, extend="both")

    fig = plt.figure(figsize=(13, 11.2))
    left, right, gap = 0.115, 0.985, 0.022
    width = (right - left - gap * (len(EVENTS) - 1)) / len(EVENTS)
    p_bottom, p_height = 0.17, 0.58
    for k, y in enumerate(EVENTS):
        a = fields[y]
        start, end = window(y)
        have = pd.DatetimeIndex(a["time"].values)
        a = a.reindex(time=pd.date_range(have[0], have[-1]))              # missing days stay blank
        a = a.rolling(time=5, center=True, min_periods=3).mean()
        days = (pd.DatetimeIndex(a["time"].values) - start).days.values
        x0 = left + k * (width + gap)
        cur = y == NOW
        strip = _map_strip(fig, [x0, p_bottom + p_height + 0.012, width, 0.05])
        strip.set_title(f"{y}/{y + 1}", fontsize=15, fontweight="bold", loc="left", pad=6,
                        color=COLORS["el_nino"] if cur else COLORS["text"])
        ax = fig.add_axes([x0, p_bottom, width, p_height])
        cf = ax.contourf(a["lon"].values, days, a.values, levels=levels, cmap=cmap, norm=norm, extend="both")
        total = (end - start).days
        ax.set_ylim(total, 0)
        ax.set_xlim(*LON_RANGE)
        ax.set_facecolor(COLORS["surface_2"])
        ticks = pd.date_range(start, end, freq="MS")[::3]
        ax.set_yticks([(t - start).days for t in ticks])
        ax.set_yticklabels([f"{calendar.month_abbr[t.month]} {t.year}" if t.month in (1, 10) else
                            calendar.month_abbr[t.month] for t in ticks] if k == 0 else [], fontsize=10)
        onset = (pd.Timestamp(f"{y}-01-01") - start).days
        ax.axhline(onset, color=COLORS["text"], lw=0.9, ls=(0, (4, 3)))
        ax.set_xticks([150, 210, 270])
        ax.set_xticks([180, 240], minor=True)
        ax.xaxis.set_major_formatter(FuncFormatter(lon_label))
        ax.tick_params(axis="x", labelsize=10)
        for sp in ax.spines.values():
            sp.set_visible(cur)
            sp.set_edgecolor(COLORS["el_nino"])
            sp.set_linewidth(2)
        gaps = pd.date_range(have[0], have[-1]).difference(have)
        if len(gaps):                                                       # label gaps of a week or more
            breaks = np.flatnonzero(np.diff(gaps.values).astype("timedelta64[D]").astype(int) > 1)
            for g0, g1 in zip(np.r_[0, breaks + 1], np.r_[breaks, len(gaps) - 1]):
                if (gaps[g1] - gaps[g0]).days >= 6:
                    ax.text(np.mean(LON_RANGE), ((gaps[g0] - start).days + (gaps[g1] - start).days) / 2,
                            f"no data, {gaps[g0]:%-d %b}–{gaps[g1]:%-d %b}", ha="center", va="center", fontsize=10,
                            color=COLORS["text_2"])
        if days[-1] < total - 1:
            ax.axhline(days[-1], color=COLORS["text_2"], lw=1, ls=(0, (3, 2)))
            ax.text(np.mean(LON_RANGE), days[-1] + 12, f"Data through\n{latest:%-d %B %Y}", ha="center",
                    va="top", fontsize=10.5, color=COLORS["text_2"])
        ax.text(0.03, 0.005, f"{counts[y]} bursts to {latest:%-d %b}", transform=ax.transAxes, fontsize=10.5,
                color=COLORS["text"], va="bottom", bbox=dict(facecolor=COLORS["surface"], edgecolor="none",
                                                              alpha=0.8, pad=2))
        if k == 0:
            ax.set_ylabel("Date  (time runs downward ↓)", fontsize=11)
    fig.text((left + right) / 2, 0.125, "Longitude along the equator  (west → east)", ha="center", fontsize=11,
             color=COLORS["text_2"])

    cax = fig.add_axes([0.25, 0.07, 0.5, 0.017])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=np.arange(-8, 9, 2))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("East–west wind anomaly (m/s), 5°S–5°N   ·   red: westerly (toward South America), "
                 "blue: stronger trade winds", fontsize=11, color=COLORS["text_2"])
    if not CLEAN:
        fig.text(0.02, 1 - 1.15 / 11.2, "How to read: each panel is one El Niño. Each row is one day, from October "
                 "of the year before (top) to the following January; position runs from the western Pacific (left) "
                 "to\nSouth America (right). Red streaks are westerly wind bursts: short spells of wind blowing toward "
                 "South America that push warm water east. The dashed line marks 1 January of the El Niño's first year.",
                 ha="left", va="top", fontsize=11.5, color=COLORS["text"], linespacing=1.4,
                 bbox=dict(facecolor=COLORS["surface_2"], edgecolor="none", pad=6))
    add_title(fig, "Westerly wind bursts along the equator before and during major El Niño events",
              f"Daily surface wind compared with normal, 5°S–5°N. From October {NOW - 1} to {latest:%-d %B %Y}: "
              f"{counts[NOW]} westerly wind bursts"
              + (f" ({missing} days missing from the record)" if missing else "") + ",\ncompared with "
              + join_and(f"{counts[y]} in {y - 1}/{y}" for y in EVENTS[1:]) + " over the same part of the year.")
    add_source(fig, "Data: NOAA NCEI Blended Sea Winds v2, daily 10 m winds (0.25°, shown on a 2° grid), 5-day "
               "means; anomalies from the 1991–2020 monthly normal. Bursts: ≥ +5 m/s over ≥ 10° of longitude for "
               "≥ 3 days. Satellite record from 1987.")
    save(fig, args.out,
         alt=f"Longitude–time diagrams of daily equatorial east–west wind anomalies from October of the year before "
             f"to January after the first year of the El Niños of " + join_and(f"{y}/{y + 1}" for y in EVENTS)
             + f". Westerly wind bursts from October to {latest:%-d %B}: "
             + join_and(f"{y}/{y + 1} {counts[y]}" for y in EVENTS) + ".")


if __name__ == "__main__":
    main()
