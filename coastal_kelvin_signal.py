"""
Kelvin waves 5 — Animation: satellite sea level around one tide gauge on the coast of the Americas

For one tide gauge (chosen with --station, a UHSLC id), from October of the year before the current
El Niño to the latest day: an animated map of NOAA's daily satellite sea level anomaly (blended
altimetry, 0.25°, the same product as anim_kelvin.py; see enso_sealevel.box_anomalies) over a box of
about 6° around the gauge, and, drawn day by day below it, the sea level at the satellite points
nearest the gauge and its Kelvin-wave signal (the anomaly minus its 91-day running mean, as for the
equatorial waves). Coastal-trapped Kelvin waves hug the coast, so they show as a band of higher sea
level along the shore. Dashed lines mark the days the equatorial Kelvin waves traced in anim_kelvin.py
reached 95°W, near South America, numbered as in that figure. The website shows one version per gauge.

    python coastal_kelvin_signal.py --station 569
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

from anim_kelvin import START, kelvin_waves, wave_signal
from enso_anim import AnimationFrames
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style
from enso_sealevel import box_anomalies
from enso_tidegauges import STATIONS, alongshore_km

NOW = 2026
# the gauges reporting since October 2025, south to north, numbered as in anim_coastal_sea_level.py
GAUGES = [91, 87, 569, 551, 556, 592, 558]
HALF = 3.0                                 # box half-height (degrees of latitude)
RED, BLUE = "#e8574a", "#3987e5"


def short(name):
    town, place = name.split(", ")
    abbr = {"California": "CA", "Oregon": "OR", "Washington": "WA"}
    return f"{town}, {abbr.get(place, place)}"


def shade(ax, x, v):
    """Red above zero, blue below; returns the artists so they can be replaced in the next frame."""
    return [ax.fill_between(x, 0, v, where=v > 0, color=RED, alpha=0.75, lw=0, interpolate=True),
            ax.fill_between(x, 0, v, where=v < 0, color=BLUE, alpha=0.75, lw=0, interpolate=True)]


def nearest_points(da, lat, lon, n=3):
    """The n points nearest the gauge with data on at least 90% of days, at least 0.3° (about 25 km) to its
    west, out to sea: altimetry next to the coast and inside straits is less reliable. Returns (lats, lons)."""
    ok = (da.notnull().mean("time") >= 0.9).values
    la, lo = np.meshgrid(da["latitude"].values, da["longitude"].values, indexing="ij")
    d = np.hypot(la - lat, (lo - lon) * np.cos(np.deg2rad(lat)))
    d[~ok | (lo > lon - 0.3)] = np.inf
    idx = np.argsort(d, axis=None)[:n]
    return la.ravel()[idx], lo.ravel()[idx]


def smooth(a, lat, lon, k=5):
    """Fill gaps next to the coast from the nearest ocean point (the land drawn on top covers them), then
    interpolate to a k times finer grid, so the map can be drawn with smooth contours."""
    from scipy import ndimage
    bad = ~np.isfinite(a)
    if bad.all():
        return None
    if bad.any():
        idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
        a = a[tuple(idx)]
    return (np.linspace(lat[0], lat[-1], len(lat) * k), np.linspace(lon[0], lon[-1], len(lon) * k),
            ndimage.zoom(a, k, order=1, mode="nearest", grid_mode=False))


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
    uid, name, lat, lon = STATIONS[k]
    km = alongshore_km()[k]
    num = GAUGES.index(uid) + 1 if uid in GAUGES else None

    # satellite sea level around the gauge, mostly offshore (the coast lies to the east)
    box = ((lat - HALF, lat + HALF), (lon - 4.8, lon + 1.2))
    da = box_anomalies(f"g{uid}", box, START, refresh=args.refresh)
    dates = pd.DatetimeIndex(da["time"].values)
    plat, plon = nearest_points(da, lat, lon)
    pts = np.nanmean(np.stack([da.sel(latitude=a, longitude=b).values for a, b in zip(plat, plon)]), axis=0)
    s = pd.Series(pts, index=dates)
    sig = wave_signal(s)
    _, _, waves = kelvin_waves(args.refresh)
    waves = [w for w in waves if w[0] + (w[3] - w[0]) / 2 >= pd.Timestamp(START)]   # as numbered in anim_kelvin.py

    H = 11.2
    fig = plt.figure(figsize=(13, H))
    pc = ccrs.PlateCarree()
    L = 0.075
    mw = 4.6                                                           # map width and height, inches
    mp = fig.add_axes([L, 5.15 / H, mw / 13, mw / H], projection=pc)
    levels = np.arange(-40, 40.1, 5)
    cmap = ListedColormap(plt.get_cmap("RdBu_r")(np.linspace(0.04, 0.96, len(levels) + 1)))
    norm = BoundaryNorm(levels, cmap.N, extend="both")
    glat, glon = da["latitude"].values, da["longitude"].values

    def draw(i):
        f = smooth(da.values[i], glat, glon)
        if f is None:
            return None
        return mp.contourf(f[1], f[0], f[2], levels=levels, cmap=cmap, norm=norm, extend="both", transform=pc,
                           zorder=1)
    mesh = draw(0)
    mp.set_extent([glon[0], glon[-1], glat[0], glat[-1]], crs=pc)       # the data's own edges: no empty strip
    mp.add_feature(cfeature.LAND.with_scale("10m"), facecolor=COLORS["land"], edgecolor="none", zorder=2)
    mp.add_feature(cfeature.COASTLINE.with_scale("10m"), edgecolor=COLORS["text_2"], linewidth=0.45, zorder=3)
    mp.add_feature(cfeature.BORDERS.with_scale("10m"), edgecolor=COLORS["muted"], linewidth=0.4, zorder=3)
    mp.plot(plon, plat, "o", ms=4, mfc="none", mec="black", mew=1.2, transform=pc, zorder=4)
    mp.plot(lon, lat, "*", ms=17, color="white", mec="black", mew=1, transform=pc, zorder=5)
    gl = mp.gridlines(draw_labels=True, color=COLORS["grid"], lw=0.4, alpha=0.5)
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = dict(color=COLORS["text_2"], fontsize=10, fontweight="bold")
    date = mp.text(0.03, 0.97, "", transform=mp.transAxes, fontsize=15, fontweight="bold", color="black", va="top",
                   zorder=6, bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=4))
    mp.set_title(f"Satellite sea level around {short(name)}", fontsize=13.5, fontweight="bold", loc="left", pad=8,
                 color=COLORS["text"])
    cax = fig.add_axes([L + mw / 13 + 0.012, 5.15 / H, 0.012, mw / H])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, ticks=levels[::2], extend="both")
    mp.set_facecolor(COLORS["surface_2"])                           # no satellite data
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    for t in cb.ax.get_yticklabels():
        t.set_fontweight("bold")
    cb.set_label("Sea level compared with normal (cm)", fontsize=11, fontweight="bold", color=COLORS["text"])

    # where the gauge is
    lx = 0.6
    loc = fig.add_axes([lx, 6.55 / H, 0.38, 3.2 / H], projection=ccrs.PlateCarree(central_longitude=-100))
    loc.set_extent([-132, -74, -8, 52], crs=pc)
    loc.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"])
    loc.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none")
    loc.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5)
    loc.plot([-132, -74], [0, 0], color=COLORS["muted"], lw=0.7, ls=(0, (4, 3)), transform=pc)
    for g in GAUGES:
        st = STATIONS[[x[0] for x in STATIONS].index(g)]
        loc.plot(st[3], st[2], "o", ms=5, color=COLORS["muted"], transform=pc, zorder=4)
    (la0, la1), (lo0, lo1) = box
    loc.plot([lo0, lo1, lo1, lo0, lo0], [la0, la0, la1, la1, la0], color=COLORS["el_nino"], lw=1.8, transform=pc,
             zorder=5)
    loc.set_title(f"{f'{num}  ' if num else ''}{name}", fontsize=13.5, fontweight="bold", loc="left", pad=6,
                  color=COLORS["text"])
    fig.text(lx, 6.35 / H, f"{abs(lat):.1f}°{'N' if lat >= 0 else 'S'}, {abs(lon):.1f}°W"
             + (f"\nabout {km:,.0f} km along the coast from La Libertad, Ecuador" if abs(km) > 1 else ""),
             fontsize=10.5, fontweight="bold", color=COLORS["text"], va="top", linespacing=1.4)
    fig.text(lx, 5.75 / H, "White star: the tide gauge. Black circles: the satellite points\nnearest it out at sea, "
             "averaged for the charts below. A coastal Kelvin\nwave shows as a band of higher sea level hugging "
             "the coast.\nBelow, dashed lines appear as each equatorial Kelvin\nwave of Figure 2 reaches 95°W, "
             "near South America.", fontsize=10.5, color=COLORS["text_2"], va="top", linespacing=1.35)

    # below: sea level at the satellite points nearest the gauge, drawn day by day
    top = fig.add_axes([L, 2.85 / H, 0.9, 1.55 / H])
    bot = fig.add_axes([L, 0.85 / H, 0.9, 1.55 / H], sharex=top)
    lim = max(10, np.ceil(np.nanmax(np.abs(s.values)) / 10) * 10)
    top.set_ylim(-lim, lim)
    slim = max(6, np.ceil(np.nanmax(np.abs(sig.values)) / 3) * 3)
    bot.set_ylim(-slim, slim)
    top.set_ylabel("SSH (cm)")
    bot.set_ylabel("Signal (cm)")
    top.set_title("Sea level height (SSH) near the gauge compared with normal", fontsize=13, fontweight="bold",
                  loc="left", pad=6, color=COLORS["text"])
    bot.set_title("Kelvin-wave signal near the gauge: SSH minus its 91-day average, so each passing wave is a peak",
                  fontsize=13, fontweight="bold", loc="left", pad=6, color=COLORS["text"])
    tnum = mdates.date2num(dates)
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
            lbl = ax.text(w[3], ylim * 0.93, f" {n}", fontsize=10.5, fontweight="bold", color=COLORS["text"],
                          va="top", alpha=0) if ax is top else None
            arrivals.append((w[3], ln, lbl))
        ax.tick_params(axis="both", labelsize=11)
    plt.setp(top.get_xticklabels(), visible=False)
    bot.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    bot.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    for ax in (top, bot):
        for tl in ax.get_xticklabels() + ax.get_yticklabels():
            tl.set_fontweight("bold")
    fills = {top: [], bot: []}

    last30 = np.nanmean(s.values[-30:])
    add_title(fig, f"Satellite sea level around {short(name)}, October {NOW - 1} to {dates[-1]:%B %Y}",
              f"Daily satellite sea level height (SSH) compared with normal. Last 30 days near the gauge: "
              f"{last30:+.0f} cm.")
    add_source(fig, "Data: NOAA blended satellite altimetry (sea level anomaly, daily, 0.25°, via NOAA CoastWatch "
               "ERDDAP), anomalies from the 2017–2024 seasonal cycle, 5-day means; points within about 25 km of the "
               "coast\nare less reliable. Kelvin-wave signal: anomaly minus its 91-day running mean (the last 45 days "
               "use a shorter average and may change). Equatorial waves as in Figure 2.")

    frames = AnimationFrames(fig, dpi=100)
    idx = list(range(0, len(dates), args.every))
    if idx[-1] != len(dates) - 1:
        idx.append(len(dates) - 1)
    for i in idx:
        d = dates[i]
        if mesh is not None:
            mesh.remove()
        mesh = draw(i)
        date.set_text(f"{d:%-d %B %Y}")
        for ax, series, ln in ((top, s, lines[0]), (bot, sig, lines[1])):
            y = series.values[:i + 1]
            ln.set_data(tnum[:i + 1], y)
            for f in fills[ax]:
                f.remove()
            fills[ax] = shade(ax, tnum[:i + 1], np.nan_to_num(y))
        for c in cursors:
            c.set_xdata([d, d])
        for t1, ln, lbl in arrivals:
            on = d >= t1
            ln.set_alpha(0.75 if on else 0.0)
            if lbl is not None:
                lbl.set_alpha(1.0 if on else 0.0)
        frames.grab(80)
    frames.durations[-1] = 4500
    frames.save(args.out, quality=82,
                alt=f"Animated map of daily satellite sea level around the {name} tide gauge from {dates[0]:%B %Y} to "
                    f"{dates[-1]:%-d %B %Y}, with the sea level at the satellite points nearest the gauge and its "
                    f"Kelvin-wave signal drawn day by day. Over the last 30 days, sea level there was {last30:+.0f} cm "
                    "compared with normal.")


if __name__ == "__main__":
    main()
