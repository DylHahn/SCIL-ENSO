"""
Equatorial 6 — Eastern Pacific or Central Pacific El Niño?

El Niño events differ in where along the equator the warming is centred: near South America
(Eastern Pacific, or "cold tongue", El Niño, such as 1997/1998) or near the date line (Central
Pacific, or "warm pool", El Niño, such as 2015/2016 was in part). Following Ren and Jin (2011),
  Eastern Pacific index  N_CT = N3 − α N4
  Central Pacific index  N_WP = N4 − α N3,   α = 2/5 when N3 and N4 have the same sign, else 0,
from the Niño 3 and Niño 4 SST anomalies (ERSST v5, 1991–2020 monthly climatology), as 3-month
running means.
  (a) the two indices from January of each event's first year to December of the next;
  (b) every El Niño since 1950 at its peak (November–January), and the current event over its
      latest three months.

    python el_nino_type.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, find_events, join_and, load_roni, save
from enso_stats import load_gridded
from event_timeseries import N_MONTHS, NOW, aligned, box_series, onset_year

EVENTS = [NOW, 2023, 2015, 1997, 1982]
HIGHLIGHT = {2023: "#9085e9", 2015: "#c98500", 1997: "#199e70", 1982: "#3987e5", 1972: COLORS["neutral"]}
EP_COLOR, CP_COLOR = "#d95926", "#3987e5"          # categorical slots: orange, blue


def type_indices(sst):
    """Monthly (Eastern Pacific, Central Pacific) indices, 3-month running means (Ren and Jin 2011)."""
    n3 = box_series(sst, (-5, 5), (210, 270))
    n4 = box_series(sst, (-5, 5), (160, 210))
    alpha = np.where(n3 * n4 > 0, 0.4, 0.0)
    ep = (n3 - alpha * n4).rolling(3, center=True).mean()
    cp = (n4 - alpha * n3).rolling(3, center=True).mean()
    last = n3.dropna().index[-1]                          # centred means: the final month uses two months
    ep.loc[last] = (n3 - alpha * n4).loc[last - pd.DateOffset(months=1):last].mean()
    cp.loc[last] = (n4 - alpha * n3).loc[last - pd.DateOffset(months=1):last].mean()
    return ep, cp


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "equatorial" / "el_nino_type.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    sst = load_gridded("sst", args.refresh)
    ep, cp = type_indices(sst)
    latest = ep.dropna().index[-1]
    past = sorted({onset_year(e) for e in find_events(load_roni(refresh=args.refresh))} - {NOW})

    fig = plt.figure(figsize=(13, 12.2))
    # (a) small multiples, most recent first
    w, gap, left = 0.168, 0.02, 0.07
    lo = min(np.nanmin(aligned(s, y)) for s in (ep, cp) for y in EVENTS)
    hi = max(np.nanmax(aligned(s, y)) for s in (ep, cp) for y in EVENTS)
    x = np.arange(N_MONTHS)
    axes = []
    for k, y in enumerate(EVENTS):
        ax = fig.add_axes([left + k * (w + gap), 0.585, w, 0.2])
        e, c = aligned(ep, y), aligned(cp, y)
        ax.axhline(0, color=COLORS["text_2"], lw=0.8)
        ax.plot(x, e, color=EP_COLOR, lw=2.4, solid_capstyle="round")
        ax.plot(x, c, color=CP_COLOR, lw=2.4, solid_capstyle="round")
        if y == NOW:
            for s, col in ((e, EP_COLOR), (c, CP_COLOR)):
                j = int(np.flatnonzero(np.isfinite(s))[-1])
                ax.plot(x[j], s[j], "o", ms=7, color=col, mec=COLORS["surface"], mew=1.5)
        ax.set_ylim(lo - 0.3, hi + 0.3)
        ax.set_xlim(0, N_MONTHS - 1)
        ax.set_xticks([0, 6, 12, 18])
        ax.set_xticklabels(["Jan", "Jul", "Jan", "Jul"])
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        if k:
            ax.set_yticklabels([])
        else:
            ax.set_ylabel("Index (°C)")
        cur = y == NOW
        ax.set_title(f"{y}/{y + 1}", fontsize=14, fontweight="bold", loc="left", pad=6,
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        for sp in ax.spines.values():
            sp.set_visible(cur)
            sp.set_edgecolor(COLORS["el_nino"])
            sp.set_linewidth(2)
        axes.append(ax)
    fig.text(left, 0.83, "(a) The two indices from January of each El Niño's first year to December of the next",
             fontsize=14, fontweight="bold", color=COLORS["text"])
    fig.text(left + 2.5 * (w + gap) - gap / 2, 0.548, "Month  (first year → second year)", ha="center",
             fontsize=11, color=COLORS["text_2"])
    fig.legend(handles=[Line2D([], [], color=EP_COLOR, lw=2.4, label="Eastern Pacific index (warming near South America)"),
                        Line2D([], [], color=CP_COLOR, lw=2.4, label="Central Pacific index (warming near the date line)")],
               loc="lower left", bbox_to_anchor=(left - 0.01, 0.845), ncol=2, fontsize=11, frameon=False,
               labelcolor=COLORS["text"], handlelength=1.8, columnspacing=2)

    # (b) every El Niño at its peak
    bx = fig.add_axes([0.07, 0.1, 0.5, 0.37])
    peak = {}
    for y in past:
        sl = slice(f"{y}-11-01", f"{y + 1}-01-01")
        peak[y] = (float(cp.loc[sl].mean()), float(ep.loc[sl].mean()))
    now_pt = (float(cp.loc[latest - pd.DateOffset(months=2):latest].mean()),
              float(ep.loc[latest - pd.DateOffset(months=2):latest].mean()))
    allv = np.array(list(peak.values()) + [now_pt])
    xlim = (min(-1.0, allv[:, 0].min() - 0.3), max(1.5, allv[:, 0].max() + 0.4))
    ylim = (min(-1.0, allv[:, 1].min() - 0.3), allv[:, 1].max() + 0.45)
    d = np.array([min(xlim[0], ylim[0]), max(xlim[1], ylim[1])])
    bx.plot(d, d, color=COLORS["muted"], lw=1, ls=(0, (4, 3)))
    bx.fill_between(d, d, d[1], color=EP_COLOR, alpha=0.07, lw=0)
    bx.fill_between(d, d[0], d, color=CP_COLOR, alpha=0.07, lw=0)
    bx.text(0.03, 0.97, "Eastern Pacific type ↑", transform=bx.transAxes, va="top", fontsize=12,
            color=COLORS["text"])
    bx.text(0.97, 0.03, "Central Pacific type ↓", transform=bx.transAxes, ha="right", fontsize=12,
            color=COLORS["text"])
    for y, (cx, ey) in peak.items():
        hl = y in EVENTS
        bx.plot(cx, ey, "o", ms=11 if hl else 7, color=HIGHLIGHT[y] if hl else COLORS["neutral"],
                mec=COLORS["surface"], mew=1.5, zorder=4 if hl else 3, alpha=1 if hl else 0.75)
        if hl:                                                  # label only the events named in the text
            right = cx < now_pt[0] and abs(ey - now_pt[1]) < 0.4
            bx.annotate(f"{y}/{y + 1}", (cx, ey), xytext=(-9 if right else 9, 4), textcoords="offset points",
                        ha="right" if right else "left", fontsize=11, color=COLORS["text"])
    bx.plot(*now_pt, "o", ms=14, color=COLORS["el_nino"], mec=COLORS["surface"], mew=1.8, zorder=6)
    bx.annotate(f"{NOW}/{NOW + 1} so far", now_pt, xytext=(10, 6), textcoords="offset points", fontsize=12,
                fontweight="bold", color=COLORS["el_nino"])
    bx.plot([], [], "o", ms=7, color=COLORS["neutral"], label="Other El Niños since 1950")
    bx.legend(loc="upper right", fontsize=10.5, frameon=False, labelcolor=COLORS["text_2"])
    bx.set_xlim(*xlim)
    bx.set_ylim(*ylim)
    bx.set_xlabel("Central Pacific index (°C)")
    bx.set_ylabel("Eastern Pacific index (°C)")
    bx.grid(True)
    bx.set_axisbelow(True)
    bx.set_title("(b) Every El Niño since 1950 at its peak", fontsize=14, loc="left", pad=10)

    def kind(cx, ey):
        return "Eastern Pacific" if ey > cx else "Central Pacific"
    notes = ("How to read (b): each dot is one El Niño, placed by\nits two indices averaged over November–January,\n"
             "when most El Niños peak. Dots above the dashed\nline warmed most in the eastern Pacific; dots\n"
             "below it warmed most near the date line. The red\ndot is the current event over its latest three\n"
             f"months ({(latest - pd.DateOffset(months=2)):%B}–{latest:%B %Y}), before its peak.\n\n"
             f"{NOW}/{NOW + 1} so far: Eastern Pacific {now_pt[1]:+.1f} °C,\nCentral Pacific {now_pt[0]:+.1f} °C "
             f"({kind(*now_pt)} type).\n"
             + "\n".join(f"{y}/{y + 1} at peak: {peak[y][1]:+.1f} and {peak[y][0]:+.1f} °C" for y in EVENTS[1:]))
    fig.text(0.615, 0.465, notes, va="top", fontsize=11.5, color=COLORS["text"], linespacing=1.45,
             bbox=dict(facecolor=COLORS["surface_2"], edgecolor="none", pad=10))

    add_title(fig, "Eastern Pacific or Central Pacific El Niño?",
              "Where along the equator the warming is centred, measured by two indices that separate warming near "
              "South America (Eastern Pacific)\nfrom warming near the date line (Central Pacific). Strong Eastern "
              "Pacific events bring the largest changes to rainfall in the Americas.")
    add_source(fig, "Data: NOAA ERSST v5 Niño 3 and Niño 4 anomalies (1991–2020 climatology), 3-month means. "
               "Indices: Ren and Jin (2011), Geophys. Res. Lett. 38, L04704; see also Kao and Yu (2009).")
    save(fig, args.out,
         alt=f"Line charts of the Eastern Pacific and Central Pacific El Niño indices for "
             + join_and(f"{y}/{y + 1}" for y in EVENTS)
             + f", and a scatter plot of every El Niño since 1950 at its peak. Over {latest:%B %Y} and the two "
             f"months before, the {NOW}/{NOW + 1} event had an Eastern Pacific index of {now_pt[1]:+.1f} °C and a "
             f"Central Pacific index of {now_pt[0]:+.1f} °C ({kind(*now_pt)} type); at their peaks, "
             + join_and(f"{y}/{y + 1} {peak[y][1]:+.1f} and {peak[y][0]:+.1f} °C" for y in EVENTS[1:]) + ".")


if __name__ == "__main__":
    main()
