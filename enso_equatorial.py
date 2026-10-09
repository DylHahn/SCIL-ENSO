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


HOW_TO_READ = ("How to read: each panel is one El Niño event. Each horizontal row shows conditions along the "
               "equator (map above the panel)\nin a single month, from the western Pacific (left) to South America "
               "(right). Rows are stacked in time order, from January at the top to the following January.")


def _map_strip(fig, rect):
    """Thin map of the equatorial Pacific matching the panel's longitude range."""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    pc = ccrs.PlateCarree()
    ax = fig.add_axes(rect, projection=ccrs.PlateCarree(central_longitude=180))
    ax.set_extent([LON_RANGE[0], LON_RANGE[1], -15, 15], crs=pc)
    ax.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"], zorder=0)
    ax.add_feature(cfeature.LAND, facecolor=COLORS["text_2"], edgecolor="none", zorder=1)
    ax.plot([LON_RANGE[0], LON_RANGE[1]], [0, 0], transform=pc, color=COLORS["el_nino"], lw=1.4, zorder=2)
    ax.spines["geo"].set_edgecolor(COLORS["grid"])
    ax.text(0.01, 0.06, "New Guinea", transform=ax.transAxes, fontsize=8, color=COLORS["text"], va="bottom")
    ax.text(0.99, 0.94, "S. America", transform=ax.transAxes, fontsize=8, color=COLORS["text"], va="top",
            ha="right")
    ax.text(0.5, 0.56, "equator", transform=ax.transAxes, fontsize=7.5, color=COLORS["el_nino"], ha="center",
            va="bottom")
    return ax


def hovmoller_figure(fields, levels, cmap_name, cbar_label, title, subtitle, source, out, alt,
                     highlight=None, cbar_ticks=None, data_through=None):
    """fields: {year: (months[list of Timestamp], lons[1-D], values[month, lon])}; months may stop
    early (current event). One panel per year, side by side, time running downward, each with a
    small map of the equator above it so the horizontal axis reads as geography."""
    years = list(fields)
    fig = plt.figure(figsize=(13, 10.4))
    if cmap_name == "turbo":
        from enso_common import temp_cmap
        cmap, norm = temp_cmap(levels)
    else:
        cmap = plt.get_cmap(cmap_name, len(levels) - 1)
        norm = BoundaryNorm(levels, cmap.N)
    width, gap, left = 0.198, 0.022, 0.10
    p_bottom, p_height = 0.19, 0.52
    cf = None
    fig.text(0.02, 1 - 1.30 / 10.4, HOW_TO_READ, ha="left", va="top", fontsize=11.5, color=COLORS["text"],
             linespacing=1.4, bbox=dict(facecolor=COLORS["surface_2"], edgecolor="none", pad=6))
    for k, y in enumerate(years):
        months, lons, vals = fields[y]
        x0 = left + k * (width + gap)
        cur = y == highlight
        strip = _map_strip(fig, [x0, p_bottom + p_height + 0.012, width, 0.052])
        strip.set_title(f"{y}–{str(y + 1)[-2:]}", fontsize=15, fontweight="bold", loc="left", pad=6,
                        color=COLORS["el_nino"] if cur else COLORS["text"])
        ax = fig.add_axes([x0, p_bottom, width, p_height])
        t = np.arange(len(months))
        cf = ax.contourf(lons, t, vals, levels=levels, cmap=cmap, norm=norm, extend="both")
        full = len(event_months(y))
        for r in range(full):                                 # faint line per month: each row is one month
            ax.axhline(r, color=COLORS["surface"], lw=0.4, alpha=0.35)
        ax.set_ylim(full - 1, 0)                              # time runs downward, full period for all
        ax.set_xlim(*LON_RANGE)
        ax.set_facecolor(COLORS["surface_2"])
        ax.set_yticks(range(full))
        labels = [calendar.month_abbr[(m % 12) + 1] for m in range(full)]
        labels[0], labels[-1] = "Jan (onset yr)", "Jan (next yr)"
        ax.set_yticklabels(labels if k == 0 else [], fontsize=9.5)
        ax.set_xticks([150, 180, 210, 240, 270])
        ax.xaxis.set_major_formatter(FuncFormatter(lon_label))
        ax.tick_params(axis="x", labelsize=9.5, rotation=0)
        for sp in ax.spines.values():
            sp.set_visible(cur)
            sp.set_edgecolor(COLORS["el_nino"])
            sp.set_linewidth(2)
        if len(months) < full:
            ax.axhline(len(months) - 1, color=COLORS["text_2"], lw=1, ls=(0, (3, 2)))
            ax.text(np.mean(LON_RANGE), len(months) + 0.4,
                    f"Data through\n{months[-1]:%B %Y}" if data_through is None else data_through,
                    ha="center", va="top", fontsize=10.5, color=COLORS["text_2"])
        if k == 0:
            ax.set_ylabel("Month  (time runs downward ↓)", fontsize=11)
    fig.text(left + 2 * (width + gap) - gap / 2, 0.14, "Longitude along the equator  (west → east)",
             ha="center", fontsize=11, color=COLORS["text_2"])

    cax = fig.add_axes([0.28, 0.085, 0.44, 0.018])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=cbar_ticks)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label(cbar_label, fontsize=11, color=COLORS["text_2"])
    add_title(fig, title, subtitle)
    add_source(fig, source)
    save(fig, out, alt=alt)
