"""
Ocean 7 — Warm water stored in the equatorial Pacific before each El Niño began

NOAA PMEL's warm water volume (the volume of water above 20 °C between 5°S and 5°N, 120°E–80°W)
for every El Niño since 1980:
  (a) the anomaly averaged over the six months before each event began (its first month at
      +0.5 °C or more in NOAA's RONI), in 10¹⁴ m³;
  (b) the monthly anomaly aligned on that first month, from 18 months before to 12 months after.
Warm water builds up along the equator before an El Niño (the "recharge") and is drained toward
the poles during it (the "discharge"). Anomalies relative to the 1991–2020 monthly climatology.

    python warm_water_before_onset.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, find_events, join_and, load_roni, \
    load_wwv_pmel, save
from anim_timeseries import ordinal
from event_timeseries import NOW, onset_year

# the site's fixed event colours (2026/2027 uses the El Niño red)
HIGHLIGHT = {2023: "#9085e9", 2015: "#c98500", 1997: "#199e70", 1982: "#3987e5"}
BEFORE, AFTER, WINDOW = 18, 12, 6


def event_starts(roni):
    """{onset year: first month at +0.5 °C or more} for every El Niño since 1980, and the current one."""
    starts = {onset_year(e): e.index[0] for e in find_events(roni)}
    run = roni.loc[f"{NOW - 1}-06":]
    above = run >= 0.5
    if above.iloc[-1]:                                       # the current event, even if still short
        k = len(above) - 1
        while k > 0 and above.iloc[k - 1]:
            k -= 1
        starts[NOW] = run.index[k]
    return {y: t for y, t in sorted(starts.items()) if t >= pd.Timestamp("1981-07-01")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "ocean" / "warm_water_before_onset.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    roni = load_roni(refresh=args.refresh)
    vol = load_wwv_pmel(refresh=args.refresh, column=1) / 1e14                 # 10¹⁴ m³
    clim = vol.loc["1991":"2020"].groupby(vol.loc["1991":"2020"].index.month).mean()
    anom = vol - clim.reindex(vol.index.month).values
    starts = event_starts(roni)
    pre = {y: float(anom.loc[t - pd.DateOffset(months=WINDOW):t - pd.DateOffset(months=1)].mean())
           for y, t in starts.items()}
    past = [v for y, v in pre.items() if y != NOW]
    mean_past = float(np.mean(past))
    color = lambda y: COLORS["el_nino"] if y == NOW else HIGHLIGHT.get(y, COLORS["neutral"])

    fig = plt.figure(figsize=(13, 10.6))
    ax = fig.add_axes([0.07, 0.55, 0.9, 0.25])
    years = list(pre)
    x = np.arange(len(years))
    ax.bar(x, [pre[y] for y in years], width=0.72, color=[color(y) for y in years],
           edgecolor=COLORS["surface"], linewidth=2, zorder=3)
    ax.axhline(0, color=COLORS["text_2"], lw=0.9, zorder=4)
    ax.axhline(mean_past, color=COLORS["text"], lw=1.2, ls=(0, (4, 3)), zorder=4)
    gap = int(np.argmin([pre[y] for y in years]))                  # label over the lowest bar, clear of the others
    ax.text(gap, mean_past + 0.08, f"average of past El Niños {mean_past:+.1f}", va="bottom", ha="center",
            fontsize=10.5, color=COLORS["text"])
    for xi, y in zip(x, years):
        if y == NOW or y in HIGHLIGHT:
            v = pre[y]
            ax.text(xi, v + (0.06 if v >= 0 else -0.06), f"{v:+.1f}", ha="center", va="bottom" if v >= 0 else "top",
                    fontsize=11, color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels([f"{y}/\n{y + 1}" for y in years], fontsize=10)
    for lbl, y in zip(ax.get_xticklabels(), years):
        if y == NOW:
            lbl.set_color(COLORS["el_nino"])
    ax.set_xlim(-0.6, len(years) - 0.4)
    lo, hi = min(pre.values()), max(pre.values())
    ax.set_ylim(min(lo, 0) - 0.35, hi + 0.45)
    ax.set_ylabel("Anomaly (10$^{14}$ m³)")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.set_title("(a) Warm water in the six months before each El Niño began", fontsize=14, loc="left", pad=10)

    bx = fig.add_axes([0.07, 0.12, 0.9, 0.33])
    lags = np.arange(-BEFORE, AFTER + 1)
    bx.axvspan(-WINDOW - 0.5, -0.5, color=COLORS["surface_2"], zorder=0)
    bx.text(-WINDOW / 2 - 0.5, 0.97, "six months\nused in (a)", transform=bx.get_xaxis_transform(), ha="center",
            va="top", fontsize=10, color=COLORS["text_2"])
    bx.axvline(0, color=COLORS["text_2"], lw=1, ls=(0, (3, 2)))
    bx.axhline(0, color=COLORS["text_2"], lw=0.9)
    ends = []
    for y, t in starts.items():
        idx = [t + pd.DateOffset(months=int(k)) for k in lags]
        s = anom.reindex(idx).values
        if y == NOW:
            bx.plot(lags, s, color=COLORS["el_nino"], lw=3.4, zorder=6, solid_capstyle="round")
            k = int(np.flatnonzero(np.isfinite(s))[-1])
            bx.plot(lags[k], s[k], "o", ms=8, color=COLORS["el_nino"], mec=COLORS["surface"], mew=1.5, zorder=7)
            ends.append((lags[k], s[k], f"{y}/{y + 1}"))
        elif y in HIGHLIGHT:
            bx.plot(lags, s, color=HIGHLIGHT[y], lw=2.0, zorder=4)
            k = int(np.flatnonzero(np.isfinite(s))[-1])
            ends.append((lags[k], s[k], f"{y}/{y + 1}"))
        else:
            bx.plot(lags, s, color=COLORS["neutral"], lw=0.9, alpha=0.6, zorder=2)
    span = np.diff(bx.get_ylim())[0]
    placed = []
    for lx, ly, txt in sorted(ends, key=lambda e: e[1]):     # labels at the line ends, kept apart
        yy = ly
        while any(abs(yy - p) < 0.06 * span and abs(lx - q) < 4 for p, q in placed):
            yy += 0.03 * span
        placed.append((yy, lx))
        bx.text(lx + 0.35, yy, txt, va="center", fontsize=10.5, color=COLORS["text"])
    bx.set_xlim(-BEFORE, AFTER + 2.5)
    bx.set_xticks(np.arange(-18, AFTER + 1, 3))
    bx.set_xticklabels([f"{k}" if k else "El Niño\nbegins" for k in np.arange(-18, AFTER + 1, 3)])
    bx.set_xlabel("Months before (−) and after the El Niño began")
    bx.set_ylabel("Anomaly (10$^{14}$ m³)")
    bx.yaxis.grid(True)
    bx.set_axisbelow(True)
    bx.set_title("(b) Warm water month by month, aligned on the month each El Niño began", fontsize=14,
                 loc="left", pad=10)

    handles = ([Line2D([], [], color=COLORS["el_nino"], lw=3.4, label=f"{NOW}/{NOW + 1}")]
               + [Line2D([], [], color=c, lw=2, label=f"{y}/{y + 1}") for y, c in HIGHLIGHT.items()]
               + [Line2D([], [], color=COLORS["neutral"], lw=1, label="Other El Niños since 1980")])
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.06, 0.845), ncol=6, fontsize=10.5,
               labelcolor=COLORS["text_2"], handlelength=1.8, columnspacing=1.2, frameon=False)

    rank = sorted(pre.values(), reverse=True).index(pre[NOW]) + 1
    # the latest month of the current event, against every past event the same number of months after it began
    lag = (vol.index[-1].year - starts[NOW].year) * 12 + vol.index[-1].month - starts[NOW].month
    now_val = float(anom.iloc[-1])
    then = [float(anom.get(t + pd.DateOffset(months=lag), np.nan)) for y, t in starts.items() if y != NOW]
    then_max = np.nanmax(then)
    big = max(past)
    big_y = [y for y, v in pre.items() if v == big][0]
    add_title(fig, "Warm water stored in the equatorial Pacific before each El Niño began",
              f"Volume of water warmer than 20 °C between 5°S and 5°N compared with normal. Before the {NOW}/{NOW + 1} "
              f"El Niño began ({starts[NOW]:%B %Y}), it was\n{pre[NOW]:+.1f} × 10$^{{14}}$ m³, "
              f"{'the largest' if rank == 1 else f'the {ordinal(rank)} largest'} of {len(pre)} El Niños since 1980 (the largest "
              f"was {big:+.1f} before {big_y}/{big_y + 1}).\nBy {vol.index[-1]:%B %Y} it had reached {now_val:+.1f}, "
              + (f"more than any past El Niño {lag} months after it began (previous highest {then_max:+.1f})."
                 if now_val > then_max else f"against a previous highest of {then_max:+.1f} at that stage."))
    add_source(fig, "Data: NOAA PMEL warm water volume (5°S–5°N, 120°E–80°W, above the 20 °C isotherm); event "
               "start: first month of NOAA CPC RONI at +0.5 °C or more. Anomalies relative to 1991–2020.")
    save(fig, args.out,
         alt=f"Bar chart and line chart of equatorial Pacific warm water volume before and during every El Niño "
             f"since 1980. Average anomaly in the six months before each event began: "
             + join_and(f"{y}/{y + 1} {pre[y]:+.1f}" for y in [NOW] + list(HIGHLIGHT) if y in pre)
             + f" × 10¹⁴ m³; average of all past events {mean_past:+.1f}.")


if __name__ == "__main__":
    main()
