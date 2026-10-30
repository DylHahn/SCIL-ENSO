"""
Kelvin waves 5 — Animation: from the equatorial Kelvin waves to one tide gauge on the coast

For one tide gauge (chosen with --station, a UHSLC id), from October of the year before the current
El Niño to the latest day, in the style of anim_kelvin.py:
  top: the equatorial Kelvin-wave signal along the equator on the day shown (NOAA blended satellite
       altimetry, as in anim_kelvin.py), so each wave can be seen approaching South America;
  middle: coastal sea level at the gauge compared with normal (UHSLC fast-delivery daily data, see
       enso_tidegauges.py), drawn day by day;
  bottom: the coastal Kelvin-wave signal at the gauge, the same anomaly minus its 91-day running
       mean, drawn day by day.
A dashed line marks each equatorial Kelvin wave traced in anim_kelvin.py once it reaches 95°W, near
South America, numbered as in that figure. The website shows one version per gauge.

    python coastal_kelvin_signal.py --station 569
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import FuncFormatter

from anim_kelvin import LON_RANGE, START, kelvin_waves, wave_signal
from enso_anim import AnimationFrames
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, lon_label
from enso_tidegauges import STATIONS, alongshore_km, anomalies

NOW = 2026
# the gauges reporting since October 2025, south to north, numbered as in anim_coastal_sea_level.py
GAUGES = [91, 87, 569, 551, 556, 592, 558]
RED, BLUE = "#e8574a", "#3987e5"


def short(name):
    town, place = name.split(", ")
    abbr = {"California": "CA", "Oregon": "OR", "Washington": "WA"}
    return f"{town}, {abbr.get(place, place)}"


def shade(ax, x, v):
    """Red above zero, blue below; returns the artists so they can be replaced in the next frame."""
    return [ax.fill_between(x, 0, v, where=v > 0, color=RED, alpha=0.75, lw=0, interpolate=True),
            ax.fill_between(x, 0, v, where=v < 0, color=BLUE, alpha=0.75, lw=0, interpolate=True)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--station", type=int, default=GAUGES[0], help="UHSLC station id")
    ap.add_argument("--every", type=int, default=3, help="days per animation frame")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "kelvin" / "coastal_kelvin_signal.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    k = [s[0] for s in STATIONS].index(args.station)
    _, name, lat, lon = STATIONS[k]
    km = alongshore_km()[k]
    num = GAUGES.index(args.station) + 1 if args.station in GAUGES else None

    # equatorial wave signal (as in anim_kelvin.py) and the waves that crossed in this period
    _, eq, waves = kelvin_waves(args.refresh)
    eq = eq.loc[START:]
    lons = np.array(eq.columns, float)
    waves = [w for w in waves if w[0] + (w[3] - w[0]) / 2 >= pd.Timestamp(START)]
    # the gauge
    anom, _ = anomalies(refresh=args.refresh)
    s = anom[name]
    sig = wave_signal(s).loc[START:]
    s = s.loc[START:]
    last = s.last_valid_index()
    dates = pd.date_range(START, max(eq.index[-1], last))
    s, sig, eq = s.reindex(dates), sig.reindex(dates), eq.reindex(dates)
    s[s.index > last] = np.nan
    sig[sig.index > last] = np.nan

    H = 10.0
    fig = plt.figure(figsize=(13, H))
    L, W = 0.085, 0.6
    prof = fig.add_axes([L, 7.3 / H, W, 1.15 / H])
    top = fig.add_axes([L, 4.15 / H, W, 2.3 / H])
    bot = fig.add_axes([L, 1.0 / H, W, 2.65 / H], sharex=top)

    # top: the equatorial Kelvin-wave signal on the day shown
    prof.axhline(0, color=COLORS["text_2"], lw=0.8)
    elim = max(8, np.ceil(np.nanpercentile(np.abs(eq.values), 99.5) / 4) * 4)
    prof.set_ylim(-elim, elim)
    prof.set_xlim(*LON_RANGE)
    prof.set_xticks([140, 160, 180, 200, 220, 240, 260])
    prof.xaxis.set_major_formatter(FuncFormatter(lon_label))
    prof.yaxis.grid(True, color=COLORS["grid"], lw=0.6)
    prof.set_ylabel("Signal (cm)")
    prof.text(1.005, 0.5, "South\nAmerica →", transform=prof.transAxes, fontsize=10.5, fontweight="bold",
              color=COLORS["text_2"], va="center")
    prof_title = prof.set_title("", fontsize=13.5, fontweight="bold", loc="left", pad=8, color=COLORS["text"])
    eq_line, = prof.plot([], [], color=COLORS["text"], lw=1.3)
    eq_fill = []

    # middle and bottom: the gauge, drawn day by day
    lim = max(20, np.ceil(np.nanmax(np.abs(s.values)) / 10) * 10)
    top.set_ylim(-lim, lim)
    slim = max(8, np.ceil(np.nanmax(np.abs(sig.values)) / 4) * 4)
    bot.set_ylim(-slim, slim)
    top.set_ylabel("Sea level (cm)")
    bot.set_ylabel("Wave signal (cm)")
    top.set_title(f"Coastal sea level at {short(name)} compared with normal", fontsize=13.5, fontweight="bold",
                  loc="left", pad=8, color=COLORS["text"])
    bot.set_title(f"Kelvin-wave signal at {short(name)}: sea level minus its 91-day average", fontsize=13.5,
                  fontweight="bold", loc="left", pad=8, color=COLORS["text"])
    lines, cursors, arrivals = [], [], []
    for ax, ylim in ((top, lim), (bot, slim)):
        ax.axhline(0, color=COLORS["text_2"], lw=0.8)
        ax.yaxis.grid(True, color=COLORS["grid"], lw=0.6)
        ax.set_axisbelow(True)
        ax.set_xlim(dates[0], pd.Timestamp(f"{NOW}-12-31"))
        lines.append(ax.plot([], [], color=COLORS["text"], lw=1.1)[0])
        cursors.append(ax.axvline(dates[0], color="white", lw=1.2, alpha=0.9))
        for n, w in enumerate(waves, 1):
            ln = ax.axvline(w[3], color=COLORS["text"], lw=1, ls=(0, (4, 3)), alpha=0)
            lbl = ax.text(w[3], ylim * 0.95, f" {n}", fontsize=10.5, fontweight="bold", color=COLORS["text"],
                          va="top", alpha=0) if ax is top else None
            arrivals.append((w[3], ln, lbl))
    fills = {top: [], bot: []}
    gaps = [ax.axvspan(last + pd.Timedelta(days=1), pd.Timestamp(f"{NOW}-12-31"), color=COLORS["surface_2"], lw=0,
                       alpha=0, zorder=0) for ax in (top, bot)]
    gap_txt = bot.text(last + pd.Timedelta(days=6), -slim * 0.6, f"Tide-gauge data\nthrough {last:%-d %b %Y}",
                       fontsize=10.5, color=COLORS["text_2"], alpha=0,
                       zorder=5, bbox=dict(facecolor=COLORS["surface_2"], edgecolor="none", pad=2))
    plt.setp(top.get_xticklabels(), visible=False)
    bot.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    bot.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    for ax in (prof, top, bot):
        ax.tick_params(axis="both", labelsize=11)
        for tl in ax.get_xticklabels() + ax.get_yticklabels():
            tl.set_fontweight("bold")

    # right: the gauge on a map, coloured by its wave signal on the day shown
    pc = ccrs.PlateCarree()
    lx = L + W + 0.075
    mx = fig.add_axes([lx, 3.55 / H, 1 - lx - 0.01, 3.1 / H], projection=ccrs.PlateCarree(central_longitude=-100))
    mx.set_extent([-132, -74, -8, 52], crs=pc)
    mx.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"])
    mx.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none")
    mx.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5)
    mx.plot([-132, -74], [0, 0], color=COLORS["muted"], lw=0.7, ls=(0, (4, 3)), transform=pc)
    for g in GAUGES:
        st = STATIONS[[x[0] for x in STATIONS].index(g)]
        mx.plot(st[3], st[2], "o", ms=5, color=COLORS["muted"], transform=pc, zorder=4)
    levels = np.linspace(-slim, slim, 9)
    cmap = ListedColormap(plt.get_cmap("RdBu_r")(np.linspace(0.04, 0.96, len(levels) + 1)))
    dot = mx.scatter([lon], [lat], c=[0.0], cmap=cmap, norm=BoundaryNorm(levels, cmap.N, extend="both"), s=190,
                     edgecolors="white", linewidths=1.6, transform=pc, zorder=5)
    mx.set_title(f"{f'{num}  ' if num else ''}{short(name)}", fontsize=13.5, fontweight="bold", loc="left", pad=6,
                 color=COLORS["text"])
    fig.text(lx, 3.35 / H, f"{abs(lat):.1f}°{'N' if lat >= 0 else 'S'}, {abs(lon):.1f}°W"
             + (f"\nabout {km:,.0f} km along the coast\nfrom La Libertad, Ecuador" if abs(km) > 1 else ""),
             fontsize=11, fontweight="bold", color=COLORS["text"], va="top", linespacing=1.4)
    fig.text(lx, 2.2 / H, "The dot's colour is the gauge's\nwave signal on the day shown.\n\nDashed lines appear as each\n"
             "equatorial Kelvin wave reaches\n95°W, near South America.", fontsize=10.5, color=COLORS["text_2"],
             va="top", linespacing=1.35)

    add_title(fig, f"From the equator to the coast: Kelvin waves at {short(name)}",
              "Top: the equatorial Kelvin waves of Figure 2 travelling east toward South America. Below: sea level at "
              "one tide gauge, where part of each wave\narrives after turning along the coast, together with the "
              "effects of local winds and storms.")
    add_source(fig, "Data: University of Hawaii Sea Level Center fast-delivery daily tide-gauge data (anomalies from the "
               "1991–2020 seasonal cycle, 10-day means, not corrected for air pressure); NOAA\nblended satellite "
               "altimetry, 1°S–1°N (see Figure 2). Wave signal: anomaly minus its 91-day running mean; the last 45 days "
               "use a shorter average and may change.")

    frames = AnimationFrames(fig, dpi=100)
    idx = list(range(0, len(dates), args.every))
    if idx[-1] != len(dates) - 1:
        idx.append(len(dates) - 1)
    tnum = mdates.date2num(dates)
    for i in idx:
        d = dates[i]
        v = eq.values[i]
        eq_line.set_data(lons, v)
        for f in eq_fill:
            f.remove()
        eq_fill = shade(prof, lons, np.nan_to_num(v))
        prof_title.set_text(f"Equatorial Kelvin-wave signal along the equator, {d:%-d %B %Y}")
        for ax, series, ln in ((top, s, lines[0]), (bot, sig, lines[1])):
            y = series.values[:i + 1]
            ln.set_data(tnum[:i + 1], y)
            for f in fills[ax]:
                f.remove()
            fills[ax] = shade(ax, tnum[:i + 1], y)
        for c in cursors:
            c.set_xdata([d, d])
        for t1, ln, lbl in arrivals:
            on = 0.75 if d >= t1 else 0.0
            ln.set_alpha(on)
            if lbl is not None:
                lbl.set_alpha(1.0 if on else 0.0)
        past = d > last
        for g in gaps:
            g.set_alpha(1.0 if past else 0.0)
        gap_txt.set_alpha(1.0 if past else 0.0)
        gap_txt.get_bbox_patch().set_alpha(1.0 if past else 0.0)
        today = sig.values[min(i, sig.index.get_indexer([last])[0])]
        dot.set_array(np.ma.masked_invalid([today]))
        frames.grab(80)
    frames.durations[-1] = 4500
    arrived = [w for w in waves if w[3] <= last]
    frames.save(args.out, quality=82,
                alt=f"Animation from {dates[0]:%B %Y} to {dates[-1]:%-d %B %Y}: the equatorial Kelvin-wave signal "
                    f"along the equator, and coastal sea level and its Kelvin-wave signal at the {name} tide gauge "
                    f"(data through {last:%-d %B %Y}), with the arrival at 95°W of {len(arrived)} equatorial Kelvin "
                    f"waves in that time. Over the last 30 days of tide-gauge data, sea level there was "
                    f"{s.loc[:last].iloc[-30:].mean():+.0f} cm compared with normal.")


if __name__ == "__main__":
    main()
