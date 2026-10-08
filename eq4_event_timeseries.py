"""
Equatorial 4 — Anomaly time series across El Niño events since 1950

Every El Niño since 1950 (NOAA's RONI rule: five or more overlapping seasons at
≥ +0.5 °C), aligned on January of its onset year and followed for 18 months:
  (a) Niño 3.4 SST anomaly        — ERSST v5, 1950–present
  (b) Niño 1+2 SST anomaly        — ERSST v5 (coastal Peru and Ecuador)
  (c) Upper-200 m temperature anomaly, 2°S–2°N, 180°–80°W — GODAS, 1980–present
Thin gray lines: individual past events; colored: the three strongest since
1980; dashed: mean of all past events; red: the current event.
Anomalies relative to the 1991–2020 monthly climatology.

    python eq4_event_timeseries.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from enso_common import (FIG_DIR, GODAS_DIR, COLORS, add_source, add_title, apply_style, event_label,
                         find_events, godas_equatorial_section, join_and, load_roni, save)
from enso_stats import load_gridded

N_MONTHS = 18
HIGHLIGHT = {1982: "#3987e5", 1997: "#199e70", 2015: "#c98500"}      # same slots as figure 9
NOW = 2026


def onset_year(ev):
    """Year in which the event's peak season begins (Dec–Feb peaks belong to the preceding year)."""
    t = ev.idxmax()
    return t.year if t.month >= 6 else t.year - 1


def box_series(sst, lat, lon):
    sub = sst.sel(lat=slice(*lat), lon=slice(*lon))
    s = sub.weighted(np.cos(np.deg2rad(sub["lat"]))).mean(("lat", "lon")).to_series()
    s.index = pd.to_datetime(s.index)
    clim = s.loc["1991":"2020"].groupby(s.loc["1991":"2020"].index.month).mean()
    return s - clim.reindex(s.index.month).values


def godas_heat_series(start="1980-01", end=None):
    """Monthly mean anomaly over 5–205 m, 2°S–2°N, 180°–80°W."""
    import xarray as xr
    from enso_common import GODAS_RAW_DIR
    end = end or "2025-12"
    months = list(pd.date_range(start, end, freq="MS"))
    raw = GODAS_RAW_DIR / f"pottmp.{NOW}.nc"
    if raw.exists():
        with xr.open_dataset(raw) as ds:
            months += list(pd.to_datetime(ds["time"].values))
    _, lons, anoms, _ = godas_equatorial_section(GODAS_DIR, [m.strftime("%Y-%m-%d") for m in months])
    east = (lons >= 180) & (lons <= 280)
    return pd.Series(np.nanmean(anoms[:, :, east], axis=(1, 2)), index=pd.DatetimeIndex(months))


def aligned(series, year):
    idx = pd.date_range(f"{year}-01-01", periods=N_MONTHS, freq="MS")
    return series.reindex(idx).values


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "equatorial" / "eq4_event_timeseries.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    events = [onset_year(e) for e in find_events(load_roni(refresh=args.refresh))]
    events = sorted({y for y in events if y < NOW})

    sst = load_gridded("sst", args.refresh)
    panels = [
        ("(a) Niño 3.4 sea surface temperature", "170°W–120°W, 5°S–5°N · ERSST v5",
         box_series(sst, (-5, 5), (190, 240))),
        ("(b) Niño 1+2 sea surface temperature", "90°W–80°W, 10°S–0° · ERSST v5",
         box_series(sst, (-10, 0), (270, 280))),
        ("(c) Upper-ocean (0–200 m) temperature", "2°S–2°N, 180°–80°W · GODAS",
         godas_heat_series()),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(13, 6.9), sharex=True)
    fig.subplots_adjust(top=0.70, bottom=0.17, left=0.06, right=0.985, wspace=0.18)
    x = np.arange(N_MONTHS)
    summary = []
    for ax, (title, sub, s) in zip(axes, panels):
        past = [y for y in events if np.isfinite(aligned(s, y)[:12]).all()]
        mat = np.array([aligned(s, y) for y in past])
        for y, row in zip(past, mat):
            if y not in HIGHLIGHT:
                ax.plot(x, row, color=COLORS["neutral"], lw=0.9, alpha=0.55, zorder=1)
        for y, c in HIGHLIGHT.items():
            if y in past:
                ax.plot(x, aligned(s, y), color=c, lw=2.0, zorder=3)
        ax.plot(x, np.nanmean(mat, axis=0), color=COLORS["text"], lw=1.8, ls=(0, (4, 3)), zorder=2)
        cur = aligned(s, NOW)
        k = int(np.flatnonzero(np.isfinite(cur))[-1])
        ax.plot(x[:k + 1], cur[:k + 1], color=COLORS["el_nino"], lw=3.2, zorder=4, solid_capstyle="round")
        ax.plot(x[k], cur[k], "o", ms=7, color=COLORS["el_nino"], mec=COLORS["surface"], mew=1.5, zorder=5)
        ax.annotate(f"{cur[k]:+.1f}", (x[k], cur[k]), xytext=(6, 2), textcoords="offset points",
                    fontsize=11, fontweight="bold", color=COLORS["text"])
        ax.axhline(0, color=COLORS["text_2"], lw=0.8)
        ax.axvline(k, color=COLORS["muted"], lw=0.8, ls=(0, (3, 2)))
        ax.set_title(title, fontsize=13, loc="left", pad=20)
        ax.text(0, 1.02, f"{sub} · {len(past)} past events", transform=ax.transAxes, fontsize=9.5,
                color=COLORS["text_2"], va="bottom")
        ax.set_xticks([0, 3, 6, 9, 12, 15])
        ax.set_xticklabels(["Jan", "Apr", "Jul", "Oct", "Jan", "Apr"], fontsize=10.5)
        ax.set_xlim(0, N_MONTHS - 1)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        same = mat[:, k]
        summary.append((title[4:], cur[k], int((same >= cur[k]).sum()), len(past),
                        past[int(np.nanargmax(same))], float(np.nanmax(same))))
    axes[0].set_ylabel("Anomaly (°C), relative to 1991–2020")
    fig.text(0.52, 0.085, "Months from January of the onset year (second “Jan” = following year)",
             ha="center", fontsize=11, color=COLORS["text_2"])
    handles = ([Line2D([], [], color=COLORS["el_nino"], lw=3.2, label=f"{NOW}–{str(NOW + 1)[-2:]}")]
               + [Line2D([], [], color=c, lw=2, label=f"{y}–{str(y + 1)[-2:]}") for y, c in HIGHLIGHT.items()]
               + [Line2D([], [], color=COLORS["neutral"], lw=1, label="Other El Niño events since 1950"),
                  Line2D([], [], color=COLORS["text"], lw=1.8, ls=(0, (4, 3)), label="Mean of past events")])
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.055, 0.775), ncol=6, fontsize=10.5,
               labelcolor=COLORS["text_2"], handlelength=1.8, columnspacing=1.2)

    short = ["Niño 3.4", "Niño 1+2", "the upper ocean"]
    top = [f"{sh} ({v:+.1f} °C)" for sh, (name, v, n_above, n, _, _) in zip(short, summary) if n_above == 0]
    add_title(fig, "Anomaly time series across El Niño events since 1950",
              "Each line is one El Niño event, aligned on January of the year it developed. At the latest month "
              "available, the current event\nexceeds every past event at the same stage in "
              + (join_and(top) if top else "none of the three measures") + ".")
    add_source(fig, "Data: NOAA ERSST v5 and NCEP GODAS; events from NOAA CPC RONI (≥ 5 overlapping seasons at "
               "+0.5 °C or more). Anomalies relative to the 1991–2020 monthly climatology.")
    save(fig, args.out,
         alt="Three panels of monthly anomaly time series for every El Niño since 1950, aligned by onset year: "
             + "; ".join(f"{name}: current {v:+.1f} °C, highest past value at the same stage {pv:+.1f} °C "
                         f"({py}–{str(py + 1)[-2:]})" for name, v, _, _, py, pv in summary) + ".")


if __name__ == "__main__":
    main()
