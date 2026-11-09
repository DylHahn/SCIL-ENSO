"""
Kelvin waves 4 — Horizontal Hovmöller diagrams of Kelvin waves in four El Niños

Daily TAO/TRITON buoy data along the equator (see enso_tao.py) from October of the year before each El Niño to
January after its first year, with time running left to right and longitude running up the page, so a wave
travelling east is a streak rising to the right. --var chooses the depth of the 20 °C isotherm, dynamic height
(surface height) or satellite sea level (the blended record from 2017 and the delayed-time record of 2012–2019,
with dynamic height for 1997/1998, before those records); --kind chooses the Kelvin-wave signal or its rate of change.

    python hovmoller_kelvin_events.py --var d20 --kind signal
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

from enso_common import FIG_DIR, COLORS, add_note, add_source, add_title, apply_style, join_and, lon_label, save
from anim_kelvin import kelvin_waves
from enso_sealevel import delayed_time_anomalies
from enso_tao import LONS, anomalies, infill_across, rate_of_change, wave_signal

NOW = 2026
EVENTS = [NOW, 2023, 2015, 1997]
SETTINGS = {"d20": dict(name="warm-layer depth (20 °C isotherm)", unit="m", signal=32, rate=4.8, step=(4, 0.6)),
            "dyn": dict(name="surface height (dynamic height)", unit="cm", signal=10, rate=1.4, step=(1.25, 0.175)),
            "ssh": dict(name="satellite sea level", unit="cm", signal=10, rate=1.6, step=(1.25, 0.2))}


def window(y):
    return pd.Timestamp(f"{y - 1}-10-01"), pd.Timestamp(f"{y + 1}-01-31")


def satellite_signal(refresh):
    """Satellite Kelvin-wave signal by event: {year: signal}, with buoy dynamic height for 1997/1998."""
    _, sig, _ = kelvin_waves(refresh)
    dt = delayed_time_anomalies("2014-08-15", "2016-03-15")
    return {NOW: sig, 2023: sig, 2015: wave_signal(dt), 1997: wave_signal(anomalies("dyn", refresh))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--var", choices=list(SETTINGS), default="d20")
    ap.add_argument("--kind", choices=["signal", "rate"], default="signal")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "kelvin" / "hovmoller_kelvin_events.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    cfg = SETTINGS[args.var]
    if args.var == "ssh":
        signals = satellite_signal(args.refresh)
    else:
        signals = dict.fromkeys(EVENTS, wave_signal(anomalies(args.var, args.refresh)))
    fields = {y: infill_across(rate_of_change(s) if args.kind == "rate" else s) for y, s in signals.items()}
    latest = fields[NOW].dropna(how="all").index[-1]
    top = cfg[args.kind]
    step = cfg["step"][args.kind == "rate"]
    levels = np.arange(-top, top + step / 2, step)
    cmap = ListedColormap(plt.get_cmap("RdBu_r")(np.linspace(0.04, 0.96, len(levels) + 1)))
    norm = BoundaryNorm(levels, cmap.N, extend="both")

    H = 11.2
    fig = plt.figure(figsize=(13, H))
    L, W = 0.08, 0.83
    for k, y in enumerate(EVENTS):
        start, end = window(y)
        ax = fig.add_axes([L, (1.15 + (len(EVENTS) - 1 - k) * 2.27) / H, W, 1.9 / H])
        w = fields[y].loc[start:min(end, latest)]
        days = (w.index - start).days.values
        cf = ax.contourf(days, np.array(w.columns, float), w.values.T, levels=levels, cmap=cmap, norm=norm, extend="both")
        total = (end - start).days
        ax.set_xlim(0, total)
        ax.set_ylim(LONS[0], LONS[-1])
        ax.set_facecolor(COLORS["surface_2"])
        ax.set_yticks([165, 190, 220, 250, 265])
        ax.set_yticklabels([lon_label(v) for v in [165, 190, 220, 250, 265]], fontsize=10.5)
        ax.set_ylabel("Longitude\n(west → east)", fontsize=10.5)
        ticks = pd.date_range(start, end, freq="MS")[::3]
        ax.set_xticks([(t - start).days for t in ticks])
        when = {t: "\nyear before" if t.year < y else "\nfirst year" if t.year == y else "\nnext year" for t in ticks}
        ax.set_xticklabels([calendar.month_abbr[t.month] + (when[t] if t.month == 1 or t == ticks[0] else "") for t in ticks]
                           if k == len(EVENTS) - 1 else [], fontsize=10.5)
        ax.axvline((pd.Timestamp(f"{y}-01-01") - start).days, color=COLORS["text"], lw=0.8, ls=(0, (4, 3)))
        cur = y == NOW
        tag = "  (buoy surface height: no daily satellite record)" if args.var == "ssh" and y == 1997 else ""
        ax.set_title(f"{y}/{y + 1}{tag}", fontsize=14, fontweight="bold", loc="left", pad=5,
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        for sp in ax.spines.values():
            sp.set_visible(cur)
            sp.set_edgecolor(COLORS["el_nino"])
            sp.set_linewidth(2)
        if cur and latest < end:
            ax.axvspan((latest - start).days, total, color=COLORS["surface_2"], zorder=3)
            ax.text(((latest - start).days + total) / 2, np.mean(ax.get_ylim()), f"Data through\n{latest:%-d %b %Y}",
                    ha="center", va="center", fontsize=10, color=COLORS["text_2"], zorder=4)
    cax = fig.add_axes([L + W + 0.012, 1.15 / H, 0.014, (3 * 2.27 + 1.9) / H])
    cb = fig.colorbar(cf, cax=cax, ticks=levels[::2])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    label = (f"Rate of change of the signal ({cfg['unit']} per day)" if args.kind == "rate"
             else f"Kelvin-wave signal ({cfg['unit']})")
    cb.set_label(label, fontsize=11, fontweight="bold", color=COLORS["text"])

    add_note("Time runs left to right and longitude runs up the page, so a wave travelling east is a streak rising to "
             "the right. The dashed line marks 1 January of each El Niño's first year.")
    what = "Rate of change of the Kelvin-wave signal" if args.kind == "rate" else "Kelvin-wave signal"
    add_title(fig, f"{what} in {cfg['name']}, four El Niño events",
              (("Daily satellite sea level" if args.var == "ssh" else "Daily buoy measurements")
               + " on the equator, 165°E–95°W, from October of the year before each El Niño.")
              + (" Red: rising; blue: falling." if args.kind == "rate" else " Red: above its 91-day average; blue: below."))
    buoys = ("TAO/TRITON moored buoys (NOAA PMEL, via NOAA CoastWatch ERDDAP), daily, at 8 moorings 10–15° apart; anomalies "
             "from each mooring's 1991–2020 seasonal cycle,\n5-day means. Signal: anomaly minus its 91-day running mean. "
             "Rate of change: centred over 4 days. Gaps up to 10 days and single missing moorings are interpolated; blank "
             "areas have no data.")
    sat = ("NOAA satellite altimetry, 0.25°, daily, 1°S–1°N, every 1° of longitude: blended near-real-time product (2017 "
           "onward, CoastWatch ERDDAP) for 2026/2027 and 2023/2024, delayed-time product (2012–2019, PIFSC ERDDAP) for "
           "2015/2016, each\nanomalies from its own seasonal cycle; 1997/1998: TAO/TRITON buoy dynamic height. 5-day means. "
           "Signal: anomaly minus its 91-day running mean. Rate of change: centred over 4 days.")
    add_source(fig, "Data: " + (sat if args.var == "ssh" else buoys))
    save(fig, args.out,
         alt=f"Longitude–time diagrams of the {what.lower()} in {cfg['name']} along the equator from TAO buoys for the "
             "El Niños of " + join_and(f"{y}/{y + 1}" for y in EVENTS) + f", with data through {latest:%-d %B %Y}.")


if __name__ == "__main__":
    main()
