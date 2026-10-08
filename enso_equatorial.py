"""
Equatorial Pacific diagnostics: Hovmöller (longitude–time) diagrams that compare
the evolution of several El Niño events month by month.

Each event is shown from January of its onset year to January of the following
year, the period in which El Niño develops and reaches its peak.
"""

from __future__ import annotations

import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import FuncFormatter

from enso_common import COLORS, add_source, add_title, lon_label, save

EVENTS = [1982, 1997, 2015, 2026]
LON_RANGE = (130, 280)


def event_months(year, n=13):
    """First-of-month timestamps from January of `year` for `n` months."""
    return list(pd.date_range(f"{year}-01-01", periods=n, freq="MS"))


def hovmoller_figure(fields, levels, cmap_name, cbar_label, title, subtitle, source, out, alt,
                     highlight=None, cbar_ticks=None, data_through=None):
    """fields: {year: (months[list of Timestamp], lons[1-D], values[month, lon])}; months may stop
    early (current event). One panel per year, side by side, time running downward."""
    years = list(fields)
    n = len(years)
    fig = plt.figure(figsize=(13, 8.8))
    cmap = plt.get_cmap(cmap_name, len(levels) - 1)
    norm = BoundaryNorm(levels, cmap.N)
    width, gap, left = 0.198, 0.022, 0.10
    cf = None
    for k, y in enumerate(years):
        months, lons, vals = fields[y]
        ax = fig.add_axes([left + k * (width + gap), 0.21, width, 0.58])
        t = np.arange(len(months))
        cf = ax.contourf(lons, t, vals, levels=levels, cmap=cmap, norm=norm, extend="both")
        full = len(event_months(y))
        ax.set_ylim(full - 1, 0)                              # time runs downward, full period for all
        ax.set_xlim(*LON_RANGE)
        ax.set_facecolor(COLORS["surface_2"])
        ticks = list(range(0, full, 2))
        ax.set_yticks(ticks)
        labels = [calendar.month_abbr[(m % 12) + 1] for m in ticks]
        labels[0], labels[-1] = "Jan\n(onset year)", "Jan\n(following year)"
        ax.set_yticklabels(labels if k == 0 else [], fontsize=10.5)
        ax.set_xticks([150, 180, 210, 240, 270])
        ax.xaxis.set_major_formatter(FuncFormatter(lon_label))
        ax.tick_params(axis="x", labelsize=9.5, rotation=0)
        cur = y == highlight
        ax.set_title(f"{y}–{str(y + 1)[-2:]}", fontsize=15, fontweight="bold", loc="left",
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        for s in ax.spines.values():
            s.set_visible(cur)
            s.set_edgecolor(COLORS["el_nino"])
            s.set_linewidth(2)
        if len(months) < full:
            ax.axhline(len(months) - 1, color=COLORS["text_2"], lw=1, ls=(0, (3, 2)))
            ax.text(np.mean(LON_RANGE), len(months) + 0.4,
                    f"Data through\n{months[-1]:%B %Y}" if data_through is None else data_through,
                    ha="center", va="top", fontsize=10.5, color=COLORS["text_2"])
    fig.text(left + 2 * (width + gap) - gap / 2, 0.155, "Longitude along the equator  (west → east)",
             ha="center", fontsize=11, color=COLORS["text_2"])

    cax = fig.add_axes([0.28, 0.095, 0.44, 0.02])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=cbar_ticks)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label(cbar_label, fontsize=11, color=COLORS["text_2"])
    add_title(fig, title, subtitle)
    add_source(fig, source)
    save(fig, out, alt=alt)
